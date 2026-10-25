import mysql.connector
from mysql.connector import Error

def obtener_conexion():

    try:
        conexion = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="rootpassword",
            database="TorneoInterfacultades"
        )
        if conexion.is_connected():
            return conexion
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None

def probar_conexion():
    conexion = obtener_conexion()
    if conexion:
        try:
            cursor = conexion.cursor()
            cursor.execute("SELECT VERSION();")
            version = cursor.fetchone()
            print(f"¡Conexión exitosa a MySQL Community Server versión: {version[0]}!")
            

            cursor.execute("SHOW TABLES;")
            tablas = cursor.fetchall()
            print("Tablas encontradas:")
            for tabla in tablas:
                print(f" - {tabla[0]}")
                
            cursor.close()
        finally:
            conexion.close()
            print("Conexión cerrada.")

if __name__ == "__main__":
    probar_conexion()
