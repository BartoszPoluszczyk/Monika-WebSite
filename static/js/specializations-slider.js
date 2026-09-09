(() => {
    const carousels = document.querySelectorAll("[data-specializations-carousel]");

    carousels.forEach((carousel) => {
        const track = carousel.querySelector(".specializations-track");
        const previous = carousel.querySelector("[data-slider-previous]");
        const next = carousel.querySelector("[data-slider-next]");

        if (!track || !previous || !next) return;

        const updateControls = () => {
            const end = track.scrollWidth - track.clientWidth - 2;
            previous.disabled = track.scrollLeft <= 2;
            next.disabled = track.scrollLeft >= end;
        };
        const move = (direction) => {
            track.scrollBy({ left: direction * Math.round(track.clientWidth * 0.78), behavior: "smooth" });
        };

        previous.addEventListener("click", () => move(-1));
        next.addEventListener("click", () => move(1));
        track.addEventListener("scroll", updateControls, { passive: true });
        window.addEventListener("resize", updateControls);
        updateControls();
    });
})();
