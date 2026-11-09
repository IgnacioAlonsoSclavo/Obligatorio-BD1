import unittest
from logica_db.conexion import obtener_conexion
from logica_db.complejos import (
    listar_complejos, crear_complejo, modificar_complejo, eliminar_complejo,
    listar_canchas_completo, crear_cancha, modificar_cancha, eliminar_cancha
)
from logica_db.jugadores import (
    crear_jugador, modificar_jugador, eliminar_jugador, listar_jugadores
)
from logica_db.equipos import (
    crear_equipo, modificar_equipo, eliminar_equipo, obtener_equipo,
    obtener_plantel, quitar_jugador_de_plantel
)
from logica_db.sanciones import (
    crear_sancion, modificar_sancion, eliminar_sancion, listar_sanciones_por_torneo,
    jugador_esta_suspendido
)
from logica_db.partidos import (
    eliminar_partido, registrar_gol, modificar_gol, eliminar_gol,
    obtener_goles_partido, registrar_tarjeta, eliminar_tarjeta,
    obtener_tarjetas_partido
)
from logica_db.reportes import (
    tabla_posiciones, goleadores, promedios_goles, canchas_mas_usadas,
    turnos_mas_usados, jugadores_por_facultad_y_tipo, obtener_jugadores_sin_minutos,
    sanciones_por_equipo_y_motivo, obtener_porcentaje_estados_partidos,
    tabla_fair_play, mejor_defensa, efectividad_local_visitante, goles_por_tipo_jugador
)


class TestComplejosYCanchas(unittest.TestCase):

    def test_abm_complejo(self):
        nombre_test = "Complejo Test ABM"
        self.assertTrue(crear_complejo(nombre_test, "Calle Falsa 123", "Montevideo"))
        
        comps = [c for c in listar_complejos() if c["nombre"] == nombre_test]
        self.assertGreater(len(comps), 0)
        id_comp = comps[0]["id_complejo"]

        self.assertTrue(modificar_complejo(id_comp, "Complejo Test Mod", "Nueva Dir 456", "Canelones"))
        comps_mod = [c for c in listar_complejos() if c["id_complejo"] == id_comp]
        self.assertEqual(comps_mod[0]["nombre"], "Complejo Test Mod")
        self.assertEqual(comps_mod[0]["departamento"], "Canelones")

        self.assertFalse(modificar_complejo(id_comp, "", "", ""))
        self.assertTrue(eliminar_complejo(id_comp))

    def test_abm_cancha(self):
        comps = listar_complejos()
        self.assertGreater(len(comps), 0)
        id_comp = comps[0]["id_complejo"]
        nombre_cancha = "Cancha Test ABM"

        self.assertTrue(crear_cancha(nombre_cancha, id_comp, "sintético", True))
        
        canchas = [c for c in listar_canchas_completo() if c["nombre_cancha"] == nombre_cancha and c["id_complejo"] == id_comp]
        self.assertEqual(len(canchas), 1)

        self.assertTrue(modificar_cancha(nombre_cancha, id_comp, "Cancha Test Mod", "parquet", False))
        canchas_mod = [c for c in listar_canchas_completo() if c["nombre_cancha"] == "Cancha Test Mod" and c["id_complejo"] == id_comp]
        self.assertEqual(len(canchas_mod), 1)
        self.assertEqual(canchas_mod[0]["superficie"], "parquet")
        self.assertFalse(bool(canchas_mod[0]["techada"]))

        self.assertTrue(eliminar_cancha("Cancha Test Mod", id_comp))


class TestJugadoresYEquipos(unittest.TestCase):

    def test_abm_jugador(self):
        ci = 99887766
        self.assertTrue(crear_jugador(ci, "TestNombre", "TestApellido", "test@correo.ucu.edu.uy", "2000-01-01", 1, "grado"))
        self.assertTrue(modificar_jugador(ci, "NombreMod", "ApellidoMod", "mod@correo.ucu.edu.uy", "2000-01-01", 1, "posgrado"))
        self.assertTrue(eliminar_jugador(ci))

    def test_validacion_capitan_en_plantel(self):
        eq = obtener_equipo(1)
        self.assertIsNotNone(eq)
        plantel = obtener_plantel(1, 1)
        self.assertGreater(len(plantel), 0)

        ci_valida = plantel[0]["ci"]
        self.assertTrue(modificar_equipo(1, ci_capitan=ci_valida))
        self.assertEqual(obtener_equipo(1)["ci_capitan"], ci_valida)

        self.assertFalse(modificar_equipo(1, ci_capitan=99999999))

        if eq["ci_capitan"]:
            modificar_equipo(1, ci_capitan=eq["ci_capitan"])


class TestSanciones(unittest.TestCase):

    def test_abm_sancion(self):
        ci = 50100011
        id_torneo = 1
        self.assertTrue(crear_sancion(ci, id_torneo, "disciplinaria", 10, 1))
        
        sanciones = listar_sanciones_por_torneo(id_torneo)
        s_creada = [s for s in sanciones if s["ci_jugador"] == ci and s["numero_fecha_inicio"] == 10]
        self.assertGreater(len(s_creada), 0)
        id_sanc = s_creada[0]["id_sancion"]

        self.assertTrue(modificar_sancion(id_sanc, "roja", 11, 2))
        sanciones_mod = listar_sanciones_por_torneo(id_torneo)
        s_mod = [s for s in sanciones_mod if s["id_sancion"] == id_sanc][0]
        self.assertEqual(s_mod["motivo"], "roja")
        self.assertEqual(s_mod["numero_fecha_inicio"], 11)
        self.assertEqual(s_mod["cantidad_fechas"], 2)

        self.assertTrue(jugador_esta_suspendido(ci, id_torneo, 11))
        self.assertTrue(jugador_esta_suspendido(ci, id_torneo, 12))
        self.assertFalse(jugador_esta_suspendido(ci, id_torneo, 13))

        self.assertFalse(modificar_sancion(id_sanc, "invalido", 11, 2))
        self.assertTrue(eliminar_sancion(id_sanc))


class TestPartidosGolesYTarjetas(unittest.TestCase):

    def test_no_eliminar_partido_jugado(self):
        conn = obtener_conexion()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id_partido FROM partido WHERE estado = 'jugado' LIMIT 1")
        p = cur.fetchone()
        conn.close()
        if p:
            self.assertFalse(eliminar_partido(p["id_partido"]))

    def test_abm_partido_programado_y_eventos(self):
        conn = obtener_conexion()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            INSERT INTO partido (id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, dia, id_turno, nombre_cancha, id_complejo, estado)
            VALUES (1, 20, 1, 2, '2026-11-25', 1, 'Cancha 1', 1, 'programado')
        """)
        id_p = cur.lastrowid
        cur.execute("INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES (%s, 50100011, 1)", (id_p,))
        conn.commit()
        conn.close()

        self.assertTrue(registrar_gol(id_p, 50100011, 12, False))
        goles = obtener_goles_partido(id_p)
        self.assertEqual(len(goles), 1)
        id_gol = goles[0]["id_gol"]

        self.assertTrue(modificar_gol(id_gol, 25, True))
        goles_mod = obtener_goles_partido(id_p)
        self.assertEqual(goles_mod[0]["minuto"], 25)
        self.assertTrue(bool(goles_mod[0]["autogol"]))

        self.assertTrue(eliminar_gol(id_gol))
        self.assertEqual(len(obtener_goles_partido(id_p)), 0)

        self.assertTrue(registrar_tarjeta(id_p, 50100011, 30, "amarilla"))
        tarjetas = obtener_tarjetas_partido(id_p)
        self.assertEqual(len(tarjetas), 1)
        id_tarjeta = tarjetas[0]["id_tarjeta"]

        self.assertTrue(eliminar_tarjeta(id_tarjeta))
        self.assertEqual(len(obtener_tarjetas_partido(id_p)), 0)

        self.assertTrue(eliminar_partido(id_p))


class TestReportesEstadisticos(unittest.TestCase):

    def test_reportes_con_datos_de_prueba(self):
        id_torneo = 1
        posiciones = tabla_posiciones(id_torneo)
        self.assertGreaterEqual(len(posiciones), 6)

        gols = goleadores()
        self.assertGreaterEqual(len(gols), 10)

        por_fecha, prom = promedios_goles(id_torneo)
        self.assertGreaterEqual(len(por_fecha), 3)

        self.assertGreater(len(canchas_mas_usadas()), 0)
        self.assertGreater(len(turnos_mas_usados()), 0)
        self.assertGreater(len(jugadores_por_facultad_y_tipo()), 0)
        self.assertGreater(len(obtener_jugadores_sin_minutos(id_torneo)), 0)
        self.assertGreater(len(sanciones_por_equipo_y_motivo()), 0)

        pcts = obtener_porcentaje_estados_partidos(id_torneo)
        self.assertIn("porcentaje_jugados", pcts)

        self.assertGreater(len(tabla_fair_play(id_torneo)), 0)
        self.assertGreater(len(mejor_defensa(id_torneo)), 0)

        efect = efectividad_local_visitante(id_torneo)
        self.assertIn("total", efect)

        self.assertGreater(len(goles_por_tipo_jugador(id_torneo)), 0)


if __name__ == "__main__":
    unittest.main()
