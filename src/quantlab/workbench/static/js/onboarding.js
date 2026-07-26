/** First-run onboarding wizard (F37) — modal 4 pasos; sin LIVE. */
(function (global) {
  "use strict";

  var TOTAL_STEPS = 4;

  function createOverlay() {
    var existing = document.getElementById("onboarding-wizard");
    if (existing) return existing;
    var overlay = document.createElement("div");
    overlay.id = "onboarding-wizard";
    overlay.className = "onboarding-wizard hidden";
    overlay.setAttribute("hidden", "");
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("aria-label", "Onboarding QuantLab");
    overlay.innerHTML =
      '<div class="onboarding-panel">' +
      '  <header class="onboarding-header">' +
      '    <div class="onboarding-brand">QuantLab</div>' +
      '    <div class="onboarding-meta">' +
      '      <span class="live-badge">LIVE_BLOCKED</span>' +
      '      <span class="onboarding-step-label" id="ob-step-label">Paso 1 / 4</span>' +
      "    </div>" +
      "  </header>" +
      '  <div class="onboarding-progress" aria-hidden="true">' +
      '    <span class="ob-dot active" data-step="1"></span>' +
      '    <span class="ob-dot" data-step="2"></span>' +
      '    <span class="ob-dot" data-step="3"></span>' +
      '    <span class="ob-dot" data-step="4"></span>' +
      "  </div>" +
      '  <div class="onboarding-body" id="ob-body"></div>' +
      '  <footer class="onboarding-footer">' +
      '    <button type="button" class="btn ghost" id="ob-prev" disabled>Anterior</button>' +
      '    <div class="onboarding-actions">' +
      '      <button type="button" class="btn ghost" id="ob-skip">Omitir</button>' +
      '      <button type="button" class="btn primary" id="ob-next">Siguiente</button>' +
      "    </div>" +
      "  </footer>" +
      "</div>";
    document.body.appendChild(overlay);
    return overlay;
  }

  function stepHtml(step) {
    if (step === 1) {
      return (
        "<h2>Modos operativos</h2>" +
        "<p class=\"ob-lead\">Antes de operar, entendé la diferencia entre modos. " +
        "<strong>LIVE sigue bloqueado</strong>.</p>" +
        '<ul class="ob-modes">' +
        "<li><span class=\"ob-mode-tag\">TESTER</span> Fake / offline — datasets locales, sin órdenes venue.</li>" +
        "<li><span class=\"ob-mode-tag\">REAL</span> Alias de <em>PAPER</em>: MD/cuenta reales + fills simulados. " +
        "<strong>REAL ≠ LIVE</strong>.</li>" +
        "<li><span class=\"ob-mode-tag live\">LIVE</span> Órdenes al venue — " +
        "<span class=\"live-badge\">BLOQUEADO</span> (LIVE_BLOCKED=True).</li>" +
        "</ul>"
      );
    }
    if (step === 2) {
      return (
        "<h2>Conectar venue tester</h2>" +
        "<p class=\"ob-lead\">Abrí Market Data y conectá un venue en modo TESTER " +
        "(p.ej. paper o a3 fake). Sin envío de órdenes reales.</p>" +
        '<div class="ob-cta-row">' +
        '<button type="button" class="btn primary" data-ob-action="open-market">' +
        "Abrir Market Data</button>" +
        "</div>" +
        '<p class="muted ob-hint">Podés completar este paso luego; el wizard solo orienta.</p>'
      );
    }
    if (step === 3) {
      return (
        "<h2>Sesión Paper / Backtest</h2>" +
        "<p class=\"ob-lead\">Para research-safe: iniciá una Sesión Paper o corré un Backtest. " +
        "Ambos usan PaperBroker — nunca place_order venue.</p>" +
        '<div class="ob-cta-row">' +
        '<button type="button" class="btn primary" data-ob-action="open-paper">' +
        "Sesión Paper</button>" +
        '<button type="button" class="btn ghost" data-ob-action="open-backtest">' +
        "Backtest</button>" +
        "</div>"
      );
    }
    return (
      "<h2>Chat IA safe</h2>" +
      "<p class=\"ob-lead\">El asistente es research-safe: allowlist de lectura/explicación. " +
      "No envía órdenes, no hace flip LIVE.</p>" +
      '<div class="ob-cta-row">' +
      '<button type="button" class="btn primary" data-ob-action="open-chat">' +
      "Abrir Chat IA</button>" +
      "</div>" +
      '<p class="muted ob-hint">Al completar, no volveremos a mostrar este wizard en esta sesión.</p>'
    );
  }

  function OnboardingWizard(openers) {
    this._openers = openers || {};
    this._step = 1;
    this._el = createOverlay();
    this._body = this._el.querySelector("#ob-body");
    this._label = this._el.querySelector("#ob-step-label");
    this._prev = this._el.querySelector("#ob-prev");
    this._next = this._el.querySelector("#ob-next");
    this._skip = this._el.querySelector("#ob-skip");
    var self = this;
    this._prev.addEventListener("click", function () {
      self.go(self._step - 1);
    });
    this._next.addEventListener("click", function () {
      if (self._step >= TOTAL_STEPS) {
        self.complete();
      } else {
        self.go(self._step + 1);
      }
    });
    this._skip.addEventListener("click", function () {
      self.complete();
    });
    this._body.addEventListener("click", function (ev) {
      var t = ev.target;
      if (!t || !t.getAttribute) return;
      var action = t.getAttribute("data-ob-action");
      if (!action) return;
      var fn = self._openers[action];
      if (typeof fn === "function") fn();
    });
  }

  OnboardingWizard.prototype.go = function (step) {
    var n = Math.max(1, Math.min(TOTAL_STEPS, step | 0));
    this._step = n;
    this._body.innerHTML = stepHtml(n);
    this._label.textContent = "Paso " + n + " / " + TOTAL_STEPS;
    this._prev.disabled = n <= 1;
    this._next.textContent = n >= TOTAL_STEPS ? "Completar" : "Siguiente";
    var dots = this._el.querySelectorAll(".ob-dot");
    for (var i = 0; i < dots.length; i++) {
      var d = dots[i];
      if (Number(d.getAttribute("data-step")) <= n) {
        d.classList.add("active");
      } else {
        d.classList.remove("active");
      }
    }
  };

  OnboardingWizard.prototype.show = function () {
    this.go(1);
    this._el.classList.remove("hidden");
    this._el.removeAttribute("hidden");
    this._el.classList.add("ob-visible");
  };

  OnboardingWizard.prototype.hide = function () {
    this._el.classList.add("hidden");
    this._el.setAttribute("hidden", "");
    this._el.classList.remove("ob-visible");
  };

  OnboardingWizard.prototype.complete = function () {
    var self = this;
    var done = function () {
      self.hide();
    };
    if (global.QLApi && typeof global.QLApi.completeOnboarding === "function") {
      global.QLApi.completeOnboarding({})
        .then(done)
        .catch(function () {
          // Fail-soft UI: ocultar igual; el flag se puede reintentar en próximo boot.
          done();
        });
    } else {
      done();
    }
  };

  global.QLOnboarding = {
    create: function (openers) {
      return new OnboardingWizard(openers);
    },
  };
})(window);
