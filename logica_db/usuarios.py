from operator import truediv

from logica_db.conexion import obtener_conexion
from mysql.connector import Error

# 1. Recibir un correo y una contraseña.
# 2. Preguntarle a MySQL si existe esa combinación.
# 3. Si existe, devolver los datos del usuario (principalmente su rol).
# 4. Si no existe o la contraseña está mal, devolver None.

# Voy a usar fetchone(), dictoinary=True y parametros seguros %s en tupla

def validar_login(correo, contrasenia):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
            SELECT correo, rol
            FROM login
            WHERE correo = %s AND contraseña = %s
        """
        cursor.execute(query, (correo,contrasenia))
        usuario = cursor.fetchone()
        return usuario
    finally:
        cursor.close()
        conexion.close()

def crear_usuario(correo, contrasenia, rol):
    if not validar_entrada(correo,contrasenia,rol):
        return False
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        query = """
            INSERT INTO login (correo, contraseña, rol)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query,(correo,contrasenia,rol))
        conexion.commit()
        return True
    except Error as e:
        conexion.rollback()
        print(f"Error al crear usuario en la base de datos: {e}")
        return False

    finally:
        cursor.close()
        conexion.close()

def validar_entrada(correo, contrasenia, rol):
    correo = correo.strip() if correo else ""
    contrasenia = contrasenia.strip() if contrasenia else ""
    rol = rol.strip().lower() if rol else ""

    if not correo or not contrasenia:
        print("Error, el correo y la contraseña no pueden estar vacios.")
        return False
    if "@" not in correo or "ucu.edu.uy" not in correo:
        print("Error, el formato del correo no es valido")
        return False

    if len(contrasenia) < 4:
        print("Error, la contraseña debe tener al menos 4 caracteres.")
        return False
    if rol not in ("admin","planillero"):
        print("Error, el rol debe ser 'admin' o 'planillero'.")
        return False
    return True
def existe_administrador():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    try:
        query = " SELECT COUNT(*) AS total FROM login WHERE rol = 'admin'"
        cursor.execute(query)
        resultado = cursor.fetchone()

        return resultado['total'] > 0
    finally:
        cursor.close()
        conexion.close()




#Para probar, el if __name__ hace que al ejecutar solo se ejecute lo de abajo y no el codigo de la clase entero
if __name__ == "__main__":
    resultado = validar_login("admin@ucu.edu.uy", "1234")

    if resultado:
        print(f"Login exitoso. Rol: {resultado['rol']}")
    else:
        print("Credenciales incorrectas.")