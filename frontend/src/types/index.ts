export type LanguageMode = "automatic" | "manual";
export type AppMode = "quick" | "meeting";

export interface Segment {
  start: number;
  end: number;
  speaker?: string;
  language?: string;
  text: string;
}

export interface ProcessResponse {
  job_id: string | null;
  status: "queued" | "complete";
  detail?: string;
}

export interface JobStatus {
  job_id: string;
  status: "queued" | "processing" | "complete" | "error";
  percent_complete: number;
  current_step?: string;
}

export interface HistoryEntry {
  id: string;
  timestamp: string;
  title: string | null;
  duration_seconds: number;
  languages: string[];
  transcript: string;
  segments: Segment[];
  job_id: string | null;
}

export interface AskResponse {
  answer: string;
  sources: string[];
}
