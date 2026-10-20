import { http, toApiError, unwrap } from "./client";
import type { LanguageCode, OcrJob } from "../types/ocr";

export const listJobs = (limit = 100) => unwrap<OcrJob[]>(http.get("/ocr/jobs/", { params: { limit } }));

export const getJob = (id: string) => unwrap<OcrJob>(http.get(`/ocr/jobs/${id}/`));

export const deleteJob = (id: string) => unwrap<{ deleted: boolean }>(http.delete(`/ocr/jobs/${id}/`));

export function createJob(files: File[], language: LanguageCode, onProgress?: (fraction: number) => void) {
  const form = new FormData();
  files.forEach((file) => form.append("files[]", file));
  form.append("language", language);
  return unwrap<OcrJob>(
    http.post("/ocr/jobs/", form, {
      timeout: 10 * 60_000,
      onUploadProgress: (event) => {
        if (onProgress && event.total) onProgress(event.loaded / event.total);
      },
    }),
  );
}

function filenameFrom(disposition: string | undefined, fallback: string): string {
  if (!disposition) return fallback;
  const encoded = /filename\*=UTF-8''([^;]+)/i.exec(disposition);
  if (encoded?.[1]) return decodeURIComponent(encoded[1]);
  const plain = /filename="?([^";]+)"?/i.exec(disposition);
  return plain?.[1] ?? fallback;
}

/** Fetch a file as a Blob and trigger a browser download. `path` is a server path such as /api/ocr/... */
export async function downloadFile(path: string, fallbackName: string): Promise<void> {
  try {
    const relative = path.replace(/^\/api/, "");
    const response = await http.get<Blob>(relative, { responseType: "blob" });
    const name = filenameFrom(response.headers["content-disposition"] as string | undefined, fallbackName);
    const url = URL.createObjectURL(response.data);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = name;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  } catch (error) {
    throw await toApiError(error);
  }
}
