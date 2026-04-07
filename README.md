# BiblioTech : Plateforme Data & IA d’analyse du marché du livre et de recommandation intelligente.

*** Contexte ***

Le marché du livre génère un volume important de données hétérogènes : métadonnées (genres, auteurs, dates), données chiffrées (notes, popularité) et données textuelles (résumés, avis lecteurs).

L’objectif du projet est de centraliser ces données, analyser les tendances du marché, identifier les facteurs de succès d’un livre et exploiter ces résultats via des modèles de Machine Learning et une API de recommandation.

BiblioTech est une plateforme Data & Intelligence Artificielle permettant de centraliser, analyser et exploiter des données issues du marché du livre.
Le projet combine une architecture Data Lake (bronze/silver/gold), des pipelines ETL, des analyses statistiques, des modèles de Machine Learning et une API de recommandation industrialisée.

## 🧱 Vue d’ensemble de BiblioTech

Cette plateforme doit gérer :

• 📚 Métadonnées structurées (livres, auteurs, genres)

• 📝 Données textuelles variables (avis)

• 📊 Tables analytiques (KPIs marché)

• 🧠 Features ML

• 🗄️ Données brutes historisées

Séparation des responsabilités:

### 🪣 1️⃣ MinIO (S3 compatible) → Le Data Lake

#### 🎯 Rôle

Stocker les données brutes et transformées.

Architecture :

bronze → brut

silver → nettoyé

gold → analytique

#### 🧠 Pourquoi pas Postgres pour ça ?

Parce que :

Le brut peut être volumineux

Format JSON / CSV / Parquet

On veut historiser

On veut stocker des dumps

On veut simuler AWS S3 (standard industrie)

#### 🎓 Pourquoi MinIO ?

• Compatible S3

• Léger

• Local

• Standard cloud industry

• Idéal pour Data Lake

👉 MinIO = ton stockage objet
👉 Il remplace AWS S3 en local

### 🗄️ 2️⃣ PostgreSQL → Données structurées analytiques

#### 🎯 Rôle

Stocker les données propres, relationnelles et requêtables.

Exemples :

• books

• authors

• genres

• market_metrics

#### 🧠 Pourquoi relationnel ?

Parce que :

• Relations claires (1 livre → plusieurs genres)

• Contraintes d’intégrité

• JOINS

• Agrégations SQL

• Vues analytiques

#### 🎓 Pourquoi Postgres ?

• Stable

• Standard industrie

• Puissant

• Compatible BI

• Excellent pour analytics

### 🍃 3️⃣ MongoDB → Données semi-structurées (avis)

#### 🎯 Rôle

Stocker les avis utilisateurs.

Pourquoi ?
Un avis peut contenir :

• texte

• rating

• date

• langue

• metadata optionnelle

Et demain ?

• tags

• émotions détectées

• score NLP

• entités nommées

#### 🧠 Pourquoi pas SQL ?

Parce que :

• Schéma variable

• JSON naturel

• Pas besoin de JOINS lourds

• Écriture rapide

#### 🎓 Pourquoi Mongo ?

• Modèle document

• Flexible

• Idéal pour texte

• Courant en data engineering

Mongo permet ainsi un stockage flexible des avis.

### Résumé : 

| Technologie | Rôle               | Pourquoi ?                         |
| ----------- | ------------------ | --------------------------------- |
| MinIO       | Data Lake          | Stockage objet brut et transformé |
| PostgreSQL  | Base relationnelle | Données structurées + SQL         |
| MongoDB     | Base document      | Avis flexibles JSON               |
| Docker      | Isolation          | Reproductibilité                  |
| .env        | Config             | Sécurité                          |


## Application par bloc

### BC01 — Collecte, Data Lake & ETL

* Application concrète :
    • Collecte multi-sources : API livres, fichiers CSV/JSON, avis textuels.
    • Mise en place d’un Data Lake bronze/silver/gold (MinIO / S3).
    • ETL Python + PySpark pour volumes importants.
    • Chargement dans :
        ◦ PostgreSQL (analytique marché),
        ◦ MongoDB (avis texte).

### BC02 — Analyse exploratoire & décisionnelle

* Application concrète :
    • Analyse du marché :
        ◦ répartition par genres, langues, périodes,
        ◦ évolution des tendances (genres émergents),
        ◦ comparaison notes ↔ caractéristiques (pages, genre, ancienneté).
    • Statistiques : corrélations, tests d’hypothèses.
    • Visualisation : dashboards (Plotly).

### BC03 — Machine Learning & recommandation

* Application concrète :
    • Prédiction :
        ◦ note moyenne d’un livre,
        ◦ probabilité de succès/popularité.
    • Segmentation :
        ◦ clustering de livres (styles/genres latents).
    • Recommandation :
        ◦ content-based (genres + texte),
        ◦ collaborative filtering (si données utilisateurs),
        ◦ score hybride (analyse marché + préférences utilisateur).

### BC04 — NLP & Deep Learning

* Application concrète :
    • Nettoyage et vectorisation des résumés et avis.
    • Analyse de sentiment des avis lecteurs.
    • Embeddings de texte pour :
        ◦ enrichir la recommandation,
        ◦ détecter thématiques dominantes par genre.
    • Modèles avancés (Transformers en option).

### BC05 — Industrialisation, API & déploiement

* Application concrète :
    • API FastAPI :
        ◦ /market/insights → tendances & statistiques,
        ◦ /recommend → recommandations personnalisées,
        ◦ /sentiment → analyse d’avis.
    • Dockerisation complète (ETL + API + services).
    • Suivi des modèles avec MLflow.
    • Déploiement local (et cloud en option).

### BC06 — Gestion de projet & vulgarisation

* Application concrète :
    • Cadrage produit (éditeur/librairie).
    • Roadmap MVP → V2.
    • Indicateurs : qualité data, performances modèles, usage API.
    • Présentation orientée aide à la décision pour non-techniques.

## Sources de données : 

    • Open Library
    • Google Books API
    • Kaggle (Goodreads / Book reviews)
    • Project Gutenberg (domaine public)


### BX-Books.csv

#### Problèmes

- Années incohérentes (0, 1378, 20230…)

- ISBN parfois dupliqués

- Encodage spécial (latin-1 souvent nécessaire)

- Titres avec caractères spéciaux

#### Nettoyage en Silver

- Année valide (entre 1900 et année actuelle)

- Suppression doublons ISBN

- Normalisation colonnes

- Conversion types

### BX-Users.csv

#### Problèmes
- Beaucoup d’âges manquants

- Ages absurdes (0, 200)

- Location non structurée (“City, State, Country” en string)

#### Nettoyage en Silver
- Extraire Country depuis Location

- Filtrer âges improbables (ex: < 10 ou > 100)

- Gérer nulls

### BX-Book-Ratings.csv

On ne garde que les ratings > 0 car données explicites venat de l'utilisateur (0 => pas de retour de l'utilisateur)

## Architecture Data : 
Kaggle => Book-Crossing: User review ratings


Bronze → nettoyage → silver
Silver → feature engineering → gold
Gold → ML



## Structure du projet : 

BiblioTech/
├── config/
│   ├── .env
│   └── settings.yaml

├── data/
│   ├── bronze/
│   │   ├── openlibrary_books_raw.jsonl
│   │   ├── googlebooks_raw.jsonl
│   │   └── reviews_raw.jsonl
│   ├── silver/
│   │   ├── books_clean.parquet
│   │   ├── authors_clean.parquet
│   │   └── reviews_clean.parquet
│   └── gold/
│       ├── market_kpis.parquet          # analytics marché
│       ├── book_features.parquet        # features ML
│       └── reco_candidates.parquet      # tables prêtes reco

├── src/
    ├── __init__.py
|   ├── frontend/  # ajout d'un front léger grâce à Streamlit
│       ├── app.py
│       ├── pages/
            ├── market.py
            ├── recommend.py
            └── sentiment.py
│        └── components/
│   ├── extractors/
        ├── __init__.py
│   │   ├── openlibrary_api.py
│   │   ├── googlebooks_api.py
│   │   └── reviews_scraper.py           # optionnel si scraping
│   ├── transformers/
        ├── __init__.py
│   │   ├── clean_books.py
│   │   ├── clean_reviews.py
│   │   ├── build_gold_tables.py
│   │   └── quality_checks.py
│   ├── loaders/
        ├── __init__.py
│   │   ├── minio_loader.py
│   │   ├── postgres_loader.py
│   │   └── mongo_loader.py
│   ├── ml/
        ├── __init__.py
│   │   ├── train_rating.py              # prédire note / succès
│   │   ├── train_reco.py                # reco content-based / hybride
│   │   ├── evaluate.py
│   │   └── mlflow_registry.py
│   ├── api/
        ├── __init__.py
│   │   ├── app.py
│   │   ├── schemas.py
│   │   ├── routes/
│   │   │   ├── market.py                # insights marché
│   │   │   ├── recommend.py             # reco
│   │   │   └── sentiment.py             # avis
│   │   └── services/
│   │       ├── market_service.py
│   │       ├── reco_service.py
│   │       └── sentiment_service.py
│   ├── utils/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── io.py
│   └── main.py

├── sql/
│   ├── schema.sql
│   └── views.sql

├── notebooks/
│   ├── 01_eda_books.ipynb
│   ├── 02_eda_reviews.ipynb
│   └── 03_modeling.ipynb

├── dashboards/
│   ├── market_dashboard.py              # plotly/streamlit/dash
│   └── exports/                         # png/html/csv

├── docs/
│   ├── architecture.md
│   ├── data_dictionary.md
│   └── ethics_and_limits.md

├── tests/
│   ├── test_extractors.py
│   ├── test_transformers.py
│   ├── test_quality_checks.py
│   └── test_api.py

├── docker-compose.yml
├── Dockerfile
├── .gitignore
├── README.md
└── requirements.txt

