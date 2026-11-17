# Project: Network Physiology 

A network model that couples multi-target phytotherapeutic agents to physiological regulatory processes, grounded in an integrative, systems-medicine view of human physiology

The model is a signed, directed graph (networkx DiGraph) over two strata: biomolecules (M: hormones,enzymes, neurotransmitters) and physiological processes (P), with edges carrying a sign (activation/inhibition), a level of evidence grade and a channel type. A plant enters as a set of documented perturbations (from a systematic review); an inference engine propagates them across the network to surface its regulatory footprint, incluiding non-obvious cross-system effects. 

**Analysis**
- Centrality(in/out degree, betweeeness) to identify central regulators and bridges.
- Community detection (Louvain) to recover functional modules.
- Signed feedbacks loops fromm the product of edge signs along simple cycles, separating homeostatic (negative) from destabilizaing (positive) loops.

Work in progress. 