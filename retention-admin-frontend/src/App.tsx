import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/layout/AppLayout";
import { Dashboard } from "@/pages/Dashboard";
import { PendingMessagesPage } from "@/pages/PendingMessagesPage";
import { RetentionCandidatesPage } from "@/pages/RetentionCandidatesPage";
import { SyncControlsPage } from "@/pages/SyncControlsPage";
import { OperationsControlCenterPage } from "@/pages/OperationsControlCenterPage";
import { MessagePreviewPage } from "@/pages/MessagePreviewPage";
import { TestSendPage } from "@/pages/TestSendPage";
import { DemoHomePage } from "@/pages/DemoHomePage";
import { Toaster } from "@/components/ui/toaster";
import { DEMO_MODE } from "@/constants";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={DEMO_MODE ? <DemoHomePage /> : <Dashboard />} />
          {!DEMO_MODE ? <Route path="candidates" element={<RetentionCandidatesPage />} /> : null}
          {!DEMO_MODE ? <Route path="pending" element={<PendingMessagesPage />} /> : null}
          {!DEMO_MODE ? <Route path="sync" element={<SyncControlsPage />} /> : null}
          {!DEMO_MODE ? <Route path="operations" element={<OperationsControlCenterPage />} /> : null}
          <Route path="test-send" element={<TestSendPage />} />
          <Route path="message-preview" element={<MessagePreviewPage />} />
          <Route path="demo/test-send" element={<TestSendPage />} />
          <Route path="demo" element={<DemoHomePage />} />
          <Route
            path="*"
            element={
              <Navigate
                to={DEMO_MODE ? "/demo" : "/"}
                replace
                state={
                  DEMO_MODE
                    ? { notice: "Этот раздел недоступен в демонстрационной версии" }
                    : undefined
                }
              />
            }
          />
        </Route>
      </Routes>
      <Toaster />
    </BrowserRouter>
  );
}
