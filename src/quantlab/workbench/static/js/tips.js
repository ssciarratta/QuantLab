/** Tooltips flotantes 1–2 líneas vía data-tip (no se recortan en menús con overflow). */
(function () {
  "use strict";

  var tipEl = null;
  var active = null;
  var hideTimer = null;

  function ensure() {
    if (!tipEl) {
      tipEl = document.createElement("div");
      tipEl.className = "ql-float-tip";
      tipEl.setAttribute("role", "tooltip");
      tipEl.hidden = true;
      document.body.appendChild(tipEl);
    }
    return tipEl;
  }

  function hide() {
    if (!tipEl) return;
    tipEl.hidden = true;
    tipEl.textContent = "";
    active = null;
  }

  function place(target, tip) {
    var r = target.getBoundingClientRect();
    var tw = tip.offsetWidth;
    var th = tip.offsetHeight;
    var x = r.left + r.width / 2 - tw / 2;
    var y = r.top - th - 8;
    if (y < 8) {
      y = r.bottom + 8;
    }
    if (x < 8) {
      x = 8;
    }
    if (x + tw > window.innerWidth - 8) {
      x = window.innerWidth - tw - 8;
    }
    tip.style.left = Math.round(x) + "px";
    tip.style.top = Math.round(y) + "px";
  }

  function show(target) {
    var text = (target.getAttribute("data-tip") || "").trim();
    if (!text) return;
    var tip = ensure();
    tip.textContent = text;
    tip.hidden = false;
    active = target;
    place(target, tip);
    requestAnimationFrame(function () {
      if (active === target) place(target, tip);
    });
  }

  document.addEventListener(
    "mouseover",
    function (ev) {
      var t = ev.target.closest && ev.target.closest("[data-tip]");
      if (!t) return;
      if (t === active) return;
      clearTimeout(hideTimer);
      show(t);
    },
    true
  );

  document.addEventListener(
    "mouseout",
    function (ev) {
      var t = ev.target.closest && ev.target.closest("[data-tip]");
      if (!t || t !== active) return;
      var rel = ev.relatedTarget;
      if (rel && rel.closest && rel.closest("[data-tip]") === t) return;
      hideTimer = setTimeout(hide, 60);
    },
    true
  );

  document.addEventListener("focusin", function (ev) {
    var t = ev.target.closest && ev.target.closest("[data-tip]");
    if (t) {
      clearTimeout(hideTimer);
      show(t);
    }
  });

  document.addEventListener("focusout", function () {
    hideTimer = setTimeout(hide, 60);
  });

  document.addEventListener("scroll", hide, true);
  window.addEventListener("blur", hide);
})();
