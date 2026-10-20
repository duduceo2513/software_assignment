import { Badge } from "@mantine/core";
import { CheckCircle2, CircleAlert, Clock, Loader } from "lucide-react";
import { STATUS_META } from "../features/ocr/format";
import type { DocumentStatus, JobStatus } from "../types/ocr";

const ICONS = {
  pending: Clock,
  processing: Loader,
  completed: CheckCircle2,
  failed: CircleAlert,
  partially_completed: CircleAlert,
} as const;

export function StatusBadge({ status }: { status: JobStatus | DocumentStatus }) {
  const meta = STATUS_META[status];
  const Icon = ICONS[status];
  return (
    <Badge color={meta.color} variant="light" size="md" leftSection={<Icon size={13} aria-hidden />}>
      {meta.label}
    </Badge>
  );
}
