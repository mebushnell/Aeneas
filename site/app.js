const state = {
  index: null,
  books: [],
  currentBook: null,
  currentPayload: null,
  records: [],
  currentRecordIndex: 0,
};

const els = {};

function $(id) {
  return document.getElementById(id);
}

function safeText(value, fallback = "") {
  return value === null || value === undefined || value === "" ? fallback : String(value);
}

function getTopArray(obj, keys) {
  for (const key of keys) {
    if (Array.isArray(obj?.[key])) return obj[key];
  }
  return [];
}

function pick(obj, keys, fallback = null) {
  if (!obj || typeof obj !== "object") return fallback;
  for (const key of keys) {
    if (obj[key] !== undefined && obj[key] !== null && obj[key] !== "") return obj[key];
  }
  return fallback;
}

function normalizeWord(word) {
  if (!word || typeof word !== "object") {
    return { display: "", orig: "", norm: "", mod: "", pos: "", sem: "" };
  }

  const display = safeText(pick(word, ["display", "t", "text"], ""));
  return {
    display,
    orig: safeText(pick(word, ["orig", "o"], "")),
    norm: safeText(pick(word, ["norm", "n"], "")),
    mod: safeText(pick(word, ["mod", "m"], "")),
    pos: safeText(pick(word, ["pos", "p"], "")),
    sem: safeText(pick(word, ["sem", "s"], "")),
  };
}

function normalizeLine(line) {
  if (!line || typeof line !== "object") {
    return { id: "", display: "", text: "", words: [] };
  }

  const words = getTopArray(line, ["words", "w"]).map(normalizeWord);
  const text = safeText(pick(line, ["text", "t"], words.map(w => w.display).join(" ")));
  const id = safeText(pick(line, ["display", "xml_id", "id"], ""));
  const display = safeText(pick(line, ["display", "xml_id", "id"], id));
  return { id, display, text, words };
}

function normalizeUnitSide(side) {
  if (!side || typeof side !== "object") {
    return { title: "", meta: "", lines: [], text: "" };
  }

  const lines = getTopArray(side, ["lines", "l"]).map(normalizeLine);
  const text = safeText(pick(side, ["text", "t"], lines.map(line => line.text).join(" ")));
  const title = safeText(pick(side, ["title", "label", "source_file", "file"], ""));
  const metaBits = [];
  const unitId = pick(side, ["unit_id", "uid"], "");
  if (unitId) metaBits.push(`ID: ${unitId}`);
  const fragments = getTopArray(side, ["fragment_ids", "f"]);
  if (fragments.length) metaBits.push(`Fragments: ${fragments.length}`);
  return { title, meta: metaBits.join(" · "), lines, text };
}

function normalizeRecord(record) {
  const source = normalizeUnitSide(pick(record, ["source", "A", "left"], {}));
  const target = normalizeUnitSide(pick(record, ["target", "B", "right"], {}));
  const n = safeText(record?.n, "");
  return { n, source, target, links: Array.isArray(record?.links) ? record.links : [] };
}

function normalizeBookMeta(entry) {
  return {
    book: Number(entry?.book ?? entry?.n ?? 0),
    file: safeText(entry?.file, ""),
    count: Number(entry?.count ?? 0),
  };
}

async function fetchJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Unable to load ${path} (${response.status})`);
  }
  return await response.json();
}

function setStatus(message, isError = false) {
  els.status.textContent = message;
  els.status.style.color = isError ? "#8b2f2f" : "";
}

function setLoading(loading) {
  els.bookSelect.disabled = loading;
  els.prevUnit.disabled = loading;
  els.nextUnit.disabled = loading;
}

function renderMetadata() {
  const index = state.index || {};
  const source = index.source || {};
  const target = index.target || {};

  els.projectTitle.textContent = index.project || "Aeneas";
  els.projectSubtitle.textContent = [
    source.author && source.title ? `${source.author}, ${source.title}` : source.title,
    target.author && target.title ? `${target.author}, ${target.title}` : target.title,
  ].filter(Boolean).join(" · ") || "Static parallel reader";

  els.sourceTitle.textContent = source.title || "Source";
  els.targetTitle.textContent = target.title || "Target";
  els.sourceMeta.textContent = [source.author, source.language].filter(Boolean).join(" · ");
  els.targetMeta.textContent = [target.author, target.language].filter(Boolean).join(" · ");
}

function renderBookSelect() {
  const select = els.bookSelect;
  select.innerHTML = "";

  for (const entry of state.books) {
    const option = document.createElement("option");
    option.value = String(entry.book);
    option.textContent = `Book ${entry.book}${entry.count ? ` (${entry.count})` : ""}`;
    select.appendChild(option);
  }

  select.disabled = state.books.length === 0;
}

function renderLine(line) {
  const row = document.createElement("div");
  row.className = "line";

  const number = document.createElement("div");
  number.className = "line-number";
  number.textContent = line.display || line.id || "";

  const body = document.createElement("div");
  body.className = "line-body";

  if (line.words && line.words.length) {
    const wrap = document.createElement("span");
    wrap.className = "word-wrap";

    line.words.forEach((word, idx) => {
      const span = document.createElement("span");
      span.className = "word";
      span.textContent = word.display || "";
      span.dataset.display = word.display || "";
      span.dataset.orig = word.orig || "";
      span.dataset.norm = word.norm || "";
      span.dataset.mod = word.mod || "";
      span.dataset.pos = word.pos || "";
      span.dataset.sem = word.sem || "";
      wrap.appendChild(span);
      if (idx < line.words.length - 1) wrap.appendChild(document.createTextNode(" "));
    });

    body.appendChild(wrap);
  } else {
    body.textContent = line.text || "";
  }

  row.append(number, body);
  return row;
}

function renderSide(container, side) {
  container.innerHTML = "";

  if (!side || !side.lines || side.lines.length === 0) {
    const empty = document.createElement("div");
    empty.className = "line";
    empty.innerHTML = '<div class="line-number">—</div><div class="line-body">No lines available.</div>';
    container.appendChild(empty);
    return;
  }

  side.lines.forEach(line => container.appendChild(renderLine(line)));
}

function currentRecord() {
  return state.records[state.currentRecordIndex] || null;
}

function updateCounters() {
  const record = currentRecord();
  const total = state.records.length;
  els.unitCounter.textContent = total ? `${state.currentRecordIndex + 1} / ${total}` : "0 / 0";
  els.unitTitle.textContent = record ? `Translation Unit ${record.n || state.currentRecordIndex + 1}` : "Translation Unit";
  els.bookLabel.textContent = state.currentBook ? `Book ${state.currentBook}` : "Book";

  const canMove = total > 1;
  els.prevUnit.disabled = !canMove || state.currentRecordIndex <= 0;
  els.nextUnit.disabled = !canMove || state.currentRecordIndex >= total - 1;
}

function renderCurrentRecord() {
  const record = currentRecord();
  if (!record) {
    els.sourceColumn.innerHTML = "";
    els.targetColumn.innerHTML = "";
    els.unitTitle.textContent = "No translation units";
    updateCounters();
    return;
  }

  renderSide(els.sourceColumn, record.source);
  renderSide(els.targetColumn, record.target);
  updateCounters();
}

async function loadBook(bookNumber) {
  const entry = state.books.find(item => Number(item.book) === Number(bookNumber));
  if (!entry) {
    throw new Error(`Book ${bookNumber} not found in index.json`);
  }

  setLoading(true);
  setStatus(`Loading Book ${bookNumber}…`);

  const file = entry.file || `book_${bookNumber}.json`;
  const payload = await fetchJson(`data/json/${file}`);
  const records = getTopArray(payload, ["records"]).map(normalizeRecord);

  state.currentBook = Number(bookNumber);
  state.currentPayload = payload;
  state.records = records;
  state.currentRecordIndex = 0;

  els.bookSelect.value = String(bookNumber);
  setStatus(`Book ${bookNumber} loaded: ${records.length} translation units.`);
  renderCurrentRecord();
  setLoading(false);
}

async function init() {
  els.projectTitle = $("project-title");
  els.projectSubtitle = $("project-subtitle");
  els.bookSelect = $("book-select");
  els.prevUnit = $("prev-unit");
  els.nextUnit = $("next-unit");
  els.status = $("status");
  els.bookLabel = $("book-label");
  els.unitTitle = $("unit-title");
  els.unitCounter = $("unit-counter");
  els.sourceTitle = $("source-title");
  els.targetTitle = $("target-title");
  els.sourceMeta = $("source-meta");
  els.targetMeta = $("target-meta");
  els.sourceColumn = $("source-column");
  els.targetColumn = $("target-column");

  try {
    setStatus("Loading index.json…");
    state.index = await fetchJson("data/json/index.json");
    state.books = getTopArray(state.index, ["books"]).map(normalizeBookMeta).filter(item => item.book);

    if (!state.books.length) {
      throw new Error("index.json does not contain any books.");
    }

    renderMetadata();
    renderBookSelect();

    els.bookSelect.addEventListener("change", async (event) => {
      try {
        await loadBook(event.target.value);
      } catch (error) {
        console.error(error);
        setStatus(error.message, true);
      }
    });

    els.prevUnit.addEventListener("click", () => {
      if (state.currentRecordIndex > 0) {
        state.currentRecordIndex -= 1;
        renderCurrentRecord();
      }
    });

    els.nextUnit.addEventListener("click", () => {
      if (state.currentRecordIndex < state.records.length - 1) {
        state.currentRecordIndex += 1;
        renderCurrentRecord();
      }
    });

    await loadBook(state.books[0].book);
  } catch (error) {
    console.error(error);
    setStatus(error.message, true);
    els.bookSelect.disabled = true;
    els.prevUnit.disabled = true;
    els.nextUnit.disabled = true;
    els.unitTitle.textContent = "Unable to load Aeneas";
  }
}

window.addEventListener("DOMContentLoaded", init);
