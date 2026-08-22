import { useNavigate } from "react-router-dom";


export default function Sidebar({
  chatHistory = [],
  startNewChat,
  deleteChat,
  selectChat,
  openChat,
  togglePin,
  currentChatId
}) {
  const navigate = useNavigate();

  const role = (localStorage.getItem("role") || "").toLowerCase().trim();
  const email = localStorage.getItem("email") || "";

  const isAdmin = role === "admin";
  const isStaff = role === "staff";

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("email");
    localStorage.removeItem("activeChatId");
    navigate("/");
  };

  return (
    <div
      className="desktop-sidebar"
      style={{
        width: "260px",
        height: "100vh",
        background: "#171717",
        color: "white",
        display: "flex",
        flexDirection: "column",
        padding: "15px",
        borderRight: "1px solid #2f2f2f",
        boxSizing: "border-box",
        flexShrink: 0
      }}
    >
      {/* LOGO */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: "20px",
          padding: "5px 0",
        }}
      >
        <img
          src="/hallow-full-logo.png"
          alt="HALLOW.AI"
          style={{
            height: "48px",
            width: "auto",
            maxWidth: "100%",
            objectFit: "contain",
          }}
        />
      </div>

      {/* NEW CHAT */}
      <button
        onClick={startNewChat}
        style={{
          padding: "12px",
          background: "#2f2f2f",
          color: "white",
          borderRadius: "8px",
          border: "1px solid #404040",
          cursor: "pointer",
          marginBottom: "20px",
          fontWeight: "500",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "8px"
        }}
      >
        ✏️ New Chat
      </button>

      <h4
        style={{
          textAlign: "center",
          color: "#9ca3af",
          marginBottom: "10px",
          fontSize: "14px"
        }}
      >
        Recent Chats
      </h4>

      <div
        style={{
          flex: 1,
          overflowY: "auto",
        }}
      >
        {chatHistory.length === 0 ? (
          <p
            style={{
              color: "#9ca3af",
              textAlign: "center",
              fontSize: "13px"
            }}
          >
            No chats yet
          </p>
        ) : (
          chatHistory.map((chat) => {
            const chatId = chat.id || chat._id;
            const isSelected = String(currentChatId) === String(chatId);
            return (
              <div
                key={chatId}
                onClick={() => {
                  const handleSelect = selectChat || openChat;
                  if (handleSelect) handleSelect(chatId);
                }}
                style={{
                  background: isSelected ? "#3a3a3a" : (chat.pinned ? "#2a2a2a" : "#2f2f2f"),
                  border: isSelected ? "1px solid #38bdf8" : (chat.pinned ? "1px solid #4b5563" : "1px solid transparent"),
                  padding: "10px 12px",
                  borderRadius: "8px",
                  marginBottom: "8px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  cursor: "pointer"
                }}
              >
                <span
                  style={{
                    fontSize: "14px",
                    color: isSelected ? "#38bdf8" : "white",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    maxWidth: "145px"
                  }}
                >
                  💬 {chat.title}
                </span>

                <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                  <span
                    onClick={(e) => {
                      e.stopPropagation();
                      if (togglePin) togglePin(chatId);
                    }}
                    style={{
                      cursor: "pointer",
                      color: chat.pinned ? "#e5e7eb" : "#6b7280",
                      fontSize: "14px"
                    }}
                    title={chat.pinned ? "Unpin chat" : "Pin chat"}
                  >
                    📎
                  </span>

                  <span
                    onClick={(e) => {
                      e.stopPropagation();
                      if (deleteChat) deleteChat(chatId);
                    }}
                    style={{
                      cursor: "pointer",
                      color: "#ef4444",
                      fontSize: "14px"
                    }}
                    title="Delete chat"
                  >
                    🗑
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* MENU */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "18px",
          marginTop: "15px",
        }}
      >
        <div
          onClick={() => navigate("/chat")}
          style={{ cursor: "pointer" }}
        >
          💬 Chat
        </div>

        <div
          onClick={() => navigate("/library")}
          style={{ cursor: "pointer" }}
        >
          📄 Library
        </div>

        {isAdmin && (
          <>
            <div
              onClick={() => navigate("/users")}
              style={{ cursor: "pointer" }}
            >
              👥 Users
            </div>

            <div
              onClick={() => navigate("/logs")}
              style={{ cursor: "pointer" }}
            >
              📊 Logs
            </div>
          </>
        )}

        {(isAdmin || isStaff) && (
          <div
            onClick={() => navigate("/feedback-review")}
            style={{ cursor: "pointer" }}
          >
            📢 Feedback Review
          </div>
        )}

        <div
          onClick={() => navigate("/profile")}
          style={{ cursor: "pointer" }}
        >
          👤 Profile
        </div>
      </div>

      {/* USER INFO */}
      <div
        style={{
          borderTop: "1px solid #404040",
          marginTop: "15px",
          paddingTop: "15px",
          textAlign: "center",
        }}
      >
        <p style={{ margin: "0 0 4px 0", fontSize: "14px" }}>
          👤 {email}
        </p>

        <p
          style={{
            color: "#9ca3af",
            margin: "0 0 10px 0",
            fontSize: "12px"
          }}
        >
          {role}
        </p>

        <button
          onClick={logout}
          style={{
            width: "100%",
            padding: "10px",
            background: "#2f2f2f",
            color: "white",
            border: "1px solid #404040",
            borderRadius: "8px",
            cursor: "pointer",
            fontWeight: "500",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "6px"
          }}
        >
          → Logout
        </button>
      </div>
    </div>

  );

}
