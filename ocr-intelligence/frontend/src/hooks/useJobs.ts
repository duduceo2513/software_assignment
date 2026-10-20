import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createJob, deleteJob, getJob, listJobs } from "../api/ocr";
import type { LanguageCode } from "../types/ocr";

const POLL_INTERVAL_MS = 2000;

export const jobKeys = {
  all: ["jobs"] as const,
  list: (limit: number) => ["jobs", "list", limit] as const,
  detail: (id: string) => ["jobs", "detail", id] as const,
};

export function useJobs(limit = 100) {
  return useQuery({
    queryKey: jobKeys.list(limit),
    queryFn: () => listJobs(limit),
    // keep the list fresh while anything is still being processed
    refetchInterval: (query) => (query.state.data?.some((job) => !job.is_finished) ? POLL_INTERVAL_MS : false),
  });
}

/** Polls every 2 s until the job reaches a terminal status, then stops automatically. */
export function useJob(id: string | undefined) {
  return useQuery({
    queryKey: jobKeys.detail(id ?? ""),
    queryFn: () => getJob(id as string),
    enabled: Boolean(id),
    refetchInterval: (query) => (query.state.data?.is_finished ? false : POLL_INTERVAL_MS),
    retry: (count, error) => (error as { status?: number }).status !== 404 && count < 2,
  });
}

export function useCreateJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: { files: File[]; language: LanguageCode; onProgress?: (fraction: number) => void }) =>
      createJob(vars.files, vars.language, vars.onProgress),
    onSuccess: (job) => {
      queryClient.setQueryData(jobKeys.detail(job.id), job);
      void queryClient.invalidateQueries({ queryKey: ["jobs", "list"] });
    },
  });
}

export function useDeleteJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteJob,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: jobKeys.all }),
  });
}
