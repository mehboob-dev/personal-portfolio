/* Expo demo — mobile-first 5-screen flow with Lightweight Charts replay. */
(function () {
  "use strict";

  const STEPS = ["benchmark", "architecture", "strategy", "replay", "outro"];
  let current = "benchmark";
  let chart = null;
  let candles = [];
  let replayTimer = null;
  let cursor = 0;
  let replaying = false;

  const steps = document.querySelectorAll(".expo-step");
  const dots = document.querySelectorAll(".dot");
  const logEl = document.getElementById("replay-log");
  const replayBtn = document.getElementById("replay-btn");
  const chartEl = document.getElementById("chart");

  /* ---- navigation ---- */
  function show(stepId) {
    if (!STEPS.includes(stepId)) return;
    current = stepId;
    steps.forEach(function (s) {
      s.classList.toggle("is-active", s.id === "step-" + stepId);
    });
    dots.forEach(function (d) {
      d.classList.toggle("is-active", d.dataset.step === stepId);
    });
    if (stepId === "replay") initReplay();
    window.scrollTo(0, 0);
  }

  document.querySelectorAll("[data-next]").forEach(function (btn) {
    btn.addEventListener("click", function () { show(btn.dataset.next); });
  });
  dots.forEach(function (d) {
    d.addEventListener("click", function () { show(d.dataset.step); });
  });

  /* ---- replay ---- */
  async function initReplay() {
    if (!currentStrategy) {
      logEl.textContent = "Pick a strategy first.";
      return;
    }
    if (chart) {
      logEl.textContent = "Load dataset…";
    }
    try {
      const res = await fetch("/expo/data/" + currentStrategy.dataset);
      const data = await res.json();
      candles = data.candles || [];
      if (!chart) {
        chart = LightweightCharts.createChart(chartEl, {
          width: chartEl.clientWidth,
          height: 260,
          layout: { background: { type: "solid", color: "#151b27" }, textColor: "#8b95a7" },
          grid: { vertLines: { color: "#232b3a" }, horzLines: { color: "#232b3a" } },
          timeScale: { timeVisible: true },
        });
      }
      if (!chart._series) {
        chart._series = chart.addCandlestickSeries({
          upColor: "#2fbf8f", downColor: "#d95c5c",
          borderUpColor: "#2fbf8f", borderDownColor: "#d95c5c",
          wickUpColor: "#2fbf8f", wickDownColor: "#d95c5c",
        });
      }
      cursor = 0;
      chart._series.setData([]);
      logEl.textContent = "Loaded " + candles.length + " candles. Tap ▶ REPLAY.";
    } catch (e) {
      logEl.textContent = "Failed to load dataset: " + e;
    }
  }

  function replay() {
    if (!chart || !candles.length) return;
    if (replaying) { stopReplay(); return; }
    replaying = true;
    replayBtn.textContent = "■ STOP";
    logEl.textContent = "";
    cursor = 0;
    chart._series.setData([]);
    tick();
  }

  function tick() {
    if (!replaying || cursor >= candles.length) { endReplay(); return; }
    const bar = candles[cursor];
    chart._series.update(bar);
    if (bar.event) logEvent(bar.event);
    cursor += 1;
    replayTimer = setTimeout(tick, 60);
  }

  function stopReplay() {
    replaying = false;
    if (replayTimer) clearTimeout(replayTimer);
    replayBtn.textContent = "▶ REPLAY";
  }

  function endReplay() {
    stopReplay();
    logEl.textContent = (logEl.textContent || "") + "\n— REPLAY COMPLETE —\nThe same engine replays history and runs live.";
  }

  function logEvent(text) {
    const span = document.createElement("div");
    span.className = "sig";
    span.textContent = text;
    logEl.appendChild(span);
  }

  replayBtn.addEventListener("click", replay);

  /* ---- strategy selection ---- */
  let currentStrategy = null;
  document.querySelectorAll(".strat-card").forEach(function (card) {
    card.addEventListener("click", function () {
      currentStrategy = { id: card.dataset.strategy, dataset: card.dataset.dataset };
      document.querySelectorAll(".strat-card").forEach(function (c) {
        c.style.borderColor = c === card ? "var(--accent)" : "";
      });
      document.getElementById("replay-title").textContent = "WATCH IT TRADE · " + card.querySelector("h3").textContent.toUpperCase();
      show("replay");
    });
  });
})();
