import { useEffect, useRef, useState } from "react";
import apiClient from "../services/apiClient";
import type { JobStatus } from "../types";

export function useJobPolling(jobId: string | null, intervalMs = 3000) {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const timer = useRef<number | null>(null);

  useEffect(() => {
    if (!jobId) {
      setStatus(null);
      return;
    }

    const poll = async () => {
      try {
        const { data } = await apiClient.get<JobStatus>(`/process/${jobId}/status`);
        setStatus(data);
        if (data.status === "complete" || data.status === "error") {
          if (timer.current) window.clearInterval(timer.current);
        }
      } catch {
        if (timer.current) window.clearInterval(timer.current);
      }
    };

    poll();
    timer.current = window.setInterval(poll, intervalMs);
    return () => {
      if (timer.current) window.clearInterval(timer.current);
    };
  }, [jobId, intervalMs]);

  return status;
}
