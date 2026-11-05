# Sistema de Gestión - Torneo Interfacultades de Fútbol 5 (UCU)

Sistema de información web para la gestión de equipos, planteles, partidos, actas de juego, sanciones y reportes estadísticos del Torneo Interfacultades de Fútbol 5 de la Universidad Católica del Uruguay (Base de Datos 1).

---

## 🚀 Opción 1: Ejecución con Docker y Docker Compose (Recomendada)

Permite levantar la aplicación Flask y la base de datos MySQL 8.0 en contenedores aislados sin necesidad de instalar MySQL ni Python en la máquina anfitriona.

### Requisitos previos
* [Docker Desktop](https://www.docker.com/) o Docker Engine con Docker Compose v2+.

### Pasos para iniciar
1. Clonar el repositorio y situarse en la raíz:
   ```bash
   git clone https://github.com/IgnacioAlonsoSclavo/Obligatorio-BD1.git
   cd Obligatorio-BD1
   ```
2. Construir e iniciar los servicios:
   ```bash
   docker compose up --build
   ```
3. La base de datos ejecutará automáticamente el archivo `script.sql` para inicializar el esquema y permisos.
4. Abrir el navegador en:
   **[http://localhost:5000](http://localhost:5000)**

Para detener los contenedores:
```bash
docker compose down
```
*(Si se desea reiniciar la base de datos desde cero eliminando los datos previos, agregar `-v`: `docker compose down -v`)*.

---

## 💻 Opción 2: Ejecución Local (sin Docker)

### Requisitos previos
* Python 3.10+
* MySQL Server 8.0+ en ejecución en el puerto 3306

### Pasos para iniciar
1. **Configurar la base de datos MySQL**:
   Ejecutar el script de base de datos en su servidor MySQL local:
   ```bash
   mysql -u root -p < script.sql
   ```
   *(La contraseña de root por defecto esperada es `rootpassword`. Si utiliza otra, puede definir la variable de entorno `DB_PASSWORD`)*.

2. **Crear y activar el entorno virtual de Python**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate    # En Linux/macOS
   # .venv\Scripts\activate     # En Windows
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**:
   ```bash
   python main.py
   ```

5. Abrir el navegador en **[http://localhost:5000](http://localhost:5000)**.

---

## 🔑 Credenciales y Usuarios del Sistema

### Base de Datos MySQL
* **Host**: `localhost` (o `db` dentro de la red Docker)
* **Puerto**: `3306` (en modo local) o `3307` (mapeado hacia tu máquina en Docker para no colisionar con un MySQL local)
* **Root Password**: `rootpassword`
* **Base de datos**: `TorneoInterfacultades`
* **Usuario Admin**: `admin` / `AdminUCU`
* **Usuario Planillero**: `planillero` / `PlanilleroPass2026!`

### Aplicación Web
Al ingresar por primera vez a la aplicación sin administradores registrados, el sistema redirige automáticamente a la pantalla de **Registro Inicial** (`/registro-inicial`) para dar de alta el usuario administrador principal (correo `@ucu.edu.uy` y contraseña mínima de 4 caracteres).
