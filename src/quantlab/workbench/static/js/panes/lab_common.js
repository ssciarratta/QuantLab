/** Helpers compartidos para paneles lab. */
(function (global) {
  "use strict";

  function preJson(obj) {
    return (
      '<pre class="lab-json mono">' +
      escapeHtml(JSON.stringify(obj, null, 2)) +
      "</pre>"
    );
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function setStatus(el, ok, msg) {
    el.textContent = msg;
    el.className = "mono " + (ok ? "status-ok" : "status-bad");
  }

  function bindRun(root, btnSel, statusSel, outSel, runner) {
    const btn = root.querySelector(btnSel);
    const status = root.querySelector(statusSel);
    const out = root.querySelector(outSel);
    btn.addEventListener("click", function () {
      status.textContent = "ejecutando…";
      status.className = "mono muted";
      runner()
        .then(function (data) {
          setStatus(status, true, "OK");
          out.innerHTML = preJson(data);
        })
        .catch(function (err) {
          setStatus(status, false, err.message || String(err));
          out.innerHTML = "";
        });
    });
  }

  global.QLLabUI = { preJson: preJson, escapeHtml: escapeHtml, setStatus: setStatus, bindRun: bindRun };
})(window);
