from logica_db.conexion import obtener_conexion

# jugador_esta_suspendido(ci_jugador, id_torneo, numero_fecha) -> bool (True si esta sancionado para esa fecha, False si puede jugar)
# crear_sancion(ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas) -> bool (True si se aplico la sancion, False si fallo)
# generar_sanciones_automaticas(id_partido) -> bool (True si proceso rojas y amarillas acumuladas, False si hubo error)
# listar_sanciones_por_torneo(id_torneo) -> list de dicts con todas las sanciones de la edicion
# eliminar_sancion(id_sancion) -> bool (True si se elimino, False si fallo)
