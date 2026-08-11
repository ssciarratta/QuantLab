/** Presets de layout cliente — abre ventanas sin tocar backend. */
(function (global) {
  "use strict";

  function apply(presetKey, onOpen) {
    var reg = global.QLPanelRegistry;
    if (!reg || !reg.layoutPresets || !reg.layoutPresets[presetKey]) return;
    var preset = reg.layoutPresets[presetKey];
    (preset.paneIds || []).forEach(function (paneId) {
      if (typeof onOpen === "function") onOpen(paneId);
    });
  }

  function list() {
    var reg = global.QLPanelRegistry;
    if (!reg || !reg.layoutPresets) return [];
    return Object.keys(reg.layoutPresets).map(function (key) {
      var p = reg.layoutPresets[key];
      return { id: key, label: p.label, tip: p.tip };
    });
  }

  global.QLLayoutPresets = {
    apply: apply,
    list: list,
  };
})(typeof window !== "undefined" ? window : globalThis);
