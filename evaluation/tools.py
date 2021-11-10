import hashlib
from evaluation.paper_resources import *
import pandas as pd
import pickle


# invalid lines are usually those that are not pair-wise across
# all systems in the campaign
def get_valid(system_df):
    return system_df.loc[system_df['valid_line']].reset_index()


# some annotations are missing for some systems,
# in that case remove those sentences as we are doing pair-wise evaluation
def get_equal_pairs(df_a, df_b):
    segid_a = df_a['SegmentID'].to_list()
    segid_b = df_b['SegmentID'].to_list()

    allowed_segids = []
    for seg in segid_a:
        if segid_a.count(seg) == segid_b.count(seg):
            allowed_segids.append(seg)

    return df_a[df_a['SegmentID'].isin(allowed_segids)].reset_index(), df_b[
        df_b['SegmentID'].isin(allowed_segids)].reset_index()


# Annonymization of resources
def hash_string_md5(systemname):
    return hashlib.md5(str(systemname).encode('utf-8')).hexdigest()


def calculate_accuracy(df_orig, human_label, metrics, round_values=True):
    # ignore systems, where human score is 0
    df = df_orig[df_orig[human_label] == 1]
    df = df[metrics]
    if len(df) == 0:
        # if there is no 1 in the array
        return df_orig[metrics].min(), df_orig[human_label] == 0

    # the array contains only zeros and ones, accuracy is therefore mean
    acc = df.mean()

    clusters = calculate_accuracy_cluster(df, acc.idxmax())

    acc = 100 * acc
    if round_values:
        acc = acc.round(1)

    acc['# points'] = len(df)
    return acc, clusters


# based on bootstrap resampling clustering
def calculate_accuracy_cluster(df, best_metric):
    n = 10000
    p_value = 0.05
    size = len(df)

    resamples = []
    # repeat n times
    for n in range(n):
        acc = df.sample(size, replace=True).mean()
        # which metrics outperform best_metric
        resamples.append(acc >= acc[best_metric])

    res_df = pd.DataFrame(resamples)
    clusters = res_df.sum() >= n * p_value
    return clusters


# Loads all annotated data from excel files
# Creates pickle file for faster calculations
def load_data(use_cache=True):
    cache_filename = "data.pickle"
    data = defaultdict(dict)
    if use_cache and os.path.isfile(cache_filename):
        with open(cache_filename, 'rb') as handle:
            data = pickle.load(handle)
    else:
        _, campaigns_list, _ = next(os.walk("public_release"))
        counter = 1
        for campaign in campaigns_list:
            if campaign not in data:
                data[campaign] = defaultdict(dict)
            for _, _, systems_list in os.walk(f"public_release/{campaign}"):
                for system in systems_list:
                    if system not in data[campaign]:
                        data[campaign][system] = defaultdict(dict)
                    print(f"Loading {counter}/{len(systems_list)}")
                    xls = pd.ExcelFile(f"public_release/{campaign}/{system}")
                    for datatype in xls.sheet_names:
                        if datatype in ["hum_annotations",
                                        "hum_only_automatic_metrics"]:
                            data[campaign][system][datatype] = pd.read_excel(
                                xls, datatype)
                        else:
                            df = pd.read_excel(xls, datatype)
                            # transform to dictionary
                            df_dict = df.set_index("Unnamed: 0").transpose()
                            df_dict = df_dict.iloc[0].to_dict()
                            data[campaign][system][datatype] = df_dict
                    counter += 1

        # save the cache data
        if use_cache:
            with open(cache_filename, 'wb') as handle:
                pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)

    print("Annotated data loaded")
    return data


# load precalculated bootstrap scores
def load_boostrap_cache():
    cache_filename = 'final_boostrap.pickle'
    if os.path.isfile(cache_filename):
        with open(cache_filename, 'rb') as handle:
            return pickle.load(handle)
    else:
        return {}


# calculate bootstrap p-value
def bootstrap_get_pvalue(bootstrap_sys_compar, metric, rank_direction):
    assert rank_direction in [-1, 1]
    count = bootstrap_sys_compar[metric].loc[
        bootstrap_sys_compar[metric] == rank_direction].count()
    p_value = 1 - count / len(bootstrap_sys_compar[metric])

    return p_value
