// ==========================================================
// BiblioTEC - catalogo.js
// Catálogo y búsqueda de libros
// ==========================================================

document.addEventListener("DOMContentLoaded", () => {

    cargarLibros();

    const formularioBusqueda =
        document.querySelector("#formBusqueda");

    if (formularioBusqueda) {

        formularioBusqueda.addEventListener(
            "submit",
            buscarLibros
        );

    }

});


// ==========================================================
// CARGAR LIBROS
// ==========================================================

async function cargarLibros() {

    try {

        const respuesta =
            await fetch("/api/libros");

        if (!respuesta.ok) {
            throw new Error("Error al cargar libros");
        }

        const libros =
            await respuesta.json();

        mostrarLibros(libros);

    } catch (error) {

        console.error(error);

        mostrarMensaje(
            "No se pudieron cargar los libros.",
            "error"
        );

    }
}


// ==========================================================
// MOSTRAR LIBROS
// ==========================================================

function mostrarLibros(libros) {

    const contenedor =
        document.querySelector("#listaLibros");

    if (!contenedor) {
        return;
    }

    contenedor.innerHTML = "";


    if (libros.length === 0) {

        contenedor.innerHTML = `
            <div class="sin-resultados">
                <h3>No encontramos libros</h3>
                <p>Prueba con otro título o autor.</p>
            </div>
        `;

        return;
    }


    libros.forEach((libro) => {

        const tarjeta =
            document.createElement("article");

        tarjeta.className = "libro-card";


        tarjeta.innerHTML = `

            <div class="libro-imagen">

                <img
                    src="${libro.imagen || '/static/img/libro-default.jpg'}"
                    alt="Portada de ${libro.titulo}"
                >

            </div>

            <div class="libro-info">

                <h3>${libro.titulo}</h3>

                <p class="autor">
                    ${libro.autor}
                </p>

                <p>
                    ${libro.categoria || "Sin categoría"}
                </p>

                <span class="disponibilidad
                    ${libro.disponible ? "disponible" : "agotado"}">

                    ${
                        libro.disponible
                        ? "Disponible"
                        : "No disponible"
                    }

                </span>

                <button
                    class="btn-prestar"
                    data-id="${libro.id_libro}"
                    ${!libro.disponible ? "disabled" : ""}
                >

                    ${
                        libro.disponible
                        ? "Solicitar préstamo"
                        : "No disponible"
                    }

                </button>

            </div>
        `;


        contenedor.appendChild(tarjeta);

    });


    agregarEventosPrestamo();
}


// ==========================================================
// BUSCAR LIBROS
// ==========================================================

async function buscarLibros(event) {

    event.preventDefault();

    const input =
        document.querySelector("#buscarLibro");

    if (!input) {
        return;
    }

    const texto =
        input.value.trim();


    if (!texto) {

        cargarLibros();

        return;
    }


    try {

        const respuesta =
            await fetch(
                `/api/libros/buscar?q=${encodeURIComponent(texto)}`
            );


        const libros =
            await respuesta.json();


        mostrarLibros(libros);


    } catch (error) {

        console.error(error);

        mostrarMensaje(
            "No se pudo realizar la búsqueda.",
            "error"
        );

    }
}


// ==========================================================
// BOTONES DE PRÉSTAMO
// ==========================================================

function agregarEventosPrestamo() {

    const botones =
        document.querySelectorAll(".btn-prestar");


    botones.forEach((boton) => {

        boton.addEventListener("click", () => {

            const idLibro =
                boton.dataset.id;

            solicitarPrestamo(idLibro);

        });

    });

}


// ==========================================================
// SOLICITAR PRÉSTAMO
// ==========================================================

async function solicitarPrestamo(idLibro) {

    const confirmar =
        window.confirm(
            "¿Deseas solicitar este libro en préstamo?"
        );


    if (!confirmar) {
        return;
    }


    try {

        const respuesta =
            await fetch("/api/prestamos", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    id_libro: idLibro
                })

            });


        const resultado =
            await respuesta.json();


        if (!respuesta.ok) {

            mostrarMensaje(
                resultado.mensaje ||
                "No se pudo realizar el préstamo.",
                "error"
            );

            return;
        }


        mostrarMensaje(
            "Préstamo realizado correctamente.",
            "success"
        );


        cargarLibros();


    } catch (error) {

        console.error(error);

        mostrarMensaje(
            "Error de conexión.",
            "error"
        );

    }
}
