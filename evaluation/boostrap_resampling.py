import pickle
import os
from evaluation.tools import hashName
from evaluation.SETTINGS import PUBLIC_DATADROP, option_investigate_metrics


def save_boostrap(data):
    with open('cached_boostrap.pickle', 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)


def load_boostrap():
    cache_filename = 'cached_boostrap.pickle'
    if os.path.isfile(cache_filename):
        with open(cache_filename, 'rb') as handle:
            loaded = pickle.load(handle)
    else:
        return {}

    annonymized = {}
    if PUBLIC_DATADROP:
        for bootkey in loaded:
            # only intersection of all metrics and those with bootstrap values
            metrics = loaded[bootkey][list(set(loaded[bootkey].keys()) & set(option_investigate_metrics))]
            annonymized[(hashName(bootkey[0]), hashName(bootkey[1]), hashName(bootkey[2]), bootkey[3])] = metrics
        loaded = annonymized
        with open('final_boostrap.pickle', 'wb') as handle:
            pickle.dump(loaded, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return loaded


def bootstrap_get_pvalue(bootstrap_sys_compar, metric, rank_direction):
    histogram = bootstrap_sys_compar[metric].value_counts()
    assert rank_direction in [-1, 1]
    count = bootstrap_sys_compar[metric].loc[bootstrap_sys_compar[metric] == rank_direction].count()
    p_value = 1 - count/len(bootstrap_sys_compar[metric])

    return p_value
