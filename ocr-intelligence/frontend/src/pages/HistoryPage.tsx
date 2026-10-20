import { ActionIcon, Button, Group, Modal, Skeleton, Stack, Table, Text, Title, Tooltip } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { Download, ExternalLink, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { StatusBadge } from "../components/StatusBadge";
import { EmptyState, ErrorState } from "../components/States";
import { formatDate, formatDuration, languageLabel } from "../features/ocr/format";
import { useDownload } from "../hooks/useDownload";
import { useDeleteJob, useJobs } from "../hooks/useJobs";
import type { OcrJob } from "../types/ocr";

export function HistoryPage() {
  const { data, isLoading, error, refetch } = useJobs(100);
  const deleteJob = useDeleteJob();
  const { busyKey, download } = useDownload();
  const [pendingDelete, setPendingDelete] = useState<OcrJob | null>(null);

  const confirmDelete = () => {
    if (!pendingDelete) return;
    deleteJob.mutate(pendingDelete.id, {
      onSuccess: () => notifications.show({ color: "green", title: "Deleted", message: "The job and its files were removed." }),
      onError: (e) => notifications.show({ color: "red", title: "Could not delete", message: e.message }),
      onSettled: () => setPendingDelete(null),
    });
  };

  return (
    <Stack gap="lg" className="oi-fade-in">
      <div>
        <Title order={2}>History</Title>
        <Text c="dimmed" size="sm">
          Previously processed documents stored on this server.
        </Text>
      </div>

      <section className="oi-card" style={{ padding: 8, overflowX: "auto" }}>
        {isLoading ? (
          <Stack p="md" gap="sm">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} height={44} />
            ))}
          </Stack>
        ) : error ? (
          <ErrorState error={error} onRetry={() => void refetch()} />
        ) : !data || data.length === 0 ? (
          <EmptyState
            title="Nothing here yet"
            message="Processed documents will be listed here."
            action={
              <Button component={Link} to="/" variant="light" mt="xs">
                Upload documents
              </Button>
            }
          />
        ) : (
          <Table verticalSpacing="sm" horizontalSpacing="md" highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Documents</Table.Th>
                <Table.Th>Language</Table.Th>
                <Table.Th>Pages</Table.Th>
                <Table.Th>Time</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th>Created</Table.Th>
                <Table.Th aria-label="Actions" />
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {data.map((job) => {
                const pages = job.documents.reduce((sum, d) => sum + d.page_count, 0);
                const seconds = job.documents.reduce((sum, d) => sum + (d.processing_seconds ?? 0), 0);
                return (
                  <Table.Tr key={job.id}>
                    <Table.Td maw={320}>
                      <Text fw={600} size="sm" truncate>
                        {job.title}
                      </Text>
                    </Table.Td>
                    <Table.Td>{languageLabel(job.language)}</Table.Td>
                    <Table.Td>{pages}</Table.Td>
                    <Table.Td>{job.is_finished ? formatDuration(seconds) : "-"}</Table.Td>
                    <Table.Td>
                      <StatusBadge status={job.status} />
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm" c="dimmed">
                        {formatDate(job.created_at)}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Group gap={4} wrap="nowrap" justify="flex-end">
                        <Tooltip label="Open">
                          <ActionIcon component={Link} to={`/jobs/${job.id}`} variant="subtle" aria-label={`Open ${job.title}`}>
                            <ExternalLink size={17} />
                          </ActionIcon>
                        </Tooltip>
                        {job.documents_count === 1 &&
                          job.documents[0]?.download_url && (
                            <Tooltip label="Download DOCX">
                              <ActionIcon
                                variant="subtle"
                                aria-label="Download DOCX"
                                loading={busyKey === job.id}
                                onClick={() => {
                                  const doc = job.documents[0];
                                  if (doc?.download_url) void download(job.id, doc.download_url, doc.original_filename);
                                }}
                              >
                                <Download size={17} />
                              </ActionIcon>
                            </Tooltip>
                          )}
                        {job.zip_url && (
                          <Tooltip label="Download ZIP">
                            <ActionIcon
                              variant="subtle"
                              aria-label="Download ZIP"
                              loading={busyKey === job.id}
                              onClick={() => void download(job.id, job.zip_url as string, "ocr-results.zip")}
                            >
                              <Download size={17} />
                            </ActionIcon>
                          </Tooltip>
                        )}
                        <Tooltip label="Delete">
                          <ActionIcon
                            variant="subtle"
                            color="red"
                            aria-label={`Delete ${job.title}`}
                            disabled={job.status === "processing"}
                            onClick={() => setPendingDelete(job)}
                          >
                            <Trash2 size={17} />
                          </ActionIcon>
                        </Tooltip>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                );
              })}
            </Table.Tbody>
          </Table>
        )}
      </section>

      <Modal opened={pendingDelete !== null} onClose={() => setPendingDelete(null)} title="Delete this job?" centered>
        <Text size="sm">
          &quot;{pendingDelete?.title}&quot; and its uploaded and generated files will be permanently removed.
        </Text>
        <Group justify="flex-end" mt="lg">
          <Button variant="default" onClick={() => setPendingDelete(null)}>
            Cancel
          </Button>
          <Button color="red" loading={deleteJob.isPending} onClick={confirmDelete}>
            Delete
          </Button>
        </Group>
      </Modal>
    </Stack>
  );
}
