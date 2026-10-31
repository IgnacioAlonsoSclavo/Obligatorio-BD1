from logica_db.conexion import obtener_conexion

def jugadores_por_facultad_y_tipo():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
            SELECT f.id_facultad, f.nombre AS facultad, j.tipo, COUNT(*) AS cantidad_jugadores
            FROM jugador AS j
            JOIN facultad AS f ON f.id_facultad = j.id_facultad
            GROUP BY f.id_facultad, f.nombre, j.tipo
            ORDER BY f.nombre, j.tipo
        """

        cursor.execute(query)
        return cursor.fetchall()
    finally:
            cursor.close()
            conexion.close()