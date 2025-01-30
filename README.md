# 🎬 PeliculasySeriesya - Plataforma de Estadísticas de Series y Películas 🎧  

## 📚 Descripción  
 PeliculasySeriesya es una aplicación web desarrollada con Flask y SQLAlchemy que permite a los usuarios registrar y visualizar estadísticas sobre las películas y series que han visto.  

🔹 Registro y autenticación de usuarios  
🔹 Análisis del tiempo total invertido en películas y series  
🔹 Gráficos interactivos de comparación  
🔹 Base de datos relacional con SQLAlchemy  

---

## ⚙️ Instalación y Configuración  

### 1⃣ Clonar el repositorio  
Para empezar, clona el repositorio en tu máquina local:  

```bash
git clone https://github.com/Sergiocondeportero/tfgPython.git
cd tfgPython
```

### 2⃣ Crear un entorno virtual (opcional, recomendado)  
Para evitar conflictos entre paquetes, se recomienda usar un entorno virtual:

```bash
# En Windows
python -m venv .venv
.venv\Scripts\activate

# En macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```
Si usas PowerShell en Windows, activa el entorno con:
```powershell
.venv\Scripts\Activate.ps1
```

### 3⃣ Instalar dependencias  
Una vez dentro del entorno virtual, instala las dependencias necesarias:

```bash
pip install -r requirements.txt
```

### 4⃣ Configurar la base de datos  
El proyecto usa una base de datos MySQL o PostgreSQL. Asegúrate de tener una base de datos creada y configura la conexión en `db.py`.

#### 🔹 **Configurar MySQL**  
Si usas MySQL, instala el servidor y crea una base de datos:

```sql
CREATE DATABASE tfg_database;
CREATE USER 'usuario'@'localhost' IDENTIFIED BY 'contraseña';
GRANT ALL PRIVILEGES ON tfg_database.* TO 'usuario'@'localhost';
FLUSH PRIVILEGES;
```
Modifica `db.py` con tus credenciales:
```python
DATABASE_URI = 'mysql+pymysql://usuario:contraseña@localhost/tfg_database'
```

#### 🔹 **Configurar PostgreSQL**  
Si prefieres PostgreSQL, instala el servidor y crea la base de datos:

```sql
CREATE DATABASE tfg_database;
CREATE USER usuario WITH PASSWORD 'contraseña';
ALTER ROLE usuario SET client_encoding TO 'utf8';
ALTER ROLE usuario SET default_transaction_isolation TO 'read committed';
ALTER ROLE usuario SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE tfg_database TO usuario;
```
Modifica `db.py`:
```python
DATABASE_URI = 'postgresql://usuario:contraseña@localhost/tfg_database'
```

Después, ejecuta la configuración de la base de datos:
```bash
python db.py
```
Esto creará las tablas necesarias en la base de datos.

### 5⃣ Configurar variables de entorno  
Crea un archivo `.env` en la raíz del proyecto y añade:

```env
FLASK_APP=main.py
FLASK_ENV=development
DATABASE_URL=mysql+pymysql://usuario:contraseña@localhost/tfg_database
SECRET_KEY=tu_clave_secreta
```
Si usas PostgreSQL, cambia `DATABASE_URL` en `.env` al formato correcto.

### 6⃣ Ejecutar la aplicación  
Finalmente, inicia el servidor Flask:

```bash
python main.py
```
El servidor estará disponible en `http://127.0.0.1:5000/`

---

## 📦 Dependencias  
El proyecto utiliza las siguientes tecnologías y paquetes:

- `Flask` - Framework web en Python  
- `Flask-SQLAlchemy` - ORM para gestionar la base de datos  
- `Jinja2` - Motor de plantillas para la interfaz web  
- `Matplotlib` - Generación de gráficos  
- `pymysql` - Conector para bases de datos MySQL  
- `python-dotenv` - Gestión de variables de entorno  

Para instalar todas las dependencias, ejecuta:
```bash
pip install -r requirements.txt
```

---

## 🚀 Uso del Proyecto  
1⃣ **Registrar usuarios** y guardar series/películas vistas  
2⃣ **Ver estadísticas personalizadas** con gráficos  
3⃣ **Comparar datos con otros usuarios**  
4⃣ **Filtrar contenido según género y duración**  

---

## 🛠️ Desarrollo y Contribución  
Si deseas contribuir a este proyecto:  

1⃣ Haz un fork del repositorio  
2⃣ Crea una nueva rama para tus cambios  
3⃣ Realiza un commit y haz push  
4⃣ Abre un Pull Request  

```bash
git checkout -b mi-nueva-funcionalidad
git commit -m "Añadida nueva funcionalidad"
git push origin mi-nueva-funcionalidad
```

---

## 📄 Licencia  
Este proyecto está bajo la licencia MIT. Puedes ver más detalles en el archivo `LICENSE`.

---

## 📞 Contacto  
👤 **Sergio Conde**  
📧 Email: [sergiocondecp@gmail.com](mailto:sergiocondecp@gmail.com)  
🔗 GitHub: [github.com/Sergiocondeportero](https://github.com/Sergiocondeportero)  