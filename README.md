Project: Network Physiology of Endobiogeny
A Python notebook for the construction, analysis, and visualization of a knowledge-based physiological regulatory network, grounded in the clinical theory of endobiogeny.

Leveraging the networkx library, the pipeline builds a signed, directed graph (DiGraph) where nodes represent physiological entities (e.g., hormones, organs) and edges represent regulatory interactions (+1 for activation, -1 for inhibition).

The analysis framework includes:

Structural Analysis: Identification of key nodes via centrality metrics (in-degree, out-degree, betweenness centrality) and detection of functional modules using the Louvain community detection algorithm.

Regulatory Dynamics: Identification of positive (destabilizing) and negative (homeostatic) feedback loops by analyzing the product of edge signs along the graph's simple cycles.

Key outputs include ranked lists of critical nodes (top regulators, bridges), identified feedback loops, and graph visualizations with nodes colored by community and edges colored by sign, revealing the system's structural and dynamic organization. The framework is designed with the future goal of expanding into a multilayered network model.
