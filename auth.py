from functools import wraps
from flask import session, redirect, url_for, flash


def login_requerido(funcion):
    """Permite entrar solamente a usuarios que iniciaron sesión."""

    @wraps(funcion)
    def decorada(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Debes iniciar sesión.", "warning")
            return redirect(url_for("login"))

        return funcion(*args, **kwargs)

    return decorada


def rol_requerido(rol):
    """Restringe una ruta a un rol específico."""

    def decorador(funcion):
        @wraps(funcion)
        def decorada(*args, **kwargs):
            if "usuario_id" not in session:
                flash("Debes iniciar sesión.", "warning")
                return redirect(url_for("login"))

            if session.get("usuario_rol") != rol:
                flash("No tienes permisos para acceder a esta sección.", "danger")
                return redirect(url_for("inicio"))

            return funcion(*args, **kwargs)

        return decorada

    return decorador
