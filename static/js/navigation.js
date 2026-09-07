(() => {
    "use strict";
    const navbar = document.querySelector(".site-navbar");
    if (!navbar) return;

    const toggle = navbar.querySelector(".navbar-toggler");
    const menu = navbar.querySelector("#mainNavigation");
    const links = [...navbar.querySelectorAll(".navigation-link")];
    const desktop = window.matchMedia("(min-width: 1101px)");

    const setOpen = (open) => {
        menu.classList.toggle("is-open", open);
        toggle.setAttribute("aria-expanded", String(open));
        toggle.setAttribute("aria-label", open ? "Zamknij menu" : "Otwórz menu");
    };

    toggle.addEventListener("click", () => {
        setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });
    navbar.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
            setOpen(false);
            toggle.focus();
        }
    });
    navbar.addEventListener("click", (event) => {
        if (event.target.closest("a") && !desktop.matches) setOpen(false);
    });
    desktop.addEventListener("change", () => setOpen(false));

    // Highlight the actual anchor after clicking a section or opening a deep link.
    // Server-rendered current-page state still works with JavaScript disabled.
    const syncActiveLink = () => {
        const target = links.find((link) => {
            const url = new URL(link.href);
            return url.pathname === location.pathname && url.hash === location.hash;
        });
        if (!target) return;
        for (const link of links) {
            const active = link === target;
            link.classList.toggle("is-active", active);
            if (active) link.setAttribute("aria-current", location.hash ? "location" : "page");
            else link.removeAttribute("aria-current");
        }
    };
    window.addEventListener("hashchange", syncActiveLink);
    syncActiveLink();
})();
