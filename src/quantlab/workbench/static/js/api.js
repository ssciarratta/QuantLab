/** Cliente HTTP JSON hacia la API loopback del workbench. */
(function (global) {
  "use strict";

  // Paths que disparan toast success/error (F41).
  const TOAST_LABELS = {
    "POST /api/broker/connect": "Connect",
    "POST /api/broker/reconnect": "Reconnect",
    "POST /api/broker/disconnect": "Disconnect",
    "POST /api/paper/submit": "Submit",
    "POST /api/paper/kill": "Kill switch",
    "POST /api/lab/backtest": "Backtest",
    "POST /api/lab/optimize": "Optimize",
    "GET /api/session/export": "Export",
    "POST /api/session/import": "Import",
    "POST /api/watchlist/import": "Watchlist import",
    "POST /api/presets/apply": "Preset",
    "POST /api/presets/save": "Preset save",
    "DELETE /api/presets/{name}": "Preset delete",
  };

  function toastKey(method, path) {
    const base = String(path || "").split("?")[0];
    if (method === "DELETE" && /^\/api\/presets\/[^/]+$/.test(base)) {
      return "DELETE /api/presets/{name}";
    }
    return method + " " + base;
  }

  function maybeToast(method, path, ok, message) {
    const label = TOAST_LABELS[toastKey(method, path)];
    if (!label || !global.QLToasts) return;
    if (ok) {
      global.QLToasts.success(label + " · " + (message || "ok"));
    } else {
      global.QLToasts.error(label + " · " + (message || "error"));
    }
  }

  async function request(method, path, body) {
    const opts = {
      method: method,
      headers: { Accept: "application/json" },
    };
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(path, opts);
    let data = null;
    const text = await res.text();
    if (text) {
      try {
        data = JSON.parse(text);
      } catch (err) {
        maybeToast(method, path, false, "respuesta no JSON");
        throw new Error("Respuesta no JSON: " + text.slice(0, 120));
      }
    }
    if (!res.ok) {
      const msg = (data && data.error) || res.statusText || "error";
      maybeToast(method, path, false, msg);
      const e = new Error(msg);
      e.status = res.status;
      e.payload = data;
      throw e;
    }
    const brief =
      (data && (data.message || data.filename || data.venue || data.kind)) || "ok";
    maybeToast(method, path, true, String(brief));
    // F72: desktop Notification on kill engage (opt-in settings).
    if (
      method === "POST" &&
      String(path || "").split("?")[0] === "/api/paper/kill" &&
      data &&
      data.engaged === true &&
      global.QLToasts &&
      typeof global.QLToasts.notifyKillEngage === "function"
    ) {
      global.QLToasts.notifyKillEngage("Paper kill ENGAGED");
    }
    return data;
  }

  global.QLApi = {
    get: function (path) {
      return request("GET", path);
    },
    post: function (path, body) {
      return request("POST", path, body || {});
    },
    put: function (path, body) {
      return request("PUT", path, body || {});
    },
    health: function () {
      return request("GET", "/api/health");
    },
    getMode: function () {
      return request("GET", "/api/mode");
    },
    setMode: function (mode) {
      return request("POST", "/api/mode", { mode: mode });
    },
    venues: function () {
      return request("GET", "/api/venues");
    },
    connect: function (venue, mode, opts) {
      const body = { venue: venue, mode: mode };
      if (opts && opts.md_source) {
        body.md_source = opts.md_source;
      }
      if (opts && opts.csv_path) {
        body.csv_path = opts.csv_path;
      }
      if (opts && opts.slippage_bps != null && opts.slippage_bps !== "") {
        body.slippage_bps = opts.slippage_bps;
      }
      return request("POST", "/api/broker/connect", body);
    },
    reconnect: function () {
      return request("POST", "/api/broker/reconnect", {});
    },
    disconnect: function () {
      return request("POST", "/api/broker/disconnect", {});
    },
    instruments: function () {
      return request("GET", "/api/broker/instruments");
    },
    snapshot: function (symbol) {
      return request("GET", "/api/broker/snapshot?symbol=" + encodeURIComponent(symbol));
    },
    account: function () {
      return request("GET", "/api/broker/account");
    },
    positions: function () {
      return request("GET", "/api/broker/positions");
    },
    brokerHeartbeat: function () {
      return request("GET", "/api/broker/heartbeat");
    },
    paperBook: function () {
      return request("GET", "/api/paper/book");
    },
    paperEquity: function (limit) {
      const q =
        limit != null ? "?limit=" + encodeURIComponent(String(limit)) : "?limit=200";
      return request("GET", "/api/paper/equity" + q);
    },
    paperPnl: function () {
      return request("GET", "/api/paper/pnl");
    },
    session: function () {
      return request("GET", "/api/session");
    },
    sessionsList: function () {
      return request("GET", "/api/sessions");
    },
    sessionsSwitch: function (sessionId) {
      return request("POST", "/api/sessions/switch", { session_id: sessionId });
    },
    sessionsNew: function (body) {
      return request("POST", "/api/sessions/new", body || {});
    },
    getActivity: function (limit) {
      const q =
        limit != null ? "?limit=" + encodeURIComponent(String(limit)) : "?limit=100";
      return request("GET", "/api/activity" + q);
    },
    getAccessLog: function (limit) {
      const q =
        limit != null ? "?limit=" + encodeURIComponent(String(limit)) : "?limit=100";
      return request("GET", "/api/access-log" + q);
    },
    getBackups: function () {
      return request("GET", "/api/backups");
    },
    runBackup: function () {
      return request("POST", "/api/backups/run", {});
    },
    getOpsMetrics: function () {
      return request("GET", "/api/ops/metrics");
    },
    risk: function () {
      return request("GET", "/api/risk");
    },
    riskUtilization: function () {
      return request("GET", "/api/risk/utilization");
    },
    paperKill: function () {
      return request("GET", "/api/paper/kill");
    },
    setPaperKill: function (engaged) {
      return request("POST", "/api/paper/kill", { engaged: !!engaged });
    },
    paperSubmit: function (intent) {
      return request("POST", "/api/paper/submit", intent);
    },
    paperFills: function () {
      return request("GET", "/api/paper/fills");
    },
    paperFillsCsvUrl: function () {
      return "/api/paper/fills.csv";
    },
    getLayout: function () {
      return request("GET", "/api/layout");
    },
    putLayout: function (layout) {
      return request("PUT", "/api/layout", layout || {});
    },
    getPresets: function () {
      return request("GET", "/api/presets");
    },
    applyPreset: function (name) {
      return request("POST", "/api/presets/apply", { name: name });
    },
    savePreset: function (name, extra) {
      const body = Object.assign({ name: name }, extra || {});
      return request("POST", "/api/presets/save", body);
    },
    deletePreset: function (name) {
      const key = encodeURIComponent(String(name || "").trim());
      return request("DELETE", "/api/presets/" + key);
    },
    watchlist: function () {
      return request("GET", "/api/watchlist");
    },
    putWatchlist: function (body) {
      return request("PUT", "/api/watchlist", body || {});
    },
    watchlistExportUrl: function () {
      return "/api/watchlist/export";
    },
    importWatchlist: function (body) {
      return request("POST", "/api/watchlist/import", body || {});
    },
    universe: function () {
      return request("GET", "/api/universe");
    },
    catalog: function () {
      return request("GET", "/api/catalog");
    },
    paperSessionStart: function (body) {
      return request("POST", "/api/paper/session/start", body || {});
    },
    paperSessionStop: function () {
      return request("POST", "/api/paper/session/stop", {});
    },
    paperSessionStep: function () {
      return request("POST", "/api/paper/session/step", {});
    },
    paperSessionStatus: function () {
      return request("GET", "/api/paper/session/status");
    },
    labCapabilities: function () {
      return request("GET", "/api/lab/capabilities");
    },
    labStrategies: function () {
      return request("GET", "/api/lab/strategies");
    },
    labMetrics: function () {
      return request("GET", "/api/lab/metrics");
    },
    labExperiments: function () {
      return request("GET", "/api/lab/experiments");
    },
    labValidation: function () {
      return request("GET", "/api/lab/validation");
    },
    labValidationRun: function (body) {
      return request("POST", "/api/lab/validation/run", body || {});
    },
    labValidationGet: function (runId) {
      return request("GET", "/api/lab/validation/" + encodeURIComponent(runId));
    },
    labBacktest: function (body) {
      return request("POST", "/api/lab/backtest", body || {});
    },
    labScanner: function (body) {
      return request("POST", "/api/lab/scanner", body || {});
    },
    labOptimize: function (body) {
      return request("POST", "/api/lab/optimize", body || {});
    },
    labOptimizeHistory: function () {
      return request("GET", "/api/lab/optimize/history");
    },
    labOptimizeGet: function (runId) {
      return request("GET", "/api/lab/optimize/history/" + encodeURIComponent(runId));
    },
    labMonteCarlo: function (body) {
      return request("POST", "/api/lab/montecarlo", body || {});
    },
    labMonteCarloHistory: function () {
      return request("GET", "/api/lab/montecarlo/history");
    },
    labMonteCarloGet: function (runId) {
      return request("GET", "/api/lab/montecarlo/history/" + encodeURIComponent(runId));
    },
    labFeatures: function (body) {
      return request("POST", "/api/lab/features/run", body || {});
    },
    labFeaturesRun: function (body) {
      return request("POST", "/api/lab/features/run", body || {});
    },
    labFeaturesStore: function () {
      return request("GET", "/api/lab/features/store");
    },
    labExportHb: function (body) {
      return request("POST", "/api/lab/export-hb", body || {});
    },
    labExports: function () {
      return request("GET", "/api/lab/exports");
    },
    labExportGet: function (exportId) {
      return request("GET", "/api/lab/exports/" + encodeURIComponent(exportId));
    },
    labReports: function () {
      return request("GET", "/api/lab/reports");
    },
    labReport: function (reportId) {
      return request("GET", "/api/lab/reports/" + encodeURIComponent(reportId));
    },
    chat: function (message) {
      return request("POST", "/api/chat", { message: message });
    },
    chatTools: function () {
      return request("GET", "/api/chat/tools");
    },
    commands: function () {
      return request("GET", "/api/commands");
    },
    getSettings: function () {
      return request("GET", "/api/settings");
    },
    putSettings: function (body) {
      return request("PUT", "/api/settings", body || {});
    },
    getI18n: function (locale) {
      const loc = encodeURIComponent(locale || "es");
      return request("GET", "/api/i18n/" + loc);
    },
    getOnboarding: function () {
      return request("GET", "/api/onboarding");
    },
    completeOnboarding: function (body) {
      return request("POST", "/api/onboarding/complete", body || {});
    },
    docsList: function () {
      return request("GET", "/api/docs");
    },
    docsContent: function (path) {
      return request(
        "GET",
        "/api/docs/content?path=" + encodeURIComponent(path || "")
      );
    },
    openapi: function () {
      return request("GET", "/api/openapi.json");
    },
    about: function () {
      return request("GET", "/api/about");
    },
    sessionExport: function () {
      return request("GET", "/api/session/export");
    },
    sessionExportDownloadUrl: function () {
      return "/api/session/export?download=1";
    },
    sessionImport: function (body) {
      return request("POST", "/api/session/import", body || {});
    },
  };
})(window);
