export type TaskStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | 'removed';

export interface TaskEvent {
  id: string;
  event_type: string;
  message: string;
  created_at: string;
}

export interface Task {
  id: string;
  status: TaskStatus;
  prompt_text: string;
  pdf_filename: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
  cancel_requested: boolean;
  attempt_count: number;
  created_by: string | null;
}

export interface TaskDetail extends Task {
  events: TaskEvent[];
}

export interface QueueSummary {
  queued: number;
  running: number;
  completed: number;
  failed: number;
  cancelled: number;
  total: number;
  active_slots: number;
  max_slots: number;
}
