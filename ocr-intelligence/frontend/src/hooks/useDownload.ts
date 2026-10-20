import { notifications } from "@mantine/notifications";
import { useCallback, useState } from "react";
import { downloadFile } from "../api/ocr";

/** Downloads a file via Blob and reports failures as toasts. `busyKey` identifies the active download. */
export function useDownload() {
  const [busyKey, setBusyKey] = useState<string | null>(null);

  const download = useCallback(async (key: string, path: string, fallbackName: string) => {
    setBusyKey(key);
    try {
      await downloadFile(path, fallbackName);
    } catch (error) {
      notifications.show({
        color: "red",
        title: "Download failed",
        message: error instanceof Error ? error.message : "Unexpected error.",
      });
    } finally {
      setBusyKey(null);
    }
  }, []);

  return { busyKey, download };
}
