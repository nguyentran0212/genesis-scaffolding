export interface SandboxFile {
  id: number;
  filename: string;
  relative_path: string;
  folder: string | null;
  mime_type: string;
  size: number;
  created_at: string;
}

// filter the display and uploads
export const ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.md'];
export const ALLOWED_MIME_TYPES = ['application/pdf', 'text/plain', 'text/markdown'];
