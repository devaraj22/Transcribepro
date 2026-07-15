import type { LanguageMode } from "../../types";

const LANGUAGES = ["en", "es", "fr", "de", "hi", "zh", "ja"];

interface Props {
  mode: LanguageMode;
  manualLanguage: string;
  onModeChange: (mode: LanguageMode) => void;
  onManualLanguageChange: (lang: string) => void;
}

export default function LanguageSelector({ mode, manualLanguage, onModeChange, onManualLanguageChange }: Props) {
  return (
    <div className="language-selector">
      <div>
        <span className="field-label">Language Mode</span>
        <div className="radio-group">
          <label>
            <input type="radio" checked={mode === "automatic"} onChange={() => onModeChange("automatic")} />
            Automatic
          </label>
          <label>
            <input type="radio" checked={mode === "manual"} onChange={() => onModeChange("manual")} />
            Manual
          </label>
        </div>
      </div>
      <div>
        <span className="field-label">Manual Language</span>
        <select
          disabled={mode !== "manual"}
          value={manualLanguage}
          onChange={(e) => onManualLanguageChange(e.target.value)}
        >
          <option value="">Select...</option>
          {LANGUAGES.map((lang) => (
            <option key={lang} value={lang}>
              {lang}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
