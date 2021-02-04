import os
from statistics import mean
from statistics import stdev


def readlast(f, sep, fixed=True):
    """Read the last segment from a file-like object.

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
        o = f.seek(o-bs-step)      # - Ignore trailing delimiter 'sep'.
        while f.read(bs) != sep:   # - Until reaching 'sep': Read data, seek past
            o = f.seek(o-step)     # read data *and* the data to read next.
    except (OSError, ValueError):  # - Beginning of file reached.
        f.seek(0)
    return f.read()[:-1]


def validation_time(path):
    """Reads the stats file at the given path and reports the runtime in milliseconds.

    :param path: path of the stats file
    :type: str
    :return: runtime in milliseconds
    :rtype: int
    """
    with open(path + "/stats.txt", "r", encoding="utf8") as file:
        last_line = readlast(file, "\n", False)
#        print(path, last_line)
        return int(last_line)


def get_network(target, shape):
    switcher1 = {
        "lubm_skg_1": "D1",
        "lubm_skg_2": "D2",
        "lubm_skg_3": "D3",
        "lubm_mkg_1": "D4",
        "lubm_mkg_2": "D5",
        "lubm_mkg_3": "D6",
        "lubm_lkg_1": "D7",
        "lubm_lkg_2": "D8",
        "lubm_lkg_3": "D9",
    }

    switcher2 = {
        "lubm_skg_1": "D10",
        "lubm_skg_2": "D11",
        "lubm_skg_3": "D12",
        "lubm_mkg_1": "D13",
        "lubm_mkg_2": "D14",
        "lubm_mkg_3": "D15",
        "lubm_lkg_1": "D16",
        "lubm_lkg_2": "D17",
        "lubm_lkg_3": "D18",
    }

    switcher3 = {
        "lubm_skg_1": "D19",
        "lubm_skg_2": "D20",
        "lubm_skg_3": "D21",
        "lubm_mkg_1": "D22",
        "lubm_mkg_2": "D23",
        "lubm_mkg_3": "D24",
        "lubm_lkg_1": "D25",
        "lubm_lkg_2": "D26",
        "lubm_lkg_3": "D27",
    }

    if shape == "schema1":
        return switcher1.get(target, None)
    elif shape == "schema2":
        return switcher2.get(target, None)
    elif shape == "schema3":
        return switcher3.get(target, None)


if __name__ == "__main__":
    base_path = "/results"
    results = {}
    networks = set()
    for approach in os.listdir(base_path):
        if not os.path.isdir(os.path.join(base_path, approach)):
            continue

        for endpoint in os.listdir(os.path.join(base_path, approach)):
            if not os.path.isdir(os.path.join(base_path, approach, endpoint)):
                continue

            for target in os.listdir(os.path.join(base_path, approach, endpoint)):
                if not os.path.isdir(os.path.join(base_path, approach, endpoint, target)):
                    continue

                for shape in os.listdir(os.path.join(base_path, approach, endpoint, target)):
                    if not os.path.isdir(os.path.join(base_path, approach, endpoint, target, shape)):
                        continue

                    if approach == "shacl2sparql" or approach == "shacl2sparql-py":
                        exec_times = []
                        for run in os.listdir(os.path.join(base_path, approach, endpoint, target, shape)):
                            if not os.path.isdir(os.path.join(base_path, approach, endpoint, target, shape, run)):
                                continue

                            exec_times.append(validation_time(os.path.join(base_path, approach, endpoint, target, shape, run)))

                        network = get_network(target, shape)
                        networks.add(network)
                        if approach not in results.keys():
                            results[approach] = {}
                        if network not in results[approach].keys():
                            results[approach][network] = {}
                            results[approach][network]['times'] = []
                        for x in exec_times:
                            results[approach][network]['times'].append(x)

        if approach == "travshacl":
            for configuration in os.listdir(os.path.join(base_path, approach)):
                if not os.path.isdir(os.path.join(base_path, approach, configuration)):
                    continue

                for endpoint in os.listdir(os.path.join(base_path, approach, configuration)):
                    if not os.path.isdir(os.path.join(base_path, approach, configuration, endpoint)):
                        continue

                    for target in os.listdir(os.path.join(base_path, approach, configuration, endpoint)):
                        if not os.path.isdir(os.path.join(base_path, approach, configuration, endpoint, target)):
                            continue

                        for shape in os.listdir(os.path.join(base_path, approach, configuration, endpoint, target)):
                            if not os.path.isdir(os.path.join(base_path, approach, configuration, endpoint, target, shape)):
                                continue

                            exec_times = []
                            for run in os.listdir(os.path.join(base_path, approach, configuration, endpoint, target, shape)):
                                if not os.path.isdir(os.path.join(base_path, approach, configuration, endpoint, target, shape, run)):
                                    continue
                                print(os.path.join(base_path, approach, configuration, endpoint, target, shape, run))
                                exec_times.append(validation_time(os.path.join(base_path, approach, configuration, endpoint, target, shape, run)))

                            print(exec_times)
                            network = get_network(target, shape)
                            networks.add(network)
                            app_name = approach + "_" + configuration
                            if app_name not in results.keys():
                                results[app_name] = {}
                            if network not in results[app_name].keys():
                                results[app_name][network] = {}
                                results[app_name][network]['times'] = []
                            for x in exec_times:
                                results[app_name][network]['times'].append(x)

    # compute the average and stdev
    for approach in results.keys():
        for network in results[approach].keys():
            times = results[approach][network]['times']
            results[approach][network]['mean'] = mean(times)
            results[approach][network]['stdev'] = stdev(times)

    networks = sorted(networks)
    print(networks)
    print(results)
    with open('/results/results.tsv', "w", encoding="utf8") as out:
        out.write("approach")
        for network in networks:
            out.write("\t" + network)
        out.write("\n")

        for approach in results.keys():
            out.write(approach)
            for network in networks:
                mean = str(results[approach][network]['mean'])
                stdev = str(results[approach][network]['stdev'])
                out.write("\t(" + mean + ", " + stdev + ")")
            out.write("\n")

