(() => {
    const notice = document.querySelector("[data-cookie-notice]");
    if (!notice) return;

    const storageKey = "monika-cookie-information-dismissed";
    let dismissed = false;
    try {
        dismissed = window.localStorage.getItem(storageKey) === "1";
    } catch (_error) {
        dismissed = false;
    }

    if (!dismissed) notice.hidden = false;

    notice.querySelector("[data-cookie-dismiss]")?.addEventListener("click", () => {
        notice.hidden = true;
        try {
            window.localStorage.setItem(storageKey, "1");
        } catch (_error) {
            // Przy zablokowanej pamięci informacja może pojawić się ponownie.
        }
    });
})();
