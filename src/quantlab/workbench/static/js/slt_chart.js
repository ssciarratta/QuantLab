/** Gráfico Corrida en vivo — lightweight-charts (preferido) + canvas con ejes. */
(function (global) {
  "use strict";

  var LC_WAIT_MS = 8000;
  var LC_POLL_MS = 100;

  function parseTs(fill) {
    var raw = fill.ts || fill.timestamp || fill.time;
    if (!raw) return null;
    if (typeof raw === "number") return raw > 1e12 ? Math.floor(raw / 1000) : raw;
    var d = new Date(raw);
    if (isNaN(d.getTime())) return null;
    return Math.floor(d.getTime() / 1000);
  }

  function normalizeBars(bars) {
    if (!bars || !bars.length) return [];
    var out = [];
    var lastT = -1;
    for (var i = 0; i < bars.length; i++) {
      var b = bars[i];
      var t = b.time;
      if (typeof t === "string") t = Math.floor(new Date(t).getTime() / 1000);
      if (typeof t !== "number" || !isFinite(t)) continue;
      if (t > 1e12) t = Math.floor(t / 1000);
      if (t <= lastT) t = lastT + 1;
      lastT = t;
      var o = Number(b.open);
      var h = Number(b.high);
      var l = Number(b.low);
      var c = Number(b.close);
      if (!isFinite(o) || !isFinite(h) || !isFinite(l) || !isFinite(c)) continue;
      out.push({ time: t, open: o, high: h, low: l, close: c });
    }
    return out;
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

  function fmtTime(ts) {
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
      ctx.fillText(fmtTime(bars[ti].time), tx, size.h - 6);
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
    var lastBars = [];
    var mode = "none";
    var chart = null;
    var series = null;
    var chartEl = null;
    var ro = null;
    var destroyed = false;
    var lcReady = false;

    if (!wrap) {
      return {
        ready: false,
        mode: function () {
          return "none";
        },
        hasSeries: function () {
          return false;
        },
        loadKlines: function () {},
        updateMarket: function () {},
        setFills: function () {},
        resize: function () {},
        destroy: function () {},
      };
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
          rightPriceScale: {
            borderColor: "rgba(255,255,255,0.15)",
            scaleMargins: { top: 0.08, bottom: 0.08 },
          },
          timeScale: {
            borderColor: "rgba(255,255,255,0.15)",
            timeVisible: true,
            secondsVisible: false,
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
        lcReady = true;
        if (typeof ResizeObserver !== "undefined") {
          ro = new ResizeObserver(function () {
            if (!chart || !wrap) return;
            var s = measureWrap(wrap, height);
            chart.applyOptions({ width: s.w, height: height });
          });
          ro.observe(wrap);
        }
        if (lastBars.length) {
          series.setData(lastBars);
          chart.timeScale().fitContent();
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
        lcReady = ok;
        if (ok && lastBars.length && buildLc()) return;
      });
    }

    waitForLc(function (ok) {
      lcReady = ok;
      if (!lastBars.length) showMessage(wrap, ok ? "Esperando velas…" : "Cargando gráficos…");
    });

    function loadKlines(payload) {
      if (destroyed || !wrap) return;
      if (!payload || !payload.bars || !payload.bars.length) {
        if (!lastBars.length) showMessage(wrap, "Sin velas — revisá símbolo y mercado");
        return;
      }
      lastBars = normalizeBars(payload.bars);
      if (!lastBars.length) {
        showMessage(wrap, "Velas inválidas");
        return;
      }
      clearMessage(wrap);
      if (mode === "lc" && series && chart) {
        series.setData(lastBars);
        chart.timeScale().fitContent();
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
      var last = lastBars[lastBars.length - 1];
      var nowSec = Math.floor(Date.now() / 1000);
      var t = nowSec >= last.time ? nowSec : last.time;
      var updated = {
        time: t,
        open: last.open,
        high: Math.max(last.high, px),
        low: Math.min(last.low, px),
        close: px,
      };
      if (t === last.time) lastBars[lastBars.length - 1] = updated;
      else lastBars.push(updated);
      if (mode === "lc" && series) {
        series.update(updated);
      } else if (mode === "canvas") {
        drawCanvasChart(wrap, lastBars, height);
      }
    }

    function setFills(fills) {
      if (mode !== "lc" || !series) return;
      if (!fills || !fills.length) {
        applyMarkers(series, []);
        return;
      }
      var markers = fills
        .map(function (f) {
          var t = parseTs(f);
          if (!t) return null;
          var side = String(f.side || "").toUpperCase();
          var isBuy = side === "BUY" || side === "B";
          return {
            time: t,
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
      applyMarkers(series, markers);
    }

    return {
      ready: true,
      mode: function () {
        return mode;
      },
      hasSeries: function () {
        return mode === "lc" ? !!series : lastBars.length > 0;
      },
      loadKlines: loadKlines,
      updateMarket: updateMarket,
      setFills: setFills,
      resize: function () {
        if (destroyed || !wrap) return;
        if (mode === "lc" && chart) {
          var s = measureWrap(wrap, height);
          chart.applyOptions({ width: s.w, height: height });
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

  global.SLTChart = { create: createSltChart };
})(typeof window !== "undefined" ? window : globalThis);
