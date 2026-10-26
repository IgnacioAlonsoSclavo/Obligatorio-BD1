CREATE DATABASE IF NOT EXISTS TorneoInterfacultades;
USE TorneoInterfacultades;

-- Tabla login:
CREATE TABLE login (
correo VARCHAR(255) PRIMARY KEY NOT NULL,
contraseña VARCHAR(255) NOT NULL,
rol ENUM('Administrador' , ' Planillero' )
);

CREATE TABLE facultad (
id_facultad INT PRIMARY KEY NOT NULL,
nombre VARCHAR(255) NOT NULL
);

CREATE TABLE jugador (
ci INT PRIMARY KEY NOT NULL,
nombre VARCHAR(255) NOT NULL,
apellido VARCHAR(255) NOT NULL,
email VARCHAR(255) NOT NULL UNIQUE,
fecha_nacimiento DATE,
id_facultad INT,
tipo ENUM ('grado' , 'posgrado' , 'docente' , 'funcionario' ),
FOREIGN KEY (id_facultad) REFERENCES facultad(id_facultad)
);

CREATE TABLE torneo (
id_torneo INT PRIMARY KEY NOT NULL,
nombre VARCHAR(255) NOT NULL,
año YEAR,
semestre INT,
fecha_inicio DATE,
fecha_fin DATE,
estado ENUM ('inscripción' , 'en curso' , 'finalizado')
);

CREATE TABLE equipo (
id_equipo INT PRIMARY KEY NOT NULL,
nombre VARCHAR(255) NOT NULL,
id_torneo INT,
id_facultad INT,
ci_capitan INT,
FOREIGN KEY (id_torneo) REFERENCES torneo(id_torneo),
FOREIGN KEY (id_facultad) REFERENCES facultad(id_facultad),
FOREIGN KEY (ci_capitan) REFERENCES jugador(ci)
);

CREATE TABLE equipo_jugador_torneo (
id_equipo INT NOT NULL,
ci_jugador INT NOT NULL,
id_torneo INT NOT NULL,
numero_camiseta INT,
UNIQUE (ci_jugador, id_torneo),
PRIMARY KEY (id_equipo, ci_jugador),
FOREIGN KEY (id_equipo) REFERENCES equipo(id_equipo),
FOREIGN KEY (ci_jugador) REFERENCES jugador(ci),
FOREIGN KEY (id_torneo) REFERENCES torneo(id_torneo)
);

CREATE TABLE complejo (
id_complejo INT PRIMARY KEY NOT NULL,
nombre varChar(255) NOT NULL,
dirección varChar(255) NOT NULL,
departamento varChar(255) NOT NULL
);

CREATE TABLE cancha (
nombre_cancha VARCHAR(255) PRIMARY KEY NOT NULL,
id_complejo INT,
superficie ENUM ('sintético' , 'parquet' ),
techada BOOLEAN,
FOREIGN KEY (id_complejo) REFERENCES complejo(id_complejo)
);

CREATE TABLE turno (
id_turno INT PRIMARY KEY NOT NULL,
hora_inicio TIME,
hora_fin TIME
);

CREATE TABLE partido (
id_partido INT PRIMARY KEY NOT NULL,
id_torneo INT,
numero_fecha INT,
id_equipo_local INT,
id_equipo_visitante INT,
dia DATETIME,
id_turno INT,
nombre_cancha VARCHAR(255),
id_complejo INT,
estado ENUM ('programado' , 'jugado' , 'postergado' , 'cancelado' ),
FOREIGN KEY (id_torneo) REFERENCES torneo(id_torneo),
FOREIGN KEY (id_equipo_local) REFERENCES equipo(id_equipo),
FOREIGN KEY (id_equipo_visitante) REFERENCES equipo(id_equipo),
FOREIGN KEY (id_turno) REFERENCES turno(id_turno),
FOREIGN KEY (nombre_cancha) REFERENCES cancha(nombre_cancha),
FOREIGN KEY (id_complejo) REFERENCES complejo(id_complejo)
);

CREATE TABLE planilla_partido (
id_partido INT PRIMARY KEY NOT NULL,
ci_jugador INT,
id_equipo INT,
FOREIGN KEY (ci_jugador) REFERENCES jugador(ci),
FOREIGN KEY (id_equipo) REFERENCES equipo(id_equipo)
);

CREATE TABLE gol (
id_gol INT PRIMARY KEY NOT NULL,
id_partido INT,
ci_jugador INT,
minuto INT,
autogol BOOLEAN,
FOREIGN KEY (id_partido) REFERENCES partido(id_partido),
FOREIGN KEY (ci_jugador) REFERENCES jugador(ci)
);

CREATE TABLE tarjeta (
id_tarjeta INT PRIMARY KEY NOT NULL,
id_partido INT,
ci_jugador INT,
minuto INT,
color ENUM ('amarilla' , 'roja' ),
FOREIGN KEY (id_partido) REFERENCES partido(id_partido),
FOREIGN KEY (ci_jugador) REFERENCES jugador(ci)
);

CREATE TABLE sancion_jugador (
id_sancion INT PRIMARY KEY NOT NULL,
ci_jugador INT,
id_torneo INT,
motivo ENUM ('roja' , 'acumulación de amarillas' , 'disciplinaria' ),
numero_fecha_inicio INT,
cantidad_fechas INT,
FOREIGN KEY (ci_jugador) REFERENCES jugador(ci),
FOREIGN KEY (id_torneo) REFERENCES torneo(id_torneo)
);


-- Usuario Admin:
CREATE USER IF NOT EXISTS 'admin'@'%' IDENTIFIED BY 'AdminUCU';
GRANT ALL PRIVILEGES ON TorneoInterfacultades.* TO 'admin'@'%';

-- Usuario Planillero:
CREATE USER IF NOT EXISTS 'planillero'@'%' IDENTIFIED BY 'PlanilleroPass2026!';

-- Permiso para autenticarse consultando la tabla de login
GRANT SELECT ON TorneoInterfacultades.login TO 'planillero'@'%';

-- Solo lectura de las tablas maestras y de consulta
GRANT SELECT ON TorneoInterfacultades.torneo TO 'planillero'@'%';
GRANT SELECT ON TorneoInterfacultades.facultad TO 'planillero'@'%';
GRANT SELECT ON TorneoInterfacultades.equipo TO 'planillero'@'%';
GRANT SELECT ON TorneoInterfacultades.jugador TO 'planillero'@'%';
GRANT SELECT ON TorneoInterfacultades.equipo_jugador_torneo TO 'planillero'@'%';
GRANT SELECT ON TorneoInterfacultades.cancha TO 'planillero'@'%';
GRANT SELECT ON TorneoInterfacultades.complejo TO 'planillero'@'%';
GRANT SELECT ON TorneoInterfacultades.turno TO 'planillero'@'%';
GRANT SELECT ON TorneoInterfacultades.sancion_jugador TO 'planillero'@'%';

-- Permisos de carga y edición en planillas, goles, tarjetas y resultado de partido
GRANT SELECT, UPDATE ON TorneoInterfacultades.partido TO 'planillero'@'%';
GRANT SELECT, INSERT, UPDATE ON TorneoInterfacultades.planilla_partido TO 'planillero'@'%';
GRANT SELECT, INSERT, UPDATE ON TorneoInterfacultades.gol TO 'planillero'@'%';
GRANT SELECT, INSERT, UPDATE ON TorneoInterfacultades.tarjeta TO 'planillero'@'%';

FLUSH PRIVILEGES;
