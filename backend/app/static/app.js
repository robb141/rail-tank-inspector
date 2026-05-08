const form = document.querySelector("#inspectionForm");
const resultBox = document.querySelector("#resultBox");
const recentList = document.querySelector("#recentList");
const queueList = document.querySelector("#queueList");
const apiStatus = document.querySelector("#apiStatus");
const resetSample = document.querySelector("#resetSample");
const clearDraft = document.querySelector("#clearDraft");
const syncQueue = document.querySelector("#syncQueue");
const draftStatus = document.querySelector("#draftStatus");

const sampleValues = Object.fromEntries(new FormData(form).entries());
const DB_NAME = "rail-inspect";
const DB_VERSION = 2;
const QUEUE_STORE = "pending-inspections";
const DRAFT_STORE = "drafts";
const CURRENT_DRAFT_ID = "current-inspection";

class ApiError extends Error {
  constructor(message, canQueue = false) {
    super(message);
    this.canQueue = canQueue;
  }
}

function openDb() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(QUEUE_STORE)) {
        db.createObjectStore(QUEUE_STORE, { keyPath: "localId" });
      }
      if (!db.objectStoreNames.contains(DRAFT_STORE)) {
        db.createObjectStore(DRAFT_STORE, { keyPath: "draftId" });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function withQueueStore(mode, callback) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(QUEUE_STORE, mode);
    const store = transaction.objectStore(QUEUE_STORE);
    const result = callback(store);

    transaction.oncomplete = () => {
      db.close();
      resolve(result);
    };
    transaction.onerror = () => {
      db.close();
      reject(transaction.error);
    };
  });
}

async function withDraftStore(mode, callback) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(DRAFT_STORE, mode);
    const store = transaction.objectStore(DRAFT_STORE);
    const result = callback(store);

    transaction.oncomplete = () => {
      db.close();
      resolve(result);
    };
    transaction.onerror = () => {
      db.close();
      reject(transaction.error);
    };
  });
}

async function queueInspection(payload, reason) {
  const now = new Date().toISOString();
  const item = {
    localId: crypto.randomUUID(),
    payload,
    status: "pending",
    createdAt: now,
    updatedAt: now,
    lastError: reason || null,
  };
  await withQueueStore("readwrite", (store) => store.put(item));
  return item;
}

async function updateQueuedInspection(item) {
  item.updatedAt = new Date().toISOString();
  await withQueueStore("readwrite", (store) => store.put(item));
}

async function deleteQueuedInspection(localId) {
  await withQueueStore("readwrite", (store) => store.delete(localId));
}

async function listQueuedInspections() {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(QUEUE_STORE, "readonly");
    const store = transaction.objectStore(QUEUE_STORE);
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
    transaction.oncomplete = () => db.close();
    transaction.onerror = () => {
      db.close();
      reject(transaction.error);
    };
  });
}

async function saveDraft() {
  const draft = {
    draftId: CURRENT_DRAFT_ID,
    values: Object.fromEntries(new FormData(form).entries()),
    updatedAt: new Date().toISOString(),
  };
  await withDraftStore("readwrite", (store) => store.put(draft));
  draftStatus.textContent = `Koncept uložený ${new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  })}`;
}

async function loadDraft() {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(DRAFT_STORE, "readonly");
    const store = transaction.objectStore(DRAFT_STORE);
    const request = store.get(CURRENT_DRAFT_ID);
    request.onsuccess = () => resolve(request.result || null);
    request.onerror = () => reject(request.error);
    transaction.oncomplete = () => db.close();
    transaction.onerror = () => {
      db.close();
      reject(transaction.error);
    };
  });
}

async function clearSavedDraft() {
  await withDraftStore("readwrite", (store) => store.delete(CURRENT_DRAFT_ID));
  draftStatus.textContent = "Koncept vymazaný";
}

function applyFormValues(values) {
  for (const [name, value] of Object.entries(values)) {
    const field = form.elements.namedItem(name);
    if (field) {
      field.value = value;
    }
  }
}

function debounce(callback, delay) {
  let timeoutId = null;
  return (...args) => {
    window.clearTimeout(timeoutId);
    timeoutId = window.setTimeout(() => callback(...args), delay);
  };
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#039;");
}

function optionalString(value) {
  const trimmed = String(value || "").trim();
  return trimmed === "" ? null : trimmed;
}

function optionalNumber(value) {
  const trimmed = String(value || "").trim();
  return trimmed === "" ? null : Number(trimmed);
}

function payloadFromForm() {
  const data = new FormData(form);
  return {
    certificate_number: data.get("certificate_number").trim(),
    holder_name: data.get("holder_name").trim(),
    holder_street: optionalString(data.get("holder_street")),
    holder_postal_code: optionalString(data.get("holder_postal_code")),
    holder_city: optionalString(data.get("holder_city")),
    holder_country: optionalString(data.get("holder_country")),
    type_approval_number: optionalString(data.get("type_approval_number")),
    tank_manufacturer_name: optionalString(data.get("tank_manufacturer_name")),
    tank_serial_number: optionalString(data.get("tank_serial_number")),
    year_of_manufacture: optionalNumber(data.get("year_of_manufacture")),
    tank_identification: data.get("tank_identification").trim(),
    tank_code: optionalString(data.get("tank_code")),
    test_pressure: optionalString(data.get("test_pressure")),
    working_pressure: optionalString(data.get("working_pressure")),
    calculation_pressure: optionalString(data.get("calculation_pressure")),
    safety_valve_pressure: optionalString(data.get("safety_valve_pressure")),
    vacuum_valve_pressure: optionalString(data.get("vacuum_valve_pressure")),
    capacity_liters: optionalNumber(data.get("capacity_liters")),
    cargo_substances: optionalString(data.get("cargo_substances")),
    special_provisions: optionalString(data.get("special_provisions")),
    tank_plate_stamp: optionalString(data.get("tank_plate_stamp")),
    next_inspection: optionalString(data.get("next_inspection")),
    inspection_place: data.get("inspection_place").trim(),
    inspection_date: data.get("inspection_date"),
    inspector_name: data.get("inspector_name").trim(),
    result: data.get("result"),
    remarks: optionalString(data.get("remarks")),
  };
}

function formValuesFromPayload(payload) {
  return Object.fromEntries(
    Object.entries(payload).map(([key, value]) => [key, value ?? ""]),
  );
}

async function loadPayloadIntoForm(payload, message) {
  applyFormValues(formValuesFromPayload(payload));
  await saveDraft();
  resultBox.className = "result";
  resultBox.innerHTML = `
    <div class="record">
      <strong>${escapeHtml(message)}</strong>
      <span>${escapeHtml(payload.certificate_number)} · ${escapeHtml(payload.tank_identification)}</span>
    </div>
  `;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function setStatus(ok, text) {
  apiStatus.textContent = text;
  apiStatus.className = ok ? "status ok" : "status error";
}

function renderResult(response) {
  const links = [];
  if (response.initial_record_docx_url) {
    links.push(`
      <div class="doc-link">
        <a href="${response.initial_record_docx_url}" download>Stiahnuť Prvotný záznam Z</a>
      </div>
    `);
  }
  if (response.certificate_docx_url) {
    links.push(`
      <div class="doc-link">
        <a href="${response.certificate_docx_url}" download>Stiahnuť Osvedčenie o skúške Z</a>
      </div>
    `);
  }
  if (links.length === 0) {
    links.push("<div class=\"muted\">Záznam bol uložený, certifikát sa negeneruje pri nevyhovujúcom výsledku.</div>");
  }

  resultBox.className = "result";
  resultBox.innerHTML = `
    <div class="record">
      <strong>${response.inspection.certificate_number}</strong>
      <span>${response.inspection.tank_identification} · ID ${response.inspection.id}</span>
    </div>
    ${links.join("")}
  `;
}

function documentLinksHtml(response) {
  const links = [];
  if (response.initial_record_docx_url) {
    links.push(`
      <div class="doc-link">
        <a href="${response.initial_record_docx_url}" download>Stiahnuť Prvotný záznam Z</a>
      </div>
    `);
  }
  if (response.certificate_docx_url) {
    links.push(`
      <div class="doc-link">
        <a href="${response.certificate_docx_url}" download>Stiahnuť Osvedčenie o skúške Z</a>
      </div>
    `);
  }
  return links.join("");
}

function openDownload(url) {
  const link = document.createElement("a");
  link.href = url;
  link.download = "";
  document.body.appendChild(link);
  link.click();
  link.remove();
}

async function generateDocument(inspectionId, documentType) {
  const response = await fetch(`/inspections/${inspectionId}/${documentType}`, {
    method: "POST",
  });
  const body = await response.json();
  if (!response.ok) {
    throw new Error(JSON.stringify(body, null, 2));
  }
  return body;
}

function renderError(error) {
  resultBox.className = "result error-text";
  resultBox.textContent = error;
}

function renderQueued(item) {
  resultBox.className = "result";
  resultBox.innerHTML = `
    <div class="record warning">
      <strong>Uložené offline</strong>
      <span>${item.payload.certificate_number} · ${item.payload.tank_identification}</span>
    </div>
    <div class="muted">Záznam je uložený v tablete a čaká na synchronizáciu.</div>
  `;
}

async function renderQueue() {
  try {
    const items = await listQueuedInspections();
    syncQueue.disabled = items.length === 0;
    if (items.length === 0) {
      queueList.className = "recent muted";
      queueList.textContent = "Offline fronta je prázdna.";
      return;
    }
    queueList.className = "recent";
    queueList.innerHTML = items
      .sort((a, b) => a.createdAt.localeCompare(b.createdAt))
      .map((item) => `
        <div class="record ${item.status === "failed" ? "failed" : "warning"}">
          <strong>${escapeHtml(item.payload.certificate_number)}</strong>
          <span>${escapeHtml(item.payload.tank_identification)} · ${escapeHtml(item.status)}</span>
          ${item.lastError ? `<span>${escapeHtml(item.lastError)}</span>` : ""}
          <div class="record-actions">
            <button
              type="button"
              class="small secondary"
              data-queue-action="edit"
              data-local-id="${escapeHtml(item.localId)}"
            >
              Upraviť
            </button>
            <button
              type="button"
              class="small danger-button"
              data-queue-action="delete"
              data-local-id="${escapeHtml(item.localId)}"
            >
              Vymazať
            </button>
          </div>
        </div>
      `).join("");
  } catch (error) {
    queueList.className = "recent error-text";
    queueList.textContent = `IndexedDB chyba: ${error.message}`;
  }
}

async function loadRecent() {
  try {
    const response = await fetch("/inspections");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const inspections = await response.json();
    if (inspections.length === 0) {
      recentList.className = "recent muted";
      recentList.textContent = "Zatiaľ nie sú uložené žiadne záznamy.";
      return;
    }
    recentList.className = "recent";
    recentList.innerHTML = inspections.slice(0, 6).map((inspection) => `
      <div class="record">
        <strong>${escapeHtml(inspection.certificate_number)}</strong>
        <span>${escapeHtml(inspection.tank_identification)} · ${escapeHtml(inspection.inspection_date)} · ${escapeHtml(inspection.result)}</span>
        <div class="record-actions">
          <button
            type="button"
            class="small secondary"
            data-load-inspection="${inspection.id}"
          >
            Použiť ako vzor
          </button>
          <button
            type="button"
            class="small secondary"
            data-document="initial-record"
            data-inspection-id="${inspection.id}"
          >
            Prvotný záznam
          </button>
          ${inspection.result === "pass" ? `
            <button
              type="button"
              class="small secondary"
              data-document="certificate"
              data-inspection-id="${inspection.id}"
            >
              Osvedčenie
            </button>
          ` : ""}
        </div>
      </div>
    `).join("");
  } catch (error) {
    recentList.className = "recent error-text";
    recentList.textContent = `Nepodarilo sa načítať záznamy: ${error.message}`;
  }
}

async function checkHealth() {
  try {
    const response = await fetch("/health");
    setStatus(response.ok, response.ok ? "Backend online" : "Backend chyba");
  } catch {
    setStatus(false, "Backend nedostupný");
  }
}

async function submitPayload(payload) {
  let response;
  try {
    response = await fetch("/inspections", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    throw new ApiError(error.message, true);
  }

  let body;
  try {
    body = await response.json();
  } catch {
    body = { detail: "Server returned an empty or invalid response." };
  }

  if (!response.ok) {
    throw new ApiError(JSON.stringify(body, null, 2), response.status >= 500);
  }
  return body;
}

async function syncQueuedInspections() {
  const items = await listQueuedInspections();
  if (items.length === 0) {
    await renderQueue();
    return;
  }

  syncQueue.disabled = true;
  syncQueue.textContent = "Synchronizujem...";
  let synced = 0;
  let failed = 0;

  for (const item of items) {
    try {
      await submitPayload(item.payload);
      await deleteQueuedInspection(item.localId);
      synced += 1;
    } catch (error) {
      item.status = "failed";
      item.lastError = error.message;
      await updateQueuedInspection(item);
      failed += 1;
    }
  }

  resultBox.className = failed === 0 ? "result" : "result error-text";
  resultBox.textContent = failed === 0
    ? `Synchronizované záznamy: ${synced}`
    : `Synchronizované: ${synced}. Zlyhalo: ${failed}.`;

  await renderQueue();
  await loadRecent();
  await checkHealth();
  syncQueue.textContent = "Synchronizovať";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = payloadFromForm();
  const submitButton = form.querySelector("button[type='submit']");
  submitButton.disabled = true;
  submitButton.textContent = "Generujem...";
  resultBox.className = "result muted";
  resultBox.textContent = "Ukladám záznam a generujem dokumenty...";

  try {
    const body = await submitPayload(payload);
    await clearSavedDraft();
    renderResult(body);
    await loadRecent();
  } catch (error) {
    if (error.canQueue) {
      const queued = await queueInspection(payload, error.message);
      await clearSavedDraft();
      renderQueued(queued);
      await renderQueue();
      await checkHealth();
    } else {
      renderError(error.message);
    }
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Vygenerovať dokumenty";
  }
});

resetSample.addEventListener("click", () => {
  applyFormValues(sampleValues);
  saveDraft();
});

clearDraft.addEventListener("click", async () => {
  applyFormValues(sampleValues);
  await clearSavedDraft();
});

syncQueue.addEventListener("click", async () => {
  try {
    await syncQueuedInspections();
  } catch (error) {
    renderError(error.message);
  } finally {
    syncQueue.textContent = "Synchronizovať";
  }
});

queueList.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-queue-action]");
  if (!button) {
    return;
  }

  try {
    const items = await listQueuedInspections();
    const item = items.find((queued) => queued.localId === button.dataset.localId);
    if (!item) {
      throw new Error("Offline záznam sa nenašiel.");
    }

    if (button.dataset.queueAction === "edit") {
      await loadPayloadIntoForm(item.payload, "Offline záznam načítaný do formulára");
      await deleteQueuedInspection(item.localId);
    }

    if (button.dataset.queueAction === "delete") {
      await deleteQueuedInspection(item.localId);
      resultBox.className = "result muted";
      resultBox.textContent = "Offline záznam bol vymazaný.";
    }

    await renderQueue();
  } catch (error) {
    renderError(error.message);
  }
});

recentList.addEventListener("click", async (event) => {
  const loadButton = event.target.closest("button[data-load-inspection]");
  if (loadButton) {
    try {
      const response = await fetch(`/inspections/${loadButton.dataset.loadInspection}`);
      const inspection = await response.json();
      if (!response.ok) {
        throw new Error(JSON.stringify(inspection, null, 2));
      }
      await loadPayloadIntoForm(inspection, "Záznam načítaný ako vzor");
    } catch (error) {
      renderError(error.message);
    }
    return;
  }

  const button = event.target.closest("button[data-document]");
  if (!button) {
    return;
  }

  const originalText = button.textContent;
  button.disabled = true;
  button.textContent = "Generujem...";

  try {
    const body = await generateDocument(button.dataset.inspectionId, button.dataset.document);
    const downloadUrl = body.initial_record_docx_url || body.certificate_docx_url;
    if (!downloadUrl) {
      throw new Error("Server nevrátil odkaz na dokument.");
    }
    openDownload(downloadUrl);
    resultBox.className = "result";
    resultBox.innerHTML = documentLinksHtml(body);
  } catch (error) {
    renderError(error.message);
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
});

window.addEventListener("online", () => {
  setStatus(true, "Sieť dostupná");
  syncQueuedInspections();
});

window.addEventListener("offline", () => {
  setStatus(false, "Offline režim");
});

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/service-worker.js").catch((error) => {
      console.warn("Service worker registration failed:", error);
    });
  });
}

const debouncedSaveDraft = debounce(() => {
  saveDraft().catch((error) => {
    draftStatus.textContent = `Koncept sa nepodarilo uložiť: ${error.message}`;
  });
}, 400);

form.addEventListener("input", debouncedSaveDraft);
form.addEventListener("change", debouncedSaveDraft);

async function boot() {
  try {
    const draft = await loadDraft();
    if (draft) {
      applyFormValues(draft.values);
      draftStatus.textContent = "Obnovený lokálny koncept";
    }
  } catch (error) {
    draftStatus.textContent = `Koncept sa nepodarilo načítať: ${error.message}`;
  }

  checkHealth();
  loadRecent();
  renderQueue();
}

boot();
