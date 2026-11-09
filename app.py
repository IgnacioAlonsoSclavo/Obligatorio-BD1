import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session

from logica_db.usuarios import validar_login, crear_usuario, existe_administrador
from logica_db.equipos import (
    crear_equipo, modificar_equipo, eliminar_equipo, obtener_equipo,
    listar_equipos, agregar_jugador, quitar_jugador_de_plantel, obtener_plantel
)
from logica_db.jugadores import (
    crear_jugador, modificar_jugador, eliminar_jugador, listar_jugadores, listar_jugadores_por_facultad
)
from logica_db.sanciones import (
    crear_sancion, modificar_sancion, eliminar_sancion, listar_sanciones_por_torneo,
    jugador_esta_suspendido
)
from logica_db.reportes import (
    tabla_posiciones, goleadores, promedios_goles,
    canchas_mas_usadas, turnos_mas_usados,
    obtener_porcentaje_estados_partidos, obtener_jugadores_sin_minutos,
    sanciones_por_equipo_y_motivo, tabla_fair_play,
    jugadores_por_facultad_y_tipo, mejor_defensa,
    efectividad_local_visitante, goles_por_tipo_jugador
)
from logica_db.partidos import (
    programar_partido, modificar_partido, eliminar_partido, listar_partidos_por_fecha, obtener_partido,
    registrar_jugador_en_planilla, registrar_gol, modificar_gol, eliminar_gol, registrar_tarjeta, eliminar_tarjeta,
    cerrar_partido_como_jugado, obtener_planilla_partido, obtener_resultado_partido,
    obtener_goles_partido, obtener_tarjetas_partido, listar_canchas, listar_turnos
)
from logica_db.complejos import (
    listar_complejos, crear_complejo, modificar_complejo, eliminar_complejo,
    listar_canchas_completo, crear_cancha, modificar_cancha, eliminar_cancha
)

app = Flask(__name__)
app.secret_key = os.urandom(24)


# -------------------------------------------------------------
# Decoradores de autenticación
# -------------------------------------------------------------

def login_requerido(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario" not in session:
            flash("Debe iniciar sesión para ingresar a esta sección.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def admin_requerido(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario" not in session or session["usuario"].get("rol") != "admin":
            flash("Acceso restringido: Requiere rol de Administrador.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# -------------------------------------------------------------
# Control de Administrador Inicial
# -------------------------------------------------------------

@app.before_request
def verificar_admin_inicial():
    # Si la base de datos no tiene administrador, redirigir automáticamente al registro inicial
    if request.endpoint and request.endpoint not in ("registro_inicial", "static"):
        if not existe_administrador():
            return redirect(url_for("registro_inicial"))


@app.route("/registro-inicial", methods=["GET", "POST"])
def registro_inicial():
    if existe_administrador():
        flash("El administrador principal ya se encuentra registrado.", "info")
        return redirect(url_for("login"))

    if request.method == "POST":
        correo = request.form.get("correo", "").strip()
        contrasenia = request.form.get("contrasenia", "").strip()

        if crear_usuario(correo, contrasenia, "admin"):
            flash("¡Administrador principal creado exitosamente! Ingrese con sus credenciales.", "success")
            return redirect(url_for("login"))
        else:
            flash("Error al registrar. Recuerde usar un correo @ucu.edu.uy y contraseña de mínimo 4 caracteres.", "danger")

    return render_template("registro_inicial.html")


# -------------------------------------------------------------
# Menú Principal y Acceso
# -------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form.get("correo", "").strip()
        contrasenia = request.form.get("contrasenia", "").strip()

        usuario = validar_login(correo, contrasenia)
        if usuario:
            session["usuario"] = usuario
            flash(f"¡Bienvenido/a {usuario['correo']}!", "success")
            if usuario["rol"] == "admin":
                return redirect(url_for("admin_panel"))
            elif usuario["rol"] == "planillero":
                return redirect(url_for("planillero_panel"))
            else:
                return redirect(url_for("index"))
        else:
            flash("Credenciales incorrectas. Verifique correo y contraseña.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión.", "info")
    return redirect(url_for("index"))


# -------------------------------------------------------------
# Consultas Públicas
# -------------------------------------------------------------

@app.route("/consultas-publicas")
def consultas_publicas():
    id_torneo = request.args.get("id_torneo", 1, type=int)
    pos = tabla_posiciones(id_torneo)
    gols = goleadores()
    por_fecha, prom_edicion = promedios_goles(id_torneo)
    canchas = canchas_mas_usadas()
    turnos = turnos_mas_usados()
    estados = obtener_porcentaje_estados_partidos(id_torneo)
    sin_min = obtener_jugadores_sin_minutos(id_torneo)
    sanc_equipo = sanciones_por_equipo_y_motivo()
    fair_play = tabla_fair_play(id_torneo)
    por_facultad = jugadores_por_facultad_y_tipo()
    defensa = mejor_defensa(id_torneo)
    efectividad = efectividad_local_visitante(id_torneo)
    goles_tipo = goles_por_tipo_jugador(id_torneo)

    return render_template(
        "consultas_publicas.html",
        id_torneo=id_torneo,
        posiciones=pos,
        goleadores=gols,
        por_fecha=por_fecha,
        promedio_edicion=prom_edicion,
        canchas=canchas,
        turnos=turnos,
        estados=estados,
        sin_minutos=sin_min,
        sanciones_equipo=sanc_equipo,
        fair_play=fair_play,
        por_facultad=por_facultad,
        defensa=defensa,
        efectividad=efectividad,
        goles_tipo=goles_tipo
    )


# -------------------------------------------------------------
# Panel de Administrador
# -------------------------------------------------------------

@app.route("/admin")
@admin_requerido
def admin_panel():
    return render_template("admin_panel.html")


# 1. Equipos
@app.route("/admin/equipos")
@admin_requerido
def admin_equipos():
    equipos = listar_equipos()
    return render_template("admin_equipos.html", equipos=equipos)


@app.route("/admin/equipos/crear", methods=["POST"])
@admin_requerido
def admin_crear_equipo():
    nombre = request.form.get("nombre", "").strip()
    id_torneo = request.form.get("id_torneo", type=int)
    id_facultad = request.form.get("id_facultad", type=int)
    ci_capitan = request.form.get("ci_capitan", type=int)

    if crear_equipo(nombre, id_torneo, id_facultad, ci_capitan):
        flash(f"Equipo '{nombre}' registrado exitosamente.", "success")
    else:
        flash("Error al registrar equipo. Verifique que el torneo y facultad existan (y que la CI del capitán pertenezca a un jugador registrado si la indicó).", "danger")
    return redirect(url_for("admin_equipos"))


@app.route("/admin/equipos/<int:id_equipo>/designar-capitan/<int:ci>", methods=["POST"])
@admin_requerido
def admin_designar_capitan(id_equipo, ci):
    if modificar_equipo(id_equipo, ci_capitan=ci):
        flash(f"Capitán actualizado exitosamente (CI: {ci}).", "success")
    else:
        flash("Error al designar capitán. El jugador debe pertenecer al plantel del equipo.", "danger")
    return redirect(url_for("admin_plantel", id_equipo=id_equipo))


@app.route("/admin/equipos/<int:id_equipo>/modificar", methods=["POST"])
@admin_requerido
def admin_modificar_equipo(id_equipo):
    nombre = request.form.get("nombre", "").strip() or None
    if modificar_equipo(id_equipo, nombre=nombre):
        flash("Equipo actualizado exitosamente.", "success")
    else:
        flash("Error al modificar el equipo.", "danger")
    return redirect(url_for("admin_equipos"))


@app.route("/admin/equipos/<int:id_equipo>/eliminar", methods=["POST"])
@admin_requerido
def admin_eliminar_equipo(id_equipo):
    if eliminar_equipo(id_equipo):
        flash("Equipo eliminado correctamente.", "success")
    else:
        flash("No se pudo eliminar el equipo.", "danger")
    return redirect(url_for("admin_equipos"))


# Plantel de un equipo
@app.route("/admin/equipos/<int:id_equipo>/plantel")
@admin_requerido
def admin_plantel(id_equipo):
    equipo = obtener_equipo(id_equipo)
    if not equipo:
        flash("Equipo no encontrado.", "danger")
        return redirect(url_for("admin_equipos"))

    plantel = obtener_plantel(id_equipo, equipo["id_torneo"])
    return render_template("admin_plantel.html", equipo=equipo, plantel=plantel)


@app.route("/admin/equipos/<int:id_equipo>/plantel/agregar", methods=["POST"])
@admin_requerido
def admin_agregar_jugador(id_equipo):
    ci_jugador = request.form.get("ci_jugador", type=int)
    id_torneo = request.form.get("id_torneo", type=int)
    numero_camiseta = request.form.get("numero_camiseta", type=int)

    if agregar_jugador(id_equipo, ci_jugador, id_torneo, numero_camiseta):
        flash("Jugador inscrito exitosamente al plantel.", "success")
    else:
        flash("No se pudo inscribir al jugador. No cumple las 5 reglas del torneo (misma facultad, cupo máx 10, máx 2 docentes/funcionarios o período cerrado).", "danger")

    return redirect(url_for("admin_plantel", id_equipo=id_equipo))


@app.route("/admin/equipos/<int:id_equipo>/plantel/quitar/<int:ci>/<int:id_torneo>", methods=["POST"])
@admin_requerido
def admin_quitar_jugador(id_equipo, ci, id_torneo):
    if quitar_jugador_de_plantel(id_equipo, ci, id_torneo):
        flash("Jugador desvinculado del plantel.", "success")
    else:
        flash("No se pudo desvincular al jugador.", "danger")
    return redirect(url_for("admin_plantel", id_equipo=id_equipo))


# 2. Jugadores
@app.route("/admin/jugadores")
@admin_requerido
def admin_jugadores():
    id_facultad = request.args.get("id_facultad", type=int)
    if id_facultad:
        jugadores = listar_jugadores_por_facultad(id_facultad)
    else:
        jugadores = listar_jugadores()
    return render_template("admin_jugadores.html", jugadores=jugadores)


@app.route("/admin/jugadores/crear", methods=["POST"])
@admin_requerido
def admin_crear_jugador():
    ci = request.form.get("ci", type=int)
    nombre = request.form.get("nombre", "").strip()
    apellido = request.form.get("apellido", "").strip()
    email = request.form.get("email", "").strip()
    fecha_nac = request.form.get("fecha_nacimiento", "").strip()
    id_facultad = request.form.get("id_facultad", type=int)
    tipo = request.form.get("tipo", "").strip()

    if crear_jugador(ci, nombre, apellido, email, fecha_nac, id_facultad, tipo):
        flash(f"Jugador {nombre} {apellido} registrado con éxito.", "success")
    else:
        flash("Error al registrar el jugador. Verifique los datos o si la cédula ya existe.", "danger")
    return redirect(url_for("admin_jugadores"))


@app.route("/admin/jugadores/<int:ci>/modificar", methods=["POST"])
@admin_requerido
def admin_modificar_jugador(ci):
    nombre = request.form.get("nombre", "").strip() or None
    apellido = request.form.get("apellido", "").strip() or None
    email = request.form.get("email", "").strip() or None
    fecha_nac = request.form.get("fecha_nacimiento", "").strip() or None
    id_facultad = request.form.get("id_facultad", type=int)
    tipo = request.form.get("tipo", "").strip() or None

    if modificar_jugador(ci, nombre, apellido, email, fecha_nac, id_facultad, tipo):
        flash(f"Datos del jugador CI {ci} actualizados exitosamente.", "success")
    else:
        flash(f"Error al modificar el jugador CI {ci}.", "danger")
    return redirect(url_for("admin_jugadores"))


@app.route("/admin/jugadores/<int:ci>/eliminar", methods=["POST"])
@admin_requerido
def admin_eliminar_jugador(ci):
    if eliminar_jugador(ci):
        flash("Jugador eliminado.", "success")
    else:
        flash("No se pudo eliminar al jugador.", "danger")
    return redirect(url_for("admin_jugadores"))


# 3. Sanciones
@app.route("/admin/sanciones")
@admin_requerido
def admin_sanciones():
    id_torneo = request.args.get("id_torneo", 1, type=int)
    sanciones = listar_sanciones_por_torneo(id_torneo)
    return render_template("admin_sanciones.html", sanciones=sanciones, id_torneo=id_torneo)


@app.route("/admin/sanciones/crear", methods=["POST"])
@admin_requerido
def admin_crear_sancion():
    ci_jugador = request.form.get("ci_jugador", type=int)
    id_torneo = request.form.get("id_torneo", type=int)
    motivo = request.form.get("motivo", "").strip()
    numero_fecha_inicio = request.form.get("numero_fecha_inicio", type=int)
    cantidad_fechas = request.form.get("cantidad_fechas", type=int)

    if crear_sancion(ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas):
        flash("Sanción registrada correctamente.", "success")
    else:
        flash("Error al registrar la sanción.", "danger")
    return redirect(url_for("admin_sanciones", id_torneo=id_torneo))


@app.route("/admin/sanciones/<int:id_sancion>/eliminar", methods=["POST"])
@admin_requerido
def admin_eliminar_sancion(id_sancion):
    id_torneo = request.args.get("id_torneo", 1, type=int)
    if eliminar_sancion(id_sancion):
        flash("Sanción revocada con éxito.", "success")
    else:
        flash("No se pudo revocar la sanción.", "danger")
    return redirect(url_for("admin_sanciones", id_torneo=id_torneo))


@app.route("/admin/sanciones/<int:id_sancion>/modificar", methods=["POST"])
@admin_requerido
def admin_modificar_sancion(id_sancion):
    id_torneo = request.form.get("id_torneo", 1, type=int)
    motivo = request.form.get("motivo", "").strip()
    numero_fecha_inicio = request.form.get("numero_fecha_inicio", type=int)
    cantidad_fechas = request.form.get("cantidad_fechas", type=int)

    if modificar_sancion(id_sancion, motivo, numero_fecha_inicio, cantidad_fechas):
        flash("Sanción modificada correctamente.", "success")
    else:
        flash("Error al modificar la sanción. Verifique los datos ingresados.", "danger")

    return redirect(url_for("admin_sanciones", id_torneo=id_torneo))


@app.route("/admin/sanciones/verificar", methods=["POST"])
@admin_requerido
def admin_verificar_suspension():
    ci_jugador = request.form.get("ci_jugador", type=int)
    id_torneo = request.form.get("id_torneo", type=int)
    numero_fecha = request.form.get("numero_fecha", type=int)

    suspendido = jugador_esta_suspendido(ci_jugador, id_torneo, numero_fecha)
    if suspendido:
        flash(f"⚠️ El jugador CI {ci_jugador} ESTÁ SUSPENDIDO para la Fecha {numero_fecha}.", "danger")
    else:
        flash(f"✅ El jugador CI {ci_jugador} está HABILITADO para disputar la Fecha {numero_fecha}.", "success")

    return redirect(url_for("admin_sanciones", id_torneo=id_torneo))


# 4. Gestión de Fixture y Partidos
@app.route("/admin/partidos")
@admin_requerido
def admin_partidos():
    id_torneo = request.args.get("id_torneo", 1, type=int)
    numero_fecha = request.args.get("numero_fecha", 1, type=int)
    partidos = listar_partidos_por_fecha(id_torneo, numero_fecha)
    for p in partidos:
        if p["estado"] == "jugado":
            p["resultado"] = obtener_resultado_partido(p["id_partido"])
    equipos = listar_equipos(id_torneo)
    canchas = listar_canchas()
    turnos = listar_turnos()
    return render_template(
        "admin_partidos.html",
        id_torneo=id_torneo,
        numero_fecha=numero_fecha,
        partidos=partidos,
        equipos=equipos,
        canchas=canchas,
        turnos=turnos
    )


@app.route("/admin/partidos/programar", methods=["POST"])
@admin_requerido
def admin_programar_partido():
    id_torneo = request.form.get("id_torneo", type=int)
    numero_fecha = request.form.get("numero_fecha", type=int)
    id_equipo_local = request.form.get("id_equipo_local", type=int)
    id_equipo_visitante = request.form.get("id_equipo_visitante", type=int)
    dia = request.form.get("dia", "").strip()
    id_turno = request.form.get("id_turno", type=int)
    cancha_complejo = request.form.get("cancha_complejo", "").strip()

    nombre_cancha = ""
    id_complejo = None
    if "|" in cancha_complejo:
        partes = cancha_complejo.split("|")
        nombre_cancha = partes[0].strip()
        id_complejo = int(partes[1].strip())

    if programar_partido(id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, dia, id_turno, nombre_cancha, id_complejo):
        flash("Partido programado exitosamente.", "success")
    else:
        flash("No se pudo programar el partido. Verifique que ambos equipos tengan al menos 5 jugadores en el torneo, no jueguen dos veces en la misma fecha ni repitan cruce en la edición, y que la cancha esté libre en ese turno.", "danger")

    return redirect(url_for("admin_partidos", id_torneo=id_torneo, numero_fecha=numero_fecha))


@app.route("/admin/partidos/<int:id_partido>/modificar", methods=["POST"])
@admin_requerido
def admin_modificar_partido(id_partido):
    id_torneo = request.form.get("id_torneo", 1, type=int)
    numero_fecha = request.form.get("numero_fecha", 1, type=int)
    dia = request.form.get("dia", "").strip() or None
    id_turno = request.form.get("id_turno", type=int)
    cancha_complejo = request.form.get("cancha_complejo", "").strip()
    estado = request.form.get("estado", "").strip()

    nombre_cancha = None
    id_complejo = None
    if cancha_complejo and "|" in cancha_complejo:
        partes = cancha_complejo.split("|")
        nombre_cancha = partes[0].strip()
        id_complejo = int(partes[1].strip())

    if modificar_partido(id_partido, dia, id_turno, nombre_cancha, id_complejo, estado):
        flash("Partido modificado exitosamente.", "success")
    else:
        flash("Error al modificar partido. No se puede modificar un partido ya jugado, ni asignar una cancha ocupada en ese turno.", "danger")

    return redirect(url_for("admin_partidos", id_torneo=id_torneo, numero_fecha=numero_fecha))


@app.route("/admin/partidos/<int:id_partido>/eliminar", methods=["POST"])
@admin_requerido
def admin_eliminar_partido(id_partido):
    partido = obtener_partido(id_partido)
    id_torneo = partido["id_torneo"] if partido else 1
    numero_fecha = partido["numero_fecha"] if partido else 1

    if eliminar_partido(id_partido):
        flash(f"Partido #{id_partido} eliminado exitosamente.", "success")
    else:
        flash("No se pudo eliminar el partido. Los partidos en estado 'jugado' no pueden eliminarse por reglamento.", "danger")

    return redirect(url_for("admin_partidos", id_torneo=id_torneo, numero_fecha=numero_fecha))


# 5. Gestión de Complejos y Canchas
@app.route("/admin/complejos")
@admin_requerido
def admin_complejos():
    complejos = listar_complejos()
    canchas = listar_canchas_completo()
    return render_template("admin_complejos.html", complejos=complejos, canchas=canchas)


@app.route("/admin/complejos/crear", methods=["POST"])
@admin_requerido
def admin_crear_complejo():
    nombre = request.form.get("nombre", "").strip()
    direccion = request.form.get("direccion", "").strip()
    departamento = request.form.get("departamento", "").strip()

    if crear_complejo(nombre, direccion, departamento):
        flash(f"Complejo '{nombre}' registrado exitosamente.", "success")
    else:
        flash("Error al registrar complejo. Verifique que los campos no estén vacíos.", "danger")

    return redirect(url_for("admin_complejos"))


@app.route("/admin/complejos/<int:id_complejo>/eliminar", methods=["POST"])
@admin_requerido
def admin_eliminar_complejo(id_complejo):
    if eliminar_complejo(id_complejo):
        flash("Complejo eliminado exitosamente.", "success")
    else:
        flash("No se pudo eliminar el complejo. Verifique que no posea canchas o partidos asociados.", "danger")

    return redirect(url_for("admin_complejos"))


@app.route("/admin/complejos/<int:id_complejo>/modificar", methods=["POST"])
@admin_requerido
def admin_modificar_complejo(id_complejo):
    nombre = request.form.get("nombre", "").strip()
    direccion = request.form.get("direccion", "").strip()
    departamento = request.form.get("departamento", "").strip()

    if modificar_complejo(id_complejo, nombre, direccion, departamento):
        flash(f"Complejo '{nombre}' modificado exitosamente.", "success")
    else:
        flash("Error al modificar el complejo. Verifique que los campos no estén vacíos.", "danger")

    return redirect(url_for("admin_complejos"))


@app.route("/admin/canchas/crear", methods=["POST"])
@admin_requerido
def admin_crear_cancha():
    nombre_cancha = request.form.get("nombre_cancha", "").strip()
    id_complejo = request.form.get("id_complejo", type=int)
    superficie = request.form.get("superficie", "sintético").strip()
    techada = request.form.get("techada") in ("1", "true", "True", True)

    if crear_cancha(nombre_cancha, id_complejo, superficie, techada):
        flash(f"Cancha '{nombre_cancha}' agregada exitosamente.", "success")
    else:
        flash("Error al crear la cancha. Verifique que el nombre no esté duplicado en ese complejo.", "danger")

    return redirect(url_for("admin_complejos"))


@app.route("/admin/canchas/eliminar", methods=["POST"])
@admin_requerido
def admin_eliminar_cancha():
    nombre_cancha = request.form.get("nombre_cancha", "").strip()
    id_complejo = request.form.get("id_complejo", type=int)

    if eliminar_cancha(nombre_cancha, id_complejo):
        flash("Cancha eliminada exitosamente.", "success")
    else:
        flash("No se pudo eliminar la cancha. Verifique que no tenga partidos asignados.", "danger")

    return redirect(url_for("admin_complejos"))


@app.route("/admin/canchas/modificar", methods=["POST"])
@admin_requerido
def admin_modificar_cancha():
    nombre_cancha = request.form.get("nombre_cancha", "").strip()
    id_complejo = request.form.get("id_complejo", type=int)
    nuevo_nombre = request.form.get("nuevo_nombre", "").strip()
    superficie = request.form.get("superficie", "sintético").strip()
    techada = request.form.get("techada") in ("1", "true", "True", True)

    if modificar_cancha(nombre_cancha, id_complejo, nuevo_nombre, superficie, techada):
        flash(f"Cancha '{nuevo_nombre}' modificada exitosamente.", "success")
    else:
        flash("Error al modificar la cancha. Verifique que el nuevo nombre no esté duplicado.", "danger")

    return redirect(url_for("admin_complejos"))


# 6. Gestión de Usuarios
@app.route("/admin/usuarios")
@admin_requerido
def admin_usuarios():
    return render_template("admin_usuarios.html")


@app.route("/admin/usuarios/crear", methods=["POST"])
@admin_requerido
def admin_crear_usuario():
    correo = request.form.get("correo", "").strip()
    contrasenia = request.form.get("contrasenia", "").strip()
    rol = request.form.get("rol", "").strip()

    if crear_usuario(correo, contrasenia, rol):
        flash(f"Usuario {correo} ({rol}) creado exitosamente.", "success")
        return redirect(url_for("admin_panel"))
    else:
        flash("Error al crear usuario. Verifique formato de correo @ucu.edu.uy y contraseña >= 4 caracteres.", "danger")
        return redirect(url_for("admin_usuarios"))


# -------------------------------------------------------------
# Panel de Planillero y Carga de Actas
# -------------------------------------------------------------

@app.route("/planillero")
@login_requerido
def planillero_panel():
    id_torneo = request.args.get("id_torneo", 1, type=int)
    numero_fecha = request.args.get("numero_fecha", 1, type=int)
    partidos = listar_partidos_por_fecha(id_torneo, numero_fecha)
    for p in partidos:
        p["resultado"] = obtener_resultado_partido(p["id_partido"])
        p["planilla"] = obtener_planilla_partido(p["id_partido"])
    return render_template(
        "planillero_panel.html",
        id_torneo=id_torneo,
        numero_fecha=numero_fecha,
        partidos=partidos
    )


@app.route("/planillero/partido/<int:id_partido>")
@login_requerido
def planillero_acta(id_partido):
    partido = obtener_partido(id_partido)
    if not partido:
        flash("Partido no encontrado.", "danger")
        return redirect(url_for("planillero_panel"))

    equipo_local = obtener_equipo(partido["id_equipo_local"])
    equipo_visitante = obtener_equipo(partido["id_equipo_visitante"])
    partido["equipo_local"] = equipo_local["nombre"] if equipo_local else f"Equipo #{partido['id_equipo_local']}"
    partido["equipo_visitante"] = equipo_visitante["nombre"] if equipo_visitante else f"Equipo #{partido['id_equipo_visitante']}"

    resultado = obtener_resultado_partido(id_partido)
    planilla = obtener_planilla_partido(id_partido)
    goles = obtener_goles_partido(id_partido)
    tarjetas = obtener_tarjetas_partido(id_partido)

    plantel_local = obtener_plantel(partido["id_equipo_local"], partido["id_torneo"])
    plantel_visitante = obtener_plantel(partido["id_equipo_visitante"], partido["id_torneo"])
    cis_en_planilla = {j["ci_jugador"] for j in planilla}

    return render_template(
        "planillero_acta.html",
        partido=partido,
        resultado=resultado,
        planilla=planilla,
        goles=goles,
        tarjetas=tarjetas,
        plantel_local=plantel_local,
        plantel_visitante=plantel_visitante,
        cis_en_planilla=cis_en_planilla
    )


@app.route("/planillero/partido/<int:id_partido>/agregar-jugador", methods=["POST"])
@login_requerido
def planillero_agregar_jugador(id_partido):
    ci_jugador = request.form.get("ci_jugador", type=int)
    id_equipo = request.form.get("id_equipo", type=int)

    if registrar_jugador_en_planilla(id_partido, ci_jugador, id_equipo):
        flash(f"Jugador CI {ci_jugador} inscripto exitosamente en la planilla.", "success")
    else:
        flash("No se pudo inscribir al jugador en la planilla. Verifique que pertenezca al plantel y NO esté suspendido para esta fecha.", "danger")

    return redirect(url_for("planillero_acta", id_partido=id_partido))


@app.route("/planillero/partido/<int:id_partido>/registrar-gol", methods=["POST"])
@login_requerido
def planillero_registrar_gol(id_partido):
    ci_jugador = request.form.get("ci_jugador", type=int)
    minuto = request.form.get("minuto", type=int)
    autogol = request.form.get("autogol") in ("1", "true", "True", True)

    if registrar_gol(id_partido, ci_jugador, minuto, autogol):
        flash("Gol registrado exitosamente.", "success")
    else:
        flash("No se pudo registrar el gol. El jugador debe figurar previamente en la planilla de este partido.", "danger")

    return redirect(url_for("planillero_acta", id_partido=id_partido))


@app.route("/planillero/partido/<int:id_partido>/gol/<int:id_gol>/modificar", methods=["POST"])
@login_requerido
def planillero_modificar_gol(id_partido, id_gol):
    minuto = request.form.get("minuto", type=int)
    autogol = request.form.get("autogol") in ("1", "true", "True", True)

    if modificar_gol(id_gol, minuto, autogol):
        flash("Gol modificado exitosamente.", "success")
    else:
        flash("No se pudo modificar el gol. Verifique los datos o si ya expiró el plazo reglamentario de 48 horas.", "danger")

    return redirect(url_for("planillero_acta", id_partido=id_partido))


@app.route("/planillero/partido/<int:id_partido>/gol/<int:id_gol>/eliminar", methods=["POST"])
@login_requerido
def planillero_eliminar_gol(id_partido, id_gol):
    if eliminar_gol(id_gol, id_partido):
        flash("Gol eliminado exitosamente.", "success")
    else:
        flash("No se pudo eliminar el gol. Verifique si el partido sigue dentro de las 48 horas reglamentarias.", "danger")

    return redirect(url_for("planillero_acta", id_partido=id_partido))


@app.route("/planillero/partido/<int:id_partido>/registrar-tarjeta", methods=["POST"])
@login_requerido
def planillero_registrar_tarjeta(id_partido):
    ci_jugador = request.form.get("ci_jugador", type=int)
    minuto = request.form.get("minuto", type=int)
    color = request.form.get("color", "").strip().lower()

    if registrar_tarjeta(id_partido, ci_jugador, minuto, color):
        flash(f"Tarjeta {color} registrada exitosamente.", "success")
    else:
        flash("No se pudo registrar la tarjeta. El jugador debe figurar previamente en la planilla.", "danger")

    return redirect(url_for("planillero_acta", id_partido=id_partido))


@app.route("/planillero/partido/<int:id_partido>/tarjeta/<int:id_tarjeta>/eliminar", methods=["POST"])
@login_requerido
def planillero_eliminar_tarjeta(id_partido, id_tarjeta):
    if eliminar_tarjeta(id_tarjeta):
        flash("Tarjeta eliminada exitosamente.", "success")
    else:
        flash("No se pudo eliminar la tarjeta. Verifique si el partido sigue dentro de las 48 horas reglamentarias.", "danger")

    return redirect(url_for("planillero_acta", id_partido=id_partido))


@app.route("/planillero/partido/<int:id_partido>/cerrar", methods=["POST"])
@login_requerido
def planillero_cerrar_partido(id_partido):
    if cerrar_partido_como_jugado(id_partido):
        flash("¡Partido cerrado como JUGADO con éxito! Las sanciones automáticas por rojas directas y acumulación de 3 amarillas fueron aplicadas para la fecha siguiente.", "success")
    else:
        flash("No se pudo cerrar el partido como jugado. Recuerde que según el reglamento de la UCU el partido solo puede cerrarse una vez transcurrido el horario del turno.", "danger")

    return redirect(url_for("planillero_acta", id_partido=id_partido))


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Servidor iniciado en http://{host}:{puerto}")
    app.run(debug=True, host=host, port=puerto)
