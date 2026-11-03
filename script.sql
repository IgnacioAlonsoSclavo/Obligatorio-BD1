CREATE DATABASE IF NOT EXISTS TorneoInterfacultades;
USE TorneoInterfacultades;

-- Tabla login:
CREATE TABLE login (
correo VARCHAR(255) PRIMARY KEY,
contraseña VARCHAR(255) NOT NULL,
rol ENUM('admin' , 'planillero' )
);

CREATE TABLE facultad (
id_facultad INT AUTO_INCREMENT PRIMARY KEY,
nombre VARCHAR(255) NOT NULL
);

CREATE TABLE jugador (
ci INT PRIMARY KEY,
nombre VARCHAR(255) NOT NULL,
apellido VARCHAR(255) NOT NULL,
email VARCHAR(255) NOT NULL UNIQUE,
fecha_nacimiento DATE,
id_facultad INT,
tipo ENUM ('grado' , 'posgrado' , 'docente' , 'funcionario' ),
FOREIGN KEY (id_facultad) REFERENCES facultad(id_facultad)
);

CREATE TABLE torneo (
id_torneo INT AUTO_INCREMENT PRIMARY KEY,
nombre VARCHAR(255) NOT NULL,
año YEAR,
semestre INT,
fecha_inicio DATE,
fecha_fin DATE,
estado ENUM ('inscripción' , 'en curso' , 'finalizado'),
CHECK (fecha_fin >= fecha_inicio),
CHECK (semestre IN (1, 2))
);

CREATE TABLE equipo (
id_equipo INT AUTO_INCREMENT PRIMARY KEY,
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
PRIMARY KEY (id_equipo, ci_jugador, id_torneo),
FOREIGN KEY (id_equipo) REFERENCES equipo(id_equipo),
FOREIGN KEY (ci_jugador) REFERENCES jugador(ci),
FOREIGN KEY (id_torneo) REFERENCES torneo(id_torneo),
UNIQUE (ci_jugador, id_torneo)
);

CREATE TABLE complejo (
id_complejo INT AUTO_INCREMENT PRIMARY KEY,
nombre varChar(255) NOT NULL,
dirección varChar(255) NOT NULL,
departamento varChar(255) NOT NULL
);

CREATE TABLE cancha (
nombre_cancha VARCHAR(255) NOT NULL,
id_complejo INT,
superficie ENUM ('sintético' , 'parquet' ),
techada BOOLEAN,
PRIMARY KEY (nombre_cancha, id_complejo),
FOREIGN KEY (id_complejo) REFERENCES complejo(id_complejo)
);

CREATE TABLE turno (
id_turno INT AUTO_INCREMENT PRIMARY KEY,
hora_inicio TIME,
hora_fin TIME,
CHECK (hora_fin > hora_inicio)
);

CREATE TABLE partido (
id_partido INT AUTO_INCREMENT PRIMARY KEY,
id_torneo INT,
numero_fecha INT,
id_equipo_local INT,
id_equipo_visitante INT,
dia DATE,
id_turno INT,
nombre_cancha VARCHAR(255),
id_complejo INT,
estado ENUM ('programado' , 'jugado' , 'postergado' , 'cancelado' ),
FOREIGN KEY (id_torneo) REFERENCES torneo(id_torneo),
FOREIGN KEY (id_equipo_local) REFERENCES equipo(id_equipo),
FOREIGN KEY (id_equipo_visitante) REFERENCES equipo(id_equipo),
FOREIGN KEY (id_turno) REFERENCES turno(id_turno),
FOREIGN KEY (nombre_cancha, id_complejo) REFERENCES cancha(nombre_cancha, id_complejo),
CHECK (numero_fecha >= 1)
);

CREATE TABLE planilla_partido (
id_partido INT NOT NULL,
ci_jugador INT NOT NULL,
id_equipo INT NOT NULL,
PRIMARY KEY (id_partido, ci_jugador),
FOREIGN KEY (id_partido) REFERENCES partido(id_partido),
FOREIGN KEY (ci_jugador) REFERENCES jugador(ci),
FOREIGN KEY (id_equipo) REFERENCES equipo(id_equipo)
);

CREATE TABLE gol (
id_gol INT AUTO_INCREMENT PRIMARY KEY,
id_partido INT,
ci_jugador INT,
minuto INT,
autogol BOOLEAN,
CHECK (minuto >= 0),
FOREIGN KEY (id_partido) REFERENCES partido(id_partido),
FOREIGN KEY (ci_jugador) REFERENCES jugador(ci)
);

CREATE TABLE tarjeta (
id_tarjeta INT AUTO_INCREMENT PRIMARY KEY,
id_partido INT,
ci_jugador INT,
minuto INT,
color ENUM ('amarilla' , 'roja' ),
FOREIGN KEY (id_partido) REFERENCES partido(id_partido),
FOREIGN KEY (ci_jugador) REFERENCES jugador(ci),
CHECK (minuto >= 0)
);

CREATE TABLE sancion_jugador (
id_sancion INT AUTO_INCREMENT PRIMARY KEY,
ci_jugador INT,
id_torneo INT,
motivo ENUM ('roja' , 'acumulación de amarillas' , 'disciplinaria' ),
numero_fecha_inicio INT,
cantidad_fechas INT,
FOREIGN KEY (ci_jugador) REFERENCES jugador(ci),
FOREIGN KEY (id_torneo) REFERENCES torneo(id_torneo),
CHECK (numero_fecha_inicio >= 1),
CHECK (cantidad_fechas >= 1)
);


CREATE OR REPLACE VIEW goles_por_partido AS
SELECT p.id_partido,
       p.id_equipo_local,
       p.id_equipo_visitante,
       SUM(IF((ejt.id_equipo = p.id_equipo_local AND NOT g.autogol) OR (ejt.id_equipo = p.id_equipo_visitante AND g.autogol), 1, 0)) AS goles_local,
       SUM(IF((ejt.id_equipo = p.id_equipo_visitante AND NOT g.autogol) OR (ejt.id_equipo = p.id_equipo_local AND g.autogol), 1, 0)) AS goles_visitante
FROM partido p
LEFT JOIN gol g ON g.id_partido = p.id_partido
LEFT JOIN equipo_jugador_torneo ejt ON ejt.ci_jugador = g.ci_jugador AND ejt.id_equipo IN (p.id_equipo_local, p.id_equipo_visitante)
WHERE p.estado = 'jugado'
GROUP BY p.id_partido, p.id_equipo_local, p.id_equipo_visitante;

CREATE OR REPLACE VIEW resultados_equipo AS
SELECT id_equipo,
       SUM(ganado) AS ganados,
       SUM(empatado) AS empatados,
       SUM(perdido) AS perdidos,
       SUM(IF(ganado, 3, IF(empatado, 1, 0))) AS puntos,
       SUM(ganado + empatado + perdido) AS partidos_jugados
FROM (
    SELECT id_equipo_local AS id_equipo,
           IF(goles_local > goles_visitante, 1, 0) AS ganado,
           IF(goles_local = goles_visitante, 1, 0) AS empatado,
           IF(goles_local < goles_visitante, 1, 0) AS perdido
    FROM goles_por_partido
    UNION ALL
    SELECT id_equipo_visitante AS id_equipo,
           IF(goles_visitante > goles_local, 1, 0) AS ganado,
           IF(goles_visitante = goles_local, 1, 0) AS empatado,
           IF(goles_visitante < goles_local, 1, 0) AS perdido
    FROM goles_por_partido
) x
GROUP BY id_equipo;

CREATE OR REPLACE VIEW goles_equipo AS
SELECT id_equipo,
       SUM(goles_a_favor) AS goles_a_favor,
       SUM(goles_en_contra) AS goles_en_contra,
       SUM(goles_a_favor - goles_en_contra) AS diferencia_de_goles
FROM (
    SELECT id_equipo_local AS id_equipo,
           SUM(goles_local) AS goles_a_favor,
           SUM(goles_visitante) AS goles_en_contra
    FROM goles_por_partido
    GROUP BY id_equipo
    UNION ALL
    SELECT id_equipo_visitante AS id_equipo,
           SUM(goles_visitante) AS goles_a_favor,
           SUM(goles_local) AS goles_en_contra
    FROM goles_por_partido
    GROUP BY id_equipo
) x
GROUP BY id_equipo;



CREATE USER IF NOT EXISTS 'admin'@'%' IDENTIFIED BY 'AdminUCU';
GRANT ALL PRIVILEGES ON TorneoInterfacultades.* TO 'admin'@'%';


CREATE USER IF NOT EXISTS 'planillero'@'%' IDENTIFIED BY 'PlanilleroPass2026!';

GRANT SELECT ON TorneoInterfacultades.login TO 'planillero'@'%';

GRANT SELECT ON TorneoInterfacultades.torneo TO 'planillero'@'%';
GRANT SELECT ON TorneoInterfacultades.facultad TO 'planillero'@'%';
GRANT SELECT ON TorneoInterfacultades.equipo TO 'planillero'@'%';
GRANT SELECT ON TorneoInterfacultades.jugador TO 'planillero'@'%';
GRANT SELECT ON TorneoInterfacultades.equipo_jugador_torneo TO 'planillero'@'%';
GRANT SELECT ON TorneoInterfacultades.cancha TO 'planillero'@'%';
GRANT SELECT ON TorneoInterfacultades.complejo TO 'planillero'@'%';
GRANT SELECT ON TorneoInterfacultades.turno TO 'planillero'@'%';
GRANT SELECT ON TorneoInterfacultades.sancion_jugador TO 'planillero'@'%';
GRANT SELECT ON TorneoInterfacultades.goles_por_partido TO 'planillero'@'%';
GRANT SELECT ON TorneoInterfacultades.resultados_equipo TO 'planillero'@'%';
GRANT SELECT ON TorneoInterfacultades.goles_equipo TO 'planillero'@'%';

GRANT SELECT, UPDATE ON TorneoInterfacultades.partido TO 'planillero'@'%';
GRANT SELECT, INSERT, UPDATE ON TorneoInterfacultades.planilla_partido TO 'planillero'@'%';
GRANT SELECT, INSERT, UPDATE ON TorneoInterfacultades.gol TO 'planillero'@'%';
GRANT SELECT, INSERT, UPDATE ON TorneoInterfacultades.tarjeta TO 'planillero'@'%';

FLUSH PRIVILEGES;
