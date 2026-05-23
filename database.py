import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

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
        """Conecta a PostgreSQL en Supabase"""
        db_url = os.getenv('DATABASE_URL')
        
        if db_url:
            self.pg_conn = psycopg2.connect(db_url)
            print("✅ PostgreSQL conectado")
        else:
            print("❌ ERROR: DATABASE_URL no encontrada")
            raise Exception("DATABASE_URL no configurada")
    
    def get_cursor(self):
        """Para queries SQL directas"""
        if not self.pg_conn:
            raise Exception("No hay conexion PostgreSQL")
        return self.pg_conn.cursor(cursor_factory=RealDictCursor)
    
    def execute_query(self, query, params=None):
        """Ejecuta SQL directo"""
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
