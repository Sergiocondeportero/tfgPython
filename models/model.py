from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db import Base

# Modelo Usuario
class Usuario(Base):
    __tablename__ = 'Usuarios'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombreUsuario = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    contrasena = Column(String, nullable=False)
    tipoUsuario = Column(String, nullable=False, default='cliente')
    imagen = Column(String, nullable=True)

    # Relación con UsuarioPelicula y UsuarioSerie
    peliculas = relationship('UsuarioPelicula', back_populates='usuario')
    series = relationship('UsuarioSerie', back_populates='usuario')

    def __init__(self, nombreUsuario, email, contrasena, tipoUsuario='cliente', imagen=None):
        self.nombreUsuario = nombreUsuario
        self.email = email
        self.contrasena = contrasena
        self.tipoUsuario = tipoUsuario
        self.imagen = imagen


# Modelo Categoría
class Categoria(Base):
    __tablename__ = 'Categorias'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False, unique=True)


# Modelo Pelicula
class Pelicula(Base):
    __tablename__ = 'Peliculas'
    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    año = Column(Integer, nullable=False)
    director = Column(String, nullable=False)
    duracion = Column(Integer, nullable=False)
    imagen = Column(String, nullable=True)  # Imagen de la película
    trailer = Column(String, nullable=True)  # URL o nombre del archivo del trailer (opcional)
    categoria_id = Column(Integer, ForeignKey('Categorias.id'), nullable=False)

    categoria = relationship('Categoria', backref='peliculas')
    usuarios = relationship('UsuarioPelicula', back_populates='pelicula')

    def __init__(self, titulo, descripcion, año, director, duracion, imagen=None, trailer=None, categoria_id=None):
        self.titulo = titulo
        self.descripcion = descripcion
        self.año = año
        self.director = director
        self.duracion = duracion
        self.imagen = imagen
        self.trailer = trailer
        self.categoria_id = categoria_id


# Modelo UsuarioPelicula (Relación muchos a muchos entre Usuarios y Películas)
class UsuarioPelicula(Base):
    __tablename__ = 'UsuarioPelicula'
    id = Column(Integer, primary_key=True, autoincrement=True)
    usuarioId = Column(Integer, ForeignKey('Usuarios.id'), nullable=False)
    peliculaId = Column(Integer, ForeignKey('Peliculas.id'), nullable=False)
    vista = Column(Boolean, default=False)
    favorita = Column(Boolean, default=False)

    usuario = relationship('Usuario', back_populates='peliculas')
    pelicula = relationship('Pelicula', back_populates='usuarios')


# Modelo UsuarioSerie (Relación muchos a muchos entre Usuarios y Series)
class UsuarioSerie(Base):
    __tablename__ = 'UsuarioSerie'
    id = Column(Integer, primary_key=True, autoincrement=True)
    usuarioId = Column(Integer, ForeignKey('Usuarios.id'), nullable=False)
    serieId = Column(Integer, ForeignKey('Series.id'), nullable=False)
    vista = Column(Boolean, default=False)
    favorita = Column(Boolean, default=False)

    usuario = relationship('Usuario', back_populates='series')
    serie = relationship('Serie', back_populates='usuarios')


# Modelo Serie
class Serie(Base):
    __tablename__ = 'Series'
    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    año = Column(Integer, nullable=False)
    temporadas = Column(Integer, nullable=False)
    capitulos = Column(Integer, nullable=False)
    duracionCapitulo = Column(Integer, nullable=False)
    imagen = Column(String, nullable=True)
    trailer = Column(String, nullable=True)  #
    categoria_id = Column(Integer, ForeignKey('Categorias.id'), nullable=False)

    categoria = relationship('Categoria', backref='series')
    usuarios = relationship('UsuarioSerie', back_populates='serie')

    def __init__(self, titulo, descripcion, año, temporadas, capitulos, duracionCapitulo, imagen=None, trailer=None, categoria_id=None):
        self.titulo = titulo
        self.descripcion = descripcion
        self.año = año
        self.temporadas = temporadas
        self.capitulos = capitulos
        self.duracionCapitulo = duracionCapitulo
        self.imagen = imagen
        self.trailer = trailer
        self.categoria_id = categoria_id
