import pandas as pd
import networkx as nx
from collections import Counter

def load_tables(model_dir = 'model'):
    nodes = pd.read_csv(f"{model_dir}/nodes.csv")
    edges = pd.read_csv(f"{model_dir}/edges.csv")
    return nodes, edges

def build_graph(nodes, edges):
    G = nx.DiGraph()
    #nodes
    for n, row in nodes.iterrows():
        attrs = row.drop('id').to_dict()
        G.add_node(row['id'], **attrs)
    #edges
    for n, row in edges.iterrows():
        attrs = row.drop(['source', 'target']).to_dict()
        G.add_edge(row['source'], row['target'], **attrs)
    return G

def summary(G):
    print(f"Number of nodes: {G.number_of_nodes()}, Number of edges: {G.number_of_edges()} ")
    print(Counter(d['stratum'] for n, d in G.nodes(data=True)))
    

if __name__ == "__main__":
    nodes, edges = load_tables()
    G = build_graph(nodes, edges)
    summary(G)

