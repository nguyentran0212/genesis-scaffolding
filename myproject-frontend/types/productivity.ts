export type Status = 'backlog' | 'todo' | 'in_progress' | 'completed' | 'canceled';
export type JournalType = 'daily' | 'weekly' | 'monthly' | 'yearly' | 'project';

export interface Project {
  id: number;
  name: string;
  description?: string;
  start_date?: string;
  deadline?: string;
  status: Status;
}

export interface Task {
  id: number;
  title: string;
  description?: string;
  hard_deadline?: string;
  assigned_date?: string;
  start_time?: string;
  duration_minutes?: number;
  status: Status;
  created_at: string;
  completed_at?: string;
  project_ids: number[];
}

export interface JournalEntry {
  id: number;
  entry_type: JournalType;
  reference_date: string;
  title?: string;
  content: string;
  project_id?: number;
  created_at: string;
  updated_at: string;
}
