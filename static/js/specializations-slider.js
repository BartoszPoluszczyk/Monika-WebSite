(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const compactLayout = window.matchMedia("(max-width: 680px)");

    document.querySelectorAll("[data-specializations-marquee]").forEach((marquee) => {
        const viewport = marquee.querySelector(".specializations-marquee-viewport");
        const track = marquee.querySelector(".specializations-marquee-track");
        const original = track?.querySelector("[data-specializations-original]");

        if (!viewport || !track || !original) return;

        const removeClones = () => {
            track.querySelectorAll("[data-specializations-clone]").forEach((clone) => clone.remove());
        };

        const refresh = () => {
            track.classList.remove("is-animated");
            removeClones();
            track.style.removeProperty("--specializations-loop-width");

            if (reduceMotion.matches || compactLayout.matches) return;

            const originalWidth = original.getBoundingClientRect().width;
            const viewportWidth = viewport.clientWidth;
            const gap = Number.parseFloat(window.getComputedStyle(track).gap) || 0;

            if (!originalWidth || !viewportWidth) return;

            let renderedWidth = originalWidth;
            const targetWidth = viewportWidth * 2 + originalWidth;

            while (renderedWidth < targetWidth) {
                const clone = original.cloneNode(true);
                clone.removeAttribute("data-specializations-original");
                clone.setAttribute("data-specializations-clone", "");
                clone.setAttribute("aria-hidden", "true");
                track.append(clone);
                renderedWidth += originalWidth + gap;
            }

            track.style.setProperty("--specializations-loop-width", `${originalWidth + gap}px`);
            if (!document.hidden) track.classList.add("is-animated");
        };

        const pauseForHiddenTab = () => {
            track.classList.toggle("is-paused", document.hidden);
        };

        const scheduleRefresh = () => window.requestAnimationFrame(refresh);
        const resizeObserver = "ResizeObserver" in window
            ? new ResizeObserver(scheduleRefresh)
            : null;

        resizeObserver?.observe(viewport);
        reduceMotion.addEventListener?.("change", scheduleRefresh);
        compactLayout.addEventListener?.("change", scheduleRefresh);
        document.addEventListener("visibilitychange", pauseForHiddenTab);

        scheduleRefresh();
    });
})();