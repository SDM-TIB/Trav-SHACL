# -*- coding: utf-8 -*-
__author__ = "Mónica Figuera"

import pandas as pd
import os
import errno


def read_last(f, sep, fixed=True):
    """Reads the last segment from a file-like object.

    :param f: File to read last line from.
    :type  f: file-like object
    :param sep: Segment separator (delimiter).
    :type  sep: bytes, str
    :param fixed: Treat data in ``f`` as a chain of fixed size blocks.
    :type  fixed: bool
    :returns: Last line of file.
    :rtype  : bytes, str
    """
    bs = len(sep)
    step = bs if fixed else 1
    if not bs:
        raise ValueError("Zero-length separator.")
    try:
        o = f.seek(0, os.SEEK_END)
        o = f.seek(o - bs - step)  # - Ignore trailing delimiter 'sep'.
        while f.read(bs) != sep:  # - Until reaching 'sep': Read data, seek past
            o = f.seek(o - step)  # read data *and* the data to read next.
    except (OSError, ValueError):  # - Beginning of file reached.
        f.seek(0)
    return f.read()[:-1]


def get_time(path):
    """Reads the stats file at the given path and reports the runtime in milliseconds.

    :param path: path of the stats file
    :type: str
    :return: runtime in milliseconds
    :rtype: int
    """
    with open(path + "/stats.txt", "r", encoding="utf8") as file:
        last_line = read_last(file, "\n", False)
        if last_line == '':
            return None  # for empty stats file
        return int(last_line)

def get_best_index(base_path, approach, best_config, dataset_name, dataset, size):
    best = -1
    best_time = prev_time = 100000000000  # random magic number
    for i, run in enumerate(
            os.listdir(os.path.join(base_path, approach, best_config, dataset_name, dataset, size))):
        r = os.path.join(base_path, approach, best_config, dataset_name, dataset, size, run)
        current_time = get_time(r) if get_time(r) is not None else prev_time
        if current_time is None:
            continue
        if current_time <= prev_time:
            best = int(i + 1)
            best_time = current_time
            prev_time = current_time
    return best, best_time

def get_best_runs():
    base_path = "/results"
    best_ds = {
        "lubm_skg_1": {},
        "lubm_skg_2": {},
        "lubm_skg_3": {},
        "lubm_mkg_1": {},
        "lubm_mkg_2": {},
        "lubm_mkg_3": {},
        "lubm_lkg_1": {},
        "lubm_lkg_2": {},
        "lubm_lkg_3": {}
    }

    for approach in os.listdir(base_path):
        if approach == "shacl2sparql" or approach == "shacl2sparql-py":
            for dataset_name in os.listdir(os.path.join(base_path, approach)):
                if not os.path.isdir(os.path.join(base_path, approach, dataset_name)):
                    continue
                for dataset in os.listdir(os.path.join(base_path, approach, dataset_name)):
                    if dataset not in best_ds.keys():
                        continue
                    best_ds[dataset][approach] = {}
                    for size in os.listdir(
                            os.path.join(base_path, approach, dataset_name, dataset)):  # schema1, schema2, schema3
                        best_index, best_time = get_best_index(base_path, approach, '', dataset_name, dataset, size)
                        best_ds[dataset][approach][size] = (
                            os.path.join(base_path, approach, dataset_name, dataset, size, str(best_index)),
                            best_time
                        )

        elif approach == 'travshacl':
            best_config = "config5"
            # for configuration in os.listdir(os.path.join(base_path, approach)):
            for dataset_name in os.listdir(os.path.join(base_path, approach, best_config)):
                if not os.path.isdir(os.path.join(base_path, approach, best_config, dataset_name)):
                    continue
                for dataset in os.listdir(os.path.join(base_path, approach, best_config, dataset_name)):
                    if dataset not in best_ds.keys():
                        continue
                    best_ds[dataset][approach] = {}
                    for size in os.listdir(os.path.join(base_path, approach, best_config, dataset_name,
                                                        dataset)):  # schema1, schema2, schema3
                        best_index, best_time = get_best_index(base_path, approach, best_config, dataset_name, dataset, size)
                        best_ds[dataset][approach][size] = (
                            os.path.join(base_path, approach, best_config, dataset_name, dataset, size, str(best_index)),
                            best_time
                        )
        else:
            continue
		
    return best_ds

def modif_columns(filename, test, approach):
    df = pd.read_csv(filename)
    df["test"] = test
    df["approach"] = approach
    df.columns = ('target', 'answer', 'time', 'test', 'approach')
    times = df["time"]
    df["time"] = [round(t / 1000, 4) for t in times]
    timeFirstFoundTuple = df['time'][df['answer'] == 0].iloc[0] / 1000
    return df, timeFirstFoundTuple, len(times)

def prettify_names(approach):
    if approach == 'shacl2sparql':
        return 'SHACL2SPARQL'
    elif approach == 'shacl2sparql-py':
        return 'SHACL2SPARQL-py'
    else:
        return 'Trav-SHACL 5'

def merge_and_save(ds, size, files):
    if "skg" in ds:
        ds = "SKGs"
    elif "mkg" in ds:
        ds = "MKGs"
    elif "lkg" in ds:
        ds = "LKGs"

    print(size, files)

    file1 = files[0][0]
    file2 = files[1][0]
    file3 = files[2][0]

    approach1 = prettify_names(files[0][1])
    approach2 = prettify_names(files[1][1])
    approach3 = prettify_names(files[2][1])

    df1, tfft1, comp1 = modif_columns(file1, ds, approach1)
    df2, tfft2, comp2 = modif_columns(file2, ds, approach2)
    df3, tfft3, comp3 = modif_columns(file3, ds, approach3)

    totaltimes = [files[0][2] / 1000,
                  files[1][2] / 1000,
                  files[2][2] / 1000]

    approaches = [approach1, approach2, approach3]
    tffts = [tfft1, tfft2, tfft3]
    comps = [comp1, comp2, comp3]

    merged1 = df1.append(df2)
    all_merged = merged1.append(df3)

    filename_trace = "/results/dief_data/" + size + "/traces/all_" + ds + ".csv"
    if not os.path.exists(os.path.dirname(filename_trace)):
        try:
            os.makedirs(os.path.dirname(filename_trace))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    with open(filename_trace, 'w', encoding='utf-8') as f:
        all_merged.to_csv(f, index=False)

    df_metrics = pd.DataFrame({
                   'test': [ds, ds, ds],
                   'approach': approaches,
                   'tfft': tffts,
                   'totaltime': totaltimes,
                   'comp': comps})

    filename_metrics = "/results/dief_data/" + size + "/metrics/" + ds + ".csv"
    if not os.path.exists(os.path.dirname(filename_metrics)):
        try:
            os.makedirs(os.path.dirname(filename_metrics))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    with open(filename_metrics, 'w', encoding='utf-8') as f:
        df_metrics.to_csv(f, index=False)


if __name__ == "__main__":
    runs = get_best_runs()
    for ds, approach in runs.items():
        files_small = []
        files_medium = []
        files_big = []
        for ap, size in approach.items():
            for s, best_val in size.items():
                path = best_val[0]
                totaltime = best_val[1]
                if s == "schema1":
                    if os.path.getsize(path + "/traces.csv") > 0:
                        files_small.append((path + "/traces.csv", ap, totaltime))
                elif s == "schema2":
                    if os.path.getsize(path + "/traces.csv") > 0:
                        files_medium.append((path + "/traces.csv", ap, totaltime))
                else:
                    if os.path.getsize(path + "/traces.csv") > 0:
                        files_big.append((path + "/traces.csv", ap, totaltime))

        if len(files_small) == 3:
            merge_and_save(ds, "schema1", files_small)
        if len(files_medium) == 3:
            merge_and_save(ds, "schema2", files_medium)
        if len(files_big) == 3:
            merge_and_save(ds, "schema3", files_big)
