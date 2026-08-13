/* Multi-theme engine supporting 4 curated engineering themes:
   - systems-light (Default)
   - monochrome
   - quant-dark
   - warm-monograph
   Applies attribute data-theme on <html> before paint to avoid FOUC. */
(function () {
  "use strict";
  var STORAGE_KEY = "portfolio_theme";
  var LEGACY_KEY = "theme";
  var THEMES = ["only-light", "systems-light", "monochrome", "quant-dark", "warm-monograph"];
  var DEFAULT_THEME = "only-light";

  function normalize(t) {
    if (!t) return DEFAULT_THEME;
    if (t === "dark") return "quant-dark";
    if (t === "light") return "only-light";
    return THEMES.indexOf(t) !== -1 ? t : DEFAULT_THEME;
  }

  function current() {
    var saved = null;
    try {
      saved = localStorage.getItem(STORAGE_KEY) || localStorage.getItem(LEGACY_KEY);
    } catch (e) { /* private mode */ }
    return normalize(saved);
  }

  function apply(theme) {
    var valid = normalize(theme);
    document.documentElement.setAttribute("data-theme", valid);
  }

  function set(theme) {
    var valid = normalize(theme);
    apply(valid);
    try {
      localStorage.setItem(STORAGE_KEY, valid);
      localStorage.setItem(LEGACY_KEY, valid === "quant-dark" ? "dark" : "light");
    } catch (e) { /* ignore */ }
    try {
      window.dispatchEvent(new CustomEvent("themechange", { detail: { theme: valid } }));
    } catch (e) { /* ignore */ }
  }

  // Pre-paint application
  apply(current());

  function init() {
    var curr = current();
    apply(curr);

    // Support select dropdown if present
    var select = document.getElementById("theme-select");
    if (select) {
      select.value = curr;
      select.addEventListener("change", function (e) {
        set(e.target.value);
      });
    }

    // Support theme swatches if present
    var swatches = document.querySelectorAll(".theme-swatch");
    if (swatches.length > 0) {
      var updateSwatches = function (activeTheme) {
        swatches.forEach(function (swatch) {
          if (swatch.getAttribute("data-theme-val") === activeTheme) {
            swatch.classList.add("is-active");
          } else {
            swatch.classList.remove("is-active");
          }
        });
      };
      
      swatches.forEach(function (swatch) {
        swatch.addEventListener("click", function () {
          var val = swatch.getAttribute("data-theme-val");
          set(val);
          updateSwatches(val);
        });
      });
      
      updateSwatches(curr);
      
      window.addEventListener("themechange", function (e) {
        updateSwatches(e.detail.theme);
      });
    }

    // Support toggle button if present (cycles or toggles)
    var btn = document.getElementById("theme-toggle");
    if (btn) {
      var refreshBtn = function () {
        var active = current();
        if (select) select.value = active;
        btn.setAttribute("data-active-theme", active);
        if (active === "quant-dark") {
          btn.innerHTML = '<span class="theme-icon">☀</span> <span class="theme-label">Light</span>';
        } else {
          btn.innerHTML = '<span class="theme-icon">🌙</span> <span class="theme-label">Dark</span>';
        }
      };

      btn.addEventListener("click", function () {
        var active = current();
        var next = active === "quant-dark" ? "systems-light" : "quant-dark";
        set(next);
        refreshBtn();
      });

      refreshBtn();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Expose global helper for theme switcher UI
  window.setPortfolioTheme = set;
  window.getPortfolioTheme = current;
})();
