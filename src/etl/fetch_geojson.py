import argparse, os, sys, requests, json
from pathlib import Path

# Download communes GeoJSON contours for Nantes Métropole (EPCI 244400404)
# using geo.api.gouv.fr endpoints. Saves to data/geo/communes_nantes_metropole.geojson
def fetch_epci_communes_geojson(epci_code='244400404'):
    urls = [
        f"https://geo.api.gouv.fr/epcis/{epci_code}/communes?format=geojson&geometry=contour",
        f"https://geo.api.gouv.fr/communes?codeEpci={epci_code}&format=geojson&geometry=contour"
    ]
    last_err = None
    for u in urls:
        try:
            r = requests.get(u, timeout=60)
            r.raise_for_status()
            js = r.json()
            return js
        except Exception as e:
            last_err = e
    raise SystemExit(f'Failed to fetch GeoJSON: {last_err}')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--epci', default='244400404')
    ap.add_argument('--out', default='data/geo/communes_nantes_metropole.geojson')
    args = ap.parse_args()

    js = fetch_epci_communes_geojson(args.epci)
    Path(os.path.dirname(args.out)).mkdir(parents=True, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(js, f, ensure_ascii=False)
    feats = js.get('features', [])
    codes = [ft.get('properties', {}).get('code') for ft in feats]
    print(f'[OK] Saved {len(feats)} features to {args.out}')
    print('Sample codes:', codes[:5])

if __name__ == '__main__':
    main()
