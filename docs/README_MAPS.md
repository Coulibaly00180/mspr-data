# Cartes — communes de Nantes Métropole

Ce projet peut générer une carte du **parti arrivé en tête par commune**. Pour cela, il faut disposer du **GeoJSON** des communes de l'EPCI 244400404 (Nantes Métropole).

## Récupérer le GeoJSON automatiquement
Dans le dossier du projet (hôte) :

```bash
docker compose run --rm app python src/etl/fetch_geojson.py
```

Cela télécharge les **contours des communes** via `geo.api.gouv.fr` et enregistre le fichier :
`data/geo/communes_nantes_metropole.geojson`

## Utiliser la carte dans l'EDA
Ouvrez le notebook `notebooks/02_eda_full.ipynb` et exécutez la section **7) Carte** :
- Choisissez l'année (`YEAR`), le `type_scrutin` (`SCRUTIN`) et le `TOUR` (1 ou 2).
- Le code joint les communes (clé `code_commune_insee`) aux `properties.code` du GeoJSON.

## Format attendu
- GeoJSON `FeatureCollection`
- Chaque `feature.properties` doit contenir `code` (code INSEE de la commune)
- Géométries `Polygon` ou `MultiPolygon`

## Dépannage
- *Clés qui ne joignent pas* : vérifier que `code_commune_insee` est au format **5 chiffres** (`str.zfill(5)`) côté données.
- *Rendu vide* : vérifier que la table ML contient des lignes pour l'année/scrutin/tour choisis.
- *Autres EPCI* : lancer `python src/etl/fetch_geojson.py --epci <CODE_EPCI>`.
