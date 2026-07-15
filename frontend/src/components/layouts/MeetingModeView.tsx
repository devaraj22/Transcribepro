import { useState } from "react";
import apiClient from "../../services/apiClient";
import { useJobPolling } from "../../hooks/useJobPolling";
import { useGlobalState } from "../../store/globalState";
import FileUploader from "../forms/FileUploader";
import LanguageSelector from "../forms/LanguageSelector";
import ProgressBar from "../ui/ProgressBar";
import TextEditor from "../ui/TextEditor";
import ChatWidget from "../ui/ChatWidget";
import HistoryPanel from "../ui/HistoryPanel";
import { downloadTextFile } from "../../utils/formatters";
import type { LanguageMode, ProcessResponse } from "../../types";

export default function MeetingModeView() {
  const { transcript, setTranscript, currentJobId, setCurrentJobId } = useGlobalState();
  const [file, setFile] = useState<File | null>(null);
  const [languageMode, setLanguageMode] = useState<LanguageMode>("automatic");
  const [manualLanguage, setManualLanguage] = useState("");
  const [statusMessage, setStatusMessage] = useState("");

  const jobStatus = useJobPolling(currentJobId);
  const isComplete = jobStatus?.status === "complete";

  const handleSubmit = async () => {
    if (!file) {
      setStatusMessage("Please choose a file first.");
      return;
    }
    const form = new FormData();
    form.append("upload_file", file);
    form.append("language_mode", languageMode);
    form.append("manual_language", manualLanguage);

    const { data } = await apiClient.post<ProcessResponse>("/process", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    if (data.job_id) {
      setCurrentJobId(data.job_id);
      setStatusMessage(`Processing meeting recording: ${data.job_id}`);
    } else {
      setStatusMessage("Processing complete.");
    }
  };

  const loadResult = async () => {
    if (!currentJobId) return;
    const { data } = await apiClient.get(`/process/${currentJobId}/result`);
    setTranscript(data.transcript ?? "");
  };

  const handleDownloadReport = () => {
    if (!currentJobId) return;
    window.open(`${apiClient.defaults.baseURL}/report/${currentJobId}`, "_blank");
  };

  if (isComplete && !transcript) {
    loadResult();
  }

  return (
    <div className="meeting-mode">
      <div className="meeting-mode__column">
        <section className="card">
          <h4>Meeting Upload</h4>
          <FileUploader onFileSelected={setFile} />
          <LanguageSelector
            mode={languageMode}
            manualLanguage={manualLanguage}
            onModeChange={setLanguageMode}
            onManualLanguageChange={setManualLanguage}
          />
          <button className="btn btn--warning" onClick={handleSubmit}>
            Submit
          </button>
          <ProgressBar
            percent={jobStatus?.percent_complete ?? 0}
            visible={!!currentJobId && !isComplete}
            label={jobStatus?.current_step}
          />
          <p className="status-text">{statusMessage}</p>
        </section>

        <section className="card">
          <h4>Transcript</h4>
          <TextEditor value={transcript} onChange={setTranscript} />
          <div className="card__row">
            <button className="btn btn--secondary" onClick={() => downloadTextFile(transcript)}>
              Download Transcript
            </button>
            <button className="btn btn--primary" onClick={handleDownloadReport} disabled={!isComplete}>
              Download PDF Report
            </button>
          </div>
        </section>

        <ChatWidget jobId={currentJobId} />
      </div>

      <div className="meeting-mode__column meeting-mode__column--sidebar">
        <HistoryPanel
          onSelect={(entry) => {
            setTranscript(entry.transcript);
            setCurrentJobId(entry.job_id);
          }}
        />
      </div>
    </div>
  );
}
