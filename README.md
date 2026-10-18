# LNX Vision

Plateforme d'analyse de réseaux d'entités : une API FastAPI construit un graphe à partir de données tabulaires, et une interface web (HTML) permet de l'explorer (graphe, carte, alertes, statistiques) et d'exporter des rapports PDF.

## Fonctionnalités

- Graphe interactif des entités et de leurs relations (vues force, radiale, groupes, analyse)
- Recherche d'entités, fiche détaillée, score de risque, connexions directes
- Recherche de chemin entre deux entités
- Carte, alertes et statistiques
- Export PDF d'une entité et rapport global

## Avertissement sur les données

Les entités, noms, relations, scores de risque et alertes de `app/data/entities.xlsx` sont **entièrement fictifs** : noms inventés, villes et événements génériques, relations attribuées au hasard. Cette base de démonstration a été générée avec l'aide de Claude (Anthropic) pour tester l'application. Toute ressemblance avec des personnes, organisations ou événements réels serait fortuite, et ces données ne doivent pas être interprétées comme des informations sur des personnes réelles.

Les données ICIJ (Offshore Leaks), elles, sont réelles et soumises aux conditions d'utilisation de l'ICIJ (voir plus bas). Elles ne sont pas incluses dans ce dépôt.

## Avertissement sur l'utilisation de données réelles

Les scores de risque et les statuts (« Critique », « Prioritaire », « Suivi », « Analyse », « Veille » dans la base de démonstration ; « Critique », « Surveillance », « Enquête », « Intérêt » dans la conversion ICIJ) sont des indicateurs **structurels** : pour les données ICIJ, ils reposent uniquement sur le nombre de connexions d'une entité dans le graphe. Ils ne constituent ni une évaluation de dangerosité, ni une accusation, ni une preuve d'infraction.

Appliqués à des données réelles (par exemple celles de l'ICIJ converties avec `icij_to_nexus.py`), ils ne doivent pas servir à désigner, accuser ou profiler des personnes ou des organisations. L'ICIJ rappelle que figurer dans ses bases ne suppose aucune faute.

L'utilisateur est seul responsable de l'usage qu'il fait de l'outil et des données qu'il y charge, dans le respect du droit applicable (RGPD, diffamation, conditions d'utilisation des sources). L'auteur décline toute responsabilité à ce sujet.

## Structure du projet

```
LNX_Vision_V1/
├── app/
│   ├── main.py            # Point d'entrée FastAPI (routes sous /api)
│   ├── api/routes.py      # Routes de l'API
│   ├── core/              # Construction du graphe, analyse, rapports PDF
│   └── data/entities.xlsx # Données d'entités (fictives)
├── frontend/              # Application frontend Python
├── lnx_vision.html        # Interface principale
├── lnx_intel.html         # Interface complémentaire
├── icij_to_nexus.py       # Conversion des données ICIJ
├── add_coordinates.py     # Ajout de coordonnées approximatives (par pays) pour la carte
├── launch_lnx.bat         # Lancement rapide sous Windows
├── LANCEMENT.txt          # Notes de lancement
└── requirements.txt       # Dépendances Python
```

## Prérequis

- Python 3.10
- Windows (le script `launch_lnx.bat` est prévu pour Windows ; le reste fonctionne ailleurs)

## Installation

```powershell
git clone https://github.com/alexandre196/LNX_VISION.git
cd LNX_VISION
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Données ICIJ

Le dossier `icij/` n'est pas versionné (fichiers trop volumineux). Pour l'utiliser :

1. Télécharger le jeu de données Offshore Leaks sur le site de l'ICIJ, en respectant ses conditions d'utilisation et de licence (attribution à l'ICIJ). Figurer dans cette base n'implique aucune infraction de la part d'une personne ou d'une société.
2. Placer les fichiers CSV (`nodes-*.csv`, `relationships.csv`) dans un dossier `icij/` à la racine du projet.

## Lancement

1. Démarrer l'API, avec l'environnement virtuel activé :

```powershell
uvicorn app.main:app --reload
```

L'API est disponible sur `http://127.0.0.1:8000` et sa documentation interactive sur `http://127.0.0.1:8000/docs`.

2. Ouvrir `lnx_vision.html` dans un navigateur (double-clic sur le fichier). L'API doit rester lancée pendant l'utilisation, dans son propre terminal.

L'onglet **CARTE** nécessite une connexion Internet pour charger le fond de carte (tuiles sombres d'Esri).

## Dépannage

- **« Impossible de joindre l'API / Failed to fetch »** : l'API n'est pas lancée (relancer `uvicorn app.main:app --reload` dans un terminal dédié et le laisser ouvert), ou une route renvoie une erreur (voir le terminal d'uvicorn).
- **Le fond de la carte est gris ou en erreur** : vérifier la connexion Internet. Le fond est chargé depuis les serveurs d'Esri ; certains fournisseurs de tuiles (OpenStreetMap, CARTO) refusent les pages ouvertes depuis un fichier local ou exigent une clé.
- **Une dépendance manque (`openpyxl`, `reportlab`…)** : activer le venv puis `pip install -r requirements.txt`.
- **`ModuleNotFoundError`** : l'environnement virtuel n'est pas activé ou les dépendances ne sont pas installées (`pip install -r requirements.txt`).
- **Un venv copié ou déplacé ne fonctionne plus** : le supprimer et le recréer à son emplacement actuel.

## Licence

© 2026 Alexandre Martin. Tous droits réservés.

Ce code ne peut être copié, modifié, redistribué ni utilisé à des fins commerciales sans l'autorisation écrite de l'auteur. Il est fourni tel quel, sans garantie d'aucune sorte.
