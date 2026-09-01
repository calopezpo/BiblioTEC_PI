import os
import smtplib

from io import BytesIO
from email.message import EmailMessage

from sqlalchemy import text

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)

from models import db, Usuario


# ============================================================
# OBTENER REPORTE GENERAL DE PRESTAMOS
# ============================================================

def obtener_reporte_prestamos():

    consulta = text("""
        SELECT
            p.id_prestamo,
            u.nombres || ' ' || u.apellidos AS usuario,
            u.correo,
            l.titulo AS libro,
            a.nombres || ' ' || a.apellidos AS autor,
            b.nombre AS biblioteca,
            e.codigo AS codigo_ejemplar,
            p.fecha_prestamo,
            p.fecha_limite,
            p.fecha_devolucion,
            p.estado
        FROM prestamos p
        INNER JOIN usuarios u
            ON p.id_usuario = u.id_usuario
        INNER JOIN ejemplares e
            ON p.id_ejemplar = e.id_ejemplar
        INNER JOIN libros l
            ON e.id_libro = l.id_libro
        INNER JOIN autores a
            ON l.id_autor = a.id_autor
        INNER JOIN bibliotecas b
            ON e.id_biblioteca = b.id_biblioteca
        ORDER BY p.fecha_prestamo DESC;
    """)

    resultado = db.session.execute(consulta)

    return resultado.mappings().all()


# ============================================================
# GENERAR PDF DEL REPORTE
# ============================================================

def generar_pdf_reporte_prestamos():

    prestamos = obtener_reporte_prestamos()

    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1 * cm,
        leftMargin=1 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm
    )

    estilos = getSampleStyleSheet()

    elementos = []

    titulo = Paragraph(
        "<b>BiblioTEC - Reporte General de Préstamos</b>",
        estilos["Title"]
    )

    descripcion = Paragraph(
        "Reporte administrativo generado automáticamente por BiblioTEC. "
        "Incluye información de usuarios, libros, autores, ejemplares, "
        "bibliotecas y préstamos.",
        estilos["Normal"]
    )

    elementos.append(titulo)
    elementos.append(Spacer(1, 0.3 * cm))
    elementos.append(descripcion)
    elementos.append(Spacer(1, 0.6 * cm))


    encabezados = [
        "ID",
        "Usuario",
        "Correo",
        "Libro",
        "Autor",
        "Biblioteca",
        "Ejemplar",
        "Préstamo",
        "Límite",
        "Devolución",
        "Estado"
    ]

    datos = [encabezados]


    for prestamo in prestamos:

        fecha_prestamo = (
            prestamo["fecha_prestamo"].strftime("%d/%m/%Y")
            if prestamo["fecha_prestamo"]
            else "-"
        )

        fecha_limite = (
            prestamo["fecha_limite"].strftime("%d/%m/%Y")
            if prestamo["fecha_limite"]
            else "-"
        )

        fecha_devolucion = (
            prestamo["fecha_devolucion"].strftime("%d/%m/%Y")
            if prestamo["fecha_devolucion"]
            else "-"
        )


        datos.append([
            str(prestamo["id_prestamo"]),
            prestamo["usuario"],
            prestamo["correo"],
            prestamo["libro"],
            prestamo["autor"],
            prestamo["biblioteca"],
            prestamo["codigo_ejemplar"],
            fecha_prestamo,
            fecha_limite,
            fecha_devolucion,
            prestamo["estado"]
        ])


    if not prestamos:

        datos.append([
            "-",
            "No existen préstamos registrados",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-"
        ])


    tabla = Table(
        datos,
        repeatRows=1,
        colWidths=[
            1 * cm,
            2.7 * cm,
            4 * cm,
            3.2 * cm,
            3 * cm,
            2.8 * cm,
            2 * cm,
            2 * cm,
            2 * cm,
            2 * cm,
            1.8 * cm
        ]
    )


    tabla.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#172033")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.HexColor("#F3D77A")
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, 0),
                7
            ),

            (
                "FONTSIZE",
                (0, 1),
                (-1, -1),
                6.5
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.grey
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "ALIGN",
                (0, 0),
                (0, -1),
                "CENTER"
            ),

            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#F1F5F9")
                ]
            )
        ])
    )


    elementos.append(tabla)

    documento.build(elementos)

    pdf = buffer.getvalue()

    buffer.close()

    return pdf


# ============================================================
# ENVIAR PDF AL CORREO DEL ADMINISTRADOR
# ============================================================

def enviar_reporte_prestamos_admin():

    admin = Usuario.query.filter_by(
        rol="Administrador",
        estado="Activo"
    ).first()


    if not admin:

        print("ERROR: No existe un administrador activo.")

        return False


    if not admin.correo:

        print("ERROR: El administrador no tiene correo registrado.")

        return False


    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")

    if not email_user or not email_password:

        print("ERROR: Faltan EMAIL_USER o EMAIL_PASSWORD en el archivo .env")

        return False


    try:

        pdf = generar_pdf_reporte_prestamos()


        mensaje = EmailMessage()

        mensaje["Subject"] = "BiblioTEC - Reporte general de préstamos"

        mensaje["From"] = (
            f'{os.getenv("EMAIL_FROM_NAME", "BiblioTEC")} '
            f'<{email_user}>'
        )

        mensaje["To"] = admin.correo


        mensaje.set_content(
            f"""Hola {admin.nombres},

BiblioTEC generó correctamente el reporte general de préstamos.

En este correo encontrarás adjunto el documento PDF con información de:

- Usuarios
- Libros
- Autores
- Ejemplares
- Bibliotecas
- Fechas de préstamo
- Fechas de devolución
- Estado de los préstamos

Este reporte fue generado automáticamente por el sistema BiblioTEC.

BiblioTEC
Sistema de gestión bibliográfica
"""
        )


        mensaje.add_attachment(
            pdf,
            maintype="application",
            subtype="pdf",
            filename="Reporte_Prestamos_BiblioTEC.pdf"
        )


        host = os.getenv(
            "EMAIL_HOST",
            "smtp.gmail.com"
        )

        port = int(
            os.getenv(
                "EMAIL_PORT",
                "587"
            )
        )


        with smtplib.SMTP(
            host,
            port
        ) as servidor:

            servidor.starttls()

            servidor.login(
                email_user,
                email_password
            )

            servidor.send_message(
                mensaje
            )


        print(
            f"Reporte enviado correctamente a: {admin.correo}"
        )

        return True


    except Exception as error:

        print(
            "ERROR AL ENVIAR REPORTE:",
            error
        )

        return False

    # ============================================================
# OBTENER REPORTE DE LIBROS DISPONIBLES
# ============================================================

def obtener_reporte_libros_disponibles():

    consulta = text("""
        SELECT
            l.id_libro,
            l.titulo,
            a.nombres || ' ' || a.apellidos AS autor,
            g.nombre AS genero,
            l.formato,
            b.nombre AS biblioteca,
            e.codigo AS codigo_ejemplar,
            e.pasillo,
            e.estante,
            e.estado
        FROM ejemplares e
        INNER JOIN libros l
            ON e.id_libro = l.id_libro
        INNER JOIN autores a
            ON l.id_autor = a.id_autor
        INNER JOIN generos g
            ON l.id_genero = g.id_genero
        INNER JOIN bibliotecas b
            ON e.id_biblioteca = b.id_biblioteca
        WHERE e.estado = 'Disponible'
          AND l.estado = 'Activo'
          AND b.estado = 'Activa'
        ORDER BY l.titulo ASC;
    """)

    resultado = db.session.execute(consulta)

    return resultado.mappings().all()


# ============================================================
# GENERAR PDF DE LIBROS DISPONIBLES
# ============================================================

def generar_pdf_libros_disponibles():

    libros = obtener_reporte_libros_disponibles()

    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1 * cm,
        leftMargin=1 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm
    )

    estilos = getSampleStyleSheet()

    elementos = []

    titulo = Paragraph(
        "<b>BiblioTEC - Reporte de Libros Disponibles</b>",
        estilos["Title"]
    )

    descripcion = Paragraph(
        "Reporte administrativo de ejemplares disponibles actualmente "
        "en las bibliotecas registradas en BiblioTEC.",
        estilos["Normal"]
    )

    elementos.append(titulo)
    elementos.append(Spacer(1, 0.3 * cm))
    elementos.append(descripcion)
    elementos.append(Spacer(1, 0.6 * cm))


    encabezados = [
        "ID",
        "Libro",
        "Autor",
        "Género",
        "Formato",
        "Biblioteca",
        "Código",
        "Pasillo",
        "Estante",
        "Estado"
    ]

    datos = [encabezados]


    for libro in libros:

        datos.append([
            str(libro["id_libro"]),
            libro["titulo"],
            libro["autor"],
            libro["genero"],
            libro["formato"],
            libro["biblioteca"],
            libro["codigo_ejemplar"],
            libro["pasillo"] or "-",
            libro["estante"] or "-",
            libro["estado"]
        ])


    if not libros:

        datos.append([
            "-",
            "No existen libros disponibles",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-"
        ])


    tabla = Table(
        datos,
        repeatRows=1,
        colWidths=[
            1 * cm,
            4.2 * cm,
            3.5 * cm,
            2.4 * cm,
            2.2 * cm,
            3.5 * cm,
            2.2 * cm,
            1.8 * cm,
            1.8 * cm,
            2 * cm
        ]
    )


    tabla.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#172033")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.HexColor("#F3D77A")
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, 0),
                7
            ),

            (
                "FONTSIZE",
                (0, 1),
                (-1, -1),
                7
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.grey
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#F1F5F9")
                ]
            )
        ])
    )


    elementos.append(tabla)

    documento.build(elementos)

    pdf = buffer.getvalue()

    buffer.close()

    return pdf


# ============================================================
# ENVIAR REPORTE DE LIBROS DISPONIBLES AL ADMIN
# ============================================================

def enviar_reporte_libros_disponibles_admin():

    admin = Usuario.query.filter_by(
        rol="Administrador",
        estado="Activo"
    ).first()

    if not admin:
        print("ERROR: No existe un administrador activo.")
        return False

    if not admin.correo:
        print("ERROR: El administrador no tiene correo registrado.")
        return False


    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")

    if not email_user or not email_password:
        print("ERROR: Faltan EMAIL_USER o EMAIL_PASSWORD en .env")
        return False


    try:

        pdf = generar_pdf_libros_disponibles()

        mensaje = EmailMessage()

        mensaje["Subject"] = "BiblioTEC - Reporte de libros disponibles"

        mensaje["From"] = (
            f'{os.getenv("EMAIL_FROM_NAME", "BiblioTEC")} '
            f'<{email_user}>'
        )

        mensaje["To"] = admin.correo


        mensaje.set_content(
            f"""Hola {admin.nombres},

Adjunto se encuentra el reporte actualizado de libros disponibles en BiblioTEC.

El documento contiene:

- Título del libro
- Autor
- Género
- Formato
- Biblioteca
- Código del ejemplar
- Pasillo
- Estante
- Estado

El reporte incluye únicamente ejemplares actualmente disponibles.

BiblioTEC
Sistema de gestión bibliográfica
"""
        )


        mensaje.add_attachment(
            pdf,
            maintype="application",
            subtype="pdf",
            filename="Reporte_Libros_Disponibles_BiblioTEC.pdf"
        )


        host = os.getenv(
            "EMAIL_HOST",
            "smtp.gmail.com"
        )

        port = int(
            os.getenv(
                "EMAIL_PORT",
                "587"
            )
        )


        with smtplib.SMTP(host, port) as servidor:

            servidor.starttls()

            servidor.login(
                email_user,
                email_password
            )

            servidor.send_message(mensaje)


        print(
            f"Reporte de libros disponibles enviado a: {admin.correo}"
        )

        return True


    except Exception as error:

        print(
            "ERROR AL ENVIAR REPORTE DE LIBROS DISPONIBLES:",
            error
        )

        return False