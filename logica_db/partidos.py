from logica_db.conexion import obtener_conexion
from mysql.connector import Error
from logica_db.sanciones import _aplicar_sanciones_del_partido



#funciones del administrador
# programar_partido(id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, dia, id_turno, nombre_cancha, id_complejo) -> bool (True si se programo, False si viola restricciones)
def programar_partido(
        id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, dia, id_turno, nombre_cancha, id_complejo
):
    if id_equipo_local == id_equipo_visitante or numero_fecha < 1:
        return False

    if not dia or not id_turno or not nombre_cancha or not id_complejo:
        return False

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    try:
        # Ambos equipos deben pertenecer al torneo y tener al menos 5 jugadores.
        query = """
                SELECT e.id_equipo
                FROM equipo AS e
                         JOIN equipo_jugador_torneo AS ejt
                              ON ejt.id_equipo = e.id_equipo
                                  AND ejt.id_torneo = e.id_torneo
                WHERE e.id_torneo = %s
                  AND e.id_equipo IN (%s, %s)
                GROUP BY e.id_equipo
                HAVING COUNT(*) >= 5 \
                """
        cursor.execute(query, (id_torneo, id_equipo_local, id_equipo_visitante))
        if len(cursor.fetchall()) != 2:
            return False

        # Comprueba el cruce en ambos sentidos y si algún equipo
        # ya tiene partido en la misma jornada.
        query = """
                SELECT id_partido
                FROM partido
                WHERE id_torneo = %s
                  AND estado <> 'cancelado'
                  AND (
                    (id_equipo_local = %s AND id_equipo_visitante = %s)
                        OR (id_equipo_local = %s AND id_equipo_visitante = %s)
                        OR (
                        numero_fecha = %s
                            AND (
                            id_equipo_local IN (%s, %s)
                                OR id_equipo_visitante IN (%s, %s)
                            )
                        )
                    )
                    LIMIT 1 \
                """
        cursor.execute(query, (id_torneo, id_equipo_local, id_equipo_visitante, id_equipo_visitante, id_equipo_local, numero_fecha, id_equipo_local, id_equipo_visitante, id_equipo_local, id_equipo_visitante,
                               ))
        if cursor.fetchone() is not None:
            return False

        # La cancha debe estar libre ese día y turno, incluso en otros torneos.
        query = """
                SELECT id_partido
                FROM partido
                WHERE dia = %s
                  AND id_turno = %s
                  AND nombre_cancha = %s
                  AND id_complejo = %s
                  AND estado IN ('programado', 'jugado')
                    LIMIT 1 \
                """
        cursor.execute(query, (dia, id_turno, nombre_cancha, id_complejo))
        if cursor.fetchone() is not None:
            return False

        query = """
                INSERT INTO partido (
                    id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante,
                    dia, id_turno, nombre_cancha, id_complejo, estado
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'programado') \
                """
        cursor.execute(query, (id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, dia, id_turno, nombre_cancha, id_complejo,))
        conexion.commit()
        return True

    except Error as e:
        conexion.rollback()
        print(f"Error al programar partido: {e}")
        return False

    finally:
        cursor.close()
        conexion.close()

# modificar_partido(id_partido, dia, id_turno, nombre_cancha, id_complejo, estado) -> bool (True si se modifico, False si fallo)
def modificar_partido(id_partido, dia, id_turno, nombre_cancha, id_complejo, estado):
    if estado not in ("programado", "postergado", "cancelado"):
        return False

    if estado == "programado" and (not dia or not id_turno or not nombre_cancha or not id_complejo):
        return False

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                SELECT id_torneo, numero_fecha, id_equipo_local,
                       id_equipo_visitante, estado
                FROM partido
                WHERE id_partido = %s \
                """
        cursor.execute(query, (id_partido,))
        partido = cursor.fetchone()

        if partido is None or partido["estado"] == "jugado":
            return False

        if estado != "cancelado":
            # Al reactivar un partido, el cruce y la fecha deben seguir libres.
            query = """
                    SELECT id_partido
                    FROM partido
                    WHERE id_torneo = %s
                      AND id_partido <> %s
                      AND estado <> 'cancelado'
                      AND (
                        (id_equipo_local = %s AND id_equipo_visitante = %s)
                            OR (id_equipo_local = %s AND id_equipo_visitante = %s)
                            OR (
                            numero_fecha = %s
                                AND (
                                id_equipo_local IN (%s, %s)
                                    OR id_equipo_visitante IN (%s, %s)
                                )
                            )
                        )
                        LIMIT 1 \
                    """
            local = partido["id_equipo_local"]
            visitante = partido["id_equipo_visitante"]
            cursor.execute(query, (
                partido["id_torneo"], id_partido,
                local, visitante, visitante, local,
                partido["numero_fecha"],
                local, visitante, local, visitante,
            ))
            if cursor.fetchone() is not None:
                return False

        if estado == "programado":
            # Se excluye el propio partido al buscar una reserva.
            query = """
                    SELECT id_partido
                    FROM partido
                    WHERE dia = %s
                      AND id_turno = %s
                      AND nombre_cancha = %s
                      AND id_complejo = %s
                      AND id_partido <> %s
                      AND estado IN ('programado', 'jugado')
                        LIMIT 1 \
                    """
            cursor.execute(query, (dia, id_turno, nombre_cancha, id_complejo, id_partido,))
            if cursor.fetchone() is not None:
                return False

        query = """
                UPDATE partido
                SET dia = %s,
                    id_turno = %s,
                    nombre_cancha = %s,
                    id_complejo = %s,
                    estado = %s
                WHERE id_partido = %s
                  AND estado <> 'jugado' \
                """
        cursor.execute(query, (
            dia, id_turno, nombre_cancha, id_complejo, estado, id_partido,))
        conexion.commit()
        return True

    except Error as e:
        conexion.rollback()
        print(f"Error al modificar partido: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()

# eliminar_partido(id_partido) -> bool (True si se elimino, False si no existe o es un partido jugado)
def eliminar_partido(id_partido):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        # Verificar que el partido exista y consultar su estado
        cursor.execute("SELECT estado FROM partido WHERE id_partido = %s", (id_partido,))
        partido = cursor.fetchone()
        if not partido:
            print("Error: El partido no existe.")
            return False

        # Regla reglamentaria oficial: Un partido jugado no puede eliminarse
        if partido["estado"] == "jugado":
            print("Error: Un partido jugado no puede eliminarse por reglamento.")
            return False

        # Limpiar registros asociados si los tuviera (goles, tarjetas, planilla)
        cursor.execute("DELETE FROM gol WHERE id_partido = %s", (id_partido,))
        cursor.execute("DELETE FROM tarjeta WHERE id_partido = %s", (id_partido,))
        cursor.execute("DELETE FROM planilla_partido WHERE id_partido = %s", (id_partido,))

        # Eliminar el partido
        cursor.execute("DELETE FROM partido WHERE id_partido = %s", (id_partido,))
        conexion.commit()
        print("Partido eliminado exitosamente.")
        return True
    except Error as e:
        conexion.rollback()
        print(f"Error al eliminar partido: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()

# listar_partidos_por_fecha(id_torneo, numero_fecha) -> list de dicts con los partidos de la fecha
def listar_partidos_por_fecha(id_torneo, numero_fecha):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                SELECT p.*,
                       el.nombre AS equipo_local,
                       ev.nombre AS equipo_visitante,
                       t.hora_inicio,
                       t.hora_fin
                FROM partido AS p
                         LEFT JOIN equipo AS el ON el.id_equipo = p.id_equipo_local
                         LEFT JOIN equipo AS ev ON ev.id_equipo = p.id_equipo_visitante
                         LEFT JOIN turno AS t ON t.id_turno = p.id_turno
                WHERE p.id_torneo = %s
                  AND p.numero_fecha = %s
                ORDER BY p.dia, t.hora_inicio, p.id_partido \
                """
        cursor.execute(query, (id_torneo, numero_fecha))
        return cursor.fetchall()
    except Error as e:
        print(f"Error al listar partidos por fecha: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()

# obtener_partido(id_partido) -> dict con datos del partido (o None si no existe)
def obtener_partido(id_partido):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                SELECT p.*,
                       CASE
                           WHEN p.estado = 'programado' THEN 1
                           WHEN p.estado = 'jugado'
                                AND TIMESTAMP(p.dia, t.hora_fin) >= NOW() - INTERVAL 48 HOUR THEN 1
                           ELSE 0
                       END AS puede_corregir_resultado
                FROM partido AS p
                         LEFT JOIN turno AS t ON t.id_turno = p.id_turno
                WHERE p.id_partido = %s \
                """
        cursor.execute(query, (id_partido,))
        return cursor.fetchone()
    except Error as e:
        print(f"Error al obtener partido: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()

#funciones del planillero
# registrar_jugador_en_planilla(id_partido, ci_jugador, id_equipo) -> bool (True si se registro, False si esta suspendido o no pertenece al plantel)
def _insertar_en_partido(query, parametros):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(query, parametros)
        registrado = cursor.rowcount == 1
        conexion.commit()
        return registrado
    except Error as e:
        conexion.rollback()
        print(f"Error al registrar datos del partido: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()


def registrar_jugador_en_planilla(id_partido, ci_jugador, id_equipo):
    query = """
            INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo)
            SELECT p.id_partido, ejt.ci_jugador, ejt.id_equipo
            FROM partido AS p
                     JOIN equipo_jugador_torneo AS ejt
                          ON ejt.id_torneo = p.id_torneo
                              AND ejt.id_equipo IN (p.id_equipo_local, p.id_equipo_visitante)
            WHERE p.id_partido = %s
              AND p.estado = 'programado'
              AND ejt.ci_jugador = %s
              AND ejt.id_equipo = %s
              AND NOT EXISTS (
                SELECT 1
                FROM sancion_jugador AS s
                WHERE s.ci_jugador = ejt.ci_jugador
                  AND s.id_torneo = p.id_torneo
                  AND p.numero_fecha BETWEEN s.numero_fecha_inicio
                    AND s.numero_fecha_inicio + s.cantidad_fechas - 1
            ) \
            """
    return _insertar_en_partido(query, (id_partido, ci_jugador, id_equipo))

# registrar_gol(id_partido, ci_jugador, minuto, autogol) -> bool (True si se registro, False si no esta en planilla)
def registrar_gol(id_partido, ci_jugador, minuto, autogol):
    if type(minuto) is not int or minuto < 0 or autogol not in (True, False, 0, 1):
        return False

    query = """
            INSERT INTO gol (id_partido, ci_jugador, minuto, autogol)
            SELECT pp.id_partido, pp.ci_jugador, %s, %s
            FROM planilla_partido AS pp
                     JOIN partido AS p ON p.id_partido = pp.id_partido
                     LEFT JOIN turno AS t ON t.id_turno = p.id_turno
            WHERE pp.id_partido = %s
              AND pp.ci_jugador = %s
              AND (
                  p.estado = 'programado'
                  OR (
                      p.estado = 'jugado'
                      AND TIMESTAMP(p.dia, t.hora_fin) >= NOW() - INTERVAL 48 HOUR
                  )
              ) \
            """
    return _insertar_en_partido(query, (minuto, bool(autogol), id_partido, ci_jugador))

# modificar_gol(id_gol, minuto, autogol) -> bool (True si se modifico, False si no cumple la ventana de 48h o no existe)
def modificar_gol(id_gol, minuto, autogol):
    if type(minuto) is not int or minuto < 0 or autogol not in (True, False, 0, 1):
        return False

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        # Verificar existencia del gol y validar ventana reglamentaria de 48 horas
        query = """
                UPDATE gol g
                JOIN partido p ON p.id_partido = g.id_partido
                LEFT JOIN turno t ON t.id_turno = p.id_turno
                SET g.minuto = %s, g.autogol = %s
                WHERE g.id_gol = %s
                  AND (
                      p.estado = 'programado'
                      OR (
                          p.estado = 'jugado'
                          AND TIMESTAMP(p.dia, t.hora_fin) >= NOW() - INTERVAL 48 HOUR
                      )
                  )
                """
        cursor.execute(query, (minuto, bool(autogol), id_gol))
        conexion.commit()

        if cursor.rowcount > 0:
            print("Gol modificado exitosamente.")
            return True

        # Si rowcount es 0, verificar si el gol existe y si la ventana de 48h sigue abierta (los valores podían ser iguales)
        cursor.execute("""
            SELECT 1
            FROM gol g
            JOIN partido p ON p.id_partido = g.id_partido
            LEFT JOIN turno t ON t.id_turno = p.id_turno
            WHERE g.id_gol = %s
              AND (
                  p.estado = 'programado'
                  OR (
                      p.estado = 'jugado'
                      AND TIMESTAMP(p.dia, t.hora_fin) >= NOW() - INTERVAL 48 HOUR
                  )
              )
        """, (id_gol,))
        if cursor.fetchone():
            return True

        print("Error: El gol no existe o ya expiró la ventana reglamentaria de 48 horas.")
        return False
    except Error as e:
        conexion.rollback()
        print(f"Error al modificar gol: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()


# eliminar_gol(id_gol, id_partido=None) -> bool (True si se elimino, False si no existe o expiro la ventana de 48h)
def eliminar_gol(id_gol, id_partido=None):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                DELETE g
                FROM gol g
                JOIN partido p ON p.id_partido = g.id_partido
                LEFT JOIN turno t ON t.id_turno = p.id_turno
                WHERE g.id_gol = %s
                  AND (%s IS NULL OR g.id_partido = %s)
                  AND (
                      p.estado = 'programado'
                      OR (
                          p.estado = 'jugado'
                          AND TIMESTAMP(p.dia, t.hora_fin) >= NOW() - INTERVAL 48 HOUR
                      )
                  )
                """
        cursor.execute(query, (id_gol, id_partido, id_partido))
        conexion.commit()

        if cursor.rowcount > 0:
            print("Gol eliminado exitosamente.")
            return True
        else:
            print("Error: No se pudo eliminar el gol. Puede no existir o haber expirado la ventana reglamentaria de 48 horas.")
            return False
    except Error as e:
        conexion.rollback()
        print(f"Error al eliminar gol: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()




# registrar_tarjeta(id_partido, ci_jugador, minuto, color) -> bool (True si se registro, False si no esta en planilla)
def registrar_tarjeta(id_partido, ci_jugador, minuto, color):
    if type(minuto) is not int or minuto < 0 or color not in ("amarilla", "roja"):
        return False

    query = """
            INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color)
            SELECT pp.id_partido, pp.ci_jugador, %s, %s
            FROM planilla_partido AS pp
                     JOIN partido AS p ON p.id_partido = pp.id_partido
            WHERE pp.id_partido = %s
              AND pp.ci_jugador = %s
              AND p.estado = 'programado' \
            """
    return _insertar_en_partido(query, (minuto, color, id_partido, ci_jugador))


def eliminar_tarjeta(id_tarjeta):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        query = """
                DELETE t
                FROM tarjeta t
                JOIN partido p ON p.id_partido = t.id_partido
                LEFT JOIN turno tu ON tu.id_turno = p.id_turno
                WHERE t.id_tarjeta = %s
                  AND (
                      p.estado = 'programado'
                      OR (
                          p.estado = 'jugado'
                          AND TIMESTAMP(p.dia, tu.hora_fin) >= NOW() - INTERVAL 48 HOUR
                      )
                  )
                """
        cursor.execute(query, (id_tarjeta,))
        conexion.commit()
        return cursor.rowcount > 0
    except Error as e:
        conexion.rollback()
        print(f"Error al eliminar tarjeta: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()

# cerrar_partido_como_jugado(id_partido) -> bool (True si se marco como jugado, False si todavia no paso la hora)
def cerrar_partido_como_jugado(id_partido):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                UPDATE partido AS p
                    JOIN turno AS t ON t.id_turno = p.id_turno
                    SET p.estado = 'jugado'
                WHERE p.id_partido = %s
                  AND p.estado = 'programado'
                  AND TIMESTAMP(p.dia, t.hora_fin) <= NOW() \
                """
        cursor.execute(query, (id_partido,))

        if cursor.rowcount != 1:
            conexion.rollback()
            return False

        cursor.execute(
            """
            SELECT id_torneo, numero_fecha
            FROM partido
            WHERE id_partido = %s
            """,
            (id_partido,),
        )
        partido = cursor.fetchone()

        _aplicar_sanciones_del_partido(cursor, id_partido, partido["id_torneo"], partido["numero_fecha"] + 1)

        conexion.commit()
        return True
    except Error as e:
        conexion.rollback()
        print(f"Error al cerrar el partido: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()

# obtener_planilla_partido(id_partido) -> list de dicts con jugadores habilitados que jugaron
def obtener_planilla_partido(id_partido):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                SELECT pp.ci_jugador, j.nombre, j.apellido,
                       pp.id_equipo, e.nombre AS equipo
                FROM planilla_partido AS pp
                         JOIN jugador AS j ON j.ci = pp.ci_jugador
                         JOIN equipo AS e ON e.id_equipo = pp.id_equipo
                WHERE pp.id_partido = %s
                ORDER BY e.nombre, j.apellido, j.nombre, pp.ci_jugador \
                """
        cursor.execute(query, (id_partido,))
        return cursor.fetchall()
    except Error as e:
        print(f"Error al obtener planilla del partido: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()

# obtener_resultado_partido(id_partido) -> dict con {'goles_local': int, 'goles_visitante': int}
def obtener_resultado_partido(id_partido):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                SELECT
                    COUNT(CASE WHEN
                                   (pp.id_equipo = p.id_equipo_local AND g.autogol = FALSE)
                                       OR
                                   (pp.id_equipo = p.id_equipo_visitante AND g.autogol = TRUE)
                                   THEN 1
                        END) AS goles_local,
                    COUNT(CASE WHEN
                                   (pp.id_equipo = p.id_equipo_visitante AND g.autogol = FALSE)
                                       OR
                                   (pp.id_equipo = p.id_equipo_local AND g.autogol = TRUE)
                                   THEN 1
                        END) AS goles_visitante
                FROM partido AS p
                         LEFT JOIN gol AS g ON g.id_partido = p.id_partido
                         LEFT JOIN planilla_partido AS pp
                                   ON pp.id_partido = g.id_partido
                                       AND pp.ci_jugador = g.ci_jugador
                WHERE p.id_partido = %s
                GROUP BY p.id_partido \
                """
        cursor.execute(query, (id_partido,))
        return cursor.fetchone()
    except Error as e:
        print(f"Error al obtener resultado del partido: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()

# Funciones auxiliares para la interfaz (frontend)
def obtener_goles_partido(id_partido):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                SELECT g.id_gol, g.ci_jugador, j.nombre, j.apellido, g.minuto, g.autogol,
                       pp.id_equipo, e.nombre AS nombre_equipo
                FROM gol AS g
                         JOIN jugador AS j ON j.ci = g.ci_jugador
                         LEFT JOIN planilla_partido AS pp
                                   ON pp.id_partido = g.id_partido AND pp.ci_jugador = g.ci_jugador
                         LEFT JOIN equipo AS e ON e.id_equipo = pp.id_equipo
                WHERE g.id_partido = %s
                ORDER BY g.minuto ASC \
                """
        cursor.execute(query, (id_partido,))
        return cursor.fetchall()
    except Error as e:
        print(f"Error al obtener goles del partido: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()

def obtener_tarjetas_partido(id_partido):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                SELECT t.id_tarjeta, t.ci_jugador, j.nombre, j.apellido, t.minuto, t.color,
                       pp.id_equipo, e.nombre AS nombre_equipo
                FROM tarjeta AS t
                         JOIN jugador AS j ON j.ci = t.ci_jugador
                         LEFT JOIN planilla_partido AS pp
                                   ON pp.id_partido = t.id_partido AND pp.ci_jugador = t.ci_jugador
                         LEFT JOIN equipo AS e ON e.id_equipo = pp.id_equipo
                WHERE t.id_partido = %s
                ORDER BY t.minuto ASC \
                """
        cursor.execute(query, (id_partido,))
        return cursor.fetchall()
    except Error as e:
        print(f"Error al obtener tarjetas del partido: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()

def listar_canchas():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                SELECT c.nombre_cancha, c.id_complejo, c.superficie, c.techada,
                       co.nombre AS complejo
                FROM cancha AS c
                         JOIN complejo AS co ON co.id_complejo = c.id_complejo
                ORDER BY co.nombre, c.nombre_cancha \
                """
        cursor.execute(query)
        return cursor.fetchall()
    except Error as e:
        print(f"Error al listar canchas: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()

def listar_turnos():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                SELECT id_turno, hora_inicio, hora_fin
                FROM turno
                ORDER BY hora_inicio \
                """
        cursor.execute(query)
        return cursor.fetchall()
    except Error as e:
        print(f"Error al listar turnos: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()
