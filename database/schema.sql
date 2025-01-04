DROP TABLE IF EXISTS products;

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    main_category TEXT,
    title TEXT NOT NULL,
    average_rating REAL,
    rating_number INTEGER,
    features TEXT NOT NULL,
    product_description TEXT,
    price REAL,
    store TEXT,
    categories TEXT,
    details TEXT,
    parent_asin TEXT
);

DROP TABLE IF EXISTS orders;

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_date TEXT,
    order_time TEXT,
    aging INTEGER,
    customer_id TEXT NOT NULL,
    gender TEXT,
    device_type TEXT,
    customer_login_type TEXT,
    product_category TEXT,
    product TEXT,
    sales INTEGER,
    quantity INTEGER,
    discount REAL,
    profit REAL,
    shipping_cost REAL,
    order_priority TEXT,
    payment_method TEXT
);
