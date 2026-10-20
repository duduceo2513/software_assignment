import { Button, Group, Skeleton, Stack, Text, Title } from "@mantine/core";
import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import { StatusBadge } from "../components/StatusBadge";
import { EmptyState, ErrorState } from "../components/States";
import { UploadPanel } from "../features/ocr/UploadPanel";
import { formatDate } from "../features/ocr/format";
import { useJobs } from "../hooks/useJobs";

const CHIPS = ["PaddleOCR", "PP-StructureV3", "Kazakh", "Russian", "English", "PDF", "TIFF", "DOCX"];

function Console() {
  return (
    <div className="oi-console" aria-hidden>
      <div className="oi-console-bar">
        <i />
        <i />
        <i />
        <span>engine.config.ts</span>
      </div>
      <div className="oi-console-body">
        <div>
          <span className="ln">1</span>
          <span className="c">{"// Current OCR Intelligence pipeline"}</span>
        </div>
        <div>
          <span className="ln">2</span>
          <span className="k">export const</span> pipeline = {"{"}
        </div>
        <div>
          <span className="ln">3</span>&nbsp;&nbsp;layout: <span className="s">&quot;PP-StructureV3&quot;</span>,
        </div>
        <div>
          <span className="ln">4</span>&nbsp;&nbsp;recognition: <span className="s">&quot;cyrillic_PP-OCRv5&quot;</span>,
        </div>
        <div>
          <span className="ln">5</span>&nbsp;&nbsp;output: <span className="s">&quot;editable .docx&quot;</span>,
        </div>
        <div>
          <span className="ln">6</span>&nbsp;&nbsp;device: <span className="s">&quot;cpu&quot;</span>,
        </div>
        <div>
          <span className="ln">7</span>
          {"}"} <span className="c">as const;</span>
        </div>
      </div>
    </div>
  );
}

function Stats() {
  const { data } = useJobs(500);
  const jobs = data ?? [];
  const documents = jobs.flatMap((job) => job.documents);
  const cells = [
    { value: jobs.length, label: "Jobs" },
    { value: documents.length, label: "Documents" },
    { value: documents.filter((d) => d.status === "completed").length, label: "Converted to DOCX" },
    { value: documents.filter((d) => d.status === "completed").reduce((sum, d) => sum + d.page_count, 0), label: "Pages recognised" },
  ];
  return (
    <div className="oi-stats" aria-label="Usage statistics">
      {cells.map(({ value, label }) => (
        <div className="oi-stat" key={label}>
          <b>{data ? value : "-"}</b>
          <span>{label}</span>
        </div>
      ))}
    </div>
  );
}

function RecentJobs() {
  const { data, isLoading, error, refetch } = useJobs(5);

  if (isLoading) {
    return (
      <Stack gap="sm">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} height={56} />
        ))}
      </Stack>
    );
  }
  if (error) return <ErrorState error={error} onRetry={() => void refetch()} />;
  if (!data || data.length === 0) {
    return <EmptyState title="No documents yet" message="Upload your first scan to see it appear here." />;
  }
  return (
    <Stack gap="xs">
      {data.map((job) => (
        <Link key={job.id} to={`/jobs/${job.id}`} style={{ textDecoration: "none", color: "inherit" }}>
          <Group className="oi-card interactive" p="sm" wrap="nowrap" justify="space-between">
            <div style={{ minWidth: 0 }}>
              <Text fw={600} size="sm" truncate>
                {job.title}
              </Text>
              <Text size="xs" c="dimmed">
                {formatDate(job.created_at)}
              </Text>
            </div>
            <StatusBadge status={job.status} />
          </Group>
        </Link>
      ))}
    </Stack>
  );
}

export function WorkspacePage() {
  return (
    <Stack gap={56}>
      <section className="oi-hero oi-fade-in">
        <div>
          <div className="oi-eyebrow">Document recognition</div>
          <h1 className="oi-display">
            OCR <em>Intelligence</em>
          </h1>
          <Text mt="lg" c="dimmed" size="lg" maw={520} lh={1.6}>
            Turns scanned PDFs and images in Kazakh, Russian and English into editable Word documents - paragraphs,
            headings and real tables, recognised locally.
          </Text>
          <Group mt="xl" gap="sm">
            <Button size="md" component="a" href="#upload">
              Start recognition
            </Button>
            <Button size="md" variant="default" component={Link} to="/history">
              View history
            </Button>
          </Group>
          <Group mt="xl" gap={8}>
            {CHIPS.map((chip) => (
              <span className="oi-chip" key={chip}>
                {chip}
              </span>
            ))}
          </Group>
        </div>
        <Console />
      </section>

      <Stats />

      <div
        id="upload"
        style={{ display: "grid", gridTemplateColumns: "minmax(0, 1.7fr) minmax(280px, 1fr)", gap: 32, scrollMarginTop: 80 }}
      >
        <section aria-labelledby="upload-title">
          <Title order={3} id="upload-title" mb={4}>
            New recognition
          </Title>
          <Text c="dimmed" size="sm" mb="lg">
            Upload one or two documents and choose the language.
          </Text>
          <UploadPanel />
        </section>
        <section aria-labelledby="recent-title" style={{ alignSelf: "start" }}>
          <div className="oi-section-title">
            <Title order={3} id="recent-title">
              Recent
            </Title>
            <Link to="/history" style={{ textDecoration: "none", color: "var(--oi-accent)", fontSize: "0.88rem", fontWeight: 600 }}>
              View all <ArrowRight size={13} style={{ verticalAlign: "-2px" }} aria-hidden />
            </Link>
          </div>
          <Text c="dimmed" size="sm" mb="lg">
            Latest jobs on this server
          </Text>
          <RecentJobs />
        </section>
      </div>
    </Stack>
  );
}
