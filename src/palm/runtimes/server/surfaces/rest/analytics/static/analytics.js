/**
 * Palm Analytics dogfood (0.35.6) — paint table + chart from REST only.
 * No joins; no Assist. Prefer series profile for chart when available.
 */
(() => {
  const $ = (id) => document.getElementById(id);
  const datasetEl = $("dataset");
  const metaEl = $("meta");
  const errEl = $("error");
  const thead = $("table").querySelector("thead");
  const tbody = $("table").querySelector("tbody");
  const canvas = $("chart");
  const subject = "dev";

  function headers(json) {
    const h = { Accept: "application/json", "X-Palm-Subject": subject };
    if (json) h["Content-Type"] = "application/json";
    return h;
  }

  function showError(msg) {
    errEl.hidden = !msg;
    errEl.textContent = msg || "";
  }

  async function api(method, path, body) {
    const res = await fetch(path, {
      method,
      headers: headers(!!body),
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const code = data.error || data.code || res.status;
      const msg = data.message || data.detail || JSON.stringify(data);
      throw new Error(`${code}: ${msg}`);
    }
    return data;
  }

  async function refreshList() {
    showError("");
    const data = await api("GET", "/v1/api/analytics/datasets");
    const rows = data.datasets || [];
    datasetEl.innerHTML = "";
    if (!rows.length) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "(no published datasets — materialize dogfood first)";
      datasetEl.appendChild(opt);
      metaEl.textContent = "0 datasets";
      return;
    }
    for (const r of rows) {
      const opt = document.createElement("option");
      opt.value = r.dataset;
      opt.textContent = `${r.dataset} · ${r.kind || "?"} · ${r.default_profile || "table"}`;
      datasetEl.appendChild(opt);
    }
    metaEl.textContent = `${rows.length} published dataset(s)`;
  }

  function renderTable(payload) {
    thead.innerHTML = "";
    tbody.innerHTML = "";
    const cols = payload.columns || [];
    const rows = payload.rows || [];
    const trh = document.createElement("tr");
    for (const c of cols) {
      const th = document.createElement("th");
      th.textContent = c;
      trh.appendChild(th);
    }
    thead.appendChild(trh);
    for (const row of rows) {
      const tr = document.createElement("tr");
      for (let i = 0; i < cols.length; i++) {
        const td = document.createElement("td");
        td.textContent = row[i] == null ? "" : String(row[i]);
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
  }

  function renderChartFromSeries(data) {
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    const series = (data.series && data.series[0]) || null;
    if (!series || !series.points || !series.points.length) {
      ctx.fillStyle = "#8b9bb4";
      ctx.fillText("No series points", 16, 24);
      return;
    }
    const pts = series.points;
    const ys = pts.map((p) => Number(p[1])).filter((n) => !Number.isNaN(n));
    const minY = Math.min(...ys, 0);
    const maxY = Math.max(...ys, 1);
    const pad = 36;
    const plotW = w - pad * 2;
    const plotH = h - pad * 2;
    ctx.strokeStyle = "#2a3548";
    ctx.beginPath();
    ctx.moveTo(pad, pad);
    ctx.lineTo(pad, h - pad);
    ctx.lineTo(w - pad, h - pad);
    ctx.stroke();
    ctx.strokeStyle = "#2dd4bf";
    ctx.lineWidth = 2;
    ctx.beginPath();
    pts.forEach((p, i) => {
      const x = pad + (i / Math.max(pts.length - 1, 1)) * plotW;
      const yv = Number(p[1]);
      const y = h - pad - ((yv - minY) / (maxY - minY || 1)) * plotH;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.fillStyle = "#8b9bb4";
    ctx.font = "12px system-ui";
    ctx.fillText(series.name || "series", pad, 18);
  }

  function renderChartFromTable(payload) {
    const cols = payload.columns || [];
    const rows = payload.rows || [];
    if (cols.length < 2 || !rows.length) {
      renderChartFromSeries({ series: [] });
      return;
    }
    const points = rows.map((r) => [r[0], r[1]]);
    renderChartFromSeries({ series: [{ name: cols[1], points }] });
  }

  async function loadSelected() {
    showError("");
    const ds = datasetEl.value;
    if (!ds) {
      showError("No dataset selected");
      return;
    }
    const table = await api("POST", "/v1/api/analytics/query", {
      dataset: ds,
      profile: "table",
      limit: 100,
    });
    if (table.status !== "ok") throw new Error(table.error || "table query failed");
    renderTable(table.data || {});
    metaEl.textContent = `${ds} · table rows=${table.meta?.row_count ?? "?"} · kind=${table.lineage?.kind || "?"}`;

    try {
      const series = await api("POST", "/v1/api/analytics/query", {
        dataset: ds,
        profile: "series",
        limit: 100,
      });
      if (series.status === "ok") renderChartFromSeries(series.data || {});
      else renderChartFromTable(table.data || {});
    } catch {
      renderChartFromTable(table.data || {});
    }
  }

  $("btn-refresh").addEventListener("click", () => {
    refreshList().catch((e) => showError(String(e.message || e)));
  });
  $("btn-load").addEventListener("click", () => {
    loadSelected().catch((e) => showError(String(e.message || e)));
  });

  refreshList().catch((e) => showError(String(e.message || e)));
})();
