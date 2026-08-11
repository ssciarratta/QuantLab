/** Gráfico estilo exchange para Corrida en vivo (lightweight-charts). */
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

  function createSltChart(opts) {
    opts = opts || {};
    var wrap = opts.container;
    if (!wrap || !global.LightweightCharts) {
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

    var chartEl = document.createElement("div");
    chartEl.className = "slt-chart-canvas";
    wrap.innerHTML = "";
    wrap.appendChild(chartEl);

    var chart = LightweightCharts.createChart(chartEl, {
      layout: {
        background: { color: "#0b1018" },
        textColor: "#b4c2d4",
      },
      grid: {
        vertLines: { color: "rgba(42,58,79,0.45)" },
        horzLines: { color: "rgba(42,58,79,0.45)" },
      },
      crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
      rightPriceScale: { borderColor: "#2a3a4f" },
      timeScale: { borderColor: "#2a3a4f", timeVisible: true, secondsVisible: true },
      width: wrap.clientWidth || 640,
      height: opts.height || 320,
    });

    var series = chart.addCandlestickSeries({
      upColor: "#3d9b6e",
      downColor: "#d4544a",
      borderUpColor: "#3d9b6e",
      borderDownColor: "#d4544a",
      wickUpColor: "#3d9b6e",
      wickDownColor: "#d4544a",
    });

    var lastBars = [];
    var ro = null;
    if (typeof ResizeObserver !== "undefined") {
      ro = new ResizeObserver(function () {
        chart.applyOptions({ width: wrap.clientWidth || 640 });
      });
      ro.observe(wrap);
    }

    function loadKlines(payload) {
      if (!payload || !payload.bars || !payload.bars.length) return;
      lastBars = payload.bars.slice();
      series.setData(lastBars);
      chart.timeScale().fitContent();
    }

    function updateMarket(mkt) {
      if (!mkt || !lastBars.length) return;
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
      var updated = Object.assign({}, last, {
        close: px,
        high: Math.max(Number(last.high), px),
        low: Math.min(Number(last.low), px),
        time: nowSec >= last.time ? nowSec : last.time,
      });
      if (updated.time === last.time) {
        lastBars[lastBars.length - 1] = updated;
        series.update(updated);
      } else {
        lastBars.push(updated);
        series.update(updated);
      }
    }

    function setFills(fills) {
      if (!fills || !fills.length) {
        series.setMarkers([]);
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
            color: isBuy ? "#3d9b6e" : "#d4544a",
            shape: isBuy ? "arrowUp" : "arrowDown",
            text: (isBuy ? "Compra " : "Venta ") + String(f.price || ""),
          };
        })
        .filter(Boolean)
        .sort(function (a, b) {
          return a.time - b.time;
        });
      series.setMarkers(markers);
    }

    function destroy() {
      if (ro) ro.disconnect();
      chart.remove();
    }

    return {
      ready: true,
      loadKlines: loadKlines,
      updateMarket: updateMarket,
      setFills: setFills,
      resize: function () {
        chart.applyOptions({ width: wrap.clientWidth || 640 });
      },
      destroy: destroy,
    };
  }

  global.SLTChart = { create: createSltChart };
})(typeof window !== "undefined" ? window : globalThis);
