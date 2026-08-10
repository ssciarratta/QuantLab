/** Formato global de fecha/hora — dd/mm - HH:mm:ss (hora local por defecto). */
(function (global) {
  "use strict";

  function pad2(n) {
    return n < 10 ? "0" + n : String(n);
  }

  function toDate(isoOrDate) {
    if (!isoOrDate && isoOrDate !== 0) return null;
    if (isoOrDate instanceof Date) return isoOrDate;
    var d = new Date(isoOrDate);
    return isNaN(d.getTime()) ? null : d;
  }

  /** 10/08 - 16:11:15 */
  function fmtDateTime(isoOrDate, opts) {
    opts = opts || {};
    var d = toDate(isoOrDate);
    if (!d) return isoOrDate == null || isoOrDate === "" ? "—" : String(isoOrDate);
    if (opts.utc) {
      return (
        pad2(d.getUTCDate()) +
        "/" +
        pad2(d.getUTCMonth() + 1) +
        " - " +
        pad2(d.getUTCHours()) +
        ":" +
        pad2(d.getUTCMinutes()) +
        ":" +
        pad2(d.getUTCSeconds()) +
        (opts.suffix || "")
      );
    }
    return (
      pad2(d.getDate()) +
      "/" +
      pad2(d.getMonth() + 1) +
      " - " +
      pad2(d.getHours()) +
      ":" +
      pad2(d.getMinutes()) +
      ":" +
      pad2(d.getSeconds())
    );
  }

  function fmtTime(isoOrDate) {
    var d = toDate(isoOrDate);
    if (!d) return "—";
    return pad2(d.getHours()) + ":" + pad2(d.getMinutes()) + ":" + pad2(d.getSeconds());
  }

  function fmtDate(isoOrDate) {
    var d = toDate(isoOrDate);
    if (!d) return "—";
    return pad2(d.getDate()) + "/" + pad2(d.getMonth() + 1) + "/" + d.getFullYear();
  }

  global.QLFmt = global.QLFmt || {};
  global.QLFmt.fmtDateTime = fmtDateTime;
  global.QLFmt.fmtTime = fmtTime;
  global.QLFmt.fmtDate = fmtDate;
  global.QLFmt.pad2 = pad2;
})(typeof window !== "undefined" ? window : this);
