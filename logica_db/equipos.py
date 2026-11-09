from mysql.connector import Error

from logica_db.conexion import obtener_conexion

# crear_equipo(nombre, id_torneo, id_facultad, ci_capitan=None) -> bool (True si se creo, False si fallo)
def crear_equipo(nombre, id_torneo, id_facultad, ci_capitan=None):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
        INSERT INTO equipo (nombre,id_torneo, id_facultad, ci_capitan)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query,(nombre,id_torneo,id_facultad,ci_capitan))
        conexion.commit()
        return True
    except Error as e:
        conexion.rollback()
        print(f"Error al crear equipo: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()

# modificar_equipo(id_equipo, nombre=None, ci_capitan=None) -> bool (True si se modifico, False si fallo)
def modificar_equipo(id_equipo, nombre=None, ci_capitan=None):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_equipo FROM equipo WHERE id_equipo = %s", (id_equipo,))
        if not cursor.fetchone():
            print("Error, el equipo no se encontro")
            return False

        if ci_capitan is not None:
            query_verificar_plantel = """
                SELECT 1
                FROM equipo_jugador_torneo
                WHERE id_equipo = %s AND ci_jugador = %s
                LIMIT 1
            """
            cursor.execute(query_verificar_plantel, (id_equipo, ci_capitan))
            if not cursor.fetchone():
                print(f"Error: El jugador con CI {ci_capitan} no pertenece al plantel del equipo {id_equipo}.")
                return False

        query = """
            UPDATE equipo
            SET nombre = COALESCE(%s, nombre),
                ci_capitan = COALESCE(%s, ci_capitan)
            WHERE id_equipo = %s
        """
        cursor.execute(query, (nombre, ci_capitan, id_equipo))
        conexion.commit()
        print("Se actualizo el equipo correctamente.")
        return True
    except Error as e:
        conexion.rollback()
        print(f"Error al modificar equipo: {e}")
        return False

    finally:
        cursor.close()
        conexion.close()
# eliminar_equipo(id_equipo) -> bool (True si se elimino, False si fallo)
def eliminar_equipo(id_equipo):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                DELETE FROM equipo
                WHERE id_equipo = %s
                """
        cursor.execute(query,(id_equipo,))
        conexion.commit()
        if cursor.rowcount > 0:
            print("Se elimino el equipo correctamente.")
            return True
        print("Error, el equipo no se encontro")
        return False
    except Error as e:
        conexion.rollback()
        print(f"Error al eliminar equipo: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()

# obtener_equipo(id_equipo) -> dict con datos del equipo (o None si no existe)
def obtener_equipo(id_equipo):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                SELECT * FROM equipo
                WHERE id_equipo = %s
                """
        cursor.execute(query,(id_equipo,))
        return cursor.fetchone()
    except Error as e:
        print(f"Error al obtener equipo: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()

# listar_equipos_por_torneo(id_torneo) -> list de dicts con los equipos inscriptos
def listar_equipos(id_torneo=None):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        if id_torneo is not None:
            query = """
                    SELECT * FROM equipo
                    WHERE id_torneo = %s
                    ORDER BY nombre
                    """
            cursor.execute(query, (id_torneo,))
        else:
            query = """
                    SELECT * FROM equipo
                    ORDER BY id_torneo, nombre
                    """
            cursor.execute(query)
        return cursor.fetchall()
    except Error as e:
        print(f"Error al listar equipos: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()

# agregar_jugador_a_plantel(id_equipo, ci_jugador, id_torneo, numero_camiseta) -> bool (True si se agrego, False si incumple reglas)

def agregar_jugador(id_equipo, ci_jugador, id_torneo, numero_camiseta):
    if not torneo_en_inscripcion(id_torneo):
        return False
    if not jugador_equipo_misma_facultad(id_equipo, ci_jugador):
        return False
    if not jugador_sin_equipo(ci_jugador, id_torneo):
        return False
    if not equipo_con_cupo(id_equipo, id_torneo):
        return False
    if not equipo_con_cupo_docente_funcionario(id_equipo, ci_jugador, id_torneo):
        return False

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        query = """
            INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (id_equipo, ci_jugador, id_torneo, numero_camiseta))
        conexion.commit()
        print("Jugador agregado al plantel exitosamente.")
        return True
    except Error as e:
        conexion.rollback()
        print(f"Error al agregar jugador al plantel: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()

# quitar_jugador_de_plantel(id_equipo, ci_jugador, id_torneo) -> bool (True si se quito, False si fallo)
def quitar_jugador_de_plantel(id_equipo, ci_jugador, id_torneo):
    if not torneo_en_inscripcion(id_torneo):
        return False

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
                DELETE FROM equipo_jugador_torneo
                WHERE id_equipo = %s AND ci_jugador = %s AND id_torneo = %s
                """
        cursor.execute(query, (id_equipo, ci_jugador, id_torneo))
        if cursor.rowcount > 0:
            # Si el jugador eliminado era el capitán del equipo, se remueve la capitanía
            cursor.execute("""
                UPDATE equipo
                SET ci_capitan = NULL
                WHERE id_equipo = %s AND ci_capitan = %s
            """, (id_equipo, ci_jugador))
            conexion.commit()
            print("Se ha quitado el jugador del plantel.")
            return True
        else:
            conexion.rollback()
            print("El jugador no pertenecia al plantel del equipo.")
            return False
    except Error as e:
        conexion.rollback()
        print(f"Error al quitar jugador del plantel: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()

def torneo_en_inscripcion(id_torneo):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT estado FROM torneo WHERE id_torneo = %s", (id_torneo,))
        torneo = cursor.fetchone()
        if not torneo:
            print("Error: El torneo no existe")
            return False
        if torneo['estado'] != 'inscripción':
            print(f"Error: No se puede modificar el estado, el torneo esta {torneo['estado']}")
            return False
        return True
    finally:
        cursor.close()
        conexion.close()

def jugador_equipo_misma_facultad(id_equipo, ci_jugador):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_facultad FROM equipo WHERE id_equipo = %s", (id_equipo,))
        equipo = cursor.fetchone()
        cursor.execute("SELECT id_facultad FROM jugador WHERE ci = %s", (ci_jugador,))
        jugador = cursor.fetchone()

        if not equipo:
            print("Error: El equipo no existe.")
            return False
        if not jugador:
            print("Error: El jugador no existe.")
            return False

        if equipo['id_facultad'] != jugador['id_facultad']:
            print("Error: El jugador y el equipo no pertenecen a la misma facultad.")
            return False
        return True
    finally:
        cursor.close()
        conexion.close()

def jugador_sin_equipo(ci_jugador, id_torneo):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
            SELECT * FROM equipo_jugador_torneo
            WHERE ci_jugador = %s AND id_torneo = %s
        """
        cursor.execute(query, (ci_jugador, id_torneo))
        equipo_jugador = cursor.fetchone()
        if equipo_jugador:
            print("Error: El jugador ya pertenece a un equipo en esta edición del torneo.")
            return False
        return True
    finally:
        cursor.close()
        conexion.close()

def equipo_con_cupo(id_equipo, id_torneo):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
            SELECT COUNT(*) AS cantidad 
            FROM equipo_jugador_torneo 
            WHERE id_equipo = %s AND id_torneo = %s
        """
        cursor.execute(query, (id_equipo, id_torneo))
        cantidad_jugadores = cursor.fetchone()
        if cantidad_jugadores and cantidad_jugadores['cantidad'] >= 10:
            print("Error: El equipo ya tiene el cupo maximo de 10 jugadores.")
            return False
        return True
    finally:
        cursor.close()
        conexion.close()

def equipo_con_cupo_docente_funcionario(id_equipo, ci_jugador, id_torneo):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT tipo FROM jugador WHERE ci = %s", (ci_jugador,))
        jugador = cursor.fetchone()
        if not jugador:
            print("Error: El jugador no existe.")
            return False

        # Si es estudiante (grado o posgrado), no consume cupo de docente/funcionario
        if jugador['tipo'] not in ('docente', 'funcionario'):
            return True

        query = """
            SELECT COUNT(DISTINCT ejt.ci_jugador) AS cantidad
            FROM equipo_jugador_torneo ejt
            JOIN jugador j ON ejt.ci_jugador = j.ci
            WHERE ejt.id_equipo = %s AND ejt.id_torneo = %s 
              AND j.tipo IN ('docente', 'funcionario')
        """
        cursor.execute(query, (id_equipo, id_torneo))
        total = cursor.fetchone()
        if total and total['cantidad'] >= 2:
            print("Error: El equipo ya cuenta con el cupo maximo de 2 docentes/funcionarios.")
            return False
        return True
    finally:
        cursor.close()
        conexion.close()
# obtener_plantel(id_equipo, id_torneo) -> list de dicts con los jugadores inscriptos del equipo
def obtener_plantel(id_equipo, id_torneo):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
            SELECT j.ci, j.nombre, j.apellido, ejt.numero_camiseta, j.tipo, (j.ci = e.ci_capitan) AS es_capitan
            FROM equipo_jugador_torneo ejt
            JOIN jugador j ON ejt.ci_jugador = j.ci
            JOIN equipo e ON ejt.id_equipo = e.id_equipo
            WHERE ejt.id_equipo = %s AND ejt.id_torneo = %s
            ORDER BY ejt.numero_camiseta ASC;
            """
        cursor.execute(query,(id_equipo, id_torneo))
        return cursor.fetchall()

    except Error as e:
        print(f"Error al obtener el plantel: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()
