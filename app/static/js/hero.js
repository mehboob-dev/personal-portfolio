/* Hero: typewriter cycling roles + a dummy ticker engine on canvas.
   Config comes from window.SITE (set by home.html) — no hard-coded copy. */
(function () {
  "use strict";

  var hero = (window.SITE && window.SITE.hero) || { roles: [] };
  var bench = (window.SITE && window.SITE.benchmark) || {};

  /* ---------- typewriter ---------- */
  function typewriter() {
    var el = document.getElementById("typed");
    if (!el || !hero.roles || !hero.roles.length) return;
    var i = 0, ch = 0, deleting = false;
    (function tick() {
      var text = hero.roles[i];
      el.textContent = text.slice(0, ch);
      if (!deleting) {
        if (ch < text.length) { ch += 1; setTimeout(tick, 60); }
        else { deleting = true; setTimeout(tick, 1600); }
      } else {
        if (ch > 0) { ch -= 1; setTimeout(tick, 30); }
        else { deleting = false; i = (i + 1) % hero.roles.length; setTimeout(tick, 300); }
      }
    })();
  }

  /* ---------- dummy ticker engine ---------- */
  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function drawTicker() {
    var canvas = document.getElementById("ticker");
    if (!canvas) return;
    var dpr = window.devicePixelRatio || 1;
    var W = canvas.clientWidth || 720, H = canvas.clientHeight || 120;
    canvas.width = W * dpr; canvas.height = H * dpr;
    canvas.style.width = W + "px"; canvas.style.height = H + "px";
    var ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);

    var bg = cssVar("--card"), text = cssVar("--muted"),
        up = cssVar("--accent"), down = cssVar("--danger"), border = cssVar("--border");
    ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);

    var symbols = (hero.ticker_symbols && hero.ticker_symbols.length) ? hero.ticker_symbols : ["BTCUSDT", "ETHUSDT"];
    var cols = 5;
    var cw = Math.floor(W / cols);
    var last = {};
    for (var s = 0; s < symbols.length; s++) last[symbols[s]] = 100;

    var start = Date.now();
    function frame() {
      var t = Date.now();
      ctx.clearRect(0, 0, W, H);
      ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
      for (var s = 0; s < Math.min(symbols.length, cols); s++) {
        var sym = symbols[s];
        var x = s * cw + 14;
        var y = 20 + s * 24;
        var px = Math.sin((t / 1400) + s * 1.7) * 2.2 + (Math.sin((t / 500) + s) * 0.6);
        var val = 100 + px;
        var green = val >= last[sym];
        ctx.fillStyle = green ? up : down;
        ctx.font = "600 12px monospace";
        ctx.fillText(sym.padEnd ? sym : sym, x, y - 12);
        ctx.fillStyle = text;
        ctx.font = "500 12px monospace";
        ctx.fillText(val.toFixed(2), x, y);
        ctx.fillStyle = green ? up : down;
        ctx.fillText((green ? "▲ " : "▼ ") + Math.abs(px).toFixed(2) + "%", x, y + 14);
        last[sym] = val;
      }
      // mini sparkline
      ctx.strokeStyle = up; ctx.lineWidth = 1.5;
      ctx.beginPath();
      for (var i = 0; i < W; i++) {
        var yy = H - 18 - (Math.sin(i / 24 + t / 900) * 10 + Math.sin(i / 7) * 3);
        if (i === 0) ctx.moveTo(i, yy); else ctx.lineTo(i, yy);
      }
      ctx.stroke();
      requestAnimationFrame(frame);
    }
    frame();
  }

  function init() {
    typewriter();
    drawTicker();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
