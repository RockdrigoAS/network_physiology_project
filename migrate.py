"""
migrate.py — converts legacy CSV files (5 node files + 3 edge files, in Spanish)
into two unified tables in English: model/nodes.csv and model/edges.csv.

"""
import pandas as pd
import os

DATA = "data_framework"     # directory containing the legacy CSV files
os.makedirs('model_data', exist_ok=True)
OUT  = "model_data"    # output directory 


# 
# Spanish/English translation map (translation_map.csv: spanish,english,kind)

trans_pd = pd.read_csv(os.path.join(DATA, 'translation_map.csv'))

tr = dict(zip(trans_pd['spanish'], trans_pd['english']))

def t(x):
    """Translates a value; if it is not in the map, it leaves it unchanged (and issues a warning)."""
    if pd.isna(x):
        return x
## if x is not in tr, print a warning ("no translation: ...") so you can catch it
    if x not in tr:
        print('no translation: ', x)
    return tr.get(x, x)
print(pd.Series(tr).head())


#######################


# target schema
node_cols = ["id", "stratum", "module", "type", "role", "readout_axis", "compartment", "notes"]
edge_cols = ["source", "target", "sign", "grade", "channel_type", "route_level", "mechanism", "status", "evidence"]

########################
# NODES
########################

# Configuration per file: (name, {old_column: new_column}, fixed_stratum, fixed_module)
# fixed_module=None means "translate the 'module' column already present in the file." 
node_files = [
("red_S_nodos.csv",                  {"nodo": "id", "modulo": "module", "readout_eje": "readout_axis"}, "S", None),
("bloque01_redox_nodosS.csv",        {"nodo_S": "id", "tipo": "type"},                                  "S", "Redox"),
("pv1_nodos_P_core.csv",             {"nodo_P": "id", "sistema": "module", "tipo": "type"},             "P", None),
("bloque01_redox_nodosP.csv",        {"nodo_P": "id", "compartimento": "compartment"},                  "P", "Redox"),
("bloque02_hepatobiliar_nodosP.csv", {"nodo_P": "id", "tipo": "type"},                                  "P", "Hepatobiliary"),
]

def load_nodes(fname, colmap, stratum, module_fijo):
    """Returns a DataFrame with exactly the columns specified in node_cols, using English names."""
    df = pd.read_csv(os.path.join(DATA, fname))
    #
    df = df.rename(columns=colmap)
    # 
    df["stratum"] = stratum
    #  
    if module_fijo is not None:
        df["module"] = module_fijo # redox, hepatobiliar: fixed module
    else:
        df["module"] = df["module"].map(t) # 
    #  
    for col in node_cols:
        if col not in df.columns:
            df[col] = pd.NA
    # 
    df["id"] = df["id"].map(t)
    df["readout_axis"] = df["readout_axis"].map(t)
    #
    df["role"] = df["readout_axis"].notna().map({True: "readout", False: "internal"})
    # 
    return df[node_cols]


def build_nodes():
    ''' . '''
    #  
    dfs = []
    for cfg in node_files:
        df = load_nodes(*cfg)
        dfs.append(df)
    nodes = pd.concat(dfs, ignore_index=True)
    #
    mask = ~nodes["id"].str.startswith("__DROP__")
    nodes = nodes[mask]
    #
    nodes = drop_duplicates(subset="id", keep="last")
    return nodes


#############################

# prueba = load_nodes("red_S_nodos.csv", {"nodo":"id","modulo":"module","readout_eje":"readout_axis"}, "S", None)
# prueba.head(10)

nodes = build_nodes()
print(len(nodes))
print(nodes["stratum"].value_counts())
print(nodes)




########################
# EDGES
########################

EDGE_FILES = [
("red_S_aristas.csv",                 {"origen": "source", "destino": "target", "signo": "sign",
"tier": "grade", "mecanismo": "mechanism", "estado": "status"}),
("bloque01_redox_aristas.csv",        {"origen": "source", "destino": "target", "signo": "sign", "tier": "grade",
"nivel_ruta": "route_level", "mecanismo": "mechanism", "estado": "status"}),
("bloque02_hepatobiliar_aristas.csv", {"origen": "source", "destino": "target", "signo": "sign", "tier": "grade",
"nivel_ruta": "route_level", "mecanismo": "mechanism", "estado": "status"}),
]
SIGN = {"+": 1, "-": -1, "±": 0, "+/-": 0}

def load_edges(fname, colmap):
    ''' . '''
    df = pd.read_csv(os.path.join(DATA, fname))
    # 
    df = df.rename(columns=colmap)
    #
    if "sign" in df.columns:
        df["sign"] = df["sign"].map(SIGN)
    # 
    if "grade" in df.columns:
        df["grade"] = pd.to_numeric(df["grade"], errors="coerce").astype(object).where(pd.notna, None)
    # 
    df["status"] = "proposed"
    # 
    for col in ["source", "target"]:
        if col in df.columns:
            # Remove whitespace and suffixes 
            df[col] = df[col].astype(str).str.replace(r"\s*\(entrada\)", "", regex=True).str.strip()
            df[col] = df[col].map(t)
    # 
    for col in edge_cols: 
        if col not in df.columns: 
            df[col] = pd.NA 
    return df[edge_cols]


def build_edges(valid_ids): 
    """valid_ids = set of ids that exist in nodes.csv (to throw away undeclared endpoints).""" 
    # 
    dfs = [] 
    for cfg in EDGE_FILES: 
        df = load_edges(*cfg) 
        dfs.append(df) 
    edges = pd.concat(dfs, ignore_index=True) 
    # 
    mask = edges["source"].isin(valid_ids) & edges["target"].isin(valid_ids) 
    edges = edges[mask].copy() 
    return edges

# edges = build_edges(valid_ids=set(nodes["id"]))
# print(len(edges))
# print(edges["grade"].value_counts(dropna=False))


########################
########################

if __name__ == "__main__": 
    os.makedirs(OUT, exist_ok=True) 
    nodes = build_nodes() 
    # 
    edges = build_edges(valid_ids=set(nodes["id"])) 
    # 
    nodes.to_csv(os.path.join(OUT, "nodes.csv"), index=False) 
    edges.to_csv(os.path.join(OUT, "edges.csv"), index=False) 
    print("saved in", OUT) 
    print("Migration complete.")