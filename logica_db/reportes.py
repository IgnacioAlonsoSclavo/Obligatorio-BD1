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
        fila = cursor.fetchone()
        promedio_edicion = fila["promedio_en_la_edicion"] if fila and fila["promedio_en_la_edicion"] is not None else 0.0

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
            FROM cancha c JOIN partido p ON c.nombre_cancha = p.nombre_cancha AND c.id_complejo = p.id_complejo
            WHERE p.estado = 'jugado'
            GROUP BY c.nombre_cancha, c.id_complejo
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

def sanciones_por_equipo_y_motivo():
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT ejt.id_equipo, e.nombre, sj.motivo, COUNT(sj.motivo) AS cantidad
            FROM sancion_jugador sj JOIN equipo_jugador_torneo ejt ON sj.ci_jugador = ejt.ci_jugador AND sj.id_torneo = ejt.id_torneo
            JOIN equipo e ON ejt.id_equipo = e.id_equipo
            GROUP BY ejt.id_equipo, e.nombre, sj.motivo
            ORDER BY e.nombre, sj.motivo
        """)
        resultado = cursor.fetchall()
        cursor.close()
        return resultado
    finally:
        conexion.close()

if __name__ == "__main__":
    ID_TORNEO = 1  # Se debe crear un torneo antes

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

    # Porcentaje de estados
    print("\n--- Porcentaje de estados de partidos ---")
    print(obtener_porcentaje_estados_partidos(ID_TORNEO))

    # Jugadores sin minutos
    print("\n--- Jugadores sin minutos ---")
    print(obtener_jugadores_sin_minutos(ID_TORNEO))

    # Sanciones por equipo y motivos
    print("\n--- Sanciones por equipo y motivo ---")
    for s in sanciones_por_equipo_y_motivo():
        print(f"{s['nombre']} ({s['id_equipo']}) - {s['motivo']}: {s['cantidad']}")


