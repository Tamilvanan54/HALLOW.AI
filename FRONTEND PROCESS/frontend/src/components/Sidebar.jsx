import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API_BASE_URL } from "../config/api";
import { FaUpload, FaTimes, FaCloudUploadAlt } from "react-icons/fa";

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

  // Post Document Modal State
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [department, setDepartment] = useState("CSE");
  const [year, setYear] = useState("3rd Year");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("email");
    localStorage.removeItem("activeChatId");
    navigate("/");
  };

  const handlePostDocument = async () => {
    if (!file) {
      alert("Please select a PDF document to upload!");
      return;
    }

    const formData = new FormData();
    formData.append("pdf", file);
    formData.append("department", department);
    formData.append("year", year);
    formData.append("uploaded_by", email);

    try {
      setUploading(true);
      setUploadStatus("Uploading & processing study material...");

      const response = await axios.post(`${API_BASE_URL}/upload-pdf`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      if (response.data && response.data.status === false) {
        alert(response.data.message || "Failed to upload document.");
      } else {
        alert(`Document posted successfully for ${department} - ${year}!`);
        setFile(null);
        setShowUploadModal(false);
        if (window.location.pathname === "/library") {
          window.location.reload();
        } else {
          navigate("/library");
        }
      }
    } catch (error) {
      console.error("POST DOCUMENT ERROR:", error);
      alert("Upload failed. Please check server connection.");
    } finally {
      setUploading(false);
      setUploadStatus("");
    }
  };

  return (
    <>
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
            src="/havox-full-logo.png"
            alt="HavoxAI"
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
            gap: "14px",
            marginTop: "15px",
          }}
        >
          <div
            onClick={() => navigate("/chat")}
            style={{ cursor: "pointer", display: "flex", alignItems: "center", gap: "8px" }}
          >
            💬 Chat
          </div>

          <div
            onClick={() => navigate("/library")}
            style={{ cursor: "pointer", display: "flex", alignItems: "center", gap: "8px" }}
          >
            📄 Library
          </div>

          {/* STAFF / ADMIN ONLY: POST DOCUMENT (LIBRARY) */}
          {(isAdmin || isStaff) && (
            <div
              onClick={() => setShowUploadModal(true)}
              style={{
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "8px 10px",
                background: "rgba(37, 99, 235, 0.2)",
                border: "1px solid #2563eb",
                borderRadius: "8px",
                color: "#60a5fa",
                fontWeight: "500",
                fontSize: "14px"
              }}
            >
              <FaUpload /> Post Document (Library)
            </div>
          )}

          {isAdmin && (
            <>
              <div
                onClick={() => navigate("/users")}
                style={{ cursor: "pointer", display: "flex", alignItems: "center", gap: "8px" }}
              >
                👥 Users
              </div>

              <div
                onClick={() => navigate("/logs")}
                style={{ cursor: "pointer", display: "flex", alignItems: "center", gap: "8px" }}
              >
                📊 Logs
              </div>
            </>
          )}

          {(isAdmin || isStaff) && (
            <div
              onClick={() => navigate("/feedback-review")}
              style={{ cursor: "pointer", display: "flex", alignItems: "center", gap: "8px" }}
            >
              📢 Feedback Review
            </div>
          )}

          <div
            onClick={() => navigate("/profile")}
            style={{ cursor: "pointer", display: "flex", alignItems: "center", gap: "8px" }}
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

      {/* POST DOCUMENT UPLOAD MODAL FOR STAFF / ADMIN */}
      {showUploadModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.75)",
            backdropFilter: "blur(4px)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 9999
          }}
        >
          <div
            style={{
              width: "440px",
              padding: "30px",
              borderRadius: "20px",
              background: "#171717",
              border: "1px solid #2f2f2f",
              boxShadow: "0px 0px 30px rgba(0,0,0,0.8)",
              position: "relative",
              color: "white"
            }}
          >
            <button
              onClick={() => setShowUploadModal(false)}
              style={{
                position: "absolute",
                right: "20px",
                top: "20px",
                background: "transparent",
                border: "none",
                color: "#9ca3af",
                fontSize: "18px",
                cursor: "pointer"
              }}
            >
              <FaTimes />
            </button>

            <h3 style={{ margin: "0 0 6px 0", fontSize: "18px", fontWeight: "600", color: "#38bdf8" }}>
              Post Document (Library)
            </h3>
            <p style={{ margin: "0 0 20px 0", fontSize: "13px", color: "#9ca3af" }}>
              Upload study material tailored to specific department & year
            </p>

            {/* SELECT DEPARTMENT */}
            <div style={{ marginBottom: "14px" }}>
              <label style={{ fontSize: "12px", color: "#9ca3af", display: "block", marginBottom: "4px" }}>
                Select Department
              </label>
              <select
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                style={{
                  width: "100%",
                  padding: "12px 14px",
                  background: "#262626",
                  color: "white",
                  border: "1px solid #404040",
                  borderRadius: "10px",
                  outline: "none"
                }}
              >
                <option value="CSE">CSE (Computer Science & Engg)</option>
                <option value="ECE">ECE (Electronics & Comm Engg)</option>
                <option value="EEE">EEE (Electrical & Electronics Engg)</option>
                <option value="MECH">MECH (Mechanical Engg)</option>
                <option value="IT">IT (Information Technology)</option>
                <option value="CIVIL">CIVIL (Civil Engg)</option>
                <option value="AIDS">AIDS (AI & Data Science)</option>
                <option value="AIML">AIML (AI & Machine Learning)</option>
                <option value="ALL">All Departments</option>
              </select>
            </div>

            {/* SELECT YEAR */}
            <div style={{ marginBottom: "18px" }}>
              <label style={{ fontSize: "12px", color: "#9ca3af", display: "block", marginBottom: "4px" }}>
                Select Year
              </label>
              <select
                value={year}
                onChange={(e) => setYear(e.target.value)}
                style={{
                  width: "100%",
                  padding: "12px 14px",
                  background: "#262626",
                  color: "white",
                  border: "1px solid #404040",
                  borderRadius: "10px",
                  outline: "none"
                }}
              >
                <option value="1st Year">1st Year</option>
                <option value="2nd Year">2nd Year</option>
                <option value="3rd Year">3rd Year</option>
                <option value="4th Year">4th Year</option>
                <option value="ALL">All Years</option>
              </select>
            </div>

            {/* FILE UPLOAD DROPBOX */}
            <div
              style={{
                border: "2px dashed #404040",
                borderRadius: "14px",
                padding: "25px",
                textAlign: "center",
                background: "#262626",
                marginBottom: "20px",
                cursor: "pointer"
              }}
              onClick={() => document.getElementById("post-doc-file-input").click()}
            >
              <FaCloudUploadAlt style={{ fontSize: "36px", color: "#3b82f6", marginBottom: "8px" }} />
              <div style={{ fontSize: "14px", fontWeight: "500" }}>
                {file ? file.name : "Click to select or drag PDF file"}
              </div>
              <div style={{ fontSize: "12px", color: "#9ca3af", marginTop: "4px" }}>
                PDF / DOC / DOCX (Max 50MB)
              </div>
              <input
                id="post-doc-file-input"
                type="file"
                accept=".pdf"
                style={{ display: "none" }}
                onChange={(e) => setFile(e.target.files[0])}
              />
            </div>

            {uploadStatus && (
              <div style={{ fontSize: "12px", color: "#38bdf8", marginBottom: "14px", textAlign: "center" }}>
                {uploadStatus}
              </div>
            )}

            {/* UPLOAD BUTTON */}
            <button
              onClick={handlePostDocument}
              disabled={uploading}
              style={{
                width: "100%",
                padding: "14px",
                borderRadius: "30px",
                border: "none",
                background: uploading ? "#4b5563" : "#2563eb",
                color: "white",
                fontWeight: "600",
                fontSize: "15px",
                cursor: uploading ? "not-allowed" : "pointer"
              }}
            >
              {uploading ? "Uploading..." : "Upload Document"}
            </button>
          </div>
        </div>
      )}
    </>
  );
}
