import { useAudioRecorder } from "../../hooks/useAudioRecorder";

interface Props {
  onRecorded: (file: File) => void;
}

export default function AudioRecorder({ onRecorded }: Props) {
  const { isRecording, audioFile, startRecording, stopRecording } = useAudioRecorder();

  if (audioFile) onRecorded(audioFile);

  return (
    <button
      type="button"
      className={`btn ${isRecording ? "btn--danger" : "btn--primary"}`}
      onClick={isRecording ? stopRecording : startRecording}
    >
      {isRecording ? "Stop Recording" : "Record Audio"}
    </button>
  );
}
