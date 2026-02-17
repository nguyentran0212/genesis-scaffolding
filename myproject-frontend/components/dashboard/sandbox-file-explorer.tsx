'use client';

import { useState } from 'react';
import { SandboxFile } from '@/types/sandbox';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  FileText, Search, Upload, Trash2,
  FileDown
} from 'lucide-react';
import { toast } from 'sonner';
import { deleteFileAction } from '@/app/actions/sandbox';
import { StandaloneUploadButton } from './standalone-upload-button';

export function SandboxFileExplorer({ initialFiles }: { initialFiles: SandboxFile[] }) {
  const [files, setFiles] = useState(initialFiles);
  const [search, setSearch] = useState('');

  const filteredFiles = files.filter(f =>
    f.filename.toLowerCase().includes(search.toLowerCase())
  );

  const handleDelete = async (file: SandboxFile) => {
    if (!confirm(`Are you sure you want to delete ${file.filename}?`)) return;

    try {
      // Assuming you have a delete action: 
      await deleteFileAction(file.id);
      setFiles(files.filter(f => f.id !== file.id));
      toast.success("File deleted");
    } catch (err) {
      toast.error("Failed to delete file");
    }
  };

  const handleDownload = (file: SandboxFile) => {
    // Logic to trigger a browser download via your API URL
    window.open(`/api/files/${file.id}/download`, '_blank');
  };
  // This function will be called when a file is uploaded or picked in the modal
  const handleFileAdded = (newFile: SandboxFile) => {
    // Avoid duplicates
    setFiles(prev => {
      if (prev.find(f => f.id === newFile.id)) return prev;
      return [newFile, ...prev];
    });
    toast.success(`${newFile.filename} added to sandbox`);
  };
  const handleUploadSuccess = (newFile: SandboxFile) => {
    // Add the new file to the top of the list
    setFiles(prev => [newFile, ...prev]);
  };

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

      <div className="bg-white border rounded-xl overflow-hidden shadow-sm">
        <table className="w-full text-left border-collapse">
          <thead className="bg-slate-50 border-b text-xs uppercase tracking-wider text-muted-foreground font-semibold">
            <tr>
              <th className="px-6 py-4">Name</th>
              <th className="px-6 py-4">Path</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {filteredFiles.map((file) => (
              <tr key={file.id} className="hover:bg-slate-50/50 transition-colors group">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${file.filename.endsWith('.pdf') ? 'bg-red-50 text-red-500' : 'bg-blue-50 text-blue-500'}`}>
                      <FileText className="h-4 w-4" />
                    </div>
                    <span className="font-medium text-sm truncate max-w-xs">{file.filename}</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <code className="text-xs bg-slate-100 px-2 py-1 rounded text-slate-600 font-mono">
                    {file.relative_path}
                  </code>
                </td>
                <td className="px-6 py-4 text-right">
                  <div className="flex justify-end gap-2">
                    <Button variant="ghost" size="icon" onClick={() => handleDownload(file)}>
                      <FileDown className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" className="text-destructive hover:bg-destructive/10" onClick={() => handleDelete(file)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredFiles.length === 0 && (
          <div className="py-20 text-center space-y-2">
            <p className="text-muted-foreground">No files found in your sandbox.</p>
            <Button variant="outline" size="sm" onClick={() => setSearch('')}>Clear Search</Button>
          </div>
        )}
      </div>
    </div>
  );
}
