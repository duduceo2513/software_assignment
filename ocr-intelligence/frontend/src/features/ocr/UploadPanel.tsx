import { ActionIcon, Button, Group, Progress, SegmentedControl, Stack, Text } from "@mantine/core";
import { Dropzone, type FileRejection } from "@mantine/dropzone";
import { notifications } from "@mantine/notifications";
import { FileImage, FileText, ScanSearch, UploadCloud, X } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCreateJob } from "../../hooks/useJobs";
import type { LanguageCode } from "../../types/ocr";
import { ACCEPTED_TYPES, LANGUAGE_OPTIONS, MAX_FILES, MAX_FILE_BYTES, formatBytes } from "./format";

function describeRejection(rejection: FileRejection): string {
  const code = rejection.errors[0]?.code;
  if (code === "file-too-large") return `${rejection.file.name}: larger than 20 MB`;
  if (code === "file-invalid-type") return `${rejection.file.name}: unsupported format`;
  if (code === "too-many-files") return `Only ${MAX_FILES} documents per run`;
  return `${rejection.file.name}: ${rejection.errors[0]?.message ?? "rejected"}`;
}

export function UploadPanel() {
  const navigate = useNavigate();
  const createJob = useCreateJob();
  const [files, setFiles] = useState<File[]>([]);
  const [language, setLanguage] = useState<LanguageCode>("auto");
  const [uploadFraction, setUploadFraction] = useState<number | null>(null);

  const addFiles = (incoming: File[]) => {
    const merged = [...files, ...incoming];
    if (merged.length > MAX_FILES) {
      notifications.show({ color: "orange", title: "Too many files", message: `Only ${MAX_FILES} documents per run.` });
    }
    setFiles(merged.slice(0, MAX_FILES));
  };

  const submit = () => {
    setUploadFraction(0);
    createJob.mutate(
      { files, language, onProgress: setUploadFraction },
      {
        onSuccess: (job) => {
          notifications.show({ color: "green", title: "Documents uploaded", message: "OCR has been queued." });
          setFiles([]);
          navigate(`/jobs/${job.id}`);
        },
        onError: (error) =>
          notifications.show({ color: "red", title: "Upload failed", message: error.message, autoClose: 8000 }),
        onSettled: () => setUploadFraction(null),
      },
    );
  };

  const busy = createJob.isPending;

  return (
    <Stack gap="lg">
      <Dropzone
        className="oi-dropzone"
        onDrop={addFiles}
        onReject={(rejections) =>
          notifications.show({
            color: "red",
            title: "Some files were rejected",
            message: rejections.map(describeRejection).join("\n"),
          })
        }
        accept={ACCEPTED_TYPES}
        maxSize={MAX_FILE_BYTES}
        multiple
        disabled={busy || files.length >= MAX_FILES}
        aria-label="Upload documents"
      >
        <Stack align="center" justify="center" gap="xs" mih={200} style={{ pointerEvents: "none" }}>
          <div className="oi-icon-tile">
            <UploadCloud size={22} aria-hidden />
          </div>
          <Text fw={650} size="lg">
            Drag documents here or click to browse
          </Text>
          <Text c="dimmed" size="sm">
            PDF, PNG, JPG, TIFF - up to {MAX_FILES} files, 20 MB each
          </Text>
        </Stack>
      </Dropzone>

      {files.length > 0 && (
        <Stack gap="xs" className="oi-fade-in" aria-label="Selected files">
          {files.map((file, index) => {
            const Icon = file.type === "application/pdf" ? FileText : FileImage;
            return (
              <Group key={`${file.name}-${index}`} className="oi-card" p="sm" wrap="nowrap" justify="space-between">
                <Group wrap="nowrap" gap="sm" miw={0}>
                  <div className="oi-icon-tile">
                    <Icon size={20} aria-hidden />
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <Text fw={600} truncate>
                      {file.name}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {formatBytes(file.size)}
                    </Text>
                  </div>
                </Group>
                <ActionIcon
                  variant="subtle"
                  color="gray"
                  aria-label={`Remove ${file.name}`}
                  disabled={busy}
                  onClick={() => setFiles(files.filter((_, i) => i !== index))}
                >
                  <X size={18} />
                </ActionIcon>
              </Group>
            );
          })}
        </Stack>
      )}

      <Group justify="space-between" align="flex-end" wrap="wrap" gap="md">
        <Stack gap={6}>
          <Text size="sm" fw={600} id="lang-label">
            Recognition language
          </Text>
          <SegmentedControl
            aria-labelledby="lang-label"
            value={language}
            onChange={(value) => setLanguage(value as LanguageCode)}
            data={LANGUAGE_OPTIONS.map(({ value, label }) => ({ value, label }))}
            disabled={busy}
          />
          <Text size="xs" c="dimmed">
            {LANGUAGE_OPTIONS.find((o) => o.value === language)?.hint}
          </Text>
        </Stack>
        <Button
          size="md"
          leftSection={<ScanSearch size={18} aria-hidden />}
          disabled={files.length === 0}
          loading={busy}
          onClick={submit}
         
        >
          Process Documents
        </Button>
      </Group>

      {busy && uploadFraction !== null && (
        <Stack gap={4}>
          <Progress value={Math.round(uploadFraction * 100)} animated aria-label="Upload progress" />
          <Text size="xs" c="dimmed">
            Uploading {Math.round(uploadFraction * 100)}%
          </Text>
        </Stack>
      )}
    </Stack>
  );
}
