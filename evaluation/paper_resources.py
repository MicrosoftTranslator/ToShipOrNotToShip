from matplotlib import pyplot as plt
import matplotlib
from scipy.stats import pearsonr, spearmanr
from collections import defaultdict
import os
import pandas as pd
import numpy as np
import random
from evaluation.SETTINGS import investigated_metrics, lang_names, metrics_names
from math import ceil
from statistics import mean

PAPER_MACROS = {}


def generate_list_of_languages(data):
    target_langs = defaultdict(int)
    pairs = defaultdict(int)
    pairs_testsetsizes = defaultdict(list)
    language_count = defaultdict(int)
    language_pairs = defaultdict(int)

    hman_annots = []
    lengths = []
    for campaign in data:
        once_per_campaign = True
        for system in data[campaign]:
            src = data[campaign][system]['hum_annotations']['Source'][0]
            trg = data[campaign][system]['hum_annotations']['Target'][0]
            hman_annots.append(len(data[campaign][system]['hum_annotations']))
            lengths.append(data[campaign][system]['automatic_metrics'][
                               'number_of_sentences'])
            language_pairs[(src, trg)] += 1

            target_langs[trg] += 1
            language_count[src] += 1
            language_count[trg] += 1
            if src in lang_names:
                src = lang_names[src]
            if trg in lang_names:
                trg = lang_names[trg]

            pairs[f"{src} - {trg}"] += 1
            if once_per_campaign:
                # systems in one campaign use the same testset, we do not won't to give higher weight to campaigns with multiple systems
                pairs_testsetsizes[f"{src} - {trg}"].append(
                    data[campaign][system]['automatic_metrics'][
                        'number_of_sentences'])
            once_per_campaign = False
    df = pd.DataFrame({"Systems": target_langs})
    df = df.sort_values(by="Systems", ascending=False)

    top_limit = 80
    legend = []
    for lang in df[df['Systems'] > 50].iterrows():
        if int(lang[1]) >= top_limit or True:
            legend.append("{} ({})".format(lang_names[lang[0]], int(lang[1])))
        else:
            legend.append("{}".format(lang_names[lang[0]]))

    PAPER_MACROS['countoflanguages'] = len(language_count)
    PAPER_MACROS['countofpairs'] = len(pairs)

    PAPER_MACROS['totalsystems'] = 0
    PAPER_MACROS['totalannotations'] = 0
    for campaign in data:
        PAPER_MACROS['totalsystems'] += len(data[campaign].keys())
        for system in data[campaign]:
            PAPER_MACROS['totalannotations'] += len(
                data[campaign][system]['hum_annotations'])
    PAPER_MACROS[
        'totalannotationsMillions'] = f"{PAPER_MACROS['totalannotations'] / 1000000:.1f} M"

    df = pd.DataFrame({"Sys.": pairs})
    df = df.sort_values(by="Sys.", ascending=False)

    PAPER_MACROS['countoflanguagesShowPairsOver'] = 15
    dfs = df[df['Sys.'] > PAPER_MACROS['countoflanguagesShowPairsOver']]
    df = dfs.reset_index()
    df = df.rename({'index': 'Language pair'}, axis=1)

    pairs_testsetsizes2 = {}
    for p in pairs_testsetsizes:
        pairs_testsetsizes2[p] = round(mean(pairs_testsetsizes[p]))
    dfpairs = pd.DataFrame({"Size": pairs_testsetsizes2})

    dfpairs.reset_index(inplace=True)
    dfpairs = dfpairs.rename({'index': 'Language pair'}, axis=1)
    df = df.merge(dfpairs)
    PAPER_MACROS['avgTestsetLength'] = round(dfpairs['Size'].mean())

    columns = 3
    lines = ceil(len(df) / columns)
    subcols = []
    for c in range(columns):
        subcols.append(df[c * lines:(c + 1) * lines].reset_index(drop=True))

    df = pd.concat(subcols, axis=1)
    df.to_latex("results/generated_lang_pairs_counts.tex", float_format="%d",
                caption="", na_rep="", index=False,
                label="tab:lang_pairs_counts")

    return target_langs, language_pairs


def generate_multiplot_deltas_excerpt(df):
    metrics = [['SacreBLEU_bleu', "COMET", 'Prism_ref', 'BLEURT_default']]

    calculate_deltas_multiplot(df, name="metric_deltas_excerpt",
                               metrics=metrics)


def generate_multiplot_deltas(df, name="metric_deltas", language=None):
    metrics = [['SacreBLEU_bleu', "COMET", 'COMET_src'],
               ['SacreBLEU_chrf', 'Prism_ref', 'Prism_src'],
               ['SacreBLEU_ter_neg', 'BERT_SCORE', 'BLEURT_default'],
               ['CharacTER_neg', 'ExtendedEditDist_neg', 'ESIM_']]

    calculate_deltas_multiplot(df, name=name, metrics=metrics,
                               language=language)


def calculate_deltas_multiplot(df, name, metrics, language=None):
    font = {'size': 7}
    matplotlib.rc('font', **font)

    x = len(metrics)
    y = len(metrics[0])
    # fig, axs = plt.subplots(y, x)
    fig = plt.figure(figsize=(y * 2, x * 2))
    gs = fig.add_gridspec(x, y, wspace=0)
    axs = gs.subplots(sharey=True)

    for i in range(x):
        for j in range(y):
            if x == 1:
                subaxs = axs[j]
            else:
                subaxs = axs[i, j]
            create_plot_with_deltas(df, metrics[i][j], subaxs, size=1,
                                    language=language)

            if j == 0:
                subaxs.set(ylabel='Human score Δ')

    fig.tight_layout()
    plt.savefig(f"results/{name}.svg")
    plt.savefig(f"results/{name}.png", dpi=600)
    plt.clf()


def generate_sys_level_tex(df, variants=False):
    df = df.loc[['# points'] + list(investigated_metrics)]
    df = df.rename(index=metrics_names)
    df = df.rename(index={'# points': 'n'})
    df = df.sort_values(by='Acc 1', axis=0, ascending=False)

    if variants:
        name = "generated_system_level_alphas_variants"
        columns = ["Acc 1", "Acc 0.05", "Acc X", "Spearman", "Pearson"]
        header = ["All", "0.05", "Within", "Spearman", "Pearson"]
        df["CLUS Spearman"] = False
        df["CLUS Pearson"] = False
    else:
        name = "generated_system_level_alphas"
        columns = ["Acc 1", "Acc 0.05", "Acc 0.01", "Acc 0.001", "Acc X"]
        header = ["All", "0.05", "0.01", "0.001", "Within"]

    df_formatted = df.apply(lambda data: bold_extreme_values(data), axis=0)
    df_formatted = color_clusters(df_formatted, df, columns)
    df_formatted.to_latex(f"results/{name}.tex", columns=columns, header=header,
                          float_format="%.1f", caption="", escape=False,
                          label="tab:system_level_description")


def generate_various_scenarios(domains=None, name="scenarios_accuracies",
                               p_value='0.05'):
    if domains is None:
        domains = {"all": "Everything", "ENU": "Into EN", "fromEN": "From EN",
                   "nonLatin": "Non Latin", "logogram_alphabet": "Logograms",
                   "nonWMT": "Non WMT", "discussion": "Discussion", }

    data = {}
    for domain in list(domains.keys()):
        filename = "results/document_level_" + domain + ".xlsx"
        if os.path.isfile(filename):
            df = pd.read_excel(filename)
            column = f"Acc {p_value}"
            data[domain] = df[['Unnamed: 0', column]].set_index('Unnamed: 0').to_dict()[column]
            col = f"CLUS {column}"
            loaded = df[['Unnamed: 0', col]].set_index('Unnamed: 0')
            # get booleans
            data[f"CLUS {domain}"] = (loaded == 1).to_dict()[col]
        else:
            del domains[domain]

    df = pd.DataFrame(data)
    df = df.loc[['# points'] + list(investigated_metrics)]
    df = df.rename(index=metrics_names)
    df = df.rename(index={'# points': 'n'})
    df = df.sort_values(by=df.columns[0], axis=0, ascending=False)

    df.to_excel("results/document_level_generated_" + name + ".xlsx")

    df_formatted = df.apply(lambda datad: bold_extreme_values(datad), axis=0)
    df_formatted = color_clusters(df_formatted, df, domains.keys())

    df_formatted = df_formatted[domains.keys()]
    df_formatted = df_formatted.rename(columns=domains)

    if name == "individual_language_pairs":
        # sort by average score
        df_formatted['sorting'] = df['ENU-FRA']  # first row
        df_formatted.at['n', 'sorting'] = 9999
        df_formatted = df_formatted.sort_values(by='sorting', axis=0,
                                                ascending=False).drop("sorting",
                                                                      axis=1)

        df_formatted = df_formatted.transpose()
        # drop results with less than 20 syspairs
        df_formatted = df_formatted[df_formatted['n'].astype(int) >= 20]
        df_formatted = df_formatted.sort_values(by='n', axis=0, ascending=False)

    df_formatted.to_latex("results/generated_" + name + ".tex", caption="",
                          float_format="%.1f", label="tab:" + name,
                          escape=False)


def generate_statistical_tests(statistics):
    outputs = defaultdict(dict)
    for metric in investigated_metrics:
        total = statistics[metric][str(1)]["concordant"] + statistics[metric][str(1)]["discordant"]
        correct = statistics[metric]['bootstrap']['correct'] + statistics[metric]['bootstrap']['error_I_correct']
        incorrect = statistics[metric]['bootstrap']['incorrect'] + statistics[metric]['bootstrap']['error_I_incorrect']

        if correct + incorrect < 10:
            continue
        outputs['No test'][metric] = round(
            100 * (statistics[metric][str(1)]["concordant"]) / total, 1)
        outputs["Boot."][metric] = round(100 * correct / (correct + incorrect),
                                         1)
        nonsignificant = statistics[metric]['bootstrap']['error_II'] + statistics[metric]['bootstrap']['not_sig']
        error_ii_perc = round(100 * (
            statistics[metric]['bootstrap']['error_II']) / nonsignificant, 1)
        outputs["Error II."][metric] = statistics[metric]['bootstrap'][
            'error_II']
        outputs["Error II. perc"][metric] = error_ii_perc
        outputs["n"][metric] = total
        outputs["boot n"][metric] = (correct + incorrect)

    df = pd.DataFrame(outputs)
    df = df.rename(index=metrics_names)
    df = df.sort_values(by=df.columns[1], axis=0, ascending=False)
    df = df.apply(lambda data: bold_extreme_values(data), axis=0)

    name = "statitical_tests"
    df.to_latex("results/generated_" + name + ".tex", caption="",
                float_format="%.1f", label="tab:" + name, escape=False)


# This function generates list of allowed campaigns containing dependent and
# independent systems
def get_dependent_independent(statistical_data, scenario):
    aimet = ['MSFT', 'PUBL']

    aicampaigns = defaultdict(list)
    for data in statistical_data:
        sys_a = data['SystemA'][0:4]
        sys_b = data['SystemB'][0:4]
        if sys_a in aimet and sys_b in aimet:
            aicampaigns[data['campaign']] += [data['SystemA'], data['SystemB']]

    publ_msft = defaultdict(list)
    publ_publ = defaultdict(list)
    msft_msft = defaultdict(list)

    counter = defaultdict(int)

    bleu = defaultdict(list)
    for data in statistical_data:
        sys_a = data['SystemA'][0:4]
        sys_b = data['SystemB'][0:4]
        if sys_a not in aimet or sys_b not in aimet:
            continue
        elif len(set(aicampaigns[data['campaign']])) != 4:
            continue  # skip campaigns not containing all 4 systems

        lastpublic = "zzz"
        lastmsft = "zzz"
        for c in set(aicampaigns[data['campaign']]):
            if c.startswith("PUBL") and c == min(c, lastpublic):
                lastpublic = c
            if c.startswith("MSFT") and c == min(c, lastmsft):
                lastmsft = c

        if 'PUBL' == sys_a and 'MSFT' == sys_b:
            if data['SystemA'] != lastpublic or data['SystemB'] != lastmsft:
                continue
            bleu["publmsft"].append(data["SacreBLEU_bleu"])

            publ_msft[data['Target']].append(
                (data['campaign'], data['SystemA'], data['SystemB']))
        elif 'PUBL' == sys_a and 'PUBL' == sys_b:
            publ_publ[data['Target']].append(
                (data['campaign'], data['SystemA'], data['SystemB']))
            bleu["publpubl"].append(data["SacreBLEU_bleu"])
        elif 'MSFT' == sys_a and 'MSFT' == sys_b:
            msft_msft[data['Target']].append(
                (data['campaign'], data['SystemA'], data['SystemB']))
            bleu["msftmsft"].append(data["SacreBLEU_bleu"])
        else:
            counter[(data['SystemA'][0:4], data['SystemB'][0:4])] += 1

    alllangs = publ_msft.keys()  # we use intersection
    allowed = []

    # we need the exact set of campaigns to generate indentical numbers
    random.seed(30)
    for lan in alllangs:
        m = min(len(publ_msft[lan]), len(publ_publ[lan]), len(msft_msft[lan]))
        if scenario == "PUBL_MSFT":
            allowed += random.sample(publ_msft[lan], m)
        if scenario == "PUBL_PUBL":
            allowed += random.sample(publ_publ[lan], m)
        if scenario == "MSFT_MSFT":
            allowed += random.sample(msft_msft[lan], m)

    return allowed


def print_paper_macros():
    with open("results/generated_macros.tex", 'w') as f:
        for definition in PAPER_MACROS:
            f.write(
                "\def\{}{{{}}}\n".format(definition, PAPER_MACROS[definition]))


def bold_extreme_values(df, format_string="%.1f", biggest=True):
    if biggest:
        # this is a hack as we are renaming the metrics oftern
        extrema = df != df[df.index.isin(investigated_metrics + list(
            metrics_names.values()))].max()  # drop non metrics values
    else:
        extrema = df != df[df.index.isin(
            investigated_metrics + list(metrics_names.values()))].min()
    bolded = df.apply(lambda x: "\\textbf{%s}" % format_string % x)
    formatted = df.apply(lambda x: format_string % x)

    # round number of examples
    df = formatted.where(extrema, bolded)
    try:
        df['n'] = str(int(float(df['n'])))
    except:
        pass

    return df


def color_clusters(df_formatted, df, columns):
    for col in columns:
        colored = df_formatted[col].apply(
            lambda x: "\\cellcolor{black!15}%s" % x)
        df_formatted[col] = colored.where(df[f'CLUS {col}'], df_formatted[col])

    return df_formatted


def create_plot_with_deltas(df, metric, plot, size=3, human_name="human1",
                            only_problematic=False, savefile=None,
                            language=None):
    if human_name != "human1":
        df = df[df[human_name] != 0]

    if language is not None:
        df = df[(df["Source"] == language) | (df["Target"] == language)]
        if len(df) < 20:
            return
        title = f"{metrics_names[metric]} Δ ({lang_names[language]})"
    else:
        title = metrics_names[metric] + " Δ"

    if hasattr(plot, 'set_title'):
        plot.set_title(title)
    else:
        plot.title(title)

    if only_problematic:
        df = df[np.sign(df[human_name]) != np.sign(df[metric])]

    pearson, _ = pearsonr(df[metric], df[human_name])
    spearman, _ = spearmanr(df[metric], df[human_name])

    if metric == "SacreBLEU_ter_neg":
        # This metric has few outliers that breaks the view a lot
        df = df[df["SacreBLEU_ter_neg"] < 0.5]
        df = df[df["SacreBLEU_ter_neg"] > -0.2]
    if metric == "SacreBLEU_bleu":
        # This metric has few outliers that breaks the view a lot
        df = df[df["SacreBLEU_bleu"] < 20]
    if metric == "SacreBLEU_chrf":
        # This metric has few outliers that breaks the view a lot
        df = df[df["SacreBLEU_chrf"] < 0.17]
    if metric == "ExtendedEditDist_neg":
        # This metric has few outliers that breaks the view a lot
        df = df[df["ExtendedEditDist_neg"] < 0.3]

    # center plot
    border = max(-df[metric].min(), df[metric].max())
    human_border = max(-df[human_name].min(), df[human_name].max())

    plot.scatter([-border, border], [0, 0], color="white", s=1)  # border
    plot.scatter([-border, border], [human_border, -human_border],
                 color="white", s=1)  # border

    # print correlations, move them a bit to avoid touching sides
    plot.annotate("P={:.2f}".format(pearson), (border, -human_border),
                  horizontalalignment='right', verticalalignment='bottom')
    plot.annotate("S={:.2f}".format(spearman), (-border, human_border),
                  horizontalalignment='left', verticalalignment='top')

    df_en = df[df['Target'] == 'ENU']
    plot.scatter(df_en[metric], df_en[human_name], color="green", s=size)

    df_en = df[df['Source'] == 'ENU']
    plot.scatter(df_en[metric], df_en[human_name], color="blue", s=size)

    df_en = df[df['Source'] != 'ENU']
    df_en = df_en[df_en['Target'] != 'ENU']
    plot.scatter(df_en[metric], df_en[human_name], color="red", s=size)

    # do not extend x axis
    plot.margins(x=0)
    plot.axvspan(-border * 1.05, 0, ymin=0.5, ymax=1, alpha=0.1, color='red',
                 lw=0)
    plot.axvspan(0, border * 1.05, ymin=0, ymax=0.5, alpha=0.1, color='red',
                 lw=0)

    if savefile is not None:
        if os.path.isfile(savefile):
            os.remove(savefile)
        plot.savefig(savefile, dpi=600)
        plot.clf()

