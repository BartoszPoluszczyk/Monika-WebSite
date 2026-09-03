// Independently implemented compatibility model, checked against the public
// Dietoterapia Lenartowicz calculator on 2026-09-03. See the comparison tests.
// Simplified original Harris–Benedict, NOT Mifflin or revised HB (1984).
// Activity additions are reference-specific assumptions, not clinical norms.
export const WORK_FACTORS = Object.freeze({ sedentary: 130, physical: 155 });
export const STEP_ADDITIONS = Object.freeze({ low: 0, medium: 5, high: 10 });
export const TRAINING_ADDITIONS = Object.freeze({
    light: Object.freeze({ one_two: 5, three: 8, four_six: 12 }),
    intense: Object.freeze({ one_two: 10, three: 15, four_six: 20 }),
});
export const GOAL_ADJUSTMENTS = Object.freeze({ maintain: 0, gain300: 300, gain500: 500, lose300: -300, lose500: -500 });
export const PREGNANCY_ADDITIONS = Object.freeze({ first: 70, second: 260, third: 500 });
export const FIELDS_BY_STEP = Object.freeze([
    Object.freeze(["sex", "age", "height", "weight", "condition", "trimester"]),
    Object.freeze(["work", "steps"]),
    Object.freeze(["training", "trainingType", "frequency"]),
    Object.freeze(["goal"]),
]);
const LIMITS = Object.freeze({
    age: { min: 18, max: 100, integer: true, message: "Podaj pełne lata od 18 do 100. Ten kalkulator jest dla dorosłych." },
    height: { min: 100, max: 250, integer: true, message: "Podaj wzrost od 100 do 250 cm, w pełnych centymetrach." },
    weight: { min: 20, max: 300, message: "Podaj masę od 20 do 300 kg, z najwyżej jednym miejscem po przecinku." },
});
function decimal(value) {
    if (typeof value !== "string" && typeof value !== "number") return NaN;
    const text = String(value).trim();
    return /^\d+(?:[.,]\d+)?$/.test(text) ? Number(text.replace(",", ".")) : NaN;
}
const contains = (options, value) => typeof value === "string" && Object.hasOwn(options, value);

export function validateInput(input = {}) {
    if (!input || typeof input !== "object") input = {};
    const errors = {}, values = {};
    for (const [field, rule] of Object.entries(LIMITS)) {
        const value = decimal(input[field]);
        const precisionValid = field !== "weight" || Math.abs(value * 10 - Math.round(value * 10)) < 1e-8;
        if (!Number.isFinite(value) || value < rule.min || value > rule.max ||
            (rule.integer && !Number.isInteger(value)) || !precisionValid) errors[field] = rule.message;
        values[field] = value;
    }
    if (!["female", "male"].includes(input.sex)) errors.sex = "Wybierz wariant wzoru: kobieta lub mężczyzna.";
    if (!["none", "pregnancy", "nursing", "partial"].includes(input.condition)) errors.condition = "Wybierz właściwy wariant ciąży lub karmienia.";
    if (input.sex === "male" && input.condition !== "none") errors.condition = "Dodatek na ciążę i karmienie jest dostępny tylko w wariancie wzoru dla kobiet.";
    if (input.condition === "pregnancy" && !contains(PREGNANCY_ADDITIONS, input.trimester)) errors.trimester = "Wybierz trymestr ciąży.";
    if (!contains(WORK_FACTORS, input.work)) errors.work = "Wybierz rodzaj pracy.";
    if (!contains(STEP_ADDITIONS, input.steps)) errors.steps = "Wybierz dzienną liczbę kroków.";
    if (!["no", "yes"].includes(input.training)) errors.training = "Zaznacz, czy regularnie trenujesz.";
    if (input.training === "yes") {
        if (!contains(TRAINING_ADDITIONS, input.trainingType)) errors.trainingType = "Wybierz rodzaj treningu.";
        if (!["one_two", "three", "four_six"].includes(input.frequency)) errors.frequency = "Wybierz częstotliwość treningów.";
    }
    if (!contains(GOAL_ADJUSTMENTS, input.goal)) errors.goal = "Wybierz cel obliczeń.";
    return { errors, values };
}

export function calculateEnergy(input = {}) {
    const { errors, values } = validateInput(input);
    if (Object.keys(errors).length) return { errors, result: null };
    // Integer hundredths keep half-up rounding stable, including decimal weight.
    // Female: 655 + 9.6W + 1.8H - 4.7A; male: 66 + 13.7W + 5H - 6.8A.
    const weightTenths = Math.round(values.weight * 10);
    const restingHundredths = input.sex === "female"
        ? 65500 + 96 * weightTenths + 180 * values.height - 470 * values.age
        : 6600 + 137 * weightTenths + 500 * values.height - 680 * values.age;
    const factorHundredths = WORK_FACTORS[input.work] + STEP_ADDITIONS[input.steps] +
        (input.training === "yes" ? TRAINING_ADDITIONS[input.trainingType][input.frequency] : 0);
    const resting = Math.floor((restingHundredths + 50) / 100);
    const maintenance = Math.floor((restingHundredths * factorHundredths + 5000) / 10000);
    const conditionAddition = input.condition === "pregnancy" ? PREGNANCY_ADDITIONS[input.trimester]
        : input.condition === "nursing" ? 500 : input.condition === "partial" ? 400 : 0;
    // Pregnancy overrides any stale goal from an earlier step.
    const goal = input.condition === "pregnancy" ? "maintain" : input.goal;
    const goalAdjustment = GOAL_ADJUSTMENTS[goal];
    let target = maintenance + conditionAddition + goalAdjustment;
    const warnings = [];
    if (input.condition !== "none") warnings.push({ code: "maternal", message: "Dodatek na ciążę lub karmienie jest uproszczeniem przyjętym w tym kalkulatorze. Nie uwzględnia m.in. etapu laktacji, liczby dzieci ani przebiegu ciąży. Kaloryczność diety ustal z dietetykiem lub lekarzem; nie rozpoczynaj redukcji na podstawie tego wyniku." });
    const bmi = values.weight / (values.height / 100) ** 2;
    if (goalAdjustment < 0 && bmi < 18.5) {
        target = null;
        warnings.push({ code: "low_bmi", message: "Przy podanych proporcjach masy i wzrostu nie wyświetlamy celu redukcyjnego. Skonsultuj potrzeby żywieniowe ze specjalistą." });
    } else if (target < 1000) {
        target = null;
        warnings.push({ code: "low_energy", message: "Obliczony wariant daje zbyt mało energii, dlatego nie pokazujemy go jako celu diety. Skonsultuj wynik z dietetykiem. Próg 1000 kcal jest zabezpieczeniem formularza, a nie zalecaną ani uniwersalnie bezpieczną kalorycznością." });
    } else if (goalAdjustment < 0 && target < resting) {
        warnings.push({ code: "below_resting", message: "Ten wariant jest niższy od oszacowanej energii spoczynkowej. Nie traktuj go jako zalecenia do samodzielnego stosowania; omów cel z dietetykiem." });
    }
    return { errors, result: { resting, maintenance, factor: factorHundredths / 100,
        conditionAddition, goalAdjustment, goal, target, warnings } };
}
