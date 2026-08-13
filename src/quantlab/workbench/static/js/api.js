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

  async function request(method, path, body, fetchOpts) {
    const opts = {
      method: method,
      headers: { Accept: "application/json" },
    };
    if (fetchOpts && fetchOpts.signal) {
      opts.signal = fetchOpts.signal;
    }
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
    openapi: function () {
      return request("GET", "/api/openapi.json");
    },
    diagnostics: function () {
      return request("GET", "/api/diagnostics");
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
    paperReconciliation: function () {
      return request("GET", "/api/paper/reconciliation");
    },
    paperRehydrate: function () {
      return request("POST", "/api/paper/reconciliation/rehydrate", {});
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
    labValidationRun: function (body, fetchOpts) {
      return request("POST", "/api/lab/validation/run", body || {}, fetchOpts);
    },
    labValidationGet: function (runId) {
      return request("GET", "/api/lab/validation/" + encodeURIComponent(runId));
    },
    labBacktest: function (body, fetchOpts) {
      return request("POST", "/api/lab/backtest", body || {}, fetchOpts);
    },
    labScanner: function (body, fetchOpts) {
      return request("POST", "/api/lab/scanner", body || {}, fetchOpts);
    },
    labOptimize: function (body, fetchOpts) {
      return request("POST", "/api/lab/optimize", body || {}, fetchOpts);
    },
    labOptimizeHistory: function () {
      return request("GET", "/api/lab/optimize/history");
    },
    labOptimizeGet: function (runId) {
      return request("GET", "/api/lab/optimize/history/" + encodeURIComponent(runId));
    },
    labMonteCarlo: function (body, fetchOpts) {
      return request("POST", "/api/lab/montecarlo", body || {}, fetchOpts);
    },
    labMonteCarloHistory: function () {
      return request("GET", "/api/lab/montecarlo/history");
    },
    labMonteCarloGet: function (runId) {
      return request("GET", "/api/lab/montecarlo/history/" + encodeURIComponent(runId));
    },
    labMonteCarloRun: function (runId) {
      return this.labMonteCarloGet(runId);
    },
    labMonteCarloDelete: function (runId) {
      return request("DELETE", "/api/lab/montecarlo/history/" + encodeURIComponent(runId));
    },
    labMontecarloJob: function (jobId) {
      return request("GET", "/api/lab/montecarlo/jobs/" + encodeURIComponent(jobId));
    },
    labMontecarloCancel: function (jobId) {
      return request(
        "POST",
        "/api/lab/montecarlo/jobs/" + encodeURIComponent(jobId) + "/cancel",
        {}
      );
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
    chat: function (message, context) {
      return request("POST", "/api/chat", {
        message: message,
        context: context || { pane: "chat" },
      });
    },
    chatHistory: function () {
      return request("GET", "/api/chat/history");
    },
    chatClear: function () {
      return request("POST", "/api/chat/clear", {});
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
    diagnostics: function () {
      return request("GET", "/api/diagnostics");
    },
    diagnosticsDownloadUrl: function () {
      return "/api/diagnostics.json";
    },
    supportBundleUrl: function () {
      return "/api/support-bundle.zip";
    },
    liveStatus: function () {
      return request("GET", "/api/live/status");
    },
    testnetStatus: function () {
      return request("GET", "/api/live/testnet");
    },
    testnetBalances: function (market) {
      var m = market || "spot";
      return request(
        "GET",
        "/api/live/testnet/balances?market=" + encodeURIComponent(m)
      );
    },
    liveUnlock: function (username, password, venueScope) {
      return request("POST", "/api/live/unlock", {
        username: username,
        password: password,
        venue_scope: venueScope || "binance_demo",
      });
    },
    liveLock: function () {
      return request("POST", "/api/live/lock", {});
    },
    liveDemoSubmit: function (payload) {
      return request("POST", "/api/live/demo/submit", payload || {});
    },
    liveDemoCancel: function (orderId) {
      return request("POST", "/api/live/demo/cancel", { order_id: orderId });
    },
    liveDemoFills: function () {
      return request("GET", "/api/live/demo/fills");
    },
    liveDemoOpenOrders: function () {
      return request("GET", "/api/live/demo/open-orders");
    },
    executionStrategies: function () {
      return request("GET", "/api/execution/strategies");
    },
    executionStrategyCapabilities: function (strategyId) {
      return request(
        "GET",
        "/api/execution/strategies/" + encodeURIComponent(strategyId) + "/capabilities"
      );
    },
    executionCreatePromotion: function (body) {
      return request("POST", "/api/execution/promotions", body || {});
    },
    executionRun: function (body) {
      return request("POST", "/api/execution/run", body || {});
    },
    executionLive: function (sessionId) {
      var q = sessionId
        ? "?session_id=" + encodeURIComponent(sessionId)
        : "";
      return request("GET", "/api/execution/live" + q);
    },
    executionValidatePromotion: function (promotionId) {
      return request(
        "POST",
        "/api/execution/promotions/" + encodeURIComponent(promotionId) + "/validate",
        {}
      );
    },
    executionPreflightPromotion: function (promotionId) {
      return request(
        "POST",
        "/api/execution/promotions/" + encodeURIComponent(promotionId) + "/preflight",
        {}
      );
    },
    executionOpenSession: function (promotionId) {
      return request(
        "POST",
        "/api/execution/promotions/" + encodeURIComponent(promotionId) + "/open-session",
        {}
      );
    },
    executionSessionStatus: function (sessionId) {
      return request(
        "GET",
        "/api/execution/sessions/" + encodeURIComponent(sessionId) + "/status"
      );
    },
    executionStopSession: function (sessionId) {
      return request(
        "POST",
        "/api/execution/sessions/" + encodeURIComponent(sessionId) + "/stop",
        {}
      );
    },
    executionStartPaper: function (sessionId, body) {
      return request(
        "POST",
        "/api/execution/sessions/" + encodeURIComponent(sessionId) + "/start-paper",
        body || {}
      );
    },
    executionSessions: function () {
      return request("GET", "/api/execution/sessions");
    },
    executionHummingbotStatus: function () {
      return request("GET", "/api/execution/hummingbot/status");
    },
    binanceScan: function (limit) {
      return request("POST", "/api/lab/binance/scan", { limit: limit || 20 });
    },
    binanceKlines: function (opts) {
      var o = opts || {};
      return request("POST", "/api/lab/binance/klines", {
        symbol: o.symbol || "BTCUSDT",
        interval: o.interval || "1m",
        limit: o.limit != null ? o.limit : 120,
        market_type: o.market_type || "spot",
        network: o.network || "mainnet",
      });
    },
    binanceScanner: function (opts) {
      const o = opts || {};
      return request("POST", "/api/lab/binance/scanner", {
        top_n: o.top_n || 5,
        symbol_limit: o.symbol_limit || 15,
        interval: o.interval || "1h",
        kline_limit: o.kline_limit || 24,
        profile: o.profile || "legacy_v1",
      });
    },
    pairwiseScanner: function (opts) {
      const o = opts || {};
      return request("POST", "/api/lab/pairwise/scanner", {
        venue: o.venue || "binance",
        market_type: o.market_type || "spot",
        symbol_limit: o.symbol_limit != null ? o.symbol_limit : 20,
        interval: o.interval || "1h",
        kline_limit: o.kline_limit != null ? o.kline_limit : 720,
        top_n: o.top_n != null ? o.top_n : 10,
        include_signals: o.include_signals !== false,
        run_validation: !!o.run_validation,
        include_ml: o.include_ml !== false,
        detectors: o.detectors || undefined,
      });
    },
    validateCandidate: function (opts) {
      const o = opts || {};
      return request("POST", "/api/lab/validate-candidate", {
        signal: o.signal,
        strategy_id: o.strategy_id,
        params: o.params || {},
        venue: o.venue || "binance",
        market_type: o.market_type || "spot",
        interval: o.interval || "1h",
        kline_limit: o.kline_limit != null ? o.kline_limit : 240,
        underlyings: o.underlyings || undefined,
        scan_id: o.scan_id || undefined,
      });
    },
    validatedStrategies: function () {
      return request("GET", "/api/lab/validated-strategies");
    },
    labDetectors: function () {
      return request("GET", "/api/lab/detectors");
    },
    venueScanner: function (opts) {
      const o = opts || {};
      const body = {
        market_type: o.market_type || "spot",
        top_n: o.top_n || 5,
        symbol_limit: o.symbol_limit != null ? o.symbol_limit : 30,
        interval: o.interval || "1h",
        profile: o.profile || "trend",
        include_ml: o.include_ml !== false,
      };
      if (o.venues && o.venues.length) {
        body.venues = o.venues;
      } else {
        body.venue = o.venue || "binance";
      }
      if (o.kline_limit != null && o.kline_limit !== "") {
        body.kline_limit = o.kline_limit;
      }
      if (o.period_days != null && o.period_days !== "") {
        body.period_days = o.period_days;
      }
      if (o.underlyings && o.underlyings.length) {
        body.underlyings = o.underlyings;
      }
      if (o.kronos && typeof o.kronos === "object") {
        body.kronos = o.kronos;
      } else {
        const kronos = {};
        if (o.kronos_enabled != null) kronos.kronos_enabled = o.kronos_enabled;
        if (o.kronos_top_n != null) kronos.kronos_top_n = o.kronos_top_n;
        if (o.kronos_pred_len != null) kronos.kronos_pred_len = o.kronos_pred_len;
        if (o.kronos_sample_count != null)
          kronos.kronos_sample_count = o.kronos_sample_count;
        if (o.kronos_lookback != null) kronos.kronos_lookback = o.kronos_lookback;
        if (o.kronos_legacy_override != null)
          kronos.kronos_legacy_override = o.kronos_legacy_override;
        if (Object.keys(kronos).length) body.kronos = kronos;
      }
      return request("POST", "/api/lab/venue/scanner", body, o.fetchOpts);
    },
    alphaProfiles: function () {
      return request("GET", "/api/lab/alpha/profiles");
    },
    binancePipeline: function (opts) {
      const o = opts || {};
      return request("POST", "/api/lab/binance/pipeline", {
        strategy_id: o.strategy_id || "momentum",
        params: o.params || {},
        top_n: o.top_n || 5,
        symbol_limit: o.symbol_limit || 15,
        interval: o.interval || "1h",
        kline_limit: o.kline_limit || 24,
        experiment_id: o.experiment_id || "wb-bn-pipe",
        walk_forward: o.walk_forward !== false,
        rank_fraction: o.rank_fraction != null ? o.rank_fraction : 0.7,
        profile: o.profile || "legacy_v1",
      });
    },
    a3MdStatus: function () {
      return request("GET", "/api/lab/a3/md-status");
    },
    about: function () {
      return request("GET", "/api/about");
    },
    simFees: function () {
      return request("GET", "/api/lab/sim/fees");
    },
    simUniverse: function (opts) {
      opts = opts || {};
      var q = [];
      if (opts.market_type) {
        q.push("market_type=" + encodeURIComponent(opts.market_type));
      }
      if (opts.hl_live != null) {
        q.push("hl_live=" + (opts.hl_live ? "1" : "0"));
      }
      var qs = q.length ? "?" + q.join("&") : "";
      return request("GET", "/api/lab/sim/universe" + qs);
    },
    simPeriod: function (periodDays, interval) {
      var q =
        "period_days=" +
        encodeURIComponent(periodDays) +
        "&interval=" +
        encodeURIComponent(interval || "1h");
      return request("GET", "/api/lab/sim/period?" + q);
    },
    simCompare: function (body, fetchOpts) {
      return request("POST", "/api/lab/sim/compare", body || {}, fetchOpts);
    },
    simRankStrategies: function (body, fetchOpts) {
      return request(
        "POST",
        "/api/lab/sim/rank-strategies",
        body || {},
        fetchOpts
      );
    },
    simSizing: function (body) {
      return request("POST", "/api/lab/sim/sizing", body || {});
    },
    updateStatus: function () {
      return request("GET", "/api/update/status");
    },
    updateApply: function () {
      return request("POST", "/api/update/apply", {});
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
