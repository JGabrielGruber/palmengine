/**
 * Palm Portal dogfood — floating chat over WebSocket Assist.
 * Session (sess-…) and instance (continue handle) are two slots.
 * Renders payload.input for dynamic widgets; dispatches path/alias/params frames.
 * Menu: debounced typeahead search, open:kind:id chips, header Menu.
 * Mobile: no autofocus (keyboard covers chips); visualViewport sizes panel.
 */
(() => {
  const $ = (id) => document.getElementById(id);
  const fab = $("fab");
  const panel = $("panel");
  const log = $("log");
  const meta = $("meta");
  const statusEl = $("conn-status");
  const choicesEl = $("choices");
  const fieldHost = $("field-host");
  const textInput = $("text-input");
  const form = $("composer");
  const btnSend = $("btn-send");
  const btnStart = $("btn-start");
  const btnMenu = $("btn-menu");
  const btnMin = $("btn-min");
  const menuSearchRow = $("menu-search-row");
  const menuSearch = $("menu-search");
  const btnMenuSearch = $("btn-menu-search");

  const messages = [];
  let typingEl = null;
  let pendingTimer = null;
  let menuSearchTimer = null;
  let lastMenuQuerySent = null;
  const MENU_SEARCH_DEBOUNCE_MS = 350;

  const state = {
    ws: null,
    reqId: 0,
    sessionId: null,
    instanceId: null,
    flowId: null,
    lastInput: null,
    lastPayload: null,
    menuSection: "root",
    connected: false,
    /** true after we auto-open operator-entry on connect (human-first) */
    bootstrapped: false,
    /** true while waiting for a turn after dispatch */
    pending: false,
  };

  function resolvePortalLang() {
    const raw = (new URLSearchParams(location.search).get("lang") || "").trim();
    const folded = raw.replace(/_/g, "-").toLowerCase();
    const skins = window.PALM_PORTAL_SKINS || {};
    if (raw && skins[raw]) return raw;
    if (folded === "pt" || folded === "pt-br") return "pt-BR";
    if (folded === "en" || folded === "en-us" || folded === "en-gb") return "en";
    for (const id of Object.keys(skins)) {
      if (id.toLowerCase() === folded) return id;
    }
    return "en";
  }

  const PORTAL_LANG = resolvePortalLang();
  const PORTAL_SKIN = (window.PALM_PORTAL_SKINS && window.PALM_PORTAL_SKINS[PORTAL_LANG]) || {
    chrome: {},
    sections: {},
    paint: {},
    prefixes: [],
    synonyms: {},
  };

  function chromeText(key, fallback) {
    const value = PORTAL_SKIN.chrome && PORTAL_SKIN.chrome[key];
    return value != null && String(value) !== "" ? String(value) : fallback;
  }

  function paint(text) {
    if (text == null) return text;
    const source = String(text);
    const map = PORTAL_SKIN.paint || {};
    if (Object.prototype.hasOwnProperty.call(map, source)) return map[source];
    const trimmed = source.trim();
    if (trimmed !== source && Object.prototype.hasOwnProperty.call(map, trimmed)) {
      return source.replace(trimmed, map[trimmed]);
    }
    if (source.includes("\n\n")) {
      const parts = source.split("\n\n");
      let hit = false;
      const painted = parts.map((part) => {
        if (Object.prototype.hasOwnProperty.call(map, part)) {
          hit = true;
          return map[part];
        }
        const t = part.trim();
        if (t !== part && Object.prototype.hasOwnProperty.call(map, t)) {
          hit = true;
          return map[t];
        }
        return part;
      });
      if (hit) return painted.join("\n\n");
    }
    const prefixes = PORTAL_SKIN.prefixes || [];
    for (const row of prefixes) {
      if (!row || row.length < 2) continue;
      const from = String(row[0]);
      if (from && source.startsWith(from)) {
        return String(row[1]) + paint(source.slice(from.length));
      }
    }
    return source;
  }

  function foldKey(value) {
    try {
      return String(value)
        .normalize("NFD")
        .replace(/\p{M}/gu, "")
        .trim()
        .toLowerCase();
    } catch (_) {
      return String(value).trim().toLowerCase();
    }
  }

  function applySynonym(raw) {
    const source = String(raw ?? "");
    const mapped = (PORTAL_SKIN.synonyms || {})[foldKey(source)];
    if (!mapped) return source;
    const payload = state.lastPayload || {};
    const schema = state.lastInput || payload.input || {};
    const choices = schema.choices || payload.choices || [];
    const values = new Set(
      (Array.isArray(choices) ? choices : []).map((item) => {
        const value = item && typeof item === "object" && item.value != null ? item.value : item;
        return String(value).toLowerCase();
      })
    );
    if (values.size && values.has(String(mapped).toLowerCase())) return mapped;
    if (
      ["yes", "no", "skip", "exit", "done", "add", "edit", "remove", "start", "leave", "more"].includes(
        String(mapped).toLowerCase()
      )
    ) {
      return mapped;
    }
    return source;
  }

  function applyChrome() {
    document.documentElement.lang = PORTAL_LANG === "pt-BR" ? "pt-BR" : "en";
    document.title = chromeText("documentTitle", document.title);
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (key) el.textContent = chromeText(key, el.textContent);
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      if (key) el.setAttribute("placeholder", chromeText(key, el.getAttribute("placeholder") || ""));
    });
    document.querySelectorAll("[data-i18n-title]").forEach((el) => {
      const key = el.getAttribute("data-i18n-title");
      if (key) el.setAttribute("title", chromeText(key, el.getAttribute("title") || ""));
    });
    document.querySelectorAll("[data-i18n-aria]").forEach((el) => {
      const key = el.getAttribute("data-i18n-aria");
      if (key) el.setAttribute("aria-label", chromeText(key, el.getAttribute("aria-label") || ""));
    });
  }

  function setPanelOpen(open) {
    panel.hidden = !open;
    document.body.classList.toggle("panel-open", open);
  }

  function paintSection(section) {
    const key = String(section || "root");
    const mapped = PORTAL_SKIN.sections && PORTAL_SKIN.sections[key];
    return mapped || key;
  }

  function renderLanding() {
    const nav = $("skins");
    if (!nav) return;
    const skins = window.PALM_PORTAL_SKINS || {};
    const ids = Object.keys(skins);
    if (!ids.length) return;
    nav.innerHTML = "";
    for (const id of ids) {
      const skin = skins[id] || {};
      const link = document.createElement("a");
      link.className = "skin-card" + (id === PORTAL_LANG ? " active" : "");
      link.href = `/portal/?lang=${encodeURIComponent(id)}&open=1`;
      const title = document.createElement("strong");
      title.textContent = skin.name || id;
      const blurb = document.createElement("span");
      blurb.textContent = skin.blurb || "";
      link.appendChild(title);
      link.appendChild(blurb);
      nav.appendChild(link);
    }
  }

  function isOpenToken(value) {
    return typeof value === "string" && value.startsWith("open:");
  }

  function isSystemSessionId(value) {
    return typeof value === "string" && value.startsWith("sess-");
  }

  function applyBoundSnapshot(bound) {
    if (!bound || typeof bound !== "object") return;
    if ("session_id" in bound) {
      const sid = bound.session_id;
      state.sessionId = isSystemSessionId(sid) ? String(sid) : null;
    }
    if ("instance_id" in bound) {
      const iid = bound.instance_id;
      if (iid == null || String(iid).trim() === "") {
        state.instanceId = null;
      } else if (!isSystemSessionId(iid)) {
        state.instanceId = String(iid);
      }
    }
    if ("flow_id" in bound) {
      state.flowId = bound.flow_id ? String(bound.flow_id) : null;
    }
  }

  function applyTurnIds(payload) {
    if (!payload || typeof payload !== "object") return;
    const refs = payload.refs && typeof payload.refs === "object" ? payload.refs : {};
    const sid = payload.session_id || refs.session_id;
    if (isSystemSessionId(sid)) {
      state.sessionId = String(sid);
    }
    const iid = payload.instance_id || refs.instance_id;
    if (iid && !isSystemSessionId(iid)) {
      state.instanceId = String(iid);
    } else if (sid && !isSystemSessionId(sid) && !payload.instance_id) {
      // Pre-plane leftover: instance-shaped value on session_id.
      state.instanceId = String(sid);
    }
  }

  function clearWalkState(keepFlowId) {
    state.sessionId = null;
    state.instanceId = null;
    if (!keepFlowId) state.flowId = null;
  }

  function bindClearFrame(flowId) {
    return {
      op: "bind",
      id: nextId(),
      clear: true,
      session_id: null,
      instance_id: null,
      flow_id: flowId || null,
    };
  }

  function withContinueParams(params) {
    const out = { ...(params || {}) };
    if (!out.session_id && state.sessionId) out.session_id = state.sessionId;
    if (!out.instance_id && state.instanceId) out.instance_id = state.instanceId;
    if (!out.flow_id && state.flowId) out.flow_id = state.flowId;
    return out;
  }

  function isMenuPayload(payload) {
    if (!payload) return false;
    const schema = payload.input;
    if (schema && (schema.widget === "menu" || schema.kind === "menu")) return true;
    if (payload.kind === "menu") return true;
    return false;
  }

  /** True on touch / coarse pointer phones — avoid stealing focus. */
  function isMobileUi() {
    try {
      return (
        window.matchMedia("(max-width: 480px)").matches ||
        window.matchMedia("(pointer: coarse)").matches
      );
    } catch (_) {
      return false;
    }
  }

  /**
   * Pin the panel to visualViewport so the composer stays above the soft keyboard.
   * Prefer inline geometry over CSS vars — more reliable on Android WebViews.
   * Never use Element.scrollIntoView here (it can scroll the document and hide the input).
   */
  function syncVisualViewport() {
    const vv = window.visualViewport;
    const root = document.documentElement;
    const mobile = isMobileUi();

    if (!vv) {
      root.style.setProperty("--vv-height", `${window.innerHeight}px`);
      root.style.setProperty("--vv-offset-top", "0px");
      root.style.setProperty("--vv-offset-left", "0px");
      root.style.setProperty("--vv-width", `${window.innerWidth}px`);
      root.style.setProperty("--keyboard-inset", "0px");
      clearPanelViewportStyles();
      return;
    }

    const top = Math.round(vv.offsetTop);
    const left = Math.round(vv.offsetLeft);
    const height = Math.round(vv.height);
    const width = Math.round(vv.width);
    const keyboardInset = Math.max(0, window.innerHeight - vv.height - vv.offsetTop);

    root.style.setProperty("--vv-height", `${height}px`);
    root.style.setProperty("--vv-offset-top", `${top}px`);
    root.style.setProperty("--vv-offset-left", `${left}px`);
    root.style.setProperty("--vv-width", `${width}px`);
    root.style.setProperty("--keyboard-inset", `${Math.round(keyboardInset)}px`);

    if (mobile && !panel.hidden) {
      // Direct styles beat CSS cascade / vh quirks when keyboard is open
      panel.style.position = "fixed";
      panel.style.top = `${top}px`;
      panel.style.left = `${left}px`;
      panel.style.right = "auto";
      panel.style.bottom = "auto";
      panel.style.width = `${width}px`;
      panel.style.height = `${height}px`;
      panel.style.maxHeight = `${height}px`;
      panel.style.borderRadius = "0";
      // Lock document so scrollIntoView / focus cannot pan the page under the keyboard
      root.classList.add("portal-keyboard-lock");
      document.body.classList.add("portal-keyboard-lock");
    } else {
      clearPanelViewportStyles();
      root.classList.remove("portal-keyboard-lock");
      document.body.classList.remove("portal-keyboard-lock");
    }

    // Only scroll the log pane — keep composer (flex footer) painted at bottom
    if (!panel.hidden) scrollLogToEnd();
  }

  function clearPanelViewportStyles() {
    [
      "position",
      "top",
      "left",
      "right",
      "bottom",
      "width",
      "height",
      "maxHeight",
      "borderRadius",
    ].forEach((prop) => {
      panel.style[prop] = "";
    });
  }

  /** Ensure composer stays in the painted panel (not under keyboard). */
  function ensureComposerVisible() {
    syncVisualViewport();
    // Composer is flex-shrink:0 at panel bottom — just pin log scroll
    scrollLogToEnd();
    // If the focused control is somehow off-panel, nudge only within log/composer
    try {
      const active = document.activeElement;
      if (active && form.contains(active) && typeof active.getBoundingClientRect === "function") {
        const pr = panel.getBoundingClientRect();
        const ar = active.getBoundingClientRect();
        if (ar.bottom > pr.bottom - 4 || ar.top < pr.top) {
          // Re-sync; do not scrollIntoView (scrolls the page on Android)
          syncVisualViewport();
        }
      }
    } catch (_) {
      /* ignore */
    }
  }

  // Meta: keep text + activity indicator
  meta.innerHTML =
    '<span class="activity" aria-live="polite"><span class="typing-dots" aria-hidden="true"><span></span><span></span><span></span></span><span class="activity-label">Palm is thinking…</span></span><span class="meta-text"></span>';
  const metaText = meta.querySelector(".meta-text");
  const activityLabel = meta.querySelector(".activity-label");

  function wsUrl() {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    const qs = new URLSearchParams(location.search);
    const override = qs.get("ws");
    if (override) return override;
    return `${proto}//${location.host}/ws/v1/assist`;
  }

  function setStatus(text, ok) {
    statusEl.textContent = paint(text);
    statusEl.style.color = ok ? "#5eead4" : "var(--muted)";
  }

  function setMeta(text) {
    if (text) {
      metaText.textContent = paint(text);
      return;
    }
    const parts = [];
    if (state.sessionId) {
      parts.push(`${chromeText("sessionWord", "session")} ${state.sessionId.slice(0, 12)}…`);
    }
    if (state.instanceId) {
      parts.push(`${chromeText("instanceWord", "instance")} ${state.instanceId.slice(0, 12)}…`);
    }
    if (state.flowId) {
      parts.push(`${chromeText("flowWord", "flow")} ${state.flowId}`);
    }
    metaText.textContent = parts.join(" · ");
  }

  function scrollLogToEnd() {
    // Only the log scroller — never Element.scrollIntoView (pans document on mobile
    // and hides the composer under the soft keyboard).
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        log.scrollTop = log.scrollHeight;
      });
    });
  }

  function appendBubble(kind, text, extraClass) {
    const el = document.createElement("div");
    el.className = `bubble ${kind}${extraClass ? ` ${extraClass}` : ""}`;
    el.textContent = kind === "user" ? String(text ?? "") : paint(text);
    log.appendChild(el);
    scrollLogToEnd();
    return el;
  }

  function showTyping(label) {
    hideTyping();
    typingEl = document.createElement("div");
    typingEl.className = "bubble typing";
    const shown = paint(label || chromeText("waitingResponse", "Waiting for response"));
    typingEl.setAttribute("aria-label", shown);
    typingEl.innerHTML =
      '<span class="typing-dots" aria-hidden="true"><span></span><span></span><span></span></span>' +
      `<span></span>`;
    typingEl.querySelector("span:last-child").textContent = shown;
    log.appendChild(typingEl);
    scrollLogToEnd();
  }

  function hideTyping() {
    if (typingEl && typingEl.parentNode) {
      typingEl.parentNode.removeChild(typingEl);
    }
    typingEl = null;
  }

  function setPending(pending, label) {
    state.pending = !!pending;
    if (pendingTimer) {
      clearTimeout(pendingTimer);
      pendingTimer = null;
    }
    if (pending) {
      meta.classList.add("busy");
      form.classList.add("busy");
      btnSend.classList.add("busy");
      btnSend.disabled = true;
      btnSend.textContent = "…";
      textInput.disabled = true;
      choicesEl.querySelectorAll("button").forEach((b) => {
        b.disabled = true;
      });
      const thinking = paint(label || chromeText("thinking", "Palm is thinking…"));
      if (activityLabel) activityLabel.textContent = thinking;
      // Slight delay so fast turns don't flash the indicator
      pendingTimer = setTimeout(() => {
        if (state.pending) showTyping(label || chromeText("thinking", "Palm is thinking…"));
      }, 120);
    } else {
      meta.classList.remove("busy");
      form.classList.remove("busy");
      btnSend.classList.remove("busy");
      btnSend.textContent = chromeText("send", "Send");
      hideTyping();
      // re-enable handled by renderInput
    }
  }

  function connect() {
    if (state.ws && (state.ws.readyState === WebSocket.OPEN || state.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }
    setStatus(chromeText("statusConnecting", "connecting…"), false);
    const ws = new WebSocket(wsUrl());
    state.ws = ws;

    ws.onopen = () => {
      state.connected = true;
      setStatus(chromeText("statusConnected", "connected"), true);
      appendBubble("sys", "Connected to Palm Assist");
      if (state.sessionId) {
        send({
          op: "bind",
          id: nextId(),
          session_id: state.sessionId,
          instance_id: state.instanceId,
          flow_id: state.flowId,
        });
      }
    };

    ws.onclose = () => {
      state.connected = false;
      setPending(false);
      setStatus(chromeText("statusDisconnected", "disconnected"), false);
      appendBubble("sys", "Disconnected");
    };

    ws.onerror = () => {
      setStatus(chromeText("statusError", "error"), false);
    };

    ws.onmessage = (ev) => {
      let msg;
      try {
        msg = JSON.parse(ev.data);
        messages.push(msg);
        console.log(messages);
      } catch {
        setPending(false);
        appendBubble("error", "Invalid frame from server");
        return;
      }
      onFrame(msg);
    };
  }

  function nextId() {
    state.reqId += 1;
    return `p${state.reqId}`;
  }

  function send(obj) {
    if (!state.ws || state.ws.readyState !== WebSocket.OPEN) {
      appendBubble("error", "Not connected");
      return;
    }
    state.ws.send(JSON.stringify(obj));
    messages.push(obj);
    console.log(messages);
    if (obj.op === "dispatch") {
      setPending(true, chromeText("thinking", "Palm is thinking…"));
    }
  }

  function dispatch(partial) {
    const frame = {
      op: "dispatch",
      id: nextId(),
      format: "assistant",
      ...partial,
    };
    if (!frame.params) frame.params = {};
    send(frame);
  }

  function onFrame(msg) {
    const op = msg.op;
    if (op === "hello") {
      appendBubble("sys", `Palm ${msg.version || "?"} · protocol ${msg.protocol}`);
      if (msg.bound) {
        applyBoundSnapshot(msg.bound);
        setMeta();
      }
      if (!state.bootstrapped) {
        state.bootstrapped = true;
        appendBubble("sys", "Starting…");
        send({
          op: "dispatch",
          id: nextId(),
          format: "assistant",
          alias: "operator-entry/start",
          params: {},
        });
      }
      return;
    }
    if (op === "pong") return;
    if (op === "bound") {
      applyBoundSnapshot(msg);
      setMeta();
      appendBubble("sys", msg.session_id ? "Session bound" : "Walk cleared");
      return;
    }
    if (op === "error") {
      setPending(false);
      const err = msg.error || {};
      appendBubble("error", `${err.code || "error"}: ${err.message || "unknown"}`);
      // restore input if we still have a schema
      if (state.lastInput) {
        renderInput({ input: state.lastInput, status: "waiting", mutation: { mutations_allowed: true } });
      } else {
        textInput.disabled = false;
        btnSend.disabled = false;
      }
      return;
    }
    if (op === "turn") {
      setPending(false);
      if (msg.bound) applyBoundSnapshot(msg.bound);
      renderTurn(msg.payload || {});
      setMeta();
    }
  }

  function renderTurn(payload) {
    applyTurnIds(payload);
    const refs = payload.refs || {};
    const path = payload.path;
    if (Array.isArray(path) && path[0] === "flows" && path[1]) {
      state.flowId = path[1];
    } else if (refs.flow_id) {
      state.flowId = refs.flow_id;
    } else if (payload.flow_id) {
      state.flowId = payload.flow_id;
    }

    // 0.32.10 — separate intro bubble, then real step question (no merged dump)
    const banner = (payload.intro_banner || "").trim();
    let question = (payload.question || "").trim();
    if (banner) {
      appendBubble("bot", banner, "banner");
      // Drop accidental prefix if server still merged banner into question
      if (question.startsWith(banner)) {
        question = question.slice(banner.length).replace(/^\s*\n+/, "").trim();
      }
    }
    if (question) appendBubble("bot", question);
    else if (!banner && payload.hint) appendBubble("bot", String(payload.hint));

    if (payload.validation_error) {
      appendBubble("error", String(payload.validation_error));
    }

    state.lastInput = payload.input || null;
    state.lastPayload = payload;
    if (isMenuPayload(payload)) {
      const sec =
        (payload.input && payload.input.section) ||
        payload.section ||
        "root";
      state.menuSection = sec;
    }
    renderInput(payload);
    renderActions(payload.actions || []);
    scrollLogToEnd();
    // Resource / transform steps auto-run — do not leave the operator typing free text.
    maybeAutoAdvanceResource(payload);
  }

  /**
   * When Assist lands on a non-interactive resource step (auto_advance), tick
   * flows/session-resume so NeonRoot (and other resources) actually run.
   */
  function maybeAutoAdvanceResource(payload) {
    if (!payload || state.pending) return;
    const schema = payload.input || {};
    const stepKind = schema.step_kind || (payload.compose && payload.compose.step_kind);
    const interactive = schema.interactive;
    const auto =
      schema.auto_advance === true ||
      interactive === false ||
      stepKind === "resource" ||
      schema.kind === "resource" ||
      schema.widget === "resource" ||
      schema.field_type === "resource";
    // Only auto-tick when still waiting — mid-drive "running" is not resumeable.
    const waiting =
      payload.status === "waiting" || payload.status === "WAITING_FOR_INPUT";
    if (!auto || !waiting) return;
    // Prefer explicit resume CTA if present
    const actions = payload.actions || [];
    const resume = actions.find(
      (a) =>
        a &&
        (a.alias === "flows/session-resume" ||
          String(a.label || "").toLowerCase().includes("resume resource"))
    );
    if (resume) {
      appendBubble("sys", "Running resource step…");
      runAction(resume);
      return;
    }
    if (!state.instanceId && !state.sessionId) return;
    appendBubble("sys", "Running resource step…");
    send({
      op: "dispatch",
      id: nextId(),
      format: "assistant",
      alias: "flows/session-resume",
      params: withContinueParams({
        session_id: state.sessionId,
        instance_id: state.instanceId,
        flow_id: state.flowId || undefined,
      }),
    });
  }

  function renderChoiceChips(choices, { menu } = {}) {
    for (const c of choices) {
      const value = c.value != null ? c.value : c;
      const label = paint(c.label != null ? c.label : String(value));
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "chip";
      if (menu || isOpenToken(String(value))) chip.classList.add("menu-item");
      chip.textContent = c.n != null ? `${c.n}. ${label}` : label;
      chip.onclick = () => submitValue(String(value));
      choicesEl.appendChild(chip);
    }
  }

  function setMenuSearchVisible(visible, section) {
    if (!menuSearchRow) return;
    menuSearchRow.hidden = !visible;
    if (visible && menuSearch) {
      menuSearch.placeholder =
        section && section !== "root"
          ? chromeText("searchSection", "Search {section}…").replace(
              "{section}",
              paintSection(section)
            )
          : paint("Search menu…");
    }
  }

  function renderInput(payload) {
    choicesEl.innerHTML = "";
    fieldHost.innerHTML = "";
    textInput.value = "";
    textInput.disabled = false;
    btnSend.disabled = false;
    btnSend.textContent = chromeText("send", "Send");

    const schema = payload.input;
    const status = payload.status;
    const menuMode = isMenuPayload(payload);

    if (status === "complete" || status === "failed") {
      textInput.placeholder = paint("Session finished");
      textInput.disabled = true;
    }

    const choices = (schema && schema.choices) || payload.choices || [];
    let widget =
      (schema && schema.widget) || (choices.length ? "choice" : "text");
    if (menuMode) widget = "menu";

    // Non-interactive resource / transform: lock composer (auto-advance handles resume)
    const autoResource =
      schema &&
      (schema.interactive === false ||
        schema.auto_advance === true ||
        schema.kind === "resource" ||
        schema.widget === "resource" ||
        schema.field_type === "resource" ||
        schema.step_kind === "resource");
    if (autoResource && status !== "complete" && status !== "failed") {
      textInput.placeholder = paint("Resource running…");
      textInput.disabled = true;
      btnSend.disabled = true;
      return;
    }

    setMenuSearchVisible(widget === "menu", state.menuSection);

    if (widget === "menu" && choices.length) {
      textInput.placeholder = paint("Pick a row, or search above…");
      renderChoiceChips(choices, { menu: true });
      if (schema && schema.has_more) {
        // Show more is usually an action; keep placeholder note
        textInput.placeholder = paint("More rows available — use Show more");
      }
    } else if (widget === "choice" && choices.length) {
      textInput.placeholder = paint("Or type a choice value…");
      renderChoiceChips(choices, { menu: false });
    } else if (widget === "confirm") {
      textInput.placeholder = paint("yes / no");
      for (const [label, value] of [
        ["Yes", "yes"],
        ["No", "no"],
      ]) {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "chip";
        chip.textContent = paint(label);
        chip.onclick = () => submitValue(value);
        choicesEl.appendChild(chip);
      }
    } else if (widget === "collection") {
      const optional = schema?.required === false || schema?.skip_allowed;
      textInput.placeholder = optional
        ? paint("Optional — type a value or Skip")
        : schema?.collection_phase === "field"
          ? paint("Enter value…")
          : schema?.collection_phase
            ? `Collection (${schema.collection_phase})…`
            : paint("add / done / item text…");
      if (optional) addSkipChip(schema);
      if (schema?.error) {
        const err = document.createElement("div");
        err.className = "field-error";
        err.textContent = String(schema.error);
        fieldHost.appendChild(err);
      }
    } else {
      textInput.placeholder =
        schema?.required === false
          ? paint("Optional — type or Skip")
          : chromeText("typeAnswer", "Type an answer…");
      if (schema?.required === false || schema?.skip_allowed) {
        addSkipChip(schema);
      }
    }

    if (schema?.error && widget !== "collection") {
      const err = document.createElement("div");
      err.className = "field-error";
      err.textContent = String(schema.error);
      fieldHost.appendChild(err);
    }

    const waiting =
      status === "waiting" ||
      status === "running" ||
      (choices && choices.length > 0);
    const locked =
      payload.mutation &&
      payload.mutation.mutations_allowed === false &&
      !waiting;
    if (locked || status === "complete" || status === "failed") {
      textInput.disabled = true;
      btnSend.disabled = true;
    }
    // No autofocus: on mobile it pops the keyboard over chips/log.
    // Desktop: focus only when user already typed in the field this session.
  }

  const NOISE_ACTIONS = new Set([
    "send answer",
    "inspect session",
    "resume session",
    "inspect this session",
  ]);

  function renderActions(actions) {
    for (const action of actions) {
      if (!action || typeof action !== "object") continue;
      const label = action.label || "Action";
      if (NOISE_ACTIONS.has(String(label).toLowerCase())) continue;
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "chip secondary";
      chip.textContent = paint(label);
      chip.onclick = () => runAction(action);
      choicesEl.appendChild(chip);
    }
  }

  function runAction(action) {
    if (state.pending) return;
    const frame = { op: "dispatch", id: nextId(), format: "assistant" };
    if (action.alias) frame.alias = action.alias;
    if (action.path) frame.path = action.path;
    frame.params = { ...(action.params || {}) };
    const alias = action.alias || "";
    const navAlias =
      alias === "assist/menu" ||
      alias === "assist/open" ||
      alias === "assist/doctor" ||
      alias === "assist/discover" ||
      alias === "assist/catalog/flows" ||
      alias === "assist/catalog/waiting";
    const freshStart =
      alias === "operator-entry/start" ||
      alias === "design-entry/start" ||
      navAlias ||
      (!!frame.params.flow_id &&
        !frame.params.value &&
        !frame.params.session_id &&
        !action.path);
    if (freshStart) {
      // Menu/open/start must not stick previous walk onto params
      const keepFlow =
        !navAlias || alias === "operator-entry/start" || alias === "design-entry/start";
      clearWalkState(keepFlow);
      if (keepFlow) state.flowId = frame.params.flow_id || null;
      setMeta();
      send(bindClearFrame(frame.params.flow_id || null));
      delete frame.params.session_id;
      delete frame.params.instance_id;
      if (navAlias) delete frame.params.flow_id;
    } else {
      frame.params = withContinueParams(frame.params);
    }
    appendBubbleUser(`[${paint(action.label || "action")}]`);
    send(frame);
  }

  function isOptionalInput(schema) {
    if (!schema) return false;
    if (schema.required === false || schema.skip_allowed) return true;
    const active = schema.collection_field;
    const fields = schema.item_fields;
    if (active && Array.isArray(fields)) {
      const f = fields.find((x) => x && x.slug === active);
      if (f && f.required === false) return true;
    }
    return false;
  }

  function addSkipChip(schema) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip secondary";
    chip.textContent = paint((schema && schema.skip_label) || "Skip");
    chip.onclick = () => submitValue(schema?.skip_value != null ? schema.skip_value : "");
    choicesEl.appendChild(chip);
  }

  function submitValue(value) {
    if (state.pending) return;
    let v = applySynonym(String(value ?? "").trim());
    const optional = isOptionalInput(state.lastInput);
    if (optional && /^(skip|none|n\/a|na|-|pass|empty|pular)$/i.test(v)) {
      v = "";
    }
    if (!v && !optional) {
      return;
    }
    appendBubbleUser(v || paint("Skip"));
    // Menu open tokens → assist/open (no sticky session)
    if (isOpenToken(v)) {
      clearWalkState();
      setMeta();
      send(bindClearFrame(null));
      dispatch({
        alias: "assist/open",
        params: { value: v, format: "assistant", include_input_schema: true },
      });
      textInput.value = "";
      return;
    }
    dispatch({ params: withContinueParams({ value: v }) });
    textInput.value = "";
  }

  function openPalmMenu(section) {
    if (state.pending) return;
    appendBubble(
      "sys",
      section ? `Menu · ${paintSection(section)}…` : "Opening Palm menu…"
    );
    clearWalkState();
    state.menuSection = section || "root";
    setMeta();
    send(bindClearFrame(null));
    const params = { format: "assistant", include_input_schema: true };
    if (section) params.section = section;
    send({
      op: "dispatch",
      id: nextId(),
      format: "assistant",
      alias: "assist/menu",
      params,
    });
  }

  function runMenuSearch(opts) {
    const options = opts || {};
    if (!menuSearch) return;
    if (state.pending && options.fromDebounce) return;
    if (state.pending && !options.force) return;
    const q = String(menuSearch.value || "").trim();
    // Avoid duplicate dispatches (debounce re-fires same query)
    const section = state.menuSection || "root";
    const key = `${section}::${q}`;
    if (options.fromDebounce && key === lastMenuQuerySent && !options.force) {
      return;
    }
    lastMenuQuerySent = key;
    if (!options.silent) {
      appendBubbleUser(q ? `Search: ${q}` : "Search (clear)");
    } else if (q) {
      setMeta(`Searching ${paintSection(section)}…`);
    }
    clearWalkState();
    send(bindClearFrame(null));
    const params = {
      format: "assistant",
      include_input_schema: true,
      section,
    };
    if (q) params.query = q;
    send({
      op: "dispatch",
      id: nextId(),
      format: "assistant",
      alias: "assist/menu",
      params,
    });
  }

  function scheduleMenuSearch() {
    if (menuSearchTimer) clearTimeout(menuSearchTimer);
    menuSearchTimer = setTimeout(() => {
      menuSearchTimer = null;
      runMenuSearch({ silent: true, fromDebounce: true });
    }, MENU_SEARCH_DEBOUNCE_MS);
  }

  function appendBubbleUser(text) {
    appendBubble("user", text);
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    if (state.pending) return;
    submitValue(textInput.value);
  });

  btnStart.onclick = () => {
    if (state.pending) return;
    appendBubble("sys", "Starting operator entry…");
    clearWalkState();
    state.bootstrapped = true;
    setMeta();
    send(bindClearFrame(null));
    send({
      op: "dispatch",
      id: nextId(),
      format: "assistant",
      alias: "operator-entry/start",
      params: {},
    });
  };

  if (btnMenu) {
    btnMenu.onclick = () => openPalmMenu("root");
  }
  if (btnMenuSearch) {
    btnMenuSearch.onclick = () => {
      if (menuSearchTimer) clearTimeout(menuSearchTimer);
      menuSearchTimer = null;
      runMenuSearch({ force: true });
    };
  }
  if (menuSearch) {
    menuSearch.addEventListener("input", () => scheduleMenuSearch());
    menuSearch.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        if (menuSearchTimer) clearTimeout(menuSearchTimer);
        menuSearchTimer = null;
        runMenuSearch({ force: true });
      }
    });
  }

  btnMin.onclick = () => {
    setPanelOpen(false);
    syncVisualViewport(); // drop keyboard-lock + inline panel geometry
  };

  fab.onclick = () => {
    setPanelOpen(panel.hidden);
    if (!panel.hidden) {
      connect();
      syncVisualViewport();
      // Desktop only: focus composer when opening (mobile keeps chips usable)
      if (!isMobileUi()) {
        try {
          textInput.focus({ preventScroll: true });
        } catch (_) {
          /* ignore */
        }
      }
      scrollLogToEnd();
    } else {
      syncVisualViewport();
    }
  };

  // Soft keyboard / browser chrome — resize panel to visible area
  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", syncVisualViewport);
    window.visualViewport.addEventListener("scroll", syncVisualViewport);
  }
  window.addEventListener("resize", syncVisualViewport);
  syncVisualViewport();

  // User focused the field: after keyboard animates, re-pin panel so input is visible
  const onComposerFocus = () => {
    // Several ticks — Android keyboard height settles late
    ensureComposerVisible();
    setTimeout(ensureComposerVisible, 100);
    setTimeout(ensureComposerVisible, 350);
    setTimeout(ensureComposerVisible, 600);
  };
  textInput.addEventListener("focus", onComposerFocus);
  form.addEventListener("focusin", onComposerFocus);

  textInput.addEventListener("blur", () => {
    setTimeout(() => {
      if (!form.contains(document.activeElement)) {
        syncVisualViewport();
      }
    }, 100);
  });

  applyChrome();
  renderLanding();
  if (activityLabel) {
    activityLabel.textContent = chromeText("thinking", "Palm is thinking…");
  }

  if (new URLSearchParams(location.search).get("open") === "1") {
    setPanelOpen(true);
    connect();
    syncVisualViewport();
  }
})();
