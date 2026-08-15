# TableKit and Advanced Table Filtering

## Purpose

Both applications use the same shared TableKit implementation at `app/static/js/table.js`. It wraps Tabulator and standardizes responsive table setup, row selection, pagination, filter controls, reset behavior, and filtered-record counts. The file is deliberately byte-identical in `itqan-trades` and `mehboob-portfolio`; make shared behavior changes in both copies and compare their hashes before handoff.

This guide records the table refactor and the advanced date/number filtering fixes completed in August 2026. Use it as the maintenance reference for any future Tabulator column or custom header filter.

## Load order

Tabulator must load before TableKit, and TableKit must load before a page initializes a table.

    <script src="https://unpkg.com/tabulator-tables@6.2.1/dist/js/tabulator.min.js"></script>
    <script src="{{ url_for('static', filename='js/table.js') }}"></script>

Create tables after the page DOM is ready:

    var table = TableKit.create("#records-table", {
      data: tableData,
      resetButton: "#reset-tabulator-filters",
      countEl: "#table-record-count",
      columns: [/* Tabulator columns */]
    });

Do not use a direct `new Tabulator(...)` for a new application table without a specific reason to bypass the shared wrapper.

## Factory behavior

`TableKit.create(container, options)` wraps its target in the responsive table structure and creates the Tabulator instance. Defaults include local pagination, a page size of 20, page-size choices of 10/20/50/All, fit-columns layout, resizing, row highlighting/selection, and a standard empty state.

Use `selectable: false` for compact read-only tables. The factory detects a supplied selection column and will not duplicate it. Set `pagination: false` for small summary grids.

### Reset registry

Each column receives a private reset registry through `headerFilterParams.resetCallbacks`. Custom editor controls register callbacks to reset their visible select/input values. A reset button clears both Tabulator state and custom-editor UI:

    table.clearHeaderFilter();
    reset.run();

Do not remove the second call. `clearHeaderFilter()` alone can leave a custom header control showing an old value after the rows have reset.

## Shared helpers

| Helper | Purpose |
| --- | --- |
| `customDropdownFilter(values)` | Dropdown with an All option. |
| `exactMatchFilter` | Exact string matching for dropdowns. |
| `statusMatchFilter` | Maps Active/In Trash to `is_deleted`. |
| `publishedMatchFilter` | Maps Published/Draft to `published`. |
| `activeStatusFilter` | Maps Active/Paused to boolean or string status data. |
| `customNumericFilterEditor` | Numeric operator and value input. |
| `advancedNumericFilterFunc` | Numeric comparison logic. |
| `customDateFilterEditor` | Day-first typed date field and calendar picker. |
| `advancedDateFilterFunc` | Date comparison logic. |

Use advanced editors by reference:

    {
      title: "Amount",
      field: "amount",
      headerFilter: TableKit.customNumericFilterEditor,
      headerFilterFunc: TableKit.advancedNumericFilterFunc
    }

    {
      title: "Created (UTC)",
      field: "created_at",
      headerFilter: TableKit.customDateFilterEditor,
      headerFilterFunc: TableKit.advancedDateFilterFunc,
      width: 180
    }

For a dropdown, call the factory because it requires allowed values:

    headerFilter: TableKit.customDropdownFilter(["Active", "In Trash"])

## Advanced numeric filtering

The numeric editor provides Greater or equal (the default), Greater, Less or equal, Less, Equal, and Not equal. Both the typed target and the row value have comma separators removed before parsing, so `1,250` and `1250` are equivalent. Empty/missing numeric rows do not incorrectly pass an active filter. A non-empty invalid target temporarily leaves rows unfiltered until the value becomes valid.

The editor returns a structured filter value such as:

    { operator: "gte", value: "1250", _seq: 3 }

`_seq` is incremented for each edit so Tabulator sees successive object values as fresh filter changes.

## Advanced date filtering

### Supported formats

The parser accepts ISO dates (`2026-08-01`), ISO date/time values, UTC-suffixed values, and day-first date strings (`01/08/2026`). It also accepts slash, hyphen, and dot separators. Comparisons are date-only; time does not affect results. Invalid calendar dates are rejected rather than rolling into another month.

Operations are on (same calendar day), not_on (different calendar day), after (strictly later), and before (strictly earlier). A complete parsed input compares exactly. Partial day-first text can narrow on/not_on searches while it is being typed; before/after require a complete valid date.

### Typed input contract

The visible date field is plain text. It accepts separators or eight consecutive digits:

    01082026  becomes  01/08/2026

Digit-only input is always interpreted as `DDMMYYYY`, never according to the browser locale. The field applies its filter automatically 350 ms after typing pauses. Blur, change, and Enter also apply the value; Enter is optional.

### Calendar picker contract

The calendar icon explicitly opens the native picker. Selecting a date immediately writes it into the text field as `DD/MM/YYYY` and applies the filter.

The native date element is intentionally a 1px, non-interactive helper. Do not restore it as a transparent overlay across the text input. Some browsers expand native date fields beyond their declared dimensions; that caused keystrokes to be captured by the invisible control, reordered digits, and intermittent text entry.

## Critical implementation rules

### Disable Tabulator live filtering for composite editors

Tabulator normally adds its own delayed listener to header inputs. The advanced editors already call Tabulator's custom `success(...)` callback with an object. If Tabulator's standard listener also runs, it subsequently submits only the raw string and overwrites the object. The observed symptom is that a filter works briefly and then all rows return.

TableKit disables that competing listener for the two advanced editors:

    if (col.headerFilter === customNumericFilterEditor ||
        col.headerFilter === customDateFilterEditor) {
      col.headerFilterLiveFilter = false;
    }

Do not remove this configuration. The custom editors implement their own updates.

### Restore values after header redraws

Tabulator can redraw headers after filtering, data changes, or layout changes. Advanced editors restore their stored operator/value in `onRendered`. Without it, a live filter can remain active while the editor appears blank.

### Isolate typing from table navigation

The typed date input stops keydown events from bubbling to table-level keyboard handling. This prevents Tabulator navigation from stealing characters or focus. Its explicit Enter handler commits the filter and blurs the input.

## Historical defect log

| Symptom | Cause | Fix |
| --- | --- | --- |
| Numeric comparison choices disappeared. | Shared refactor simplified original controls. | Restored all six operators. |
| Filter worked briefly, then all rows returned. | Tabulator live listener overwrote object filter state. | Disable built-in live filtering for advanced editors. |
| Filter controls looked blank after updates. | Values were not restored after redraw. | Restore state in `onRendered`. |
| Calendar worked but typing was intermittent/reordered. | Invisible native input covered text field. | 1px helper plus explicit calendar-icon click. |
| `01082026` was ambiguous. | Browser locale interpreted digits. | Day-first input mask. |
| Typed dates needed Enter. | Only commit events applied state. | 350 ms debounced automatic apply. |
| Reset left values visible in headers. | UI existed outside Tabulator default reset. | Per-table reset registry. |

## Verification checklist

1. Verify pagination, sorting, selection, and reset buttons.
2. Test a dropdown selection, then reset to All.
3. Test every numeric operator with a known value and a comma-formatted number.
4. Type a date with slashes and type `01082026`; verify it displays as `01/08/2026`.
5. Stop typing and confirm automatic date filtering applies without Enter.
6. Confirm blur and Enter still commit the typed date.
7. Use the calendar icon and confirm selection filters immediately.
8. Test on, not_on, before, and after with neighboring known dates.
9. Reset and confirm both rows and header controls reset.
10. Confirm both copies of `app/static/js/table.js` have the same hash.

Quick checks:

    node --check app/static/js/table.js
    Get-FileHash ..\itqan-trades\app\static\js\table.js, ..\mehboob-portfolio\app\static\js\table.js

## Maintenance rule

Page templates may have different columns, formatters, data, and wording. Shared TableKit behavior must remain identical between the two repositories. Update both scripts in the same change, syntax-check both, and compare hashes before completion.
