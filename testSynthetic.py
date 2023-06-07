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
    model_file = './models/Model_barabasi_albert/nrange_150_250_iter_103800.ckpt'

    file_path = './results'

    if not os.path.exists('./results/'):
        os.mkdir('./results/')
    # if not os.path.exists('../results/FINDER_ND/synthetic'):
        # os.mkdir('../results/FINDER_ND/synthetic')
    
    for file in [file for file in os.listdir("input/ba_graph/") if file.endswith('.txt')]:
        with open(f"results/{file}", 'w') as fout:
            val, sol = dqn.Evaluate(f"input/ba_graph/{file}", model_file)
            for i, s in enumerate(sol):
                fout.write(f'{i}, {s}\n')
            fout.flush()
        print(file, "done")

if __name__=="__main__":
    main()
