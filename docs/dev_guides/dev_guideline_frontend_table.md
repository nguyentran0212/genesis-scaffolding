# Developer Guide: Data Table System

This guide explains how to use the project's **Data Table Engine** to build powerful, sortable, filterable, and paginated tables for any backend entity.

## Architecture Overview

The system uses a **Three-Layer Architecture** powered by `@tanstack/react-table`. This separates the complex table logic (sorting, selection, pagination) from the UI and the specific data being displayed.

### Directory Structure
| Path | Responsibility |
| :--- | :--- |
| `components/dashboard/shared/data-table/` | **Shared UI Layer:** Generic table engine, sortable headers, column togglers, and pagination controls. |
| `components/dashboard/[entity]/table/` | **Definition Layer:** Column definitions (`columns.tsx`) and specific filters (`toolbar.tsx`). |
| `components/dashboard/[entity]/[entity]-table.tsx` | **Orchestrator:** Connects the engine to the definitions, defines default sorting, and handles bulk logic. |

---

## 1. Pagination

The DataTable supports two pagination modes. For most use cases, **client-side pagination is recommended** for simplicity.

### Uncontrolled (Client-side) Pagination (Recommended)

TanStack Table manages pagination state internally. Fetch all data once, pass to DataTable:

```tsx
// In your page (server component)
const tasks = await getTasksAction();
return <TaskTable tasks={tasks} />;

// In TaskTable
<DataTable
  data={tasks}
  columns={columns}
  enablePagination={true}
  defaultPageSize={20}
/>
```

### Controlled (Server-side) Pagination

Use when fetching paginated data from the server. Requires manual wiring:

```tsx
<DataTable
  data={tasks}
  columns={columns}
  enablePagination={true}
  manualPagination={true}           // Tell TanStack pagination is server-side
  pageCount={Math.ceil(total / pageSize)}
  paginationState={{ pageIndex, pageSize }}
  onPaginationChange={(pageIndex, pageSize) => {
    // Handle page change - update URL, refetch, etc.
  }}
/>
```

---

## 2. Sorting Fundamentals

### The `DataTableColumnHeader`
To make a column sortable, use the `DataTableColumnHeader` component:

```tsx
header: ({ column }) => <DataTableColumnHeader column={column} title="Due Date" />
```

### Initial & Multi-Field Sorting
Define `initialSorting` to stack multiple sort rules:

```tsx
const defaultSorting: SortingState = [
  { id: "status", desc: true },       // Primary sort
  { id: "hard_deadline", desc: false } // Secondary sort
];
```

---

## 3. Advanced Sorting Logic

### Pattern A: The "Nulls Last" Strategy
Force empty values to the bottom:

```tsx
const dateSortingWithNullsLast = (rowA: Row<any>, rowB: Row<any>, columnId: string) => {
  const a = rowA.getValue(columnId);
  const b = rowB.getValue(columnId);
  if (!a && !b) return 0;
  if (!a) return 1;
  if (!b) return -1;
  return new Date(a).getTime() - new Date(b).getTime();
};
```

### Pattern B: Status Weight Sorting (Enums)
Use a weight map for logical ordering:

```tsx
const STATUS_WEIGHTS = { in_progress: 3, todo: 2, backlog: 1 };
const statusSortingFn = (rowA: Row<any>, rowB: Row<any>, columnId: string) => {
  const weightA = STATUS_WEIGHTS[rowA.getValue(columnId)] ?? 0;
  const weightB = STATUS_WEIGHTS[rowB.getValue(columnId)] ?? 0;
  return weightA - weightB;
};
```

---

## 4. Implementation Workflow (Example: `Task` Entity)

### Step 1: Define Columns (`columns.tsx`)
```tsx
export const getTaskColumns = (projects: Project[], variant: string): ColumnDef<Task>[] => [
  {
    accessorKey: "status",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Status" />,
    sortingFn: statusSortingFn,
    cell: ({ row }) => <Badge>{row.getValue("status")}</Badge>,
  },
  {
    accessorKey: "hard_deadline",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Deadline" />,
    sortingFn: dateSortingWithNullsLast,
    cell: ({ row }) => <div>{row.getValue("hard_deadline") || "No Date"}</div>,
  }
];
```

### Step 2: Create the Orchestrator (`task-table.tsx`)
```tsx
"use client";

interface TaskTableProps {
  tasks: Task[];
  projects: Project[];
  variant?: "table" | "list" | "dashboard";
  floatingOffset?: boolean;
}

export function TaskTable({ tasks, projects, variant = "table", floatingOffset = false }: TaskTableProps) {
  const enablePagination = variant === "table";
  const columns = React.useMemo(() => getTaskColumns(projects, variant), [projects, variant]);

  return (
    <DataTable
      data={tasks}
      columns={columns}
      enablePagination={enablePagination}
      defaultPageSize={20}
      renderToolbar={(table) => <TaskTableToolbar table={table} />}
      renderFloatingBar={(table) => <BulkActionBar ... />}
    />
  );
}
```

### Step 3: Use in a Page
```tsx
// Simple server component - no client hooks needed
export default async function TasksPage() {
  const tasks = await getTasksAction({ include_completed: false });
  const projects = await getProjectsAction();

  return (
    <TaskTable tasks={tasks} projects={projects} />
  );
}
```

---

## 5. Selection and Bulk Actions

Use the `renderFloatingBar` prop:

```tsx
renderFloatingBar={(table) => {
  const selectedRows = table.getFilteredSelectedRowModel().rows;
  const selectedIds = selectedRows.map(r => (r.original as any).id);
  if (selectedIds.length === 0) return null;
  return <BulkActionBar selectedIds={selectedIds} onClear={() => table.resetRowSelection()} />;
}}
```

---

## 6. Best Practices

1. **Client-side for <1000 items:** Fetch all data once, let TanStack handle sorting/pagination. Simpler and faster UX.
2. **Memoization:** Wrap `getColumns()` in `useMemo` to prevent recalculation on state changes.
3. **Unique IDs:** Always provide `getRowId` - without it, selection breaks when sorting.
4. **Display vs. Data:**
   - Use `accessorFn` to return a **sortable primitive**
   - Use `cell` to return the **JSX/UI**
5. **Multi-Sort:** Keep `enableMultiSort={true}` to allow `Shift + Click` for complex sorting.
