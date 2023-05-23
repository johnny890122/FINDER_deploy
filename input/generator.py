import networkx as nx

graph_type = "ba_graph"

if graph_type == "ba_graph":
	size = {
		"low": {"n": 100, "m": 1}, 
		"high": {"n": 400, "m": 4}
	}
	density = {
		"low": {"n": 200, "m": 1}, 
		"high": {"n": 200, "m": 4}
	}

	for i in range(5):
		for key in ["low", "high"]:
			G_for_size = nx.barabasi_albert_graph(n=size[key]["n"], m=size[key]["m"])
			G_for_density = nx.barabasi_albert_graph(n=density[key]["n"], m=density[key]["m"])

			nx.write_edgelist(G_for_size, "ba/size_{}_{}.txt".format(key, i), data=False)
			nx.write_edgelist(G_for_density, "ba/density_{}_{}.txt".format(key, i), data=False)

elif graph_type == "covert":
	pass
elif graph_type == "dark":
	pass
else:
	raise NotImplementedError()