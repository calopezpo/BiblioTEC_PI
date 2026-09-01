from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlalchemy import text, or_, func
from sqlalchemy.exc import SQLAlchemyError

from config import Config
from models import (
    db,
    Usuario,
    MaterialBibliografico,
    Autor,
    Genero,
    Biblioteca,
    Ejemplar,
    Prestamo,
    Reserva,
    Mood,
    LibroMood
)

from auth import login_requerido, rol_requerido
from email_service import enviar_correo_prestamo, enviar_correo_devolucion
from report_service import (
    enviar_reporte_prestamos_admin,
    enviar_reporte_libros_disponibles_admin
)


app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


# ============================================================
# INICIO
# ============================================================

@app.route("/")
def inicio():
    libros = MaterialBibliografico.query.filter_by(
        estado="Activo"
    ).order_by(
        MaterialBibliografico.id_libro.desc()
    ).limit(6).all()

    return render_template(
        "index.html",
        libros=libros
    )


# ============================================================
# CATALOGO
# ============================================================

@app.route("/catalogo")
def catalogo():
    q = request.args.get("q", "").strip()

    consulta = MaterialBibliografico.query.join(
        Autor,
        MaterialBibliografico.id_autor == Autor.id_autor
    ).join(
        Genero,
        MaterialBibliografico.id_genero == Genero.id_genero
    ).filter(
        MaterialBibliografico.estado == "Activo"
    )

    if q:
        termino = f"%{q}%"

        consulta = consulta.filter(
            or_(
                MaterialBibliografico.titulo.ilike(termino),
                MaterialBibliografico.descripcion.ilike(termino),
                MaterialBibliografico.isbn.ilike(termino),
                Autor.nombres.ilike(termino),
                Autor.apellidos.ilike(termino),
                Genero.nombre.ilike(termino)
            )
        )

    libros = consulta.order_by(
        MaterialBibliografico.titulo
    ).all()

    return render_template(
        "catalogo.html",
        libros=libros,
        q=q
    )


# ============================================================
# DETALLE DEL LIBRO
# ============================================================

@app.route("/libro/<int:id_libro>")
def detalle_libro(id_libro):
    libro = db.get_or_404(
        MaterialBibliografico,
        id_libro
    )

    ejemplares = Ejemplar.query.filter_by(
        id_libro=id_libro
    ).all()

    return render_template(
        "detalle_libro.html",
        libro=libro,
        ejemplares=ejemplares
    )


# ============================================================
# SORPRENDEME
# ============================================================

@app.route("/sorprendeme")
def sorprendeme():

    libro = MaterialBibliografico.query.filter_by(
        estado="Activo"
    ).order_by(
        func.random()
    ).first()

    if not libro:
        flash(
            "Todavía no existen libros activos en el catálogo.",
            "warning"
        )

        return redirect(
            url_for("catalogo")
        )

    return redirect(
        url_for(
            "detalle_libro",
            id_libro=libro.id_libro
        )
    )


# ============================================================
# MOOD SEARCH
# ============================================================

@app.route("/mood")
def mood():

    nombre = request.args.get(
        "mood",
        ""
    ).strip()

    libros = []

    if nombre:

        libros = MaterialBibliografico.query.join(
            LibroMood,
            LibroMood.id_libro == MaterialBibliografico.id_libro
        ).join(
            Mood,
            Mood.id_mood == LibroMood.id_mood
        ).filter(
            MaterialBibliografico.estado == "Activo",
            Mood.nombre.ilike(nombre)
        ).order_by(
            MaterialBibliografico.id_libro.desc()
        ).all()

    moods = Mood.query.order_by(
        Mood.nombre
    ).all()

    return render_template(
        "mood.html",
        moods=moods,
        libros=libros,
        mood_actual=nombre
    )


# ============================================================
# SWIPE
# ============================================================

@app.route("/swipe")
def swipe():

    libros = MaterialBibliografico.query.filter_by(
        estado="Activo"
    ).order_by(
        MaterialBibliografico.id_libro.desc()
    ).all()

    return render_template(
        "swipe.html",
        libros=libros
    )


# ============================================================
# REGISTRO
# ============================================================

@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":

        nombres = request.form.get(
            "nombres",
            ""
        ).strip()

        apellidos = request.form.get(
            "apellidos",
            ""
        ).strip()

        correo = request.form.get(
            "correo",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not nombres or not apellidos or not correo or not password:

            flash(
                "Completa todos los campos.",
                "warning"
            )

            return render_template(
                "registro.html"
            )

        if len(password) < 6:

            flash(
                "La contraseña debe tener al menos 6 caracteres.",
                "warning"
            )

            return render_template(
                "registro.html"
            )

        if Usuario.query.filter_by(
            correo=correo
        ).first():

            flash(
                "Ya existe una cuenta con ese correo.",
                "danger"
            )

            return render_template(
                "registro.html"
            )

        usuario = Usuario(
            nombres=nombres,
            apellidos=apellidos,
            correo=correo,
            rol="Lector"
        )

        usuario.set_password(
            password
        )

        try:

            db.session.execute(
                text(
                    "CALL sp_registrar_usuario("
                    ":nombres, :apellidos, :correo, :password_hash)"
                ),
                {
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "correo": correo,
                    "password_hash": usuario.password_hash
                }
            )

            db.session.commit()

        except SQLAlchemyError as error:

            db.session.rollback()

            print(
                "ERROR REGISTRO:",
                error
            )

            flash(
                "No se pudo crear la cuenta. Intenta nuevamente.",
                "danger"
            )

            return render_template(
                "registro.html"
            )

        flash(
            "Cuenta creada correctamente. Ya puedes iniciar sesión.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "registro.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        correo = request.form.get(
            "correo",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        usuario = Usuario.query.filter_by(
            correo=correo,
            estado="Activo"
        ).first()

        try:
            password_correcto = (
                usuario
                and usuario.check_password(password)
            )

        except ValueError:
            password_correcto = False

        if password_correcto:

            session.clear()

            session["usuario_id"] = usuario.id_usuario
            session["usuario_nombre"] = usuario.nombres
            session["usuario_rol"] = usuario.rol

            flash(
                f"Bienvenido, {usuario.nombres}.",
                "success"
            )

            if usuario.es_admin():

                return redirect(
                    url_for("admin")
                )

            return redirect(
                url_for("inicio")
            )

        flash(
            "Correo o contraseña incorrectos.",
            "danger"
        )

    return render_template(
        "login.html"
    )


# ============================================================
# CERRAR SESION
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "Sesión cerrada correctamente.",
        "success"
    )

    return redirect(
        url_for("inicio")
    )


# ============================================================
# REALIZAR PRESTAMO
# ============================================================

@app.post("/prestamo/<int:id_ejemplar>")
@login_requerido
def realizar_prestamo(id_ejemplar):

    ejemplar = db.get_or_404(
        Ejemplar,
        id_ejemplar
    )

    if ejemplar.estado != "Disponible":

        flash(
            "Ese ejemplar no está disponible.",
            "warning"
        )

        return redirect(
            url_for(
                "detalle_libro",
                id_libro=ejemplar.id_libro
            )
        )

    try:

        db.session.execute(
            text(
                "CALL sp_realizar_prestamo("
                ":usuario, :ejemplar)"
            ),
            {
                "usuario": session["usuario_id"],
                "ejemplar": id_ejemplar
            }
        )

        db.session.commit()

        prestamo = Prestamo.query.filter_by(
            id_usuario=session["usuario_id"],
            id_ejemplar=id_ejemplar
        ).order_by(
            Prestamo.id_prestamo.desc()
        ).first()

        correo_enviado = False

        if prestamo:
            correo_enviado = enviar_correo_prestamo(
                prestamo
            )

        if correo_enviado:

            flash(
                "Préstamo registrado. También enviamos la confirmación a tu correo.",
                "success"
            )

        else:

            flash(
                "Préstamo registrado correctamente, pero no se pudo enviar el correo.",
                "warning"
            )

    except SQLAlchemyError as error:

        db.session.rollback()

        print(
            "ERROR PRESTAMO:",
            error
        )

        flash(
            "No se pudo registrar el préstamo.",
            "danger"
        )

    return redirect(
        url_for(
            "detalle_libro",
            id_libro=ejemplar.id_libro
        )
    )


# ============================================================
# PROCESAR DEVOLUCION
# ============================================================

def procesar_devolucion(prestamo):

    db.session.execute(
        text(
            "CALL sp_devolver_libro(:prestamo)"
        ),
        {
            "prestamo": prestamo.id_prestamo
        }
    )

    db.session.commit()

    db.session.refresh(
        prestamo
    )

    return enviar_correo_devolucion(
        prestamo
    )


# ============================================================
# DEVOLUCION DESDE USUARIO
# ============================================================

@app.post("/prestamo/<int:id_prestamo>/devolver")
@login_requerido
def devolver_prestamo(id_prestamo):

    prestamo = db.get_or_404(
        Prestamo,
        id_prestamo
    )

    if (
        prestamo.id_usuario != session["usuario_id"]
        and session.get("usuario_rol") != "Administrador"
    ):

        flash(
            "No tienes permisos para devolver este préstamo.",
            "danger"
        )

        return redirect(
            url_for("mis_libros")
        )

    if prestamo.estado != "Activo":

        flash(
            "Este préstamo ya no está activo.",
            "warning"
        )

        return redirect(
            url_for("mis_libros")
        )

    try:

        correo_enviado = procesar_devolucion(
            prestamo
        )

        if correo_enviado:

            flash(
                "Libro devuelto correctamente. Te enviamos la confirmación por correo.",
                "success"
            )

        else:

            flash(
                "Libro devuelto correctamente, pero no se pudo enviar el correo.",
                "warning"
            )

    except SQLAlchemyError as error:

        db.session.rollback()

        print(
            "ERROR DEVOLUCION:",
            error
        )

        flash(
            "No se pudo registrar la devolución.",
            "danger"
        )

    return redirect(
        url_for("mis_libros")
    )


# ============================================================
# RESERVAR LIBRO
# ============================================================

@app.post("/reserva/<int:id_libro>/<int:id_biblioteca>")
@login_requerido
def realizar_reserva(id_libro, id_biblioteca):

    libro = db.get_or_404(
        MaterialBibliografico,
        id_libro
    )

    try:

        db.session.execute(
            text(
                "CALL sp_realizar_reserva("
                ":usuario, :libro, :biblioteca)"
            ),
            {
                "usuario": session["usuario_id"],
                "libro": id_libro,
                "biblioteca": id_biblioteca
            }
        )

        db.session.commit()

        flash(
            "Reserva registrada correctamente.",
            "success"
        )

    except SQLAlchemyError as error:

        db.session.rollback()

        print(
            "ERROR RESERVA:",
            error
        )

        flash(
            "No se pudo registrar la reserva.",
            "danger"
        )

    return redirect(
        url_for(
            "detalle_libro",
            id_libro=libro.id_libro
        )
    )


# ============================================================
# MIS LIBROS
# ============================================================

@app.route("/mis-libros")
@login_requerido
def mis_libros():

    usuario_id = session["usuario_id"]

    prestamos = Prestamo.query.filter_by(
        id_usuario=usuario_id
    ).order_by(
        Prestamo.id_prestamo.desc()
    ).all()

    reservas = Reserva.query.filter_by(
        id_usuario=usuario_id
    ).order_by(
        Reserva.id_reserva.desc()
    ).all()

    return render_template(
        "mis_libros.html",
        prestamos=prestamos,
        reservas=reservas
    )


# ============================================================
# PERFIL
# ============================================================

@app.route("/perfil")
@login_requerido
def perfil():

    usuario = db.get_or_404(
        Usuario,
        session["usuario_id"]
    )

    return render_template(
        "perfil.html",
        usuario=usuario
    )


# ============================================================
# PANEL ADMINISTRADOR
# ============================================================

@app.route("/admin")
@rol_requerido("Administrador")
def admin():

    total_usuarios = Usuario.query.count()

    total_libros = MaterialBibliografico.query.count()

    total_prestamos = Prestamo.query.count()

    total_reservas = Reserva.query.count()


    autores = Autor.query.order_by(
        Autor.apellidos,
        Autor.nombres
    ).all()


    generos = Genero.query.order_by(
        Genero.nombre
    ).all()


    moods = Mood.query.order_by(
        Mood.nombre
    ).all()


    bibliotecas = Biblioteca.query.filter_by(
        estado="Activa"
    ).order_by(
        Biblioteca.nombre
    ).all()


    prestamos_activos = Prestamo.query.filter_by(
        estado="Activo"
    ).order_by(
        Prestamo.fecha_limite.asc()
    ).all()


    return render_template(
        "admin/dashboard.html",

        total_usuarios=total_usuarios,

        total_libros=total_libros,

        total_prestamos=total_prestamos,

        total_reservas=total_reservas,

        autores=autores,

        generos=generos,

        moods=moods,

        bibliotecas=bibliotecas,

        prestamos_activos=prestamos_activos
    )


# ============================================================
# ENVIAR REPORTE DE PRESTAMOS AL ADMIN
# ============================================================

@app.post("/admin/reportes/prestamos/enviar")
@rol_requerido("Administrador")
def enviar_reporte_prestamos():

    enviado = enviar_reporte_prestamos_admin()

    if enviado:

        flash(
            "Reporte de préstamos generado y enviado al correo del administrador.",
            "success"
        )

    else:

        flash(
            "No se pudo generar o enviar el reporte de préstamos.",
            "danger"
        )

    return redirect(
        url_for("admin")
    )


# ============================================================
# ENVIAR REPORTE DE LIBROS DISPONIBLES AL ADMIN
# ============================================================

@app.post("/admin/reportes/libros-disponibles/enviar")
@rol_requerido("Administrador")
def enviar_reporte_libros_disponibles():

    enviado = enviar_reporte_libros_disponibles_admin()

    if enviado:

        flash(
            "Reporte de libros disponibles enviado al correo del administrador.",
            "success"
        )

    else:

        flash(
            "No se pudo generar o enviar el reporte de libros disponibles.",
            "danger"
        )

    return redirect(
        url_for("admin")
    )


# ============================================================
# ADMIN AGREGAR LIBRO
# ============================================================

@app.post("/admin/libros/nuevo")
@rol_requerido("Administrador")
def admin_nuevo_libro():

    titulo = request.form.get(
        "titulo",
        ""
    ).strip()

    isbn = request.form.get(
        "isbn",
        ""
    ).strip()

    descripcion = request.form.get(
        "descripcion",
        ""
    ).strip()

    portada = request.form.get(
        "portada",
        ""
    ).strip() or None

    formato = request.form.get(
        "formato",
        "Fisico"
    ).strip()


    id_autor = request.form.get(
        "id_autor",
        type=int
    )

    nuevo_autor_nombres = request.form.get(
        "nuevo_autor_nombres",
        ""
    ).strip()

    nuevo_autor_apellidos = request.form.get(
        "nuevo_autor_apellidos",
        ""
    ).strip()


    id_genero = request.form.get(
        "id_genero",
        type=int
    )

    id_mood = request.form.get(
        "id_mood",
        type=int
    )


    anio_texto = request.form.get(
        "anio_publicacion",
        ""
    ).strip()

    anio_publicacion = (
        int(anio_texto)
        if anio_texto.isdigit()
        else None
    )


    id_biblioteca = request.form.get(
        "id_biblioteca",
        type=int
    )

    codigo = request.form.get(
        "codigo",
        ""
    ).strip()

    pasillo = request.form.get(
        "pasillo",
        ""
    ).strip()

    estante = request.form.get(
        "estante",
        ""
    ).strip()


    if not titulo or not isbn or not id_genero:

        flash(
            "Título, ISBN y género son obligatorios.",
            "warning"
        )

        return redirect(
            url_for("admin")
        )


    if formato not in (
        "Fisico",
        "Digital",
        "Audiolibro"
    ):

        flash(
            "El formato seleccionado no es válido.",
            "warning"
        )

        return redirect(
            url_for("admin")
        )


    if MaterialBibliografico.query.filter_by(
        isbn=isbn
    ).first():

        flash(
            "Ya existe un libro con ese ISBN.",
            "danger"
        )

        return redirect(
            url_for("admin")
        )


    if formato == "Fisico" and codigo:

        if not id_biblioteca:

            flash(
                "Para crear el ejemplar físico debes elegir una biblioteca.",
                "warning"
            )

            return redirect(
                url_for("admin")
            )


        if Ejemplar.query.filter_by(
            codigo=codigo
        ).first():

            flash(
                "Ya existe un ejemplar con ese código.",
                "danger"
            )

            return redirect(
                url_for("admin")
            )


    try:

        if not id_autor:

            if not nuevo_autor_nombres or not nuevo_autor_apellidos:

                flash(
                    "Selecciona un autor existente o escribe el nombre y apellido del nuevo autor.",
                    "warning"
                )

                return redirect(
                    url_for("admin")
                )


            autor_existente = Autor.query.filter(
                func.lower(
                    Autor.nombres
                ) == nuevo_autor_nombres.lower(),

                func.lower(
                    Autor.apellidos
                ) == nuevo_autor_apellidos.lower()
            ).first()


            if autor_existente:

                id_autor = autor_existente.id_autor


            else:

                db.session.execute(
                    text(
                        "CALL sp_registrar_autor("
                        ":nombres, :apellidos, :nacionalidad)"
                    ),
                    {
                        "nombres": nuevo_autor_nombres,
                        "apellidos": nuevo_autor_apellidos,
                        "nacionalidad": None
                    }
                )

                db.session.flush()


                nuevo_autor = Autor.query.filter(
                    func.lower(
                        Autor.nombres
                    ) == nuevo_autor_nombres.lower(),

                    func.lower(
                        Autor.apellidos
                    ) == nuevo_autor_apellidos.lower()
                ).first()


                if not nuevo_autor:

                    db.session.rollback()

                    flash(
                        "No se pudo registrar el nuevo autor.",
                        "danger"
                    )

                    return redirect(
                        url_for("admin")
                    )


                id_autor = nuevo_autor.id_autor


        db.session.execute(
            text(
                "CALL sp_registrar_libro("
                ":titulo, :isbn, :descripcion, :anio, "
                ":portada, :formato, :autor, :genero)"
            ),
            {
                "titulo": titulo,
                "isbn": isbn,
                "descripcion": descripcion,
                "anio": anio_publicacion,
                "portada": portada,
                "formato": formato,
                "autor": id_autor,
                "genero": id_genero
            }
        )

        db.session.flush()


        libro = MaterialBibliografico.query.filter_by(
            isbn=isbn
        ).first()


        if not libro:

            db.session.rollback()

            flash(
                "No se pudo encontrar el libro después de registrarlo.",
                "danger"
            )

            return redirect(
                url_for("admin")
            )


        # ====================================================
        # ASIGNACION AUTOMATICA DEL MOOD SEGUN EL GENERO
        # ====================================================

        if not id_mood:

            genero_libro = db.session.get(
                Genero,
                id_genero
            )


            if genero_libro:

                genero_nombre = genero_libro.nombre.strip().lower()


                relaciones_mood = {
                    "romance": "Romantico",
                    "terror": "Intenso",
                    "distopia": "Intenso",
                    "drama": "Intenso",
                    "aventura": "Feliz",
                    "realismo magico": "Relajado",
                    "ficcion": "Relajado",
                    "clasico": "Aprender"
                }


                nombre_mood = relaciones_mood.get(
                    genero_nombre
                )


                if nombre_mood:

                    mood_automatico = Mood.query.filter(
                        func.lower(
                            Mood.nombre
                        ) == nombre_mood.lower()
                    ).first()


                    if mood_automatico:

                        id_mood = mood_automatico.id_mood


        # ====================================================
        # GUARDAR RELACION LIBRO - MOOD
        # ====================================================

        if id_mood:

            relacion_existente = LibroMood.query.filter_by(
                id_libro=libro.id_libro,
                id_mood=id_mood
            ).first()


            if not relacion_existente:

                db.session.execute(
                    text(
                        "CALL sp_asignar_mood_libro("
                        ":libro, :mood)"
                    ),
                    {
                        "libro": libro.id_libro,
                        "mood": id_mood
                    }
                )


        # ====================================================
        # CREAR EJEMPLAR FISICO
        # ====================================================

        if formato == "Fisico" and codigo:

            db.session.execute(
                text(
                    "CALL sp_registrar_ejemplar("
                    ":libro, :biblioteca, :codigo, "
                    ":pasillo, :estante)"
                ),
                {
                    "libro": libro.id_libro,
                    "biblioteca": id_biblioteca,
                    "codigo": codigo,
                    "pasillo": pasillo or None,
                    "estante": estante or None
                }
            )


        db.session.commit()


        flash(
            "Libro agregado correctamente al catálogo y Mood Search.",
            "success"
        )


    except SQLAlchemyError as error:

        db.session.rollback()

        print(
            "ERROR AL AGREGAR LIBRO:",
            error
        )

        flash(
            "No se pudo agregar el libro. Revisa los datos ingresados.",
            "danger"
        )


    return redirect(
        url_for("admin")
    )


# ============================================================
# ADMIN DEVOLVER LIBRO
# ============================================================

@app.post("/admin/prestamo/<int:id_prestamo>/devolver")
@rol_requerido("Administrador")
def admin_devolver_prestamo(id_prestamo):

    prestamo = db.get_or_404(
        Prestamo,
        id_prestamo
    )

    if prestamo.estado != "Activo":

        flash(
            "Ese préstamo ya no está activo.",
            "warning"
        )

        return redirect(
            url_for("admin")
        )

    try:

        correo_enviado = procesar_devolucion(
            prestamo
        )

        if correo_enviado:

            flash(
                "Préstamo marcado como devuelto y usuario notificado por correo.",
                "success"
            )

        else:

            flash(
                "Préstamo devuelto, pero el correo no pudo enviarse.",
                "warning"
            )


    except SQLAlchemyError as error:

        db.session.rollback()

        print(
            "ERROR DEVOLUCION ADMIN:",
            error
        )

        flash(
            "No se pudo completar la devolución.",
            "danger"
        )


    return redirect(
        url_for("admin")
    )


# ============================================================
# ERROR 404
# ============================================================

@app.errorhandler(404)
def pagina_no_encontrada(error):

    return render_template(
        "error.html",
        codigo=404,
        mensaje="La página que buscas no existe."
    ), 404


# ============================================================
# ERROR 500
# ============================================================

@app.errorhandler(500)
def error_interno(error):

    db.session.rollback()

    return render_template(
        "error.html",
        codigo=500,
        mensaje="Ocurrió un error interno en BiblioTEC."
    ), 500


# ============================================================
# EJECUTAR
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)