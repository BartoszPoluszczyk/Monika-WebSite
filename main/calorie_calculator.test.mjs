// Run: node --test main/calorie_calculator.test.mjs
import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { calculateEnergy, validateInput, WORK_FACTORS, STEP_ADDITIONS, TRAINING_ADDITIONS } from "../static/js/calorie-calculator-core.mjs";

const reference = JSON.parse(readFileSync(new URL("./calorie_calculator.reference.json", import.meta.url)));
const sample = reference.baseline;
for (const fixture of reference.cases) {
    test("reference parity: " + fixture.name, () => {
        const { errors, result } = calculateEnergy({ ...sample, ...fixture.input });
        assert.deepEqual(errors, {});
        for (const [key, value] of Object.entries(fixture.expected)) assert.equal(result[key], value, key);
    });
}
test("all 42 work/steps/training combinations use additive factors and unrounded PPM", () => {
    for (const [work, base] of Object.entries(WORK_FACTORS)) {
        for (const [steps, addition] of Object.entries(STEP_ADDITIONS)) {
            const variants = [{ training: "no", addition: 0 }];
            for (const [trainingType, frequencies] of Object.entries(TRAINING_ADDITIONS)) {
                for (const [frequency, addition] of Object.entries(frequencies)) variants.push({ training: "yes", trainingType, frequency, addition });
            }
            for (const variant of variants) {
                const { result } = calculateEnergy({ ...sample, work, steps, ...variant });
                const expectedFactor = (base + addition + variant.addition) / 100;
                assert.equal(result.factor, expectedFactor);
                assert.equal(result.maintenance, Math.round(1411.5 * expectedFactor));
            }
        }
    }
});
test("Polish comma and dot, whitespace and numeric inputs agree", () => {
    const comma = calculateEnergy({ ...sample, weight: " 70,5 " });
    const dot = calculateEnergy({ ...sample, weight: "70.5" });
    assert.deepEqual(comma, dot);
    assert.deepEqual(dot, calculateEnergy({ ...sample, weight: 70.5 }));
});
test("half-up rounding uses full PPM, not already rounded PPM", () => {
    const { result } = calculateEnergy(sample);
    assert.equal(result.resting, 1412); // Actual PPM = 1411.5.
    assert.equal(result.maintenance, 1835); // Rounding PPM before multiplying would give 1836.
    assert.equal(calculateEnergy({ ...sample, training: "yes", trainingType: "intense", frequency: "four_six" }).result.maintenance, 2117);
});
test("disabled training details never affect the result or validation", () => {
    assert.deepEqual(calculateEnergy({ ...sample, trainingType: "bad", frequency: "bad" }), calculateEnergy(sample));
});
test("an inactive trimester is ignored", () => {
    assert.deepEqual(calculateEnergy({ ...sample, trimester: "bad" }), calculateEnergy(sample));
});
test("pregnancy overrides stale reduction or gain, with exactly one supplement", () => {
    for (const goal of ["lose300", "lose500", "gain300", "gain500", "maintain"]) {
        const { result } = calculateEnergy({ ...sample, condition: "pregnancy", trimester: "second", goal });
        assert.equal(result.goalAdjustment, 0);
        assert.equal(result.conditionAddition, 260);
        assert.equal(result.target, 2095);
        assert.equal(result.goal, "maintain");
        assert.ok(result.warnings.some(w => w.code === "maternal"));
    }
});
test("nursing and partial nursing additions combine with goals only once", () => {
    for (const [condition, extra] of [["nursing", 500], ["partial", 400]]) {
        for (const [goal, adjustment] of [["maintain", 0], ["lose300", -300], ["gain300", 300]]) {
            const { result } = calculateEnergy({ ...sample, condition, goal });
            assert.equal(result.target, 1835 + extra + adjustment);
            assert.ok(result.warnings.some(w => w.code === "maternal"));
        }
    }
});
test("male variant rejects inconsistent maternal data", () => {
    for (const condition of ["pregnancy", "nursing", "partial"]) {
        assert.ok(calculateEnergy({ ...sample, sex: "male", condition }).errors.condition);
    }
});
test("unknown and prototype-like choices are not accepted", () => {
    for (const field of ["sex", "condition", "trimester", "work", "steps", "training", "trainingType", "frequency", "goal"]) {
        for (const value of ["", undefined, null, "constructor", "__proto__", "toString", [], {}, 1.3]) {
            const input = { ...sample, training: "yes", condition: "pregnancy", [field]: value };
            assert.ok(calculateEnergy(input).errors[field], field + ": " + String(value));
        }
    }
});
test("empty and malformed input never returns a result or throws", () => {
    for (const input of [undefined, null, {}, [], "", 3]) assert.equal(calculateEnergy(input).result, null);
});
test("invalid numeric syntax is rejected instead of silently truncated", () => {
    for (const field of ["age", "height", "weight"]) {
        for (const value of ["", " ", null, undefined, [], {}, true, NaN, Infinity, "1e2", "0x50", "-80", "70kg", "70,5.5", "70..5", "<script>"]) {
            const { errors, result } = calculateEnergy({ ...sample, [field]: value });
            assert.equal(result, null);
            assert.ok(errors[field]);
        }
    }
});
test("adults only; height and age whole; weight at most one decimal place", () => {
    const invalid = { age: [0, 10, 17, 17.9, 30.5, 101], height: [99, 170.5, 251], weight: [19.9, 70.55, 300.1] };
    for (const [field, values] of Object.entries(invalid)) {
        for (const value of values) assert.ok(validateInput({ ...sample, [field]: value }).errors[field]);
    }
});
test("declared boundaries parse, while unsafe targets are guarded separately", () => {
    for (const [field, values] of Object.entries({ age: [18, 100], height: [100, 250], weight: [20, 300] })) {
        for (const value of values) {
            const { errors, result } = calculateEnergy({ ...sample, [field]: value });
            assert.deepEqual(errors, {});
            assert.ok(Number.isFinite(result.resting));
            assert.ok(Number.isFinite(result.maintenance));
        }
    }
});
test("low BMI reduction does not produce a calorie target", () => {
    const { result } = calculateEnergy({ ...sample, weight: 45, goal: "lose300" });
    assert.equal(result.target, null);
    assert.ok(result.warnings.some(w => w.code === "low_bmi"));
    assert.ok(result.maintenance > 0);
});
test("a target below 1000 is suppressed, not replaced by an invented safe target", () => {
    const { result } = calculateEnergy({ ...sample, age: 100, height: 150, weight: 50, goal: "lose500" });
    assert.equal(result.target, null);
    assert.ok(result.warnings.some(w => w.code === "low_energy"));
});
test("below-resting warning preserves parity for an ordinary adult example", () => {
    const { result } = calculateEnergy({ ...sample, goal: "lose500" });
    assert.equal(result.target, 1335);
    assert.ok(result.warnings.some(w => w.code === "below_resting"));
});
