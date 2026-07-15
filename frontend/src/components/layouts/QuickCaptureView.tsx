import { useState } from "react";
import apiClient from "../../services/apiClient";
import { useJobPolling } from "../../hooks/useJobPolling";
import { useGlobalState } from "../../store/globalState";
import FileUploader from "../forms/FileUploader";
import AudioRecorder from "../forms/AudioRecorder";
import LanguageSelector from "../forms/LanguageSelector";
import ProgressBar from "../ui/ProgressBar";
import TextEditor from "../ui/TextEditor";
import { buildWhatsAppLink, downloadTextFile } from "../../utils/formatters";
import type { LanguageMode, ProcessResponse } from "../../types";

export default function QuickCaptureView() {
  const { transcript, setTranscript, currentJobId, setCurrentJobId } = useGlobalState();
  const [file, setFile] = useState<File | null>(null);
  const [languageMode, setLanguageMode] = useState<LanguageMode>("automatic");
  const [manualLanguage, setManualLanguage] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [enhancementOutput, setEnhancementOutput] = useState<string>("");

  const jobStatus = useJobPolling(currentJobId);

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
      setStatusMessage(`Processing long recording: ${data.job_id}`);
    } else {
      setStatusMessage("Processing complete.");
    }
  };

  const handleCleanup = async () => {
    const { data } = await apiClient.post("/enhance/cleanup", { text: transcript });
    setTranscript(data.text);
  };

  const handleSummarize = async () => {
    const { data } = await apiClient.post("/enhance/summarize", { text: transcript });
    setEnhancementOutput(data.summary);
  };

  const handleActionItems = async () => {
    const { data } = await apiClient.post("/enhance/action-items", { text: transcript });
    setEnhancementOutput(data.items.join("\n• "));
  };

  const handleTitle = async () => {
    const { data } = await apiClient.post("/enhance/title", { text: transcript });
    setEnhancementOutput(data.title);
  };

  return (
    <div className="view-stack">
      <section className="card">
        <h4>Quick Capture</h4>
        <div className="card__row">
          <AudioRecorder onRecorded={setFile} />
        </div>
      </section>

      <section className="card">
        <h4>Upload / Record Input</h4>
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
          visible={!!currentJobId && jobStatus?.status !== "complete"}
          label={jobStatus?.current_step}
        />
        <p className="status-text">{statusMessage}</p>
      </section>

      <section className="card">
        <h4>Transcript</h4>
        <TextEditor value={transcript} onChange={setTranscript} />
        <div className="card__row">
          <button className="btn btn--success" onClick={() => window.open(buildWhatsAppLink(transcript), "_blank")}>
            Share to WhatsApp
          </button>
          <button className="btn btn--secondary" onClick={() => downloadTextFile(transcript)}>
            Download Transcript
          </button>
        </div>
      </section>

      <section className="card">
        <h5>Enhancements</h5>
        <div className="card__row">
          <button className="btn btn--secondary" onClick={handleCleanup}>Clean Up</button>
          <button className="btn btn--secondary" onClick={handleSummarize}>Summarize</button>
          <button className="btn btn--secondary" onClick={handleActionItems}>Action Items</button>
          <button className="btn btn--secondary" onClick={handleTitle}>Auto Title</button>
        </div>
        <div className="enhancement-output">{enhancementOutput}</div>
      </section>
    </div>
  );
}
