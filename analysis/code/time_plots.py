import matplotlib
import matplotlib.pyplot as plt
matplotlib.rcParams.update({'errorbar.capsize': 5})


def create_plot(title, datasets, results):
    x = [0, 1, 2]
    color = ["#20639B", "#5DD39E", "#121212", "#D5717F", "#AA14E1", "#E12C14", "#E18314", "#EBEE11", "#41947F", "#FFFFAB", "#D3D3D3"]
    labels = datasets

    plt.xticks(x, labels, rotation=0, fontsize='large')
    plt.yticks(fontsize='large')
    fig = plt.gcf()
    ax = plt.gca()
    ax.set_xlabel("Validated Data Sets", fontsize='large')
    ax.set_ylabel("Validation Time [s]", fontsize='large')
    ax.set_title(title, fontsize='x-large')

    # SHACL2SPARQL
    data_s2s = [float(results[ds]["shacl2sparql"]["mean"])/1000 for ds in datasets]
    err_s2s = [float(results[ds]["shacl2sparql"]["stdev"])/1000 for ds in datasets]
    ax.errorbar([x1 - 0.375 for x1 in x], data_s2s, yerr=err_s2s, fmt='o', color="#d7c841", label="SHACL2SPARQL") # or #f0bf44

    # S2S-py
    data = [float(results[ds]["shacl2sparql-py"]["mean"])/1000 for ds in datasets]
    err = [float(results[ds]["shacl2sparql-py"]["stdev"])/1000 for ds in datasets]
    ax.errorbar([x1 - 0.3 for x1 in x], data, yerr=err, fmt='o', color="#d85e62", label="SHACL2SPARQL-py") # or #c17471

    # 1: BFS IN BIG
    data = [float(results[ds]["travshacl_config1"]["mean"])/1000 for ds in datasets]
    err = [float(results[ds]["travshacl_config1"]["stdev"])/1000 for ds in datasets]
    ax.errorbar([x1 - 0.225 for x1 in x], data, yerr=err, fmt='o', color=color[2], label="Trav-SHACL 1")

    # 2: BFS IN SMALL
    data = [float(results[ds]["travshacl_config2"]["mean"])/1000 for ds in datasets]
    err = [float(results[ds]["travshacl_config2"]["stdev"])/1000 for ds in datasets]
    ax.errorbar([x1 - 0.15 for x1 in x], data, yerr=err, fmt='o', color=color[1], label="Trav-SHACL 2")

    # 3: BFS OUT BIG
    data = [float(results[ds]["travshacl_config3"]["mean"])/1000 for ds in datasets]
    err = [float(results[ds]["travshacl_config3"]["stdev"])/1000 for ds in datasets]
    ax.errorbar([x1 - 0.075 for x1 in x], data, yerr=err, fmt='o', color=color[4], label="Trav-SHACL 3")

    # 4: BFS OUT SMALL
    data = [float(results[ds]["travshacl_config4"]["mean"])/1000 for ds in datasets]
    err = [float(results[ds]["travshacl_config4"]["stdev"])/1000 for ds in datasets]
    ax.errorbar(x, data, yerr=err, fmt='o', color="#264653", label="Trav-SHACL 4")

    # 5: DFS IN BIG
    data = [float(results[ds]["travshacl_config5"]["mean"])/1000 for ds in datasets]
    err = [float(results[ds]["travshacl_config5"]["stdev"])/1000 for ds in datasets]
    ax.errorbar([x1 + 0.075 for x1 in x], data, yerr=err, fmt='o', color="#90c0d6", label="Trav-SHACL 5")

    # 6: DFS IN SMALL
    data = [float(results[ds]["travshacl_config6"]["mean"])/1000 for ds in datasets]
    err = [float(results[ds]["travshacl_config6"]["stdev"])/1000 for ds in datasets]
    ax.errorbar([x1 + 0.15 for x1 in x], data, yerr=err, fmt='o', color=color[6], label="Trav-SHACL 6")

    # 7: DFS OUT BIG
    data = [float(results[ds]["travshacl_config7"]["mean"])/1000 for ds in datasets]
    err = [float(results[ds]["travshacl_config7"]["stdev"])/1000 for ds in datasets]
    ax.errorbar([x1 + 0.225 for x1 in x], data, yerr=err, fmt='o', color=color[8], label="Trav-SHACL 7")

    # 8: DFS OUT SMALL
    data = [float(results[ds]["travshacl_config8"]["mean"])/1000 for ds in datasets]
    err = [float(results[ds]["travshacl_config8"]["stdev"])/1000 for ds in datasets]
    ax.errorbar([x1 + 0.3 for x1 in x], data, yerr=err, fmt='o', color="#9c6e1a", label="Trav-SHACL 8")

    # 9: Random
    data = [float(results[ds]["travshacl_config9"]["mean"])/1000 for ds in datasets]
    err = [float(results[ds]["travshacl_config9"]["stdev"])/1000 for ds in datasets]
    ax.errorbar([x1 + 0.375 for x1 in x], data, yerr=err, fmt='o', color=color[10], label="Trav-SHACL 9")

    plt.legend(title="Engine", loc='upper left', bbox_to_anchor=(1.0, 1.0), fontsize='small')
    plt.tight_layout()
    fig.savefig("/results/plots/exec-time/execution_time_" + title.replace(" ", "").lower() + ".png", dpi=300, bbox_inches='tight')
    plt.cla()
    plt.clf()


if __name__ == "__main__":
    # load the result data into memory
    with open('/results/results.tsv', 'r', encoding='utf8') as resf:
        line = resf.readline()
        header = line.split('\t')
        results = dict()

        line = resf.readline()
        while line:
            content = line.split('\t')
            approach = content[0]
            for i, c in enumerate(content):
                if i > 0:
                    #                dataset = "Schema1SKGs"
                    dataset = header[i].replace("\n", "").strip()
                    res = c.replace("\n", "")[1:-1].split(",")

                    if dataset not in results.keys():
                        results[dataset] = {}

                    if approach not in results[dataset].keys():
                        results[dataset][approach] = {"mean": res[0], "stdev": res[1].strip()}

            line = resf.readline()

    # print the execution time plots
    create_plot("Schema 1 SKGs", ["D1", "D2", "D3"], results)
    create_plot("Schema 2 SKGs", ["D10", "D11", "D12"], results)
    create_plot("Schema 3 SKGs", ["D19", "D20", "D21"], results)

    create_plot("Schema 1 MKGs", ["D4", "D5", "D6"], results)
    create_plot("Schema 2 MKGs", ["D13", "D14", "D15"], results)
    create_plot("Schema 3 MKGs", ["D22", "D23", "D24"], results)

    create_plot("Schema 1 LKGs", ["D7", "D8", "D9"], results)
    create_plot("Schema 2 LKGs", ["D16", "D17", "D18"], results)
    create_plot("Schema 3 LKGs", ["D25", "D26", "D27"], results)
