import { calculateEnergy, validateInput, FIELDS_BY_STEP } from "./calorie-calculator-core.mjs";

const form = document.getElementById("calorie-calculator");
if (form) {
    const fields = FIELDS_BY_STEP.flat();
    const byId = (id) => document.getElementById(id);
    const panels = [...form.querySelectorAll("[data-calorie-step]")];
    const stepLinks = [...form.querySelectorAll("[data-step-link]")];
    const errorSummary = byId("calculator-errors");
    const emptyState = byId("calculator-empty");
    const resultPanel = byId("calculator-result");
    const announcement = byId("calculator-announcement");
    const formatter = new Intl.NumberFormat("pl-PL", { useGrouping: true });
    let step = 0, reachedStep = 0, hasComputed = false;

    function control(field) {
        const first = form.querySelector('[data-field="' + field + '"]');
        return first?.type === "radio" ? form.querySelector('[data-field="' + field + '"]:checked') : first;
    }
    function readInput() {
        return Object.fromEntries(fields.map((field) => [field, control(field)?.value ?? ""]));
    }
    function clearErrors() {
        errorSummary.hidden = true;
        for (const field of fields) {
            byId(field + "-error").textContent = "";
            form.querySelectorAll('[data-field="' + field + '"]').forEach((el) => el.removeAttribute("aria-invalid"));
        }
    }
    function clearResult(message = "") {
        const hadResult = !resultPanel.hidden;
        resultPanel.hidden = true;
        emptyState.hidden = false;
        byId("calculator-empty-text").textContent = message ||
            "Przejdź przez cztery kroki, aby poznać PPM, CPM i wynik dla wybranego celu.";
        announcement.textContent = hadResult ? "Dane się zmieniły. Oblicz wynik ponownie." : "";
    }
    function showStep(index, focus = true) {
        step = index;
        reachedStep = Math.max(reachedStep, index);
        panels.forEach((panel, i) => { panel.hidden = i !== step; });
        stepLinks.forEach((button, i) => {
            button.disabled = i > reachedStep;
            button.classList.toggle("is-complete", i < step);
            if (i === step) button.setAttribute("aria-current", "step");
            else button.removeAttribute("aria-current");
        });
        byId("calculator-back").hidden = step === 0;
        byId("calculator-next").hidden = step === panels.length - 1;
        byId("calculate-button").hidden = step !== panels.length - 1;
        if (focus) byId("step-title-" + step).focus();
    }
    function syncConditionalFields() {
        const male = control("sex")?.value === "male";
        const condition = byId("condition");
        if (male) condition.value = "none";
        condition.disabled = male;
        byId("condition-fields").hidden = male;
        const pregnant = condition.value === "pregnancy";
        const nursing = ["nursing", "partial"].includes(condition.value);
        byId("trimester-fields").hidden = !pregnant;
        byId("trimester").disabled = !pregnant;
        byId("maternal-note").hidden = !(pregnant || nursing);
        byId("pregnancy-goal-note").hidden = !pregnant;
        byId("nursing-goal-note").hidden = !nursing;
        form.querySelectorAll('[data-field="goal"]').forEach((radio) => {
            const unavailable = pregnant && radio.value !== "maintain";
            radio.disabled = unavailable;
            radio.closest("label").hidden = unavailable;
            if (pregnant) radio.checked = radio.value === "maintain";
        });
        const training = control("training")?.value === "yes";
        byId("training-fields").hidden = !training;
        byId("trainingType").disabled = !training;
        byId("frequency").disabled = !training;
    }
    function displayErrors(errors) {
        const firstStep = FIELDS_BY_STEP.findIndex((group) => group.some((field) => errors[field]));
        if (firstStep >= 0) showStep(firstStep, false);
        for (const [field, message] of Object.entries(errors)) {
            byId(field + "-error").textContent = message;
            form.querySelectorAll('[data-field="' + field + '"]').forEach((el) => el.setAttribute("aria-invalid", "true"));
        }
        errorSummary.hidden = false;
        errorSummary.focus();
        announcement.textContent = "Uzupełnij lub popraw zaznaczone pola.";
    }
    function goForward(destination) {
        clearErrors();
        const { errors } = validateInput(readInput());
        const requiredFields = FIELDS_BY_STEP.slice(0, destination).flat();
        const relevant = Object.fromEntries(Object.entries(errors).filter(([field]) => requiredFields.includes(field)));
        if (Object.keys(relevant).length) { displayErrors(relevant); return; }
        showStep(destination);
    }
    const goalLabels = {
        maintain: "Utrzymanie masy ciała",
        gain300: "Zwiększenie masy · +300 kcal", gain500: "Zwiększenie masy · +500 kcal",
        lose300: "Zmniejszenie masy · −300 kcal", lose500: "Zmniejszenie masy · −500 kcal",
    };
    const signedCalories = (value) => (value > 0 ? "+" : "") + formatter.format(value) + " kcal";

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        if (step < panels.length - 1) { goForward(step + 1); return; }
        clearErrors();
        const { errors, result } = calculateEnergy(readInput());
        if (!result) { clearResult(); displayErrors(errors); return; }
        byId("target-total").hidden = result.target === null;
        byId("target-value").textContent = result.target === null ? "" : formatter.format(result.target);
        byId("result-goal").textContent = result.target === null
            ? "Ten wariant wymaga indywidualnej konsultacji. Poniżej pokazujemy jedynie szacunek PPM i CPM."
            : goalLabels[result.goal] + (result.conditionAddition ? " · uwzględniono dodatek na ciążę lub karmienie." : ".");
        byId("resting-value").textContent = formatter.format(result.resting) + " kcal";
        byId("maintenance-value").textContent = formatter.format(result.maintenance) + " kcal";
        byId("activity-value").textContent = result.factor.toFixed(2).replace(".", ",");
        byId("condition-result-row").hidden = !result.conditionAddition;
        byId("condition-value").textContent = signedCalories(result.conditionAddition);
        byId("goal-value").textContent = signedCalories(result.goalAdjustment);
        const warnings = byId("calculator-warnings");
        warnings.replaceChildren();
        for (const warning of result.warnings) {
            const p = document.createElement("p");
            p.textContent = warning.message;
            p.dataset.warning = warning.code;
            warnings.append(p);
        }
        warnings.hidden = !result.warnings.length;
        emptyState.hidden = true;
        resultPanel.hidden = false;
        hasComputed = true;
        announcement.textContent = result.target === null ? "Wynik wymaga konsultacji. Przeczytaj ostrzeżenie."
            : "Szacunkowy wynik dla celu: " + formatter.format(result.target) + " kilokalorii dziennie. " +
              result.warnings.map((warning) => warning.message).join(" ");
        resultPanel.focus();
    });
    byId("calculator-next").addEventListener("click", () => goForward(step + 1));
    byId("calculator-back").addEventListener("click", () => { clearErrors(); showStep(step - 1); });
    stepLinks.forEach((button, index) => button.addEventListener("click", () => {
        if (index > step) goForward(index);
        else { clearErrors(); showStep(index); }
    }));
    form.addEventListener("input", () => {
        clearErrors();
        syncConditionalFields();
        clearResult(hasComputed ? "Dane zostały zmienione. Przejdź do kroku „Cel” i oblicz wynik ponownie." : "");
    });
    // change also covers select/radio changes in browsers that omit input events.
    form.addEventListener("change", () => {
        syncConditionalFields();
        clearErrors();
        if (!resultPanel.hidden) clearResult("Dane zostały zmienione. Przejdź do kroku „Cel” i oblicz wynik ponownie.");
    });
    form.addEventListener("reset", () => {
        queueMicrotask(() => {
            reachedStep = 0;
            hasComputed = false;
            clearErrors();
            clearResult();
            syncConditionalFields();
            showStep(0);
            announcement.textContent = "Formularz i wynik zostały wyczyszczone.";
        });
    });
    syncConditionalFields();
    showStep(0, false);
    byId("calculator-next").disabled = false;
    byId("calculate-button").disabled = false;
    byId("calculator-loading").hidden = true;
}
