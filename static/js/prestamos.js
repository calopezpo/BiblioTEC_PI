// ==========================================================
// BiblioTEC - prestamos.js
// Gestión de préstamos del usuario
// ==========================================================

document.addEventListener("DOMContentLoaded", () => {

    cargarPrestamos();

});


// ==========================================================
// CARGAR PRÉSTAMOS
// ==========================================================

async function cargarPrestamos() {

    try {

        const respuesta =
            await fetch("/api/mis-prestamos");


        if (!respuesta.ok) {
            throw new Error(
                "No se pudieron cargar los préstamos"
            );
        }


        const prestamos =
            await respuesta.json();


        mostrarPrestamos(prestamos);


    } catch (error) {

        console.error(error);

        mostrarMensaje(
            "No se pudieron cargar tus préstamos.",
            "error"
        );

    }
}


// ==========================================================
// MOSTRAR PRÉSTAMOS
// ==========================================================

function mostrarPrestamos(prestamos) {

    const contenedor =
        document.querySelector("#listaPrestamos");


    if (!contenedor) {
        return;
    }


    contenedor.innerHTML = "";


    if (prestamos.length === 0) {

        contenedor.innerHTML = `
            <div class="sin-resultados">

                <h3>No tienes préstamos</h3>

                <p>
                    Cuando solicites un libro,
                    aparecerá aquí.
                </p>

            </div>
        `;

        return;
    }


    prestamos.forEach((prestamo) => {

        const elemento =
            document.createElement("div");

        elemento.className = "prestamo-card";


        elemento.innerHTML = `

            <div>

                <h3>
                    ${prestamo.titulo}
                </h3>

                <p>
                    Autor: ${prestamo.autor}
                </p>

                <p>
                    Fecha de préstamo:
                    ${formatearFecha(prestamo.fecha_prestamo)}
                </p>

                <p>
                    Fecha límite:
                    ${formatearFecha(prestamo.fecha_devolucion)}
                </p>

            </div>

            <div>

                <span class="estado-prestamo">
                    ${prestamo.estado}
                </span>

                ${
                    prestamo.estado === "ACTIVO"
                    ? `
                        <button
                            class="btn-devolver"
                            data-id="${prestamo.id_prestamo}"
                        >
                            Devolver libro
                        </button>
                    `
                    : ""
                }

            </div>
        `;


        contenedor.appendChild(elemento);

    });


    agregarEventosDevolucion();
}


// ==========================================================
// DEVOLUCIÓN
// ==========================================================

function agregarEventosDevolucion() {

    const botones =
        document.querySelectorAll(".btn-devolver");


    botones.forEach((boton) => {

        boton.addEventListener("click", () => {

            const idPrestamo =
                boton.dataset.id;

            devolverLibro(idPrestamo);

        });

    });

}


// ==========================================================
// DEVOLVER LIBRO
// ==========================================================

async function devolverLibro(idPrestamo) {

    if (
        !window.confirm(
            "¿Confirmas que deseas devolver este libro?"
        )
    ) {
        return;
    }


    try {

        const respuesta =
            await fetch(
                `/api/prestamos/${idPrestamo}/devolver`,
                {
                    method: "PUT"
                }
            );


        const resultado =
            await respuesta.json();


        if (!respuesta.ok) {

            mostrarMensaje(
                resultado.mensaje ||
                "No se pudo devolver el libro.",
                "error"
            );

            return;
        }


        mostrarMensaje(
            "Libro devuelto correctamente.",
            "success"
        );


        cargarPrestamos();


    } catch (error) {

        console.error(error);

        mostrarMensaje(
            "Error de conexión.",
            "error"
        );

    }
}


// ==========================================================
// FORMATEAR FECHA
// ==========================================================

function formatearFecha(fecha) {

    if (!fecha) {
        return "Sin fecha";
    }

    const fechaObjeto =
        new Date(fecha);


    return fechaObjeto.toLocaleDateString(
        "es-EC",
        {
            year: "numeric",
            month: "long",
            day: "numeric"
        }
    );
}