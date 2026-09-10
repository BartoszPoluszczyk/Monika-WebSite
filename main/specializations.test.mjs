// Run: node --test main/specializations.test.mjs
// Tests the actual reveal controller with a small DOM/IntersectionObserver double.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { runInNewContext } from "node:vm";

const source = readFileSync(new URL("../static/js/specializations-reveal.js", import.meta.url), "utf8");

function setup({ count = 7, reduced = false, supported = true, failure = "", listsPresent = true } = {}) {
    const rows = Array.from({ length: count }, (_, index) => {
        const classes = new Set();
        const styles = new Map();
        return {
            index,
            classes,
            styles,
            classList: {
                add: (...names) => names.forEach((name) => classes.add(name)),
                remove: (...names) => names.forEach((name) => classes.delete(name)),
                contains: (name) => classes.has(name),
            },
            style: {
                setProperty: (name, value) => styles.set(name, value),
                removeProperty: (name) => styles.delete(name),
            },
        };
    });
    const listeners = new Map();
    const list = {
        querySelectorAll: () => rows,
        addEventListener: (type, listener) => listeners.set(type, listener),
        removeEventListener: (type) => listeners.delete(type),
    };
    const motion = {
        matches: reduced,
        addEventListener: (_, callback) => { motion.change = callback; },
    };
    let observer;
    class Observer {
        constructor(callback, options) {
            if (failure === "construct") throw new Error("Unavailable");
            this.callback = callback;
            this.options = options;
            this.observed = new Set();
            this.unobserved = [];
            observer = this;
        }
        observe(row) {
            if (failure === "observe" && row.index === 2) throw new Error("Cannot observe");
            this.observed.add(row);
        }
        unobserve(row) { this.observed.delete(row); this.unobserved.push(row); }
        disconnect() { this.observed.clear(); this.disconnected = true; }
        enter(indices) { this.callback(indices.map((index) => ({ target: rows[index], isIntersecting: true }))); }
    }
    const window = { matchMedia: () => motion };
    if (supported) window.IntersectionObserver = Observer;
    runInNewContext(source, {
        window,
        document: { querySelectorAll: () => listsPresent ? [list] : [] },
    });
    return { rows, observer, motion, listeners };
}

test("each strip is observed individually, without clones or an auto-scroll loop", () => {
    const { rows, observer } = setup();
    assert.equal(rows.length, 7);
    assert.equal(observer.observed.size, 7);
    assert.equal(observer.options.rootMargin, "0px 0px -24px 0px");
    assert.ok(rows.every((row) => row.classes.has("is-reveal-pending")));
});

test("only intersecting strips are revealed and each is unobserved after one entrance", () => {
    const { rows, observer } = setup();
    observer.callback([{ target: rows[0], isIntersecting: false }]);
    assert.ok(rows[0].classes.has("is-reveal-pending"));
    observer.enter([0]);
    assert.ok(rows[0].classes.has("is-reveal-entering"));
    assert.equal(rows[0].classes.has("is-reveal-pending"), false);
    assert.equal(observer.observed.has(rows[0]), false);
    assert.ok(rows[1].classes.has("is-reveal-pending"));
    observer.enter([0]);
    assert.equal(observer.unobserved.length, 1);
});

test("simultaneous strips reveal in DOM order with a bounded stagger", () => {
    const { rows, observer } = setup();
    observer.enter([6, 4, 2, 0, 5, 3, 1]);
    assert.deepEqual(rows.map((row) => row.styles.get("--specialization-reveal-delay")), [
        "0ms", "100ms", "200ms", "300ms", "400ms", "400ms", "400ms",
    ]);
});

test("slow scrolling does not accumulate delays from earlier strips", () => {
    const { rows, observer } = setup();
    observer.enter([0]);
    observer.enter([1]);
    assert.equal(rows[1].styles.get("--specialization-reveal-delay"), "0ms");
});

test("finished animations clean up transforms and do not replay on scroll back", () => {
    const { rows, observer, listeners } = setup();
    observer.enter([0]);
    listeners.get("animationend")({ target: rows[0], animationName: "unrelated" });
    assert.ok(rows[0].classes.has("is-reveal-entering"));
    listeners.get("animationend")({ target: rows[0], animationName: "specialization-slide-in" });
    assert.equal(rows[0].classes.size, 0);
    assert.equal(rows[0].styles.size, 0);
    observer.enter([0]);
    assert.equal(rows[0].classes.size, 0);
});

test("reduced motion and unsupported browsers keep all content visible", () => {
    for (const options of [{ reduced: true }, { supported: false }]) {
        const { rows, observer } = setup(options);
        assert.equal(observer, undefined);
        assert.ok(rows.every((row) => row.classes.size === 0));
    }
});

test("enabling reduced motion mid-scroll exposes every remaining strip", () => {
    const { rows, observer, motion } = setup();
    observer.enter([0]);
    motion.matches = true;
    motion.change();
    assert.ok(observer.disconnected);
    assert.ok(rows.every((row) => row.classes.size === 0 && row.styles.size === 0));
});

test("observer failures never leave the content hidden", () => {
    for (const failure of ["construct", "observe"]) {
        const { rows } = setup({ failure });
        assert.ok(rows.every((row) => row.classes.size === 0));
    }
});

test("empty sections and pages without specializations are harmless", () => {
    assert.doesNotThrow(() => setup({ count: 0 }));
    assert.doesNotThrow(() => setup({ listsPresent: false }));
});
