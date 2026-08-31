document.addEventListener("DOMContentLoaded", () => {
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
});
