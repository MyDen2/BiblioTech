# BiblioTech

## Présentation

BiblioTech est une plateforme data orientée analyse et recommandation de livres.  
Le projet met en place une architecture inspirée du cloud avec :

- un Data Lake local basé sur **MinIO**
- des pipelines ETL en **Python / Pandas**
- une base relationnelle **PostgreSQL**
- des données organisées en couches **bronze / silver / gold**

L’objectif est de centraliser, nettoyer, enrichir et exploiter des données livres afin de préparer des analyses métier et des modèles de recommandation.

## Objectifs du projet

- ingérer des données brutes issues du dataset Book-Crossing
- construire un pipeline ETL reproductible
- stocker les données dans un Data Lake S3-compatible
- charger les données utiles dans PostgreSQL
- produire des tables analytiques prêtes pour SQL, dashboards et ML

## Architecture

```text
Sources CSV
   ↓
MinIO / Data Lake
   ├── bronze : données brutes
   ├── silver : données nettoyées
   └── gold   : données analytiques
   ↓
PostgreSQL
   ↓
SQL / Dashboard / API / Machine Learning
```

## Documentation détaillée :

- docs/architecture.md
- docs/data_dictionary.md

## Arborescence

BiblioTech/
├── config/
│   ├── .env
│   └── settings.yaml
├── data/
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── src/
│   ├── extractors/
│   ├── transformers/
│   ├── loaders/
│   ├── ml/
│   ├── api/
│   ├── utils/
│   └── main.py
├── sql/
│   ├── schema.sql
│   └── views.sql
├── notebooks/
├── dashboards/
├── docs/
├── tests/
├── docker-compose.yml
├── Dockerfile
├── .gitignore
├── README.md
└── requirements.txt

## Dataset utilisé

Projet basé principalement sur le dataset Book-Crossing :

BX-Book-Ratings.csv
BX_Books.csv
BX-Users.csv

## Couches de données
### Bronze

#### Données brutes non modifiées :

- BX-Book-Ratings.csv
- BX_Books.csv
- BX-Users.csv

### Silver

#### Données nettoyées :

- ratings_clean.parquet
- books_clean.parquet
- users_clean.parquet
- ratings_joinable.parquet

### Gold

#### Données analytiques :

- book_popularity.parquet

### Infrastructure

Les services sont lancés avec Docker :

- MinIO : stockage objet S3-compatible
- PostgreSQL : base relationnelle
- MongoDB : stockage NoSQL
- pgAdmin : administration PostgreSQL

Lancement :

docker compose up -d

### Configuration

Le fichier config/.env contient les variables d’environnement :

- identifiants MinIO
- configuration PostgreSQL
- buckets bronze / silver / gold

### Installation

Créer un environnement virtuel puis installer les dépendances :

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

### Exécution du pipeline

#### Lancer une étape spécifique : 

python -m src.main clean_ratings
python -m src.main clean_books
python -m src.main clean_users
python -m src.main filter_joinable_ratings
python -m src.main build_book_popularity
python -m src.main load_postgres

#### Lancer le pipeline complet :

python -m src.main full_pipeline

### Initialisation SQL

#### Créer les tables :

Get-Content .\sql\schema.sql | docker exec -i bibliotech_postgres psql -U bibliotech -d bibliotech_db

#### Créer les vues :

Get-Content .\sql\views.sql | docker exec -i bibliotech_postgres psql -U bibliotech -d bibliotech_db

