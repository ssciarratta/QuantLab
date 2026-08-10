/** Panel Help / Docs — browser markdown local (F38). */
(function (global) {
  "use strict";

  function createDocsPane() {
    const root = document.createElement("div");
    root.className = "pane-docs";

    root.innerHTML =
      '<div class="pane-section">' +
      '<div class="pane-head"><h3>Help / Docs</h3>' +
      '<p class="muted pane-sub">Markdown local · solo lectura</p></div>' +
      '<div class="pane-actions">' +
      '<input type="search" id="docs-q" class="docs-search" placeholder="Buscar título / path…" autocomplete="off" style="flex:1;min-width:8rem" />' +
      '<button type="button" class="btn secondary" id="docs-refresh">Actualizar</button>' +
      '<span class="mono muted" id="docs-count">—</span>' +
      "</div>" +
      "</div>" +
      '<div class="pane-section">' +
      '<div id="docs-list"></div>' +
      "</div>" +
      '<div class="pane-section">' +
      '<div class="pane-actions">' +
      '<span class="mono" id="docs-sel">sin selección</span>' +
      '<button type="button" class="btn secondary" id="docs-mode-html" disabled>HTML</button>' +
      '<button type="button" class="btn secondary" id="docs-mode-pre" disabled>Texto</button>' +
      "</div>" +
      '<div id="docs-preview" class="docs-preview"></div>' +
      "</div>";

    const listEl = root.querySelector("#docs-list");
    const countEl = root.querySelector("#docs-count");
    const previewEl = root.querySelector("#docs-preview");
    const selEl = root.querySelector("#docs-sel");
    const qEl = root.querySelector("#docs-q");
    const btnHtml = root.querySelector("#docs-mode-html");
    const btnPre = root.querySelector("#docs-mode-pre");

    let allDocs = [];
    let selectedPath = null;
    let selectedPayload = null;
    let viewMode = "html";

    function renderPreview() {
      if (!selectedPayload) {
        previewEl.innerHTML = '<p class="muted mono">seleccioná un doc</p>';
        return;
      }
      if (viewMode === "html" && selectedPayload.html) {
        previewEl.innerHTML =
          '<div class="docs-html">' + selectedPayload.html + "</div>";
        return;
      }
      const text = selectedPayload.content || "";
      previewEl.innerHTML =
        '<pre class="docs-pre mono">' + QLLabUI.escapeHtml(text) + "</pre>";
    }

    function setSelection(path) {
      selectedPath = path;
      selEl.textContent = path ? path : "sin selección";
      btnHtml.disabled = !path;
      btnPre.disabled = !path;
    }

    async function loadDoc(path) {
      const data = await QLApi.docsContent(path);
      selectedPayload = data;
      setSelection(path);
      viewMode = data.html ? "html" : "pre";
      renderPreview();
      renderList();
    }

    function filteredDocs() {
      const q = String(qEl.value || "")
        .trim()
        .toLowerCase();
      if (!q) return allDocs;
      return allDocs.filter(function (d) {
        const hay =
          (d.path || "") +
          " " +
          (d.name || "") +
          " " +
          (d.title || "") +
          " " +
          (d.subdir || "");
        return hay.toLowerCase().indexOf(q) >= 0;
      });
    }

    function renderList() {
      const rows = filteredDocs();
      countEl.textContent = rows.length + " / " + allDocs.length + " docs";
      if (!rows.length) {
        listEl.innerHTML = '<p class="muted mono">sin coincidencias</p>';
        return;
      }
      const html = rows
        .map(function (d) {
          const active = d.path === selectedPath ? " active" : "";
          const badge = d.subdir ? '<span class="docs-badge">' + QLLabUI.escapeHtml(d.subdir) + "</span>" : "";
          return (
            '<button type="button" class="docs-row' +
            active +
            '" data-path="' +
            QLLabUI.escapeHtml(d.path) +
            '">' +
            '<span class="docs-row-title">' +
            QLLabUI.escapeHtml(d.title || d.name) +
            badge +
            "</span>" +
            '<span class="muted mono">' +
            QLLabUI.escapeHtml(d.path) +
            "</span>" +
            "</button>"
          );
        })
        .join("");
      listEl.innerHTML = '<div class="docs-list">' + html + "</div>";
      listEl.querySelectorAll("[data-path]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          const path = btn.getAttribute("data-path");
          loadDoc(path).catch(function (err) {
            previewEl.innerHTML =
              '<p class="status-bad mono">' +
              QLLabUI.escapeHtml(err.message || String(err)) +
              "</p>";
          });
        });
      });
    }

    async function refresh() {
      const data = await QLApi.docsList();
      allDocs = data.docs || [];
      renderList();
    }

    root.querySelector("#docs-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        listEl.innerHTML =
          '<p class="status-bad mono">' +
          QLLabUI.escapeHtml(err.message || String(err)) +
          "</p>";
      });
    });

    qEl.addEventListener("input", function () {
      renderList();
    });

    btnHtml.addEventListener("click", function () {
      viewMode = "html";
      renderPreview();
    });
    btnPre.addEventListener("click", function () {
      viewMode = "pre";
      renderPreview();
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createDocsPane = createDocsPane;
})(window);
