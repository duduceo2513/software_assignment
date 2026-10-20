import { Alert, Button, Collapse, Group, Progress, Stack, Text } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { ChevronDown, ChevronUp, CircleAlert, Download, FileText } from "lucide-react";
import { StatusBadge } from "../../components/StatusBadge";
import type { OcrDocument } from "../../types/ocr";
import { formatBytes, formatDuration, languageLabel } from "./format";

interface Props {
  document: OcrDocument;
  downloading: boolean;
  onDownload: (document: OcrDocument) => void;
}

function ProgressSection({ document }: { document: OcrDocument }) {
  if (document.status === "pending") {
    return (
      <Stack gap={4}>
        <Progress value={100} color="gray" animated aria-label="Waiting in queue" />
        <Text size="xs" c="dimmed">
          Waiting in the queue for a free OCR worker...
        </Text>
      </Stack>
    );
  }
  const known = document.page_count > 0 && document.pages_processed > 0;
  return (
    <Stack gap={4}>
      <Progress
        value={known ? (document.pages_processed / document.page_count) * 100 : 100}
        animated={!known}
        striped={!known}
        aria-label="Recognition progress"
      />
      <Text size="xs" c="dimmed">
        {known
          ? `${document.pages_processed} of ${document.page_count} pages recognised`
          : `Preparing ${document.page_count} page${document.page_count === 1 ? "" : "s"} (first run loads the models)...`}
      </Text>
    </Stack>
  );
}

export function DocumentCard({ document, downloading, onDownload }: Props) {
  const [opened, { toggle }] = useDisclosure(false);
  const active = document.status === "pending" || document.status === "processing";

  return (
    <div className="oi-card" style={{ padding: 20 }}>
      <Group justify="space-between" wrap="nowrap" align="flex-start">
        <Group wrap="nowrap" gap="md" miw={0}>
          <div className={`oi-icon-tile${document.status === "completed" ? " success" : document.status === "failed" ? " danger" : ""}`}>
            <FileText size={22} aria-hidden />
          </div>
          <div style={{ minWidth: 0 }}>
            <Text fw={650} truncate>
              {document.original_filename}
            </Text>
            <Text size="sm" c="dimmed">
              {document.page_count} page{document.page_count === 1 ? "" : "s"} - {languageLabel(document.language)} -{" "}
              {formatBytes(document.file_size)}
              {document.status === "completed" && ` - ${formatDuration(document.processing_seconds)}`}
            </Text>
          </div>
        </Group>
        <StatusBadge status={document.status} />
      </Group>

      {active && (
        <div style={{ marginTop: 16 }}>
          <ProgressSection document={document} />
        </div>
      )}

      {document.status === "failed" && (
        <Alert mt="md" color="red" icon={<CircleAlert size={18} />} title="Processing failed">
          {document.error_message || "The document could not be processed."}
        </Alert>
      )}

      {document.status === "completed" && (
        <Stack mt="md" gap="sm">
          <Group justify="space-between">
            <Button
              variant="subtle"
              size="compact-sm"
              onClick={toggle}
              aria-expanded={opened}
              rightSection={opened ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            >
              {opened ? "Hide" : "Show"} recognised text
            </Button>
            <Button
              leftSection={<Download size={17} aria-hidden />}
              loading={downloading}
              disabled={!document.has_result}
              onClick={() => onDownload(document)}
            >
              Download DOCX
            </Button>
          </Group>
          <Collapse in={opened}>
            {document.text_preview ? (
              <div className="oi-preview" tabIndex={0} aria-label="Recognised text preview">
                {document.text_preview}
              </div>
            ) : (
              <Text size="sm" c="dimmed">
                No text was detected on this document.
              </Text>
            )}
          </Collapse>
        </Stack>
      )}
    </div>
  );
}
