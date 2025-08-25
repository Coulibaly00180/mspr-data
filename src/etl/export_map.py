import argparse, json, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection

def load_master(path):
    return pd.read_csv(path)

def load_geojson(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_winners(df, year, scrutin_sub, tour):
    # columns we need
    need = [c for c in ['code_commune_insee','annee','type_scrutin','tour','parti_en_tete'] if c in df.columns]
    sub = df[need].dropna()
    sub = sub[(sub['annee'] == year) & (sub['type_scrutin'].str.contains(scrutin_sub, case=False, na=False))]
    if 'tour' in sub.columns and tour is not None:
        sub = sub[sub['tour'] == tour]
    return sub.set_index('code_commune_insee')['parti_en_tete'].to_dict()

def render_map(geojson, winners, title, out_png):
    partis = sorted(set([p for p in winners.values() if isinstance(p, str) and len(p)>0]))
    parti_to_id = {p:i for i,p in enumerate(partis)}

    patches, vals = [], []
    for ft in geojson.get('features', []):
        props = ft.get('properties', {})
        code = str(props.get('code', '')).zfill(5)
        geom = ft.get('geometry', {})
        if not code or not geom:
            continue
        polys = []
        if geom.get('type') == 'Polygon':
            polys = [geom['coordinates']]
        elif geom.get('type') == 'MultiPolygon':
            polys = geom['coordinates']
        pid = parti_to_id.get(winners.get(code, None), None)
        for poly in polys:
            if not poly: 
                continue
            ring = poly[0]
            patches.append(MplPolygon(ring, closed=True))
            vals.append(pid if pid is not None else np.nan)

    fig, ax = plt.subplots(figsize=(8,8))
    pc = PatchCollection(patches, alpha=0.85)
    if len(vals):
        arr = np.array([v if v==v else -1 for v in vals])
        # Normalize to [0,1] ignoring -1 (no explicit colormap per instructions)
        if np.any(arr>=0):
            vmax = max(arr[arr>=0]) or 1
            normed = np.where(arr>=0, (arr / max(vmax,1)), 0.0)
            pc.set_array(normed)
    ax.add_collection(pc)
    ax.autoscale_view()
    ax.set_aspect('equal', 'box')
    ax.set_title(title)
    # Legend proxy (text-only, as we're using default colormap without explicit colors)
    legend_text = "\n".join(f"{i}: {p}" for p,i in parti_to_id.items())
    ax.text(1.01, 0.5, legend_text, transform=ax.transAxes, va='center')
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()
    return parti_to_id

def main():
    ap = argparse.ArgumentParser(description="Export PNG map of 'parti en tête' by commune")
    ap.add_argument("--data", default="data/processed_csv/master_ml.csv", help="Path to master CSV")
    ap.add_argument("--geojson", default="data/geo/communes_nantes_metropole.geojson", help="GeoJSON path")
    ap.add_argument("--year", type=int, required=True, help="Year to plot (e.g., 2022)")
    ap.add_argument("--scrutin", default="presidentielle", help="Substring match for type_scrutin (e.g., 'presidentielle')")
    ap.add_argument("--tour", type=int, default=1, help="Round (1 or 2)")
    ap.add_argument("--out", default="reports/figures/map_parti_en_tete.png", help="Output PNG")
    args = ap.parse_args()

    df = load_master(args.data)
    gj = load_geojson(args.geojson)
    winners = build_winners(df, args.year, args.scrutin, args.tour)
    title = f"Parti en tête — {args.year}, {args.scrutin} T{args.tour}"
    parti_to_id = render_map(gj, winners, title, args.out)
    print(f"[OK] Map saved to {args.out}")
    print("[INFO] Legend mapping (index -> parti):", {i:p for p,i in parti_to_id.items()})

if __name__ == "__main__":
    main()
