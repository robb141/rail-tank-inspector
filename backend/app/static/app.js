const form = document.querySelector("#inspectionForm");
const resultBox = document.querySelector("#resultBox");
const recentList = document.querySelector("#recentList");
const queueList = document.querySelector("#queueList");
const apiStatus = document.querySelector("#apiStatus");
const clearDraft = document.querySelector("#clearDraft");
const cancelEdit = document.querySelector("#cancelEdit");
const submitInspection = document.querySelector("#submitInspection");
const syncQueue = document.querySelector("#syncQueue");
const draftStatus = document.querySelector("#draftStatus");
const recentSearch = document.querySelector("#recentSearch");
const recentResultFilter = document.querySelector("#recentResultFilter");
const refreshRecent = document.querySelector("#refreshRecent");
const recentCount = document.querySelector("#recentCount");
const inspectionDetail = document.querySelector("#inspectionDetail");
const closeDetail = document.querySelector("#closeDetail");
const detailTitle = document.querySelector("#detailTitle");
const detailSubtitle = document.querySelector("#detailSubtitle");
const detailContent = document.querySelector("#detailContent");
const detailActions = document.querySelector("#detailActions");

let recentInspections = [];
let editingInspectionId = null;
const DB_NAME = "rail-inspect";
const DB_VERSION = 2;
const QUEUE_STORE = "pending-inspections";
const DRAFT_STORE = "drafts";
const CURRENT_DRAFT_ID = "current-inspection";
const VALUE_LABELS = {
  pass: "Vyhovuje",
  fail: "Nevyhovuje",
  not_applicable: "Nevzťahuje sa",
  periodic: "Periodická P",
  intermediate: "Medzikontrola L",
  initial: "Východisková",
  exceptional: "Mimoriadna",
};
const DETAIL_GROUPS = [
  {
    title: "Identifikácia",
    fields: [
      ["certificate_number", "Číslo osvedčenia"],
      ["order_number", "Č. zákazky / objednávky"],
      ["tank_identification", "Označenie cisterny"],
      ["inspection_place", "Miesto skúšky"],
      ["inspection_date", "Dátum skúšky"],
      ["inspector_name", "Inšpektor"],
      ["result", "Výsledok"],
      ["current_inspection_type", "Aktuálna skúška"],
    ],
  },
  {
    title: "Držiteľ",
    fields: [
      ["holder_name", "Držiteľ"],
      ["holder_street", "Ulica"],
      ["holder_postal_code", "PSČ"],
      ["holder_city", "Mesto"],
      ["holder_country", "Štát"],
    ],
  },
  {
    title: "Cisterna",
    fields: [
      ["type_approval_number", "Číslo schválenia typu"],
      ["tank_manufacturer_name", "Výrobca kotla"],
      ["tank_serial_number", "Číslo kotla"],
      ["year_of_manufacture", "Rok výroby"],
      ["tank_code", "Tankcode"],
      ["capacity_liters", "Objem v litroch"],
      ["last_inspection_date_type", "Dátum a druh poslednej skúšky"],
      ["periodic_inspection_date", "P"],
      ["intermediate_inspection_date", "L"],
    ],
  },
  {
    title: "Tlaky a ventily",
    fields: [
      ["test_pressure", "Skúšobný tlak"],
      ["working_pressure", "Pracovný tlak"],
      ["calculation_pressure", "Výpočtový tlak"],
      ["current_test_pressure", "Aktuálny skúšobný tlak"],
      ["safety_valve_pressure", "Pretlak poistného ventilu"],
      ["vacuum_valve_pressure", "Podtlak poistného ventilu"],
      ["safety_valve_type", "Typ poistného ventilu"],
      ["safety_valve_number", "Číslo PV"],
    ],
  },
  {
    title: "Kontroly",
    fields: [
      ["external_inspection_result", "Vonkajšia prehliadka"],
      ["internal_inspection_result", "Vnútorná prehliadka"],
      ["weld_inspection_result", "Kontrola zvarov"],
      ["plate_inspection_result", "Kontrola štítkov"],
      ["heating_coils_external_result", "Vykurovacie hady vonk."],
      ["heating_coils_internal_result", "Vykurovacie hady vnút."],
      ["side_valves_side_1_result", "Bočné ventily I. str."],
      ["side_valves_side_2_result", "Bočné ventily II. str."],
      ["center_valve_result", "Stredový ventil"],
      ["lid_gasket_result", "Veko + tesnenie"],
      ["grounding_result", "Uzemnenie"],
    ],
  },
  {
    title: "Protokoly a merania",
    fields: [
      ["utt_protocol_number", "Protokol UTT"],
      ["rubber_protocol_number", "Protokol gum."],
      ["measured_wall_thickness_front_mm", "Min. hrúbka čelá mm"],
      ["measured_wall_thickness_shell_mm", "Min. hrúbka luby mm"],
      ["measuring_device_number", "Č. mer. zariadenia"],
      ["calibration_valid_until", "Kalibrácia do"],
      ["test_duration", "Čas trvania skúšky"],
    ],
  },
  {
    title: "Poznámky",
    fields: [
      ["cargo_substances", "Ložný tovar"],
      ["special_provisions", "Zvláštne ustanovenia"],
      ["tank_plate_stamp", "Orazenie štítka"],
      ["next_inspection", "Budúca skúška"],
      ["remarks", "Poznámky"],
      ["extraordinary_inspection_reason", "Dôvod mimoriadnej kontroly"],
    ],
  },
  {
    title: "Spôsobilosť dodávateľa",
    fields: [
      ["supplier_device_owner", "Vlastník zariadenia"],
      ["supplier_device_type", "Druh zariadenia"],
      ["supplier_device_serial_number", "Výrobné číslo zariadenia"],
      ["supplier_calibration_validity", "Platnosť kalibrácie"],
      ["supplier_calibration_company", "Kalibračná spoločnosť"],
      ["supplier_snas_registration_number", "Registračné číslo SNAS"],
      ["supplier_other_findings", "Iné zistenia"],
    ],
  },
];

class ApiError extends Error {
  constructor(message, canQueue = false) {
    super(message);
    this.canQueue = canQueue;
  }
}

function formatApiError(body, fallback = "Server error") {
  if (body && typeof body.detail === "string") {
    return body.detail;
  }
  if (body && Array.isArray(body.detail)) {
    return body.detail
      .map((item) => item.msg || JSON.stringify(item))
      .join("\n");
  }
  if (body && typeof body === "object") {
    return JSON.stringify(body, null, 2);
  }
  return fallback;
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

async function queueInspection(payload, reason, operation = "create", inspectionId = null) {
  const now = new Date().toISOString();
  const item = {
    localId: crypto.randomUUID(),
    operation,
    inspectionId,
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
    editingInspectionId,
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

function displayValue(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  return VALUE_LABELS[value] || String(value);
}

function queuedOperationLabel(item) {
  return (item.operation || "create") === "update"
    ? `Úprava ID ${item.inspectionId}`
    : "Nový záznam";
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
    order_number: optionalString(data.get("order_number")),
    last_inspection_date_type: optionalString(data.get("last_inspection_date_type")),
    periodic_inspection_date: optionalString(data.get("periodic_inspection_date")),
    intermediate_inspection_date: optionalString(data.get("intermediate_inspection_date")),
    current_inspection_type: optionalString(data.get("current_inspection_type")),
    test_pressure: optionalString(data.get("test_pressure")),
    working_pressure: optionalString(data.get("working_pressure")),
    calculation_pressure: optionalString(data.get("calculation_pressure")),
    current_test_pressure: optionalString(data.get("current_test_pressure")),
    safety_valve_pressure: optionalString(data.get("safety_valve_pressure")),
    vacuum_valve_pressure: optionalString(data.get("vacuum_valve_pressure")),
    external_inspection_result: optionalString(data.get("external_inspection_result")),
    internal_inspection_result: optionalString(data.get("internal_inspection_result")),
    weld_inspection_result: optionalString(data.get("weld_inspection_result")),
    plate_inspection_result: optionalString(data.get("plate_inspection_result")),
    heating_coils_external_result: optionalString(data.get("heating_coils_external_result")),
    heating_coils_internal_result: optionalString(data.get("heating_coils_internal_result")),
    side_valves_side_1_result: optionalString(data.get("side_valves_side_1_result")),
    side_valves_side_2_result: optionalString(data.get("side_valves_side_2_result")),
    center_valve_result: optionalString(data.get("center_valve_result")),
    lid_gasket_result: optionalString(data.get("lid_gasket_result")),
    safety_valve_type: optionalString(data.get("safety_valve_type")),
    safety_valve_number: optionalString(data.get("safety_valve_number")),
    grounding_result: optionalString(data.get("grounding_result")),
    utt_protocol_number: optionalString(data.get("utt_protocol_number")),
    rubber_protocol_number: optionalString(data.get("rubber_protocol_number")),
    measured_wall_thickness_front_mm: optionalString(data.get("measured_wall_thickness_front_mm")),
    measured_wall_thickness_shell_mm: optionalString(data.get("measured_wall_thickness_shell_mm")),
    measuring_device_number: optionalString(data.get("measuring_device_number")),
    calibration_valid_until: optionalString(data.get("calibration_valid_until")),
    test_duration: optionalString(data.get("test_duration")),
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
    extraordinary_inspection_reason: optionalString(data.get("extraordinary_inspection_reason")),
    supplier_device_owner: optionalString(data.get("supplier_device_owner")),
    supplier_device_type: optionalString(data.get("supplier_device_type")),
    supplier_device_serial_number: optionalString(data.get("supplier_device_serial_number")),
    supplier_calibration_validity: optionalString(data.get("supplier_calibration_validity")),
    supplier_calibration_company: optionalString(data.get("supplier_calibration_company")),
    supplier_snas_registration_number: optionalString(data.get("supplier_snas_registration_number")),
    supplier_other_findings: optionalString(data.get("supplier_other_findings")),
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

function setEditingInspection(inspectionId) {
  editingInspectionId = inspectionId;
  submitInspection.textContent = inspectionId ? "Uložiť zmeny" : "Vygenerovať dokumenty";
  cancelEdit.classList.toggle("hidden", !inspectionId);
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
  if (response.initial_record_pdf_url) {
    links.push(`
      <div class="doc-link">
        <a href="${response.initial_record_pdf_url}" download>Stiahnuť Prvotný záznam Z PDF</a>
      </div>
    `);
  }
  if (response.certificate_pdf_url) {
    links.push(`
      <div class="doc-link">
        <a href="${response.certificate_pdf_url}" download>Stiahnuť Osvedčenie o skúške Z PDF</a>
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

function currentFilteredInspections(inspections = recentInspections) {
  return inspections.filter(inspectionMatchesFilters);
}

async function generateDocument(inspectionId, documentType) {
  const response = await fetch(`/inspections/${inspectionId}/${documentType}`, {
    method: "POST",
  });
  const body = await response.json();
  if (!response.ok) {
    throw new Error(formatApiError(body, `HTTP ${response.status}`));
  }
  return body;
}

async function fetchInspection(inspectionId) {
  const response = await fetch(`/inspections/${inspectionId}`);
  const inspection = await response.json();
  if (!response.ok) {
    throw new Error(formatApiError(inspection, `HTTP ${response.status}`));
  }
  return inspection;
}

async function handleLoadInspection(inspectionId) {
  const inspection = await fetchInspection(inspectionId);
  await loadPayloadIntoForm(inspection, "Záznam načítaný ako vzor");
  setEditingInspection(null);
  closeInspectionDetail();
}

async function handleEditInspection(inspectionId) {
  const inspection = await fetchInspection(inspectionId);
  await loadPayloadIntoForm(inspection, "Záznam načítaný na úpravu");
  setEditingInspection(Number(inspectionId));
  closeInspectionDetail();
}

async function handleDocumentButton(button) {
  const originalText = button.textContent;
  button.disabled = true;
  button.textContent = "Generujem...";

  try {
    const body = await generateDocument(button.dataset.inspectionId, button.dataset.document);
    const downloadUrl = body.initial_record_docx_url
      || body.certificate_docx_url
      || body.initial_record_pdf_url
      || body.certificate_pdf_url;
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
}

function renderError(error) {
  resultBox.className = "result error-text";
  resultBox.textContent = error;
}

function renderQueued(item) {
  const title = (item.operation || "create") === "update"
    ? "Úprava uložená offline"
    : "Uložené offline";
  resultBox.className = "result";
  resultBox.innerHTML = `
    <div class="record warning">
      <strong>${escapeHtml(title)}</strong>
      <span>${item.payload.certificate_number} · ${item.payload.tank_identification}</span>
    </div>
    <div class="muted">Zmena je uložená v tablete a čaká na synchronizáciu.</div>
  `;
}

function inspectionMatchesFilters(inspection) {
  const query = recentSearch.value.trim().toLowerCase();
  const resultFilter = recentResultFilter.value;
  const searchable = [
    inspection.certificate_number,
    inspection.tank_identification,
    inspection.holder_name,
    inspection.inspection_place,
    inspection.inspection_date,
    inspection.inspector_name,
  ].join(" ").toLowerCase();

  return (!query || searchable.includes(query))
    && (!resultFilter || inspection.result === resultFilter);
}

function documentActionButtonsHtml(inspection) {
  return `
    <button
      type="button"
      class="small secondary"
      data-edit-inspection="${inspection.id}"
    >
      Upraviť záznam
    </button>
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
    <button
      type="button"
      class="small secondary"
      data-document="initial-record/pdf"
      data-inspection-id="${inspection.id}"
    >
      Prvotný záznam PDF
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
      <button
        type="button"
        class="small secondary"
        data-document="certificate/pdf"
        data-inspection-id="${inspection.id}"
      >
        Osvedčenie PDF
      </button>
    ` : ""}
  `;
}

function closeInspectionDetail() {
  inspectionDetail.classList.add("hidden");
  detailContent.innerHTML = "";
  detailActions.innerHTML = "";
}

function renderInspectionDetail(inspection) {
  detailTitle.textContent = inspection.certificate_number || "Detail záznamu";
  detailSubtitle.textContent = [
    inspection.tank_identification,
    inspection.inspection_date,
    inspection.holder_name,
  ].filter(Boolean).join(" · ");

  detailContent.innerHTML = DETAIL_GROUPS.map((group) => `
    <section class="detail-section">
      <h3>${escapeHtml(group.title)}</h3>
      <div class="detail-grid">
        ${group.fields.map(([key, label]) => `
          <div class="detail-row">
            <div class="detail-label">${escapeHtml(label)}</div>
            <div class="detail-value">${escapeHtml(displayValue(inspection[key]))}</div>
          </div>
        `).join("")}
      </div>
    </section>
  `).join("");
  detailActions.innerHTML = documentActionButtonsHtml(inspection);
  inspectionDetail.classList.remove("hidden");
}

async function openInspectionDetail(inspectionId) {
  const inspection = await fetchInspection(inspectionId);
  renderInspectionDetail(inspection);
}

function renderRecent(inspections) {
  const filtered = currentFilteredInspections(inspections);
  if (inspections.length === 0) {
    recentList.className = "recent muted";
    recentList.textContent = "Zatiaľ nie sú uložené žiadne záznamy.";
    recentCount.textContent = "0 záznamov";
    return;
  }
  if (filtered.length === 0) {
    recentList.className = "recent muted";
    recentList.textContent = "Nenašli sa žiadne záznamy pre tento filter.";
    recentCount.textContent = `0 z ${inspections.length} záznamov`;
    return;
  }

  recentCount.textContent = `${filtered.length} z ${inspections.length} záznamov`;
  recentList.className = "recent";
  recentList.innerHTML = filtered.slice(0, 12).map((inspection) => `
    <div class="record">
      <strong>${escapeHtml(inspection.certificate_number)}</strong>
      <span>${escapeHtml(inspection.tank_identification)} · ${escapeHtml(inspection.inspection_date)} · ${escapeHtml(inspection.result)}</span>
      <span>${escapeHtml(inspection.holder_name)}</span>
      <div class="record-actions">
        <button
          type="button"
          class="small secondary"
          data-view-inspection="${inspection.id}"
        >
          Detail
        </button>
        ${documentActionButtonsHtml(inspection)}
      </div>
    </div>
  `).join("");
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
          <span>${escapeHtml(item.payload.tank_identification)} · ${escapeHtml(queuedOperationLabel(item))} · ${escapeHtml(item.status)}</span>
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
    recentInspections = await response.json();
    renderRecent(recentInspections);
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
    throw new ApiError(formatApiError(body, `HTTP ${response.status}`), response.status >= 500);
  }
  return body;
}

async function updatePayload(inspectionId, payload) {
  let response;
  try {
    response = await fetch(`/inspections/${inspectionId}`, {
      method: "PUT",
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
    throw new ApiError(formatApiError(body, `HTTP ${response.status}`), response.status >= 500);
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
      if ((item.operation || "create") === "update") {
        if (!item.inspectionId) {
          throw new Error("Offline úprava nemá ID pôvodného záznamu.");
        }
        await updatePayload(item.inspectionId, item.payload);
      } else {
        await submitPayload(item.payload);
      }
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
  const submitButton = submitInspection;
  const isEditing = editingInspectionId !== null;
  submitButton.disabled = true;
  submitButton.textContent = isEditing ? "Ukladám..." : "Generujem...";
  resultBox.className = "result muted";
  resultBox.textContent = isEditing
    ? "Ukladám zmeny a generujem nové dokumenty..."
    : "Ukladám záznam a generujem dokumenty...";

  try {
    const body = isEditing
      ? await updatePayload(editingInspectionId, payload)
      : await submitPayload(payload);
    await clearSavedDraft();
    setEditingInspection(null);
    renderResult(body);
    await loadRecent();
  } catch (error) {
    if (error.canQueue) {
      const queued = await queueInspection(
        payload,
        error.message,
        isEditing ? "update" : "create",
        isEditing ? editingInspectionId : null,
      );
      await clearSavedDraft();
      setEditingInspection(null);
      renderQueued(queued);
      await renderQueue();
      await checkHealth();
    } else {
      renderError(error.message);
    }
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = editingInspectionId ? "Uložiť zmeny" : "Vygenerovať dokumenty";
  }
});

cancelEdit.addEventListener("click", async () => {
  setEditingInspection(null);
  await clearSavedDraft();
  resultBox.className = "result muted";
  resultBox.textContent = "Úprava bola zrušená.";
});

clearDraft.addEventListener("click", async () => {
  form.reset();
  setEditingInspection(null);
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

recentSearch.addEventListener("input", () => renderRecent(recentInspections));
recentResultFilter.addEventListener("change", () => renderRecent(recentInspections));
refreshRecent.addEventListener("click", () => loadRecent());

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
      setEditingInspection((item.operation || "create") === "update" ? item.inspectionId : null);
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
  const viewButton = event.target.closest("button[data-view-inspection]");
  if (viewButton) {
    try {
      await openInspectionDetail(viewButton.dataset.viewInspection);
    } catch (error) {
      renderError(error.message);
    }
    return;
  }

  const editButton = event.target.closest("button[data-edit-inspection]");
  if (editButton) {
    try {
      await handleEditInspection(editButton.dataset.editInspection);
    } catch (error) {
      renderError(error.message);
    }
    return;
  }

  const loadButton = event.target.closest("button[data-load-inspection]");
  if (loadButton) {
    try {
      await handleLoadInspection(loadButton.dataset.loadInspection);
    } catch (error) {
      renderError(error.message);
    }
    return;
  }

  const button = event.target.closest("button[data-document]");
  if (!button) {
    return;
  }

  await handleDocumentButton(button);
});

detailActions.addEventListener("click", async (event) => {
  const editButton = event.target.closest("button[data-edit-inspection]");
  if (editButton) {
    try {
      await handleEditInspection(editButton.dataset.editInspection);
    } catch (error) {
      renderError(error.message);
    }
    return;
  }

  const loadButton = event.target.closest("button[data-load-inspection]");
  if (loadButton) {
    try {
      await handleLoadInspection(loadButton.dataset.loadInspection);
    } catch (error) {
      renderError(error.message);
    }
    return;
  }

  const button = event.target.closest("button[data-document]");
  if (button) {
    await handleDocumentButton(button);
  }
});

closeDetail.addEventListener("click", closeInspectionDetail);

inspectionDetail.addEventListener("click", (event) => {
  if (event.target === inspectionDetail) {
    closeInspectionDetail();
  }
});

window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !inspectionDetail.classList.contains("hidden")) {
    closeInspectionDetail();
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
    navigator.serviceWorker.register("/static/service-worker.js").then((registration) => {
      registration.addEventListener("updatefound", () => {
        const worker = registration.installing;
        if (!worker) {
          return;
        }
        worker.addEventListener("statechange", () => {
          if (worker.state === "activated" && navigator.serviceWorker.controller) {
            window.location.reload();
          }
        });
      });
    }).catch((error) => {
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
      setEditingInspection(draft.editingInspectionId || null);
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
