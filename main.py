from collections import defaultdict

from math import ceil
from copy import deepcopy
from constants import *
from models import UE, FCN
from genetic import roga_algorithm
import json

# Create instances of UE
# has to be ordered by primary key
UEs = [
    UE(1, 10, 1, 10, 20, 0.1),
    UE(2, 20, 2, 20, 20, 0.2),
    UE(3, 15, 1.5, 15, 15, 0.15),
    UE(4, 30, 3, 30, 3, 0.3),
    UE(5, 25, 2.5, 25, 2.5, 0.25)
]

# has to be ordered by primary key
FCNs = [
    FCN(1),
    FCN(2),
]


def epsiloon(ue: UE, fcn_id: int):
    return ue.Computation_Resource_fu / (ue.get_Average_Sojourn_Time_tauuf(fcn_id) - ue.get_t_up_uf(fcn_id))


def G_coefficient(yf, incomes):
    sum_yif = 0
    for i in range(len(incomes) - 1):
        yif = 0
        for j in range(i):
            yif += incomes[j][1]
        yif = yif / yf
        sum_yif += yif
    return 1 - 1 / (len(incomes)) * (1 + 2 * sum_yif)


def gini_coefficient_based_fcn_selection(UEs: list[UE], FCNs: list[FCN]):
    selected_ue_s: dict[int, list[int]] = defaultdict(list)
    selected_fcn_s: dict[int, list[int]] = defaultdict(list)
    YF: dict[int, float] = defaultdict(float)
    IF: dict[int, int] = defaultdict(int)
    incomes = defaultdict(list)
    for fcn in FCNs:
        BOR: list[UE] = list()
        # Step 1: Pre-offloading
        for ue in UEs:
            if ue.get_t_up_uf(fcn.pk) < ue.get_Average_Sojourn_Time_tauuf(fcn.pk) and ue.get_q_F_uf(
                    fcn.pk, fcn.Computing_Capacity_cF[ue.pk]
            ) < ue.Q_local:
                BOR.append(ue)
            else:
                print(fcn.pk, ue.get_t_up_uf(fcn.pk), ue.get_Average_Sojourn_Time_tauuf(fcn.pk),
                      ue.get_q_F_uf(fcn.pk, fcn.Computing_Capacity_cF[ue.pk]), ue.Q_local)
        selected_ue_s[fcn.pk] = BOR
        if not BOR: continue
        yf = 0
        for ue in BOR:
            epsilon = epsiloon(ue, fcn.pk)
            weight_factor = (sum([epsiloon(ue, fcn.pk) for ue in BOR]) / (len(BOR) * epsilon)) * (
                    ue.get_Average_Sojourn_Time_tauuf(fcn.pk) / (
                    ue.get_t_up_uf(fcn.pk) + ue.get_t_exe_uf(fcn.Computing_Capacity_cF[ue.pk])))
            income = weight_factor * max(ue.get_Quf(fcn.pk, fcn.Computing_Capacity_cF[ue.pk]), 0)
            incomes[fcn.pk].append((ue.pk, income, epsilon))
            yf += income
        incomes[fcn.pk].sort(key=lambda x: x[1])
        YF[fcn.pk] = yf
        epsilon_mid = sorted(incomes[fcn.pk], key=lambda x: x[2])[len(BOR) // 2]
        L_F = min(K, len(BOR), int(fcn.cF / epsilon_mid[2]))
        G_f = G_coefficient(yf, incomes[fcn.pk])
        IF[fcn.pk] = min(ceil(1 / G_f) + ceil(L_F / len(BOR) * (len(BOR) - ceil(1 / G_f))), len(BOR)) - 1
        # Step 2: Gini Coefficient Calculation
        selected_ue_s[fcn.pk] = incomes[fcn.pk][:IF[fcn.pk]]
        for i in range(IF[fcn.pk]):
            ue, income, eps = incomes[fcn.pk][i]
            selected_fcn_s[ue].append((fcn.pk, income))
    if_copy = {**IF}
    while True:
        enter = False
        copy_selected_fcn_s = deepcopy(selected_fcn_s)
        print(selected_fcn_s)
        for ue_id in selected_fcn_s.keys():
            if len(selected_fcn_s[ue_id]) > 1:
                fcn_pk, income = max(selected_fcn_s[ue_id], key=lambda x: x[1])
                enter = True
                for i, inc in selected_fcn_s[ue_id]:
                    if fcn_pk == i: continue
                    if incomes[i][if_copy[i]] not in selected_ue_s[i]:
                        selected_ue_s[i].append(incomes[i][if_copy[i]])
                        try:
                            copy_selected_fcn_s[incomes[i][if_copy[i]][0]].append((i, inc))
                        except KeyError:
                            copy_selected_fcn_s[incomes[i][if_copy[i]][0]] = [(i, inc)]
                    selected_ue_s[i] = list(filter(lambda x: x[0] != ue_id, selected_ue_s[i]))
                    if len(incomes[i]) - 1 > if_copy[i]:
                        if_copy[i] += 1
                copy_selected_fcn_s[ue_id] = [(fcn_pk, income)]
        selected_fcn_s = deepcopy(copy_selected_fcn_s)
        if not enter: break
    return selected_fcn_s, selected_ue_s


print("Selected UEs Based on Gini Coefficient")
selected_fcn_s, selected_ue_s = gini_coefficient_based_fcn_selection(UEs, FCNs)
with open("./file2.json", "w") as f:
    json.dump(selected_ue_s, f)
with open("./file3.json", "w") as f:
    json.dump(selected_fcn_s, f)

# Getting the EUs and FCNs
ues = []
for selected_fcn in selected_fcn_s.keys():
    ues.append(UEs[selected_fcn - 1])

fcns = []
for selected_ue in selected_ue_s.keys():
    fcns.append(FCNs[selected_ue - 1])

roga_algorithm(FCNs=fcns, UEs=ues, num_generations=10, crossover_rate=0.7, mutation_rate=0.1)
