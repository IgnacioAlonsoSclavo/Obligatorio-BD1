from logica_db.conexion import obtener_conexion

# crear_jugador(ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo) -> bool (True si se creo, False si fallo)
# modificar_jugador(ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo) -> bool (True si se modifico, False si fallo)
# eliminar_jugador(ci) -> bool (True si se elimino, False si no existia)
# obtener_jugador(ci) -> dict con datos del jugador (o None si no existe)
# listar_jugadores() -> list de dicts con todos los jugadores
# listar_jugadores_por_facultad(id_facultad) -> list de dicts de jugadores de esa facultad
