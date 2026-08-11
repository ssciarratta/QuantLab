/** Gráfico Corrida en vivo — lightweight-charts (preferido) + canvas con ejes. */
(function (global) {
  "use strict";

  var LC_WAIT_MS = 8000;
  var LC_POLL_MS = 100;

  var INTERVAL_SEC = {
    "1m": 60,
    "3m": 180,
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
  };

  function resolveIntervalSec(tf) {
    if (!tf) return 60;
    var key = String(tf).trim();
    return INTERVAL_SEC[key] || 60;
  }

  function nowSec(serverNow) {
    var client = Math.floor(Date.now() / 1000);
    if (serverNow != null && isFinite(Number(serverNow))) {
      return Math.min(client, Math.floor(Number(serverNow)));
    }
    return client;
  }

  function barOpenTime(tsSec, sec) {
    var s = sec > 0 ? sec : 60;
    return Math.floor(tsSec / s) * s;
  }

  /** LC v4 muestra UTC en eje; codificamos hora local como UTC para alinear con reloj del usuario. */
  function toLocalChartTime(utcSec) {
    var d = new Date(utcSec * 1000);
    return Math.floor(
      Date.UTC(
        d.getFullYear(),
        d.getMonth(),
        d.getDate(),
        d.getHours(),
        d.getMinutes(),
        d.getSeconds()
      ) / 1000
    );
  }

  function toChartBar(bar) {
    return {
      time: toLocalChartTime(bar.time),
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
    };
  }

  function formatChartAxisTime(time) {
    var ts =
      typeof time === "number"
        ? time
        : time && time.timestamp != null
          ? time.timestamp
          : time && time.year != null
            ? Math.floor(
                Date.UTC(
                  time.year,
                  time.month - 1,
                  time.day,
                  time.hour || 0,
                  time.minute || 0,
                  time.second || 0
                ) / 1000
              )
            : null;
    if (ts == null) return "";
    var d = new Date(ts * 1000);
    var hh = String(d.getUTCHours()).padStart(2, "0");
    var mm = String(d.getUTCMinutes()).padStart(2, "0");
    return hh + ":" + mm;
  }

  function parseBarTime(raw) {
    if (raw == null) return null;
    var t = raw;
    if (typeof t === "string") t = Math.floor(new Date(t).getTime() / 1000);
    if (typeof t !== "number" || !isFinite(t)) return null;
    if (t > 1e12) t = Math.floor(t / 1000);
    return t;
  }

  function normalizeBars(bars, intervalSec, serverNow) {
    if (!bars || !bars.length) return [];
    var sec = intervalSec > 0 ? intervalSec : 60;
    var now = nowSec(serverNow);
    var formingOpen = barOpenTime(now, sec);
    var byTime = {};
    for (var i = 0; i < bars.length; i++) {
      var b = bars[i];
      var t = parseBarTime(b.time);
      if (t == null) continue;
      t = barOpenTime(t, sec);
      if (t > formingOpen) continue;
      var o = Number(b.open);
      var h = Number(b.high);
      var l = Number(b.low);
      var c = Number(b.close);
      if (!isFinite(o) || !isFinite(h) || !isFinite(l) || !isFinite(c)) continue;
      byTime[t] = { time: t, open: o, high: h, low: l, close: c };
    }
    var out = Object.keys(byTime)
      .map(function (k) {
        return byTime[k];
      })
      .sort(function (a, b) {
        return a.time - b.time;
      });
    return out;
  }

  function trimSyntheticBars(bars, intervalSec) {
    if (!bars || bars.length < 2) return bars || [];
    var sec = intervalSec > 0 ? intervalSec : 60;
    var out = [bars[0]];
    for (var i = 1; i < bars.length; i++) {
      var prev = out[out.length - 1];
      var cur = bars[i];
      var delta = cur.time - prev.time;
      if (delta > 0 && delta < sec) continue;
      if (cur.time === prev.time) {
        out[out.length - 1] = cur;
        continue;
      }
      out.push(cur);
    }
    return out;
  }

  function clipBarsToNow(bars, intervalSec, serverNow) {
    if (!bars || !bars.length) return [];
    var sec = intervalSec > 0 ? intervalSec : 60;
    var formingOpen = barOpenTime(nowSec(serverNow), sec);
    var out = bars.filter(function (b) {
      return b.time <= formingOpen;
    });
    return trimSyntheticBars(out, sec);
  }

  function parseTs(fill) {
    var raw = fill.ts || fill.timestamp || fill.time;
    if (!raw) return null;
    if (typeof raw === "number") return raw > 1e12 ? Math.floor(raw / 1000) : raw;
    var d = new Date(raw);
    if (isNaN(d.getTime())) return null;
    return Math.floor(d.getTime() / 1000);
  }

  function showMessage(wrap, msg) {
    var existing = wrap.querySelector(".slt-chart-placeholder");
    if (existing) {
      existing.textContent = String(msg || "Sin datos");
      return;
    }
    var el = document.createElement("div");
    el.className = "slt-chart-placeholder muted";
    el.textContent = String(msg || "Sin datos");
    wrap.appendChild(el);
  }

  function clearMessage(wrap) {
    var el = wrap.querySelector(".slt-chart-placeholder");
    if (el) el.remove();
  }

  function measureWrap(wrap, height) {
    var w = wrap.clientWidth || 0;
    if (w < 80) {
      var p = wrap.parentElement;
      while (p && w < 80) {
        w = p.clientWidth || 0;
        p = p.parentElement;
      }
    }
    return { w: Math.max(160, w || 480), h: height || 200 };
  }

  function fmtPrice(v) {
    if (!isFinite(v)) return "";
    if (Math.abs(v) >= 1000) return v.toFixed(2);
    if (Math.abs(v) >= 1) return v.toFixed(4);
    return v.toFixed(6);
  }

  function fmtTimeLocal(ts) {
    var d = new Date(ts * 1000);
    var hh = String(d.getHours()).padStart(2, "0");
    var mm = String(d.getMinutes()).padStart(2, "0");
    return hh + ":" + mm;
  }

  function drawCanvasChart(wrap, bars, height) {
    var size = measureWrap(wrap, height);
    wrap.innerHTML = "";
    var canvas = document.createElement("canvas");
    canvas.className = "slt-chart-canvas slt-chart-canvas-fallback";
    canvas.width = size.w;
    canvas.height = size.h;
    wrap.appendChild(canvas);
    if (!bars.length) {
      showMessage(wrap, "Sin velas para graficar");
      return;
    }
    var ctx = canvas.getContext("2d");
    if (!ctx) return;

    var pad = { t: 10, r: 52, b: 22, l: 8 };
    var plotW = size.w - pad.l - pad.r;
    var plotH = size.h - pad.t - pad.b;
    var lo = Infinity;
    var hi = -Infinity;
    bars.forEach(function (b) {
      lo = Math.min(lo, b.low);
      hi = Math.max(hi, b.high);
    });
    if (!isFinite(lo) || !isFinite(hi) || hi <= lo) return;

    var margin = (hi - lo) * 0.04;
    lo -= margin;
    hi += margin;

    ctx.fillStyle = "#14101c";
    ctx.fillRect(0, 0, size.w, size.h);

    ctx.strokeStyle = "rgba(255,255,255,0.08)";
    ctx.lineWidth = 1;
    ctx.font = "10px system-ui, sans-serif";
    ctx.fillStyle = "#9a93ad";
    ctx.textAlign = "right";
    for (var g = 0; g <= 4; g++) {
      var gy = pad.t + (plotH * g) / 4;
      ctx.beginPath();
      ctx.moveTo(pad.l, gy);
      ctx.lineTo(pad.l + plotW, gy);
      ctx.stroke();
      var price = hi - ((hi - lo) * g) / 4;
      ctx.fillText(fmtPrice(price), size.w - 4, gy + 3);
    }

    ctx.textAlign = "center";
    var n = bars.length;
    var step = Math.max(1, Math.floor(n / 5));
    for (var ti = 0; ti < n; ti += step) {
      var tx = pad.l + (plotW * (ti + 0.5)) / n;
      ctx.fillText(fmtTimeLocal(bars[ti].time), tx, size.h - 6);
    }

    var slot = plotW / n;
    var bodyW = Math.max(1, slot * 0.55);
    bars.forEach(function (b, i) {
      var x = pad.l + i * slot + slot / 2;
      var yOpen = pad.t + ((hi - b.open) / (hi - lo)) * plotH;
      var yClose = pad.t + ((hi - b.close) / (hi - lo)) * plotH;
      var yHi = pad.t + ((hi - b.high) / (hi - lo)) * plotH;
      var yLo = pad.t + ((hi - b.low) / (hi - lo)) * plotH;
      var up = b.close >= b.open;
      ctx.strokeStyle = up ? "#5dd39e" : "#ff7b7b";
      ctx.fillStyle = up ? "#5dd39e" : "#ff7b7b";
      ctx.beginPath();
      ctx.moveTo(x, yHi);
      ctx.lineTo(x, yLo);
      ctx.stroke();
      var top = Math.min(yOpen, yClose);
      var bh = Math.max(1, Math.abs(yClose - yOpen));
      ctx.fillRect(x - bodyW / 2, top, bodyW, bh);
    });
  }

  function addCandleSeries(chart) {
    if (typeof chart.addCandlestickSeries === "function") {
      return chart.addCandlestickSeries({
        upColor: "#5dd39e",
        downColor: "#ff7b7b",
        borderUpColor: "#5dd39e",
        borderDownColor: "#ff7b7b",
        wickUpColor: "#5dd39e",
        wickDownColor: "#ff7b7b",
      });
    }
    var LC = global.LightweightCharts;
    if (LC && typeof chart.addSeries === "function" && LC.CandlestickSeries) {
      return chart.addSeries(LC.CandlestickSeries, {
        upColor: "#5dd39e",
        downColor: "#ff7b7b",
        borderUpColor: "#5dd39e",
        borderDownColor: "#ff7b7b",
        wickUpColor: "#5dd39e",
        wickDownColor: "#ff7b7b",
      });
    }
    return null;
  }

  function applyMarkers(series, markers) {
    if (!series) return;
    if (typeof series.setMarkers === "function") {
      series.setMarkers(markers);
      return;
    }
    var LC = global.LightweightCharts;
    if (LC && typeof LC.createSeriesMarkers === "function") {
      if (!series._sltMarkers) {
        series._sltMarkers = LC.createSeriesMarkers(series, markers);
      } else if (series._sltMarkers.setMarkers) {
        series._sltMarkers.setMarkers(markers);
      }
    }
  }

  function waitForLc(cb, started) {
    started = started || Date.now();
    if (global.LightweightCharts && typeof global.LightweightCharts.createChart === "function") {
      cb(true);
      return;
    }
    if (Date.now() - started > LC_WAIT_MS) {
      cb(false);
      return;
    }
    setTimeout(function () {
      waitForLc(cb, started);
    }, LC_POLL_MS);
  }

  function createSltChart(opts) {
    opts = opts || {};
    var wrap = opts.container;
    var height = opts.height || 200;
    var chartInterval = opts.interval || "1m";
    var intervalSec = resolveIntervalSec(chartInterval);
    var lastBars = [];
    var lastFills = [];
    var serverNowSec = null;
    var chartSymbol = null;
    var mode = "none";
    var chart = null;
    var series = null;
    var chartEl = null;
    var ro = null;
    var destroyed = false;

    if (!wrap) {
      return {
        ready: false,
        mode: function () {
          return "none";
        },
        hasSeries: function () {
          return false;
        },
        setInterval: function () {},
        loadKlines: function () {},
        updateMarket: function () {},
        setFills: function () {},
        resize: function () {},
        destroy: function () {},
      };
    }

    function syncInterval(tf) {
      if (!tf) return;
      chartInterval = String(tf);
      intervalSec = resolveIntervalSec(chartInterval);
    }

    function applyVisibleWindow() {
      if (!chart || !lastBars.length) return;
      try {
        chart.timeScale().fitContent();
        var ps = chart.priceScale("right");
        if (ps && ps.applyOptions) {
          ps.applyOptions({ autoScale: true });
        }
      } catch (e) {}
    }

    function priceInRange(px, ref) {
      if (!isFinite(px) || !isFinite(ref) || ref <= 0) return true;
      var ratio = px / ref;
      return ratio >= 0.2 && ratio <= 5;
    }

    function resetSeriesData() {
      lastBars = [];
      lastFills = [];
      if (mode === "lc" && series) {
        try {
          series.setData([]);
          applyMarkers(series, []);
        } catch (e) {}
      }
    }

    function renderSeriesData() {
      if (mode === "lc" && series && chart) {
        series.setData(lastBars.map(toChartBar));
        applyVisibleWindow();
      } else if (mode === "canvas" && lastBars.length) {
        drawCanvasChart(wrap, lastBars, height);
      }
      refreshMarkers();
    }

    function buildNowMarker() {
      var formingOpen = barOpenTime(nowSec(serverNowSec), intervalSec);
      if (!lastBars.length) return null;
      var hasBar = lastBars.some(function (b) {
        return b.time === formingOpen;
      });
      if (!hasBar) return null;
      return {
        time: toLocalChartTime(formingOpen),
        position: "inBar",
        color: "rgba(200, 196, 216, 0.85)",
        shape: "circle",
        text: "Ahora",
      };
    }

    function buildFillMarkers(fills) {
      var now = nowSec(serverNowSec);
      var formingOpen = barOpenTime(now, intervalSec);
      return (fills || [])
        .map(function (f) {
          var t = parseTs(f);
          if (!t || t > now) return null;
          t = barOpenTime(t, intervalSec);
          if (t > formingOpen) return null;
          var side = String(f.side || "").toUpperCase();
          var isBuy = side === "BUY" || side === "B";
          return {
            time: toLocalChartTime(t),
            position: isBuy ? "belowBar" : "aboveBar",
            color: isBuy ? "#5dd39e" : "#ff7b7b",
            shape: isBuy ? "arrowUp" : "arrowDown",
            text: isBuy ? "C" : "V",
          };
        })
        .filter(Boolean)
        .sort(function (a, b) {
          return a.time - b.time;
        });
    }

    function refreshMarkers() {
      if (mode !== "lc" || !series) return;
      var markers = buildFillMarkers(lastFills);
      var nowMarker = buildNowMarker();
      if (nowMarker) markers.push(nowMarker);
      applyMarkers(series, markers);
    }

    function destroyLc() {
      if (ro) {
        ro.disconnect();
        ro = null;
      }
      if (chart) {
        try {
          chart.remove();
        } catch (e) {}
      }
      chart = null;
      series = null;
      chartEl = null;
      if (mode === "lc") mode = "none";
    }

    function buildLc() {
      if (destroyed || !wrap || !global.LightweightCharts) return false;
      var size = measureWrap(wrap, height);
      if (size.w < 80) return false;

      destroyLc();
      wrap.innerHTML = "";
      chartEl = document.createElement("div");
      chartEl.className = "slt-chart-canvas slt-chart-lc";
      chartEl.style.width = "100%";
      chartEl.style.height = height + "px";
      wrap.appendChild(chartEl);

      var LC = global.LightweightCharts;
      var crossMode =
        LC.CrosshairMode && LC.CrosshairMode.Normal != null ? LC.CrosshairMode.Normal : 0;
      try {
        chart = LC.createChart(chartEl, {
          layout: { background: { color: "#14101c" }, textColor: "#c4bdd8" },
          grid: {
            vertLines: { color: "rgba(255,255,255,0.08)" },
            horzLines: { color: "rgba(255,255,255,0.08)" },
          },
          crosshair: { mode: crossMode },
          localization: {
            locale:
              typeof navigator !== "undefined" && navigator.language
                ? navigator.language
                : "es-AR",
            timeFormatter: formatChartAxisTime,
            dateFormatter: function (time) {
              var ts =
                typeof time === "number"
                  ? time
                  : time && time.year != null
                    ? Math.floor(
                        Date.UTC(time.year, time.month - 1, time.day) / 1000
                      )
                    : null;
              if (ts == null) return "";
              var d = new Date(ts * 1000);
              return (
                String(d.getUTCDate()).padStart(2, "0") +
                "/" +
                String(d.getUTCMonth() + 1).padStart(2, "0")
              );
            },
          },
          rightPriceScale: {
            borderColor: "rgba(255,255,255,0.15)",
            scaleMargins: { top: 0.08, bottom: 0.08 },
            autoScale: true,
          },
          timeScale: {
            borderColor: "rgba(255,255,255,0.15)",
            timeVisible: true,
            secondsVisible: false,
            rightOffset: 4,
          },
          width: size.w,
          height: height,
        });
        series = addCandleSeries(chart);
        if (!series) {
          destroyLc();
          return false;
        }
        mode = "lc";
        if (typeof ResizeObserver !== "undefined") {
          ro = new ResizeObserver(function () {
            if (!chart || !wrap) return;
            var s = measureWrap(wrap, height);
            chart.applyOptions({ width: s.w, height: height });
          });
          ro.observe(wrap);
        }
        if (lastBars.length) {
          renderSeriesData();
          clearMessage(wrap);
        }
        return true;
      } catch (e) {
        destroyLc();
        return false;
      }
    }

    function ensureLcThenRender() {
      if (destroyed || !wrap) return;
      if (lastBars.length && mode !== "lc") {
        drawCanvasChart(wrap, lastBars, height);
        mode = "canvas";
      }
      waitForLc(function (ok) {
        if (destroyed || !wrap) return;
        if (ok && lastBars.length && buildLc()) return;
      });
    }

    waitForLc(function (ok) {
      if (!lastBars.length) showMessage(wrap, ok ? "Esperando velas…" : "Cargando gráficos…");
    });

    function loadKlines(payload) {
      if (destroyed || !wrap) return;
      if (!payload || !payload.bars || !payload.bars.length) {
        if (!lastBars.length) showMessage(wrap, "Sin velas — revisá símbolo y mercado");
        return;
      }
      var nextSymbol = payload.symbol ? String(payload.symbol).toUpperCase() : null;
      if (nextSymbol && chartSymbol && nextSymbol !== chartSymbol) {
        resetSeriesData();
      }
      if (nextSymbol) chartSymbol = nextSymbol;
      if (payload.interval) syncInterval(payload.interval);
      if (payload.server_now != null) serverNowSec = Number(payload.server_now);
      lastBars = normalizeBars(payload.bars, intervalSec, serverNowSec);
      if (!lastBars.length) {
        showMessage(wrap, "Velas inválidas o fuera de rango");
        return;
      }
      clearMessage(wrap);
      if (mode === "lc" && series && chart) {
        renderSeriesData();
        return;
      }
      ensureLcThenRender();
    }

    function updateMarket(mkt) {
      if (!lastBars.length || !mkt) return;
      var px =
        mkt.last != null && mkt.last !== ""
          ? Number(mkt.last)
          : mkt.bid != null && mkt.ask != null
            ? (Number(mkt.bid) + Number(mkt.ask)) / 2
            : null;
      if (!isFinite(px)) return;

      var now = nowSec(serverNowSec);
      var formingOpen = barOpenTime(now, intervalSec);
      lastBars = clipBarsToNow(lastBars, intervalSec, serverNowSec);
      if (!lastBars.length) return;

      var refPx = lastBars[lastBars.length - 1].close;
      if (!priceInRange(px, refPx)) return;

      var last = lastBars[lastBars.length - 1];
      var updated;
      if (!last || last.time < formingOpen) {
        updated = { time: formingOpen, open: px, high: px, low: px, close: px };
        if (last && last.time === formingOpen) {
          lastBars[lastBars.length - 1] = updated;
        } else {
          lastBars.push(updated);
        }
      } else if (last.time === formingOpen) {
        updated = {
          time: formingOpen,
          open: last.open,
          high: Math.max(last.high, px),
          low: Math.min(last.low, px),
          close: px,
        };
        lastBars[lastBars.length - 1] = updated;
      } else {
        return;
      }

      if (mode === "lc" && series) {
        series.update(toChartBar(updated));
        refreshMarkers();
      } else if (mode === "canvas") {
        drawCanvasChart(wrap, lastBars, height);
      }
    }

    function setFills(fills) {
      lastFills = fills || [];
      refreshMarkers();
    }

    return {
      ready: true,
      mode: function () {
        return mode;
      },
      hasSeries: function () {
        return mode === "lc" ? !!series : lastBars.length > 0;
      },
      setInterval: syncInterval,
      getSymbol: function () {
        return chartSymbol;
      },
      clear: resetSeriesData,
      loadKlines: loadKlines,
      updateMarket: updateMarket,
      setFills: setFills,
      resize: function () {
        if (destroyed || !wrap) return;
        if (mode === "lc" && chart) {
          var s = measureWrap(wrap, height);
          chart.applyOptions({ width: s.w, height: height });
          applyVisibleWindow();
        } else if (lastBars.length) {
          drawCanvasChart(wrap, lastBars, height);
        } else {
          ensureLcThenRender();
        }
      },
      destroy: function () {
        destroyed = true;
        destroyLc();
      },
    };
  }

  global.SLTChart = {
    create: createSltChart,
    _test: {
      normalizeBars: normalizeBars,
      clipBarsToNow: clipBarsToNow,
      barOpenTime: barOpenTime,
      toLocalChartTime: toLocalChartTime,
      resolveIntervalSec: resolveIntervalSec,
    },
  };
})(typeof window !== "undefined" ? window : globalThis);
