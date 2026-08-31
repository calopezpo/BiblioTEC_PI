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
