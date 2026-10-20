import { Button, Stack, Text, Title } from "@mantine/core";
import { FileSearch, ServerOff } from "lucide-react";
import type { ReactNode } from "react";

export function EmptyState({ title, message, action }: { title: string; message: string; action?: ReactNode }) {
  return (
    <Stack align="center" gap="xs" py={48} className="oi-fade-in">
      <div className="oi-icon-tile">
        <FileSearch size={22} aria-hidden />
      </div>
      <Title order={4}>{title}</Title>
      <Text c="dimmed" size="sm" ta="center" maw={380}>
        {message}
      </Text>
      {action}
    </Stack>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message = error instanceof Error ? error.message : "Something went wrong.";
  return (
    <Stack align="center" gap="xs" py={48} role="alert">
      <div className="oi-icon-tile danger">
        <ServerOff size={22} aria-hidden />
      </div>
      <Title order={4}>Could not load data</Title>
      <Text c="dimmed" size="sm" ta="center" maw={420}>
        {message}
      </Text>
      {onRetry && (
        <Button variant="light" onClick={onRetry} mt="xs">
          Try again
        </Button>
      )}
    </Stack>
  );
}
