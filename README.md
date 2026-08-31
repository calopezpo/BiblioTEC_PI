# BiblioTEC

BiblioTEC es el proyecto integrador desarrollado con Python, Flask, PostgreSQL, HTML, CSS y JavaScript.

La estructura fue simplificada para que la parte de Programación Orientada a Objetos sea fácil de entender, mantener y explicar. En lugar de tener una gran cantidad de archivos `.py`, las clases principales se encuentran reunidas en `models.py`, siguiendo el estilo trabajado en la actividad de Tienda Online con Flask.

## Estructura

```text
BiblioTEC/
│
├── app.py
├── auth.py
├── config.py
├── models.py
├── requirements.txt
├── .env.example
├── .gitignore
│
├── database/
│   └── backups/
│
├── templates/
│   ├── admin/
│   ├── base.html
│   ├── index.html
│   ├── catalogo.html
│   ├── detalle_libro.html
│   ├── login.html
│   ├── registro.html
│   ├── mis_libros.html
│   ├── perfil.html
│   ├── mood.html
│   └── swipe.html
│
└── static/
    ├── css/
    ├── js/
    └── img/
```

## ¿Qué contiene cada archivo Python?

### `app.py`
Contiene las rutas principales de Flask: inicio, catálogo, detalle de libros, registro, login, perfil, Mood Search y panel administrativo.

### `models.py`
Contiene las clases que representan el dominio del proyecto y las tablas de PostgreSQL.

Se aplica POO principalmente con:

- `MaterialBibliografico` como clase padre.
- `LibroFisico`, `LibroDigital` y `Audiolibro` como clases hijas.
- Herencia para reutilizar atributos y métodos.
- Polimorfismo mediante el método `obtener_acceso()`.
- Encapsulación de la contraseña mediante `set_password()` y `check_password()`.
- Métodos propios en `Usuario`, `Ejemplar`, `Prestamo` y `Reserva`.

### `auth.py`
Contiene los decoradores para controlar que un usuario haya iniciado sesión y para restringir el panel administrativo.

### `config.py`
Lee la configuración desde `.env` y realiza la conexión con PostgreSQL.

## Base de datos

La base utilizada es:

```text
bibliotec_db
```

Las tablas se crean y administran desde PostgreSQL/pgAdmin. SQLAlchemy se utiliza para conectar las clases de Python con esas tablas.

La carpeta:

```text
database/backups/
```

es para guardar el backup de PostgreSQL, por ejemplo:

```text
bibliotec_db.backup
```

## Preparar el proyecto

### 1. Crear el entorno virtual

```powershell
python -m venv venv
```

### 2. Activarlo en Windows

```powershell
venv\Scripts\activate
```

### 3. Instalar las dependencias

```powershell
pip install -r requirements.txt
```

### 4. Crear el archivo `.env`

Copia `.env.example` y cambia el nombre de la copia a:

```text
.env
```

Luego configura tu contraseña local de PostgreSQL:

```text
DATABASE_URL=postgresql+psycopg2://postgres:TU_PASSWORD@localhost:5432/bibliotec_db
```

El archivo `.env` está ignorado por Git para no publicar contraseñas.

### 5. Ejecutar

```powershell
python app.py
```

Luego abre:

```text
http://127.0.0.1:5000
```

## Relación con Programación Orientada a Objetos

La jerarquía principal es:

```text
MaterialBibliografico
├── LibroFisico
├── LibroDigital
└── Audiolibro
```

Ejemplo de polimorfismo:

```python
for material in materiales:
    print(material.obtener_acceso())
```

Cada objeto puede ejecutar el mismo método pero obtener un comportamiento diferente.

## Importante

Los usuarios insertados anteriormente con contraseñas como `clave_prueba_123` sirven únicamente para probar PostgreSQL. Para iniciar sesión desde Flask, crea un usuario desde el formulario de registro, porque Flask guardará la contraseña mediante hash.

No subas `.env`, contraseñas reales ni el entorno virtual `venv/` a GitHub.
