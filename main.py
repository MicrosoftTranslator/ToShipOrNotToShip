#!/usr/bin/env python
# -*- coding: utf-8 -*-
from evaluation.tools import load_data, load_boostrap_cache
from evaluation.SETTINGS import scenarios, lang_names
from evaluation.analysis import compute_statistics_for_eval, \
    generate_accuracy_results
from evaluation.paper_resources import generate_list_of_languages, \
    generate_various_scenarios, PAPER_MACROS, print_paper_macros
import pickle
from statistics import median
from pathlib import Path
import os


if __name__ == "__main__":
    # create folder for results if not exists
    Path("results").mkdir(parents=True, exist_ok=True)

    # you shouldn't use cache if you do any changes to the calculations like
    # selecting different set of metrics
    use_statdata_cache = True

    data = load_data()

    _, language_pairs = generate_list_of_languages(data)

    stat_cache_filename = "statistical_data.pickle"
    if use_statdata_cache and os.path.isfile(stat_cache_filename):
        with open(stat_cache_filename, 'rb') as handle:
            stat_data = pickle.load(handle)
    else:
        bootstrap = load_boostrap_cache()
        stat_data = compute_statistics_for_eval(data, bootstrap)
        with open(stat_cache_filename, 'wb') as handle:
            pickle.dump(stat_data, handle, protocol=pickle.HIGHEST_PROTOCOL)

    bleu_diffs = []
    for processed_data in stat_data:
        hum = 1 if processed_data['human1'] >= 0 else -1
        bleu = 1 if processed_data['SacreBLEU_bleu'] >= 0 else -1

        if processed_data['human0.05'] != 0 and hum != bleu:
            bleu_diffs.append(abs(processed_data['SacreBLEU_bleu']))

    PAPER_MACROS['bleumismatchcount'] = len(bleu_diffs)
    PAPER_MACROS['bleumismatchmedian'] = round(median(bleu_diffs), 1)

    for scenario in scenarios:
        generate_accuracy_results(stat_data, scenario)

    generate_various_scenarios(
        {'MSFT_MSFT': "Dependent", 'PUBL_MSFT': "Independent"}, "dependent")

    # calculate accuracies for all language pairs
    langpairs_to_accumulate = {}
    for language_pair in language_pairs.keys():
        if language_pairs[language_pair] > 20:
            src = language_pair[0]
            trg = language_pair[1]
            pair = f"{src}-{trg}"
            named_pair = f"{lang_names[src]} - {lang_names[trg]}"
            langpairs_to_accumulate[pair] = named_pair
            generate_accuracy_results(stat_data, pair)
    generate_various_scenarios(langpairs_to_accumulate,
                               "individual_language_pairs", p_value='0.05')

    # generate tables from paper
    generate_various_scenarios()
    print_paper_macros()
