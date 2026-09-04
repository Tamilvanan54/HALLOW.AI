export default function ModelSelector({ model, setModel }) {
  return (
    <select
      value={model}
      onChange={(e) => setModel(e.target.value)}
      style={{
        padding: "10px",
        borderRadius: "8px",
        background: "#2f2f2f",
        color: "white",
        border: "1px solid #404040",
      }}
    >
      <option value="Qwen">Qwen 2.5 (3B)</option>
      <option value="Llama">Llama 3.2 (3B)</option>
    </select>
  );
}
