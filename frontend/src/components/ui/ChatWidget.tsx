import { useState } from "react";
import apiClient from "../../services/apiClient";
import type { AskResponse } from "../../types";

interface Props {
  jobId: string | null;
}

interface ChatMessage {
  question: string;
  answer: string;
  sources: string[];
}

export default function ChatWidget({ jobId }: Props) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);

  const handleAsk = async () => {
    if (!jobId || !question.trim()) return;
    setLoading(true);
    try {
      const { data } = await apiClient.post<AskResponse>("/ask", { job_id: jobId, question });
      setMessages((prev) => [...prev, { question, answer: data.answer, sources: data.sources }]);
      setQuestion("");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-widget">
      <h5>Ask about this transcript</h5>
      <div className="chat-widget__messages">
        {messages.map((msg, i) => (
          <div key={i} className="chat-widget__message">
            <p className="chat-widget__question">Q: {msg.question}</p>
            <p className="chat-widget__answer">{msg.answer}</p>
            {msg.sources.length > 0 && (
              <p className="chat-widget__sources">Sources: {msg.sources.join(", ")}</p>
            )}
          </div>
        ))}
      </div>
      <div className="chat-widget__input-row">
        <input
          type="text"
          value={question}
          disabled={!jobId}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAsk()}
          placeholder={jobId ? "Ask a question about this recording..." : "Process a recording first"}
        />
        <button className="btn btn--secondary" onClick={handleAsk} disabled={!jobId || loading}>
          {loading ? "Asking..." : "Ask"}
        </button>
      </div>
    </div>
  );
}
