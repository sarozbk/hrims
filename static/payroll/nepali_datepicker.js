(function () {
  const selector =
    'input[data-nepali-datepicker="true"], input[type="date"]:not([data-nepali-datepicker="false"]):not([hidden])';
  const dateFormat = "YYYY-MM-DD";
  const nepaliMonths = [
    "वैशाख",
    "जेठ",
    "असार",
    "साउन",
    "भदौ",
    "असोज",
    "कात्तिक",
    "मंसिर",
    "पुस",
    "माघ",
    "फागुन",
    "चैत",
  ];
  const numberFormat = /^\d{4}-\d{2}-\d{2}$/;
  const styleProperties = [
    "backgroundColor",
    "border",
    "borderRadius",
    "boxSizing",
    "color",
    "fontFamily",
    "fontSize",
    "fontWeight",
    "lineHeight",
    "outline",
    "padding",
    "transition",
  ];
  let generatedId = 0;

  if (!window.NepaliFunctions || !window.NepaliFunctions.BS) {
    throw new Error("Nepali calendar functions did not load.");
  }
  window.NepaliFunctions.BS.GetMonthsInUnicode = () => nepaliMonths.slice();
  window.NepaliFunctions.BS.GetMonthInUnicode = (month) => {
    const index = Number(month);
    return Number.isInteger(index) && index >= 0 && index < nepaliMonths.length
      ? nepaliMonths[index]
      : null;
  };

  function toGregorianDate(value) {
    const functions = window.NepaliFunctions;
    const normalized = functions.ConvertToNumber(value.trim());
    const parts = normalized.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
    if (!parts) return null;

    const bsDate = `${parts[1]}-${parts[2].padStart(2, "0")}-${parts[3].padStart(2, "0")}`;
    const adDate = functions.BS2AD(bsDate, dateFormat, dateFormat);
    if (
      typeof adDate !== "string" ||
      !numberFormat.test(adDate) ||
      functions.AD2BS(adDate, dateFormat, dateFormat) !== bsDate
    ) {
      return null;
    }

    return adDate;
  }

  function toBikramSambatDate(value) {
    if (!value) return "";
    const bsDate = window.NepaliFunctions.AD2BS(value, dateFormat, dateFormat);
    return typeof bsDate === "string" ? bsDate : "";
  }

  function dispatchDateEvents(input) {
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function initializePicker(input) {
    if (input.dataset.nepaliDatepickerReady) return;
    if (typeof input.NepaliDatePicker !== "function") {
      throw new Error("Nepali datepicker library did not load.");
    }

    input.NepaliDatePicker({
      dateFormat,
      language: "nepali",
      unicodeDate: false,
      onSelect: function () {
        dispatchDateEvents(input);
      },
    });
    input.dataset.nepaliDatepickerReady = "true";
  }

  function copyDateStyles(source, visible) {
    const computedStyles = window.getComputedStyle(source);
    styleProperties.forEach((property) => {
      if (!source.style[property]) {
        visible.style[property] = computedStyles[property];
      }
    });
  }

  function createBikramSambatInput(source) {
    const visible = source.cloneNode(false);
    const gregorianDate = source.value;
    const defaultGregorianDate = source.defaultValue;
    const required = source.required;

    visible.type = "text";
    visible.removeAttribute("name");
    visible.id = source.id ? `${source.id}-nepali` : `nepali-date-${++generatedId}`;
    visible.removeAttribute("min");
    visible.removeAttribute("max");
    visible.removeAttribute("step");
    visible.removeAttribute("value");
    visible.required = required;
    visible.removeAttribute("aria-hidden");
    Array.from(visible.attributes).forEach((attribute) => {
      if (/^on/i.test(attribute.name) || /^hx-/i.test(attribute.name)) {
        visible.removeAttribute(attribute.name);
      }
    });
    visible.value = toBikramSambatDate(gregorianDate);
    visible.defaultValue = toBikramSambatDate(defaultGregorianDate);
    visible.dataset.nepaliDatepicker = "true";
    visible.dataset.nepaliDateSource = "true";
    visible.setAttribute("autocomplete", "off");
    if (!visible.placeholder) visible.placeholder = "YYYY-MM-DD (BS)";
    visible.classList.add("horilla-nepali-date-input");
    copyDateStyles(source, visible);

    source.hidden = true;
    source.removeAttribute("required");
    source.setAttribute("aria-hidden", "true");
    source.dataset.nepaliDatepicker = "false";
    source.parentNode.insertBefore(visible, source);

    if (source.id) {
      document.querySelectorAll("label").forEach((label) => {
        if (label.htmlFor === source.id) label.htmlFor = visible.id;
      });
    }

    let updatingGregorianValue = false;

    function updateVisibleDate() {
      if (updatingGregorianValue) return;
      const bsDate = toBikramSambatDate(source.value);
      if (visible.value !== bsDate) visible.value = bsDate;
      visible.setCustomValidity("");
    }

    function updateGregorianDate() {
      const previousValue = source.value;
      let nextValue = "";
      let validationMessage = "";

      if (visible.value) {
        nextValue = toGregorianDate(visible.value) || "";
        if (!nextValue) {
          validationMessage = "Enter a valid Bikram Sambat date in YYYY-MM-DD format.";
        }
      }

      if (nextValue) {
        const minimum = source.getAttribute("min");
        const maximum = source.getAttribute("max");
        if (minimum && nextValue < minimum) {
          validationMessage = `Date must be on or after ${minimum}.`;
        } else if (maximum && nextValue > maximum) {
          validationMessage = `Date must be on or before ${maximum}.`;
        }
      }

      visible.setCustomValidity(validationMessage);
      source.value = nextValue;
      if (previousValue !== nextValue) {
        updatingGregorianValue = true;
        dispatchDateEvents(source);
        updatingGregorianValue = false;
      }
    }

    visible.addEventListener("input", updateGregorianDate);
    visible.addEventListener("change", updateGregorianDate);
    source.addEventListener("input", updateVisibleDate);
    source.addEventListener("change", updateVisibleDate);
    initializePicker(visible);
  }

  function initialize(root) {
    if (!root || typeof root.querySelectorAll !== "function") return;

    const inputs = Array.from(root.querySelectorAll(selector));
    if (root.matches && root.matches(selector)) inputs.unshift(root);

    inputs.forEach((input) => {
      if (input.dataset.nepaliDateSource) {
        initializePicker(input);
      } else if (input.type === "date") {
        createBikramSambatInput(input);
      } else {
        initializePicker(input);
      }
    });
  }

  if (!window.horillaNepaliDatepickerInitialized) {
    document.addEventListener("htmx:afterSettle", (event) => {
      initialize(event.target);
    });
    new MutationObserver((records) => {
      records.forEach((record) => {
        record.addedNodes.forEach(initialize);
      });
    }).observe(document.documentElement, { childList: true, subtree: true });
    window.horillaNepaliDatepickerInitialized = true;
  }

  initialize(document);
})();
