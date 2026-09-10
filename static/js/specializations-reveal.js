(() => {
    const lists = document.querySelectorAll("[data-specializations-reveal]");
    if (!lists.length) return;

    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (motion.matches || !("IntersectionObserver" in window)) return;

    lists.forEach((list) => {
        const rows = Array.from(list.querySelectorAll(".specialization-band"));
        if (!rows.length) return;

        let observer;

        const resetRow = (row) => {
            row.classList.remove("is-reveal-pending", "is-reveal-entering");
            row.style.removeProperty("--specialization-reveal-delay");
        };

        const finishAnimation = (event) => {
            if (event.animationName === "specialization-slide-in" && rows.includes(event.target)) {
                resetRow(event.target);
            }
        };

        const showAll = () => {
            observer?.disconnect();
            rows.forEach(resetRow);
            list.removeEventListener("animationend", finishAnimation);
        };

        try {
            // Pending rows have opacity: 0, but no transform: observing a row
            // already translated offscreen would prevent its reveal firing.
            observer = new window.IntersectionObserver((entries) => {
                entries
                    .filter((entry) => entry.isIntersecting && entry.target.classList.contains("is-reveal-pending"))
                    .sort((a, b) => rows.indexOf(a.target) - rows.indexOf(b.target))
                    .forEach((entry, index) => {
                        const row = entry.target;
                        // Stagger rows that enter together, without delaying
                        // later rows when the visitor scrolls slowly.
                        row.style.setProperty("--specialization-reveal-delay", `${Math.min(index * 100, 400)}ms`);
                        row.classList.remove("is-reveal-pending");
                        row.classList.add("is-reveal-entering");
                        observer.unobserve(row);
                    });
            }, { rootMargin: "0px 0px -24px 0px", threshold: 0 });

            list.addEventListener("animationend", finishAnimation);
            rows.forEach((row) => {
                row.classList.add("is-reveal-pending");
                observer.observe(row);
            });

            motion.addEventListener?.("change", () => {
                if (motion.matches) showAll();
            });
        } catch {
            // A failed enhancement must never hide the admin-managed content.
            showAll();
        }
    });
})();
