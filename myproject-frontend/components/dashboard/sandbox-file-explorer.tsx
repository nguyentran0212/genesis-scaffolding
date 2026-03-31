"use client";

import * as React from "react";
import { SandboxFile } from "@/types/sandbox";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import { StandaloneUploadButton } from "./standalone-upload-button";
import { SandboxTable } from "./sandbox/sandbox-table";

export function SandboxFileExplorer({ initialFiles }: { initialFiles: SandboxFile[] }) {
  const [files, setFiles] = React.useState(initialFiles);
  const [search, setSearch] = React.useState("");

  const filteredFiles = React.useMemo(
    () =>
      files.filter((f) =>
        f.filename.toLowerCase().includes(search.toLowerCase())
      ),
    [files, search]
  );

  const handleFileDeleted = React.useCallback((fileId: number) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId));
  }, []);

  const handleUploadSuccess = React.useCallback((newFile: SandboxFile) => {
    setFiles((prev) => [newFile, ...prev]);
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 bg-white p-4 rounded-xl border shadow-sm">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search sandbox..."
            className="pl-10"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <StandaloneUploadButton onSuccess={handleUploadSuccess} />
      </div>

      <SandboxTable files={filteredFiles} onFileDeleted={handleFileDeleted} />
    </div>
  );
}
