from logica_db.conexion import obtener_conexion

# crear_equipo(nombre, id_torneo, id_facultad, ci_capitan) -> bool (True si se creo, False si fallo)
# modificar_equipo(id_equipo, nombre, ci_capitan) -> bool (True si se modifico, False si fallo)
# eliminar_equipo(id_equipo) -> bool (True si se elimino, False si fallo)
# obtener_equipo(id_equipo) -> dict con datos del equipo (o None si no existe)
# listar_equipos_por_torneo(id_torneo) -> list de dicts con los equipos inscriptos


# agregar_jugador_a_plantel(id_equipo, ci_jugador, id_torneo, numero_camiseta) -> bool (True si se agrego, False si incumple reglas)
# quitar_jugador_de_plantel(id_equipo, ci_jugador, id_torneo) -> bool (True si se quito, False si fallo)
# obtener_plantel(id_equipo, id_torneo) -> list de dicts con los jugadores inscriptos del equipo
