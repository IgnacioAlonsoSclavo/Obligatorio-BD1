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
            return {
                "total_partidos": 0,
                "porcentaje_jugados": 0.0,
                "porcentaje_postergados_cancelados": 0.0
            }
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
                   e.nombre AS nombre_equipo,
                   r.partidos_jugados,
                   g.goles_a_favor,
                   g.goles_en_contra,
                   g.diferencia_de_goles,
                   r.ganados,
                   r.empatados,
                   r.perdidos,
                   r.puntos
            FROM resultados_equipo r
            JOIN goles_equipo g ON g.id_equipo = r.id_equipo
            JOIN equipo e ON e.id_equipo = r.id_equipo
            WHERE e.id_torneo = %s
            ORDER BY r.puntos DESC, g.diferencia_de_goles DESC, g.goles_a_favor DESC;
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


def tabla_fair_play(id_torneo):
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT e.id_equipo,
                   e.nombre AS nombre_equipo,
                   COALESCE(SUM(IF(p.id_torneo = %s AND t.color = 'amarilla', 1, 0)), 0) AS amarillas,
                   COALESCE(SUM(IF(p.id_torneo = %s AND t.color = 'roja', 1, 0)), 0) AS rojas,
                   COALESCE(SUM(IF(p.id_torneo = %s,
                                   IF(t.color = 'amarilla', 1, IF(t.color = 'roja', 3, 0)),
                                   0)), 0) AS puntos_fair_play
            FROM equipo e
            LEFT JOIN equipo_jugador_torneo ejt ON ejt.id_equipo = e.id_equipo AND ejt.id_torneo = e.id_torneo
            LEFT JOIN tarjeta t ON t.ci_jugador = ejt.ci_jugador
            LEFT JOIN partido p ON p.id_partido = t.id_partido AND p.id_torneo = %s
            WHERE e.id_torneo = %s
            GROUP BY e.id_equipo, e.nombre
            ORDER BY puntos_fair_play ASC, rojas ASC, amarillas ASC;
        """, (id_torneo, id_torneo, id_torneo, id_torneo, id_torneo))
        resultado = cursor.fetchall()
        cursor.close()
        return resultado
    finally:
        conexion.close()


def jugadores_por_facultad_y_tipo():
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT f.id_facultad,
                   f.nombre AS nombre_facultad,
                   COUNT(IF(j.tipo = 'grado', 1, NULL)) AS total_grado,
                   COUNT(IF(j.tipo = 'posgrado', 1, NULL)) AS total_posgrado,
                   COUNT(IF(j.tipo = 'docente', 1, NULL)) AS total_docente,
                   COUNT(IF(j.tipo = 'funcionario', 1, NULL)) AS total_funcionario,
                   COUNT(j.ci) AS total_jugadores
            FROM facultad f
            LEFT JOIN jugador j ON f.id_facultad = j.id_facultad
            GROUP BY f.id_facultad, f.nombre
            ORDER BY f.id_facultad ASC;
        """)
        resultado = cursor.fetchall()
        cursor.close()
        return resultado
    finally:
        conexion.close()


def mejor_defensa(id_torneo):
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT e.id_equipo,
                   e.nombre AS nombre_equipo,
                   r.partidos_jugados,
                   g.goles_en_contra,
                   ROUND(g.goles_en_contra / r.partidos_jugados, 2) AS promedio_recibidos
            FROM resultados_equipo r
            JOIN goles_equipo g ON g.id_equipo = r.id_equipo
            JOIN equipo e ON e.id_equipo = r.id_equipo
            WHERE e.id_torneo = %s AND r.partidos_jugados > 0
            ORDER BY promedio_recibidos ASC, g.goles_en_contra ASC;
        """, (id_torneo,))
        resultado = cursor.fetchall()
        cursor.close()
        return resultado
    finally:
        conexion.close()


def efectividad_local_visitante(id_torneo):
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                SUM(IF(goles_local > goles_visitante, 1, 0)) AS victorias_local,
                SUM(IF(goles_visitante > goles_local, 1, 0)) AS victorias_visitante,
                SUM(IF(goles_local = goles_visitante, 1, 0)) AS empates,
                COUNT(*) AS total_jugados
            FROM goles_por_partido gp
            JOIN partido p ON p.id_partido = gp.id_partido
            WHERE p.id_torneo = %s AND p.estado = 'jugado';
        """, (id_torneo,))
        fila = cursor.fetchone()
        cursor.close()
        if not fila or not fila["total_jugados"]:
            return {"total": 0, "vic_local": 0, "vic_visitante": 0, "empates": 0, "pct_local": 0, "pct_visitante": 0, "pct_empate": 0}

        total = fila["total_jugados"]
        vl = fila["victorias_local"] or 0
        vv = fila["victorias_visitante"] or 0
        em = fila["empates"] or 0
        return {
            "total": total,
            "vic_local": vl,
            "vic_visitante": vv,
            "empates": em,
            "pct_local": round((vl / total) * 100, 1),
            "pct_visitante": round((vv / total) * 100, 1),
            "pct_empate": round((em / total) * 100, 1)
        }
    finally:
        conexion.close()


def goles_por_tipo_jugador(id_torneo):
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT j.tipo AS tipo_jugador,
                   COUNT(g.id_gol) AS total_goles,
                   COUNT(DISTINCT j.ci) AS cantidad_goleadores,
                   ROUND(COUNT(g.id_gol) / COUNT(DISTINCT j.ci), 2) AS promedio_por_goleador
            FROM gol g
            JOIN jugador j ON g.ci_jugador = j.ci
            JOIN partido p ON g.id_partido = p.id_partido
            WHERE p.id_torneo = %s AND g.autogol = FALSE
            GROUP BY j.tipo
            ORDER BY total_goles DESC;
        """, (id_torneo,))
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

    # Fair Play por equipo
    print(f"\n--- Fair play (torneo {ID_TORNEO}) ---")
    for f in tabla_fair_play(ID_TORNEO):
        print(f"{f['nombre']} ({f['id_equipo']}): {f['puntos_fair_play']} puntos")
