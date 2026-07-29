/** Panel Validation — Walk-Forward / train-val-OOS runner + anti-leakage (F32). */
(function (global) {
  "use strict";

  function createValidationPane() {
    const root = document.createElement("div");
    root.className = "pane-lab pane-validation";
    root.innerHTML =
      '<div class="pane-section">' +
      '<div class="pane-head"><h3>Validation</h3>' +
      '<p class="muted pane-sub">Walk-forward · anti-leakage</p></div>' +
      '<div class="pane-toolbar">' +
      '<label>n_bars <input type="number" id="vl-bars" class="mono" min="20" max="200" value="40"></label>' +
      '<label>train <input type="number" id="vl-train" class="mono" min="2" max="100" value="10"></label>' +
      '<label>test <input type="number" id="vl-test" class="mono" min="1" max="50" value="5"></label>' +
      "</div>" +
      '<div class="pane-actions">' +
      '<button type="button" class="btn" id="vl-run">Correr splits</button>' +
      '<button type="button" class="btn secondary" id="vl-refresh">Actualizar</button>' +
      '<span class="mono" id="vl-status">—</span>' +
      "</div>" +
      '<p class="muted mono" id="vl-meta">—</p>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Anti-leakage</h3>" +
      '<p class="mono" id="vl-leak">—</p>' +
      '<div id="vl-leak-list"></div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Train / Val / OOS</h3>" +
      '<div id="vl-tvo"></div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Walk-forward folds</h3>" +
      '<div id="vl-folds"></div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Historial sesión</h3>" +
      '<div id="vl-runs"></div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Raw</h3>" +
      '<div id="vl-out"></div>' +
      "</div>";

    const status = root.querySelector("#vl-status");
    const meta = root.querySelector("#vl-meta");
    const leakEl = root.querySelector("#vl-leak");
    const leakList = root.querySelector("#vl-leak-list");
    const tvoEl = root.querySelector("#vl-tvo");
    const foldsEl = root.querySelector("#vl-folds");
    const runsEl = root.querySelector("#vl-runs");
    const out = root.querySelector("#vl-out");

    function esc(s) {
      return QLLabUI.escapeHtml(s);
    }

    function segCell(seg) {
      if (!seg || seg.start_idx == null) return "—";
      return (
        "[" +
        seg.start_idx +
        "…" +
        seg.end_idx +
        "] · n=" +
        seg.count
      );
    }

    function renderResult(data) {
      const anti = data.anti_leakage || {};
      const ok = anti.ok !== false && data.ok !== false;
      QLLabUI.setStatus(
        status,
        ok,
        ok ? "OK · leak " + (anti.n_checks || 0) + " checks" : "LEAK"
      );
      meta.textContent =
        (data.source || "synthetic") +
        " · n_bars=" +
        (data.n_bars != null ? data.n_bars : "?") +
        (data.run_id ? " · " + data.run_id : "") +
        (data.persisted ? " · persisted" : " · preview") +
        (data.path ? " · " + data.path : "");

      leakEl.textContent =
        (anti.ok ? "PASS" : "FAIL") +
        " · checks=" +
        (anti.n_checks != null ? anti.n_checks : "?") +
        " · failed=" +
        (anti.n_failed != null ? anti.n_failed : "?");
      leakEl.className = "mono " + (anti.ok ? "status-ok" : "status-bad");

      const checks = anti.checks || [];
      if (checks.length) {
        leakList.innerHTML =
          '<table class="data-table validation-table"><thead><tr>' +
          "<th>pair</th><th>ok</th><th>issues</th>" +
          "</tr></thead><tbody>" +
          checks
            .map(function (c) {
              return (
                "<tr>" +
                '<td class="mono">' +
                esc(c.pair) +
                "</td>" +
                '<td class="mono">' +
                (c.ok ? "✓" : "✗") +
                "</td>" +
                '<td class="mono">' +
                esc((c.issues || []).join("; ") || "—") +
                "</td>" +
                "</tr>"
              );
            })
            .join("") +
          "</tbody></table>";
      } else {
        leakList.innerHTML = "";
      }

      const tvo = data.train_val_oos || {};
      const segs = tvo.segments || {};
      tvoEl.innerHTML =
        '<table class="data-table validation-table"><thead><tr>' +
        "<th>segment</th><th>count</th><th>indices</th>" +
        "</tr></thead><tbody>" +
        ["train", "validation", "oos"]
          .map(function (name) {
            const seg = segs[name] || {};
            const count =
              seg.count != null
                ? seg.count
                : tvo[name] != null
                  ? tvo[name]
                  : "—";
            return (
              "<tr>" +
              "<td>" +
              name +
              "</td>" +
              '<td class="num">' +
              esc(count) +
              "</td>" +
              '<td class="mono">' +
              esc(segCell(seg)) +
              "</td>" +
              "</tr>"
            );
          })
          .join("") +
        "</tbody></table>";

      const folds = (data.walk_forward && data.walk_forward.folds) || [];
      if (!folds.length) {
        foldsEl.innerHTML = '<p class="muted mono">sin folds</p>';
      } else {
        foldsEl.innerHTML =
          '<table class="data-table validation-table"><thead><tr>' +
          "<th>fold</th><th>train</th><th>test</th><th>train idx</th><th>test idx</th>" +
          "</tr></thead><tbody>" +
          folds
            .map(function (f) {
              return (
                "<tr>" +
                '<td class="num">' +
                esc(f.fold) +
                "</td>" +
                '<td class="num">' +
                esc(f.train) +
                "</td>" +
                '<td class="num">' +
                esc(f.test) +
                "</td>" +
                '<td class="mono">' +
                esc(segCell(f.train_idx)) +
                "</td>" +
                '<td class="mono">' +
                esc(segCell(f.test_idx)) +
                "</td>" +
                "</tr>"
              );
            })
            .join("") +
          "</tbody></table>";
      }

      out.innerHTML = QLLabUI.preJson(data);
    }

    function renderRuns(listPayload) {
      const runs = (listPayload && listPayload.runs) || [];
      if (!runs.length) {
        runsEl.innerHTML =
          '<p class="muted mono">sin corridas — corré splits</p>';
        return;
      }
      runsEl.innerHTML =
        '<table class="data-table validation-table"><thead><tr>' +
        "<th>run_id</th><th>n_bars</th><th>folds</th><th>leak</th>" +
        "</tr></thead><tbody>" +
        runs
          .map(function (r) {
            return (
              "<tr>" +
              '<td class="mono">' +
              esc(r.run_id) +
              "</td>" +
              '<td class="num">' +
              esc(r.n_bars != null ? r.n_bars : "—") +
              "</td>" +
              '<td class="num">' +
              esc(r.n_folds != null ? r.n_folds : "—") +
              "</td>" +
              '<td class="mono">' +
              (r.anti_leakage_ok === false ? "FAIL" : "PASS") +
              "</td>" +
              "</tr>"
            );
          })
          .join("") +
        "</tbody></table>";
    }

    async function refresh() {
      const data = await QLApi.labValidation();
      const source = data.latest || data.preview || data;
      renderResult(source);
      renderRuns(data);
      if (!status.textContent || status.textContent === "—") {
        QLLabUI.setStatus(status, true, "list " + (data.count || 0));
      }
    }

    root.querySelector("#vl-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        QLLabUI.setStatus(status, false, err.message);
      });
    });

    QLLabUI.bindRun(root, "#vl-run", "#vl-status", "#vl-out", function () {
      const nBars = parseInt(root.querySelector("#vl-bars").value, 10) || 40;
      const trainSize = parseInt(root.querySelector("#vl-train").value, 10) || 10;
      const testSize = parseInt(root.querySelector("#vl-test").value, 10) || 5;
      return QLApi.labValidationRun({
        n_bars: nBars,
        train_size: trainSize,
        test_size: testSize,
        step: testSize,
      }).then(function (data) {
        renderResult(data);
        refresh().catch(function () {});
        return data;
      });
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createValidationPane = createValidationPane;
})(window);
