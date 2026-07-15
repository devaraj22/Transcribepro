import { useEffect } from "react";
import apiClient from "../../services/apiClient";
import { formatDuration } from "../../utils/formatters";
import { useGlobalState } from "../../store/globalState";
import type { HistoryEntry } from "../../types";

interface Props {
  onSelect?: (entry: HistoryEntry) => void;
}

export default function HistoryPanel({ onSelect }: Props) {
  const { history, setHistory } = useGlobalState();

  useEffect(() => {
    apiClient.get<HistoryEntry[]>("/history").then(({ data }) => setHistory(data));
  }, [setHistory]);

  return (
    <div className="history-panel">
      <h5>Recent (max 5)</h5>
      {history.length === 0 && <p className="text-muted">No history yet.</p>}
      <ul>
        {history.map((entry) => (
          <li key={entry.id} onClick={() => onSelect?.(entry)}>
            <strong>{entry.title ?? "Untitled recording"}</strong>
            <span>{formatDuration(entry.duration_seconds)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
