'use server';

import { getAccessToken } from '@/lib/session';
import { SandboxFile } from '@/types/sandbox';
import { revalidateTag } from 'next/cache';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

/**
 * Fetch all files in the user's sandbox
 */
export async function getFilesAction(): Promise<SandboxFile[]> {
  const token = await getAccessToken();
  const response = await fetch(`${FASTAPI_URL}/files/`, {
    headers: { 'Authorization': `Bearer ${token}` },
    next: { tags: ['sandbox'] } // Use tags for easy revalidation after upload
  });

  if (!response.ok) throw new Error('Failed to fetch sandbox files');
  return response.json();
}

/**
 * Upload a file to the sandbox
 * @param formData contains the 'file' and optionally 'subfolder'
 */
export async function uploadFileAction(formData: FormData): Promise<SandboxFile> {
  const token = await getAccessToken();
  const subfolder = formData.get('subfolder') as string;

  const url = new URL(`${FASTAPI_URL}/files/upload`);
  if (subfolder) url.searchParams.append('subfolder', subfolder);

  const response = await fetch(url.toString(), {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData, // Send raw FormData (browser/Next.js handles boundary)
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Upload failed');
  }

  const result = await response.json();
  const fileObject = result.file || result;

  if (!fileObject.id) {
    console.error("Backend did not return a file ID:", result);
    throw new Error("Upload succeeded but server did not return file metadata.");
  }
  // Refresh the sandbox data across the app
  revalidateTag('sandbox', "max");

  return fileObject as SandboxFile;
}

/**
 * Fetch available folders for organization
 */
export async function getFoldersAction(): Promise<string[]> {
  const token = await getAccessToken();
  const response = await fetch(`${FASTAPI_URL}/files/folders`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
}
