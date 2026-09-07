// Run: node --test main/navigation.test.mjs
// Unit tests for the actual menu controller; these are not browser/layout tests.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { runInNewContext } from "node:vm";

const source = readFileSync(new URL("../static/js/navigation.js", import.meta.url), "utf8");
const element = (attrs = {}) => ({
    attrs: { ...attrs },
    listeners: {},
    focused: false,
    classList: {
        values: new Set(),
        toggle(name, enabled) {
            if (enabled) this.values.add(name);
            else this.values.delete(name);
        },
        contains(name) { return this.values.has(name); },
    },
    setAttribute(name, value) { this.attrs[name] = value; },
    getAttribute(name) { return this.attrs[name] ?? null; },
    removeAttribute(name) { delete this.attrs[name]; },
    addEventListener(name, callback) { this.listeners[name] = callback; },
    focus() { this.focused = true; },
});

function setup({ wide = false, pathname = "/", hash = "" } = {}) {
    const toggle = element({ "aria-expanded": "false" });
    const menu = element();
    const navbar = element();
    const links = ["/", "/#o-mnie", "/#pomoc", "/#oferta", "/#wspolpraca", "/kalkulator-kalorii/"]
        .map((href) => Object.assign(element(), { href: "https://example.test" + href }));
    navbar.querySelector = (selector) => selector === ".navbar-toggler" ? toggle : menu;
    navbar.querySelectorAll = () => links;
    const desktop = { matches: wide, addEventListener: (_, callback) => { desktop.change = callback; } };
    const location = { pathname, hash };
    const listeners = {};
    runInNewContext(source, {
        document: { querySelector: () => navbar },
        window: {
            matchMedia: () => desktop,
            addEventListener: (name, callback) => { listeners[name] = callback; },
        },
        location, URL,
    });
    return { toggle, menu, navbar, links, desktop, location, listeners };
}

test("mobile toggle synchronizes visibility, aria-expanded and its label", () => {
    const { toggle, menu } = setup();
    toggle.listeners.click();
    assert.equal(menu.classList.contains("is-open"), true);
    assert.equal(toggle.getAttribute("aria-expanded"), "true");
    assert.equal(toggle.getAttribute("aria-label"), "Zamknij menu");
    toggle.listeners.click();
    assert.equal(menu.classList.contains("is-open"), false);
    assert.equal(toggle.getAttribute("aria-expanded"), "false");
    assert.equal(toggle.getAttribute("aria-label"), "Otwórz menu");
});

test("Escape closes the menu and returns keyboard focus to its toggle", () => {
    const { toggle, menu, navbar } = setup();
    toggle.listeners.click();
    navbar.listeners.keydown({ key: "Escape" });
    assert.equal(menu.classList.contains("is-open"), false);
    assert.equal(toggle.focused, true);
});

test("following a mobile navigation or booking link closes the menu", () => {
    const { toggle, menu, navbar } = setup();
    toggle.listeners.click();
    navbar.listeners.click({ target: { closest: () => ({ tagName: "A" }) } });
    assert.equal(menu.classList.contains("is-open"), false);
});

test("switching breakpoints clears the expanded mobile state", () => {
    const { toggle, menu, desktop } = setup();
    toggle.listeners.click();
    desktop.matches = true;
    desktop.change();
    assert.equal(menu.classList.contains("is-open"), false);
    assert.equal(toggle.getAttribute("aria-expanded"), "false");
});

test("deep links and hash changes select exactly one matching navigation item", () => {
    const { links, location, listeners } = setup({ hash: "#o-mnie" });
    assert.equal(links[1].getAttribute("aria-current"), "location");
    location.hash = "#oferta";
    listeners.hashchange();
    assert.equal(links[3].getAttribute("aria-current"), "location");
    assert.equal(links.filter((link) => link.classList.contains("is-active")).length, 1);
    assert.equal(links.filter((link) => link.getAttribute("aria-current")).length, 1);
    location.hash = "";
    listeners.hashchange();
    assert.equal(links[0].getAttribute("aria-current"), "page");
});

test("calculator selects its page link instead of the home section", () => {
    const { links } = setup({ pathname: "/kalkulator-kalorii/" });
    assert.equal(links[5].getAttribute("aria-current"), "page");
    assert.equal(links.filter((link) => link.classList.contains("is-active")).length, 1);
});

test("pages without the navbar do not throw", () => {
    assert.doesNotThrow(() => runInNewContext(source, { document: { querySelector: () => null } }));
});
