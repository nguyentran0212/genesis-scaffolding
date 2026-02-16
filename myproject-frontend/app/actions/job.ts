'use server';

import { getAccessToken } from '@/lib/session';
import { WorkflowJob, JobFile } from '@/types/job';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

export async function getJobsAction(limit: number = 20, offset: number = 0): Promise<WorkflowJob[]> {
  const token = await getAccessToken();

  if (!token) throw new Error('Unauthorized');

  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });

  const response = await fetch(`${FASTAPI_URL}/jobs/?${params}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    // We want the job list to be dynamic, but we can use a short revalidation
    next: { revalidate: 10, tags: ['jobs'] }
  });

  if (!response.ok) {
    throw new Error('Failed to fetch jobs');
  }

  return response.json();
}

export async function getJobFilesAction(jobId: number): Promise<JobFile[]> {
  const token = await getAccessToken();

  if (!token) throw new Error('Unauthorized');

  try {
    const response = await fetch(`${FASTAPI_URL}/jobs/${jobId}/output`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      // Do not cache this; we want the latest file list upon job completion
      next: { revalidate: 0 }
    });

    if (!response.ok) {
      // If the backend returns 404, it might just mean no files were produced yet
      if (response.status === 404) return [];
      throw new Error('Failed to fetch job output files');
    }

    return await response.json();
  } catch (error) {
    console.error(`[getJobFilesAction] Error for job ${jobId}:`, error);
    return [];
  }
}

export async function getJobByIdAction(jobId: number): Promise<WorkflowJob> {
  const token = await getAccessToken();

  if (!token) throw new Error('Unauthorized');

  const response = await fetch(`${FASTAPI_URL}/jobs/${jobId}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    // Ensure we don't cache an old "running" status forever
    cache: 'no-store'
  });

  if (!response.ok) {
    if (response.status === 404) throw new Error('Job not found');
    throw new Error('Failed to fetch job detail');
  }

  return response.json();
}

