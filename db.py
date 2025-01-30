# db.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuración de la base de datos (SQLite en este caso)
DATABASE_URL = "sqlite:///database/peliculas.db"  # Ruta de la base de datos

# Crear el motor de la base de datos
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Crear la base para las clases (Declarative Base)
Base = declarative_base()

# Crear la clase de sesión
Session = sessionmaker(bind=engine)

# Función para obtener una sesión de base de datos
def get_session():
    return Session()

# Función para crear las tablas cuando inicie la base de datos
def create_tables():
    Base.metadata.create_all(bind=engine)

# Función para eliminar las tablas de la base de datos (útil en desarrollo)
def drop_tables():
    Base.metadata.drop_all(bind=engine)
