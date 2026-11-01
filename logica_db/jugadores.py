from logica_db.conexion import obtener_conexion

#Segunda Query
def goleadores():
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT j.ci, j.nombre, COUNT(ci_jugador) AS cantidad_goles
            FROM gol g JOIN jugador j ON g.ci_jugador = j.ci
            WHERE !autogol
            GROUP BY j.ci, j.nombre
            ORDER BY cantidad_goles DESC
            LIMIT 10
        """, (limite,))
        resultado = cursor.fetchall()
        cursor.close()
        return resultado
    finally:
        conexion.close()