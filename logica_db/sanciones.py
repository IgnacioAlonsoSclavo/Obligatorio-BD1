from mysql.connector import Error

from logica_db.conexion import obtener_conexion

# jugador_esta_suspendido(ci_jugador, id_torneo, numero_fecha) -> bool (True si esta sancionado para esa fecha, False si puede jugar)
def jugador_esta_suspendido(ci_jugador,id_torneo,numero_fecha):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                SELECT id_sancion
                FROM sancion_jugador
                WHERE ci_jugador = %s AND id_torneo = %s
                AND %s BETWEEN numero_fecha_inicio AND (numero_fecha_inicio + cantidad_fechas - 1)
                LIMIT 1 
                """
        cursor.execute(query,(ci_jugador ,id_torneo ,numero_fecha))
        resultado = cursor.fetchone()
        return resultado is not None
    except Error as e:
        print(f"Error al verificar suspension: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()
# crear_sancion(ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas) -> bool (True si se aplico la sancion, False si fallo)
def crear_sancion(ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas)
                VALUES (%s, %s, %s, %s, %s)
                """
        cursor.execute(query,(ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas))
        conexion.commit()
        return True
    except Error as e:
        conexion.rollback()
        print(f"Error al crear sancion: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()


def _registrar_sancion_si_no_existe(cursor, ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas=1):
    query_existe = """
        SELECT id_sancion
        FROM sancion_jugador
        WHERE ci_jugador = %s AND id_torneo = %s AND motivo = %s AND numero_fecha_inicio = %s
        LIMIT 1
    """
    cursor.execute(query_existe, (ci_jugador, id_torneo, motivo, numero_fecha_inicio))
    if not cursor.fetchone():
        query_insert = """
            INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query_insert, (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas))


def _aplicar_sanciones_del_partido(cursor, id_partido, id_torneo, fecha_sancion):
    #Rojas directas
    query_rojas = """
        SELECT DISTINCT ci_jugador
        FROM tarjeta
        WHERE id_partido = %s AND color = 'roja'
    """
    cursor.execute(query_rojas, (id_partido,))
    for j in cursor.fetchall():
        _registrar_sancion_si_no_existe(cursor, j["ci_jugador"], id_torneo, "roja", fecha_sancion)

    #Acumulación de amarillas (cada 3 amarillas en el torneo)
    query_amarillas = """
        SELECT DISTINCT ci_jugador
        FROM tarjeta
        WHERE id_partido = %s AND color = 'amarilla'
    """
    cursor.execute(query_amarillas, (id_partido,))
    jugadores_amarillas = cursor.fetchall()

    query_contar_amarillas = """
        SELECT COUNT(*) AS total
        FROM tarjeta t
        JOIN partido p ON t.id_partido = p.id_partido
        WHERE t.ci_jugador = %s AND p.id_torneo = %s AND t.color = 'amarilla'
    """

    query_sanciones_previas = """
        SELECT COUNT(*) AS total
        FROM sancion_jugador sj
        WHERE ci_jugador = %s AND id_torneo = %s AND motivo = 'acumulación de amarillas'
    """

    for j in jugadores_amarillas:
        cursor.execute(query_contar_amarillas, (j["ci_jugador"], id_torneo))
        conteo = cursor.fetchone()
        total_amarillas = conteo["total"] if conteo else 0

        cursor.execute(query_sanciones_previas, (j["ci_jugador"], id_torneo))
        previas = cursor.fetchone()
        sanciones_previas = previas["total"] if previas else 0

        if total_amarillas // 3 > sanciones_previas:
            _registrar_sancion_si_no_existe(
                cursor,j["ci_jugador"] , id_torneo, "acumulación de amarillas", fecha_sancion
            )

# generar_sanciones_automaticas(id_partido) -> bool (True si proceso rojas y amarillas acumuladas, False si hubo error)
def generar_sanciones_automaticas(id_partido):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query_partido = "SELECT id_torneo, numero_fecha FROM partido WHERE id_partido = %s"
        cursor.execute(query_partido, (id_partido,))
        partido = cursor.fetchone()
        if not partido:
            print("Error: No se encontró el partido.")
            return False

        id_torneo = partido["id_torneo"]
        fecha_sancion = partido["numero_fecha"] + 1

        _aplicar_sanciones_del_partido(cursor, id_partido, id_torneo, fecha_sancion)

        conexion.commit()
        return True
    except Error as e:
        conexion.rollback()
        print(f"Error al generar sanciones automáticas: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()

# listar_sanciones_por_torneo(id_torneo) -> list de dicts con todas las sanciones de la edicion
def listar_sanciones_por_torneo(id_torneo):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                SELECT
                    s.id_sancion,
                    s.ci_jugador,
                    j.nombre,
                    j.apellido,
                    s.motivo,
                    s.numero_fecha_inicio,
                    s.cantidad_fechas,
                    (s.numero_fecha_inicio + s.cantidad_fechas - 1) AS fecha_fin
                FROM sancion_jugador s
                JOIN jugador j ON s.ci_jugador = j.ci
                WHERE s.id_torneo = %s
                ORDER BY s.numero_fecha_inicio ASC, j.apellido ASC
        """
        cursor.execute(query, (id_torneo,))
        return cursor.fetchall()
    except Error as e:
        print(f"Error al listar sanciones: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()

# eliminar_sancion(id_sancion) -> bool (True si se elimino, False si fallo)
def eliminar_sancion(id_sancion):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                DELETE FROM sancion_jugador
                WHERE id_sancion = %s
                """
        cursor.execute(query,(id_sancion,))
        conexion.commit()
        if cursor.rowcount > 0:
            print("Se elimino la sancion correctamente.")
            return True
        print("Error, la sancion no se encontro")
        return False
    except Error as e:
        conexion.rollback()
        print(f"Error al eliminar sancion: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()


def modificar_sancion(id_sancion, motivo, numero_fecha_inicio, cantidad_fechas):
    if not id_sancion or not motivo or numero_fecha_inicio is None or cantidad_fechas is None:
        return False

    motivo = motivo.strip()
    if motivo not in ("roja", "acumulación de amarillas", "disciplinaria"):
        return False

    try:
        numero_fecha_inicio = int(numero_fecha_inicio)
        cantidad_fechas = int(cantidad_fechas)
    except (ValueError, TypeError):
        return False

    if numero_fecha_inicio < 1 or cantidad_fechas < 1:
        return False

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT 1 FROM sancion_jugador WHERE id_sancion = %s", (id_sancion,))
        if not cursor.fetchone():
            return False

        query = """
            UPDATE sancion_jugador
            SET motivo = %s,
                numero_fecha_inicio = %s,
                cantidad_fechas = %s
            WHERE id_sancion = %s
        """
        cursor.execute(query, (motivo, numero_fecha_inicio, cantidad_fechas, id_sancion))
        conexion.commit()
        return True
    except Error as e:
        conexion.rollback()
        print(f"Error al modificar sancion: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()

