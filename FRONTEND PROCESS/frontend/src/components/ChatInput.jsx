export default function ChatInput({
  message,
  setMessage,
  sendMessage,
  model,
  setModel,
}) {
  return (
    <div
      style={{
        width: "100%",
        maxWidth: "950px",
        margin: "0 auto",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          background: "#2f2f2f",
          border: "1px solid #3f3f3f",
          borderRadius: "30px",
          padding: "14px 18px",
          gap: "12px",
          boxShadow:
            "0 0 20px rgba(0,0,0,0.25)",
          width: "100%",
        }}
      >
        <input
          type="text"
          placeholder="Message Study AI..."
          value={message}
          onChange={(e) =>
            setMessage(e.target.value)
          }
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              sendMessage();
            }
          }}
          style={{
            flex: 1,
            background: "transparent",
            border: "none",
            outline: "none",
            color: "white",
            fontSize: "16px",
          }}
        />

        <select
          value={model}
          onChange={(e) =>
            setModel(e.target.value)
          }
          style={{
            background: "transparent",
            border: "none",
            color: "#d1d5db",
            cursor: "pointer",
            outline: "none",
            fontSize: "14px",
          }}
        >
          <option
            value="Qwen"
            style={{ color: "black" }}
          >
            Qwen
          </option>

          <option
            value="Llama"
            style={{ color: "black" }}
          >
            Llama
          </option>
        </select>

        <button
          onClick={sendMessage}
          style={{
            width: "46px",
            height: "46px",
            borderRadius: "50%",
            border: "none",
            background: "#ffffff",
            color: "#000",
            cursor: "pointer",
            fontWeight: "bold",
            fontSize: "18px",
            flexShrink: 0,
          }}
        >
          ↑
        </button>
      </div>
    </div>
  );
}
