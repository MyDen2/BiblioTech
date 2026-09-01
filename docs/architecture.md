# BiblioTech – Architecture Data

## 1. Objectif du projet

BiblioTech est une plateforme de recherche et de recommandation de livres
construite à partir du dataset Book-Crossing.

Le projet met en place une architecture data complète permettant :

- l'ingestion de données brutes ;
- leur nettoyage et leur normalisation ;
- leur stockage dans un Data Lake ;
- leur exploitation dans PostgreSQL ;
- l'entraînement d'un système de recommandation ;
- l'exposition des données et recommandations via une API FastAPI ;
- leur consultation depuis une interface Streamlit.

---

## 2. Architecture globale

L'architecture générale du projet est la suivante :

Book-Crossing (CSV)
        ↓
MinIO
        ↓
┌─────────────────────────────┐
│ Bronze : données brutes     │
│ Silver : données nettoyées  │
│ Gold   : données agrégées   │
└─────────────────────────────┘
        ↓
   ┌───────────────┐
   │               │
PostgreSQL         ML
   │               │
   │        Modèle de recommandation
   │               │
   └───────┬───────┘
           ↓
        FastAPI
           ↓
       Streamlit

---

## 3. Data Lake – MinIO

Le stockage objet est assuré par MinIO, compatible avec l'API Amazon S3.

Les données sont organisées selon une architecture en trois couches :
Bronze, Silver et Gold.

### Bronze

La couche Bronze contient les données brutes du dataset Book-Crossing.

Format principal : CSV.

Exemples :

- `BX_Books.csv`
- `BX-Users.csv`
- `BX-Book-Ratings.csv`

Les données sont conservées au plus proche de leur format source.

### Silver

La couche Silver contient les données nettoyées, normalisées et rendues
cohérentes entre elles.

Format : Parquet.

Principaux fichiers :

- `books_clean.parquet`
- `users_clean.parquet`
- `ratings_clean.parquet`
- `ratings_joinable.parquet`

Le nettoyage comprend notamment :

- normalisation des noms de colonnes ;
- correction de problèmes d'encodage ;
- normalisation de l'affichage des auteurs ;
- validation des années de publication ;
- suppression des doublons ;
- filtrage des ratings invalides ou implicites ;
- suppression des références orphelines.

### Gold

La couche Gold contient les données préparées pour des usages analytiques.

Principal fichier :

- `book_popularity.parquet`

Cette table contient notamment :

- `book_key`
- `title`
- `author`
- `year_of_publication`
- `publisher`
- URLs des couvertures
- `ratings_count`
- `average_rating`
- `weighted_score`

---

## 4. Identification des œuvres avec `book_key`

Le dataset Book-Crossing identifie initialement les livres par ISBN.

Un ISBN représente cependant une édition physique d'un livre et non
nécessairement une œuvre logique.

BiblioTech introduit donc un identifiant `book_key`, construit à partir
du titre et de l'auteur normalisés.

Exemple :

`1984|george orwell`

Plusieurs éditions ISBN correspondant à une même œuvre peuvent ainsi
être regroupées.

Cette représentation est utilisée pour :

- l'agrégation des ratings ;
- la table de popularité ;
- PostgreSQL ;
- le modèle de recommandation ;
- l'API ;
- l'interface utilisateur.

---

## 5. Pipeline ETL

Les transformations sont principalement réalisées en Python avec Pandas.

### 5.1 Ingestion

Les données CSV sont stockées dans la couche Bronze de MinIO.

Les accès au stockage objet sont centralisés dans le module `s3_io`.

### 5.2 Nettoyage des livres

Le pipeline produit `books_clean.parquet`.

Les principales opérations sont :

- nettoyage des ISBN ;
- correction des problèmes d'encodage ;
- nettoyage des titres, auteurs et éditeurs ;
- normalisation de l'affichage des auteurs ;
- validation des années de publication ;
- déduplication des ISBN ;
- génération de `book_key`.

### 5.3 Nettoyage des utilisateurs et ratings

Les utilisateurs et ratings sont nettoyés séparément.

Les ratings implicites (`rating = 0`) ne sont pas utilisés comme notes
explicites dans le système de recommandation.

### 5.4 Ratings joignables

`ratings_joinable.parquet` conserve uniquement les ratings associés
à des utilisateurs et des œuvres existants.

Les ratings sont ensuite ramenés au niveau logique :

`user_id × book_key`

Lorsqu'un utilisateur a noté plusieurs éditions correspondant à une même
œuvre, ces ratings sont agrégés.

Le fichier final contient :

- `user_id`
- `book_key`
- `rating`

---

## 6. Couche Gold – Popularité des œuvres

La table `book_popularity.parquet` agrège les ratings au niveau
`book_key`.

Pour chaque œuvre, elle calcule :

- le nombre de ratings (`ratings_count`) ;
- la note moyenne (`average_rating`) ;
- un score pondéré (`weighted_score`).

Le score pondéré limite la survalorisation des œuvres ayant une excellente
moyenne mais très peu de ratings.

La table est ensuite triée par score pondéré puis par nombre de ratings.

---

## 7. PostgreSQL

PostgreSQL fournit la couche relationnelle utilisée par l'application
et permet également l'exploitation SQL des données.

### Tables issues du dataset

- `books`
- `users`
- `ratings`
- `book_popularity`

Le modèle relationnel utilise principalement `book_key` pour identifier
une œuvre.

Relations principales :

`ratings.user_id → users.user_id`

`ratings.book_key → books.book_key`

`book_popularity.book_key → books.book_key`

### Tables applicatives

Deux tables sont séparées des utilisateurs historiques du dataset :

- `app_users`
- `user_book_ratings`

`app_users` représente les utilisateurs réels créés depuis l'application.

`user_book_ratings` contient leurs notes personnelles et utilise également
`book_key`.

Cette séparation évite de mélanger les utilisateurs historiques ayant servi
à construire le modèle avec les utilisateurs de l'application.

---

## 8. Modèle de recommandation

BiblioTech utilise actuellement un système de recommandation collaborative
item-based.

### Données d'entraînement

Le modèle est entraîné à partir de `ratings_joinable.parquet`.

Les 5 000 œuvres ayant reçu le plus de ratings sont sélectionnées afin
de limiter la taille du modèle et de conserver suffisamment de signal
collaboratif.

### Matrice utilisateur × œuvre

Une matrice sparse est construite sous la forme :

`utilisateurs × book_key`

Chaque cellule contient le rating attribué par un utilisateur à une œuvre.

### Similarité

La matrice est transposée afin de comparer les œuvres entre elles.

Une similarité cosinus est calculée entre les vecteurs de ratings des
différentes œuvres.

Le modèle peut ainsi produire des recommandations du type :

`1984 → Animal Farm, Brave New World, ...`

### Artefacts ML

Les artefacts sont sauvegardés dans :

`models/reco/`

avec notamment :

- `similarity.joblib`
- `book_index_map.joblib`
- `book_metadata.joblib`

---

## 9. Recommandation utilisateur

Les utilisateurs historiques du dataset servent à entraîner le modèle.

Les nouveaux utilisateurs de l'application sont stockés séparément dans
`app_users`.

Leurs notes sont enregistrées dans `user_book_ratings`.

À partir des œuvres qu'un utilisateur de l'application a appréciées,
BiblioTech exploite la matrice de similarité pré-calculée pour générer
des recommandations personnalisées.

Il n'est donc pas nécessaire de réentraîner immédiatement le modèle
lorsqu'un nouvel utilisateur s'inscrit ou ajoute une note.

---

---

## 10. Évaluation du système de recommandation

Le système de recommandation fait l'objet d'une évaluation offline afin
de mesurer quantitativement sa capacité à retrouver des œuvres pertinentes.

Le script d'évaluation est disponible dans :

`src/ml/evaluate_reco.py`

### 10.1 Protocole d'évaluation

L'évaluation utilise une approche de type **leave-one-out**.

Elle est réalisée sur un échantillon de 1 000 utilisateurs historiques
possédant au moins deux œuvres appréciées, une œuvre étant considérée
comme appréciée lorsque sa note est supérieure ou égale à 7/10.

L'évaluation est limitée aux œuvres appartenant au catalogue des
5 000 œuvres utilisées par le modèle.

Pour chaque utilisateur :

1. une œuvre appréciée est masquée et utilisée comme vérité terrain ;
2. les autres œuvres appréciées constituent le profil connu ;
3. le système génère un Top 5 de recommandations ;
4. les recommandations sont comparées à l'œuvre masquée.

Cette approche permet d'évaluer la capacité du modèle à retrouver une
préférence connue à partir des autres préférences de l'utilisateur.

### 10.2 Métriques

Quatre indicateurs sont utilisés :

- **Precision@5** : proportion d'œuvres pertinentes parmi les cinq
  recommandations ;
- **Recall@5** : proportion des œuvres pertinentes retrouvées dans le
  Top 5 ;
- **HitRate@5** : proportion d'utilisateurs pour lesquels au moins une
  œuvre pertinente apparaît dans le Top 5 ;
- **Coverage** : proportion du catalogue apparaissant dans les
  recommandations générées.

Dans le protocole leave-one-out utilisé ici, une seule œuvre pertinente
est masquée par utilisateur. `Recall@5` et `HitRate@5` prennent donc la
même valeur.

### 10.3 Résultats

Les résultats obtenus sur 1 000 utilisateurs sont :

| Métrique | Résultat |
|---|---:|
| Precision@5 | 0,0386 |
| Recall@5 | 0,1930 |
| HitRate@5 | 0,1930 |
| Coverage | 0,4110 |

Le modèle retrouve donc l'œuvre masquée dans son Top 5 pour 19,3 % des
utilisateurs évalués.

Les recommandations produites pendant cette évaluation couvrent 41,1 %
du catalogue de 5 000 œuvres utilisé par le modèle.

### 10.4 Baseline de popularité

Afin de disposer d'un point de comparaison, le filtrage collaboratif
est évalué face à une baseline simple fondée sur la popularité.

Cette baseline recommande les œuvres appréciées les plus fréquentes,
en excluant celles déjà utilisées pour constituer le profil connu de
l'utilisateur.

| Méthode | HitRate@5 |
|---|---:|
| Baseline popularité | 0,0230 |
| Filtrage collaboratif item-based | 0,1930 |

Le filtrage collaboratif améliore ainsi le HitRate@5 de **0,1700**,
soit **17 points**, par rapport à la baseline.

Son HitRate@5 est environ **8,4 fois supérieur** à celui de la stratégie
de popularité.

Cette comparaison met en évidence l'apport du signal collaboratif par
rapport à une stratégie globale ne tenant pas compte du profil de
l'utilisateur.

### 10.5 Limites du protocole

L'évaluation actuelle réutilise la matrice de similarité calculée lors
de l'entraînement sur l'ensemble des interactions historiques.

Elle fournit donc une comparaison reproductible entre le filtrage
collaboratif et la baseline, mais elle ne constitue pas une évaluation
totalement isolée des données ayant servi à construire les similarités.

Par ailleurs, le dataset Book-Crossing ne fournit pas de timestamps
d'évaluation exploitables permettant de réaliser directement une
validation temporelle.

---

## 11. API FastAPI

FastAPI expose les principales fonctionnalités de BiblioTech.

Fonctionnalités principales :

- recherche d'œuvres ;
- création d'un utilisateur ;
- enregistrement ou mise à jour d'un rating ;
- recommandation à partir d'une œuvre ;
- recommandation personnalisée pour un utilisateur.

Exemples d'endpoints :

- `GET /books/search`
- `GET /recommend/book`
- `GET /recommend/user/{app_user_id}`
- `POST /users`
- `POST /ratings`

L'identifiant fonctionnel utilisé pour les œuvres est `book_key`.

---

## 12. Interface Streamlit

Une interface Streamlit consomme l'API FastAPI.

Elle permet notamment :

- de rechercher un livre par titre ou auteur ;
- de sélectionner une œuvre ;
- d'afficher ses métadonnées ;
- d'afficher sa couverture lorsqu'elle est disponible ;
- de demander des recommandations ;
- d'afficher les œuvres similaires et leurs scores.

Les couvertures sont obtenues à partir des URLs présentes dans le dataset.

---

## 13. Vues SQL

Des vues SQL peuvent être utilisées pour simplifier les analyses métier,
notamment :

- `vw_top_popular_books`
- `vw_top_rated_books`
- `vw_author_stats`
- `vw_year_stats`
- `vw_user_activity`

Elles permettent d'exposer des indicateurs analytiques sans répéter les
requêtes d'agrégation.

---

## 14. Technologies utilisées

| Technologie | Rôle |
|---|---|
| MinIO | Data Lake compatible S3 |
| PostgreSQL | Stockage relationnel |
| Pandas | Nettoyage et transformation |
| Parquet | Stockage analytique |
| boto3 | Communication avec MinIO |
| SQLAlchemy | Accès à PostgreSQL |
| SciPy | Matrice sparse |
| scikit-learn | Similarité cosinus |
| joblib | Sérialisation des artefacts ML |
| FastAPI | API REST |
| Streamlit | Interface utilisateur |
| Docker | Conteneurisation |
| ftfy | Correction de problèmes d'encodage |

---

## 15. Choix techniques

### Pourquoi MinIO ?

MinIO permet de reproduire localement une architecture de stockage objet
compatible S3 et de séparer les données selon leur niveau de transformation.

### Pourquoi Parquet ?

Parquet est un format colonne adapté aux traitements analytiques. Il offre
une bonne compression et permet des lectures efficaces avec Pandas.

### Pourquoi PostgreSQL ?

PostgreSQL fournit une couche relationnelle robuste pour les requêtes SQL
et les données nécessaires à l'application.

### Pourquoi `book_key` ?

Un ISBN représente une édition alors que BiblioTech cherche principalement
à recommander des œuvres.

`book_key` permet donc de regrouper plusieurs éditions représentant
le même livre logique.

### Pourquoi un modèle item-based ?

La similarité entre œuvres peut être pré-calculée à partir des comportements
des utilisateurs historiques.

Cette approche permet ensuite de générer rapidement des recommandations,
y compris pour les nouveaux utilisateurs de l'application dès qu'ils ont
fourni suffisamment de ratings.

---

## 16. Conclusion

BiblioTech met en œuvre une chaîne data complète allant des données brutes
jusqu'à une application de recommandation.

L'architecture sépare clairement :

- le stockage brut et transformé dans MinIO ;
- les données relationnelles dans PostgreSQL ;
- les utilisateurs historiques utilisés pour construire le modèle ;
- les utilisateurs réels de l'application ;
- les artefacts du système de recommandation ;
- l'exposition des fonctionnalités via FastAPI ;
- leur utilisation dans Streamlit.

La qualité du projet est vérifiée à deux niveaux complémentaires :

- des tests automatisés valident le fonctionnement des principaux
  composants logiciels ;
- une évaluation offline mesure quantitativement les performances du
  système de recommandation et les compare à une baseline de popularité.

Les 31 tests automatisés passent et le modèle collaboratif atteint un
HitRate@5 de 19,3 %, contre 2,3 % pour la baseline de popularité.

L'utilisation de `book_key` permet enfin de raisonner principalement au
niveau de l'œuvre plutôt qu'au niveau de chaque édition ISBN.