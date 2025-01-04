
class DB():
    def __init__(self, sql_connection_getter, logger):
        self.connection_getter = sql_connection_getter
        self.logger = logger
    
    def orders_by_customer(self, customer_id: str):
        _list = []
        connection = self.connection_getter(self.logger)
        cursor = connection.cursor()
        cnvs = cursor.execute('SELECT * FROM orders WHERE customer_id=?', (customer_id,)).fetchall()
        if len(cnvs) == 0:
            connection.close()
            return _list
        connection.close()
        _list = [{'id': prompt['id'], 'order_date': prompt['order_date'], 'product': prompt['product'], \
                  'quantity': prompt['quantity'], 'order_time': prompt['order_time']} for prompt in cnvs]

        return _list

    def _data_as_text(self, data):
        return data.replace('[', '').replace(']', '').replace("'", "").replace('{', '').replace('}', '') \
            .replace('"', '').replace('Product Description', '')
    
    def products_as_documents(self):
        _documents = []
        _metas = []

        connection = self.connection_getter(self.logger)
        cursor = connection.cursor()
        prods = cursor.execute('SELECT * FROM products').fetchall()
        for prod in prods:
            _documents.append(f"{prod['title']}. {self._data_as_text(prod['features'])}. {self._data_as_text(prod['product_description'])}. {self._data_as_text(prod['details'])}.")
            _metas.append({"id": prod["id"], "rating": prod["average_rating"]})
        connection.close()

        return _documents, _metas