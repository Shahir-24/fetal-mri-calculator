const form = document.getElementById("calculator-form");
const resultsPanel = document.getElementById("results-panel");
const formStatus = document.getElementById("form-status");
const clearButton = document.getElementById("clear-form");
const presetButtons = document.querySelectorAll(".preset-button");

const STORAGE_KEY = "fetal-mri-calculator-form-v4";

let activeController = null;
let requestCounter = 0;

function debounce(fn, delay) {
  let timer = null;
  return (...args) => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => fn(...args), delay);
  };
}

function setStatus(message, tone = "neutral") {
  if (!formStatus) {
    return;
  }
  formStatus.textContent = message;
  formStatus.dataset.tone = tone;
}

function serializeForm() {
  if (!form) {
    return {};
  }
  const data = new FormData(form);
  return Object.fromEntries(Array.from(data.entries(), ([key, value]) => [key, String(value)]));
}

function hasMeaningfulEntries(values) {
  return Object.entries(values).some(([key, value]) => {
    if (key === "gestational_days") {
      return false;
    }
    return String(value).trim() !== "";
  });
}

function persistForm() {
  if (!form) {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(serializeForm()));
}

function updateGroupProgress() {
  if (!form) {
    return;
  }
  for (const heading of form.querySelectorAll(".field-group-heading[data-field-names]")) {
    const rawNames = heading.getAttribute("data-field-names");
    if (!rawNames) {
      continue;
    }
    const names = JSON.parse(rawNames);
    const completed = names.filter((name) => {
      const field = form.querySelector(`[name="${name}"]`);
      return field instanceof HTMLInputElement && field.value.trim() !== "";
    }).length;
    const progress = heading.querySelector(".group-progress");
    if (progress) {
      progress.textContent = `${completed}/${names.length}`;
      progress.dataset.complete = completed === names.length ? "true" : "false";
    }
  }
}

function applyValues(values) {
  if (!form) {
    return;
  }
  for (const [name, value] of Object.entries(values)) {
    const field = form.querySelector(`[name="${name}"]`);
    if (!(field instanceof HTMLInputElement)) {
      continue;
    }
    field.value = String(value);
  }
  persistForm();
  updateGroupProgress();
}

function resetForm() {
  if (!form) {
    return;
  }
  form.reset();
  applyValues({ gestational_days: "0" });
  window.localStorage.removeItem(STORAGE_KEY);
  updateGroupProgress();
}

function restoreForm() {
  if (!form) {
    return;
  }
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return;
  }
  try {
    const values = JSON.parse(raw);
    applyValues(values);
  } catch (_error) {
    window.localStorage.removeItem(STORAGE_KEY);
  }
}

async function refreshResults() {
  if (!form || !resultsPanel) {
    return;
  }

  const currentRequest = ++requestCounter;
  if (activeController) {
    activeController.abort();
  }
  activeController = new AbortController();

  resultsPanel.classList.add("is-loading");
  setStatus("Refreshing interpretation...", "working");
  persistForm();

  try {
    const response = await fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      signal: activeController.signal,
    });

    if (!response.ok) {
      throw new Error("Refresh failed.");
    }

    const html = await response.text();
    if (currentRequest !== requestCounter) {
      return;
    }

    resultsPanel.innerHTML = html;
    setStatus(
      `Updated ${new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}.`,
      "success",
    );
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      return;
    }
    setStatus("Could not refresh results. Check the inputs and try again.", "error");
  } finally {
    if (currentRequest === requestCounter) {
      resultsPanel.classList.remove("is-loading");
    }
  }
}

const debouncedRefresh = debounce(refreshResults, 220);

if (form) {
  restoreForm();

  form.addEventListener("input", () => {
    persistForm();
    updateGroupProgress();
    debouncedRefresh();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    await refreshResults();
  });

  if (hasMeaningfulEntries(serializeForm())) {
    window.setTimeout(refreshResults, 0);
  }
  updateGroupProgress();
}

presetButtons.forEach((button) => {
  if (!(button instanceof HTMLButtonElement)) {
    return;
  }
  button.addEventListener("click", async () => {
    const payload = button.dataset.sampleValues;
    if (!payload) {
      return;
    }
    applyValues(JSON.parse(payload));
    setStatus(`Loaded ${button.dataset.presetTitle || "preset"} case.`, "success");
    await refreshResults();
  });
});

if (clearButton instanceof HTMLButtonElement) {
  clearButton.addEventListener("click", async () => {
    resetForm();
    setStatus("Form cleared.", "neutral");
    await refreshResults();
  });
}

document.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) {
    return;
  }

  const copyTarget = target.getAttribute("data-copy-target");
  if (!copyTarget) {
    return;
  }

  const source = document.getElementById(copyTarget);
  if (!(source instanceof HTMLTextAreaElement)) {
    return;
  }

  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(source.value);
    } else {
      source.focus();
      source.select();
      document.execCommand("copy");
    }
    const previousLabel = target.textContent;
    target.textContent = "Copied";
    window.setTimeout(() => {
      target.textContent = previousLabel;
    }, 1200);
  } catch (_error) {
    setStatus("Clipboard access failed. You can still copy directly from the text box.", "error");
  }
});
