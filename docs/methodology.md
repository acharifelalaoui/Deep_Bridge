# Méthodologie – Deep Bridge

## Contexte médical (cours / projet)

La sténose carotidienne est un rétrécissement artériel.  
NASCET et ECST sont des façons classiques d’exprimer un pourcentage à partir de diamètres.

Dans ce projet, on n’automatise pas le diagnostic : on aide à visualiser et à calculer à partir de mesures saisies.

## Formule NASCET

```text
% = 100 * (1 - D_stenose / D_reference)
```

Pour ECST, on utilise un diamètre de référence de type “bulbe estimé” saisi par l’utilisateur.

## Étapes du proto

1. Charger les DICOM
2. Trier / regrouper les séries
3. Afficher avec window/level
4. Mesurer
5. Calculer le %
6. Exporter un rapport

## IA (plus tard)

Pour entraîner un modèle, il faudrait notamment :

- images + identifiants anonymisés
- labels (côté carotide, ROI ou masques)
- éventuellement un grade de sténose
- un split train/val/test **par patient**

Pour l’instant, seule l’architecture est en place.
