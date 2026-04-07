DROP TABLE IF EXISTS book_popularity;
DROP TABLE IF EXISTS ratings;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS books;

CREATE TABLE books (
    isbn VARCHAR(20) PRIMARY KEY,
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
    isbn VARCHAR(20) NOT NULL,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 10),
    PRIMARY KEY (user_id, isbn),
    CONSTRAINT fk_ratings_user
        FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT fk_ratings_book
        FOREIGN KEY (isbn) REFERENCES books(isbn)
);

CREATE TABLE book_popularity (
    isbn VARCHAR(20) PRIMARY KEY,
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
        FOREIGN KEY (isbn) REFERENCES books(isbn)
);