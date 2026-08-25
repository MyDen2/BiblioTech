DROP TABLE IF EXISTS user_book_ratings;
DROP TABLE IF EXISTS app_users;

DROP TABLE IF EXISTS book_popularity;
DROP TABLE IF EXISTS ratings;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS books;


CREATE TABLE books (
    book_key TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    year_of_publication INTEGER,
    publisher TEXT,
    image_url_s TEXT,
    image_url_m TEXT,
    image_url_l TEXT
);


CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    location TEXT,
    country TEXT,
    age INTEGER
);


CREATE TABLE ratings (
    user_id BIGINT NOT NULL,
    book_key TEXT NOT NULL,
    rating NUMERIC(4,2) NOT NULL CHECK (rating BETWEEN 1 AND 10),

    PRIMARY KEY (user_id, book_key),

    CONSTRAINT fk_ratings_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id),

    CONSTRAINT fk_ratings_book
        FOREIGN KEY (book_key)
        REFERENCES books(book_key)
);


CREATE TABLE book_popularity (
    book_key TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    year_of_publication INTEGER,
    publisher TEXT,
    image_url_s TEXT,
    image_url_m TEXT,
    image_url_l TEXT,
    ratings_count INTEGER NOT NULL,
    average_rating NUMERIC(4,2) NOT NULL,
    weighted_score NUMERIC(4,2) NOT NULL,

    CONSTRAINT fk_book_popularity_book
        FOREIGN KEY (book_key)
        REFERENCES books(book_key)
);