# LayerNameReplacer/utils.py

def normalize_layer_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")
