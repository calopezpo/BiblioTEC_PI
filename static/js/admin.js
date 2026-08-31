// ==========================================================
// BiblioTEC - admin.js
// Panel administrativo
// ==========================================================

document.addEventListener("DOMContentLoaded", () => {

    cargarLibrosAdmin();
    cargarPrestamosAdmin();
    cargarUsuariosAdmin();


    const formulario =
        document.querySelector("#formNuevoLibro");


    if (formulario) {

        formulario.addEventListener(
            "submit",
            agregarLibro
        );

    }

});


// ==========================================================
// AGREGAR LIBRO
// ==========================================================

async function agregarLibro(event) {

    event.preventDefault();


    const titulo =
        document.querySelector("#titulo");

    const autor =
        document.querySelector("#autor");

    const categoria =
        document.querySelector("#categoria");

    const isbn =
        document.querySelector("#isbn");

    const editorial =
        document.querySelector("#editorial");

    const anio =
        document.querySelector("#anio");


    if (
        !titulo.value.trim() ||
        !autor.value.trim()
    ) {

        mostrarMensaje(
            "Título y autor son obligatorios.",
            "error"
        );

        return;
    }


    try {

        const respuesta =
            await fetch("/api/admin/libros", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    titulo: titulo.value.trim(),

                    autor: autor.value.trim(),

                    categoria:
                        categoria
                        ? categoria.value.trim()
                        : "",

                    isbn:
                        isbn
                        ? isbn.value.trim()
                        : "",

                    editorial:
                        editorial
                        ? editorial.value.trim()
                        : "",

                    anio:
                        anio
                        ? anio.value
                        : null

                })

            });


        const resultado =
            await respuesta.json();


        if (!respuesta.ok) {

            mostrarMensaje(
                resultado.mensaje ||
                "No se pudo agregar el libro.",
                "error"
            );

            return;
        }


        mostrarMensaje(
            "Libro agregado correctamente.",
            "success"
        );


        event.target.reset();


        cargarLibrosAdmin();


    } catch (error) {

        console.error(error);

        mostrarMensaje(
            "Error al agregar el libro.",
            "error"
        );

    }
}


// ==========================================================
// CARGAR LIBROS
// ==========================================================

async function cargarLibrosAdmin() {

    const contenedor =
        document.querySelector("#tablaLibros");


    if (!contenedor) {
        return;
    }


    try {

        const respuesta =
            await fetch("/api/admin/libros");


        const libros =
            await respuesta.json();


        contenedor.innerHTML = "";


        libros.forEach((libro) => {

            const fila =
                document.createElement("tr");


            fila.innerHTML = `

                <td>
                    ${libro.id_libro}
                </td>

                <td>
                    ${libro.titulo}
                </td>

                <td>
                    ${libro.autor}
                </td>

                <td>
                    ${libro.categoria || "N/A"}
                </td>

                <td>
                    ${libro.disponible ? "Disponible" : "Prestado"}
                </td>

                <td>

                    <button
                        class="btn-eliminar"
                        data-id="${libro.id_libro}"
                    >
                        Eliminar
                    </button>

                </td>

            `;


            contenedor.appendChild(fila);

        });


        agregarEventosEliminar();

    } catch (error) {

        console.error(error);

    }
}


// ==========================================================
// ELIMINAR LIBRO
// ==========================================================

function agregarEventosEliminar() {

    const botones =
        document.querySelectorAll(".btn-eliminar");


    botones.forEach((boton) => {

        boton.addEventListener("click", () => {

            eliminarLibro(
                boton.dataset.id
            );

        });

    });

}


async function eliminarLibro(idLibro) {

    if (
        !window.confirm(
            "¿Seguro que deseas eliminar este libro?"
        )
    ) {
        return;
    }


    try {

        const respuesta =
            await fetch(
                `/api/admin/libros/${idLibro}`,
                {
                    method: "DELETE"
                }
            );


        const resultado =
            await respuesta.json();


        if (!respuesta.ok) {

            mostrarMensaje(
                resultado.mensaje ||
                "No se pudo eliminar.",
                "error"
            );

            return;
        }


        mostrarMensaje(
            "Libro eliminado correctamente.",
            "success"
        );


        cargarLibrosAdmin();


    } catch (error) {

        console.error(error);

        mostrarMensaje(
            "Error de conexión.",
            "error"
        );

    }
}


// ==========================================================
// PRÉSTAMOS DEL SISTEMA
// ==========================================================

async function cargarPrestamosAdmin() {

    const contenedor =
        document.querySelector("#tablaPrestamos");


    if (!contenedor) {
        return;
    }


    try {

        const respuesta =
            await fetch(
                "/api/admin/prestamos"
            );


        const prestamos =
            await respuesta.json();


        contenedor.innerHTML = "";


        prestamos.forEach((prestamo) => {

            const fila =
                document.createElement("tr");


            fila.innerHTML = `

                <td>
                    ${prestamo.id_prestamo}
                </td>

                <td>
                    ${prestamo.usuario}
                </td>

                <td>
                    ${prestamo.titulo}
                </td>

                <td>
                    ${prestamo.estado}
                </td>

                <td>
                    ${formatearFecha(
                        prestamo.fecha_prestamo
                    )}
                </td>

            `;


            contenedor.appendChild(fila);

        });

    } catch (error) {

        console.error(error);

    }
}


// ==========================================================
// USUARIOS
// ==========================================================

async function cargarUsuariosAdmin() {

    const contenedor =
        document.querySelector("#tablaUsuarios");


    if (!contenedor) {
        return;
    }


    try {

        const respuesta =
            await fetch(
                "/api/admin/usuarios"
            );


        const usuarios =
            await respuesta.json();


        contenedor.innerHTML = "";


        usuarios.forEach((usuario) => {

            const fila =
                document.createElement("tr");


            fila.innerHTML = `

                <td>
                    ${usuario.id_usuario}
                </td>

                <td>
                    ${usuario.nombres}
                    ${usuario.apellidos}
                </td>

                <td>
                    ${usuario.correo}
                </td>

                <td>
                    ${usuario.rol}
                </td>

            `;


            contenedor.appendChild(fila);

        });

    } catch (error) {

        console.error(error);

    }
}


// ==========================================================
// FECHA
// ==========================================================

function formatearFecha(fecha) {

    if (!fecha) {
        return "N/A";
    }

    return new Date(fecha).toLocaleDateString(
        "es-EC"
    );
}