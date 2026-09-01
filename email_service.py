import os
import smtplib
from email.message import EmailMessage
from html import escape


def _configuracion_correo():
    return {
        "host": os.getenv("EMAIL_HOST", "smtp.gmail.com"),
        "port": int(os.getenv("EMAIL_PORT", "587")),
        "user": os.getenv("EMAIL_USER", "").strip(),
        "password": os.getenv("EMAIL_PASSWORD", "").strip(),
        "from_name": os.getenv("EMAIL_FROM_NAME", "BiblioTEC").strip()
    }


def _enviar(destinatario, asunto, texto, html):
    """
    Envía un correo usando SMTP.
    Devuelve True si se envió y False si no hay configuración o falla SMTP.
    """
    config = _configuracion_correo()

    if not config["user"] or not config["password"] or not destinatario:
        print("Correo no enviado: faltan EMAIL_USER / EMAIL_PASSWORD / destinatario.")
        return False

    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = f'{config["from_name"]} <{config["user"]}>'
    mensaje["To"] = destinatario
    mensaje.set_content(texto)
    mensaje.add_alternative(html, subtype="html")

    try:
        with smtplib.SMTP(config["host"], config["port"], timeout=20) as servidor:
            servidor.ehlo()
            servidor.starttls()
            servidor.ehlo()
            servidor.login(config["user"], config["password"])
            servidor.send_message(mensaje)

        return True

    except (smtplib.SMTPException, OSError) as error:
        print(f"Error enviando correo: {error}")
        return False


def enviar_correo_prestamo(prestamo):
    if not prestamo:
        return False

    usuario = prestamo.usuario
    ejemplar = prestamo.ejemplar
    libro = ejemplar.libro
    biblioteca = ejemplar.biblioteca

    asunto = "BiblioTEC - Préstamo confirmado"

    texto = (
        f"Hola {usuario.nombres},\n\n"
        "Tu préstamo fue registrado correctamente.\n\n"
        f"Libro: {libro.titulo}\n"
        f"Biblioteca: {biblioteca.nombre}\n"
        f"Dirección: {biblioteca.direccion}\n"
        f"Fecha de préstamo: {prestamo.fecha_prestamo}\n"
        f"Fecha límite: {prestamo.fecha_limite}\n\n"
        "Recuerda devolver el libro dentro de la fecha indicada.\n\n"
        "BiblioTEC"
    )

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:620px;margin:auto">
        <h2 style="color:#b38b16">BiblioTEC</h2>
        <p>Hola <strong>{escape(usuario.nombres)}</strong>,</p>
        <p>Tu préstamo fue registrado correctamente.</p>

        <div style="padding:16px;border:1px solid #ddd;border-radius:10px">
            <p><strong>Libro:</strong> {escape(libro.titulo)}</p>
            <p><strong>Biblioteca:</strong> {escape(biblioteca.nombre)}</p>
            <p><strong>Dirección:</strong> {escape(biblioteca.direccion)}</p>
            <p><strong>Fecha de préstamo:</strong> {prestamo.fecha_prestamo}</p>
            <p><strong>Fecha límite:</strong> {prestamo.fecha_limite}</p>
        </div>

        <p>Recuerda devolver el libro dentro de la fecha indicada.</p>
        <p>Gracias por utilizar BiblioTEC.</p>
    </div>
    """

    return _enviar(usuario.correo, asunto, texto, html)


def enviar_correo_devolucion(prestamo):
    if not prestamo:
        return False

    usuario = prestamo.usuario
    libro = prestamo.ejemplar.libro

    asunto = "BiblioTEC - Devolución confirmada"

    texto = (
        f"Hola {usuario.nombres},\n\n"
        "Confirmamos que tu libro fue devuelto correctamente.\n\n"
        f"Libro: {libro.titulo}\n"
        f"Fecha de devolución: {prestamo.fecha_devolucion}\n"
        f"Estado del préstamo: {prestamo.estado}\n\n"
        "Ya no tienes pendiente la devolución de este préstamo.\n\n"
        "BiblioTEC"
    )

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:620px;margin:auto">
        <h2 style="color:#b38b16">BiblioTEC</h2>
        <p>Hola <strong>{escape(usuario.nombres)}</strong>,</p>
        <p>Confirmamos que tu libro fue devuelto correctamente.</p>

        <div style="padding:16px;border:1px solid #ddd;border-radius:10px">
            <p><strong>Libro:</strong> {escape(libro.titulo)}</p>
            <p><strong>Fecha de devolución:</strong> {prestamo.fecha_devolucion}</p>
            <p><strong>Estado:</strong> {escape(prestamo.estado)}</p>
        </div>

        <p><strong>Ya no tienes pendiente la devolución de este préstamo.</strong></p>
        <p>Gracias por utilizar BiblioTEC.</p>
    </div>
    """

    return _enviar(usuario.correo, asunto, texto, html)
