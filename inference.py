'''
inference.py: inference algorithm that operates over the regulatory network G (from network.py)
G is a signed, directed graph: nodes are biomolecules (M) or physiological processes (P); each edge carries a sign, 
an evidence grade and channel type.
Modes:
-forward: perturb an M node; return the best signed path to each reachable target.
-abductive: from a peripheral observation, trace upstream to its candidate regulators (main mode given evidence from systematic review). 
-footprint: from a set of pertubation of each plant, integrate their signed path acroos the network (M sources forward, P sources abductive).
-metrics: structural exploration (centrality, connectivity, communities, feedback loops).

'''


import networkx as nx
from collections import defaultdict, Counter

pend_grade = 10

def _grade(v):
    '''Parse a grade from a edge to int; if grade missing/non-numeric
    return 'pending_grade = 10 (larger that any real grade (1/3)), so 
    unknown evidence always treated as weakest.
    '''
    try:
        return int(v)
    except (TypeError, ValueError):
        return pend_grade

def _propagation_edges(G, node, reverse=False):
    '''Yield (neighbour, edge_data) pairs through which node propagates.
    If reverse = False list successors (forward), predecessors if True (abductive).
    Skip channel_type "aggregation" edges, so integrators aren't double-counted.
    '''
    if reverse:
        neighbors = G.predecessors(node)
    else:
        neighbors = G.successors(node)
    for nbr in neighbors:
        if reverse:
            data = G[nbr][node]
        else:
            data = G[node][nbr]
        if data.get("channel_type") == "aggregation":
            continue
        yield (nbr, data)

def _enumerate_paths(G, src, cutoff=6, reverse=False):
    '''Enumerate simple paths, from source (src) to cutoff hops (DFS), 
    Accumulates the product of signs and worst (max), grade. reverse=True walks upstream.
    Returns: a list of (target, sign, worst_grade, hops, path) one entry per reachable node.
    '''
    results = []
    #stack = [(node, sign_acum, worst_acum, [path], {nodes visited})]
    stack = [(src, 1, 0, [src], {src})]
    while stack:
        node, sign, worst, path, seen = stack.pop() #unpack the stack
        for nbr, data in _propagation_edges(G, node, reverse):
            if nbr in seen:
                continue
            else:
                s2 = sign * data.get("sign", 0)
                w2 = max(worst, _grade(data.get("grade")))
                p2 = path + [nbr]
                if len(p2)-1 <= cutoff:
                    results.append((nbr, s2, w2, len(p2) - 1, p2))
                    stack.append((nbr, s2, w2, p2, seen | {nbr})) 
    return results

##
def forward(G, src, cutoff=6):
    '''Forward propagation from source (src), keeping the best path per target.
    Best = lowest worst_grade, then fewest hops. 
    Returns: dict {target: {sign, grade, hops, path}}
    '''
    best = {}
    for (tgt, sign, worst, hops, path) in _enumerate_paths(G, src, cutoff):
        cand = (worst, hops)
        if tgt not in best or cand < best[tgt][0]:
            best[tgt] = (cand, sign, worst, hops, path)
    for k in best.keys():
        c, s, w, h, p = best[k]
        best[k] = {"sign":s, "grade":w, "hops":h, "path":p}
    return best

def abductive(G, observed, cutoff=6):
    '''Abductive propagation from peripheral observation up to upstream regulators.
    Enumerates every upstream path (keeps all candidates) and reports
    immediate_inputs = number of direct regulators.
    Returns: dict {"immediate_inputs": int, "candidates": {upstream: [routes]}}
    '''
    routes = _enumerate_paths(G, observed, cutoff, reverse=True)
    candidates = defaultdict(list)
    for (upstream, sign, worst, hops, path) in routes:
        candidates[upstream].append({"sign":sign, "grade":worst, "hops":hops, "path":path})
    immediate_inputs = len(list(_propagation_edges(G, observed, reverse=True)))
    return {"Immediate inputs": immediate_inputs, "candidates": dict(candidates)}


def footprint(G, perturbations, cutoff=5, max_grade=3):
    '''Integrate a plant's perturbations into its network footprint.
    perturbations = dict of effects of plant: {node: initial_sign}, if node
    is molecular target (type M) propagate forward, if physiological process 
    (type P), propagates abductively (reverse). If node from plant does not exist
    in the physiological network, return missing nodes.
    Returns: dict {"footprint": {target: {...}}, "missing nodes": [...]}'''
    dict_footprint = defaultdict(lambda: {"sign": set(), "best_grade": 100, "min_hops": 100, "sources": set(), "via": set(), "paths": [] })
    missing = []
    for src, scr_sign in perturbations.items():
        if src not in G:
            missing.append(src)
            continue
        reverse = (G.nodes[src].get("stratum") == "P")
        for (tgt, sign, worst, hops, path) in _enumerate_paths(G, src, cutoff, reverse=reverse):
            if worst > max_grade:
                continue
            eff = sign * scr_sign
            d = dict_footprint[tgt]
            d["sign"].add(eff)
            d["best_grade"] = min(d["best_grade"], worst)
            d["min_hops"] = min(d["min_hops"], hops)
            d["sources"].add(src)
            d["via"].add(path[-2])
            d["paths"].append(path)
    for tgt in dict_footprint:
        d = dict_footprint[tgt]
        d["net"] = next(iter(d["signs"])) if len(d["signs"]) == 1 else 0
    return {"footprint": dict(dict_footprint), "missing nodes": missing}


def metrics(G):
    '''algo'''
    bt_c = nx.betweenness_centrality(G)
    bt_c = sorted(bt_c.items(), key=lambda kv : kv[1], reverse=True)
    n_in = sorted(G.in_degree(), key=lambda kv : kv[1], reverse=True)
    n_out = sorted(G.out_degree(), key=lambda kv : kv[1], reverse=True)
    comm = nx.community.louvain_communities(G.to_undirected(), seed=0)
    n_comm = len(comm)
    scc = list(nx.strongly_connected_components(G))
    n_scc = nx.number_strongly_connected_components(G)
    wcc = list(nx.weakly_connected_components(G))
    n_wcc = len(wcc)
    cycles = nx.simple_cycles(G)
    loops = [c for c in scc if len(c) > 1]
    islands = [c for c in wcc if len(c) < 10]
    degree_hist = nx.degree_histogram(G)
    print(f"Number of nodes: {G.number_of_nodes()}, Number of edges: {G.number_of_edges()} ")
    print(Counter(d['stratum'] for n, d in G.nodes(data=True)))
    print(f"Top betweenness: {bt_c[:10]}")
    print(f"Top nodes degree in: {n_in[:10]}")
    print(f"Top nodes degree out: {n_out[:10]}")
    print(f"Number of communities: {n_comm}; communities: {comm}")
    # print(f"Connected components: {scc}, NCC {n_scc} ")
    print(f"loops{loops}")
    print(f"islands{islands}")
    print(f" Number of weakly connected components {n_wcc}")
    print(f"cycles {cycles}")

