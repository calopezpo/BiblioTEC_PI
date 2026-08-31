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
    Ejemplar,
    Prestamo,
    Reserva,
    Mood,
    LibroMood
)
from auth import login_requerido, rol_requerido


app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


# =========================================================================
# RUTAS GENERALES
# =========================================================================

@app.route("/")
def inicio():
    libros = (
        MaterialBibliografico.query
        .filter_by(estado="Activo")
        .order_by(MaterialBibliografico.id_libro.desc())
        .limit(6)
        .all()
    )
    return render_template("index.html", libros=libros)


@app.route("/catalogo")
def catalogo():
    q = request.args.get("q", "").strip()

    consulta = (
        MaterialBibliografico.query
        .join(Autor, MaterialBibliografico.id_autor == Autor.id_autor)
        .join(Genero, MaterialBibliografico.id_genero == Genero.id_genero)
        .filter(MaterialBibliografico.estado == "Activo")
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

    libros = consulta.order_by(MaterialBibliografico.titulo).all()
    return render_template("catalogo.html", libros=libros, q=q)


@app.route("/libro/<int:id_libro>")
def detalle_libro(id_libro):
    libro = db.get_or_404(MaterialBibliografico, id_libro)
    ejemplares = Ejemplar.query.filter_by(id_libro=id_libro).all()
    return render_template("detalle_libro.html", libro=libro, ejemplares=ejemplares)


@app.route("/sorprendeme")
def sorprendeme():
    libro = (
        MaterialBibliografico.query
        .filter_by(estado="Activo")
        .order_by(func.random())
        .first()
    )

    if not libro:
        flash("Todavía no existen libros activos en el catálogo.", "warning")
        return redirect(url_for("catalogo"))

    return redirect(url_for("detalle_libro", id_libro=libro.id_libro))


@app.route("/mood")
def mood():
    nombre = request.args.get("mood", "").strip()
    libros = []

    if nombre:
        libros = (
            MaterialBibliografico.query
            .join(LibroMood, LibroMood.id_libro == MaterialBibliografico.id_libro)
            .join(Mood, Mood.id_mood == LibroMood.id_mood)
            .filter(
                MaterialBibliografico.estado == "Activo",
                Mood.nombre.ilike(nombre)
            )
            .order_by(MaterialBibliografico.titulo)
            .all()
        )

    moods = Mood.query.order_by(Mood.nombre).all()

    return render_template(
        "mood.html",
        moods=moods,
        libros=libros,
        mood_actual=nombre
    )


@app.route("/swipe")
def swipe():
    libros = (
        MaterialBibliografico.query
        .filter_by(estado="Activo")
        .order_by(func.random())
        .limit(10)
        .all()
    )
    return render_template("swipe.html", libros=libros)


# =========================================================================
# REGISTRO, LOGIN Y SESIÓN
# =========================================================================

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombres = request.form.get("nombres", "").strip()
        apellidos = request.form.get("apellidos", "").strip()
        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")

        if not nombres or not apellidos or not correo or not password:
            flash("Completa todos los campos.", "warning")
            return render_template("registro.html")

        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "warning")
            return render_template("registro.html")

        if Usuario.query.filter_by(correo=correo).first():
            flash("Ya existe una cuenta con ese correo.", "danger")
            return render_template("registro.html")

        usuario = Usuario(
            nombres=nombres,
            apellidos=apellidos,
            correo=correo,
            rol="Lector"
        )
        usuario.set_password(password)

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
        except SQLAlchemyError:
            db.session.rollback()
            flash("No se pudo crear la cuenta. Intenta nuevamente.", "danger")
            return render_template("registro.html")

        flash("Cuenta creada correctamente. Ya puedes iniciar sesión.", "success")
        return redirect(url_for("login"))

    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")

        usuario = Usuario.query.filter_by(correo=correo, estado="Activo").first()

        try:
            password_correcto = usuario and usuario.check_password(password)
        except ValueError:
            # Evita que usuarios de prueba con contraseña en texto plano rompan el login.
            password_correcto = False

        if password_correcto:
            session.clear()
            session["usuario_id"] = usuario.id_usuario
            session["usuario_nombre"] = usuario.nombres
            session["usuario_rol"] = usuario.rol

            flash(f"Bienvenido, {usuario.nombres}.", "success")

            if usuario.es_admin():
                return redirect(url_for("admin"))

            return redirect(url_for("inicio"))

        flash("Correo o contraseña incorrectos.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("inicio"))


# =========================================================================
# PRÉSTAMOS Y RESERVAS
# =========================================================================

@app.post("/prestamo/<int:id_ejemplar>")
@login_requerido
def realizar_prestamo(id_ejemplar):
    ejemplar = db.get_or_404(Ejemplar, id_ejemplar)

    if ejemplar.estado != "Disponible":
        flash("Ese ejemplar no está disponible.", "warning")
        return redirect(url_for("detalle_libro", id_libro=ejemplar.id_libro))

    try:
        db.session.execute(
            text("CALL sp_realizar_prestamo(:usuario, :ejemplar)"),
            {
                "usuario": session["usuario_id"],
                "ejemplar": id_ejemplar
            }
        )
        db.session.commit()
        flash("Préstamo registrado correctamente.", "success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("No se pudo registrar el préstamo.", "danger")

    return redirect(url_for("detalle_libro", id_libro=ejemplar.id_libro))


@app.post("/prestamo/<int:id_prestamo>/devolver")
@login_requerido
def devolver_prestamo(id_prestamo):
    prestamo = db.get_or_404(Prestamo, id_prestamo)

    if prestamo.id_usuario != session["usuario_id"] and session.get("usuario_rol") != "Administrador":
        flash("No tienes permisos para devolver este préstamo.", "danger")
        return redirect(url_for("mis_libros"))

    if prestamo.estado != "Activo":
        flash("Este préstamo ya no está activo.", "warning")
        return redirect(url_for("mis_libros"))

    try:
        db.session.execute(
            text("CALL sp_devolver_libro(:prestamo)"),
            {"prestamo": id_prestamo}
        )
        db.session.commit()
        flash("Libro devuelto correctamente. Se agregaron tus XP.", "success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("No se pudo registrar la devolución.", "danger")

    return redirect(url_for("mis_libros"))


@app.post("/reserva/<int:id_libro>/<int:id_biblioteca>")
@login_requerido
def realizar_reserva(id_libro, id_biblioteca):
    libro = db.get_or_404(MaterialBibliografico, id_libro)

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
        flash("Reserva registrada correctamente.", "success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("No se pudo registrar la reserva.", "danger")

    return redirect(url_for("detalle_libro", id_libro=libro.id_libro))


# =========================================================================
# USUARIO
# =========================================================================

@app.route("/mis-libros")
@login_requerido
def mis_libros():
    usuario_id = session["usuario_id"]

    prestamos = (
        Prestamo.query
        .filter_by(id_usuario=usuario_id)
        .order_by(Prestamo.id_prestamo.desc())
        .all()
    )

    reservas = (
        Reserva.query
        .filter_by(id_usuario=usuario_id)
        .order_by(Reserva.id_reserva.desc())
        .all()
    )

    return render_template(
        "mis_libros.html",
        prestamos=prestamos,
        reservas=reservas
    )


@app.route("/perfil")
@login_requerido
def perfil():
    usuario = db.get_or_404(Usuario, session["usuario_id"])
    return render_template("perfil.html", usuario=usuario)


# =========================================================================
# ADMINISTRADOR
# =========================================================================

@app.route("/admin")
@rol_requerido("Administrador")
def admin():
    total_usuarios = Usuario.query.count()
    total_libros = MaterialBibliografico.query.count()
    total_prestamos = Prestamo.query.count()
    total_reservas = Reserva.query.count()

    return render_template(
        "admin/dashboard.html",
        total_usuarios=total_usuarios,
        total_libros=total_libros,
        total_prestamos=total_prestamos,
        total_reservas=total_reservas
    )


@app.errorhandler(404)
def pagina_no_encontrada(error):
    return render_template(
        "error.html",
        codigo=404,
        mensaje="La página que buscas no existe."
    ), 404


@app.errorhandler(500)
def error_interno(error):
    db.session.rollback()
    return render_template(
        "error.html",
        codigo=500,
        mensaje="Ocurrió un error interno en BiblioTEC."
    ), 500


if __name__ == "__main__":
    app.run(debug=True)
