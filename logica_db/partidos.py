from logica_db.conexion import obtener_conexion

#funciones del administrador
# programar_partido(id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, dia, id_turno, nombre_cancha, id_complejo) -> bool (True si se programo, False si viola restricciones)
# modificar_partido(id_partido, dia, id_turno, nombre_cancha, id_complejo, estado) -> bool (True si se modifico, False si fallo)
# listar_partidos_por_fecha(id_torneo, numero_fecha) -> list de dicts con los partidos de la fecha
# obtener_partido(id_partido) -> dict con datos del partido (o None si no existe)

#funciones del planillero
# registrar_jugador_en_planilla(id_partido, ci_jugador, id_equipo) -> bool (True si se registro, False si esta suspendido o no pertenece al plantel)
# registrar_gol(id_partido, ci_jugador, minuto, autogol) -> bool (True si se registro, False si no esta en planilla)
# registrar_tarjeta(id_partido, ci_jugador, minuto, color) -> bool (True si se registro, False si no esta en planilla)
# cerrar_partido_como_jugado(id_partido) -> bool (True si se marco como jugado, False si todavia no paso la hora)
# obtener_planilla_partido(id_partido) -> list de dicts con jugadores habilitados que jugaron
# obtener_resultado_partido(id_partido) -> dict con {'goles_local': int, 'goles_visitante': int}
