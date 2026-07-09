/**
 * Palm Portal dogfood (0.32.11) — floating chat over WebSocket Assist.
 * Renders payload.input for dynamic widgets; dispatches path/alias/params frames.
 * Intro auto-continue: separate intro_banner bubble + real step question.
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
  const btnMin = $("btn-min");

  const messages = [];
  let typingEl = null;
  let pendingTimer = null;

  const state = {
    ws: null,
    reqId: 0,
    sessionId: null,
    flowId: null,
    lastInput: null,
    connected: false,
    /** true after we auto-open operator-entry on connect (human-first) */
    bootstrapped: false,
    /** true while waiting for a turn after dispatch */
    pending: false,
  };

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
    statusEl.textContent = text;
    statusEl.style.color = ok ? "#5eead4" : "var(--muted)";
  }

  function setMeta() {
    const parts = [];
    if (state.sessionId) parts.push(`session ${state.sessionId.slice(0, 12)}…`);
    if (state.flowId) parts.push(`flow ${state.flowId}`);
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
    el.textContent = text;
    log.appendChild(el);
    scrollLogToEnd();
    return el;
  }

  function showTyping(label) {
    hideTyping();
    typingEl = document.createElement("div");
    typingEl.className = "bubble typing";
    typingEl.setAttribute("aria-label", label || "Waiting for response");
    typingEl.innerHTML =
      '<span class="typing-dots" aria-hidden="true"><span></span><span></span><span></span></span>' +
      `<span>${label || "Palm is thinking…"}</span>`;
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
      if (activityLabel) activityLabel.textContent = label || "Palm is thinking…";
      // Slight delay so fast turns don't flash the indicator
      pendingTimer = setTimeout(() => {
        if (state.pending) showTyping(label || "Palm is thinking…");
      }, 120);
    } else {
      meta.classList.remove("busy");
      form.classList.remove("busy");
      btnSend.classList.remove("busy");
      btnSend.textContent = "Send";
      hideTyping();
      // re-enable handled by renderInput
    }
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
      setPending(false);
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
      setPending(true, "Palm is thinking…");
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
        if (msg.bound.session_id) state.sessionId = msg.bound.session_id;
        if (msg.bound.flow_id) state.flowId = msg.bound.flow_id;
        setMeta();
      }
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
    renderInput(payload);
    renderActions(payload.actions || []);
    scrollLogToEnd();
  }

  function renderInput(payload) {
    choicesEl.innerHTML = "";
    fieldHost.innerHTML = "";
    textInput.value = "";
    textInput.disabled = false;
    btnSend.disabled = false;
    btnSend.textContent = "Send";

    const schema = payload.input;
    const status = payload.status;

    if (status === "complete" || status === "failed") {
      textInput.placeholder = "Session finished";
      textInput.disabled = true;
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
      const optional = schema?.required === false || schema?.skip_allowed;
      textInput.placeholder = optional
        ? "Optional — type a value or Skip"
        : schema?.collection_phase === "field"
          ? "Enter value…"
          : schema?.collection_phase
            ? `Collection (${schema.collection_phase})…`
            : "add / done / item text…";
      if (optional) addSkipChip(schema);
      if (schema?.error) {
        const err = document.createElement("div");
        err.className = "field-error";
        err.textContent = String(schema.error);
        fieldHost.appendChild(err);
      }
    } else {
      textInput.placeholder =
        schema?.required === false ? "Optional — type or Skip" : "Type an answer…";
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
      chip.textContent = label;
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
    const freshStart =
      action.alias === "operator-entry/start" ||
      action.alias === "design-entry/start" ||
      (!!frame.params.flow_id && !frame.params.value && !frame.params.session_id && !action.path);
    if (freshStart) {
      state.sessionId = null;
      state.flowId = frame.params.flow_id || null;
      setMeta();
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
    chip.textContent = (schema && schema.skip_label) || "Skip";
    chip.onclick = () => submitValue(schema?.skip_value != null ? schema.skip_value : "");
    choicesEl.appendChild(chip);
  }

  function submitValue(value) {
    if (state.pending) return;
    let v = String(value ?? "").trim();
    const optional = isOptionalInput(state.lastInput);
    if (optional && /^(skip|none|n\/a|na|-|pass|empty)$/i.test(v)) {
      v = "";
    }
    if (!v && !optional) {
      return;
    }
    appendBubbleUser(v || "Skip");
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
    if (state.pending) return;
    submitValue(textInput.value);
  });

  btnStart.onclick = () => {
    if (state.pending) return;
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
    syncVisualViewport(); // drop keyboard-lock + inline panel geometry
  };

  fab.onclick = () => {
    panel.hidden = !panel.hidden;
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

  if (new URLSearchParams(location.search).get("open") === "1") {
    panel.hidden = false;
    connect();
    syncVisualViewport();
  }
})();
