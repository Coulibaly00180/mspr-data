import argparse
import os
import sys
import pandas as pd
import numpy as np
from src.common.io import ensure_dir, read_csv_safe, write_csv_safe

# ETL:
# - charge data/raw_csv
# - harmonise schémas et clés
# - joint les indicateurs
# - calcule features (per capita, deltas, vainqueur précédent)
# - exporte data/processed_csv/master_ml.csv

def load_raw(data_dir: str):
    """
    Charge les données brutes à partir des fichiers CSV dans le répertoire spécifié.
    Priorise les fichiers d'élection détaillés (*_par_commune.csv) par rapport aux fichiers maîtres.
    """
    raw = {}
    files = os.listdir(data_dir)
    
    # Collecte et concaténation de tous les fichiers d'élection détaillés par commune.
    # Ces fichiers sont prioritaires car ils contiennent les données les plus granulaires.
    parts = []
    for f in files:
        if "_par_commune.csv" in f:
            parts.append(read_csv_safe(os.path.join(data_dir, f)))
    
    if parts:
        raw["elections_master"] = pd.concat(parts, ignore_index=True)
    else:
        # Si aucun fichier détaillé n'est trouvé, utilise le fichier maître global comme solution de repli.
        cand = [f for f in files if f.lower().startswith("elections_master") and f.lower().endswith(".csv")]
        if cand:
            raw["elections_master"] = read_csv_safe(os.path.join(data_dir, cand[0]))
        else:
            raw["elections_master"] = pd.DataFrame()

    # Charge le fichier des indicateurs socio-économiques.
    ind_cand = [f for f in files if f.lower().startswith("indicateurs_") and f.lower().endswith(".csv")]
    if ind_cand:
        raw["indicateurs"] = read_csv_safe(os.path.join(data_dir, ind_cand[0]))
    else:
        alt = [f for f in files if "indicateur" in f.lower() and f.lower().endswith(".csv")]
        raw["indicateurs"] = read_csv_safe(os.path.join(data_dir, alt[0])) if alt else pd.DataFrame()

    # Charge le fichier des communes de la métropole de Nantes.
    ref_cand = [f for f in files if f.lower().startswith("communes_") and f.lower().endswith(".csv")]
    raw["communes"] = read_csv_safe(os.path.join(data_dir, ref_cand[0])) if ref_cand else pd.DataFrame()

    # Charge le fichier des nuances politiques.
    nu_cand = [f for f in files if f.lower().startswith("nuances_") and f.lower().endswith(".csv")]
    raw["nuances"] = read_csv_safe(os.path.join(data_dir, nu_cand[0])) if nu_cand else pd.DataFrame()

    return raw

def normalize_keys(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardise les noms de colonnes dans un DataFrame pour un ensemble commun de clés.
    Convertit également les colonnes pertinentes aux types de données appropriés et gère la colonne 'estime' manquante.
    """
    if df.empty:
        return df
    # Mappe les noms de colonnes courants à des noms standardisés pour faciliter la jointure et le traitement.
    rename_map = {
        'code_commune_insee':'code_commune_insee',
        'commune_insee':'code_commune_insee',
        'insee_code':'code_commune_insee',
        'code':'code_commune_insee',
        'nom_commune':'nom_commune',
        'commune':'nom_commune',
        'nom':'nom_commune',
        'annee':'annee',
        'year':'annee',
        'type_scrutin':'type_scrutin',
        'tour':'tour',
        'date_scrutin':'date_scrutin',
        'parti_en_tete':'parti_en_tete',
        'estime':'estime'
    }
    out = df.copy()
    # Renomme les colonnes du DataFrame en utilisant la carte de renommage.
    for col in list(df.columns):
        key = col.lower()
        if key in rename_map:
            out.rename(columns={col: rename_map[key]}, inplace=True)
    # Convertit les colonnes numériques et de date aux types appropriés.
    if "annee" in out.columns:
        out["annee"] = pd.to_numeric(out["annee"], errors="coerce").astype("Int64")
    if "tour" in out.columns:
        out["tour"] = pd.to_numeric(out["tour"], errors="coerce").astype("Int64")
    if "date_scrutin" in out.columns:
        out["date_scrutin"] = pd.to_datetime(out["date_scrutin"], errors="coerce")
    # Formate le code INSEE de la commune pour s'assurer qu'il a 5 chiffres (remplit avec des zéros si nécessaire).
    if "code_commune_insee" in out.columns:
        out["code_commune_insee"] = out["code_commune_insee"].astype(str).str.zfill(5)
    # Ajoute une colonne 'estime' si elle n'existe pas, par défaut à False.
    if "estime" not in out.columns:
        out["estime"] = False
    return out

def derive_features(master: pd.DataFrame, indicators: pd.DataFrame) -> pd.DataFrame:
    """
    Dérive de nouvelles caractéristiques et fusionne les indicateurs socio-économiques dans le DataFrame maître.
    Calcule le taux de participation, les pourcentages de votes blancs/nuls, les pourcentages par parti, et détermine
    le parti en tête pour chaque élection. Standardise également les noms de partis et calcule
    le vainqueur précédent.
    """
    if master.empty:
        return master
    # S'assure que les colonnes essentielles pour le traitement existent, sinon les initialise à NaN.
    for c in ["code_commune_insee","nom_commune","annee","type_scrutin","tour"]:
        if c not in master.columns:
            master[c] = np.nan
    # S'assure que les colonnes de résultats de vote existent, sinon les initialise à NaN.
    for need in ["inscrits","votants","blancs","nuls","exprimes"]:
        if need not in master.columns:
            master[need] = np.nan

    # Fonction utilitaire pour calculer un ratio en gérant les divisions par zéro.
    def safe_ratio(a, b):
        b = np.where(b==0, np.nan, b)
        return a / b

    # Calcule le taux de participation et les pourcentages de votes blancs/nuls.
    master["turnout_pct"] = safe_ratio(master["votants"], master["inscrits"])
    master["blancs_pct"] = safe_ratio(master["blancs"], master["votants"])
    master["nuls_pct"]   = safe_ratio(master["nuls"], master["votants"])

    # Calcule les pourcentages de voix pour chaque parti/candidat.
    voix_cols = []
    for col in master.columns:
        if col.startswith('voix_') and not col.startswith('voix_pct_'):
            voix_cols.append(col)
            party_code = col.replace('voix_', '')
            pct_col_name = f'{party_code}_pct'
            if pct_col_name not in master.columns:
                 master[pct_col_name] = safe_ratio(master[col], master['exprimes'])

    # Détermine le parti arrivé en tête (celui avec le plus de voix).
    if 'parti_en_tete' not in master.columns and voix_cols:
        master['parti_en_tete'] = master[voix_cols].idxmax(axis=1).str.replace('voix_', '').str.upper()

    # Standardise les noms des partis politiques en catégories plus larges pour l'harmonisation.
    party_mapping = {
        'FN': 'RN', 'LREM': 'RE', 'VEC': 'EELV', 'SOC': 'PS', 'UDI': 'LR',
        'UMP': 'LR', 'FG': 'LFI', 'FI': 'LFI', 'NUP': 'NUPES', 'ENS': 'RE',
        'COM': 'PCF', 'RDG': 'PRG', 'MDM': 'MODEM', 'UC': 'LR', 'DVD': 'DVD',
        'DVG': 'DVG', 'EXG': 'EXG', 'EXD': 'EXD', 'DIV': 'DIV', 'REG': 'REG',
        'HOLLANDE': 'PS', 'SARKOZY': 'LR', 'MACRON': 'RE', 'MELENCHON': 'LFI',
        'LEPEN': 'RN', 'FILLON': 'LR', 'HAMON': 'PS', 'JADOT': 'EELV',
        'PÉCRESSE': 'LR', 'ZEMMOUR': 'EXD', 'HIDALGO': 'PS', 'ROUSSEL': 'PCF',
        'DUPONT-AIGNAN': 'DLF', 'POUTOU': 'NPA', 'ARTHAUD': 'LO', 'LASSALLE': 'DIV'
    }
    if 'parti_en_tete' in master.columns:
        master['famille_politique'] = master['parti_en_tete'].str.upper().map(party_mapping).fillna(master['parti_en_tete'])


    # Joint les indicateurs socio-économiques au DataFrame principal.
    ind = normalize_keys(indicators.copy())
    join_cols = [c for c in ["code_commune_insee","annee"] if c in ind.columns]
    if len(join_cols)==2:
        ind_cols = [c for c in ind.columns if c not in join_cols + ["nom_commune","code_epci"]]
        master = master.merge(ind[join_cols + ind_cols], on=join_cols, how="left")

    # Trie les données pour permettre le calcul correct des deltas (changements d'indicateurs).
    master = master.sort_values(["code_commune_insee","type_scrutin","annee","tour"])
    # Calcule le delta (changement) des indicateurs socio-économiques d'une année à l'autre.
    for feat in ["population","median_income","unemployment_rate","poverty_rate","security_incidents_per_1000"]:
        if feat in master.columns:
            master[f"{feat}_delta"] = master.groupby(["code_commune_insee","type_scrutin"])[feat].diff()

    # Calcule le vainqueur de l'élection précédente pour chaque commune et type de scrutin.
    if "parti_en_tete" in master.columns:
        master["winner_prev"] = master.groupby(["code_commune_insee","type_scrutin"])["parti_en_tete"].shift(1)

    return master

def main():
    """
    Fonction principale pour exécuter le processus ETL.
    Analyse les arguments, charge les données brutes, les traite et sauvegarde le jeu de données maître.
    """
    ap = argparse.ArgumentParser(description="Build master ML dataset from raw CSVs")
    ap.add_argument("--raw-dir", default="data/raw_csv", help="Input raw CSV directory")
    ap.add_argument("--out", default="data/processed_csv/master_ml.csv", help="Output CSV path")
    args = ap.parse_args()

    raw = load_raw(args.raw_dir)
    elections = normalize_keys(raw["elections_master"])
    indicators = normalize_keys(raw["indicateurs"])

    if elections.empty:
        print("[ERROR] No elections data found in raw dir.", file=sys.stderr)
        sys.exit(2)

    master = derive_features(elections, indicators)

    ensure_dir(os.path.dirname(args.out))
    write_csv_safe(master, args.out, index=False)
    print(f"[OK] Wrote {args.out} with {len(master):,} rows and {len(master.columns)} columns.")


if __name__ == "__main__":
    main()