# Deep Bridge

Projet universitaire – Master MBDS (Universite Cote d'Azur) / cycle ingenieur.

Application Deep Bridge :
- visualisation DICOM (viewer)
- mesures / NASCET / ECST
- pipeline de sortie
- **prediction de risque operatoire** sur le dataset clinique du groupe precedent

> Prototype pedagogique, pas un outil de diagnostic clinique.

## Donnees utilisees

### 1) Dataset clinique (disponible dans le depot groupe 2)

Source :
[projets-d-innovation-deepbridge-groupe2-tpi](https://github.com/MBDS-ANTENNES-24-25/projets-d-innovation-deepbridge-groupe2-tpi)

Fichier local :
`data/dataset/deep-bridge-data-clean.csv` (**651 patients**)

Cible : `complication` (0/1)  
Features pre-operatoires : age, sexe, technique, shunt, anomalie, etc.

Ce dataset sert au module **Risk Prediction** (Random Forest), comme dans le README `tpi-python` du groupe precedent.

### 2) Images DICOM

Les **fichiers DICOM patients ne sont pas dans le depot GitHub public**.  
Donc :
- bouton **Open DICOM** si tu as un dossier local
- bouton **Demo** pour des images synthetiques de test

## Objectifs couverts

- Charger / visualiser DICOM
- Mesures + NASCET/ECST + gravite
- Pipeline de sortie droite/gauche + suggestion
- Risk Prediction supervisee sur CSV clinique reel
- Etiquetage / export rapport

## Installation

```powershell
cd deep_bridge
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/train_risk_model.py
python -m app.main
```

## Utilisation rapide

1. `python -m app.main`
2. **Demo** (visu DICOM de test)
3. Panneau **Risk Prediction** :
   - dataset CSV charge automatiquement
   - choisir un patient
   - **Predire risque de complication**
4. Panneau **Pipeline d'analyse** pour NASCET / suggestion

## Entrainement risque

```powershell
python scripts/train_risk_model.py
```

## Tests

```powershell
pytest
```

## Structure

```text
app/
  dicom/ imaging/ carotid/ ml/ ui/
data/
  dataset/   # CSV clinique groupe2
  demo/      # DICOM synthetiques
  models/    # Random Forest entraine
docs/
scripts/
```

## Limites

- pas de DICOM patients dans le repo public
- Risk Prediction = modele de recherche sur CSV
- suggestions non cliniques
