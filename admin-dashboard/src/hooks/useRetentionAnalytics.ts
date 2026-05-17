import { useCallback, useState } from "react";
import {
  fetchAutomationSettings,
  fetchAiPerformance,
  fetchModerationInsights,
  fetchRetentionOverview,
  fetchSchedulerStatus,
} from "@/api/retention";
import { getErrorMessage } from "@/api/client";
import { toast } from "@/hooks/use-toast";
import type {
  AutomationSettings,
  AiPerformance,
  ModerationInsights,
  RetentionOverview,
  SchedulerStatus,
} from "@/types/api";

export function useRetentionAnalytics() {
  const [overview, setOverview] = useState<RetentionOverview | null>(null);
  const [scheduler, setScheduler] = useState<SchedulerStatus | null>(null);
  const [automation, setAutomation] = useState<AutomationSettings | null>(null);
  const [insights, setInsights] = useState<ModerationInsights | null>(null);
  const [aiPerformance, setAiPerformance] = useState<AiPerformance | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [overviewData, schedulerData, automationData, insightsData, aiPerfData] =
        await Promise.all([
        fetchRetentionOverview(),
        fetchSchedulerStatus(),
        fetchAutomationSettings(),
        fetchModerationInsights(),
        fetchAiPerformance(),
      ]);
      setOverview(overviewData);
      setScheduler(schedulerData);
      setAutomation(automationData);
      setInsights(insightsData);
      setAiPerformance(aiPerfData);
    } catch (err) {
      toast({
        title: "Ошибка загрузки аналитики",
        description: getErrorMessage(err),
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, []);

  return { overview, scheduler, automation, insights, aiPerformance, loading, load };
}
