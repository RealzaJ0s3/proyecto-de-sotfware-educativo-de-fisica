import mysql.connector
from mysql.connector import Error

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialize_connection()
        return cls._instance
    
    def _initialize_connection(self):
        """Conecta a MariaDB (XAMPP)"""
        try:
            self.connection = mysql.connector.connect(
                host='localhost',
                port=3306,
                database='fisica_cbit',
                user='root',
                password='',
                autocommit=True
            )
            self.cursor = self.connection.cursor(dictionary=True)
            print("✅ Conectado a MariaDB")
        except Error as e:
            print(f"❌ Error: {e}")
            raise
    
    def get_cursor(self):
        return self.cursor
    
    def execute_query(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                return self.cursor.fetchall()
            else:
                self.connection.commit()
                return self.cursor.lastrowid
        except Error as e:
            print(f"Error en query: {e}")
            return None
    
    def close(self):
        if self.connection.is_connected():
            self.cursor.close()
            self.connection.close()