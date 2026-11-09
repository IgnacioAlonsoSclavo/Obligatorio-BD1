CREATE DATABASE IF NOT EXISTS TorneoInterfacultades CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE TorneoInterfacultades;
SET NAMES utf8mb4;

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
ci_capitan INT UNIQUE,
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

-- ============================================================
-- DATOS MAESTROS Y DE PRUEBA (Segunda entrega / Requisitos UCU)
-- Nota: No se incluyen usuarios de login (se registran en la app)
-- ============================================================

-- 1. Facultades
INSERT INTO facultad (id_facultad, nombre) VALUES
(1, 'Ingeniería y Tecnologías'),
(2, 'Ciencias Empresariales'),
(3, 'Ciencias de la Salud'),
(4, 'Derecho y Humanidades')
ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);

-- 2. Torneo
INSERT INTO torneo (id_torneo, nombre, año, semestre, fecha_inicio, fecha_fin, estado) VALUES
(1, 'Torneo Interfacultades 2026 - Segundo Semestre', 2026, 2, '2026-08-01', '2026-12-15', 'en curso')
ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);

-- 3. Complejos y Canchas
INSERT INTO complejo (id_complejo, nombre, dirección, departamento) VALUES
(1, 'Complejo Deportivo Central UCU', 'Av. 8 de Octubre 2738', 'Montevideo'),
(2, 'Polideportivo San Ignacio', 'Comandante Braga 2715', 'Montevideo')
ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);

INSERT INTO cancha (nombre_cancha, id_complejo, superficie, techada) VALUES
('Cancha 1', 1, 'sintético', true),
('Cancha 2', 1, 'sintético', false),
('Cancha A', 2, 'parquet', true),
('Cancha B', 2, 'sintético', false)
ON DUPLICATE KEY UPDATE superficie=VALUES(superficie);

-- 4. Turnos oficiales (18:00 a 23:00 de 1 hora)
INSERT INTO turno (id_turno, hora_inicio, hora_fin) VALUES
(1, '18:00:00', '19:00:00'),
(2, '19:00:00', '20:00:00'),
(3, '20:00:00', '21:00:00'),
(4, '21:00:00', '22:00:00'),
(5, '22:00:00', '23:00:00')
ON DUPLICATE KEY UPDATE hora_inicio=VALUES(hora_inicio);

-- 5. Jugadores (Estudiantes, Docentes y Funcionarios)
INSERT INTO jugador (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo) VALUES
-- Facultad 1: Ingeniería
(50100011, 'Lucas', 'Rodríguez', 'lucas.rodriguez@correo.ucu.edu.uy', '2002-04-12', 1, 'grado'),
(50100012, 'Martín', 'González', 'martin.gonzalez@correo.ucu.edu.uy', '2001-09-23', 1, 'grado'),
(50100013, 'Rodrigo', 'Silva', 'rodrigo.silva@correo.ucu.edu.uy', '2003-01-15', 1, 'grado'),
(50100014, 'Bruno', 'Pérez', 'bruno.perez@correo.ucu.edu.uy', '1998-11-05', 1, 'posgrado'),
(50100015, 'Diego', 'Fernández', 'diego.fernandez@correo.ucu.edu.uy', '1985-06-30', 1, 'docente'),
(50100016, 'Nicolás', 'López', 'nicolas.lopez@correo.ucu.edu.uy', '1990-03-18', 1, 'funcionario'),
(50100017, 'Mateo', 'Martínez', 'mateo.martinez@correo.ucu.edu.uy', '2004-07-22', 1, 'grado'),

(50200021, 'Santiago', 'Morales', 'santiago.morales@correo.ucu.edu.uy', '2002-08-14', 1, 'grado'),
(50200022, 'Ignacio', 'Suárez', 'ignacio.suarez@correo.ucu.edu.uy', '2001-12-03', 1, 'grado'),
(50200023, 'Joaquín', 'Castro', 'joaquin.castro@correo.ucu.edu.uy', '2003-05-19', 1, 'grado'),
(50200024, 'Gabriel', 'Torres', 'gabriel.torres@correo.ucu.edu.uy', '2000-10-27', 1, 'grado'),
(50200025, 'Matías', 'Benítez', 'matias.benitez@correo.ucu.edu.uy', '1997-04-08', 1, 'posgrado'),
(50200026, 'Alejandro', 'Ramos', 'alejandro.ramos@correo.ucu.edu.uy', '1982-02-11', 1, 'docente'),

-- Facultad 2: Empresariales
(50300031, 'Juan Pablo', 'Díaz', 'juan.diaz@correo.ucu.edu.uy', '2002-03-25', 2, 'grado'),
(50300032, 'Facundo', 'Romero', 'facundo.romero@correo.ucu.edu.uy', '2001-07-17', 2, 'grado'),
(50300033, 'Agustín', 'Acosta', 'agustin.acosta@correo.ucu.edu.uy', '2003-11-29', 2, 'grado'),
(50300034, 'Gonzalo', 'Méndez', 'gonzalo.mendez@correo.ucu.edu.uy', '2000-02-04', 2, 'grado'),
(50300035, 'Sebastián', 'Flores', 'sebastian.flores@correo.ucu.edu.uy', '1996-09-12', 2, 'posgrado'),
(50300036, 'Pablo', 'Herrera', 'pablo.herrera@correo.ucu.edu.uy', '1988-05-21', 2, 'funcionario'),
(50300037, 'Felipe', 'Sosa', 'felipe.sosa@correo.ucu.edu.uy', '2004-01-09', 2, 'grado'),

(50400041, 'Federico', 'Álvarez', 'federico.alvarez@correo.ucu.edu.uy', '2002-06-18', 2, 'grado'),
(50400042, 'Manuel', 'Vargas', 'manuel.vargas@correo.ucu.edu.uy', '2001-10-31', 2, 'grado'),
(50400043, 'Emiliano', 'Medina', 'emiliano.medina@correo.ucu.edu.uy', '2003-04-07', 2, 'grado'),
(50400044, 'Tomás', 'Ríos', 'tomas.rios@correo.ucu.edu.uy', '2000-08-22', 2, 'grado'),
(50400045, 'Andrés', 'Pereira', 'andres.pereira@correo.ucu.edu.uy', '1984-12-15', 2, 'docente'),
(50400046, 'Javier', 'Domínguez', 'javier.dominguez@correo.ucu.edu.uy', '2003-02-28', 2, 'grado'),

-- Facultad 3: Salud
(50500051, 'Christian', 'Olivera', 'christian.olivera@correo.ucu.edu.uy', '2001-05-14', 3, 'grado'),
(50500052, 'Maximiliano', 'Castillo', 'maxi.castillo@correo.ucu.edu.uy', '2002-09-08', 3, 'grado'),
(50500053, 'Renzo', 'Cabrera', 'renzo.cabrera@correo.ucu.edu.uy', '2003-03-21', 3, 'grado'),
(50500054, 'Kevin', 'Vega', 'kevin.vega@correo.ucu.edu.uy', '2000-11-17', 3, 'grado'),
(50500055, 'Leonardo', 'Navarro', 'leonardo.navarro@correo.ucu.edu.uy', '1995-07-03', 3, 'posgrado'),
(50500056, 'Camilo', 'Delgado', 'camilo.delgado@correo.ucu.edu.uy', '1986-10-25', 3, 'docente'),

-- Facultad 4: Derecho
(50600061, 'Guillermo', 'Santana', 'guillermo.santana@correo.ucu.edu.uy', '2002-01-30', 4, 'grado'),
(50600062, 'Franco', 'Rojas', 'franco.rojas@correo.ucu.edu.uy', '2001-08-19', 4, 'grado'),
(50600063, 'Enzo', 'Giménez', 'enzo.gimenez@correo.ucu.edu.uy', '2003-12-10', 4, 'grado'),
(50600064, 'Valentín', 'Núñez', 'valentin.nunez@correo.ucu.edu.uy', '2000-04-05', 4, 'grado'),
(50600065, 'Damián', 'Ruiz', 'damian.ruiz@correo.ucu.edu.uy', '1998-06-16', 4, 'posgrado'),
(50600066, 'Esteban', 'Marín', 'esteban.marin@correo.ucu.edu.uy', '1989-09-02', 4, 'funcionario')
ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);

-- 6. Equipos (6 equipos con capitanes asignados)
INSERT INTO equipo (id_equipo, nombre, id_torneo, id_facultad, ci_capitan) VALUES
(1, 'Sistemas FC', 1, 1, 50100011),
(2, 'Electrónica United', 1, 1, 50200021),
(3, 'Economía FC', 1, 2, 50300031),
(4, 'Marketing Sport', 1, 2, 50400041),
(5, 'Medicina 5', 1, 3, 50500051),
(6, 'Derecho Penal', 1, 4, 50600061)
ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);

-- 7. Planteles (equipo_jugador_torneo)
-- Cada equipo cuenta con entre 6 y 7 jugadores de su misma facultad y <= 2 docentes/funcionarios
INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta) VALUES
-- Sistemas FC
(1, 50100011, 1, 10),
(1, 50100012, 1, 1),
(1, 50100013, 1, 7),
(1, 50100014, 1, 9),
(1, 50100015, 1, 5),
(1, 50100016, 1, 3),
(1, 50100017, 1, 8), -- Jugador sin minutos (no entrará en planillas)

-- Electrónica United
(2, 50200021, 1, 10),
(2, 50200022, 1, 1),
(2, 50200023, 1, 4),
(2, 50200024, 1, 8),
(2, 50200025, 1, 7),
(2, 50200026, 1, 2),

-- Economía FC
(3, 50300031, 1, 10),
(3, 50300032, 1, 1),
(3, 50300033, 1, 5),
(3, 50300034, 1, 9),
(3, 50300035, 1, 11),
(3, 50300036, 1, 3),
(3, 50300037, 1, 6), -- Jugador sin minutos (no entrará en planillas)

-- Marketing Sport
(4, 50400041, 1, 7),
(4, 50400042, 1, 1),
(4, 50400043, 1, 8),
(4, 50400044, 1, 10),
(4, 50400045, 1, 4),
(4, 50400046, 1, 5),

-- Medicina 5
(5, 50500051, 1, 9),
(5, 50500052, 1, 1),
(5, 50500053, 1, 6),
(5, 50500054, 1, 10),
(5, 50500055, 1, 3),
(5, 50500056, 1, 5),

-- Derecho Penal
(6, 50600061, 1, 10),
(6, 50600062, 1, 1),
(6, 50600063, 1, 2),
(6, 50600064, 1, 8),
(6, 50600065, 1, 7),
(6, 50600066, 1, 4)
ON DUPLICATE KEY UPDATE numero_camiseta=VALUES(numero_camiseta);

-- 8. Partidos (3 Fechas Jugadas + Fechas 4 y 5 para pruebas interactivas)
INSERT INTO partido (id_partido, id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, dia, id_turno, nombre_cancha, id_complejo, estado) VALUES
-- Fecha 1 (Disputada)
(1, 1, 1, 1, 4, '2026-10-05', 1, 'Cancha 1', 1, 'jugado'),
(2, 1, 1, 2, 5, '2026-10-05', 2, 'Cancha 1', 1, 'jugado'),
(3, 1, 1, 3, 6, '2026-10-05', 3, 'Cancha 1', 1, 'jugado'),

-- Fecha 2 (Disputada)
(4, 1, 2, 1, 2, '2026-10-12', 1, 'Cancha A', 2, 'jugado'),
(5, 1, 2, 4, 3, '2026-10-12', 2, 'Cancha A', 2, 'jugado'),
(6, 1, 2, 5, 6, '2026-10-12', 3, 'Cancha A', 2, 'jugado'),

-- Fecha 3 (Disputada)
(7, 1, 3, 1, 3, '2026-10-19', 1, 'Cancha 2', 1, 'jugado'),
(8, 1, 3, 2, 6, '2026-10-19', 2, 'Cancha 2', 1, 'jugado'),
(9, 1, 3, 4, 5, '2026-10-19', 3, 'Cancha 2', 1, 'jugado'),

-- Fecha 4 (Para probar en la aplicación)
(10, 1, 4, 1, 5, '2026-11-10', 1, 'Cancha 1', 1, 'programado'),
(11, 1, 4, 2, 3, '2026-11-10', 2, 'Cancha 1', 1, 'programado'),
(12, 1, 4, 4, 6, '2026-11-10', 3, 'Cancha 1', 1, 'postergado'),

-- Fecha 5 (Para probar reprogramación / cancelación)
(13, 1, 5, 1, 6, '2026-11-17', 1, 'Cancha A', 2, 'cancelado'),
(14, 1, 5, 2, 4, '2026-11-17', 2, 'Cancha A', 2, 'programado')
ON DUPLICATE KEY UPDATE estado=VALUES(estado);

-- 9. Planillas de Juego (Partidos 1 al 9 disputados)
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
-- Partido 1: Sistemas (1) vs Marketing (4)
(1, 50100011, 1), (1, 50100012, 1), (1, 50100013, 1), (1, 50100014, 1), (1, 50100015, 1), (1, 50100016, 1),
(1, 50400041, 4), (1, 50400042, 4), (1, 50400043, 4), (1, 50400044, 4), (1, 50400045, 4), (1, 50400046, 4),

-- Partido 2: Electrónica (2) vs Medicina (5)
(2, 50200021, 2), (2, 50200022, 2), (2, 50200023, 2), (2, 50200024, 2), (2, 50200025, 2),
(2, 50500051, 5), (2, 50500052, 5), (2, 50500053, 5), (2, 50500054, 5), (2, 50500055, 5),

-- Partido 3: Economía (3) vs Derecho (6)
(3, 50300031, 3), (3, 50300032, 3), (3, 50300033, 3), (3, 50300034, 3), (3, 50300035, 3), (3, 50300036, 3),
(3, 50600061, 6), (3, 50600062, 6), (3, 50600063, 6), (3, 50600064, 6), (3, 50600065, 6),

-- Partido 4: Sistemas (1) vs Electrónica (2)
(4, 50100011, 1), (4, 50100012, 1), (4, 50100013, 1), (4, 50100014, 1), (4, 50100015, 1),
(4, 50200021, 2), (4, 50200022, 2), (4, 50200023, 2), (4, 50200024, 2), (4, 50200025, 2),

-- Partido 5: Marketing (4) vs Economía (3)
(5, 50400041, 4), (5, 50400042, 4), (5, 50400043, 4), (5, 50400044, 4), (5, 50400045, 4),
(5, 50300031, 3), (5, 50300032, 3), (5, 50300033, 3), (5, 50300034, 3), (5, 50300035, 3),

-- Partido 6: Medicina (5) vs Derecho (6)
(6, 50500051, 5), (6, 50500052, 5), (6, 50500053, 5), (6, 50500054, 5), (6, 50500055, 5),
(6, 50600061, 6), (6, 50600062, 6), (6, 50600064, 6), (6, 50600065, 6), (6, 50600066, 6),

-- Partido 7: Sistemas (1) vs Economía (3)
(7, 50100011, 1), (7, 50100012, 1), (7, 50100013, 1), (7, 50100014, 1), (7, 50100016, 1),
(7, 50300031, 3), (7, 50300032, 3), (7, 50300033, 3), (7, 50300034, 3), (7, 50300036, 3),

-- Partido 8: Electrónica (2) vs Derecho (6)
(8, 50200021, 2), (8, 50200022, 2), (8, 50200023, 2), (8, 50200024, 2), (8, 50200026, 2),
(8, 50600061, 6), (8, 50600062, 6), (8, 50600064, 6), (8, 50600065, 6), (8, 50600066, 6),

-- Partido 9: Marketing (4) vs Medicina (5)
(9, 50400041, 4), (9, 50400042, 4), (9, 50400043, 4), (9, 50400044, 4), (9, 50400046, 4),
(9, 50500051, 5), (9, 50500052, 5), (9, 50500053, 5), (9, 50500054, 5), (9, 50500056, 5)
ON DUPLICATE KEY UPDATE id_equipo=VALUES(id_equipo);

-- 10. Goles Registrados (Resultados oficiales)
INSERT INTO gol (id_gol, id_partido, ci_jugador, minuto, autogol) VALUES
-- Partido 1: Sistemas (3) - Marketing (1)
(1, 1, 50100011, 12, false),
(2, 1, 50100014, 28, false),
(3, 1, 50400042, 35, true),  -- Autogol de Marketing a favor de Sistemas
(4, 1, 50400041, 39, false),

-- Partido 2: Electrónica (2) - Medicina (2)
(5, 2, 50200021, 10, false),
(6, 2, 50500051, 18, false),
(7, 2, 50200025, 26, false),
(8, 2, 50500054, 38, false),

-- Partido 3: Economía (4) - Derecho (2)
(9, 3, 50300031, 5, false),
(10, 3, 50300034, 15, false),
(11, 3, 50600061, 22, false),
(12, 3, 50300031, 29, false),
(13, 3, 50600065, 33, false),
(14, 3, 50300034, 38, false),

-- Partido 4: Sistemas (2) - Electrónica (1)
(15, 4, 50100011, 14, false),
(16, 4, 50200021, 23, false),
(17, 4, 50100014, 36, false),

-- Partido 5: Marketing (0) - Economía (3)
(18, 5, 50300031, 8, false),
(19, 5, 50300034, 21, false),
(20, 5, 50300035, 34, false),

-- Partido 6: Medicina (1) - Derecho (3)
(21, 6, 50600061, 11, false),
(22, 6, 50500051, 24, false),
(23, 6, 50600064, 30, false),
(24, 6, 50600065, 37, false),

-- Partido 7: Sistemas (1) - Economía (1)
(25, 7, 50100011, 19, false),
(26, 7, 50300031, 27, false),

-- Partido 8: Electrónica (3) - Derecho (0)
(27, 8, 50200021, 9, false),
(28, 8, 50200025, 22, false),
(29, 8, 50200024, 35, false),

-- Partido 9: Marketing (2) - Medicina (2)
(30, 9, 50400041, 13, false),
(31, 9, 50500051, 20, false),
(32, 9, 50400044, 31, false),
(33, 9, 50500054, 39, false)
ON DUPLICATE KEY UPDATE minuto=VALUES(minuto);

-- 11. Tarjetas Registradas
INSERT INTO tarjeta (id_tarjeta, id_partido, ci_jugador, minuto, color) VALUES
-- Amarillas y rojas distribuidas
(1, 1, 50100014, 20, 'amarilla'), -- Bruno Pérez (1ra amarilla)
(2, 1, 50400043, 31, 'amarilla'),

(3, 2, 50200023, 14, 'amarilla'),
(4, 2, 50500053, 29, 'amarilla'),

(5, 3, 50600063, 25, 'roja'),     -- Enzo Giménez (Roja directa en fecha 1 -> sancionado en fecha 2)
(6, 3, 50300033, 32, 'amarilla'),

(7, 4, 50100014, 18, 'amarilla'), -- Bruno Pérez (2da amarilla)
(8, 4, 50200024, 29, 'amarilla'),

(9, 5, 50400045, 12, 'amarilla'),
(10, 5, 50300036, 30, 'amarilla'),

(11, 6, 50500056, 17, 'amarilla'),
(12, 6, 50600064, 35, 'amarilla'),

(13, 7, 50100014, 15, 'amarilla'), -- Bruno Pérez (3ra amarilla en fecha 3 -> sancionado en fecha 4)
(14, 7, 50300032, 28, 'amarilla'),

(15, 8, 50200026, 16, 'amarilla'),
(16, 8, 50600066, 34, 'amarilla'),

(17, 9, 50400044, 22, 'amarilla'),
(18, 9, 50500054, 38, 'amarilla')
ON DUPLICATE KEY UPDATE minuto=VALUES(minuto);

-- 12. Sanciones del Tribunal / Automáticas
INSERT INTO sancion_jugador (id_sancion, ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas) VALUES
-- Sanción por roja en Fecha 1 (cumple en Fecha 2)
(1, 50600063, 1, 'roja', 2, 1),

-- Sanción por acumulación de 3 amarillas en Fecha 3 (cumple en Fecha 4)
(2, 50100014, 1, 'acumulación de amarillas', 4, 1),

-- Sanción disciplinaria aplicada por la organización (2 fechas)
(3, 50500056, 1, 'disciplinaria', 3, 2)
ON DUPLICATE KEY UPDATE motivo=VALUES(motivo);

