import Header from "../common/Header";
import Footer from "../common/Footer";
import QuickCaptureView from "./QuickCaptureView";
import MeetingModeView from "./MeetingModeView";
import { useGlobalState } from "../../store/globalState";

export default function AppLayout() {
  const { mode, setMode } = useGlobalState();

  return (
    <div className="app-container">
      <Header />
      <main className="app-main">
        <div className="mode-selector">
          <label>
            <input type="radio" checked={mode === "quick"} onChange={() => setMode("quick")} />
            Quick Capture
          </label>
          <label>
            <input type="radio" checked={mode === "meeting"} onChange={() => setMode("meeting")} />
            Meeting Mode
          </label>
        </div>
        {mode === "quick" ? <QuickCaptureView /> : <MeetingModeView />}
      </main>
      <Footer />
    </div>
  );
}
