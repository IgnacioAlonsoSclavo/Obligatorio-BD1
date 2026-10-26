CREATE DATABASE IF NOT EXISTS TorneoInterfacultades;
USE TorneoInterfacultades;

-- Tabla login:
CREATE TABLE IF NOT EXISTS login (
    correo VARCHAR(100) PRIMARY KEY,
    contraseña VARCHAR(255) NOT NULL,
    rol ENUM('administrador', 'planillero') NOT NULL
);

hola prueba

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
