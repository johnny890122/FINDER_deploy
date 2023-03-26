import networkx as nx

def getRobustness(G, sol):
    G = G.copy()
    GCCsize = len(max(nx.connected_components(G), key=len))
    G.remove_node(sol)
    newGCCsize = len(max(nx.connected_components(G), key=len))
    return (GCCsize - newGCCsize) / ((G.number_of_nodes() * G.number_of_nodes()))

G = nx.barabasi_albert_graph(20, 6)

reward = 0
for i in range(15):
    reward += getRobustness(G, i)
    G.remove_node(i)
    print(reward)

