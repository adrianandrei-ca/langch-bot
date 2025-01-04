import sqlite3
import os
import csv

DB_PATH = os.getenv("DB_PATH", "static/database")
DB_SQLITE_FILE = os.getenv("DB_SQLITE_FILE", "database.db")

CSV_ORDERS_FILE = os.getenv("ORDERS_FILE", "data/Order_Data_Dataset.csv")
CSV_PRODUCTS_FILE = os.getenv("PRODUCTS_FILE", "data/Product_Information_Dataset.csv")

def load_orders(connection, logger):
    cur = connection.cursor()

    with open(CSV_ORDERS_FILE,'r') as fin: 
        # csv.DictReader uses first line in file for column headings by default
        dr = csv.DictReader(fin) # comma is default delimiter
        to_db = [(i['Order_Date'], i['Time'], i['Aging'], i['Customer_Id'], i['Gender'], i['Device_Type'], \
                  i['Customer_Login_type'], i['Product_Category'], i['Product'], i['Sales'], i['Quantity'], \
                  i['Discount'], i['Profit'], i['Shipping_Cost'], i['Order_Priority'], i['Payment_method']) for i in dr]
        logger.info("Inserting {} order records".format(len(to_db)))

    cur.executemany("INSERT INTO orders (order_date, order_time, aging, customer_id, gender, device_type, \
                    customer_login_type, product_category, product, sales, quantity, discount, profit, \
                    shipping_cost, order_priority, payment_method) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", to_db)
    connection.commit()

def load_products(connection, logger):
    cur = connection.cursor()

    with open(CSV_PRODUCTS_FILE,'r') as fin: 
        # csv.DictReader uses first line in file for column headings by default
        dr = csv.DictReader(fin) # comma is default delimiter
        to_db = [(i['main_category'], i['title'], i['average_rating'], i['rating_number'], i['features'], i['description'], \
                  i['price'], i['store'], i['categories'], i['details'], i['parent_asin']) for i in dr]
        logger.info("Inserting {} product records".format(len(to_db)))

    cur.executemany("INSERT INTO products (main_category, title, average_rating, rating_number, features, product_description, price, \
                    store, categories, details, parent_asin) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", to_db)
    connection.commit()

def _init_db(db_file, logger):
    isExist = os.path.exists(db_file)
    if not isExist:
        sql_script = None
        with open('database/schema.sql', 'r') as sql_file:
            sql_script = sql_file.read()
        logger.info("opening database {}".format(db_file))
        connection = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        connection.executescript(sql_script)
        connection.commit()

        load_orders(connection, logger)
        load_products(connection, logger)

        connection.close()
        logger.info("New database created")

def get_sql_db_connection(logger):
    db_file = os.path.join(DB_PATH, DB_SQLITE_FILE)
    _init_db(db_file, logger)

    connection = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    connection.row_factory = sqlite3.Row
    return connection

def init_db(logger):
    os.makedirs(DB_PATH, exist_ok = True)
    db_file = os.path.join(DB_PATH, DB_SQLITE_FILE)
    _init_db(db_file, logger)