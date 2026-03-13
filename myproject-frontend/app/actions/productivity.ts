'use server'

import { apiFetch } from "@/lib/api-client";
import { revalidatePath } from "next/cache";
import { Task, Project, JournalEntry } from "@/types/productivity";

// --- Tasks ---

export async function getTasksAction(params?: any): Promise<Task[]> {
  const query = new URLSearchParams(params).toString();
  const res = await apiFetch(`/productivity/tasks?${query}`);
  if (!res.ok) throw new Error("Failed to fetch tasks");
  return res.json();
}

export async function createTaskAction(data: any) {
  const res = await apiFetch(`/productivity/tasks`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  revalidatePath('/dashboard/productivity');
  return res.json();
}

export async function bulkUpdateTasksAction(data: {
  ids: number[],
  updates: any,
  add_project_ids?: number[],
  remove_project_ids?: number[]
}) {
  const res = await apiFetch(`/productivity/tasks/bulk`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
  revalidatePath('/dashboard/productivity');
  return res.json();
}

export async function getTaskAction(id: string | number): Promise<Task> {
  const res = await apiFetch(`/productivity/tasks/${id}`);
  if (!res.ok) throw new Error("Failed to fetch task");
  return res.json();
}

export async function updateTaskAction(id: string | number, data: any) {
  const res = await apiFetch(`/productivity/tasks/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });

  if (!res.ok) throw new Error("Failed to update task");

  // Revalidate both the specific task and the general dashboard
  revalidatePath('/dashboard/projects');
  revalidatePath('/dashboard/tasks');
  return res.json();
}

export async function deleteTaskAction(id: string | number) {
  const res = await apiFetch(`/productivity/tasks/${id}`, {
    method: 'DELETE',
  });

  if (!res.ok) throw new Error("Failed to delete task");

  revalidatePath('/dashboard/projects');
  revalidatePath('/dashboard/tasks');
}

// --- Projects ---

export async function getProjectsAction(): Promise<Project[]> {
  const res = await apiFetch(`/productivity/projects`);
  if (!res.ok) throw new Error("Failed to fetch projects");
  return res.json();
}

export async function createProjectAction(data: any) {
  const res = await apiFetch(`/productivity/projects`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  revalidatePath('/dashboard/productivity');
  return res.json();
}

export async function getProjectAction(id: string | number): Promise<Project> {
  const res = await apiFetch(`/productivity/projects/${id}`);
  if (!res.ok) throw new Error("Failed to fetch project");
  return res.json();
}

export async function updateProjectAction(id: string | number, data: any) {
  const res = await apiFetch(`/productivity/projects/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
  revalidatePath('/dashboard/projects');
  revalidatePath(`/dashboard/projects/${id}`);
  return res.json();
}

export async function deleteProjectAction(id: string | number) {
  const res = await apiFetch(`/productivity/projects/${id}`, {
    method: 'DELETE',
  });
  revalidatePath('/dashboard/projects');
}

// --- Journals ---

export async function getJournalsAction(params?: any): Promise<JournalEntry[]> {
  const query = new URLSearchParams(params).toString();
  const res = await apiFetch(`/productivity/journals?${query}`);
  if (!res.ok) throw new Error("Failed to fetch journals");
  return res.json();
}
