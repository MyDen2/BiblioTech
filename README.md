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

-   interface utilisateur avec **Streamlit** ;

-   tests automatisés avec **pytest**.

Les données sont organisées selon une architecture **Bronze / Silver /
Gold**.

------------------------------------------------------------------------

## Objectifs du projet

-   ingérer les données brutes du dataset Book-Crossing ;

-   construire un pipeline ETL reproductible ;

-   nettoyer et normaliser les données ;

-   stocker les données dans un Data Lake compatible S3 ;

-   distinguer les éditions ISBN des œuvres logiques via `book_key` ;

-   charger les données utiles dans PostgreSQL ;

-   produire des indicateurs analytiques de popularité ;

-   entraîner et évaluer un système de recommandation ;

-   exposer les fonctionnalités via une API REST ;

-   proposer une interface de recherche et de recommandation ;

-   sécuriser les fonctionnalités personnalisées par authentification ;

-   vérifier les principaux composants avec des tests automatisés.

------------------------------------------------------------------------

## Architecture

``` text

Book-Crossing

    |

    | CSV

    v

MinIO Data Lake

    |-- Bronze : données brutes

    |-- Silver : données nettoyées

    `-- Gold   : données agrégées

          |

          +----------+

          |          |

          v          v

     PostgreSQL      ML

          |          |

          |     Modèle item-based

          |     Similarité cosinus

          |          |

          +----+-----+

               v

            FastAPI

               |

               v

           Streamlit
```

------------------------------------------------------------------------

## Documentation

-   `docs/architecture.md`

-   `docs/data_dictionary.md`

-   `docs/privacy.md`

------------------------------------------------------------------------

## Arborescence

``` text

BiblioTech/

├── config/

│   ├── .env

│   └── settings.yaml

├── data/

│   ├── bronze/

│   ├── silver/

│   └── gold/

├── models/

│   └── reco/

│       ├── similarity.joblib

│       ├── book_index_map.joblib

│       └── book_metadata.joblib

├── src/

│   ├── api/

│   │   ├── app.py

│   │   └── database.py

│   ├── extractors/

│   ├── front/

│   │   └── app.py

│   ├── loaders/

│   ├── ml/

│   │   ├── evaluate_reco.py

│   │   ├── predict.py

│   │   ├── recommender.py

│   │   └── train_reco.py

│   ├── transformers/

│   ├── utils/

│   └── main.py

├── tests/

│   ├── conftest.py

│   ├── test_api.py

│   ├── test_book_utils.py

│   └── test_recommender.py

├── sql/

│   ├── schema.sql

│   ├── app_schema.sql

│   └── views.sql

├── docs/

│   ├── architecture.md

│   └── data_dictionary.md

├── docker-compose.yml

├── Dockerfile

├── .gitignore

├── README.md

└── requirements.txt
```

\> Les fichiers de configuration contenant des secrets, les données
locales et les artefacts ML générés ne sont pas destinés à être
versionnés.

------------------------------------------------------------------------

## Dataset

Le projet utilise principalement le dataset **Book-Crossing** :

-   `BX-Book-Ratings.csv`

-   `BX_Books.csv`

-   `BX-Users.csv`

Il contient des informations sur les livres, les utilisateurs
historiques et leurs évaluations.

------------------------------------------------------------------------

## Identification des œuvres

Le dataset original utilise l'ISBN comme identifiant.

Un ISBN représente une **édition** d'un livre et non nécessairement une
œuvre logique. Plusieurs ISBN peuvent donc correspondre à différentes
éditions d'une même œuvre.

BiblioTech génère un identifiant logique `book_key` à partir du titre et
de l'auteur normalisés.

Exemple :

``` text

1984|george orwell
```

L'ISBN est conservé dans les données nettoyées pour identifier les
éditions, tandis que le système de recommandation travaille
principalement au niveau de l'œuvre (`book_key`).

------------------------------------------------------------------------

## Couches de données

### Bronze

La couche Bronze contient les données brutes :

-   `BX-Book-Ratings.csv`

-   `BX_Books.csv`

-   `BX-Users.csv`

### Silver

La couche Silver contient les données nettoyées et normalisées :

-   `ratings_clean.parquet`

-   `books_clean.parquet`

-   `users_clean.parquet`

-   `ratings_joinable.parquet`

`ratings_joinable.parquet` contient les évaluations explicites
exploitables au niveau :

``` text

user_id × book_key
```

Lorsque plusieurs éditions ISBN d'une même œuvre ont été évaluées par un
utilisateur, les évaluations peuvent être agrégées au niveau de l'œuvre.

### Gold

La couche Gold contient :

``` text

book_popularity.parquet
```

Cette table fournit notamment :

-   le nombre de ratings ;

-   la note moyenne ;

-   un score de popularité pondéré.

------------------------------------------------------------------------

## PostgreSQL

### Données historiques

Les données issues du dataset sont chargées dans :

-   `books`

-   `users`

-   `ratings`

-   `book_popularity`

### Données applicatives

Les utilisateurs réels de l'application sont stockés séparément dans :

-   `app_users`

-   `user_book_ratings`

Cette séparation évite de confondre les utilisateurs historiques ayant
servi à construire le modèle avec les utilisateurs de l'application
BiblioTech.

### Authentification des utilisateurs

Les utilisateurs applicatifs disposent d'un mot de passe permettant leur
authentification.

Le mot de passe n'est jamais enregistré en clair. Il est haché avec
**Argon2id** avant son stockage dans la colonne `password_hash` de la
table `app_users`.

L'authentification est réalisée par l'API à partir de l'adresse email et
du mot de passe. Après authentification, l'API génère un **JSON Web
Token (JWT)** temporaire permettant d'identifier l'utilisateur lors des
requêtes protégées.

Les routes liées aux données personnelles de l'utilisateur utilisent
l'identité contenue dans le JWT plutôt qu'un `app_user_id` fourni
librement par le client.

------------------------------------------------------------------------

## Système de recommandation

BiblioTech utilise un système de recommandation **collaboratif
item-based**.

Les **5 000 œuvres les plus notées** sont sélectionnées puis
représentées dans une matrice sparse :

``` text

utilisateurs × œuvres
```

Une similarité cosinus est calculée entre les œuvres.

Le modèle peut ensuite fonctionner selon deux modes :

-   recommandation d'œuvres similaires à une œuvre donnée ;

-   recommandation personnalisée à partir des œuvres appréciées par un
    utilisateur de l'application.

Les utilisateurs applicatifs sont projetés dans l'espace de similarité
appris sur les évaluations historiques. Il n'est donc pas nécessaire de
réentraîner le modèle après chaque nouvelle notation.

### Artefacts générés

Les artefacts ML sont enregistrés dans `models/reco/` :

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

------------------------------------------------------------------------

## Évaluation du système de recommandation

Une évaluation offline permet de mesurer quantitativement la capacité du
système à retrouver des œuvres pertinentes.

### Protocole

L'évaluation utilise une approche **leave-one-out** sur un échantillon
de **1 000 utilisateurs historiques** possédant au moins deux œuvres
appréciées, définies ici par une note supérieure ou égale à `7/10`.

Pour chaque utilisateur :

1. une œuvre appréciée est masquée ;

2. les autres œuvres appréciées constituent le profil connu ;

3. le système génère un Top 5 de recommandations ;

4. les recommandations sont comparées à l'œuvre masquée.

L'évaluation est limitée aux œuvres appartenant au catalogue des **5 000
œuvres** du modèle.

### Métriques

Les métriques utilisées sont :

-   **Precision@5** : proportion d'éléments pertinents dans les cinq
    recommandations ;

-   **Recall@5** : capacité à retrouver l'œuvre pertinente masquée ;

-   **HitRate@5** : proportion d'utilisateurs pour lesquels l'œuvre
    masquée apparaît dans le Top 5 ;

-   **Coverage** : proportion du catalogue apparaissant dans les
    recommandations.

### Résultats

| Métrique | Filtrage collaboratif |

|---|---:|

| Precision@5 | 3,86 % |

| Recall@5 | 19,30 % |

| HitRate@5 | 19,30 % |

| Coverage | 41,10 % |

Dans ce protocole leave-one-out, une seule œuvre pertinente est masquée
par utilisateur. `Recall@5` et `HitRate@5` sont donc identiques.

### Comparaison avec une baseline

Le système collaboratif est comparé à une baseline simple fondée sur les
œuvres les plus populaires.

\| Méthode \| HitRate@5 \|

\|---\|---:\|

\| Baseline popularité \| 2,30 % \|

\| Filtrage collaboratif item-based \| **19,30 %** \|

Le filtrage collaboratif obtient ainsi :

-   un gain absolu de **17 points de HitRate@5** ;

-   un HitRate@5 environ **8,4 fois supérieur** à celui de la baseline.

Cette comparaison montre que l'exploitation des similarités entre œuvres
apporte une amélioration mesurable par rapport à une stratégie reposant
uniquement sur la popularité.

### Reproduire l'évaluation

``` powershell

python -m src.ml.evaluate_reco
```

### Limite méthodologique

L'évaluation actuelle réutilise la matrice de similarité calculée lors
de l'entraînement sur l'ensemble des interactions historiques.

Elle fournit une comparaison reproductible avec la baseline, mais elle
ne constitue pas une évaluation totalement isolée des données ayant
servi à construire les similarités.

Une évaluation future plus stricte consisterait à effectuer le découpage
entraînement/test **avant** le calcul de la matrice de similarité.

Le dataset Book-Crossing ne fournissant pas de timestamps d'évaluation
exploitables, une validation temporelle directe n'est pas disponible
dans le protocole actuel.

------------------------------------------------------------------------

## API FastAPI

Principaux endpoints :

``` text
GET  /books/search
GET  /recommend/book
GET  /recommend/user
POST /users
POST /login
POST /ratings
```

L'API permet notamment :

-   de rechercher des œuvres ;
-   d'obtenir des recommandations à partir d'une œuvre ;
-   de créer un utilisateur applicatif ;
-   d'authentifier un utilisateur ;
-   de générer un token JWT ;
-   d'enregistrer ou mettre à jour les évaluations de l'utilisateur
    authentifié ;
-   d'obtenir des recommandations personnalisées.

### Authentification

La création d'un utilisateur nécessite un mot de passe.

Le mot de passe est haché avec **Argon2id** et seul son hash est
enregistré dans PostgreSQL.

L'endpoint `POST /login` vérifie l'adresse email et le mot de passe puis
retourne un token JWT.

Les routes `POST /ratings` et `GET /recommend/user` sont protégées par
authentification Bearer.

L'identité de l'utilisateur est extraite du JWT. Le client ne fournit
donc pas directement `app_user_id` pour enregistrer une évaluation ou
obtenir ses recommandations personnalisées.

Une requête vers une route protégée sans token valide retourne une
erreur `401 Unauthorized`.

### Lancer l'API

``` powershell
uvicorn src.api.app:app --reload
```

La documentation interactive Swagger est disponible sur :

``` text
/docs
```

Le bouton **Authorize** de Swagger permet de fournir le JWT pour tester
les routes protégées.

---**

## Interface Streamlit

L'interface Streamlit permet de :

-   rechercher un livre ;

-   sélectionner une œuvre ;

-   consulter ses métadonnées ;

-   afficher sa couverture lorsqu'elle est disponible ;

-   choisir le nombre de recommandations ;

-   obtenir des œuvres similaires.

Lancer l'interface :

``` powershell

streamlit run src/front/app.py
```

------------------------------------------------------------------------

## Tests automatisés

Le projet comporte des tests automatisés avec **pytest** couvrant
notamment :

-   la normalisation des textes et la construction de `book_key` ;
-   la logique du système de recommandation ;
-   la recommandation personnalisée ;
-   l'exclusion des œuvres déjà évaluées ;
-   les principaux endpoints FastAPI ;
-   la validation des données reçues par l'API ;
-   la création des utilisateurs ;
-   l'authentification avec mot de passe ;
-   la génération du JWT ;
-   le refus des identifiants invalides ;
-   la protection des routes nécessitant une authentification ;
-   l'association des ratings à l'utilisateur authentifié ;
-   plusieurs cas d'erreur.

Lancer les tests :

``` powershell
pytest -v
```

État actuel :

``` text
39 passed
```

Ces tests vérifient le fonctionnement logiciel. Ils sont complémentaires
à l'évaluation offline du modèle, qui mesure la qualité des
recommandations.

------------------------------------------------------------------------

## Sécurité applicative

BiblioTech intègre une couche d'authentification pour les utilisateurs
applicatifs.

Les principales mesures mises en œuvre sont :

-   hachage des mots de passe avec Argon2id ;
-   absence de stockage des mots de passe en clair ;
-   absence du hash dans les réponses de l'API ;
-   authentification par email et mot de passe ;
-   génération de tokens JWT temporaires ;
-   protection des routes utilisateur avec Bearer Authentication ;
-   identification de l'utilisateur à partir du JWT ;
-   secrets techniques conservés dans `config/.env` et exclus de Git.

L'application reste actuellement un prototype local. Une mise en
production publique nécessiterait des mesures supplémentaires telles que
HTTPS, gestion de la récupération des mots de passe, politique de
conservation des données, mécanisme utilisateur de suppression du compte
et sécurisation de l'infrastructure.

---**

## Infrastructure

Les principaux services sont :

-   **MinIO** : stockage objet compatible S3 ;

-   **PostgreSQL** : base relationnelle ;

-   **pgAdmin** : administration PostgreSQL.

Démarrer l'infrastructure :

``` powershell

docker compose up -d
```

------------------------------------------------------------------------

## Configuration

Le fichier :

``` text
config/.env
```

contient notamment les variables nécessaires :

-   à MinIO ;
-   à PostgreSQL ;
-   à la signature et à la durée de validité des tokens JWT.

Exemple de variables liées à l'authentification :

``` env
JWT_SECRET_KEY=...
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

`JWT_SECRET_KEY` doit être une valeur secrète et suffisamment longue.

Le fichier `.env` contient des informations sensibles et ne doit jamais
être versionné.

---**

## Installation

Créer l'environnement virtuel :

``` powershell

python -m venv .venv
```

L'activer sous PowerShell :

``` powershell

.venv\Scripts\Activate.ps1
```

Installer les dépendances :

``` powershell

pip install -r requirements.txt
```

------------------------------------------------------------------------

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
le modèle, les artefacts ML doivent être reconstruits :

``` powershell

python -m src.ml.train_reco
```

------------------------------------------------------------------------

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

------------------------------------------------------------------------

## Exemple de recommandation

Pour l'œuvre :

``` text

1984 — George Orwell
```

le modèle retourne notamment :

-   **Animal Farm** --- George Orwell ;

-   **Brave New World** --- Aldous Huxley ;

-   **Lord of the Flies** --- William Gerald Golding.

Les recommandations sont déterminées à partir des comportements de
notation des utilisateurs historiques et de la similarité cosinus entre
œuvres.

------------------------------------------------------------------------

## Technologies

| Technologie | Utilisation |

|---|---|

| Python | Développement principal |

| Pandas | ETL et préparation des données |

| MinIO | Data Lake compatible S3 |

| Parquet | Stockage analytique |

| PostgreSQL | Base relationnelle |

| SQLAlchemy | Accès PostgreSQL |

| SciPy | Matrices sparse |

| scikit-learn | Similarité cosinus |

| joblib | Sérialisation des artefacts ML |

| FastAPI | API REST | | pwdlib / Argon2id | Hachage sécurisé des
mots de passe | | PyJWT | Génération et validation des tokens JWT |

| Streamlit | Interface utilisateur |

| pytest | Tests automatisés |

| Docker | Infrastructure |

| ftfy | Correction d'encodage |

------------------------------------------------------------------------

## Conclusion

BiblioTech met en œuvre une architecture data complète allant de
l'ingestion de données brutes jusqu'à leur exploitation dans une
application de recherche et de recommandation.

Le projet combine **Data Engineering, SQL, Machine Learning, API, tests
automatisés et interface web** dans une architecture cohérente centrée
sur les œuvres identifiées par `book_key`.

Le système de recommandation ne repose pas uniquement sur une
démonstration qualitative : son fonctionnement est évalué offline et
comparé à une baseline de popularité. Sur le protocole actuel, le
filtrage collaboratif atteint un **HitRate@5 de 19,3 % contre 2,3 % pour
la baseline**, ce qui met en évidence l'apport de la personnalisation
par similarité entre œuvres.
