import { Route, Routes } from "react-router-dom";
import { AppLayout } from "./layouts/AppLayout";
import { HistoryPage } from "./pages/HistoryPage";
import { JobPage } from "./pages/JobPage";
import { WorkspacePage } from "./pages/WorkspacePage";
import { EmptyState } from "./components/States";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<WorkspacePage />} />
        <Route path="jobs/:jobId" element={<JobPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="*" element={<EmptyState title="Page not found" message="This page does not exist." />} />
      </Route>
    </Routes>
  );
}
