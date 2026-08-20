import { useState } from "react";
import axios from "axios";
import { API_BASE_URL } from "../config/api";

const formatMathText = (text) => {
  if (!text || !text.trim()) return "";
  let formatted = text;

  // Defensive check: strip any residual raw SSE protocol string if unparsed
  formatted = formatted.replace(/^event:\s*\w+\s*\n+data:\s*\{.*?\}/gis, "");
  formatted = formatted.replace(/(?:\n|^)data:\s*\{"token":"(.*?)"\}/gi, "$1");

  // Deduplicate any repeated ### Example headings
  formatted = formatted.replace(/(?:\n*\s*###?\s*(?:Example|[A-Za-z0-9_\s]*Example):?\s*)+/gi, "\n\n### Example\n");

  // Convert LaTeX fractions and square roots to clean readable notation
  formatted = formatted.replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, "($1)/($2)");
  formatted = formatted.replace(/\\sqrt\{([^}]+)\}/g, "√($1)");
  formatted = formatted.replace(/\\sqrt\s*([a-zA-Z0-9]+)/g, "√$1");
  formatted = formatted.replace(/\\text\{([^}]+)\}/g, "$1");
  formatted = formatted.replace(/\\mathrm\{([^}]+)\}/g, "$1");

  // Convert LaTeX math symbols to Unicode
  formatted = formatted
    .replace(/\\pm/g, "±")
    .replace(/\\sqrt/g, "√")
    .replace(/\\infty/g, "∞")
    .replace(/\\mathbb\{R\}/g, "ℝ")
    .replace(/\\cdot/g, "·")
    .replace(/\\times/g, "×")
    .replace(/\\div/g, "÷")
    .replace(/\\geq/g, "≥")
    .replace(/\\leq/g, "≤")
    .replace(/\\neq/g, "≠")
    .replace(/\\Rightarrow/g, "⇒")
    .replace(/\\Leftrightarrow/g, "⇔")
    .replace(/\^2/g, "²")
    .replace(/\^3/g, "³");

  // Force step headings and Example onto separate lines with clean spacing
  formatted = formatted.replace(/([^\n])\s*(###?\s*Step|\bStep\s+\d+:)/g, "$1\n\n$2");
  formatted = formatted.replace(/([^\n])\s*(###?\s*Final Answer:|\bFinal Answer:)/g, "$1\n\n$2");

  return formatted.trim();
};

export default function ChatWindow({ messages }) {
  const [openMenu, setOpenMenu] = useState(null);
  const [copied, setCopied] = useState(false);
  const [feedbackSaved, setFeedbackSaved] = useState(false);

  const copyMessage = (text) => {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).catch(() => fallbackCopy(text));
    } else {
      fallbackCopy(text);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const fallbackCopy = (text) => {
    try {
      const textArea = document.createElement("textarea");
      textArea.value = text;
      textArea.style.position = "fixed";
      textArea.style.left = "-999999px";
      textArea.style.top = "-999999px";
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      document.execCommand("copy");
      document.body.removeChild(textArea);
    } catch (e) {
      console.error("Copy failed:", e);
    }
  };

  const reportAnswer = async (question, answer) => {
    try {
      const reported_by = localStorage.getItem("email");
      const response = await axios.post(`${API_BASE_URL}/feedback`, null, {
        params: {
          question,
          answer,
          feedback: "Incorrect Answer",
          reported_by
        }
      });
      setFeedbackSaved(true);
      setTimeout(() => setFeedbackSaved(false), 2000);
    } catch (error) {
      console.error("FEEDBACK ERROR:", error);
      alert("Feedback Failed");
    }
  };

  return (
    <div
      style={{
        flex: 1,
        overflowY: "auto",
        padding: "30px",
        width: "100%",
        boxSizing: "border-box",
      }}
    >
      {copied && (
        <div
          style={{
            position: "fixed",
            bottom: "100px",
            left: "50%",
            transform: "translateX(-50%)",
            background: "#2f2f2f",
            color: "white",
            padding: "10px 18px",
            borderRadius: "10px",
            border: "1px solid #444",
            zIndex: 9999,
            fontSize: "14px",
          }}
        >
          ✓ Copied
        </div>
      )}

      {feedbackSaved && (
        <div
          style={{
            position: "fixed",
            bottom: "150px",
            left: "50%",
            transform: "translateX(-50%)",
            background: "#2f2f2f",
            color: "white",
            padding: "10px 18px",
            borderRadius: "10px",
            border: "1px solid #444",
            zIndex: 9999,
            fontSize: "14px",
          }}
        >
          ✓ Feedback Saved
        </div>
      )}

      {messages.map((msg, index) => (
        <div
          key={index}
          style={{
            marginBottom: "25px",
            display: "flex",
            flexDirection: "column",
            alignItems: msg.sender === "User" ? "flex-end" : "flex-start",
          }}
        >
          <div
            style={{
              fontSize: "13px",
              color: "#9ca3af",
              marginBottom: "6px",
            }}
          >
            {msg.sender === "User" ? "You" : "HALLOW.AI"}
          </div>

          <div
            style={{
              background: msg.sender === "User" ? "#303030" : "transparent",
              padding: msg.sender === "User" ? "14px 18px" : "0px",
              borderRadius: msg.sender === "User" ? "20px" : "0px",
              maxWidth: "95%",
              color: "white",
              fontSize: "15px",
              lineHeight: "1.8",
              wordBreak: "break-word",
              whiteSpace: "pre-wrap",
              position: "relative",
            }}
          >
            {msg.sender === "AI" ? (
              <>
                {/* 1. Typo Correction Indicator - displayed ONLY when corrected_query or displayNote exists */}
                {(msg.displayNote || msg.correctedQuery) && (
                  <div
                    style={{
                      display: "inline-block",
                      marginBottom: "10px",
                      padding: "4px 10px",
                      background: "#1e293b",
                      color: "#38bdf8",
                      borderRadius: "6px",
                      fontSize: "13px",
                      fontWeight: "500",
                      border: "1px solid #0284c7"
                    }}
                  >
                    🔍 {msg.displayNote || `Searching for: ${msg.correctedQuery}`}
                  </div>
                )}

                {/* 2. Streaming Status Indicator */}
                {msg.streaming && msg.statusText && !msg.text && (
                  <div
                    style={{
                      color: "#38bdf8",
                      fontStyle: "italic",
                      fontSize: "14px",
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      marginBottom: "8px"
                    }}
                  >
                    <span style={{ animation: "spin 1s linear infinite" }}>⚡</span>
                    {msg.statusText}
                  </div>
                )}

                {/* 3. Refusal Card or Clean Answer Text */}
                {msg.confidence === "refused" ? (
                  <div
                    style={{
                      background: "#262626",
                      borderLeft: "4px solid #ef4444",
                      padding: "16px",
                      borderRadius: "8px",
                      marginTop: "6px",
                      color: "#f3f4f6"
                    }}
                  >
                    <div style={{ fontWeight: "600", color: "#f87171", marginBottom: "4px" }}>
                      Document Restricted Response
                    </div>
                    {msg.text || "I can answer only from the uploaded study materials. I could not find enough relevant information in the available documents for this question."}
                  </div>
                ) : (
                  msg.text || msg.streaming ? (
                    <>
                      {formatMathText(msg.text)}
                      {msg.streaming && (
                        <span
                          style={{
                            display: "inline-block",
                            width: "8px",
                            height: "15px",
                            marginLeft: "4px",
                            backgroundColor: "#38bdf8",
                            verticalAlign: "middle",
                            borderRadius: "2px"
                          }}
                        />
                      )}
                    </>
                  ) : (
                    <span style={{ color: "#9ca3af", fontStyle: "italic" }}>
                      Searching uploaded study materials…
                    </span>
                  )
                )}

                {/* 4. Expandable Sources Card - displayed ONLY after final response completes (streaming === false) */}
                {!msg.streaming && msg.sources && msg.sources.length > 0 && (
                  <div
                    style={{
                      marginTop: "16px",
                      padding: "12px 14px",
                      background: "#1e1e1e",
                      borderRadius: "10px",
                      border: "1px solid #333"
                    }}
                  >
                    <div style={{ fontWeight: "600", fontSize: "13px", color: "#38bdf8", marginBottom: "8px" }}>
                      Sources ({msg.sources.length})
                    </div>
                    {msg.sources.map((s, sIdx) => (
                      <details key={sIdx} style={{ marginBottom: "6px", fontSize: "13px", color: "#d1d5db" }}>
                        <summary style={{ cursor: "pointer", fontWeight: "500" }}>
                          • {s.document} — Page {s.page}
                        </summary>
                        {s.snippet && (
                          <div style={{ marginTop: "4px", padding: "6px 10px", background: "#111111", borderRadius: "6px", fontSize: "12px", color: "#9ca3af", fontStyle: "italic" }}>
                            "{s.snippet}"
                          </div>
                        )}
                      </details>
                    ))}
                  </div>
                )}
              </>
            ) : (
              msg.text
            )}

            {/* Menu options for AI answers */}
            {msg.sender === "AI" && msg.text && (
              <div
                style={{
                  display: "flex",
                  gap: "12px",
                  marginTop: "10px",
                  alignItems: "center",
                }}
              >
                <button
                  onClick={() => copyMessage(msg.text)}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "#9ca3af",
                    cursor: "pointer",
                    fontSize: "16px",
                  }}
                  title="Copy response"
                >
                  ⧉
                </button>

                <button
                  onClick={() => setOpenMenu(openMenu === index ? null : index)}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "#9ca3af",
                    cursor: "pointer",
                    fontSize: "18px",
                  }}
                >
                  ⋮
                </button>

                {openMenu === index && (
                  <div
                    style={{
                      background: "#2f2f2f",
                      border: "1px solid #444",
                      borderRadius: "10px",
                      padding: "8px",
                    }}
                  >
                    <div
                      onClick={() =>
                        reportAnswer(
                          index > 0 ? messages[index - 1]?.text : "",
                          msg.text
                        )
                      }
                      style={{
                        cursor: "pointer",
                        color: "#ef4444",
                        fontSize: "14px",
                      }}
                    >
                      Report Incorrect Answer
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
