from mysql.connector import Error

from logica_db.conexion import obtener_conexion

# crear_jugador(ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo) -> bool (True si se creo, False si fallo)
def crear_jugador(ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                INSERT INTO jugador (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo)
                VALUES (%s, %s, %s, %s, %s, %s, %s) 
                """
        cursor.execute(query,(ci, nombre ,apellido ,email ,fecha_nacimiento ,id_facultad ,tipo))
        conexion.commit()
        return True
    except Error as e:
        conexion.rollback()
        print(f"Error al crear jugador: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()
# modificar_jugador(ci, nombre=None, apellido=None, email=None, fecha_nacimiento=None, id_facultad=None, tipo=None) -> bool (True si se modifico, False si fallo)
def modificar_jugador(ci, nombre=None, apellido=None, email=None, fecha_nacimiento=None, id_facultad=None, tipo=None):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                UPDATE jugador
                SET nombre = COALESCE(%s, nombre),
                    apellido = COALESCE(%s, apellido),
                    email = COALESCE(%s, email),
                    fecha_nacimiento = COALESCE(%s, fecha_nacimiento),
                    id_facultad = COALESCE(%s, id_facultad),
                    tipo = COALESCE(%s, tipo)
                WHERE ci = %s 
        """
        cursor.execute(query, (nombre, apellido, email, fecha_nacimiento, id_facultad, tipo, ci))
        conexion.commit()
        if cursor.rowcount > 0:
            print("Se actualizo el jugador correctamente.")
            return True
        print("Error, el jugador no se encontro")
        return False
    except Error as e:
        conexion.rollback()
        print(f"Error al modificar jugador: {e}")
        return False

    finally:

        cursor.close()
        conexion.close()
# eliminar_jugador(ci) -> bool (True si se elimino, False si no existia)
def eliminar_jugador(ci):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                DELETE FROM jugador
                WHERE ci = %s
                """
        cursor.execute(query,(ci,))
        conexion.commit()
        if cursor.rowcount > 0:
            print("Se elimino el jugador correctamente.")
            return True
        print("Error, el jugador no se encontro")
        return False
    except Error as e:
        conexion.rollback()
        print(f"Error al eliminar jugador: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()

# obtener_jugador(ci) -> dict con datos del jugador (o None si no existe)
def obtener_jugador(ci):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                SELECT * FROM jugador
                WHERE ci = %s
                """
        cursor.execute(query,(ci,))
        return cursor.fetchone()
    except Error as e:
        print(f"Error al obtener el jugador: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()

# listar_jugadores() -> list de dicts con todos los jugadores
def listar_jugadores():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                SELECT * FROM jugador
                ORDER BY apellido, nombre
                """
        cursor.execute(query,)
        return cursor.fetchall()
    except Error as e:
        print(f"Error al listar jugadores: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()

# listar_jugadores_por_facultad(id_facultad) -> list de dicts de jugadores de esa facultad
def listar_jugadores_por_facultad(id_facultad):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                SELECT * FROM jugador
                WHERE id_facultad = %s
                ORDER BY apellido, nombre
                """
        cursor.execute(query,(id_facultad,))
        return cursor.fetchall()
    except Error as e:
        print(f"Error al listar jugadores: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()
