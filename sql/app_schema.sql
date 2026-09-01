CREATE TABLE IF NOT EXISTS app_users (
    app_user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    age INTEGER CHECK (age BETWEEN 10 AND 100),
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_book_ratings (
    rating_id SERIAL PRIMARY KEY,
    app_user_id INTEGER NOT NULL
        REFERENCES app_users(app_user_id)
        ON DELETE CASCADE,
    book_key TEXT NOT NULL
        REFERENCES books(book_key),
    rating INTEGER NOT NULL
        CHECK (rating BETWEEN 1 AND 10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (app_user_id, book_key)
);