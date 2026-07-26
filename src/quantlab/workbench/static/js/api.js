/** Cliente HTTP JSON hacia la API loopback del workbench. */
(function (global) {
  "use strict";

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
        throw new Error("Respuesta no JSON: " + text.slice(0, 120));
      }
    }
    if (!res.ok) {
      const msg = (data && data.error) || res.statusText || "error";
      const e = new Error(msg);
      e.status = res.status;
      e.payload = data;
      throw e;
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
    paperBook: function () {
      return request("GET", "/api/paper/book");
    },
    session: function () {
      return request("GET", "/api/session");
    },
    risk: function () {
      return request("GET", "/api/risk");
    },
    paperSubmit: function (intent) {
      return request("POST", "/api/paper/submit", intent);
    },
    paperFills: function () {
      return request("GET", "/api/paper/fills");
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
    labBacktest: function (body) {
      return request("POST", "/api/lab/backtest", body || {});
    },
    labScanner: function (body) {
      return request("POST", "/api/lab/scanner", body || {});
    },
    labOptimize: function (body) {
      return request("POST", "/api/lab/optimize", body || {});
    },
    labMonteCarlo: function (body) {
      return request("POST", "/api/lab/montecarlo", body || {});
    },
    labFeatures: function (body) {
      return request("POST", "/api/lab/features", body || {});
    },
    labExportHb: function (body) {
      return request("POST", "/api/lab/export-hb", body || {});
    },
    chat: function (message) {
      return request("POST", "/api/chat", { message: message });
    },
    chatTools: function () {
      return request("GET", "/api/chat/tools");
    },
  };
})(window);
