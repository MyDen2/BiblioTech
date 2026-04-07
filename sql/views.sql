-- quelques vues utiles :

-- top livres les plus populaires
-- top livres les mieux notés avec minimum de votes
-- top auteurs par nombre de livres notés
-- moyenne des notes par année de publication

-- ================================
-- Top livres les plus populaires
-- ================================
CREATE OR REPLACE VIEW vw_top_popular_books AS
SELECT
    isbn,
    title,
    author,
    ratings_count,
    average_rating,
    weighted_score
FROM book_popularity
ORDER BY ratings_count DESC;


-- ================================
-- Top livres les mieux notés (avec minimum de votes)
-- ================================
CREATE OR REPLACE VIEW vw_top_rated_books AS
SELECT
    isbn,
    title,
    author,
    ratings_count,
    average_rating,
    weighted_score
FROM book_popularity
WHERE ratings_count >= 50
ORDER BY weighted_score DESC;


-- ================================
-- Statistiques par auteur
-- ================================
CREATE OR REPLACE VIEW vw_author_stats AS
SELECT
    author,
    COUNT(*) AS books_count,
    SUM(ratings_count) AS total_ratings,
    ROUND(AVG(average_rating), 2) AS avg_rating
FROM book_popularity
GROUP BY author
HAVING COUNT(*) >= 3
ORDER BY total_ratings DESC;


-- ================================
-- Statistiques par année
-- ================================
CREATE OR REPLACE VIEW vw_year_stats AS
SELECT
    year_of_publication,
    COUNT(*) AS books_count,
    SUM(ratings_count) AS total_ratings,
    ROUND(AVG(average_rating), 2) AS avg_rating
FROM book_popularity
WHERE year_of_publication IS NOT NULL
GROUP BY year_of_publication
ORDER BY year_of_publication;


-- ================================
-- Activité utilisateurs
-- ================================
CREATE OR REPLACE VIEW vw_user_activity AS
SELECT
    r.user_id,
    COUNT(*) AS ratings_count,
    ROUND(AVG(r.rating), 2) AS avg_rating
FROM ratings r
GROUP BY r.user_id
ORDER BY ratings_count DESC;