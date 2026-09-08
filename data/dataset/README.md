# Dataset Deep Bridge

## Source

Donnees reprises du depot public du groupe precedent :

https://github.com/MBDS-ANTENNES-24-25/projets-d-innovation-deepbridge-groupe2-tpi

Fichiers utilises :
- `deep-bridge-data-clean.csv` : 651 patients operes, cible = complication
- `description-colonnes.txt` : description des variables
- README source dans `README_SOURCE_GROUPE2.md`

## Important

Ce CSV contient des **donnees cliniques tabulaires** (age, sexe, technique, anomalies...),
pas des images DICOM.

Les images DICOM patients ne sont pas dans ce depot GitHub public.
Pour la visu DICOM, Deep Bridge garde donc :
- ouverture d'un vrai dossier DICOM local si tu en as un
- mode DEMO synthetique sinon

## Utilisation dans l'appli

1. Lancer Deep Bridge
2. Panneau **Risk Prediction**
3. Charger dataset CSV (auto au demarrage si present)
4. Selectionner un patient / saisir features pre-op
5. Predire le risque de complication (Random Forest)

Entrainement :

```powershell
python scripts/train_risk_model.py
```
