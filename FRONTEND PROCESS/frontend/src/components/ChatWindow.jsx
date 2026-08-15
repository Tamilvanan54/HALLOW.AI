import { useState } from "react";
import axios from "axios";

const formatMathText = (text) => {
  if (!text) return "";
  let formatted = text;

  // Convert LaTeX fractions and square roots
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
    .replace(/\\mathbb\{Q\}/g, "ℚ")
    .replace(/\\mathbb\{Z\}/g, "ℤ")
    .replace(/\\R/g, "ℝ")
    .replace(/\\cdot/g, "·")
    .replace(/\\times/g, "×")
    .replace(/\\div/g, "÷")
    .replace(/\\geq/g, "≥")
    .replace(/\\leq/g, "≤")
    .replace(/\\neq/g, "≠")
    .replace(/\\Rightarrow/g, "⇒")
    .replace(/\\Leftrightarrow/g, "⇔")
    .replace(/\\iff/g, "⇔")
    .replace(/\\quad/g, " ")
    .replace(/\\\)/g, "")
    .replace(/\\\]/g, "")
    .replace(/\\\(/g, "")
    .replace(/\\\[/g, "")
    .replace(/\^2/g, "²")
    .replace(/\^3/g, "³");

  // Force step headings onto separate lines with blank line spacing
  formatted = formatted.replace(/([^\n])\s*(###?\s*Step|\bStep\s+\d+:)/g, "$1\n\n$2");
  formatted = formatted.replace(/([^\n])\s*(\bFinal Answer:)/g, "$1\n\n$2");
  formatted = formatted.replace(/([^\n])\s*(\bVerification\b)/g, "$1\n\n$2");

  return formatted;
};

export default function ChatWindow({
  messages,
}) {

  const [openMenu, setOpenMenu] =
    useState(null);

  const [copied, setCopied] =
    useState(false);

    const [feedbackSaved, setFeedbackSaved] =
  useState(false);

  const copyMessage = (text) => {

    navigator.clipboard.writeText(
      text
    );

    setCopied(true);

    setTimeout(() => {

      setCopied(false);

    }, 2000);
  };

 const reportAnswer = async (
  question,
  answer
) => {

  try {

    const reported_by =
      localStorage.getItem("email");

    const response =
      await axios.post(
        "http://127.0.0.1:8000/feedback",
        null,
        {
          params: {
            question,
            answer,
            feedback:
              "Incorrect Answer",
            reported_by
          }
        }
      );

    console.log(
      "FEEDBACK SAVED:",
      response.data
    );

   setFeedbackSaved(true);

setTimeout(() => {

  setFeedbackSaved(false);

}, 2000);

  } catch (error) {

    console.error(
      "FEEDBACK ERROR:",
      error
    );

    alert(
      "Feedback Failed"
    );
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
            transform:
              "translateX(-50%)",
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
      transform:
        "translateX(-50%)",
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

      {messages.map(
        (msg, index) => (

          <div
            key={index}
            style={{
              marginBottom: "25px",
              display: "flex",
              flexDirection: "column",
              alignItems:
                msg.sender === "User"
                  ? "flex-end"
                  : "flex-start",
            }}
          >
            <div
              style={{
                fontSize: "13px",
                color: "#9ca3af",
                marginBottom: "6px",
              }}
            >
              {msg.sender === "User"
                ? "You"
                : "HALLOW.AI"}
            </div>

            <div
              style={{
                background:
                  msg.sender === "User"
                    ? "#303030"
                    : "transparent",

                padding:
                  msg.sender === "User"
                    ? "14px 18px"
                    : "0px",

                borderRadius:
                  msg.sender === "User"
                    ? "20px"
                    : "0px",

                maxWidth: "95%",

                color: "white",

                fontSize: "15px",

                lineHeight: "1.8",

                wordBreak:
                  "break-word",

                whiteSpace:
                  "pre-wrap",

                position:
                  "relative",
              }}
            >
              {msg.sender === "AI" ? formatMathText(msg.text) : msg.text}

              {msg.sender ===
                "AI" && (

                <div
                  style={{
                    display: "flex",
                    gap: "12px",
                    marginTop: "10px",
                    alignItems:
                      "center",
                  }}
                >
                  <button
                    onClick={() =>
                      copyMessage(
                        msg.text
                      )
                    }
                    style={{
                      background:
                        "transparent",
                      border:
                        "none",
                      color:
                        "#9ca3af",
                      cursor:
                        "pointer",
                      fontSize:
                        "16px",
                    }}
                  >
                    ⧉
                  </button>

                  <button
                    onClick={() =>
                      setOpenMenu(
                        openMenu ===
                          index
                          ? null
                          : index
                      )
                    }
                    style={{
                      background:
                        "transparent",
                      border:
                        "none",
                      color:
                        "#9ca3af",
                      cursor:
                        "pointer",
                      fontSize:
                        "18px",
                    }}
                  >
                    ⋮
                  </button>

                  {openMenu ===
                    index && (

                    <div
                      style={{
                        background:
                          "#2f2f2f",
                        border:
                          "1px solid #444",
                        borderRadius:
                          "10px",
                        padding:
                          "8px",
                      }}
                    >
                      <div
                        onClick={() =>
                          reportAnswer(
                            index > 0
                              ? messages[
                                  index - 1
                                ]?.text
                              : "",
                            msg.text
                          )
                        }
                        style={{
                          cursor:
                            "pointer",
                          color:
                            "#ef4444",
                          fontSize:
                            "14px",
                        }}
                      >
                        Report Incorrect
                        Answer
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )
      )}
    </div>
  );
}