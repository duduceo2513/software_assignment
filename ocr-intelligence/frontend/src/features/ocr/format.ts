import type { DocumentStatus, JobStatus, LanguageCode } from "../../types/ocr";

export const LANGUAGE_OPTIONS: { value: LanguageCode; label: string; hint: string }[] = [
  { value: "auto", label: "Auto", hint: "Multilingual Cyrillic + Latin model" },
  { value: "kk", label: "Kazakh", hint: "Cyrillic model incl. Ә Ғ Қ Ң Ө Ұ Ү Һ І" },
  { value: "ru", label: "Russian", hint: "Cyrillic model" },
  { value: "en", label: "English", hint: "Dedicated English model" },
];

export const languageLabel = (code: LanguageCode) =>
  LANGUAGE_OPTIONS.find((option) => option.value === code)?.label ?? code;

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function formatDuration(seconds: number | null): string {
  if (seconds === null) return "-";
  if (seconds < 60) return `${seconds.toFixed(1)} s`;
  return `${Math.floor(seconds / 60)} min ${Math.round(seconds % 60)} s`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export const STATUS_META: Record<JobStatus | DocumentStatus, { label: string; color: string }> = {
  pending: { label: "In queue", color: "gray" },
  processing: { label: "Processing", color: "brand" },
  completed: { label: "Completed", color: "green" },
  failed: { label: "Failed", color: "red" },
  partially_completed: { label: "Partially completed", color: "orange" },
};

export const ACCEPTED_TYPES = {
  "application/pdf": [".pdf"],
  "image/png": [".png"],
  "image/jpeg": [".jpg", ".jpeg"],
  "image/tiff": [".tif", ".tiff"],
};

export const MAX_FILES = 2;
export const MAX_FILE_BYTES = 20 * 1024 * 1024;
