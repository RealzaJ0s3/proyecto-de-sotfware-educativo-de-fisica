import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import traceback

load_dotenv()

class Database:
    _instance = None
    pg_conn = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        db_url = os.getenv('DATABASE_URL')
        print(f"DEBUG: DATABASE_URL existe = {db_url is not None}")
        
        if db_url:
            try:
                self.pg_conn = psycopg2.connect(db_url)
                print("✅ PostgreSQL conectado exitosamente")
            except Exception as e:
                print(f"❌ ERROR conectando a PostgreSQL: {e}")
                traceback.print_exc()
                raise
        else:
            print("❌ ERROR: DATABASE_URL no encontrada en variables de entorno")
            raise Exception("DATABASE_URL no configurada")
    
    def get_cursor(self):
        if not self.pg_conn:
            raise Exception("No hay conexion PostgreSQL")
        return self.pg_conn.cursor(cursor_factory=RealDictCursor)
    
    def execute_query(self, query, params=None):
        if not self.pg_conn:
            return None
        try:
            cursor = self.pg_conn.cursor(cursor_factory=RealDictCursor)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
            else:
                self.pg_conn.commit()
                result = True
            
            cursor.close()
            return result
        except Exception as e:
            print(f"Error en query: {e}")
            self.pg_conn.rollback()
            return None
    
    def close(self):
        if self.pg_conn:
            self.pg_conn.close()
