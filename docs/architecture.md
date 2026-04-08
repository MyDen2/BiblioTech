# BiblioTech – Architecture Data

## 1. Objectif du projet

BiblioTech est une plateforme d’analyse et de recommandation de livres basée sur des données utilisateurs (ratings, profils) et des métadonnées (livres, auteurs).

L’objectif est de construire une architecture data complète permettant :
- l’ingestion de données brutes,
- leur transformation et nettoyage,
- leur stockage dans un Data Lake,
- leur exploitation analytique via une base relationnelle,
- leur préparation pour des modèles de recommandation.

---

## 2. Architecture globale

Le projet repose sur une architecture inspirée des systèmes cloud modernes :

Sources (CSV / API)
↓
MinIO (Data Lake)
→ bronze (données brutes)
→ silver (données nettoyées)
→ gold (données analytiques)
↓
PostgreSQL (base relationnelle)
↓
SQL / API / Dashboard / ML


---

## 3. Data Lake – MinIO

Le stockage des données est assuré par **MinIO**, une solution compatible S3.

### Organisation en couches :

#### Bronze
- Données brutes non modifiées
- Format : CSV
- Exemple :
  - `BX-Book-Ratings.csv`
  - `BX_Books.csv`
  - `BX-Users.csv`

#### Silver
- Données nettoyées et normalisées
- Format : Parquet
- Exemples :
  - `books_clean.parquet`
  - `users_clean.parquet`
  - `ratings_clean.parquet`
  - `ratings_joinable.parquet`

#### Gold
- Données enrichies et prêtes pour l’analyse
- Format : Parquet
- Exemple :
  - `book_popularity.parquet`

---

## 4. Pipeline ETL

Les transformations sont réalisées en Python avec Pandas.

### Étapes principales :

#### 1. Ingestion
- Lecture des données depuis MinIO (bronze)
- Utilisation de `boto3` via un module `s3_io`

#### 2. Nettoyage (Silver)
- Normalisation des colonnes
- Suppression des valeurs invalides
- Filtrage des ratings implicites (`rating = 0`)
- Déduplication

#### 3. Qualité des données
- Vérification des relations :
  - `ratings` ↔ `books`
  - `ratings` ↔ `users`
- Suppression des données orphelines

#### 4. Enrichissement (Gold)
- Agrégation des ratings par livre
- Calcul :
  - `ratings_count`
  - `average_rating`
  - `weighted_score`

---

## 5. 🗄️ Base de données – PostgreSQL

Les données sont chargées depuis MinIO vers PostgreSQL.

### Tables principales :

- `books`
- `users`
- `ratings`
- `book_popularity`

### Relations :

- `ratings.user_id → users.user_id`
- `ratings.isbn → books.isbn`

### Objectif :
- permettre des requêtes SQL analytiques
- servir de base pour API et dashboards

---

## 6. Vues SQL

Des vues ont été créées pour exposer des indicateurs métier :

- `vw_top_popular_books`
- `vw_top_rated_books`
- `vw_author_stats`
- `vw_year_stats`
- `vw_user_activity`

Ces vues permettent de simplifier l’accès aux données analytiques.

---

## 7. Technologies utilisées

| Composant        | Rôle |
|------------------|------|
| **MinIO**        | Data Lake (stockage objet S3) |
| **PostgreSQL**   | Base relationnelle analytique |
| **Pandas**       | Transformation de données |
| **boto3**        | Accès S3 (MinIO) |
| **Docker**       | Environnement conteneurisé |
| **SQLAlchemy**   | Connexion PostgreSQL |

---

## 8. Choix techniques

### Pourquoi MinIO ?
- Simulation locale d’un Data Lake cloud
- Compatible AWS S3
- Permet une architecture scalable

### Pourquoi Parquet ?
- Format colonne optimisé
- Compression efficace
- Lecture rapide pour analytics

### Pourquoi PostgreSQL ?
- Standard SQL robuste
- Support des jointures complexes
- Intégration facile avec Python

---

## 9. Limites actuelles

- Données issues d’un dataset statique (Book-Crossing)
- Qualité hétérogène des ISBN
- Absence de données temps réel
- Nettoyage des pays encore simplifié
- Pas encore de pipeline orchestré (Airflow / cron)

---

## 10. Évolutions prévues

- Ajout de données via API (OpenLibrary, Google Books)
- Mise en place de modèles de recommandation (Bloc ML)
- Création d’une API (FastAPI)
- Dashboard interactif (Streamlit / Plotly)
- Orchestration du pipeline

---

## 11. Conclusion

Le projet BiblioTech met en place une architecture data complète inspirée des standards du cloud, avec séparation claire des couches de données et automatisation des transformations.

Cette base permet de construire des analyses avancées et des modèles de recommandation à partir de données fiables et structurées.