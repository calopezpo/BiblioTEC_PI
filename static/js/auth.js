// ==========================================================
// BiblioTEC - auth.js
// Login y registro de usuarios
// ==========================================================

document.addEventListener("DOMContentLoaded", () => {

    const loginForm = document.querySelector("#loginForm");
    const registroForm = document.querySelector("#registroForm");

    if (loginForm) {
        loginForm.addEventListener("submit", iniciarSesion);
    }

    if (registroForm) {
        registroForm.addEventListener("submit", registrarUsuario);
    }

});


// ==========================================================
// LOGIN
// ==========================================================

async function iniciarSesion(event) {

    event.preventDefault();

    const correo = document.querySelector("#correo");
    const password = document.querySelector("#password");

    if (!correo || !password) {
        return;
    }

    if (!correo.value.trim() || !password.value.trim()) {

        mostrarMensaje(
            "Completa todos los campos.",
            "error"
        );

        return;
    }

    try {

        const respuesta = await fetch("/api/login", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                correo: correo.value.trim(),
                password: password.value
            })

        });

        const resultado = await respuesta.json();

        if (!respuesta.ok) {

            mostrarMensaje(
                resultado.mensaje || "Correo o contraseña incorrectos.",
                "error"
            );

            return;
        }

        mostrarMensaje(
            "Inicio de sesión correcto.",
            "success"
        );

        setTimeout(() => {

            if (resultado.rol === "admin") {
                window.location.href = "/admin";
            } else {
                window.location.href = "/catalogo";
            }

        }, 800);

    } catch (error) {

        console.error(error);

        mostrarMensaje(
            "No se pudo conectar con el servidor.",
            "error"
        );

    }
}


// ==========================================================
// REGISTRO
// ==========================================================

async function registrarUsuario(event) {

    event.preventDefault();

    const nombres = document.querySelector("#nombres");
    const apellidos = document.querySelector("#apellidos");
    const cedula = document.querySelector("#cedula");
    const correo = document.querySelector("#correo");
    const telefono = document.querySelector("#telefono");
    const password = document.querySelector("#password");
    const confirmarPassword = document.querySelector("#confirmarPassword");

    if (
        !nombres ||
        !apellidos ||
        !cedula ||
        !correo ||
        !password ||
        !confirmarPassword
    ) {
        return;
    }


    // ------------------------------------------------------
    // VALIDACIÓN
    // ------------------------------------------------------

    if (
        !nombres.value.trim() ||
        !apellidos.value.trim() ||
        !cedula.value.trim() ||
        !correo.value.trim() ||
        !password.value.trim()
    ) {

        mostrarMensaje(
            "Completa todos los campos obligatorios.",
            "error"
        );

        return;
    }


    // ------------------------------------------------------
    // VALIDAR CONTRASEÑAS
    // ------------------------------------------------------

    if (password.value !== confirmarPassword.value) {

        mostrarMensaje(
            "Las contraseñas no coinciden.",
            "error"
        );

        return;
    }


    // ------------------------------------------------------
    // VALIDAR CORREO
    // ------------------------------------------------------

    const expresionCorreo =
        /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!expresionCorreo.test(correo.value)) {

        mostrarMensaje(
            "Ingresa un correo electrónico válido.",
            "error"
        );

        return;
    }


    // ------------------------------------------------------
    // ENVIAR AL BACKEND
    // ------------------------------------------------------

    try {

        const respuesta = await fetch("/api/registro", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                nombres: nombres.value.trim(),
                apellidos: apellidos.value.trim(),
                cedula: cedula.value.trim(),
                correo: correo.value.trim(),
                telefono: telefono
                    ? telefono.value.trim()
                    : "",
                password: password.value

            })

        });


        const resultado = await respuesta.json();


        if (!respuesta.ok) {

            mostrarMensaje(
                resultado.mensaje || "No se pudo registrar el usuario.",
                "error"
            );

            return;
        }


        mostrarMensaje(
            "Usuario registrado correctamente.",
            "success"
        );


        setTimeout(() => {

            window.location.href = "/login";

        }, 1000);


    } catch (error) {

        console.error(error);

        mostrarMensaje(
            "Error de conexión con el servidor.",
            "error"
        );

    }
}


// ==========================================================
// CERRAR SESIÓN
// ==========================================================

async function cerrarSesion() {

    try {

        await fetch("/api/logout", {
            method: "POST"
        });

        window.location.href = "/";

    } catch (error) {

        console.error(error);

        window.location.href = "/";

    }
}