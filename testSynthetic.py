#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys,os
sys.path.append(os.path.dirname(__file__) + os.sep + '../')
from FINDER import FINDER
from tqdm import tqdm

def main():
    dqn = FINDER()
    data_test_path = './data/synthetic/'
    data_test_name = ['test']
    model_file = './models/Model_dark/nrange_200_200_iter_154500.ckpt'

    file_path = './results'

    if not os.path.exists('./results/'):
        os.mkdir('./results/')

    for i in range(100):
        with open(f"data/ba/finder_node_hist/g_{i}.txt", 'w') as fout:
            val, sol = dqn.Evaluate(f"data/ba/g_{i}", model_file)
            for i, s in enumerate(sol):
                fout.write(f'{i}, {s}\n')
            fout.flush()
        print("done")
        break

if __name__=="__main__":
    main()
