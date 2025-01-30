import base64
import io
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from matplotlib import pyplot as plt
from six import BytesIO
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.functions import current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models.model import Usuario, Pelicula, Serie, Categoria, UsuarioPelicula, UsuarioSerie
import db

app = Flask(__name__)

app.secret_key = "supersecretkey"

# Configuración de Flask para subir archivos
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Crear las tablas de la base de datos cuando inicie la aplicación
db.create_tables()

# Función para verificar las extensiones permitidas
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def crear_categorias_iniciales():
    categorias = ["Acción", "Comedia", "Drama", "Ciencia ficción", "Aventura", "Terror", "Romance", "Documental"]

    # Crear la sesión de base de datos
    session_db = db.get_session()

    # Verificar si las categorías ya existen
    for categoria in categorias:
        categoria_existente = session_db.query(Categoria).filter(Categoria.nombre == categoria).first()
        if not categoria_existente:
            nueva_categoria = Categoria(nombre=categoria)
            session_db.add(nueva_categoria)


    session_db.commit()
    session_db.close()


# Llamar a la función para crear las categorías cuando la aplicación inicie
with app.app_context():
    crear_categorias_iniciales()
# Ruta de inicio
@app.route("/")
def home():
    # Crear la sesión
    session = db.Session()


    peliculas = session.query(Pelicula).all()
    series = session.query(Serie).all()



    return render_template("index.html", peliculas=peliculas, series=series)

# Ruta de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre_usuario = request.form['username']
        password = request.form['password']

        session_db = db.Session()
        usuario = session_db.query(Usuario).filter_by(nombreUsuario=nombre_usuario).first()

        if usuario and check_password_hash(usuario.contrasena, password):

            session['user_id'] = usuario.id
            session['username'] = usuario.nombreUsuario
            session['tipo_usuario'] = usuario.tipoUsuario


            imagen = usuario.imagen if usuario.imagen else 'uploads/default.jpg'
            imagen = imagen.replace("\\", "/")

            session['imagen'] = imagen  # Almacenar la ruta corregida
            flash('¡Inicio de sesión exitoso!', 'success')

            session_db.close()
            return redirect(url_for('home'))
        else:
            flash('Credenciales incorrectas, por favor intenta nuevamente.', 'danger')
            session_db.close()
            return redirect(url_for('login'))

    return render_template('login.html')

# Ruta de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre_usuario = request.form['nombreUsuario']
        email = request.form['email']
        contrasena = request.form['contrasena']
        tipo_usuario = request.form['tipo_usuario']


        session_db = db.Session()
        usuario_existente = session_db.query(Usuario).filter_by(email=email).first()
        if usuario_existente:
            flash("El correo electrónico ya está registrado.", "danger")
            session_db.close()
            return redirect(url_for('register'))

        # Cifrar la contraseña
        contrasena_cifrada = generate_password_hash(contrasena)

        # Manejar la foto de perfil (opcional)
        imagen = 'uploads/default.jpg'
        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                imagen_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(imagen_path)
                imagen = os.path.join('uploads', filename)

        # Crear el nuevo usuario
        nuevo_usuario = Usuario(
            nombreUsuario=nombre_usuario,
            email=email,
            contrasena=contrasena_cifrada,
            tipoUsuario=tipo_usuario or "cliente",
            imagen=imagen
        )

        session_db.add(nuevo_usuario)
        session_db.commit()
        session_db.close()

        flash("Usuario registrado exitosamente", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# Ruta de perfil del usuario
@app.route('/perfil')
def perfil():
    if 'user_id' not in session:
        flash('Por favor inicia sesión primero', 'danger')
        return redirect(url_for('login'))

    usuario = db.Session().query(Usuario).filter_by(id=session['user_id']).first()


    imagen = usuario.imagen.replace("\\", "/")


    if 'username' not in session:
        session['username'] = usuario.nombreUsuario

    return render_template('perfil.html', usuario=usuario, imagen=imagen)

# Ruta de editar perfil
@app.route('/editarPerfil', methods=['GET', 'POST'])
def editar_perfil():
    if 'user_id' not in session:
        flash("Debes iniciar sesión para acceder a esta página", "danger")
        return redirect(url_for("login"))

    session_db = db.Session()
    usuario = session_db.query(Usuario).get(session["user_id"])

    if not usuario:
        flash("Usuario no encontrado", "danger")
        session_db.close()
        return redirect(url_for("home"))

    if request.method == 'POST':
        nuevo_nombre = request.form['nombreUsuario']
        nuevo_email = request.form['email']
        nueva_contrasena = request.form['password']

        # Actualizamos los datos en la base de datos
        usuario.nombreUsuario = nuevo_nombre
        usuario.email = nuevo_email

        if nueva_contrasena:
            usuario.contrasena = generate_password_hash(nueva_contrasena)


        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                imagen_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(imagen_path)

                usuario.imagen = os.path.join('uploads', filename)
                session['imagen'] = usuario.imagen

        try:
            session_db.commit()
            session.clear()


            session['user_id'] = usuario.id
            session['username'] = usuario.nombreUsuario
            session['imagen'] = usuario.imagen if usuario.imagen else 'uploads/default.jpg'

            flash("Perfil actualizado con éxito", "success")

        except Exception as e:
            session_db.rollback()
            flash(f"Hubo un error al actualizar el perfil: {e}", "danger")

        session_db.close()


        return redirect(url_for("perfil", _anchor=""))

    session_db.close()
    return render_template('editarUsuario.html', usuario=usuario)



# Ruta para cambiar la contraseña
@app.route('/cambiarContrasena', methods=['GET', 'POST'])
def cambiar_contrasena():
    if request.method == 'POST':
        contrasena_actual = request.form['contrasena_actual']
        nueva_contrasena = request.form['nueva_contrasena']


        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor inicia sesión primero', 'danger')
            return redirect(url_for('login'))


        session_db = db.Session()
        usuario = session_db.query(Usuario).get(user_id)


        if usuario and check_password_hash(usuario.contrasena, contrasena_actual):

            nueva_contrasena_hash = generate_password_hash(nueva_contrasena)
            usuario.contrasena = nueva_contrasena_hash

            session_db.commit()
            flash('Contraseña cambiada con éxito', 'success')
            session_db.close()
            return redirect(url_for('perfil'))
        else:
            flash('La contraseña actual no es correcta', 'danger')
            session_db.close()
            return render_template('cambiarContrasena.html')

    return render_template('cambiarContrasena.html')
# Ruta de logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión exitosamente', 'success')
    return redirect(url_for('home'))
#Ruta listar usuarios
@app.route("/usuarios")
def listar_usuarios():
    if session.get("tipo_usuario") != "administrador":
        flash("No tienes permiso para acceder a esta página", "danger")
        return redirect(url_for("home"))

    session_db = db.Session()
    try:
        usuarios = session_db.query(Usuario).all()  # Obtener todos los usuarios
    except Exception as e:
        flash("Error al obtener la lista de usuarios: " + str(e), "danger")
        usuarios = []
    finally:
        session_db.close()

    return render_template("usuarios.html", usuarios=usuarios)
# Ruta para crear un usuario
@app.route('/crearUsuario', methods=['GET', 'POST'])
def crearUsuario():
    if request.method == 'POST':
        nombre_usuario = request.form['nombreUsuario']
        email = request.form['email']
        contrasena = request.form['contrasena']
        tipo_usuario = request.form['tipo_usuario']


        session_db = db.Session()
        usuario_existente = session_db.query(Usuario).filter_by(email=email).first()
        if usuario_existente:
            flash("El correo electrónico ya está registrado.", "danger")
            session_db.close()
            return redirect(url_for('crearUsuario'))


        contrasena_cifrada = generate_password_hash(contrasena)


        imagen = 'uploads/default.jpg'
        if 'fotoPerfil' in request.files:
            file = request.files['fotoPerfil']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                imagen_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(imagen_path)
                imagen = os.path.join('uploads', filename)

        # Crear el nuevo usuario
        nuevo_usuario = Usuario(
            nombreUsuario=nombre_usuario,
            email=email,
            contrasena=contrasena_cifrada,
            tipoUsuario=tipo_usuario or "cliente",
            imagen=imagen
        )

        session_db.add(nuevo_usuario)
        session_db.commit()
        session_db.close()

        flash("Usuario creado exitosamente", "success")


        return redirect(url_for('listar_usuarios'))

    return render_template('crearUsuario.html')

# Ruta para eliminar un usuario (solo administradores)
@app.route("/eliminarUsuario/<int:id>", methods=["GET", "POST"])
def eliminar_usuario(id):
    if session.get("tipo_usuario") != "administrador":
        flash("No tienes permiso para realizar esta acción", "danger")
        return redirect(url_for("home"))


    session_db = db.Session()
    usuario = session_db.query(Usuario).get(id)

    if not usuario:
        flash("Usuario no encontrado", "danger")
        session_db.close()
        return redirect(url_for("listar_usuarios"))

    if request.method == "POST":
        try:
            session_db.delete(usuario)
            session_db.commit()
            flash("Usuario eliminado con éxito", "success")
        except Exception as e:
            session_db.rollback()
            flash(f"Error al eliminar el usuario: {e}", "danger")
        finally:
            session_db.close()

        return redirect(url_for("listar_usuarios"))

    session_db.close()
    return render_template("eliminarUsuario.html", usuario=usuario)
#Ruta editar Usuarios
@app.route("/editarUsuario/<int:id>", methods=["GET", "POST"])
def editarUsuario(id):

    if session.get("tipo_usuario") != "administrador":
        flash("No tienes permiso para acceder a esta página", "danger")
        return redirect(url_for("home"))


    session_db = db.Session()
    usuario = session_db.query(Usuario).get(id)

    if not usuario:
        flash("Usuario no encontrado", "danger")
        session_db.close()
        return redirect(url_for("listar_usuarios"))

    # Si el método de la solicitud es POST, es decir, el formulario fue enviado
    if request.method == 'POST':

        nuevo_nombre = request.form['nombreUsuario']
        nuevo_email = request.form['email']
        nuevo_tipo_usuario = request.form['tipo_usuario']


        usuario.nombreUsuario = nuevo_nombre
        usuario.email = nuevo_email
        usuario.tipoUsuario = nuevo_tipo_usuario


        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and allowed_file(file.filename):
                # Guardar la nueva imagen
                filename = secure_filename(file.filename)
                imagen_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(imagen_path)


                usuario.imagen = os.path.join('uploads', filename)


        try:
            session_db.commit()
            flash("Usuario actualizado con éxito", "success")
        except Exception as e:
            session_db.rollback()
            flash(f"Hubo un error al actualizar el usuario: {e}", "danger")


        session_db.close()


        return redirect(url_for("listar_usuarios"))


    session_db.close()
    return render_template("editarUsuario.html", usuario=usuario)
#Rutas de Peliculas
@app.route("/gestionSeriesPeliculas")
def gestion_series_peliculas():
    if session.get("tipo_usuario") != "administrador":
        flash("No tienes permiso para acceder a esta página", "danger")
        return redirect(url_for("home"))

    session_db = db.get_session()
    try:

        peliculas = session_db.query(Pelicula).options(joinedload(Pelicula.categoria)).all()
        series = session_db.query(Serie).options(joinedload(Serie.categoria)).all()
        categorias = session_db.query(Categoria).all()
    except Exception as e:
        flash(f"Error al obtener datos: {str(e)}", "danger")
    finally:
        session_db.close()

    return render_template("gestionSeriesPeliculas.html", peliculas=peliculas, series=series, categorias=categorias)

@app.route("/agregarPelicula", methods=["GET", "POST"])
def agregar_pelicula():
    if request.method == "POST":

        titulo = request.form["tituloPelicula"]
        descripcion = request.form["descripcionPelicula"]
        año = request.form["añoPelicula"]
        director = request.form["directorPelicula"]
        duracion = request.form["duracionPelicula"]
        categoria_id = request.form["categoriaPelicula"]
        trailer = request.form["trailerPelicula"]
        imagen = request.files.get("imagenPelicula")

        imagen_path = "imagenesPeliculas/default.jpg"
        if imagen and allowed_file(imagen.filename):
            imagen_filename = secure_filename(imagen.filename)
            imagen_path = os.path.join("static", "imagenesPeliculas", imagen_filename)
            imagen.save(imagen_path)
            imagen_path = f"imagenesPeliculas/{imagen_filename}"

        nueva_pelicula = Pelicula(
            titulo=titulo,
            descripcion=descripcion,
            año=año,
            director=director,
            duracion=duracion,
            categoria_id=categoria_id,
            trailer=trailer,
            imagen=imagen_path,
        )

        session_db = db.get_session()
        try:
            session_db.add(nueva_pelicula)
            session_db.commit()
            flash("Película agregada correctamente", "success")
        except Exception as e:
            session_db.rollback()
            flash(f"Error: {str(e)}", "danger")
        finally:
            session_db.close()

        return redirect(url_for("gestion_series_peliculas"))


    categorias = Categoria.query.all()
    return render_template("pagina_peliculas.html", categorias=categorias)

@app.route("/eliminarPelicula/<int:id>", methods=["POST"])
def eliminar_pelicula(id):
    session_db = db.get_session()
    try:
        pelicula = session_db.query(Pelicula).filter(Pelicula.id == id).first()
        if not pelicula:
            flash("Película no encontrada", "danger")
            return redirect(url_for("gestion_series_peliculas"))

        session_db.delete(pelicula)
        session_db.commit()
        flash("Película eliminada correctamente", "success")
    except Exception as e:
        session_db.rollback()
        flash(f"Error al eliminar la película: {str(e)}", "danger")
    finally:
        session_db.close()

    return redirect(url_for("gestion_series_peliculas"))

@app.route("/editarPelicula/<int:id>", methods=["GET", "POST"])
def editar_pelicula(id):
    session_db = db.get_session()

    pelicula = session_db.query(Pelicula).filter_by(id=id).first()

    if not pelicula:
        flash("La película no existe.", "danger")
        return redirect(url_for("gestion_series_peliculas"))

    if request.method == "POST":
        titulo = request.form.get("tituloPelicula")
        descripcion = request.form.get("descripcionPelicula")
        año = request.form.get("añoPelicula")
        director = request.form.get("directorPelicula")
        duracion = request.form.get("duracionPelicula")
        categoria_id = request.form.get("categoriaPelicula")
        imagen = request.files.get("imagenPelicula")
        trailer = request.form.get("trailerPelicula")

        pelicula.titulo = titulo
        pelicula.descripcion = descripcion
        pelicula.año = int(año) if año else pelicula.año
        pelicula.director = director
        pelicula.duracion = int(duracion) if duracion else pelicula.duracion
        pelicula.categoria_id = int(categoria_id) if categoria_id else pelicula.categoria_id
        pelicula.trailer = trailer

        # Manejo de la imagen
        if imagen and imagen.filename != "":
            imagen_filename = secure_filename(imagen.filename)
            imagen_path = os.path.join("static", "imagenesPeliculas", imagen_filename)
            imagen.save(imagen_path)
            pelicula.imagen = f"imagenesPeliculas/{imagen_filename}"
        session_db.commit()
        session_db.close()
        flash("Película actualizada correctamente.", "success")
        return redirect(url_for("gestion_series_peliculas"))

    categorias = session_db.query(Categoria).all()
    session_db.close()

    return render_template("editarPelicula.html", pelicula=pelicula, categorias=categorias)

#Rutas de serie
@app.route("/agregarSerie", methods=["GET", "POST"])
def agregar_serie():
    if request.method == "POST":

        titulo = request.form.get("tituloSerie")
        descripcion = request.form.get("descripcionSerie")
        año = request.form.get("añoSerie")
        temporadas = request.form.get("temporadasSerie")
        capitulos = request.form.get("capitulosSerie")
        duracion_capitulo = request.form.get("duracionCapituloSerie")  # Corregido el nombre del campo
        categoria_id = request.form.get("categoriaSerie")
        trailer = request.form.get("trailerSerie")
        imagen = request.files.get("imagenSerie")


        if not titulo or not descripcion or not año or not temporadas or not capitulos or not duracion_capitulo or not categoria_id:
            flash("Todos los campos obligatorios deben ser completados", "danger")
            return redirect(url_for("gestion_series_peliculas"))


        imagen_path = "imagenesSeries/default.jpg"
        if imagen and allowed_file(imagen.filename):
            imagen_filename = secure_filename(imagen.filename)
            imagen_path = os.path.join("static", "imagenesSeries", imagen_filename)
            imagen.save(imagen_path)
            imagen_path = f"imagenesSeries/{imagen_filename}"


        nueva_serie = Serie(
            titulo=titulo,
            descripcion=descripcion,
            año=int(año),
            temporadas=int(temporadas),
            capitulos=int(capitulos),
            duracionCapitulo=int(duracion_capitulo),  # Corregido: debe usar duracionCapitulo
            categoria_id=int(categoria_id),
            trailer=trailer,
            imagen=imagen_path,
        )


        session_db = db.get_session()
        try:
            session_db.add(nueva_serie)
            session_db.commit()
            flash("Serie agregada correctamente", "success")
        except Exception as e:
            session_db.rollback()
            flash(f"Error al agregar la serie: {str(e)}", "danger")
        finally:
            session_db.close()

        return redirect(url_for("gestion_series_peliculas"))


    categorias = Categoria.query.all()
    return render_template("pagina_series.html", categorias=categorias)


@app.route("/eliminarSerie/<int:id>", methods=["POST"])
def eliminar_serie(id):
    session_db = db.get_session()
    try:
        serie = session_db.query(Serie).filter(Serie.id == id).first()
        if not serie:
            flash("Serie no encontrada", "danger")
            return redirect(url_for("gestion_series_peliculas"))

        session_db.delete(serie)
        session_db.commit()
        flash("Serie eliminada correctamente", "success")
    except Exception as e:
        session_db.rollback()
        flash(f"Error al eliminar la serie: {str(e)}", "danger")
    finally:
        session_db.close()

    return redirect(url_for("gestion_series_peliculas"))

@app.route("/editarSerie/<int:id>", methods=["GET", "POST"])
def editar_serie(id):
    session_db = db.get_session()

    serie = session_db.query(Serie).filter_by(id=id).first()

    if not serie:
        flash("La serie no existe.", "danger")
        return redirect(url_for("gestion_series_peliculas"))

    if request.method == "POST":
        titulo = request.form.get("tituloSerie")
        descripcion = request.form.get("descripcionSerie")
        año = request.form.get("añoSerie")
        temporadas = request.form.get("temporadasSerie")
        capitulos = request.form.get("capitulosSerie")
        duracion_capitulo = request.form.get("duracionSerie")
        categoria_id = request.form.get("categoriaSerie")
        imagen = request.files.get("imagenSerie")
        trailer = request.form.get("trailerSerie")

        serie.titulo = titulo
        serie.descripcion = descripcion
        serie.año = int(año) if año else serie.año
        serie.temporadas = int(temporadas) if temporadas else serie.temporadas
        serie.capitulos = int(capitulos) if capitulos else serie.capitulos
        serie.duracionCapitulo = int(duracion_capitulo) if duracion_capitulo else serie.duracionCapitulo
        serie.categoria_id = int(categoria_id) if categoria_id else serie.categoria_id
        serie.trailer = trailer

        # Manejo de la imagen
        if imagen and imagen.filename != "":
            imagen_filename = secure_filename(imagen.filename)
            imagen_path = os.path.join("static", "imagenesSeries", imagen_filename)
            imagen.save(imagen_path)
            serie.imagen = f"imagenesSeries/{imagen_filename}"

        session_db.commit()
        session_db.close()
        flash("Serie actualizada correctamente.", "success")
        return redirect(url_for("gestion_series_peliculas"))

    categorias = session_db.query(Categoria).all()
    session_db.close()

    return render_template("editarSerie.html", serie=serie, categorias=categorias)

#catalogo de series y peliculas
@app.route('/catalogoPeliculas', methods=['GET', 'POST'])
def catalogo_peliculas():
    session_db = db.Session()
    usuario_id = session.get('user_id')

    if usuario_id is None:
        return redirect(url_for('login'))

    if request.method == 'POST':
        contenido_id = request.form['contenido_id']
        accion = request.form['accion']


        pelicula = session_db.query(Pelicula).filter_by(id=contenido_id).first()

        if pelicula:
            if accion == 'vista':

                usuario_pelicula = session_db.query(UsuarioPelicula).filter(
                    UsuarioPelicula.usuarioId == usuario_id,
                    UsuarioPelicula.peliculaId == pelicula.id
                ).one_or_none()


                if usuario_pelicula:
                    usuario_pelicula.vista = not usuario_pelicula.vista
                else:

                    usuario_pelicula = UsuarioPelicula(
                        usuarioId=usuario_id,
                        peliculaId=pelicula.id,
                        vista=True
                    )
                    session_db.add(usuario_pelicula)

            elif accion == 'favorita':

                usuario_pelicula = session_db.query(UsuarioPelicula).filter(
                    UsuarioPelicula.usuarioId == usuario_id,
                    UsuarioPelicula.peliculaId == pelicula.id
                ).one_or_none()

                if usuario_pelicula:
                    usuario_pelicula.favorita = not usuario_pelicula.favorita
                else:
                    usuario_pelicula = UsuarioPelicula(
                        usuarioId=usuario_id,
                        peliculaId=pelicula.id,
                        favorita=True
                    )
                    session_db.add(usuario_pelicula)

            session_db.commit()


    peliculas = session_db.query(Pelicula).options(joinedload(Pelicula.categoria)).all()


    estado_peliculas = {}
    for pelicula in peliculas:

        usuario_pelicula = session_db.query(UsuarioPelicula).filter(
            UsuarioPelicula.usuarioId == usuario_id,
            UsuarioPelicula.peliculaId == pelicula.id
        ).one_or_none()

        if usuario_pelicula:
            estado_peliculas[pelicula.id] = {
                'vista': usuario_pelicula.vista,
                'favorita': usuario_pelicula.favorita
            }
        else:
            estado_peliculas[pelicula.id] = {
                'vista': False,
                'favorita': False
            }

    session_db.close()

    # Pasar las películas con las categorías a la plantilla
    return render_template('catalogoPeliculas.html', peliculas=peliculas, estado_peliculas=estado_peliculas)

@app.route('/catalogoSeries', methods=['GET', 'POST'])
def catalogo_series():
    session_db = db.Session()
    usuario_id = session.get('user_id')

    if usuario_id is None:
        return redirect(url_for('login'))

    if request.method == 'POST':
        contenido_id = request.form['contenido_id']
        accion = request.form['accion']


        serie = session_db.query(Serie).filter_by(id=contenido_id).first()

        if serie:
            if accion == 'vista':

                usuario_serie = session_db.query(UsuarioSerie).filter(
                    UsuarioSerie.usuarioId == usuario_id,
                    UsuarioSerie.serieId == serie.id
                ).one_or_none()

                if usuario_serie:
                    usuario_serie.vista = not usuario_serie.vista
                else:

                    usuario_serie = UsuarioSerie(
                        usuarioId=usuario_id,
                        serieId=serie.id,
                        vista=True
                    )
                    session_db.add(usuario_serie)

            elif accion == 'favorita':

                usuario_serie = session_db.query(UsuarioSerie).filter(
                    UsuarioSerie.usuarioId == usuario_id,
                    UsuarioSerie.serieId == serie.id
                ).one_or_none()

                if usuario_serie:
                    usuario_serie.favorita = not usuario_serie.favorita
                else:
                    usuario_serie = UsuarioSerie(
                        usuarioId=usuario_id,
                        serieId=serie.id,
                        favorita=True
                    )
                    session_db.add(usuario_serie)

            session_db.commit()


    series = session_db.query(Serie).options(joinedload(Serie.categoria)).all()


    estado_series = {}
    for serie in series:
        usuario_serie = session_db.query(UsuarioSerie).filter(
            UsuarioSerie.usuarioId == usuario_id,
            UsuarioSerie.serieId == serie.id
        ).one_or_none()

        if usuario_serie:
            estado_series[serie.id] = {
                'vista': usuario_serie.vista,
                'favorita': usuario_serie.favorita
            }
        else:
            estado_series[serie.id] = {
                'vista': False,
                'favorita': False
            }

    session_db.close()


    return render_template('catalogoSeries.html', series=series, estado_series=estado_series)
#favoritos y vistos


@app.route('/favoritos', methods=['GET', 'POST'])
def favoritos():
    session_db = db.Session()
    usuario_id = session.get('user_id')

    if usuario_id is None:
        return redirect(url_for('login'))


    peliculas_favoritas = session_db.query(Pelicula).join(UsuarioPelicula).options(
        joinedload(Pelicula.categoria)
    ).filter(
        UsuarioPelicula.usuarioId == usuario_id,
        UsuarioPelicula.favorita == True
    ).all()


    series_favoritas = session_db.query(Serie).join(UsuarioSerie).options(
        joinedload(Serie.categoria)
    ).filter(
        UsuarioSerie.usuarioId == usuario_id,
        UsuarioSerie.favorita == True
    ).all()

    session_db.close()


    return render_template('favoritos.html', peliculas_favoritas=peliculas_favoritas, series_favoritas=series_favoritas)


@app.route('/vistos', methods=['GET', 'POST'])
def vistos():
    session_db = db.Session()
    usuario_id = session.get('user_id')

    if usuario_id is None:
        return redirect(url_for('login'))


    peliculas_vistas = session_db.query(Pelicula).join(UsuarioPelicula).options(
        joinedload(Pelicula.categoria)
    ).filter(
        UsuarioPelicula.usuarioId == usuario_id,
        UsuarioPelicula.vista == True
    ).all()


    series_vistas = session_db.query(Serie).join(UsuarioSerie).options(
        joinedload(Serie.categoria)
    ).filter(
        UsuarioSerie.usuarioId == usuario_id,
        UsuarioSerie.vista == True
    ).all()

    session_db.close()


    return render_template('vistos.html', peliculas_vistas=peliculas_vistas, series_vistas=series_vistas)


@app.route('/catalogo', methods=['GET', 'POST'])
def catalogo():
    session_db = db.Session()
    usuario_id = session.get('user_id')

    if usuario_id is None:
        return redirect(url_for('login'))

    peliculas = []
    series = []


    categorias = session_db.query(Categoria).all()
    categorias_data = [{'id': categoria.id, 'nombre': categoria.nombre} for categoria in categorias]


    nombre_filtro = request.args.get('nombre', '')
    categoria_filtro = request.args.get('categoria', '')

    if request.method == 'POST':
        if 'accion' in request.form:
            contenido_id = request.form['contenido_id']
            accion = request.form['accion']
            tipo_contenido = request.form['tipo_contenido']

            if tipo_contenido == "pelicula":
                contenido = session_db.query(Pelicula).filter_by(id=contenido_id).first()

                if contenido:
                    usuario_contenido = session_db.query(UsuarioPelicula).filter(
                        UsuarioPelicula.usuarioId == usuario_id,
                        UsuarioPelicula.peliculaId == contenido.id
                    ).one_or_none()

                    if accion == 'vista':
                        if usuario_contenido:
                            usuario_contenido.vista = not usuario_contenido.vista
                        else:
                            usuario_contenido = UsuarioPelicula(
                                usuarioId=usuario_id,
                                peliculaId=contenido.id,
                                vista=True
                            )
                            session_db.add(usuario_contenido)
                    elif accion == 'favorita':
                        if usuario_contenido:
                            usuario_contenido.favorita = not usuario_contenido.favorita
                        else:
                            usuario_contenido = UsuarioPelicula(
                                usuarioId=usuario_id,
                                peliculaId=contenido.id,
                                favorita=True
                            )
                            session_db.add(usuario_contenido)

            elif tipo_contenido == "serie":
                contenido = session_db.query(Serie).filter_by(id=contenido_id).first()

                if contenido:
                    usuario_contenido = session_db.query(UsuarioSerie).filter(
                        UsuarioSerie.usuarioId == usuario_id,
                        UsuarioSerie.serieId == contenido.id
                    ).one_or_none()

                    if accion == 'vista':
                        if usuario_contenido:
                            usuario_contenido.vista = not usuario_contenido.vista
                        else:
                            usuario_contenido = UsuarioSerie(
                                usuarioId=usuario_id,
                                serieId=contenido.id,
                                vista=True
                            )
                            session_db.add(usuario_contenido)
                    elif accion == 'favorita':
                        if usuario_contenido:
                            usuario_contenido.favorita = not usuario_contenido.favorita
                        else:
                            usuario_contenido = UsuarioSerie(
                                usuarioId=usuario_id,
                                serieId=contenido.id,
                                favorita=True
                            )
                            session_db.add(usuario_contenido)

            session_db.commit()

        else:  #
            categoria_filtro = request.form.get('categoria', '')
            nombre_filtro = request.form.get('nombre', '')

            # Filtrar por categoría y nombre
            query_peliculas = session_db.query(Pelicula).options(joinedload(Pelicula.categoria))
            query_series = session_db.query(Serie).options(joinedload(Serie.categoria))

            if categoria_filtro:
                query_peliculas = query_peliculas.filter(Pelicula.categoria.has(nombre=categoria_filtro))
                query_series = query_series.filter(Serie.categoria.has(nombre=categoria_filtro))

            if nombre_filtro:
                query_peliculas = query_peliculas.filter(Pelicula.titulo.ilike(f"%{nombre_filtro}%"))
                query_series = query_series.filter(Serie.titulo.ilike(f"%{nombre_filtro}%"))

            peliculas = query_peliculas.all()
            series = query_series.all()

    else:
        # Si no hay búsqueda, cargar todas las películas y series
        peliculas = session_db.query(Pelicula).options(joinedload(Pelicula.categoria)).all()
        series = session_db.query(Serie).options(joinedload(Serie.categoria)).all()

    # Construir el estado para películas y series
    estado_contenido = {}

    for pelicula in peliculas:
        usuario_pelicula = session_db.query(UsuarioPelicula).filter(
            UsuarioPelicula.usuarioId == usuario_id,
            UsuarioPelicula.peliculaId == pelicula.id
        ).one_or_none()

        estado_contenido[f"pelicula-{pelicula.id}"] = {
            'vista': usuario_pelicula.vista if usuario_pelicula else False,
            'favorita': usuario_pelicula.favorita if usuario_pelicula else False
        }

    for serie in series:
        usuario_serie = session_db.query(UsuarioSerie).filter(
            UsuarioSerie.usuarioId == usuario_id,
            UsuarioSerie.serieId == serie.id
        ).one_or_none()

        estado_contenido[f"serie-{serie.id}"] = {
            'vista': usuario_serie.vista if usuario_serie else False,
            'favorita': usuario_serie.favorita if usuario_serie else False
        }

    session_db.close()  # Cierra la sesión cuando termines

    # Pasar películas, series, categorías (ahora como diccionarios) y su estado a la plantilla
    return render_template('catalogo.html', peliculas=peliculas, series=series, categorias=categorias_data,
                           estado_contenido=estado_contenido, nombre_filtro=nombre_filtro, categoria_filtro=categoria_filtro)


def obtener_peliculas_series(session_db, nombre_filtro, categoria_filtro):
    # Obtener películas y series filtradas por nombre y categoría
    query_peliculas = session_db.query(Pelicula).options(joinedload(Pelicula.categoria))
    query_series = session_db.query(Serie).options(joinedload(Serie.categoria))

    # Filtrar por categoría, si se proporcionó un filtro
    if categoria_filtro:
        query_peliculas = query_peliculas.filter(Pelicula.categoria.has(nombre=categoria_filtro))
        query_series = query_series.filter(Serie.categoria.has(nombre=categoria_filtro))

    # Filtrar por nombre, si se proporcionó un filtro
    if nombre_filtro:
        query_peliculas = query_peliculas.filter(Pelicula.titulo.ilike(f"%{nombre_filtro}%"))
        query_series = query_series.filter(Serie.titulo.ilike(f"%{nombre_filtro}%"))

    peliculas = query_peliculas.all()
    series = query_series.all()

    return peliculas, series


@app.route('/buscar', methods=['GET'])
def buscar():
    session_db = db.Session()  # Crea una nueva sesión de base de datos
    usuario_id = session.get('user_id')  # Obtén el ID del usuario de la sesión

    if usuario_id is None:
        return redirect(url_for('login'))  # Redirige al login si no hay un usuario autenticado

    # Obtener parámetros de búsqueda desde la URL (GET)
    nombre_filtro = request.args.get('nombre', '')  # Obtener el nombre de búsqueda
    categoria_filtro = request.args.get('categoria', '')  # Obtener la categoría de búsqueda

    # Cargar todas las categorías disponibles y convertirlas en diccionarios
    categorias = session_db.query(Categoria).all()
    categorias_data = [{'id': categoria.id, 'nombre': categoria.nombre} for categoria in categorias]

    # Llamar a la función común para obtener películas y series filtradas
    peliculas, series = obtener_peliculas_series(session_db, nombre_filtro, categoria_filtro)

    session_db.close()  # Cierra la sesión cuando termines

    # Pasar películas, series, categorías a la plantilla
    return render_template('catalogo.html', peliculas=peliculas, series=series, categorias=categorias_data,
                           nombre_filtro=nombre_filtro, categoria_filtro=categoria_filtro)


# Endpoint para actualizar el estado de vista y favorita
@app.route('/actualizar_estado', methods=['POST'])
def actualizar_estado():
    session_db = db.Session()
    usuario_id = session.get('user_id')

    if not usuario_id:
        return redirect(url_for('login'))

    contenido_id = request.form.get('contenido_id')
    tipo = request.form.get('tipo')
    accion = request.form.get('accion')

    if tipo == 'pelicula':
        registro = session_db.query(UsuarioPelicula).filter_by(usuarioId=usuario_id, peliculaId=contenido_id).first()
        if not registro:
            registro = UsuarioPelicula(usuarioId=usuario_id, peliculaId=contenido_id, vista=False, favorita=False)
            session_db.add(registro)

        if accion == 'vista':
            registro.vista = not registro.vista
        elif accion == 'favorita':
            registro.favorita = not registro.favorita

    elif tipo == 'serie':
        registro = session_db.query(UsuarioSerie).filter_by(usuarioId=usuario_id, serieId=contenido_id).first()
        if not registro:
            registro = UsuarioSerie(usuarioId=usuario_id, serieId=contenido_id, vista=False, favorita=False)
            session_db.add(registro)

        if accion == 'vista':
            registro.vista = not registro.vista
        elif accion == 'favorita':
            registro.favorita = not registro.favorita

    session_db.commit()
    session_db.close()

    return redirect(url_for('catalogo'))


# Ruta para mostrar estadísticas
@app.route('/estadisticas')
def estadisticas():
    # Obtener la sesión de la base de datos
    session_sqlalchemy = db.get_session()

    # Obtener los usuarios desde la base de datos
    usuarios = session_sqlalchemy.query(Usuario).all()
    datos_comparativos = []
    graficos_individuales = {}
    circulares_individuales = {}
    graficos_por_contenido = {}

    # Recorremos los usuarios para obtener sus estadísticas
    for usuario in usuarios:
        usuario_id = usuario.id
        print(f"Procesando usuario ID: {usuario_id}")

        # Obtener las películas y series vistas por el usuario
        peliculas_vistas = session_sqlalchemy.query(UsuarioPelicula).filter(UsuarioPelicula.usuarioId == usuario_id,
                                                                            UsuarioPelicula.vista == True).all()
        series_vistas = session_sqlalchemy.query(UsuarioSerie).filter(UsuarioSerie.usuarioId == usuario_id,
                                                                      UsuarioSerie.vista == True).all()

        # Verificamos cuántas películas y series tiene este usuario
        print(f"Usuario {usuario_id} tiene {len(peliculas_vistas)} películas vistas.")
        print(f"Usuario {usuario_id} tiene {len(series_vistas)} series vistas.")

        # Si no hay series o películas, los datos no se pasarán a los gráficos
        if len(peliculas_vistas) == 0 and len(series_vistas) == 0:
            print(f"Usuario {usuario_id} no tiene series ni películas vistas. Saltando.")
            continue

        # Calcular tiempos totales
        tiempo_total_peliculas = sum(pelicula.pelicula.duracion for pelicula in peliculas_vistas)
        tiempo_total_series = 0
        for serie in series_vistas:
            duracion_capitulo = serie.serie.duracionCapitulo
            capitulos = serie.serie.capitulos
            tiempo_total_series += duracion_capitulo * capitulos

        # Guardamos los datos para cada usuario
        datos_comparativos.append({
            'usuario_id': usuario_id,
            'tiempo_total_peliculas': tiempo_total_peliculas,
            'tiempo_total_series': tiempo_total_series,
            'peliculas_vistas_count': len(peliculas_vistas),
            'series_vistas_count': len(series_vistas),
            'peliculas_vistas': peliculas_vistas,
            'series_vistas': series_vistas
        })

        # Verificamos los tiempos calculados
        print(f"Usuario {usuario_id} - Tiempo total en películas: {tiempo_total_peliculas} minutos.")
        print(f"Usuario {usuario_id} - Tiempo total en series: {tiempo_total_series} minutos.")

        # Generar gráficos individuales para cada usuario (Gráfico de barras y circular)
        img_barras = crear_grafico_barras(tiempo_total_peliculas, tiempo_total_series)
        img_circular = crear_grafico_circular(len(peliculas_vistas), len(series_vistas))

        graficos_individuales[usuario_id] = img_barras
        circulares_individuales[usuario_id] = img_circular

        # Generar gráficos por contenido (por película y serie)
        graficos_por_contenido[usuario_id] = {
            'peliculas': generar_graficos_por_contenido(peliculas_vistas),
            'series': generar_graficos_por_contenido(series_vistas)
        }

    # Verificamos los datos globales
    tiempo_peliculas = sum(dato['tiempo_total_peliculas'] for dato in datos_comparativos)
    tiempo_series = sum(dato['tiempo_total_series'] for dato in datos_comparativos)

    print(f"Tiempo total de todas las películas: {tiempo_peliculas} minutos.")
    print(f"Tiempo total de todas las series: {tiempo_series} minutos.")

    # Generar gráficos comparativos de todas las películas y series
    img_comparativo_peliculas = generar_grafico_comparativo_todas_las_peliculas(
        [pelicula for usuario in datos_comparativos for pelicula in usuario['peliculas_vistas']]
    )
    img_comparativo_series = generar_grafico_comparativo_todas_las_series(
        [serie for usuario in datos_comparativos for serie in usuario['series_vistas']]
    )

    print("Generando gráficos comparativos...")

    # Gráfico base64 (Generamos y codificamos en base64)
    img_base64 = crear_grafico_comparativa(tiempo_peliculas, tiempo_series)

    # Verificamos si el gráfico se genera correctamente
    print("Generando gráfico base64...")

    return render_template('estadisticas.html',
                           img_base64=img_base64,
                           estadisticas=datos_comparativos,
                           graficos_individuales=graficos_individuales,
                           circulares_individuales=circulares_individuales,
                           graficos_por_contenido=graficos_por_contenido,
                           img_comparativo_peliculas=img_comparativo_peliculas,
                           img_comparativo_series=img_comparativo_series)

# Funciones para generar los gráficos en base64

def crear_grafico_comparativa(tiempo_peliculas, tiempo_series):
    fig, ax = plt.subplots()
    ax.bar(['Películas', 'Series'], [tiempo_peliculas, tiempo_series], color=['blue', 'red'])
    ax.set_ylabel('Tiempo Total (minutos)')
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode('utf-8')


def crear_grafico_barras(tiempo_peliculas, tiempo_series):
    fig, ax = plt.subplots()
    ax.bar(['Películas', 'Series'], [tiempo_peliculas, tiempo_series], color=['blue', 'red'])
    ax.set_ylabel('Tiempo Total (minutos)')
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode('utf-8')


def crear_grafico_circular(peliculas_vistas, series_vistas):
    fig, ax = plt.subplots()
    ax.pie([peliculas_vistas, series_vistas], labels=['Películas', 'Series'], autopct='%1.1f%%', colors=['blue', 'red'])
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode('utf-8')


# Función para generar gráficos por contenido (películas y series por título)
def generar_graficos_por_contenido(vistas):
    contenido_graficos = {}
    for vista in vistas:
        # Determinamos si es una película o una serie
        if hasattr(vista, 'pelicula'):
            titulo = vista.pelicula.titulo
            duracion = vista.pelicula.duracion
        else:
            titulo = vista.serie.titulo
            duracion = vista.serie.duracionCapitulo

        # Creamos un gráfico por título de contenido
        fig, ax = plt.subplots()
        ax.bar([titulo], [duracion], color=['green'])
        ax.set_ylabel('Duración (minutos)')
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        contenido_graficos[titulo] = base64.b64encode(img.getvalue()).decode('utf-8')
    return contenido_graficos


# Función para generar el gráfico comparativo de todas las películas vistas
def generar_grafico_comparativo_todas_las_peliculas(peliculas_vistas):
    titulos = [pelicula.pelicula.titulo for pelicula in peliculas_vistas]
    duraciones = [pelicula.pelicula.duracion for pelicula in peliculas_vistas]

    fig, ax = plt.subplots()
    ax.bar(titulos, duraciones, color='blue')
    ax.set_ylabel('Duración (minutos)')
    ax.set_xlabel('Películas')
    ax.set_xticklabels(titulos, rotation=90)  # Rotamos las etiquetas de los títulos
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode('utf-8')


# Función para generar el gráfico comparativo de todas las series vistas
def generar_grafico_comparativo_todas_las_series(series_vistas):
    titulos = [serie.serie.titulo for serie in series_vistas]
    duraciones = [serie.serie.duracionCapitulo * serie.serie.capitulos for serie in series_vistas]

    fig, ax = plt.subplots()
    ax.bar(titulos, duraciones, color='red')
    ax.set_ylabel('Duración Total (minutos)')
    ax.set_xlabel('Series')
    ax.set_xticklabels(titulos, rotation=90)  # Rotamos las etiquetas de los títulos
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode('utf-8')


#Contacto
@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        # Obtener los datos del formulario de contacto
        nombre = request.form['nombre']
        correo = request.form['correo']
        mensaje = request.form['mensaje']

        # Validación básica (puedes agregar más validaciones si es necesario)
        if not nombre or not correo or not mensaje:
            flash('Todos los campos son obligatorios', 'danger')
            return redirect(url_for('contacto'))  # Redirige de nuevo al formulario si hay error

        # Aquí puedes hacer algo con los datos del formulario, como enviarlo por correo o guardarlo en la base de datos
        # En este ejemplo solo mostramos un mensaje de éxito
        flash('Mensaje enviado correctamente', 'success')

        # Redirige a la página de contacto o a otra página de agradecimiento
        return redirect(url_for('contacto'))

    return render_template('contacto.html')

#privacidad
@app.route('/privacidad')
def politica_privacidad():
    return render_template('privacidad.html')

if __name__ == "__main__":
    app.run(debug=True)
