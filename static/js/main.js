document.addEventListener("DOMContentLoaded", () => {

    // SWIPE & MATCH
    const cards = Array.from(document.querySelectorAll(".swipe-card"));
    const counter = document.querySelector("#swipeCounter");
    let actual = 0;

    function mostrarTarjeta(indice) {
        if (!cards.length) return;

        cards.forEach((card, i) => {
            card.classList.toggle("hidden", i !== indice);
        });

        if (counter) {
            counter.textContent = `${indice + 1} de ${cards.length}`;
        }
    }

    document.querySelectorAll(".js-next-card").forEach((boton) => {
        boton.addEventListener("click", () => {
            if (!cards.length) return;

            actual = (actual + 1) % cards.length;
            mostrarTarjeta(actual);
        });
    });


    // MENU HAMBURGUESA
    const menuToggle = document.getElementById("menuToggle");
    const navLinks = document.getElementById("navLinks");

    if (menuToggle && navLinks) {

        menuToggle.addEventListener("click", () => {
            navLinks.classList.toggle("active");

            const abierto = navLinks.classList.contains("active");

            menuToggle.setAttribute("aria-expanded", abierto);
            menuToggle.textContent = abierto ? "✕" : "☰";
        });

        navLinks.querySelectorAll("a").forEach((link) => {
            link.addEventListener("click", () => {
                navLinks.classList.remove("active");
                menuToggle.setAttribute("aria-expanded", "false");
                menuToggle.textContent = "☰";
            });
        });

        window.addEventListener("resize", () => {
            if (window.innerWidth > 900) {
                navLinks.classList.remove("active");
                menuToggle.setAttribute("aria-expanded", "false");
                menuToggle.textContent = "☰";
            }
        });

    }

});