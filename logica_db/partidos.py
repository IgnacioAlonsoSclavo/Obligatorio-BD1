from logica_db.conexion import obtener_conexion

#Vista para la primera Query
def crear_vista_goles_por_partido():
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute("""
            CREATE OR REPLACE VIEW goles_por_partido AS
            SELECT p.id_partido, p.id_equipo_local, p.id_equipo_visitante,
                   SUM(IF((ejt.id_equipo = p.id_equipo_local AND NOT g.autogol)
                       OR (ejt.id_equipo = p.id_equipo_visitante AND g.autogol), 1, 0)) AS goles_local,
                   SUM(IF((ejt.id_equipo = p.id_equipo_visitante AND NOT g.autogol)
                       OR (ejt.id_equipo = p.id_equipo_local AND g.autogol), 1, 0)) AS goles_visitante
            FROM partido p
            LEFT JOIN gol g ON g.id_partido = p.id_partido
            LEFT JOIN equipo_jugador_torneo ejt
              ON ejt.ci_jugador = g.ci_jugador
             AND ejt.id_equipo IN (p.id_equipo_local, p.id_equipo_visitante)
            WHERE p.estado = 'jugado'
            GROUP BY p.id_partido, p.id_equipo_local, p.id_equipo_visitante
        """)
        cursor.close()
    finally:
        conexion.close()