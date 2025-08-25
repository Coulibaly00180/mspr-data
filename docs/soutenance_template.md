---
marp: true
theme: default
paginate: true
footer: "MSPR — Nantes Métropole | 2025-08-21"
---

# Prédire le parti arrivé en tête
### Nantes Métropole (2012–2022)
**POC Data Science — Soutenance**

---
## 1. Contexte & objectifs
- Problématique : prédire le parti arrivé en tête par commune
- Périmètre : EPCI 244400404 (24 communes), 2012–2022
- Sortie : classification multi-classes (parti_en_tete)
- Contraintes : reproductibilité, explicabilité, QA

---
## 2. Données & sources
- Élections : présidentielles, législatives, européennes, municipales
- Indicateurs socio-éco : FILOSOFI, RP/INSEE, SIRENE, RNA, SSMSI
- Référentiels : communes INSEE, nuances politiques
- Table master : `master_ml.csv`

---
## 3. Pipeline (ETL → Features → Modèles)
```mermaid
flowchart LR
  A[CSV bruts] --> B[ETL build_master.py]
  B --> C[master_ml.csv]
  C --> D[Entraînement (train.py)]
  D --> E[Rapports & figures]
```

---
## 4. Qualité de données (exemples)
- Unicité des clés `(commune, scrutin, année, tour)`
- Cohérence `turnout/blancs/nuls` et `Σ voix_pct ≈ 100%`
- Complétude ≥ 95 % des colonnes clés
- Traçabilité & licences

---
## 5. Features
- Indicateurs de contexte (revenu, pauvreté, chômage, densité…)
- Deltas vs scrutin précédent (même type)
- Historique : `winner_prev`, `score_prev_<parti>` (si dispo)
- Encodage catégoriel : `type_scrutin`, `tour`

---
## 6. Jeu d’entraînement & split
- Split **temporel** : train (anciens scrutins) / test (plus récents)
- Baselines : vainqueur précédent, score précédent
- Classes : rééquilibrage si besoin (`class_weight`)

---
## 7. Modèles & métriques
- Logistic Regression (L2, balanced)
- Random Forest (n_estimators, depth)
- Métriques : Accuracy, F1 macro
- Matrice de confusion par classe

---
## 8. Résultats (exemple)
- Accuracy test : `XX %` (RF) ; `YY %` (LR)
- Top features : `median_income`, `turnout_pct`, …
- Observation : stabilité sur communes X/Y/Z

---
## 9. Visualisations
- Évolution `turnout/blancs/nuls` (2012→2022)
- Carte du parti en tête par commune
- Corrélations indicateurs ↔ résultats
- Importance des variables (permutation)

---
## 10. Limites & biais
- Données estimées / millésimes décalés
- Taille d’échantillon
- Effets spécifiques à chaque scrutin

---
## 11. Roadmap
- Remplacer estimations par séries officielles
- Ajouter municipales/législatives manquantes si besoin
- Dashboard (Streamlit/PowerBI)
- SHAP pour interprétabilité fine

---
## 12. Conclusion
- POC valide et réplicable
- Améliorations identifiées
- Go/No-Go et prochaines étapes

---
## Annexes
- Dictionnaire des données
- Schémas ETL
- Paramètres d’entraînement
