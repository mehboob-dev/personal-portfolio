/* ==========================================================================
   TABLEKIT — shared Tabulator wrapper (unified across itqan-trades and
   mehboob-portfolio). Keep this file byte-identical in both repos.
   ========================================================================== */
(function () {
  "use strict";

  /* --- Per-table reset registry (unified customFilterResetList) ---------- */
  function createResetRegistry() {
    var list = [];
    return {
      list: list,
      push: function (fn) { list.push(fn); },
      run: function () { list.forEach(function (fn) { fn(); }); }
    };
  }

  /* --- preventHeaderSort: keep click events from also sorting ------------ */
  function preventHeaderSort(el) {
    ["mousedown", "click", "pointerdown", "touchstart"].forEach(function (evt) {
      el.addEventListener(evt, function (e) {
        if (e.target.closest && e.target.closest(".tabulator-col")) e.stopPropagation();
      });
    });
  }

  /* --- Pure filter functions --------------------------------------------- */
  function exactMatchFilter(headerValue, rowValue) {
    if (headerValue === undefined || headerValue === null || headerValue === "") return true;
    return String(rowValue) === String(headerValue);
  }

  function statusMatchFilter(headerValue, rowValue) {
    if (headerValue === undefined || headerValue === null || headerValue === "") return true;
    return rowValue === (headerValue === "In Trash");
  }

  function publishedMatchFilter(headerValue, rowValue) {
    if (headerValue === undefined || headerValue === null || headerValue === "") return true;
    return rowValue === (headerValue === "Published");
  }

  function activeStatusFilter(headerValue, rowValue) {
    if (headerValue === undefined || headerValue === null || headerValue === "") return true;
    if (headerValue === "Active") return rowValue === false || rowValue === "active";
    if (headerValue === "Paused") return rowValue === true || rowValue === "paused";
    return true;
  }

  /* Accepts ISO (YYYY-MM-DD) or DMY (dd/mm/yyyy), with optional time/UTC
     suffix — strips to a date-only string before parsing. */
  function flexParseDate(s) {
    if (!s) return null;
    s = String(s).trim().replace(/\s*UTC\s*$/i, "").split("T")[0].split(" ")[0];
    var m = s.match(/^(\d{4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})$/);
    var d, mo, y;
    if (m) {
      y = +m[1]; mo = +m[2]; d = +m[3];
    } else {
      m = s.match(/^(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})$/);
      if (!m) return null;
      d = +m[1]; mo = +m[2]; y = +m[3];
      if (y < 100) y += 2000;
    }
    var dt = new Date(y, mo - 1, d);
    if (dt.getFullYear() !== y || dt.getMonth() !== mo - 1 || dt.getDate() !== d) return null;
    return dt;
  }

  function dateToStr(dt) {
    return dt.getFullYear() + "-" + ("0" + (dt.getMonth() + 1)).slice(-2) + "-" + ("0" + dt.getDate()).slice(-2);
  }

  /* itqan-records variant: strips commas from the target, treats "—"/empty
     row values as pass-through. */
  function advancedNumericFilterFunc(headerValue, rowValue) {
    if (headerValue === undefined || headerValue === null || headerValue === "") return true;
    if (rowValue === undefined || rowValue === null || rowValue === "" || rowValue === String.fromCharCode(0x2014)) return false;
    var n = parseFloat(String(rowValue).replace(/,/g, "").trim());
    if (isNaN(n)) return false;
    var op = "gte", val = headerValue;
    if (typeof headerValue === "object") { op = headerValue.operator || "gte"; val = headerValue.value; }
    var target = parseFloat(String(val).replace(/,/g, "").trim());
    if (isNaN(target)) return true;
    return op === "gt" ? n > target : op === "gte" ? n >= target : op === "lt" ? n < target : op === "lte" ? n <= target : op === "eq" ? n === target : op === "neq" ? n !== target : true;
  }
  function advancedDateFilterFunc(headerValue, rowValue) {
    if (headerValue === undefined || headerValue === null) return true;
    var op = "on", val = typeof headerValue === "object" ? (headerValue.value || "") : String(headerValue);
    if (typeof headerValue === "object") op = headerValue.operator || "on";
    if (!val) return true;
    var target = flexParseDate(val), row = flexParseDate(rowValue);
    if (!row) return false;
    if (!target) {
      var typed = String(val).trim().toLowerCase(), iso = dateToStr(row), dmy = ("0" + row.getDate()).slice(-2) + "/" + ("0" + (row.getMonth() + 1)).slice(-2) + "/" + row.getFullYear();
      return op === "on" ? iso.indexOf(typed) !== -1 || dmy.indexOf(typed) !== -1 : op === "not_on" ? iso.indexOf(typed) === -1 && dmy.indexOf(typed) === -1 : true;
    }
    return op === "on" ? dateToStr(row) === dateToStr(target) : op === "not_on" ? dateToStr(row) !== dateToStr(target) : op === "after" ? row > target : op === "before" ? row < target : true;
  }
  function customDropdownFilter(values) {
    return function (cell, onRendered, success, cancel, editorParams) {
      var reset = editorParams && editorParams.resetCallbacks;
      var select = document.createElement("select");
      select.style.padding = "4px";
      select.style.background = "var(--bg-canvas)";
      select.style.border = "1px solid var(--border-subtle)";
      select.style.color = "var(--text-primary)";
      select.style.borderRadius = "var(--radius-xs)";
      select.style.fontFamily = "var(--font-mono)";
      select.style.fontSize = "0.75rem";
      select.style.width = "100%";
      select.style.boxSizing = "border-box";
      var allOpt = document.createElement("option");
      allOpt.value = "";
      allOpt.text = "All";
      select.appendChild(allOpt);
      values.forEach(function (val) {
        var opt = document.createElement("option");
        opt.value = val;
        opt.text = val;
        select.appendChild(opt);
      });
      preventHeaderSort(select);
      select.addEventListener("change", function () { success(select.value); });
      onRendered(function () { select.value = cell.getValue() || ""; });
      if (reset) reset.push(function () { select.value = ""; });
      return select;
    };
  }

  function customNumericFilterEditor(cell, onRendered, success, cancel, editorParams) {
    var reset = editorParams && editorParams.resetCallbacks, container = document.createElement("div"), select = document.createElement("select"), input = document.createElement("input"), seq = 0;
    container.className = "custom-header-filter-container";
    [{value:"gte",text:"Greater or equal"},{value:"gt",text:"> (Greater)"},{value:"lte",text:"Less or equal"},{value:"lt",text:"< (Less)"},{value:"eq",text:"= (Equal)"},{value:"neq",text:"Not equal"}].forEach(function(op){var option=document.createElement("option");option.value=op.value;option.text=op.text;select.appendChild(option);});
    input.type="text"; input.placeholder="Value..."; input.style.width="100%"; input.style.boxSizing="border-box"; preventHeaderSort(select); preventHeaderSort(input);
    function emit(){var value=input.value.trim(); if(!value){success(null);return;} success({operator:select.value,value:value,_seq:++seq});}
    select.addEventListener("change",emit); input.addEventListener("input",emit); onRendered(function(){var value=cell.getValue();select.value=value&&typeof value==="object"?(value.operator||"gte"):"gte";input.value=value&&typeof value==="object"?(value.value||""):"";});
    container.appendChild(select);container.appendChild(input);if(reset)reset.push(function(){select.value="gte";input.value="";});return container;
  }
  function customDateFilterEditor(cell, onRendered, success, cancel, editorParams) {
    var reset=editorParams&&editorParams.resetCallbacks,container=document.createElement("div"),select=document.createElement("select"),input=document.createElement("input"),nativeInput=document.createElement("input"),seq=0,inputTimer;
    container.className="custom-header-filter-container";["on","not_on","after","before"].forEach(function(op){var option=document.createElement("option");option.value=op;option.text=op;select.appendChild(option);});
    input.type="text";input.placeholder="dd/mm/yyyy";input.style.width="100%";input.style.boxSizing="border-box";nativeInput.type="date";nativeInput.tabIndex=-1;nativeInput.style.cssText="position:absolute;right:0;top:0;width:1px;height:1px;opacity:0;pointer-events:none;border:none;padding:0;margin:0;";
    function emit(){var value=input.value.trim();if(!value){success(null);return;}success({operator:select.value,value:value,_seq:++seq});}
    select.addEventListener("change",emit);input.addEventListener("input",function(){var digits=input.value.replace(/\D/g, "").slice(0, 8), formatted=digits.length>4?digits.slice(0,2)+"/"+digits.slice(2,4)+"/"+digits.slice(4):digits.length>2?digits.slice(0,2)+"/"+digits.slice(2):digits;if(input.value!==formatted)input.value=formatted;nativeInput.value="";clearTimeout(inputTimer);inputTimer=setTimeout(emit,350);});input.addEventListener("change",function(){clearTimeout(inputTimer);emit();});input.addEventListener("keydown",function(event){event.stopPropagation();if(event.key === "Enter"){event.preventDefault();clearTimeout(inputTimer);emit();input.blur();}});nativeInput.addEventListener("change",function(){if(nativeInput.value){var p=nativeInput.value.split("-");input.value=p[2]+"/"+p[1]+"/"+p[0];clearTimeout(inputTimer);emit();}});preventHeaderSort(select);preventHeaderSort(input);preventHeaderSort(nativeInput);
    var row=document.createElement("div"),icon=document.createElement("span");row.style.position="relative";row.style.width="100%";icon.innerHTML="&#128197;";icon.style.cssText="position:absolute;right:3px;top:50%;transform:translateY(-50%);font-size:0.75rem;cursor:pointer;z-index:3;line-height:1;";icon.addEventListener("click",function(event){event.preventDefault();event.stopPropagation();if(nativeInput.showPicker){nativeInput.showPicker();}else{nativeInput.click();}});row.appendChild(input);row.appendChild(nativeInput);row.appendChild(icon);container.appendChild(select);container.appendChild(row);
    onRendered(function(){var value=cell.getValue();select.value=value&&typeof value==="object"?(value.operator||"on"):"on";input.value=value&&typeof value==="object"?(value.value||""):"";});if(reset)reset.push(function(){select.value="on";input.value="";nativeInput.value="";});return container;
  }

  function customHeaderSelectFormatter(column) {
    var tableInstance = column.getTable();
    var input = document.createElement("input");
    input.type = "checkbox";
    input.ariaLabel = "Select all rows";
    preventHeaderSort(input);

    input.addEventListener("change", function (e) {
      e.stopPropagation();
      var activeRows = tableInstance.getRows("active");
      if (input.checked) {
        tableInstance.selectRow(activeRows);
      } else {
        tableInstance.deselectRow(activeRows);
      }
    });

    tableInstance._headerSelectionCheckbox = input;
    return input;
  }

  function create(container, opts) {
    var el = typeof container === "string" ? document.querySelector(container) : container;
    if (!el) throw new Error("TableKit: container not found: " + container);

    opts = opts || {};

    /* Wrap in the responsive wrapper (idempotent — skip if already wrapped). */
    if (!el.classList.contains("table-responsive-wrapper")) {
      var wrapper = document.createElement("div");
      wrapper.className = "table-responsive-wrapper";
      var inner = document.createElement("div");
      inner.className = opts.tableClass || "table-kit";
      el.parentNode.insertBefore(wrapper, el);
      wrapper.appendChild(inner);
      inner.appendChild(el);
      el = inner;
    }

    var reset = createResetRegistry();
    var columns = (opts.columns || []).slice();

    /* Inject the per-table reset registry into every column's headerFilterParams
       so the shared editors can self-register their reset callbacks. */
    columns.forEach(function (col) {
      col.headerFilterParams = col.headerFilterParams || {};
      col.headerFilterParams.resetCallbacks = reset;
      if (col.headerFilter === customNumericFilterEditor || col.headerFilter === customDateFilterEditor) {
        col.headerFilterLiveFilter = false;
      }
      if (col.titleFormatter === "rowSelection") {
        col.titleFormatter = customHeaderSelectFormatter;
      }
    });

    /* Auto-prepend the shared selection column unless disabled or present. */
    var hasSelection = columns.some(function (c) {
      return c.formatter === "rowSelection" || c.titleFormatter === "rowSelection" || c.titleFormatter === customHeaderSelectFormatter;
    });
    if (opts.selectable !== false && !hasSelection) {
      columns.unshift({
        formatter: "rowSelection",
        titleFormatter: customHeaderSelectFormatter,
        hozAlign: "center",
        headerSort: false,
        width: 60,
        cellClick: function (e, cell) {
          e.stopPropagation();
          cell.getRow().toggleSelect();
        }
      });
    }

    var config = {
      data: opts.data || [],
      columns: columns,
      layout: "fitColumns",
      resizableColumnFit: true,
      pagination: opts.pagination !== undefined ? opts.pagination : "local",
      paginationSize: opts.paginationSize !== undefined ? opts.paginationSize : 20,
      paginationSizeSelector: opts.paginationSizeSelector !== undefined ? opts.paginationSizeSelector : [10, 20, 50, true],
      placeholder: opts.placeholder !== undefined ? opts.placeholder : "No data found.",
      selectableRows: opts.selectable === false ? false : "highlight",
      header: opts.header !== undefined ? opts.header : true
    };
    if (opts.rowClick) config.rowClick = opts.rowClick;

    var table = new Tabulator(el, config);
    table._resetCallbacks = reset;
    table._tablekitOptions = opts;

    function updateHeaderCheckbox() {
      var input = table._headerSelectionCheckbox;
      if (!input) return;
      var activeRows = table.getRows("active");
      if (!activeRows || activeRows.length === 0) {
        input.checked = false;
        input.indeterminate = false;
        return;
      }
      var selectedActive = activeRows.filter(function (r) {
        return r.isSelected();
      });
      if (selectedActive.length === 0) {
        input.checked = false;
        input.indeterminate = false;
      } else if (selectedActive.length === activeRows.length) {
        input.checked = true;
        input.indeterminate = false;
      } else {
        input.checked = false;
        input.indeterminate = true;
      }
    }

    table.on("rowSelectionChanged", updateHeaderCheckbox);
    table.on("dataFiltered", updateHeaderCheckbox);

    if (opts.resetButton) {
      var btn = typeof opts.resetButton === "string" ? document.querySelector(opts.resetButton) : opts.resetButton;
      if (btn) {
        btn.addEventListener("click", function () {
          table.clearHeaderFilter();
          reset.run();
        });
      }
    }

    if (opts.countEl) {
      var countEl = typeof opts.countEl === "string" ? document.querySelector(opts.countEl) : opts.countEl;
      if (countEl) {
        var renderCount = function () {
          var count = table.getDataCount();
          countEl.textContent = "Showing " + count + (opts.countLabel ? " " + opts.countLabel : "");
        };
        table.on("dataFiltered", renderCount);
        renderCount();
      }
    }

    if (opts.initialFilter) {
      table.setHeaderFilterValue(opts.initialFilter.field, opts.initialFilter.value);
    }

    if (opts.onReady) opts.onReady(table);

    updateHeaderCheckbox();
    return table;
  }

  window.TableKit = {
    create: create,
    exactMatchFilter: exactMatchFilter,
    statusMatchFilter: statusMatchFilter,
    publishedMatchFilter: publishedMatchFilter,
    activeStatusFilter: activeStatusFilter,
    advancedNumericFilterFunc: advancedNumericFilterFunc,
    advancedDateFilterFunc: advancedDateFilterFunc,
    customDropdownFilter: customDropdownFilter,
    customNumericFilterEditor: customNumericFilterEditor,
    customDateFilterEditor: customDateFilterEditor
  };
})();
