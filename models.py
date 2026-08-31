from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# =========================================================================
# USUARIOS
# =========================================================================

class Usuario(db.Model):
    __tablename__ = "usuarios"

    id_usuario = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(30), nullable=False, default="Lector")
    xp = db.Column(db.Integer, nullable=False, default=0)
    estado = db.Column(db.String(20), nullable=False, default="Activo")
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        """Guarda la contraseña como hash y no como texto plano."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Comprueba la contraseña ingresada durante el login."""
        return check_password_hash(self.password_hash, password)

    def es_admin(self):
        return self.rol == "Administrador"

    def agregar_xp(self, puntos):
        if puntos > 0:
            self.xp += puntos

    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    def __repr__(self):
        return f"<Usuario {self.correo} - {self.rol}>"


# =========================================================================
# CATÁLOGO
# =========================================================================

class Autor(db.Model):
    __tablename__ = "autores"

    id_autor = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100))
    nacionalidad = db.Column(db.String(80))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos or ''}".strip()


class Genero(db.Model):
    __tablename__ = "generos"

    id_genero = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)


class Biblioteca(db.Model):
    __tablename__ = "bibliotecas"

    id_biblioteca = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(20))
    horario = db.Column(db.String(120))
    estado = db.Column(db.String(20), nullable=False, default="Activa")
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)


class MaterialBibliografico(db.Model):
    """
    Clase padre para los materiales de BiblioTEC.
    La columna 'formato' permite aplicar herencia y polimorfismo.
    """

    __tablename__ = "libros"

    id_libro = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    anio_publicacion = db.Column(db.Integer)
    portada = db.Column(db.String(500))
    formato = db.Column(db.String(30), nullable=False, default="Fisico")
    id_autor = db.Column(db.Integer, db.ForeignKey("autores.id_autor"), nullable=False)
    id_genero = db.Column(db.Integer, db.ForeignKey("generos.id_genero"), nullable=False)
    estado = db.Column(db.String(20), nullable=False, default="Activo")
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    autor = db.relationship("Autor", backref="libros")
    genero = db.relationship("Genero", backref="libros")

    __mapper_args__ = {
        "polymorphic_on": formato,
        "polymorphic_identity": "Material"
    }

    def obtener_acceso(self):
        """Método que cada tipo de material puede redefinir."""
        return "Consultar información del material"

    def ficha(self):
        return f"{self.titulo} | {self.formato} | ISBN: {self.isbn}"

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.titulo}>"


class LibroFisico(MaterialBibliografico):
    __mapper_args__ = {"polymorphic_identity": "Fisico"}

    def obtener_acceso(self):
        return "Consultar disponibilidad y ubicación física"


class LibroDigital(MaterialBibliografico):
    __mapper_args__ = {"polymorphic_identity": "Digital"}

    def obtener_acceso(self):
        return "Abrir contenido digital"


class Audiolibro(MaterialBibliografico):
    __mapper_args__ = {"polymorphic_identity": "Audiolibro"}

    def obtener_acceso(self):
        return "Abrir reproductor de audio"


# =========================================================================
# EJEMPLARES, PRÉSTAMOS Y RESERVAS
# =========================================================================

class Ejemplar(db.Model):
    __tablename__ = "ejemplares"

    id_ejemplar = db.Column(db.Integer, primary_key=True)
    id_libro = db.Column(db.Integer, db.ForeignKey("libros.id_libro"), nullable=False)
    id_biblioteca = db.Column(db.Integer, db.ForeignKey("bibliotecas.id_biblioteca"), nullable=False)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    pasillo = db.Column(db.String(30))
    estante = db.Column(db.String(30))
    estado = db.Column(db.String(30), nullable=False, default="Disponible")
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    libro = db.relationship("MaterialBibliografico", backref="ejemplares")
    biblioteca = db.relationship("Biblioteca", backref="ejemplares")

    def esta_disponible(self):
        return self.estado == "Disponible"

    def obtener_ubicacion(self):
        return f"{self.pasillo or 'Sin pasillo'} - {self.estante or 'Sin estante'}"


class Prestamo(db.Model):
    __tablename__ = "prestamos"

    id_prestamo = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuarios.id_usuario"), nullable=False)
    id_ejemplar = db.Column(db.Integer, db.ForeignKey("ejemplares.id_ejemplar"), nullable=False)
    fecha_prestamo = db.Column(db.Date, nullable=False)
    fecha_limite = db.Column(db.Date, nullable=False)
    fecha_devolucion = db.Column(db.Date)
    estado = db.Column(db.String(20), nullable=False, default="Activo")

    usuario = db.relationship("Usuario", backref="prestamos")
    ejemplar = db.relationship("Ejemplar", backref="prestamos")

    def esta_activo(self):
        return self.estado == "Activo"

    def __repr__(self):
        return f"<Prestamo {self.id_prestamo} - {self.estado}>"


class Reserva(db.Model):
    __tablename__ = "reservas"

    id_reserva = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuarios.id_usuario"), nullable=False)
    id_libro = db.Column(db.Integer, db.ForeignKey("libros.id_libro"), nullable=False)
    id_biblioteca = db.Column(db.Integer, db.ForeignKey("bibliotecas.id_biblioteca"), nullable=False)
    fecha_reserva = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_expiracion = db.Column(db.DateTime, nullable=False)
    estado = db.Column(db.String(20), nullable=False, default="Activa")

    usuario = db.relationship("Usuario", backref="reservas")
    libro = db.relationship("MaterialBibliografico", backref="reservas")
    biblioteca = db.relationship("Biblioteca", backref="reservas")

    def cancelar(self):
        self.estado = "Cancelada"

    def completar(self):
        self.estado = "Completada"


# =========================================================================
# FAVORITOS Y MOOD SEARCH
# =========================================================================

class Favorito(db.Model):
    __tablename__ = "favoritos"

    id_usuario = db.Column(db.Integer, db.ForeignKey("usuarios.id_usuario"), primary_key=True)
    id_libro = db.Column(db.Integer, db.ForeignKey("libros.id_libro"), primary_key=True)
    fecha_agregado = db.Column(db.DateTime, default=datetime.utcnow)


class Mood(db.Model):
    __tablename__ = "moods"

    id_mood = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))


class LibroMood(db.Model):
    __tablename__ = "libro_mood"

    id_libro = db.Column(db.Integer, db.ForeignKey("libros.id_libro"), primary_key=True)
    id_mood = db.Column(db.Integer, db.ForeignKey("moods.id_mood"), primary_key=True)
