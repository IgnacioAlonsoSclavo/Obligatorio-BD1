from logica_db.conexion import obtener_conexion

def obtener_jugadores_sin_minutos(id_torneo):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
        SELECT j.ci, j.nombre, j.apellido, e.nombre AS nombre_equipo, ejt.numero_camiseta
        FROM equipo_jugador_torneo ejt
        JOIN jugador j ON ejt.ci_jugador = j.ci
        JOIN equipo e ON ejt.id_equipo = e.id_equipo
        WHERE ejt.id_torneo = %s
            AND ejt.ci_jugador NOT IN(
            SELECT pp.ci_jugador
            FROM planilla_partido pp
            JOIN partido p ON pp.id_partido = p.id_partido
            WHERE p.id_torneo = %s
        )
        ORDER BY e.nombre, j.apellido;
        """
        cursor.execute(query,(id_torneo, id_torneo))
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()

def obtener_porcentaje_estados_partidos(id_torneo):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
        SELECT estado, COUNT(*) AS cantidad
        FROM partido
        WHERE id_torneo = %s AND estado IN ('jugado', 'cancelado', 'postergado')
        GROUP BY estado;
        """
        cursor.execute(query, (id_torneo,))
        filas = cursor.fetchall()

        if not filas:
            return {"jugados": 0.0, "postergados_cancelados": 0.0}
        #como me traje solo los 'jugados', 'cancelados' y 'postergados' el total son ellos
        total = sum(f["cantidad"] for f in filas)
        #solo los que tienen estado 'jugado'
        jugados = sum(f["cantidad"] for f in filas if f["estado"] == "jugado")
        #los que tienen estado 'postergado' o 'cancelado'
        postergados_cancelados = total - jugados

        return{
            "total_partidos": total,
            "porcentaje_jugados": round((jugados/total) * 100, 2),
            "porcentaje_postergados_cancelados": round((postergados_cancelados/total) * 100,2)
        }
    finally:
        cursor.close()
        conexion.close()


if __name__ == "__main__":
    resultado = obtener_porcentaje_estados_partidos(1)
    print("Resultado:", resultado)


def crear_vistas():
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()

        cursor.execute("""
                       CREATE
                       OR REPLACE VIEW goles_por_partido AS
                       SELECT p.id_partido,
                              p.id_equipo_local,
                              p.id_equipo_visitante,
                              SUM(IF((ejt.id_equipo = p.id_equipo_local AND NOT g.autogol) OR (ejt.id_equipo = p.id_equipo_visitante AND g.autogol), 1,0)) AS goles_local,
                              SUM(IF((ejt.id_equipo = p.id_equipo_visitante AND NOT g.autogol) OR (ejt.id_equipo = p.id_equipo_local AND g.autogol), 1, 0)) AS goles_visitante
                       FROM partido p LEFT JOIN gol g ON g.id_partido = p.id_partido LEFT JOIN equipo_jugador_torneo ejt ON ejt.ci_jugador = g.ci_jugador AND ejt.id_equipo IN (p.id_equipo_local, p.id_equipo_visitante)
                       WHERE p.estado = 'jugado'
                       GROUP BY p.id_partido, p.id_equipo_local, p.id_equipo_visitante
                       """)

        cursor.execute("""
                       CREATE
                       OR REPLACE VIEW resultados_equipo AS
                       SELECT id_equipo,
                              SUM(ganado) AS ganados,
                              SUM(empatado) AS empatados,
                              SUM(perdido) AS perdidos,
                              SUM(IF(ganado, 3, IF(empatado, 1, 0))) AS puntos,
                              SUM(ganado + empatado + perdido) AS partidos_jugados
                       FROM (SELECT id_equipo_local AS id_equipo,
                                    IF(goles_local > goles_visitante, 1, 0) AS ganado,
                                    IF(goles_local = goles_visitante, 1, 0) AS empatado,
                                    IF(goles_local < goles_visitante, 1, 0) AS perdido
                             FROM goles_por_partido

                             UNION ALL

                             SELECT id_equipo_visitante AS id_equipo,
                                    IF(goles_visitante > goles_local, 1, 0) AS ganado,
                                    IF(goles_visitante = goles_local, 1, 0) AS empatado,
                                    IF(goles_visitante < goles_local, 1, 0) AS perdido
                             FROM goles_por_partido) x
                       GROUP BY id_equipo
                       """)

        cursor.execute("""
                       CREATE
                       OR REPLACE VIEW goles_equipo AS
                       SELECT id_equipo,
                              SUM(goles_a_favor) AS goles_a_favor,
                              SUM(goles_en_contra) AS goles_en_contra,
                              SUM(goles_a_favor - goles_en_contra) AS diferencia_de_goles
                       FROM (SELECT id_equipo_local AS id_equipo,
                                    SUM(goles_local) AS goles_a_favor,
                                    SUM(goles_visitante) AS goles_en_contra
                             FROM goles_por_partido
                             GROUP BY id_equipo

                             UNION ALL

                             SELECT id_equipo_visitante AS id_equipo,
                                    SUM(goles_visitante) AS goles_a_favor,
                                    SUM(goles_local) AS goles_en_contra
                             FROM goles_por_partido
                             GROUP BY id_equipo) x
                       GROUP BY id_equipo
                       """)

        cursor.close()
    finally:
        conexion.close()

# Consultas

def tabla_posiciones(id_torneo):
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
                       SELECT r.id_equipo,
                              r.partidos_jugados,
                              g.goles_a_favor,
                              g.goles_en_contra,
                              g.diferencia_de_goles,
                              r.ganados,
                              r.empatados,
                              r.perdidos,
                              r.puntos
                       FROM resultados_equipo r JOIN goles_equipo g ON g.id_equipo = r.id_equipo JOIN equipo e ON e.id_equipo = r.id_equipo
                       WHERE e.id_torneo = %s
                       """, (id_torneo,))
        resultado = cursor.fetchall()
        cursor.close()
        return resultado
    finally:
        conexion.close()


def goleadores():
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
                       SELECT j.ci, j.nombre, COUNT(ci_jugador) AS cantidad_goles
                       FROM gol g JOIN jugador j ON g.ci_jugador = j.ci
                       WHERE !autogol
                       GROUP BY j.ci, j.nombre
                       ORDER BY cantidad_goles DESC
                            LIMIT 10
                       """)
        resultado = cursor.fetchall()
        cursor.close()
        return resultado
    finally:
        conexion.close()


def promedios_goles(id_torneo):
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)

        # Promedio por fecha
        cursor.execute("""
                       SELECT p.numero_fecha,
                              COUNT(g.id_gol) AS cantidad_goles,
                              COUNT(g.id_gol) / COUNT(DISTINCT p.id_partido) AS promedio_por_fecha
                       FROM gol g RIGHT JOIN partido p ON g.id_partido = p.id_partido
                       WHERE p.estado = 'jugado' AND p.id_torneo = %s
                       GROUP BY p.numero_fecha
                       ORDER BY p.numero_fecha ASC
                       """, (id_torneo,))
        por_fecha = cursor.fetchall()

        # Promedio de toda la edición
        cursor.execute("""
                       SELECT (SELECT COUNT(*)
                               FROM gol g JOIN partido p ON g.id_partido = p.id_partido
                               WHERE p.estado = 'jugado' AND p.id_torneo = %s)
                                  /
                              (SELECT COUNT(*)
                               FROM partido
                               WHERE estado = 'jugado' AND id_torneo = %s) AS promedio_en_la_edicion
                       """, (id_torneo, id_torneo))
        cursor.fetchone()["promedio_en_la_edicion"]

        cursor.close()
        return por_fecha, promedio_edicion
    finally:
        conexion.close()

def canchas_mas_usadas():
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.nombre_cancha, COUNT(*) AS cantidad_de_usos_cancha
            FROM cancha c JOIN partido p ON c.nombre_cancha = p.nombre_cancha
            WHERE p.estado = 'jugado'
            GROUP BY c.nombre_cancha
            ORDER BY cantidad_de_usos_cancha DESC
        """)
        resultado = cursor.fetchall()
        cursor.close()
        return resultado
    finally:
        conexion.close()


def turnos_mas_usados():
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT t.hora_inicio, t.hora_fin, COUNT(*) AS cantidad_de_usos_hora
            FROM turno t JOIN partido p ON t.id_turno = p.id_turno
            WHERE p.estado = 'jugado'
            GROUP BY t.hora_inicio, t.hora_fin
            ORDER BY cantidad_de_usos_hora DESC
        """)
        resultado = cursor.fetchall()
        cursor.close()
        return resultado
    finally:
        conexion.close()

# 8. Cantidad de sanciones por equipo y por motivo
#    Agrupa sanciones recibidas por cada equipo distinguiendo el motivo (roja, acumulación de amarillas, disciplinaria).
# def obtener_sanciones_por_equipo_y_motivo(id_torneo):
#     pass

if __name__ == "__main__":
    ID_TORNEO = 1  # Se debe crear un torneo antes

    crear_vistas()
    print("Vistas creadas.\n")

    # Tabla de posiciones
    print(f"--- Tabla de posiciones (torneo {ID_TORNEO}) ---")
    print("Equipo | PJ | GF | GC | DG | G | E | P | Pts")
    posiciones = tabla_posiciones(ID_TORNEO)
    for f in sorted(posiciones, key=lambda f: f["puntos"], reverse=True):
        print(f"{f['id_equipo']} | {f['partidos_jugados']} | {f['goles_a_favor']} | "
              f"{f['goles_en_contra']} | {f['diferencia_de_goles']} | {f['ganados']} | "
              f"{f['empatados']} | {f['perdidos']} | {f['puntos']}")
    if not posiciones:
        print("(sin partidos jugados en este torneo)")

    # Goleadores
    print("\n--- Top 10 goleadores ---")
    for g in goleadores():
        print(f"{g['nombre']} ({g['ci']}): {g['cantidad_goles']} goles")

    # Promedios de goles
    por_fecha, promedio_edicion = promedios_goles(ID_TORNEO)
    print(f"\n--- Promedio de goles por fecha (torneo {ID_TORNEO}) ---")
    for f in por_fecha:
        print(f"Fecha {f['numero_fecha']}: {f['cantidad_goles']} goles, "
              f"promedio {f['promedio_por_fecha']}")
    print("Promedio de la edición:", promedio_edicion)

    # Canchas más utilizadas
    print("\n--- Canchas más utilizadas ---")
    for c in canchas_mas_usadas():
        print(f"{c['nombre_cancha']}: {c['cantidad_de_usos_cancha']} usos")

    # Turnos más utilizados
    print("\n--- Turnos más utilizados ---")
    for t in turnos_mas_usados():
        print(f"{t['hora_inicio']} a {t['hora_fin']}: {t['cantidad_de_usos_hora']} usos")


