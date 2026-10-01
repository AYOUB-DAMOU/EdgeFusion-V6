def load_excel(file_path):
    """
    Lit le fichier Excel et retourne les données de configuration des tags.

    Colonnes supportées :
    - Tag       (obligatoire) : Node ID OPC UA
    - Mapping   (optionnel)   : Clé MQTT personnalisée
    - Topic     (optionnel)   : Sous-topic MQTT spécifique
    - Operation (optionnel)   : Opération mathématique (+, -, ×, ÷)
    - Value     (optionnel)   : Nombre fixe ou node_id d'un autre tag

    Retourne un dict :
    {
        "tags"       : [liste node IDs],
        "tag_topics" : {node_id: topic},
        "tag_mapping": {node_id: mqtt_key},
        "tag_operations": {node_id: {"op": "+", "val": "10"}},
        "summary"    : "3 tags | 2 topics | 1 mappés | 1 opérations"
    }
    """
    import pandas as pd
    df = pd.read_excel(file_path)

    if "Tag" not in df.columns:
        raise ValueError("Colonne 'Tag' manquante dans le fichier Excel")

    df = df.dropna(subset=["Tag"])
    df = df[df["Tag"].astype(str).str.startswith("ns=")]
    tags = df["Tag"].tolist()

    # Colonne Topic
    tag_topics = {}
    if "Topic" in df.columns:
        tag_topics = {
            row["Tag"]: str(row["Topic"]).strip()
            for _, row in df.iterrows()
            if pd.notna(row.get("Topic")) and str(row.get("Topic")).strip() != ""
        }

    # Colonne Mapping
    tag_mapping = {}
    if "Mapping" in df.columns:
        tag_mapping = {
            row["Tag"]: str(row["Mapping"]).strip()
            for _, row in df.iterrows()
            if pd.notna(row.get("Mapping")) and str(row.get("Mapping")).strip() != ""
        }

    # Colonnes Operation + Value
    tag_operations = {}
    if "Operation" in df.columns and "Value" in df.columns:
        for _, row in df.iterrows():
            op  = str(row.get("Operation", "")).strip() if pd.notna(row.get("Operation")) else ""
            val = str(row.get("Value",     "")).strip() if pd.notna(row.get("Value"))     else ""
            if op and val:
                tag_operations[row["Tag"]] = {"op": op, "val": val}

    summary = (
        f"{len(tags)} tags  |  {len(tag_topics)} topics  "
        f"|  {len(tag_mapping)} mappés  |  {len(tag_operations)} opérations"
    )

    return {
        "tags":           tags,
        "tag_topics":     tag_topics,
        "tag_mapping":    tag_mapping,
        "tag_operations": tag_operations,
        "summary":        summary
    }
