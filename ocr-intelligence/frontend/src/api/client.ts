import axios from "axios";
import type { ApiEnvelope } from "../types/ocr";

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api",
  timeout: 120_000,
});

export class ApiRequestError extends Error {
  readonly code: string;
  readonly status: number | null;

  constructor(message: string, code: string, status: number | null) {
    super(message);
    this.name = "ApiRequestError";
    this.code = code;
    this.status = status;
  }
}

function envelopeError(body: unknown): { message: string; code: string } | null {
  if (body && typeof body === "object" && "error" in body) {
    const error = (body as ApiEnvelope<unknown>).error;
    if (error && typeof error.message === "string") return { message: error.message, code: error.code };
  }
  return null;
}

/** Translate any failure (axios, network, API envelope) into a readable ApiRequestError. */
export async function toApiError(error: unknown): Promise<ApiRequestError> {
  if (error instanceof ApiRequestError) return error;
  if (axios.isAxiosError(error)) {
    if (!error.response) {
      const timedOut = error.code === "ECONNABORTED";
      return new ApiRequestError(
        timedOut
          ? "The server took too long to respond."
          : "Cannot reach the OCR server. Check that the backend is running.",
        timedOut ? "timeout" : "network_error",
        null,
      );
    }
    let body: unknown = error.response.data;
    if (body instanceof Blob) {
      // responseType "blob" delivers JSON error envelopes as Blobs
      try {
        body = JSON.parse(await body.text());
      } catch {
        body = null;
      }
    }
    const parsed = envelopeError(body);
    if (parsed) return new ApiRequestError(parsed.message, parsed.code, error.response.status);
    if (error.response.status >= 500) {
      return new ApiRequestError("The server hit an error. Please try again.", "server_error", error.response.status);
    }
    return new ApiRequestError(`Request failed (${error.response.status}).`, "http_error", error.response.status);
  }
  return new ApiRequestError(error instanceof Error ? error.message : "Unexpected error.", "unknown", null);
}

export async function unwrap<T>(request: Promise<{ data: ApiEnvelope<T> }>): Promise<T> {
  try {
    const { data } = await request;
    if (!data.success || data.data === null) {
      throw new ApiRequestError(data.error?.message ?? "Request failed.", data.error?.code ?? "error", null);
    }
    return data.data;
  } catch (error) {
    throw await toApiError(error);
  }
}
