from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlalchemy import text, or_

from config import Config
from models import (
    db,
    Usuario,
    MaterialBibliografico,
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
    libros = MaterialBibliografico.query.filter_by(estado="Activo").limit(6).all()
    return render_template("index.html", libros=libros)


@app.route("/catalogo")
def catalogo():
    q = request.args.get("q", "").strip()

    consulta = MaterialBibliografico.query.filter_by(estado="Activo")

    if q:
        consulta = consulta.filter(
            or_(
                MaterialBibliografico.titulo.ilike(f"%{q}%"),
                MaterialBibliografico.descripcion.ilike(f"%{q}%"),
                MaterialBibliografico.isbn.ilike(f"%{q}%")
            )
        )

    libros = consulta.order_by(MaterialBibliografico.titulo).all()
    return render_template("catalogo.html", libros=libros, q=q)


@app.route("/libro/<int:id_libro>")
def detalle_libro(id_libro):
    libro = MaterialBibliografico.query.get_or_404(id_libro)
    ejemplares = Ejemplar.query.filter_by(id_libro=id_libro).all()
    return render_template("detalle_libro.html", libro=libro, ejemplares=ejemplares)


@app.route("/mood")
def mood():
    nombre = request.args.get("mood", "").strip()

    libros = []

    if nombre:
        libros = (
            MaterialBibliografico.query
            .join(LibroMood, LibroMood.id_libro == MaterialBibliografico.id_libro)
            .join(Mood, Mood.id_mood == LibroMood.id_mood)
            .filter(Mood.nombre.ilike(nombre))
            .all()
        )

    moods = Mood.query.order_by(Mood.nombre).all()
    return render_template("mood.html", moods=moods, libros=libros, mood_actual=nombre)


@app.route("/swipe")
def swipe():
    libros = MaterialBibliografico.query.filter_by(estado="Activo").limit(10).all()
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

        # Se usa el procedimiento almacenado que ya existe en PostgreSQL.
        db.session.execute(
            text("CALL sp_registrar_usuario(:nombres, :apellidos, :correo, :password_hash)"),
            {
                "nombres": nombres,
                "apellidos": apellidos,
                "correo": correo,
                "password_hash": usuario.password_hash
            }
        )
        db.session.commit()

        flash("Cuenta creada correctamente. Ya puedes iniciar sesión.", "success")
        return redirect(url_for("login"))

    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")

        usuario = Usuario.query.filter_by(correo=correo, estado="Activo").first()

        if usuario and usuario.check_password(password):
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

    return render_template("mis_libros.html", prestamos=prestamos, reservas=reservas)


@app.route("/perfil")
@login_requerido
def perfil():
    usuario = Usuario.query.get_or_404(session["usuario_id"])
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


# =========================================================================
# INICIO DEL PROYECTO
# =========================================================================

if __name__ == "__main__":
    app.run(debug=True)
