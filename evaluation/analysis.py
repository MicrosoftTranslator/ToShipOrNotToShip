from itertools import combinations
from scipy.stats import wilcoxon, kendalltau
from evaluation.tools import get_valid, get_equal_pairs, calculate_accuracy, bootstrap_get_pvalue
from evaluation.paper_resources import PAPER_MACROS, get_dependent_independent, generate_statistical_tests, generate_multiplot_deltas, generate_multiplot_deltas_excerpt, generate_sys_level_tex
from evaluation.SETTINGS import investigated_alphas, wmt_langs, logograms, non_latin_langs, investigated_metrics
from collections import defaultdict
from scipy.stats import pearsonr, spearmanr
import pandas as pd


def compute_statistics_for_eval(data, bootstrap=None):
    stat_data = []

    missing = defaultdict(lambda: defaultdict(int))
    missing_campaigns = defaultdict(lambda: defaultdict(int))

    counter = 0
    for campaign in data:
        counter += 1
        for systempair in list(combinations(data[campaign].keys(), 2)):
            # IMPORTANT. We can make comparison only for same set of campaigns.
            # If a given metric doesn't support language pair in a campaign,
            # then it must be removed from all comparisons

            skip_pair = False
            for metric in investigated_metrics:
                if metric not in data[campaign][systempair[0]]['automatic_metrics'] or metric not in data[campaign][systempair[1]]['automatic_metrics']:
                    missing[(data[campaign][systempair[0]]['hum_annotations']['Source'][0], data[campaign][systempair[0]]['hum_annotations']['Target'][0])][metric] += 1
                    missing_campaigns[campaign][metric] += 1
                    missing_campaigns[campaign]["counter"] = counter
                    skip_pair = True
            if skip_pair:
                continue

            valid_data_a = get_valid(data[campaign][systempair[0]]['hum_annotations'])
            valid_data_b = get_valid(data[campaign][systempair[1]]['hum_annotations'])
            if len(valid_data_a) != len(valid_data_b) or sum(abs(valid_data_a['SegmentID']-valid_data_b['SegmentID'])) != 0:
                valid_data_a, valid_data_b = get_equal_pairs(valid_data_a, valid_data_b)

            # double check that segment ids are equal
            if sum(abs(valid_data_a['SegmentID']-valid_data_b['SegmentID'])) != 0:
                raise ValueError("SegmentIDs are not equal")

            human_syspair_score = valid_data_a["Score"].mean() - valid_data_b["Score"].mean()

            processed_data = {'campaign': campaign,
                              'Source': data[campaign][systempair[0]]['hum_annotations']['Source'][0],
                              'Target': data[campaign][systempair[0]]['hum_annotations']['Target'][0],
                              'SystemA': data[campaign][systempair[0]]['automatic_metrics']['System'],
                              'SystemB': data[campaign][systempair[1]]['automatic_metrics']['System'],
                              'SystemAid': data[campaign][systempair[0]]['automatic_metrics']['SystemID'],
                              'SystemBid': data[campaign][systempair[1]]['automatic_metrics']['SystemID'],
                              'domain': data[campaign][systempair[0]]['automatic_metrics']['domain']}

            differences = (valid_data_a["Score"] - valid_data_b["Score"]).to_list()

            if len(differences) < 100:
                raise ValueError("There is too few lines, something is wrong!")

            t_stat, p_value_twosided = wilcoxon(differences, alternative='two-sided')

            processed_data["annot_counts"] = len(differences)
            processed_data["human_pvalue"] = p_value_twosided

            for p_value in investigated_alphas:
                if p_value_twosided > p_value:
                    processed_data['human'+str(p_value)] = 0
                else:
                    processed_data['human'+str(p_value)] = human_syspair_score

            if p_value_twosided > 0.05 or p_value_twosided < 0.001:
                processed_data['humanX'] = 0
            else:
                processed_data['humanX'] = human_syspair_score

            for metric in data[campaign][systempair[0]]['automatic_metrics']:
                if metric not in investigated_metrics:
                    continue

                value_a = data[campaign][systempair[0]]['automatic_metrics'][metric]
                value_b = data[campaign][systempair[1]]['automatic_metrics'][metric]
                # It may be confusing, why human score differences are sometimes calculated over a smaller set of sentences than automatic metric
                # This is due to the standard practice in MT, where human evaluation is run over a subset of sentences. 
                # Automatic metric could be also evaluated only on the equal set of sentences, but that would hurt their performance.
                # However, we got comparable results even when we restricted automatic metrics to sentences evaluated by humans.
                # Whenever a subset of sentences was used, the XLSX file contains 4 sheets:
                # hum_annotations: contains all sentences evaluated by humans and metrics
                # hum_only_automatic_metrics: contains system-level metric scores over sentences evaluated by humans
                # full_testset: contains all sentences evaluated by metrics (a subset of hum_annotations)
                # automatic_metrics: contain system-level metric scores over all sentences
                # If you are interested in scenario where metrics are compared only on the sentences evaluated by humans, uncomment the following code:
                #
                # if "hum_only_automatic_metrics" in data[campaign][systempair[0]]:                
                #     value_a = data[campaign][systempair[0]]['hum_only_automatic_metrics'][metric]
                #     value_b = data[campaign][systempair[1]]['hum_only_automatic_metrics'][metric]

                processed_data[metric] = value_a - value_b

                if bootstrap:
                    key = (processed_data["campaign"], processed_data["SystemAid"], processed_data["SystemBid"], 300)
                    if key in bootstrap:
                        if metric in bootstrap[key]:
                            rank_direction = 1 if value_a >= value_b else -1
                            processed_data[f'bootstrap_pvalue_{metric}'] = bootstrap_get_pvalue(bootstrap[key], metric, rank_direction)

            stat_data.append(processed_data)

    return stat_data


def generate_accuracy_results(stat_data, scenario="all", bootstrap_p_value=0.05):
    print(f"Calculating scenario {scenario}")

    statistics = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    if scenario in ["PUBL_MSFT", "PUBL_PUBL", "MSFT_MSFT"]:
        allowed_camp = get_dependent_independent(stat_data, scenario)

    dependent_total_annotations = 0
    processed_data_subset = []
    for processed in stat_data:
        if scenario in ["PUBL_MSFT", "PUBL_PUBL", "MSFT_MSFT"]:
            if (processed['campaign'], processed['SystemA'], processed['SystemB']) not in allowed_camp:
                continue

        if scenario == "all" or scenario == "bootstrap":
            pass
        elif scenario == "intoXX" and processed["Target"] == "ENU":
            continue
        elif scenario == "fromEN" and processed["Source"] != "ENU":
            continue
        elif scenario == "nonWMT" and processed["Target"] in wmt_langs:
            continue
        elif scenario == "nonLatin" and processed["Target"] not in non_latin_langs:
            continue
        elif scenario == "nonEnglish" and (processed["Source"] == "ENU" or processed["Target"] == "ENU"):
            continue
        elif scenario == "discussion" and processed["domain"] != 'discussion':
            continue
        elif scenario == "logogram_alphabet" and (processed["Target"] not in logograms):
            continue
        elif len(scenario) == 3 and scenario != processed["Target"]:
            # used to calculate accuracies for given target languages
            continue
        elif len(scenario) == 7:
            # used to calculate accuracies for translation direction
            src = scenario[0:3]
            trg = scenario[4:]
            if src != processed["Source"] or trg != processed["Target"]:
                continue

        dependent_total_annotations += processed["annot_counts"]
        processed_data_subset.append(processed)

    processed_df = pd.DataFrame(processed_data_subset)
    if len(processed_df) < 10:
        print(f"Skipping scenario {scenario} for not enough examples")
        return

    multiplied_metrics = processed_df[investigated_metrics].transpose() * processed_df['human1']
    processed_agreement = (multiplied_metrics > 0).astype(int).transpose()
    human_significance = (processed_df[[f"human{x}" for x in investigated_alphas + ["X"]]] != 0).astype(int)
    processed_agreement = pd.concat([processed_agreement, human_significance], axis=1)

    for processed in processed_data_subset:
        for metric in processed.keys():
            if metric not in investigated_metrics:
                continue  # this also ignores other columns

            for p_value in investigated_alphas:
                if scenario == "bootstrap":
                    if bootstrap_p_value != p_value:
                        pass
                    else:
                        boot_key = f"bootstrap_pvalue_{metric}"
                        if boot_key not in processed:
                            continue

                        if processed[boot_key] > bootstrap_p_value:
                            bootstrap_decision = 0
                        elif processed[metric] > 0:
                            bootstrap_decision = 1
                        else:
                            bootstrap_decision = -1

                        if bootstrap_decision == 0 and processed[f'human{bootstrap_p_value}'] == 0:
                            statistics[metric]["bootstrap"]["not_sig"] += 1
                        elif bootstrap_decision != 0 and processed[f'human{bootstrap_p_value}'] == 0:
                            statistics[metric]["bootstrap"]["error_I"] += 1
                            if (bootstrap_decision > 0 and processed['human1'] > 0) or (bootstrap_decision < 0 and processed['human1'] < 0):
                                statistics[metric]["bootstrap"]["error_I_correct"] += 1
                            else:
                                statistics[metric]["bootstrap"]["error_I_incorrect"] += 1
                        elif bootstrap_decision == 0 and processed[f'human{bootstrap_p_value}'] != 0:
                            statistics[metric]["bootstrap"]["error_II"] += 1
                        elif (bootstrap_decision > 0 and processed['human1'] > 0) or (bootstrap_decision < 0 and processed['human1'] < 0):
                            statistics[metric]["bootstrap"]["correct"] += 1
                        else:
                            statistics[metric]["bootstrap"]["incorrect"] += 1

                if processed['human'+str(p_value)] != 0:
                    if (processed[metric] > 0 and processed['human'+str(p_value)] > 0) or (processed[metric] < 0 and processed['human'+str(p_value)] < 0):
                        statistics[metric][str(p_value)]["concordant"] += 1
                    else:
                        statistics[metric][str(p_value)]["discordant"] += 1

                    if processed['human'+str(p_value)] > 0 and processed[metric] > 0:
                        statistics[metric][str(p_value)]["kappa_gg"] += 1
                    elif processed['human'+str(p_value)] < 0 and processed[metric] < 0:
                        statistics[metric][str(p_value)]["kappa_ll"] += 1
                    elif processed['human'+str(p_value)] >= 0:
                        statistics[metric][str(p_value)]["kappa_gl"] += 1
                    elif processed[metric] >= 0:
                        statistics[metric][str(p_value)]["kappa_lg"] += 1
                else:
                    statistics[metric][str(p_value)]["ignored"] += 1

    if scenario == "bootstrap":
        generate_statistical_tests(statistics)

    outputs = defaultdict(dict)
    for p_value in investigated_alphas:
        for metric in investigated_metrics:
            if scenario == "bootstrap" and bootstrap_p_value == p_value:
                outputs["Boot Correct"][metric] = statistics[metric]['bootstrap']['correct']
                outputs["Boot Incorrect"][metric] = statistics[metric]['bootstrap']['incorrect']
                outputs["Boot Not sig"][metric] = statistics[metric]['bootstrap']['not_sig']
                outputs["Boot Err. I."][metric] = statistics[metric]['bootstrap']['error_I']
                outputs["Boot Err. II."][metric] = statistics[metric]['bootstrap']['error_II']
                outputs["Boot I. Correct"][metric] = statistics[metric]['bootstrap']['error_I_correct']
                outputs["Boot I. Incorrect"][metric] = statistics[metric]['bootstrap']['error_I_incorrect']

            outputs["Pearson"][metric], _ = pearsonr(processed_df[metric], processed_df['human1'])
            outputs["Pearson"]['# points'] = len(processed_df)
            outputs["Spearman"][metric], _ = spearmanr(processed_df[metric], processed_df['human1'])
            outputs["Spearman"]['# points'] = len(processed_df)
            outputs["Kendal"][metric], _ = kendalltau(processed_df[metric], processed_df['human1'])
            outputs["Kendal"]['# points'] = len(processed_df)

        acc, clusters = calculate_accuracy(processed_agreement, f'human{p_value}', investigated_metrics, True)

        outputs[f'Acc {p_value}'] = acc.to_dict()
        outputs[f'CLUS Acc {p_value}'] = clusters.to_dict()

    # when p-value is between 0.05 and 0.001
    acc, clusters = calculate_accuracy(processed_agreement, 'humanX', investigated_metrics, True)
    outputs[f'Acc X'] = acc.to_dict()
    outputs[f'CLUS Acc X'] = clusters.to_dict()

    if scenario in ["PUBL_MSFT", "MSFT_MSFT"]:
        PAPER_MACROS['dependentLanguageCount'] = len(set(processed_df['Target']))
        PAPER_MACROS['dependentCampaigns'] = len(processed_df['Target'])
        PAPER_MACROS['dependentTotalEvaluationCountRounded'] = int(round(dependent_total_annotations*3/10000, 0)*10000)

    df = pd.DataFrame(outputs, columns=outputs.keys())
    df = df.sort_values(by='Acc 1', axis=0, ascending=False)

    df.to_excel("results/document_level_"+scenario+".xlsx")

    if scenario == "all":
        generate_multiplot_deltas(processed_df)
        generate_multiplot_deltas_excerpt(processed_df)
        generate_sys_level_tex(df)
        generate_sys_level_tex(df, True)
