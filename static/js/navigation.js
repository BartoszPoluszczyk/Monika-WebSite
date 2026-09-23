(() => {
    "use strict";

    const navbar = document.querySelector(".site-navbar");
    if (!navbar) return;

    const toggle = navbar.querySelector(".navbar-toggler");
    const menu = navbar.querySelector("#mainNavigation");
    const links = [...navbar.querySelectorAll(".navigation-link")];
    const desktop = window.matchMedia("(min-width: 1101px)");
    const sectionLinks = links.filter((link) => link.dataset.scrollspyTarget);
    const homeLink = sectionLinks.find(
        (link) => link.dataset.scrollspyTarget === "strona-glowna"
    );
    const homePath = homeLink
        ? new URL(homeLink.href, window.location.href).pathname
        : null;
    const isHomePage = homePath === window.location.pathname;

    const setOpen = (open) => {
        menu.classList.toggle("is-open", open);
        toggle.setAttribute("aria-expanded", String(open));
        toggle.setAttribute(
            "aria-label",
            open ? "Zamknij menu" : "Otwórz menu"
        );
    };

    toggle.addEventListener("click", () => {
        setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });

    navbar.addEventListener("keydown", (event) => {
        if (
            event.key === "Escape"
            && toggle.getAttribute("aria-expanded") === "true"
        ) {
            setOpen(false);
            toggle.focus();
        }
    });

    navbar.addEventListener("click", (event) => {
        if (event.target.closest("a") && !desktop.matches) {
            setOpen(false);
        }
    });

    desktop.addEventListener("change", () => setOpen(false));

    const setActiveLink = (target) => {
        if (!target) return;

        for (const link of links) {
            const active = link === target;
            link.classList.toggle("is-active", active);

            if (active) {
                link.setAttribute(
                    "aria-current",
                    link.dataset.scrollspyTarget === "strona-glowna"
                        ? "page"
                        : "location"
                );
            } else {
                link.removeAttribute("aria-current");
            }
        }
    };

    const syncActiveLinkFromLocation = () => {
        if (isHomePage) {
            const hashTarget = window.location.hash.slice(1);
            const target = sectionLinks.find(
                (link) => link.dataset.scrollspyTarget === hashTarget
            );
            setActiveLink(target || homeLink);
            return;
        }

        const target = links.find((link) => {
            const url = new URL(link.href, window.location.href);
            return (
                url.pathname === window.location.pathname
                && url.hash === window.location.hash
            );
        });
        if (target) setActiveLink(target);
    };

    const observedSections = isHomePage
        ? sectionLinks
            .map((link) => ({
                link,
                section: document.getElementById(
                    link.dataset.scrollspyTarget
                ),
            }))
            .filter(({ section }) => section)
        : [];

    const updateActiveFromScroll = () => {
        if (!observedSections.length) return;

        const mobileOffset = navbar.getBoundingClientRect().height + 24;
        const marker = desktop.matches
            ? Math.min(window.innerHeight * 0.34, 320)
            : mobileOffset;

        let current = observedSections[0];
        for (const candidate of observedSections) {
            if (candidate.section.getBoundingClientRect().top <= marker) {
                current = candidate;
            } else {
                break;
            }
        }

        const pageBottom = window.scrollY + window.innerHeight;
        const documentBottom = document.documentElement.scrollHeight;
        if (pageBottom >= documentBottom - 2) {
            current = observedSections[observedSections.length - 1];
        }

        setActiveLink(current.link);
    };

    let scrollFrame = null;
    const scheduleScrollUpdate = () => {
        if (scrollFrame !== null) return;

        scrollFrame = window.requestAnimationFrame(() => {
            scrollFrame = null;
            updateActiveFromScroll();
        });
    };

    window.addEventListener("hashchange", () => {
        syncActiveLinkFromLocation();
        scheduleScrollUpdate();
    });

    if (isHomePage) {
        window.addEventListener("scroll", scheduleScrollUpdate, {
            passive: true,
        });
        window.addEventListener("resize", scheduleScrollUpdate);
        window.addEventListener("load", scheduleScrollUpdate);
        syncActiveLinkFromLocation();
        scheduleScrollUpdate();
    } else {
        syncActiveLinkFromLocation();
    }
})();
