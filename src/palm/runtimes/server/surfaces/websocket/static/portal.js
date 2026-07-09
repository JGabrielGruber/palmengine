/**
 * Palm Portal dogfood (0.32.4) — floating chat over WebSocket Assist.
 * Renders payload.input for dynamic widgets; dispatches path/alias/params frames.
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
  const btnMin = $("btn-min");

  const messages = [];

  const state = {
    ws: null,
    reqId: 0,
    sessionId: null,
    flowId: null,
    lastInput: null,
    connected: false,
    /** true after we auto-open operator-entry on connect (human-first) */
    bootstrapped: false,
  };

  function wsUrl() {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    const qs = new URLSearchParams(location.search);
    const override = qs.get("ws");
    if (override) return override;
    return `${proto}//${location.host}/ws/v1/assist`;
  }

  function setStatus(text, ok) {
    statusEl.textContent = text;
    statusEl.style.color = ok ? "#5eead4" : "var(--muted)";
  }

  function setMeta() {
    const parts = [];
    if (state.sessionId) parts.push(`session ${state.sessionId.slice(0, 12)}…`);
    if (state.flowId) parts.push(`flow ${state.flowId}`);
    meta.textContent = parts.join(" · ");
  }

  function appendBubble(kind, text) {
    const el = document.createElement("div");
    el.className = `bubble ${kind}`;
    el.textContent = text;
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
  }

  function connect() {
    if (state.ws && (state.ws.readyState === WebSocket.OPEN || state.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }
    setStatus("connecting…", false);
    const ws = new WebSocket(wsUrl());
    state.ws = ws;

    ws.onopen = () => {
      state.connected = true;
      setStatus("connected", true);
      appendBubble("sys", "Connected to Palm Assist");
      // optional reconnect bind
      if (state.sessionId) {
        send({
          op: "bind",
          id: nextId(),
          session_id: state.sessionId,
          flow_id: state.flowId,
        });
      }
    };

    ws.onclose = () => {
      state.connected = false;
      setStatus("disconnected", false);
      appendBubble("sys", "Disconnected");
    };

    ws.onerror = () => {
      setStatus("error", false);
    };

    ws.onmessage = (ev) => {
      let msg;
      try {
        msg = JSON.parse(ev.data);
        messages.push(msg);
        console.log(messages);
      } catch {
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
  }

  function dispatch(partial) {
    const frame = {
      op: "dispatch",
      id: nextId(),
      format: "assistant",
      ...partial,
    };
    // ensure params object
    if (!frame.params) frame.params = {};
    send(frame);
  }

  function onFrame(msg) {
    const op = msg.op;
    if (op === "hello") {
      appendBubble("sys", `Palm ${msg.version || "?"} · protocol ${msg.protocol}`);
      if (msg.bound) {
        if (msg.bound.session_id) state.sessionId = msg.bound.session_id;
        if (msg.bound.flow_id) state.flowId = msg.bound.flow_id;
        setMeta();
      }
      // Human-first: open with operator-entry menu — no need to type "Hello"
      // Skip if reconnecting to an existing session or already bootstrapped.
      if (!state.bootstrapped && !state.sessionId) {
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
      state.sessionId = msg.session_id || null;
      state.flowId = msg.flow_id || null;
      setMeta();
      appendBubble("sys", "Session bound");
      return;
    }
    if (op === "error") {
      const err = msg.error || {};
      appendBubble("error", `${err.code || "error"}: ${err.message || "unknown"}`);
      return;
    }
    if (op === "turn") {
      if (msg.bound) {
        if (msg.bound.session_id) state.sessionId = msg.bound.session_id;
        if (msg.bound.flow_id) state.flowId = msg.bound.flow_id;
      }
      renderTurn(msg.payload || {});
      setMeta();
    }
  }

  function renderTurn(payload) {
    if (payload.session_id) state.sessionId = payload.session_id;
    if (payload.instance_id && !state.sessionId) state.sessionId = payload.instance_id;
    const refs = payload.refs || {};
    // Prefer path-derived flow (post auto-start) over sticky operator-entry bind
    const path = payload.path;
    if (Array.isArray(path) && path[0] === "flows" && path[1]) {
      state.flowId = path[1];
    } else if (refs.flow_id) {
      state.flowId = refs.flow_id;
    } else if (payload.flow_id) {
      state.flowId = payload.flow_id;
    }

    const q = payload.question || payload.hint || "";
    if (q) appendBubble("bot", q);
    if (payload.validation_error) {
      appendBubble("error", String(payload.validation_error));
    }

    state.lastInput = payload.input || null;
    renderInput(payload);
    renderActions(payload.actions || []);
  }

  function renderInput(payload) {
    choicesEl.innerHTML = "";
    fieldHost.innerHTML = "";
    textInput.value = "";
    textInput.disabled = false;
    btnSend.disabled = false;

    const schema = payload.input;
    const status = payload.status;

    if (status === "complete" || status === "failed") {
      textInput.placeholder = "Session finished";
      textInput.disabled = true;
      // still allow action chips below
    }

    const choices = (schema && schema.choices) || payload.choices || [];
    const widget = (schema && schema.widget) || (choices.length ? "choice" : "text");

    if (widget === "choice" && choices.length) {
      textInput.placeholder = "Or type a choice value…";
      for (const c of choices) {
        const value = c.value != null ? c.value : c;
        const label = c.label != null ? c.label : String(value);
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "chip";
        chip.textContent = c.n != null ? `${c.n}. ${label}` : label;
        chip.onclick = () => submitValue(String(value));
        choicesEl.appendChild(chip);
      }
    } else if (widget === "confirm") {
      textInput.placeholder = "yes / no";
      for (const [label, value] of [
        ["Yes", "yes"],
        ["No", "no"],
      ]) {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "chip";
        chip.textContent = label;
        chip.onclick = () => submitValue(value);
        choicesEl.appendChild(chip);
      }
    } else if (widget === "collection") {
      textInput.placeholder = schema?.collection_phase
        ? `Collection (${schema.collection_phase})…`
        : "add / done / item text…";
      if (schema?.error) {
        const err = document.createElement("div");
        err.className = "field-error";
        err.textContent = String(schema.error);
        fieldHost.appendChild(err);
      }
    } else {
      textInput.placeholder =
        schema?.required === false ? "Optional answer…" : "Type an answer…";
    }

    if (schema?.error && widget !== "collection") {
      const err = document.createElement("div");
      err.className = "field-error";
      err.textContent = String(schema.error);
      fieldHost.appendChild(err);
    }

    // Human-first: allow answers when waiting (or choices present), even if
    // mutation gate is missing/stale — chips stay usable.
    const waiting =
      status === "waiting" ||
      status === "running" ||
      (choices && choices.length > 0);
    const locked =
      payload.mutation &&
      payload.mutation.mutations_allowed === false &&
      !waiting;
    if (locked || status === "complete" || status === "failed") {
      if (status === "complete" || status === "failed" || locked) {
        textInput.disabled = true;
        btnSend.disabled = status === "complete" || status === "failed" || locked;
      }
    } else {
      textInput.focus();
    }
  }

  const NOISE_ACTIONS = new Set([
    "send answer",
    "inspect session",
    "resume session",
    "inspect this session",
  ]);

  function renderActions(actions) {
    // Append secondary action chips after choice chips (human-first: drop agent chrome)
    for (const action of actions) {
      if (!action || typeof action !== "object") continue;
      const label = action.label || "Action";
      if (NOISE_ACTIONS.has(String(label).toLowerCase())) continue;
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "chip secondary";
      chip.textContent = label;
      chip.onclick = () => runAction(action);
      choicesEl.appendChild(chip);
    }
  }

  function runAction(action) {
    const frame = { op: "dispatch", id: nextId(), format: "assistant" };
    if (action.alias) frame.alias = action.alias;
    if (action.path) frame.path = action.path;
    frame.params = { ...(action.params || {}) };
    const label = String(action.label || "").toLowerCase();
    // Fresh starts: do not drag prior session into a new operator-entry / flow create
    const freshStart =
      action.alias === "operator-entry/start" ||
      action.alias === "design-entry/start" ||
      (!!frame.params.flow_id && !frame.params.value && !frame.params.session_id && !action.path);
    if (freshStart) {
      state.sessionId = null;
      state.flowId = frame.params.flow_id || null;
      setMeta();
      // bind clear so server does not re-inject old session
      send({ op: "bind", id: nextId(), session_id: null, flow_id: frame.params.flow_id || null });
    } else {
      if (!frame.params.session_id && state.sessionId) {
        frame.params.session_id = state.sessionId;
      }
      if (!frame.params.flow_id && state.flowId) {
        frame.params.flow_id = state.flowId;
      }
    }
    appendBubbleUser(`[${action.label || "action"}]`);
    send(frame);
  }

  function submitValue(value) {
    const v = String(value ?? "").trim();
    if (!v && state.lastInput?.required !== false) {
      // allow empty only when not required
      if (state.lastInput?.required !== false) return;
    }
    appendBubbleUser(v || "(empty)");
    const params = { value: v };
    if (state.sessionId) params.session_id = state.sessionId;
    if (state.flowId) params.flow_id = state.flowId;
    dispatch({ params });
    textInput.value = "";
  }

  function appendBubbleUser(text) {
    appendBubble("user", text);
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    submitValue(textInput.value);
  });

  btnStart.onclick = () => {
    appendBubble("sys", "Starting operator entry…");
    state.sessionId = null;
    state.flowId = null;
    state.bootstrapped = true;
    setMeta();
    send({ op: "bind", id: nextId(), session_id: null, flow_id: null });
    send({
      op: "dispatch",
      id: nextId(),
      format: "assistant",
      alias: "operator-entry/start",
      params: {},
    });
  };

  btnMin.onclick = () => {
    panel.hidden = true;
  };

  fab.onclick = () => {
    panel.hidden = !panel.hidden;
    if (!panel.hidden) {
      connect();
      textInput.focus();
    }
  };

  // Auto-open when ?open=1
  if (new URLSearchParams(location.search).get("open") === "1") {
    panel.hidden = false;
    connect();
  }
})();
