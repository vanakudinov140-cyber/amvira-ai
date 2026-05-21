import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/layout/AppLayout";
import { Dashboard } from "@/pages/Dashboard";
import { PendingMessagesPage } from "@/pages/PendingMessagesPage";
import { RetentionCandidatesPage } from "@/pages/RetentionCandidatesPage";
import { SyncControlsPage } from "@/pages/SyncControlsPage";
import { OperationsControlCenterPage } from "@/pages/OperationsControlCenterPage";
import { Toaster } from "@/components/ui/toaster";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="candidates" element={<RetentionCandidatesPage />} />
          <Route path="pending" element={<PendingMessagesPage />} />
          <Route path="sync" element={<SyncControlsPage />} />
          <Route path="operations" element={<OperationsControlCenterPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
      <Toaster />
    </BrowserRouter>
  );
}
