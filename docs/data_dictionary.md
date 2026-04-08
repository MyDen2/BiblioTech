# BiblioTech – Data Dictionary

## 1. Objectif

Ce document décrit les structures de données utilisées dans le projet BiblioTech, incluant les tables, colonnes, types, et leur signification métier.

Les données sont organisées en couches :
- Bronze : données brutes
- Silver : données nettoyées
- Gold : données enrichies et analytiques

---

## 2. Bronze Layer (données brutes)

### Source : Book-Crossing Dataset

#### BX-Book-Ratings.csv

| Colonne | Type | Description |
|--------|------|------------|
| User-ID | integer | Identifiant utilisateur |
| ISBN | string | Identifiant du livre |
| Book-Rating | integer | Note donnée (0 = implicite, 1–10 = explicite) |

 Remarque :
- Les valeurs `0` correspondent à des interactions implicites (non utilisées dans l’analyse).

---

#### BX_Books.csv

| Colonne | Type | Description |
|--------|------|------------|
| ISBN | string | Identifiant du livre |
| Book-Title | string | Titre |
| Book-Author | string | Auteur |
| Year-Of-Publication | string/integer | Année (peut contenir des erreurs) |
| Publisher | string | Éditeur |
| Image-URL-S | string | Image petite |
| Image-URL-M | string | Image moyenne |
| Image-URL-L | string | Image grande |

---

#### BX-Users.csv

| Colonne | Type | Description |
|--------|------|------------|
| User-ID | integer | Identifiant utilisateur |
| Location | string | Localisation (ville, pays…) |
| Age | integer | Âge utilisateur (souvent manquant ou aberrant) |

---

## 3. Silver Layer (données nettoyées)

### books_clean.parquet

| Colonne | Type | Description |
|--------|------|------------|
| isbn | string | Identifiant unique du livre (normalisé) |
| title | string | Titre nettoyé |
| author | string | Auteur |
| year_of_publication | integer | Année corrigée (1900–2025) |
| publisher | string | Éditeur |
| image_url_s | string | Image petite |
| image_url_m | string | Image moyenne |
| image_url_l | string | Image grande |

Règles :
- suppression des doublons ISBN
- normalisation des textes
- filtrage des années invalides

---

### users_clean.parquet

| Colonne | Type | Description |
|--------|------|------------|
| user_id | integer | Identifiant utilisateur |
| location | string | Localisation brute |
| country | string | Pays extrait depuis location |
| age | integer | Âge (filtré entre 10 et 100) |

Règles :
- suppression des user_id invalides
- extraction du pays (dernier segment de location)
- nettoyage des âges aberrants

---

### ratings_clean.parquet

| Colonne | Type | Description |
|--------|------|------------|
| user_id | integer | Identifiant utilisateur |
| isbn | string | Identifiant livre |
| rating | integer | Note explicite (1 à 10) |

Règles :
- suppression des ratings = 0
- suppression des valeurs invalides
- déduplication (user_id, isbn)

---

### ratings_joinable.parquet

| Colonne | Type | Description |
|--------|------|------------|
| user_id | integer | Identifiant utilisateur |
| isbn | string | Identifiant livre |
| rating | integer | Note utilisateur |

Règles :
- uniquement les ratings ayant :
  - un utilisateur existant
  - un livre existant

Dataset prêt pour jointures SQL et ML

---

## 4. Gold Layer (données analytiques)

### book_popularity.parquet

| Colonne | Type | Description |
|--------|------|------------|
| isbn | string | Identifiant du livre |
| title | string | Titre |
| author | string | Auteur |
| year_of_publication | integer | Année |
| publisher | string | Éditeur |
| ratings_count | integer | Nombre de notes |
| average_rating | float | Moyenne des notes |
| weighted_score | float | Score pondéré |

### weighted_score (important)

Le score pondéré est calculé pour éviter les biais liés aux petits volumes :

- Un livre avec peu de notes mais très élevées ne doit pas être surévalué
- Un livre populaire est favorisé

---

## 5. PostgreSQL Tables

Les tables SQL reflètent les données Silver et Gold :

### books
→ correspond à `books_clean`

### users
→ correspond à `users_clean`

### ratings
→ correspond à `ratings_joinable`

### book_popularity
→ correspond à la table Gold

---

## 6. Relations

| Table source | Colonne | Table cible | Colonne |
|-------------|--------|-------------|--------|
| ratings | user_id | users | user_id |
| ratings | isbn | books | isbn |
| book_popularity | isbn | books | isbn |

---

## 7. Limites des données

- ISBN parfois incohérents ou manquants
- Âges utilisateurs peu fiables
- Données non temporelles (pas de date de rating)
- Dataset statique (pas de mise à jour temps réel)

---

## 8. Utilisation

Ces données sont utilisées pour :
- analyses SQL
- dashboards
- API
- modèles de recommandation (Bloc ML)

---

## 9. Conclusion

Le data dictionary permet de garantir la compréhension, la traçabilité et la qualité des données dans l’ensemble du pipeline BiblioTech.