from mysql.connector import Error
from logica_db.conexion import obtener_conexion

# -------------------------------------------------------------
# Gestión de Complejos Deportivos
# -------------------------------------------------------------

def listar_complejos():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
            SELECT id_complejo, nombre, dirección, departamento
            FROM complejo
            ORDER BY id_complejo ASC
        """
        cursor.execute(query)
        return cursor.fetchall()
    except Error as e:
        print(f"Error al listar complejos: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()


def crear_complejo(nombre, direccion, departamento):
    nombre = nombre.strip() if nombre else ""
    direccion = direccion.strip() if direccion else ""
    departamento = departamento.strip() if departamento else ""

    if not nombre or not direccion or not departamento:
        return False

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        query = """
            INSERT INTO complejo (nombre, dirección, departamento)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (nombre, direccion, departamento))
        conexion.commit()
        return True
    except Error as e:
        conexion.rollback()
        print(f"Error al crear complejo: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()


def eliminar_complejo(id_complejo):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        query = "DELETE FROM complejo WHERE id_complejo = %s"
        cursor.execute(query, (id_complejo,))
        conexion.commit()
        return cursor.rowcount > 0
    except Error as e:
        conexion.rollback()
        print(f"Error al eliminar complejo: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()


# -------------------------------------------------------------
# Gestión de Canchas
# -------------------------------------------------------------

def listar_canchas_completo():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
            SELECT c.nombre_cancha, c.id_complejo, c.superficie, c.techada,
                   co.nombre AS nombre_complejo
            FROM cancha c
            JOIN complejo co ON co.id_complejo = c.id_complejo
            ORDER BY co.nombre ASC, c.nombre_cancha ASC
        """
        cursor.execute(query)
        return cursor.fetchall()
    except Error as e:
        print(f"Error al listar canchas: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()


def crear_cancha(nombre_cancha, id_complejo, superficie, techada):
    nombre_cancha = nombre_cancha.strip() if nombre_cancha else ""
    if not nombre_cancha or not id_complejo:
        return False

    if superficie not in ("sintético", "parquet"):
        superficie = "sintético"

    techada_val = bool(techada)

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        query = """
            INSERT INTO cancha (nombre_cancha, id_complejo, superficie, techada)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (nombre_cancha, id_complejo, superficie, techada_val))
        conexion.commit()
        return True
    except Error as e:
        conexion.rollback()
        print(f"Error al crear cancha: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()


def eliminar_cancha(nombre_cancha, id_complejo):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        query = "DELETE FROM cancha WHERE nombre_cancha = %s AND id_complejo = %s"
        cursor.execute(query, (nombre_cancha, id_complejo))
        conexion.commit()
        return cursor.rowcount > 0
    except Error as e:
        conexion.rollback()
        print(f"Error al eliminar cancha: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()
