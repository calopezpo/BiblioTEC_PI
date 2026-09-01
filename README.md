# BiblioTEC

Proyecto integrador desarrollado con Python, Flask, PostgreSQL, HTML, CSS y JavaScript.

## Archivos principales

- `app.py`: rutas Flask y conexión entre la interfaz y PostgreSQL.
- `models.py`: clases POO y mapeo de las tablas con SQLAlchemy.
- `auth.py`: protección de rutas y roles.
- `config.py`: configuración de la conexión.
- `templates/`: vistas HTML con Jinja.
- `static/`: CSS y JavaScript.

## Configuración local

1. Crear entorno virtual:

```powershell
python -m venv venv
venv\Scripts\activate
```

2. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

3. Crear `.env` a partir de `.env.example`:

```powershell
Copy-Item .env.example .env
```

4. En `.env`, colocar las credenciales locales de PostgreSQL:

```text
SECRET_KEY=una-clave-local
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bibliotec_db
DB_USER=postgres
DB_PASSWORD=TU_PASSWORD_DE_POSTGRES
```

5. Ejecutar:

```powershell
python app.py
```

Abrir `http://127.0.0.1:5000`.

## POO aplicada

La jerarquía principal es:

```text
MaterialBibliografico
├── LibroFisico
├── LibroDigital
└── Audiolibro
```

El método `obtener_acceso()` se redefine en las subclases, demostrando polimorfismo.

`Usuario` encapsula el manejo de contraseñas mediante `set_password()` y `check_password()`.

## Seguridad

- `.env` no debe subirse a GitHub.
- `.env.example` nunca debe contener contraseñas reales.
- `venv/` y `__pycache__/` no se suben al repositorio.


## Correos de confirmación

BiblioTEC puede enviar correos cuando:

- se registra un préstamo;
- el usuario devuelve un libro;
- el administrador marca un préstamo como devuelto.

Para Gmail, configura en `.env`:

```text
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=tu_correo@gmail.com
EMAIL_PASSWORD=tu_password_de_aplicacion
EMAIL_FROM_NAME=BiblioTEC
```

Usa una contraseña de aplicación de Gmail. No coloques tu contraseña normal de Gmail y no subas `.env` a GitHub.

## Administración de libros

El administrador puede entrar a `/admin` y agregar un nuevo libro. Si el libro es físico, también puede registrar opcionalmente su primer ejemplar seleccionando biblioteca, código, pasillo y estante.
