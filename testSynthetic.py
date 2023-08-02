#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys,os
sys.path.append(os.path.dirname(__file__) + os.sep + '../')
from FINDER import FINDER
from tqdm import tqdm

def main():
    dqn = FINDER()
    # model_file = './models/Model_barabasi_albert/nrange_200_200_iter_154500.ckpt'
    model_file = './models/Model_dark/nrange_200_200_iter_464100.ckpt'

    for i in range(100):
        with open(f"data/dark/finder_node_hist/g_{i}.txt", 'w') as fout:
            val, sol = dqn.Evaluate(f"data/dark/g_{i}", model_file)
            for i, s in enumerate(sol):
                fout.write(f'{i}, {s}\n')
            fout.flush()
        print("done")

if __name__=="__main__":
    main()
