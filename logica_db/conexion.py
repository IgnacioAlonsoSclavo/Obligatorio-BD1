import os
import mysql.connector
from mysql.connector import Error

def obtener_conexion():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "rootpassword"),
            database=os.getenv("DB_NAME", "TorneoInterfacultades")
        )
    except Error as e:
        raise ConnectionError(f"No se pudo conectar a MySQL: {e}") from e
def probar_conexion():
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT VERSION();")
        version = cursor.fetchone()
        print("Conexión exitosa a MySQL Server")

        cursor.execute("SHOW TABLES;")
        for tabla in cursor.fetchall():
            print(f" - {tabla[0]}")

        cursor.close()
    finally:
        conexion.close()
        print("Conexión cerrada.")
if __name__ == "__main__":
    probar_conexion()
