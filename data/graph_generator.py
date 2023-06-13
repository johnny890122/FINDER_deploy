#!/usr/bin/env python
# coding: utf-8

# In[2]:


import networkx as nx
import matplotlib.pyplot as plt
from typing import Type
from simulator import CovertGenerator, DarkGenerator
import numpy as np
from tqdm import trange

# In[3]:


def ba_generator(min_n: int=20, max_n: int=30, m: int=2) -> Type[nx.classes.graph.Graph]:
    n = np.random.randint(max_n - min_n + 1) + min_n
    return nx.barabasi_albert_graph(n ,m)

def covert_generator(min_n: int=20, max_n: int=30, density: int=0.1):
    generator = CovertGenerator(min_n, max_n, density)
    generator.simulate()
    return generator.G

def dark_generator(min_n: int=20, max_n: int=30, density: int=0.1):
    generator = DarkGenerator(min_n, max_n, density)
    generator.simulate()
    return generator.G

def write_gml(G: Type[nx.classes.graph.Graph], data_dir: str, file_name: str) -> None:
    nx.write_gml(G, data_dir+file_name)

def read_gml(data_dir: str, file_name: str) -> Type[nx.classes.graph.Graph]:
    G = nx.read_gml(data_dir + file_name)
    return nx.relabel_nodes(G, lambda x: int(x))

def get_real_graph(data_dir: str, file_name: str) -> Type[nx.classes.graph.Graph]:
    return read_gml(data_dir, file_name)


# In[50]:


# output_dir = "./911/"
# file_name = "g_0"
# ba_graph = ba_generator()
# write_gml(ba_graph, output_dir, file_name)
# # G = read_gml(output_dir, file_name)


# In[5]:


# _911_G = get_real_graph(data_dir="./real/", file_name="911")


# In[9]:





# In[20]:


# iters = 100
# for i in range(iters):
#     G = dark_generator(min_n=200, max_n=200, density=0.01)
#     write_gml(G, data_dir="./dark/", file_name=f"g_{i}")


# In[21]:


iters = 100
for i in trange(iters):
    G = covert_generator(min_n=200, max_n=200, density=0.01)
    write_gml(G, data_dir="./covert/", file_name=f"g_{i}")


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




