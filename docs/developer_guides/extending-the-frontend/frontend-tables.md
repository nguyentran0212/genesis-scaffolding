# Data Table System

This guide explains how to use the Data Table Engine to build sortable, filterable, and paginated tables for any backend entity.

## Architecture Overview

The system uses a **Three-Layer Architecture** powered by `@tanstack/react-table`:

| Layer | Path | Responsibility |
|---|---|---|
| **Shared UI** | `components/dashboard/shared/data-table/` | Generic table engine, sortable headers, column togglers, pagination |
| **Definition** | `components/dashboard/[entity]/table/` | Column definitions and specific filters |
| **Orchestrator** | `components/dashboard/[entity]/[entity]-table.tsx` | Connects engine to definitions, defines defaults, handles bulk logic |

## Pagination

**Client-side pagination (recommended)**: TanStack Table manages pagination state internally. Fetch all data once and pass to DataTable with `enablePagination={true}` and `defaultPageSize={20}`.

**Server-side pagination**: Use when fetching paginated data from the server. Set `manualPagination={true}` and provide `pageCount`, `paginationState`, and `onPaginationChange`.

## Sorting

Use `DataTableColumnHeader` to make columns sortable. For multi-field sorting, define `initialSorting` with an array of sort rules.

### Common Sorting Patterns

**"Nulls Last"**: Force empty values to the bottom of sorted results.

**Status Weight Sorting**: Use a weight map for logical ordering of enum values (e.g., `in_progress > todo > backlog`).

## Implementation Workflow

### Step 1: Define Columns

Create `columns.tsx` that exports column definitions. Each column uses `DataTableColumnHeader` for sortable headers, `sortingFn` for custom sort logic, and `cell` for rendering.

### Step 2: Create the Orchestrator

Create `[entity]-table.tsx` that wraps `DataTable` with the columns and toolbar. Use `useMemo` to prevent column recalculation on state changes.

### Step 3: Use in a Page

Server components can fetch data and render the table directly without client hooks.

## Selection and Bulk Actions

Use the `renderFloatingBar` prop to show a floating action bar when rows are selected. The bar receives `selectedIds` from `table.getFilteredSelectedRowModel().rows`.

## Best Practices

1. **Client-side for <1000 items**: Fetch all data once; simpler and faster UX.
2. **Memoization**: Wrap `getColumns()` in `useMemo`.
3. **Unique IDs**: Always provide `getRowId` — without it selection breaks when sorting.
4. **Display vs. Data**: Use `accessorFn` to return a sortable primitive; use `cell` to return JSX.
5. **Multi-Sort**: Keep `enableMultiSort={true}` to allow `Shift + Click` for complex sorting.
