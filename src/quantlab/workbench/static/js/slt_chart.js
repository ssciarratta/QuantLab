/** Gráfico estilo exchange para Corrida en vivo (lightweight-charts v4/v5). */
(function (global) {
  "use strict";

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
      out.push({
        time: t,
        open: Number(b.open),
        high: Number(b.high),
        low: Number(b.low),
        close: Number(b.close),
      });
    }
    return out;
  }

  function addCandleSeries(chart, opts) {
    if (typeof chart.addCandlestickSeries === "function") {
      return chart.addCandlestickSeries(opts);
    }
    var LC = global.LightweightCharts;
    if (LC && typeof chart.addSeries === "function" && LC.CandlestickSeries) {
      return chart.addSeries(LC.CandlestickSeries, opts);
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
      } else if (typeof series._sltMarkers.setMarkers === "function") {
        series._sltMarkers.setMarkers(markers);
      }
    }
  }

  function showChartMessage(wrap, msg) {
    wrap.innerHTML =
      '<div class="slt-chart-placeholder muted">' + String(msg || "Sin datos") + "</div>";
  }

  function createSltChart(opts) {
    opts = opts || {};
    var wrap = opts.container;
    if (!wrap || !global.LightweightCharts) {
      if (wrap) showChartMessage(wrap, "Cargando librería de gráficos…");
      return {
        ready: false,
        loadKlines: function () {
          return Promise.resolve();
        },
        updateMarket: function () {},
        setFills: function () {},
        resize: function () {},
        destroy: function () {},
      };
    }

    var chart = null;
    var series = null;
    var chartEl = null;
    var lastBars = [];
    var ro = null;
    var destroyed = false;
    var height = opts.height || 220;

    function measure() {
      var w = wrap.clientWidth || wrap.offsetWidth || 0;
      if (w < 60 && wrap.parentElement) {
        w = wrap.parentElement.clientWidth || 480;
      }
      return { w: Math.max(120, w), h: height };
    }

    function buildChart() {
      if (destroyed || chart) return;
      var size = measure();
      if (size.w < 60) {
        requestAnimationFrame(buildChart);
        return;
      }
      wrap.innerHTML = "";
      chartEl = document.createElement("div");
      chartEl.className = "slt-chart-canvas";
      chartEl.style.width = "100%";
      chartEl.style.height = height + "px";
      wrap.appendChild(chartEl);

      chart = LightweightCharts.createChart(chartEl, {
        layout: {
          background: { color: "#14101c" },
          textColor: "#c4bdd8",
        },
        grid: {
          vertLines: { color: "rgba(255,255,255,0.06)" },
          horzLines: { color: "rgba(255,255,255,0.06)" },
        },
        crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
        rightPriceScale: { borderColor: "rgba(255,255,255,0.12)" },
        timeScale: { borderColor: "rgba(255,255,255,0.12)", timeVisible: true, secondsVisible: false },
        width: size.w,
        height: height,
      });

      series = addCandleSeries(chart, {
        upColor: "#5dd39e",
        downColor: "#ff7b7b",
        borderUpColor: "#5dd39e",
        borderDownColor: "#ff7b7b",
        wickUpColor: "#5dd39e",
        wickDownColor: "#ff7b7b",
      });

      if (!series) {
        showChartMessage(wrap, "No se pudo crear el gráfico de velas.");
        chart.remove();
        chart = null;
        return;
      }

      if (typeof ResizeObserver !== "undefined") {
        ro = new ResizeObserver(function () {
          if (!chart) return;
          var s = measure();
          chart.applyOptions({ width: s.w });
        });
        ro.observe(wrap);
      }
    }

    buildChart();

    function loadKlines(payload) {
      if (!payload || !payload.bars || !payload.bars.length) {
        if (!chart) buildChart();
        if (!lastBars.length) showChartMessage(wrap, "Sin velas — revisá símbolo y mercado (spot/futures).");
        return;
      }
      if (!chart || !series) buildChart();
      if (!series) return;
      lastBars = normalizeBars(payload.bars);
      if (!lastBars.length) {
        showChartMessage(wrap, "Velas inválidas desde Binance.");
        return;
      }
      if (!chartEl || !wrap.contains(chartEl)) {
        wrap.innerHTML = "";
        chartEl = document.createElement("div");
        chartEl.className = "slt-chart-canvas";
        wrap.appendChild(chartEl);
      }
      series.setData(lastBars);
      chart.timeScale().fitContent();
    }

    function updateMarket(mkt) {
      if (!mkt || !lastBars.length || !series) return;
      var last = lastBars[lastBars.length - 1];
      var px =
        mkt.last != null && mkt.last !== ""
          ? Number(mkt.last)
          : mkt.mid != null
            ? Number(mkt.mid)
            : mkt.bid != null && mkt.ask != null
              ? (Number(mkt.bid) + Number(mkt.ask)) / 2
              : null;
      if (!isFinite(px)) return;
      var nowSec = Math.floor(Date.now() / 1000);
      var t = nowSec >= last.time ? nowSec : last.time;
      var updated = {
        time: t,
        open: last.open,
        high: Math.max(Number(last.high), px),
        low: Math.min(Number(last.low), px),
        close: px,
      };
      if (t === last.time) {
        lastBars[lastBars.length - 1] = updated;
      } else {
        lastBars.push(updated);
      }
      series.update(updated);
    }

    function setFills(fills) {
      if (!series) return;
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

    function destroy() {
      destroyed = true;
      if (ro) ro.disconnect();
      if (chart) chart.remove();
      chart = null;
      series = null;
    }

    return {
      ready: true,
      loadKlines: loadKlines,
      updateMarket: updateMarket,
      setFills: setFills,
      resize: function () {
        if (!chart) {
          buildChart();
          return;
        }
        var s = measure();
        chart.applyOptions({ width: s.w, height: height });
      },
      destroy: destroy,
    };
  }

  global.SLTChart = { create: createSltChart };
})(typeof window !== "undefined" ? window : globalThis);
