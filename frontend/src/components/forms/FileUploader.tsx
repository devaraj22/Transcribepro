import { useState, type DragEvent } from "react";

interface Props {
  onFileSelected: (file: File) => void;
}

export default function FileUploader({ onFileSelected }: Props) {
  const [fileName, setFileName] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFiles = (files: FileList | null) => {
    const file = files?.[0];
    if (file) {
      setFileName(file.name);
      onFileSelected(file);
    }
  };

  const handleDrop = (e: DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  return (
    <label
      className={`upload-box ${isDragging ? "upload-box--dragging" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
    >
      {fileName ?? "Drag and drop or click to select an audio/video file"}
      <input type="file" accept="audio/*,video/*" hidden onChange={(e) => handleFiles(e.target.files)} />
    </label>
  );
}
