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


def modificar_complejo(id_complejo, nombre, direccion, departamento):
    nombre = nombre.strip() if nombre else ""
    direccion = direccion.strip() if direccion else ""
    departamento = departamento.strip() if departamento else ""

    if not id_complejo or not nombre or not direccion or not departamento:
        return False

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_complejo FROM complejo WHERE id_complejo = %s", (id_complejo,))
        if not cursor.fetchone():
            return False

        query = """
            UPDATE complejo
            SET nombre = %s,
                dirección = %s,
                departamento = %s
            WHERE id_complejo = %s
        """
        cursor.execute(query, (nombre, direccion, departamento, id_complejo))
        conexion.commit()
        return True
    except Error as e:
        conexion.rollback()
        print(f"Error al modificar complejo: {e}")
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


def modificar_cancha(nombre_cancha, id_complejo, nuevo_nombre, superficie, techada):
    nombre_cancha = nombre_cancha.strip() if nombre_cancha else ""
    nuevo_nombre = nuevo_nombre.strip() if nuevo_nombre else ""
    if not nombre_cancha or not nuevo_nombre or not id_complejo:
        return False

    if superficie not in ("sintético", "parquet"):
        superficie = "sintético"

    techada_val = bool(techada)

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT 1 FROM cancha WHERE nombre_cancha = %s AND id_complejo = %s", (nombre_cancha, id_complejo))
        if not cursor.fetchone():
            return False

        if nuevo_nombre != nombre_cancha:
            cursor.execute("SELECT 1 FROM cancha WHERE nombre_cancha = %s AND id_complejo = %s", (nuevo_nombre, id_complejo))
            if cursor.fetchone():
                return False

            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            cursor.execute("""
                UPDATE cancha
                SET nombre_cancha = %s, superficie = %s, techada = %s
                WHERE nombre_cancha = %s AND id_complejo = %s
            """, (nuevo_nombre, superficie, techada_val, nombre_cancha, id_complejo))
            cursor.execute("""
                UPDATE partido
                SET nombre_cancha = %s
                WHERE nombre_cancha = %s AND id_complejo = %s
            """, (nuevo_nombre, nombre_cancha, id_complejo))
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        else:
            cursor.execute("""
                UPDATE cancha
                SET superficie = %s, techada = %s
                WHERE nombre_cancha = %s AND id_complejo = %s
            """, (superficie, techada_val, nombre_cancha, id_complejo))

        conexion.commit()
        return True
    except Error as e:
        conexion.rollback()
        print(f"Error al modificar cancha: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()
