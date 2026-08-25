# BiblioTech

## Présentation

BiblioTech est une plateforme data de recherche et de recommandation de
livres construite à partir du dataset Book-Crossing.

Le projet met en œuvre une chaîne complète allant des données brutes
jusqu'à une application interactive :

-   Data Lake local avec **MinIO** ;
-   pipelines ETL en **Python / Pandas** ;
-   stockage relationnel avec **PostgreSQL** ;
-   système de recommandation collaborative avec **scikit-learn** ;
-   API REST avec **FastAPI** ;
-   interface utilisateur avec **Streamlit**.

Les données sont organisées selon une architecture **Bronze / Silver /
Gold**.

## Objectifs du projet

-   ingérer les données brutes du dataset Book-Crossing ;
-   construire un pipeline ETL reproductible ;
-   nettoyer et normaliser les données ;
-   stocker les données dans un Data Lake compatible S3 ;
-   distinguer les éditions ISBN des œuvres logiques via `book_key` ;
-   charger les données utiles dans PostgreSQL ;
-   produire des indicateurs analytiques de popularité ;
-   entraîner un système de recommandation ;
-   exposer les fonctionnalités via une API ;
-   proposer une interface de recherche et de recommandation.

## Architecture

``` text
Book-Crossing
    |
    | CSV
    v
MinIO Data Lake
    |-- Bronze : données brutes
    |-- Silver : données nettoyées
    `-- Gold   : données agrégées
          |
          +----------+
          |          |
          v          v
     PostgreSQL      ML
          |          |
          |    Modèle item-based
          |    Similarité cosinus
          |          |
          +----+-----+
               v
            FastAPI
               |
               v
           Streamlit
```

## Documentation

-   `docs/architecture.md`
-   `docs/data_dictionary.md`

## Arborescence

``` text
BiblioTech/
├── config/
│   ├── .env
│   └── settings.yaml
├── data/
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── models/
│   └── reco/
│       ├── similarity.joblib
│       ├── book_index_map.joblib
│       └── book_metadata.joblib
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
│   ├── app_schema.sql
│   └── views.sql
├── notebooks/
├── dashboards/
├── docs/
├── docker-compose.yml
├── Dockerfile
├── .gitignore
├── README.md
└── requirements.txt
```

## Dataset

Le projet utilise principalement le dataset **Book-Crossing** :

-   `BX-Book-Ratings.csv`
-   `BX_Books.csv`
-   `BX-Users.csv`

## Identification des œuvres

Le dataset original utilise l'ISBN comme identifiant. Un ISBN représente
une **édition** d'un livre et non nécessairement une œuvre logique.

BiblioTech génère donc un identifiant `book_key` à partir du titre et de
l'auteur normalisés.

Exemple : `1984|george orwell`

Le système de recommandation travaille principalement au niveau de
l'œuvre (`book_key`) plutôt qu'au niveau de l'édition (`isbn`).

## Couches de données

### Bronze

-   `BX-Book-Ratings.csv`
-   `BX_Books.csv`
-   `BX-Users.csv`

### Silver

-   `ratings_clean.parquet`
-   `books_clean.parquet`
-   `users_clean.parquet`
-   `ratings_joinable.parquet`

`ratings_joinable.parquet` contient les ratings valides au niveau
`user_id × book_key`.

### Gold

-   `book_popularity.parquet`

Cette table contient notamment le nombre de ratings, la note moyenne et
un score de popularité pondéré.

## PostgreSQL

### Données historiques

-   `books`
-   `users`
-   `ratings`
-   `book_popularity`

### Données applicatives

-   `app_users`
-   `user_book_ratings`

Cette séparation distingue les utilisateurs historiques ayant servi à
construire le modèle des utilisateurs réels de l'application.

## Système de recommandation

BiblioTech utilise un système de recommandation **collaboratif
item-based**.

Les **5 000 œuvres les plus notées** sont sélectionnées puis
représentées dans une matrice sparse `utilisateurs × œuvres`. Une
similarité cosinus est calculée entre les œuvres.

Artefacts générés dans `models/reco/` :

-   `similarity.joblib`
-   `book_index_map.joblib`
-   `book_metadata.joblib`

### Entraîner le modèle

``` powershell
python -m src.ml.train_reco
```

### Tester une recommandation

``` powershell
python -m src.ml.predict --book_key "1984|george orwell" --top_n 5
```

## API FastAPI

Principaux endpoints :

``` text
GET  /books/search
GET  /recommend/book
GET  /recommend/user/{app_user_id}
POST /users
POST /ratings
```

Lancer l'API :

``` powershell
uvicorn src.api.app:app --reload
```

Documentation interactive : `/docs`.

## Interface Streamlit

L'interface permet de rechercher un livre, sélectionner une œuvre,
afficher ses métadonnées et sa couverture, puis obtenir des
recommandations.

``` powershell
streamlit run src/front/app.py
```

## Infrastructure

Les principaux services sont :

-   **MinIO** : stockage objet compatible S3 ;
-   **PostgreSQL** : base relationnelle ;
-   **pgAdmin** : administration PostgreSQL.

``` powershell
docker compose up -d
```

## Configuration

Le fichier `config/.env` contient les variables nécessaires à MinIO et
PostgreSQL. Il ne doit pas être versionné.

## Installation

``` powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Exécution du pipeline ETL

### Étapes individuelles

``` powershell
python -m src.main clean_ratings
python -m src.main clean_books
python -m src.main clean_users
python -m src.main filter_joinable_ratings
python -m src.main build_book_popularity
python -m src.main load_postgres
```

### Pipeline complet

``` powershell
python -m src.main full_pipeline
```

Après une modification affectant `book_key` ou les ratings utilisés par
le modèle :

``` powershell
python -m src.ml.train_reco
```

## Initialisation PostgreSQL

### Tables du dataset

``` powershell
Get-Content .\sql\schema.sql | docker exec -i bibliotech_postgres psql -U bibliotech -d bibliotech_db
```

### Tables applicatives

``` powershell
Get-Content .\sql\app_schema.sql | docker exec -i bibliotech_postgres psql -U bibliotech -d bibliotech_db
```

### Vues

``` powershell
Get-Content .\sql\views.sql | docker exec -i bibliotech_postgres psql -U bibliotech -d bibliotech_db
```

## Exemple de recommandation

À partir de `1984 — George Orwell`, le système peut notamment identifier
:

-   Animal Farm --- George Orwell
-   Brave New World --- Aldous Huxley
-   Lord of the Flies --- William Gerald Golding

## Limites actuelles

-   dataset Book-Crossing ancien et statique ;
-   qualité hétérogène des métadonnées ;
-   `book_key` construit heuristiquement à partir du titre et de
    l'auteur ;
-   certaines traductions ou variantes peuvent être considérées comme
    des œuvres distinctes ;
-   modèle limité aux 5 000 œuvres les plus notées ;
-   cold start pour les nouveaux utilisateurs sans ratings ;
-   certaines couvertures externes peuvent devenir indisponibles ;
-   pipeline non orchestré automatiquement.

## Évolutions possibles

-   enrichissement via Open Library ou Google Books ;
-   amélioration de la résolution des œuvres ;
-   système hybride collaboratif + contenu ;
-   stratégie de recommandation pour le cold start ;
-   évaluation quantitative du modèle ;
-   orchestration automatique du pipeline ;
-   automatisation du réentraînement ;
-   tests automatisés et monitoring.

## Technologies

  Technologie    Utilisation
  -------------- --------------------------------
  Python         Développement principal
  Pandas         ETL et préparation des données
  MinIO          Data Lake compatible S3
  Parquet        Stockage analytique
  PostgreSQL     Base relationnelle
  SQLAlchemy     Accès PostgreSQL
  SciPy          Matrices sparse
  scikit-learn   Similarité cosinus
  joblib         Sérialisation du modèle
  FastAPI        API REST
  Streamlit      Interface utilisateur
  Docker         Infrastructure
  ftfy           Correction d'encodage

## Conclusion

BiblioTech met en œuvre une architecture data complète allant de
l'ingestion de données brutes jusqu'à leur exploitation dans une
application de recommandation.

Le projet combine Data Engineering, SQL, Machine Learning, API et
visualisation dans une architecture cohérente centrée sur les œuvres
identifiées par `book_key`.
