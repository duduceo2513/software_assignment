// Mirrors apps/ocr/serializers.py

export type LanguageCode = "auto" | "kk" | "ru" | "en";
export type JobStatus = "pending" | "processing" | "completed" | "failed" | "partially_completed";
export type DocumentStatus = "pending" | "processing" | "completed" | "failed";

export interface OcrDocument {
  id: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  page_count: number;
  pages_processed: number;
  language: LanguageCode;
  status: DocumentStatus;
  processing_seconds: number | null;
  created_at: string;
  finished_at: string | null;
  error_message: string;
  text_preview: string;
  has_result: boolean;
  download_url: string | null;
}

export interface OcrJob {
  id: string;
  title: string;
  status: JobStatus;
  language: LanguageCode;
  documents_count: number;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  error_message: string;
  is_finished: boolean;
  documents: OcrDocument[];
  zip_url: string | null;
}

export interface ApiEnvelope<T> {
  success: boolean;
  data: T | null;
  error: { code: string; message: string; details: unknown } | null;
}
