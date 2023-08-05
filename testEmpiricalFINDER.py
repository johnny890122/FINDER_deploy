#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys,os
sys.path.append(os.path.dirname(__file__) + os.sep + '../')
from FINDER import FINDER
from tqdm import tqdm

model_mapping = {
    'DOMESTICTERRORWEB.gml': 2, 'suicide.gml': 2, 'MAIL.gml': 2,
    'HAMBURG_TIE_YEAR.gml': 4, 
    'HEROIN_DEALING.gml': 5,
}

mapping = {
    2: 'DOMESTICTERRORWEB.gml', 
    3: 'suicide.gml', 4: 'HAMBURG_TIE_YEAR.gml',
    5: 'HEROIN_DEALING.gml', 
    7: 'MAIL.gml', 
}

if not os.path.exists(f"./empirical_data/finder_node_hist"):
    os.mkdir(f"./empirical_data/finder_node_hist")

if not os.path.exists(f"./empirical_data/finder_reward_hist"):
    os.mkdir(f"./empirical_data/finder_reward_hist")

def main(dqn, model, file_idx):
    assert model in ["ba", "dark", "covert"]
    model_alias = model if model != "ba" else "barabasi_albert"
    data_file = f"./empirical_data/{mapping[file_idx]}"
    model_file = f'./models/Model_{model_alias}/{model}{model_mapping[mapping[file_idx]]}.ckpt'

    with open(f"./empirical_data/finder_node_hist/{model}_{file_idx}.txt", 'w') as fout:
        val, sol = dqn.Evaluate(data_file, model_file)
        for i, s in enumerate(sol):
            fout.write(f'{i}, {s}\n')
        fout.flush()
    print("done")

if __name__=="__main__":
    dqn = FINDER()
    for method in ["ba", "dark", "covert"]:
        for file_idx, file_name in mapping.items():
            print(method, file_name)
            main(dqn, method, file_idx)
            




