/**
 * Palm Analytics (0.39) — dashboards + single-dataset dogfood.
 * Consumes REST only; no joins.
 */
(() => {
  const $ = (id) => document.getElementById(id);
  const dashboardEl = $("dashboard");
  const datasetEl = $("dataset");
  const metaEl = $("meta");
  const errEl = $("error");
  const tilesEl = $("tiles");
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

  function renderTableInto(tableEl, payload) {
    const th = tableEl.querySelector("thead");
    const tb = tableEl.querySelector("tbody");
    th.innerHTML = "";
    tb.innerHTML = "";
    const cols = (payload && payload.columns) || [];
    const rows = (payload && payload.rows) || [];
    const trh = document.createElement("tr");
    for (const c of cols) {
      const cell = document.createElement("th");
      cell.textContent = c;
      trh.appendChild(cell);
    }
    th.appendChild(trh);
    for (const row of rows) {
      const tr = document.createElement("tr");
      for (let i = 0; i < cols.length; i++) {
        const td = document.createElement("td");
        td.textContent = row[i] == null ? "" : String(row[i]);
        tr.appendChild(td);
      }
      tb.appendChild(tr);
    }
  }

  function renderChartOn(canvasEl, data) {
    const ctx = canvasEl.getContext("2d");
    const w = canvasEl.width;
    const h = canvasEl.height;
    ctx.clearRect(0, 0, w, h);
    const series = (data && data.series && data.series[0]) || null;
    if (!series || !series.points || !series.points.length) {
      ctx.fillStyle = "#8b9bb4";
      ctx.fillText("No series", 16, 24);
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
      renderChartOn(canvas, { series: [] });
      return;
    }
    renderChartOn(canvas, {
      series: [{ name: cols[1], points: rows.map((r) => [r[0], r[1]]) }],
    });
  }

  async function refreshLists() {
    showError("");
    const [ds, dash] = await Promise.all([
      api("GET", "/v1/api/analytics/datasets"),
      api("GET", "/v1/api/analytics/dashboards"),
    ]);
    datasetEl.innerHTML = "";
    for (const r of ds.datasets || []) {
      const opt = document.createElement("option");
      opt.value = r.dataset;
      opt.textContent = `${r.dataset} · ${r.kind || "?"}`;
      datasetEl.appendChild(opt);
    }
    dashboardEl.innerHTML = "";
    const rows = dash.dashboards || [];
    if (!rows.length) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "(no dashboards registered)";
      dashboardEl.appendChild(opt);
    }
    for (const r of rows) {
      const opt = document.createElement("option");
      opt.value = r.name;
      opt.textContent = `${r.title || r.name} (${r.tile_count || 0} tiles)`;
      dashboardEl.appendChild(opt);
    }
    const q = new URLSearchParams(location.search).get("dashboard");
    if (q && [...dashboardEl.options].some((o) => o.value === q)) {
      dashboardEl.value = q;
    }
    metaEl.textContent = `${(ds.datasets || []).length} dataset(s) · ${rows.length} dashboard(s)`;
  }

  async function loadDashboard() {
    showError("");
    tilesEl.innerHTML = "";
    const name = dashboardEl.value;
    if (!name) {
      showError("No dashboard selected");
      return;
    }
    const data = await api(
      "GET",
      `/v1/api/analytics/dashboards/${encodeURIComponent(name)}/render`
    );
    if (data.status !== "ok") throw new Error(data.error || "render failed");
    metaEl.textContent = `${data.dashboard.title || name} · ${data.tiles.length} tiles`;
    for (const block of data.tiles) {
      const tile = block.tile || {};
      const result = block.result || {};
      const card = document.createElement("section");
      card.className = "card tile";
      const h = document.createElement("h3");
      h.textContent = tile.title || tile.dataset || tile.id;
      card.appendChild(h);
      if (result.status !== "ok") {
        const e = document.createElement("p");
        e.className = "err";
        e.textContent = result.error || "query failed";
        card.appendChild(e);
        tilesEl.appendChild(card);
        continue;
      }
      const profile = tile.profile || result.profile;
      if (profile === "kpi") {
        const p = document.createElement("p");
        const d = result.data || {};
        p.textContent = `${d.label || "KPI"}: ${d.value}`;
        card.appendChild(p);
      } else if (profile === "series") {
        const c = document.createElement("canvas");
        c.width = 640;
        c.height = 200;
        card.appendChild(c);
        renderChartOn(c, result.data || {});
      } else {
        const wrap = document.createElement("div");
        wrap.className = "table-wrap";
        const table = document.createElement("table");
        table.innerHTML = "<thead></thead><tbody></tbody>";
        wrap.appendChild(table);
        card.appendChild(wrap);
        renderTableInto(table, result.data || {});
      }
      tilesEl.appendChild(card);
    }
  }

  async function loadDataset() {
    showError("");
    const ds = datasetEl.value;
    if (!ds) {
      showError("No dataset");
      return;
    }
    const table = await api("POST", "/v1/api/analytics/query", {
      dataset: ds,
      profile: "table",
      limit: 100,
    });
    if (table.status !== "ok") throw new Error(table.error || "failed");
    renderTableInto($("table"), table.data || {});
    try {
      const series = await api("POST", "/v1/api/analytics/query", {
        dataset: ds,
        profile: "series",
        limit: 100,
      });
      if (series.status === "ok") renderChartOn(canvas, series.data || {});
      else renderChartFromTable(table.data || {});
    } catch {
      renderChartFromTable(table.data || {});
    }
  }

  $("btn-refresh").addEventListener("click", () => {
    refreshLists().catch((e) => showError(String(e.message || e)));
  });
  $("btn-load").addEventListener("click", () => {
    loadDashboard().catch((e) => showError(String(e.message || e)));
  });
  $("btn-load-ds").addEventListener("click", () => {
    loadDataset().catch((e) => showError(String(e.message || e)));
  });

  refreshLists()
    .then(() => {
      if (dashboardEl.value) return loadDashboard();
    })
    .catch((e) => showError(String(e.message || e)));
})();
