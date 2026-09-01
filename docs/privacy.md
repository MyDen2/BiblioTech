# Politique de confidentialité et protection des données

## 1. Objet du document

Ce document décrit les principes de protection des données appliqués
dans le projet **BiblioTech**.

BiblioTech est un prototype local de plateforme de recherche et de
recommandation de livres construit à partir du dataset Book-Crossing. Il
combine un pipeline de données, une base PostgreSQL, un système de
recommandation, une API FastAPI et une interface Streamlit.

L'objectif de cette documentation est d'identifier les données
manipulées, de décrire les mesures techniques mises en œuvre et de
présenter les limites actuelles du prototype au regard de la protection
des données personnelles.

BiblioTech ne prétend pas constituer, dans son état actuel, une solution
de production garantissant à elle seule une conformité complète au RGPD.

------------------------------------------------------------------------

## 2. Catégories de données

Le projet distingue deux catégories d'utilisateurs :

1.  les utilisateurs historiques provenant du dataset Book-Crossing ;
2.  les utilisateurs réels créés dans l'application BiblioTech.

Cette séparation est conservée dans l'architecture et dans PostgreSQL
afin de ne pas confondre les données utilisées pour construire le modèle
avec les données produites par l'application.

### 2.1 Données historiques Book-Crossing

Les données historiques proviennent du dataset Book-Crossing et
comprennent notamment :

-   un identifiant historique `user_id` ;
-   la localisation ;
-   le pays lorsque celui-ci peut être extrait ;
-   l'âge lorsqu'il est exploitable ;
-   les évaluations attribuées aux livres.

Ces données sont utilisées pour :

-   préparer les données du système de recommandation ;
-   construire les relations entre utilisateurs historiques et œuvres ;
-   calculer les similarités entre œuvres ;
-   produire des statistiques de popularité ;
-   évaluer offline le système de recommandation.

Les utilisateurs historiques ne sont pas utilisés comme comptes
applicatifs.

### 2.2 Données des utilisateurs BiblioTech

Les comptes créés dans l'application sont stockés dans la table
`app_users`.

Les informations concernées sont :

-   `app_user_id` ;
-   `username` ;
-   `email` ;
-   `password_hash` ;
-   `age` ;
-   `country` ;
-   `created_at`.

Les évaluations effectuées dans l'application sont stockées séparément
dans `user_book_ratings` avec notamment :

-   `rating_id` ;
-   `app_user_id` ;
-   `book_key` ;
-   `rating` ;
-   `created_at`.

Les utilisateurs applicatifs et les utilisateurs historiques du dataset
sont donc séparés.

------------------------------------------------------------------------

## 3. Finalités des traitements

Les données applicatives sont utilisées uniquement pour les
fonctionnalités du prototype BiblioTech, notamment :

-   créer et identifier un compte utilisateur ;
-   authentifier l'utilisateur ;
-   enregistrer ses évaluations de livres ;
-   construire son profil de préférences ;
-   générer des recommandations personnalisées.

Les évaluations des utilisateurs applicatifs sont projetées dans
l'espace de similarité construit à partir des données historiques. Elles
ne nécessitent pas un réentraînement du modèle après chaque nouvelle
notation.

------------------------------------------------------------------------

## 4. Minimisation des données

BiblioTech applique un principe de minimisation en limitant les
informations demandées aux données utiles au fonctionnement du
prototype.

L'application ne prévoit pas de collecte de données telles que :

-   numéro de téléphone ;
-   adresse postale complète ;
-   données bancaires ;
-   document d'identité.

L'âge et le pays permettent de conserver des informations de profil
limitées, tandis que l'adresse email sert à identifier le compte lors de
l'authentification.

Dans une version destinée à la production, la nécessité de chaque donnée
personnelle devrait être réévaluée en fonction des finalités réellement
retenues.

------------------------------------------------------------------------

## 5. Sécurité des mots de passe

Les mots de passe ne sont jamais stockés en clair dans PostgreSQL.

Lors de la création d'un utilisateur, le mot de passe est transformé en
hash à l'aide d'**Argon2id**, via `pwdlib`.

Seul le résultat du hachage est enregistré dans :

``` text
app_users.password_hash
```

Le mot de passe original n'est pas retourné par l'API et le hash n'est
pas exposé dans les réponses destinées au client.

Lors de la connexion, le mot de passe fourni est vérifié par comparaison
avec le hash enregistré.

------------------------------------------------------------------------

## 6. Authentification et JWT

L'authentification est réalisée via :

``` text
POST /login
```

Après vérification de l'adresse email et du mot de passe, l'API génère
un **JSON Web Token (JWT)** temporaire.

Dans la configuration actuelle, la durée de validité prévue est de 60
minutes.

Les routes personnalisées suivantes sont protégées :

``` text
POST /ratings
GET  /recommend/user
```

Le token est transmis à l'API avec une authentification de type
**Bearer**.

L'identité de l'utilisateur est déterminée à partir du champ `sub` du
JWT. L'utilisateur n'envoie donc pas librement un `app_user_id` pour
enregistrer une évaluation ou demander ses recommandations
personnalisées.

Cette approche réduit notamment le risque qu'un client tente d'utiliser
directement l'identifiant d'un autre utilisateur pour accéder aux
fonctionnalités personnalisées.

------------------------------------------------------------------------

## 7. Gestion des secrets

Les informations techniques sensibles sont placées dans :

``` text
config/.env
```

Ce fichier contient notamment les paramètres nécessaires à :

-   PostgreSQL ;
-   MinIO ;
-   la signature des tokens JWT.

La clé `JWT_SECRET_KEY` ne doit pas être stockée directement dans le
code source.

Le fichier `.env` est exclu du versionnement Git et ne doit pas être
publié dans le dépôt.

Les tokens JWT et les mots de passe utilisés lors des tests ou
démonstrations doivent également être considérés comme des informations
sensibles et ne doivent pas être partagés ou intégrés à la documentation
publique.

------------------------------------------------------------------------

## 8. Contrôle d'accès

Les fonctionnalités générales de consultation peuvent rester publiques,
notamment :

``` text
GET /books/search
GET /recommend/book
```

Les fonctionnalités associées aux données personnelles d'un utilisateur
nécessitent une authentification :

``` text
POST /ratings
GET /recommend/user
```

Une requête effectuée vers une route protégée sans authentification
valide est refusée avec une réponse `401 Unauthorized`.

L'identifiant applicatif utilisé par ces routes provient du JWT
authentifié.

------------------------------------------------------------------------

## 9. Conservation et suppression des données

La relation entre `app_users` et `user_book_ratings` utilise une
suppression en cascade au niveau PostgreSQL.

Ainsi, la suppression d'un utilisateur dans la base permet également de
supprimer les évaluations applicatives qui lui sont associées.

Cependant, le prototype ne fournit pas encore de fonctionnalité
permettant à l'utilisateur de supprimer lui-même son compte depuis
l'interface ou l'API.

Aucune politique automatisée de durée de conservation des comptes et des
évaluations applicatives n'est actuellement mise en œuvre.

Pour une mise en production, il serait nécessaire de définir notamment :

-   une durée de conservation adaptée aux finalités ;
-   une procédure de suppression de compte ;
-   une procédure permettant de traiter les demandes relatives aux
    droits des personnes ;
-   les règles applicables aux sauvegardes et aux journaux techniques.

------------------------------------------------------------------------

## 10. Droits des personnes

Dans un service déployé auprès de véritables utilisateurs, la gestion
des données personnelles devrait permettre de répondre aux droits
applicables, selon le contexte juridique du traitement, notamment :

-   droit d'accès ;
-   droit de rectification ;
-   droit à l'effacement ;
-   droit à la limitation ;
-   droit à la portabilité lorsque celui-ci est applicable ;
-   droit d'opposition lorsque celui-ci est applicable.

BiblioTech étant actuellement un prototype local, ces mécanismes ne sont
pas tous disponibles directement depuis l'interface.

La suppression en cascade constitue une base technique pour l'effacement
des données applicatives, mais elle ne remplace pas un processus complet
de gestion des droits.

------------------------------------------------------------------------

## 11. Données et système de recommandation

Le modèle de recommandation est entraîné à partir des évaluations
historiques issues de Book-Crossing.

Le système est un filtrage collaboratif **item-based** fondé sur une
similarité cosinus entre œuvres.

Pour un utilisateur de l'application, les recommandations personnalisées
utilisent les œuvres qu'il a évaluées et, en particulier, celles
considérées comme appréciées par le système.

Les comptes applicatifs ne sont pas fusionnés avec les identifiants des
utilisateurs historiques du dataset.

Les artefacts du modèle contiennent les informations nécessaires à la
recommandation des œuvres et ne constituent pas une base de comptes
utilisateurs BiblioTech.

------------------------------------------------------------------------

## 12. Tests de sécurité fonctionnelle

Les tests automatisés du projet couvrent notamment :

-   la création des utilisateurs ;
-   la validation des mots de passe ;
-   le login ;
-   le refus d'identifiants incorrects ;
-   la protection des routes authentifiées ;
-   le refus d'accès sans authentification ;
-   l'association d'une évaluation à l'utilisateur authentifié ;
-   la recommandation personnalisée associée à l'utilisateur
    authentifié.

À l'état actuel du projet, la suite automatisée comporte :

``` text
39 passed
```

Ces tests vérifient le comportement logiciel attendu. Ils ne constituent
pas à eux seuls un audit de sécurité ou de conformité RGPD.

------------------------------------------------------------------------

## 13. Mesures mises en œuvre

À l'état actuel, BiblioTech met notamment en œuvre :

  -----------------------------------------------------------------------
  Mesure                              État
  ----------------------------------- -----------------------------------
  Séparation données historiques /    Mise en œuvre
  utilisateurs applicatifs            

  Hachage des mots de passe avec      Mise en œuvre
  Argon2id                            

  Absence de stockage du mot de passe Mise en œuvre
  en clair                            

  Authentification par email et mot   Mise en œuvre
  de passe                            

  JWT temporaire                      Mise en œuvre

  Protection des routes utilisateur   Mise en œuvre

  Identité utilisateur issue du JWT   Mise en œuvre

  Secrets dans `.env` exclu de Git    Mise en œuvre

  Suppression en cascade des ratings  Mise en œuvre au niveau PostgreSQL
  lors de la suppression d'un compte  

  Suppression de compte accessible à  À mettre en œuvre
  l'utilisateur                       

  Politique de conservation           À définir

  Réinitialisation du mot de passe    À mettre en œuvre

  HTTPS pour un déploiement public    À mettre en œuvre

  Révocation / renouvellement des     À mettre en œuvre
  tokens                              
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 15. Positionnement du projet

La protection des données est prise en compte dans la conception de
BiblioTech à travers la séparation des données, la limitation des
informations applicatives, le hachage des mots de passe, la gestion des
secrets et le contrôle d'accès par JWT.

Ces mesures améliorent la sécurité du prototype et démontrent la prise
en compte des enjeux liés aux données personnelles.
