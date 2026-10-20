import { Alert, Button, Group, Skeleton, Stack, Text, Title } from "@mantine/core";
import { ArrowLeft, CircleAlert, FileArchive } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { StatusBadge } from "../components/StatusBadge";
import { ErrorState } from "../components/States";
import { DocumentCard } from "../features/ocr/DocumentCard";
import { formatDate, languageLabel } from "../features/ocr/format";
import { useDownload } from "../hooks/useDownload";
import { useJob } from "../hooks/useJobs";
import type { OcrDocument } from "../types/ocr";

export function JobPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const { data: job, isLoading, error, refetch, isFetching } = useJob(jobId);
  const { busyKey, download } = useDownload();

  if (isLoading) {
    return (
      <Stack gap="md">
        <Skeleton height={36} width={320} />
        <Skeleton height={140} radius="lg" />
        <Skeleton height={140} radius="lg" />
      </Stack>
    );
  }
  if (error || !job) {
    return (
      <>
        <BackLink />
        <ErrorState error={error} onRetry={() => void refetch()} />
      </>
    );
  }

  const onDownload = (document: OcrDocument) => {
    if (document.download_url) void download(document.id, document.download_url, document.original_filename);
  };

  return (
    <Stack gap="lg" className="oi-fade-in">
      <BackLink />
      <Group justify="space-between" align="flex-start" wrap="nowrap">
        <div style={{ minWidth: 0 }}>
          <Title order={2} style={{ letterSpacing: "-0.01em" }}>
            {job.is_finished ? "Results" : "Processing"}
          </Title>
          <Text c="dimmed" size="sm" truncate>
            {job.title} - {languageLabel(job.language)} - started {formatDate(job.created_at)}
          </Text>
        </div>
        <Group gap="sm" wrap="nowrap">
          {!job.is_finished && isFetching && (
            <Text size="xs" c="dimmed">
              Updating...
            </Text>
          )}
          <StatusBadge status={job.status} />
        </Group>
      </Group>

      {job.status === "failed" && job.error_message && (
        <Alert color="red" icon={<CircleAlert size={18} />} title="The job failed">
          {job.error_message}
        </Alert>
      )}
      {job.status === "partially_completed" && (
        <Alert color="orange" icon={<CircleAlert size={18} />} title="Some documents failed">
          The finished documents can still be downloaded.
        </Alert>
      )}

      <Stack gap="md">
        {job.documents.map((document) => (
          <DocumentCard
            key={document.id}
            document={document}
            downloading={busyKey === document.id}
            onDownload={onDownload}
          />
        ))}
      </Stack>

      {job.zip_url && job.is_finished && (
        <Group justify="flex-end">
          <Button
            variant="light"
            size="md"
            leftSection={<FileArchive size={18} aria-hidden />}
            loading={busyKey === "zip"}
            onClick={() => void download("zip", job.zip_url as string, "ocr-results.zip")}
          >
            Download all as ZIP
          </Button>
        </Group>
      )}
    </Stack>
  );
}

function BackLink() {
  return (
    <Link to="/" style={{ textDecoration: "none", width: "fit-content" }}>
      <Group gap={6} c="dimmed">
        <ArrowLeft size={16} aria-hidden />
        <Text size="sm" fw={600}>
          Workspace
        </Text>
      </Group>
    </Link>
  );
}
