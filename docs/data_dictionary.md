# BiblioTech – Data Dictionary

## 1. Objectif

Ce document décrit les principales structures de données utilisées dans
BiblioTech, leurs colonnes, leurs types et leur signification métier.

Les données du pipeline sont organisées en trois couches :

- Bronze : données brutes ;
- Silver : données nettoyées et normalisées ;
- Gold : données agrégées et analytiques.

Le projet distingue également deux identifiants importants :

- `isbn` : identifie une édition d'un livre ;
- `book_key` : identifie une œuvre logique à partir du titre et de l'auteur.

---

## 2. Bronze Layer – Données brutes

### Source : Book-Crossing Dataset

### BX-Book-Ratings.csv

| Colonne | Type | Description |
|---|---|---|
| User-ID | integer | Identifiant de l'utilisateur |
| ISBN | string | ISBN de l'édition notée |
| Book-Rating | integer | Note : 0 implicite, 1 à 10 explicite |

Règles métier :

- `0` correspond à une interaction implicite ;
- seules les notes explicites de 1 à 10 sont conservées pour le système actuel.

---

### BX_Books.csv

| Colonne | Type | Description |
|---|---|---|
| ISBN | string | Identifiant d'une édition |
| Book-Title | string | Titre |
| Book-Author | string | Auteur |
| Year-Of-Publication | string/integer | Année de publication |
| Publisher | string | Éditeur |
| Image-URL-S | string | URL de petite couverture |
| Image-URL-M | string | URL de couverture moyenne |
| Image-URL-L | string | URL de grande couverture |

Les données sources peuvent contenir des problèmes d'encodage,
des années invalides et des variations dans l'écriture des métadonnées.

---

### BX-Users.csv

| Colonne | Type | Description |
|---|---|---|
| User-ID | integer | Identifiant utilisateur |
| Location | string | Localisation déclarée |
| Age | integer | Âge, potentiellement manquant ou aberrant |

---

## 3. Silver Layer – Données nettoyées

### books_clean.parquet

Contient les éditions nettoyées du catalogue.

| Colonne | Type | Description |
|---|---|---|
| isbn | string | Identifiant de l'édition |
| title | string | Titre nettoyé |
| author | string | Auteur nettoyé et normalisé pour l'affichage |
| year_of_publication | integer / null | Année valide |
| publisher | string | Éditeur |
| image_url_s | string | URL de petite couverture |
| image_url_m | string | URL de couverture moyenne |
| image_url_l | string | URL de grande couverture |
| book_key | string | Identifiant logique de l'œuvre |

Exemple de `book_key` :

`1984|george orwell`

Principales règles :

- normalisation de l'ISBN ;
- correction des problèmes d'encodage ;
- nettoyage des textes ;
- normalisation de l'affichage des auteurs ;
- validation des années de publication ;
- suppression des doublons ISBN ;
- génération de `book_key`.

`isbn` identifie donc une édition tandis que `book_key` permet de
regrouper les éditions représentant une même œuvre logique.

---

### users_clean.parquet

| Colonne | Type | Description |
|---|---|---|
| user_id | integer | Identifiant utilisateur |
| location | string | Localisation nettoyée |
| country | string | Pays extrait de la localisation |
| age | integer / null | Âge nettoyé |

Principales règles :

- validation des identifiants ;
- extraction du pays ;
- traitement des âges manquants ou aberrants.

---

### ratings_clean.parquet

Contient les ratings explicites nettoyés avant résolution des œuvres.

| Colonne | Type | Description |
|---|---|---|
| user_id | integer | Identifiant utilisateur |
| isbn | string | ISBN de l'édition notée |
| rating | integer | Note explicite de 1 à 10 |

Principales règles :

- suppression des ratings implicites (`rating = 0`) ;
- suppression des valeurs invalides ;
- déduplication des couples `(user_id, isbn)`.

---

### ratings_joinable.parquet

Contient les ratings valides ramenés au niveau de l'œuvre.

| Colonne | Type | Description |
|---|---|---|
| user_id | integer | Identifiant utilisateur |
| book_key | string | Identifiant logique de l'œuvre |
| rating | float | Note de l'utilisateur pour l'œuvre |

Principales règles :

- conservation uniquement des utilisateurs existants ;
- conservation uniquement des livres existants ;
- rattachement des ISBN à leur `book_key` ;
- regroupement par `(user_id, book_key)` ;
- moyenne des ratings lorsqu'un utilisateur a noté plusieurs éditions de la même œuvre.

Ce fichier constitue notamment la base du modèle de recommandation.

---

## 4. Gold Layer – Données analytiques

### book_popularity.parquet

Contient les statistiques de popularité calculées au niveau de l'œuvre.

| Colonne | Type | Description |
|---|---|---|
| book_key | string | Identifiant unique de l'œuvre |
| title | string | Titre représentatif |
| author | string | Auteur |
| year_of_publication | integer / null | Année de publication |
| publisher | string | Éditeur |
| image_url_s | string | URL de petite couverture |
| image_url_m | string | URL de couverture moyenne |
| image_url_l | string | URL de grande couverture |
| ratings_count | integer | Nombre de ratings |
| average_rating | float | Moyenne des ratings |
| weighted_score | float | Score de popularité pondéré |

### weighted_score

Le score pondéré combine :

- la note moyenne de l'œuvre ;
- son nombre de ratings ;
- la moyenne globale ;
- un nombre minimal de votes de référence.

Son objectif est de limiter la survalorisation d'une œuvre ayant une
excellente moyenne mais très peu de ratings.

---

## 5. PostgreSQL – Données du dataset

### books

Table de référence des œuvres utilisée par l'application.

Clé primaire :

`book_key`

### users

Utilisateurs historiques issus de Book-Crossing.

Clé primaire :

`user_id`

Ces utilisateurs servent notamment à construire les données historiques
utilisées par le système de recommandation.

### ratings

Ratings historiques au niveau œuvre.

Clé primaire composée :

`(user_id, book_key)`

Relations :

`ratings.user_id → users.user_id`

`ratings.book_key → books.book_key`

### book_popularity

Statistiques de popularité au niveau œuvre.

Clé primaire :

`book_key`

Relation :

`book_popularity.book_key → books.book_key`

---

## 6. PostgreSQL – Données applicatives

Les utilisateurs de BiblioTech sont séparés des utilisateurs historiques
du dataset.

### app_users

| Colonne | Type | Description |
|---|---|---|
| app_user_id | integer | Identifiant applicatif |
| username | string | Nom de l'utilisateur |
| email | string | Adresse email unique |
| age | integer / null | Âge |
| country | string / null | Pays |
| created_at | timestamp | Date de création |

Clé primaire :

`app_user_id`

---

### user_book_ratings

Contient les notes saisies par les utilisateurs de l'application.

| Colonne | Type | Description |
|---|---|---|
| rating_id | integer | Identifiant du rating |
| app_user_id | integer | Utilisateur de l'application |
| book_key | string | Œuvre notée |
| rating | integer | Note de 1 à 10 |
| created_at | timestamp | Date de création ou mise à jour |

Relations :

`user_book_ratings.app_user_id → app_users.app_user_id`

`user_book_ratings.book_key → books.book_key`

Contrainte d'unicité :

`(app_user_id, book_key)`

Un utilisateur de l'application ne peut donc posséder qu'une note
active par œuvre. Une nouvelle notation peut mettre à jour la précédente.

---

## 7. Relations principales

| Source | Colonne | Cible | Colonne |
|---|---|---|---|
| ratings | user_id | users | user_id |
| ratings | book_key | books | book_key |
| book_popularity | book_key | books | book_key |
| user_book_ratings | app_user_id | app_users | app_user_id |
| user_book_ratings | book_key | books | book_key |

Deux populations d'utilisateurs sont volontairement séparées :

**Utilisateurs historiques**

`users → ratings`

Ils proviennent du dataset Book-Crossing et fournissent le signal
collaboratif utilisé pour construire le modèle.

**Utilisateurs applicatifs**

`app_users → user_book_ratings`

Ils correspondent aux utilisateurs de BiblioTech.

---

## 8. Données utilisées par le modèle ML

Le modèle de recommandation utilise `ratings_joinable.parquet`.

L'unité recommandée est l'œuvre identifiée par `book_key`.

Pour l'entraînement actuel :

- les 5 000 œuvres les plus notées sont sélectionnées ;
- une matrice sparse `utilisateur × œuvre` est construite ;
- une similarité cosinus item-item est calculée.

Les principaux artefacts générés sont :

- `similarity.joblib`
- `book_index_map.joblib`
- `book_metadata.joblib`

`book_index_map` associe chaque `book_key` présent dans le modèle
à sa position dans la matrice de similarité.

---

## 9. Limites des données

- dataset Book-Crossing ancien et statique ;
- métadonnées parfois incomplètes ou incorrectes ;
- ISBN parfois incohérents ;
- absence de date pour les ratings historiques ;
- âges utilisateurs parfois peu fiables ;
- variantes de titres et traductions pouvant générer plusieurs `book_key` ;
- `book_key` est un identifiant logique construit heuristiquement ;
- modèle ML limité actuellement aux 5 000 œuvres les plus notées ;
- certaines URLs de couvertures peuvent devenir indisponibles.

---

## 10. Utilisation des données

Les données alimentent :

- les analyses SQL ;
- les indicateurs de popularité ;
- PostgreSQL ;
- le modèle de recommandation ;
- l'API FastAPI ;
- l'interface Streamlit.

---

## 11. Conclusion

Le Data Dictionary documente le passage des données brutes Book-Crossing
vers une représentation centrée sur les œuvres.

L'ISBN reste utile dans les premières étapes du pipeline pour identifier
les éditions sources, tandis que `book_key` devient l'identifiant principal
pour les analyses, PostgreSQL et le système de recommandation.

La séparation entre utilisateurs historiques (`users`) et utilisateurs
applicatifs (`app_users`) permet enfin de conserver une distinction claire
entre les données utilisées pour construire le modèle et celles produites
par l'application BiblioTech.