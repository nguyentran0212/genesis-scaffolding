"use client";

import * as React from "react";
import { SandboxFile } from "@/types/sandbox";
import { DataTable } from "@/components/dashboard/shared/data-table/data-table";
import { getSandboxColumns } from "./table/columns";

interface SandboxTableProps {
  files: SandboxFile[];
  onFileDeleted: (relativePath: string) => void;
}

export function SandboxTable({ files, onFileDeleted }: SandboxTableProps) {
  const columns = React.useMemo(
    () => getSandboxColumns(onFileDeleted),
    [onFileDeleted]
  );

  return (
    <DataTable
      data={files}
      columns={columns}
      getRowId={(row: SandboxFile) => row.relative_path}
      enablePagination={true}
      defaultPageSize={20}
    />
  );
}
