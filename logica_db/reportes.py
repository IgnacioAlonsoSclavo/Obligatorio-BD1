from logica_db.conexion import obtener_conexion

# 3. Tabla de Fair Play por equipo
#    Cálculo: 1 punto por tarjeta amarilla y 3 puntos por cada roja.
#    Criterio de orden: El mejor equipo es el de menor puntaje acumulado (ASC).
# def obtener_tabla_fair_play(id_torneo):
#     pass

# 5. Canchas y turnos más utilizados
#    Identifica qué complejos/canchas y horarios tienen mayor cantidad de partidos programados/jugados.
# def obtener_canchas_turnos_mas_usados(id_torneo):
#     pass

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



# 8. Cantidad de sanciones por equipo y por motivo
#    Agrupa sanciones recibidas por cada equipo distinguiendo el motivo (roja, acumulación de amarillas, disciplinaria).
# def obtener_sanciones_por_equipo_y_motivo(id_torneo):
#     pass


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