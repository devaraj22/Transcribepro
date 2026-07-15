import { createContext, useContext, useState, type ReactNode } from "react";
import type { AppMode, HistoryEntry } from "../types";

interface GlobalState {
  mode: AppMode;
  setMode: (mode: AppMode) => void;
  transcript: string;
  setTranscript: (text: string) => void;
  currentJobId: string | null;
  setCurrentJobId: (jobId: string | null) => void;
  history: HistoryEntry[];
  setHistory: (entries: HistoryEntry[]) => void;
}

const GlobalStateContext = createContext<GlobalState | undefined>(undefined);

export function GlobalStateProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<AppMode>("quick");
  const [transcript, setTranscript] = useState("");
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  const value: GlobalState = {
    mode,
    setMode,
    transcript,
    setTranscript,
    currentJobId,
    setCurrentJobId,
    history,
    setHistory,
  };

  return <GlobalStateContext.Provider value={value}>{children}</GlobalStateContext.Provider>;
}

export function useGlobalState() {
  const ctx = useContext(GlobalStateContext);
  if (!ctx) throw new Error("useGlobalState must be used within GlobalStateProvider");
  return ctx;
}
