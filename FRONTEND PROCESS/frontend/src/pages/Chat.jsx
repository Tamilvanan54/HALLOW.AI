import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { API_BASE_URL, RAG_BASE_URL } from "../config/api";

import MobileSidebar from "../components/MobileSidebar";
import ChatWindow from "../components/ChatWindow";
import ChatInput from "../components/ChatInput";

import useChatHistory from "../hooks/useChatHistory";

export default function Chat() {
  const [message, setMessage] = useState("");
  const [model, setModel] = useState("Qwen");
  const [messages, setMessages] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const chatContainerRef = useRef(null);
  const abortControllerRef = useRef(null);

  const {
    chatHistory,
    addChat,
    deleteChat,
    togglePin
  } = useChatHistory();

  useEffect(() => {
    localStorage.removeItem("activeChatId");
  }, []);

  // AUTO SCROLL
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  // NEW CHAT
  const startNewChat = () => {
    setMessages([]);
    setCurrentChatId(null);
    setMessage("");
    localStorage.removeItem("activeChatId");
  };

  // DELETE CHAT
  const handleDeleteChat = (chatId) => {
    deleteChat(chatId);
    if (currentChatId === chatId) {
      startNewChat();
    }
  };

  // SELECT CHAT
  const selectChat = async (chatId) => {
    setCurrentChatId(chatId);
    localStorage.setItem("activeChatId", String(chatId));

    try {
      const response = await axios.get(`${API_BASE_URL}/get-messages`, {
        params: { session_id: chatId }
      });

      if (response.data.status && Array.isArray(response.data.messages)) {
        const formattedMessages = response.data.messages.map((m) => ({
          sender: m.sender === "user" ? "User" : "AI",
          text: m.message,
          streaming: false
        }));
        setMessages(formattedMessages);
      } else {
        setMessages([]);
      }
    } catch (error) {
      console.error("Failed to load chat messages:", error);
      setMessages([]);
    }
  };

  // STOP GENERATION
  const stopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsGenerating(false);
      setMessages((prev) => {
        const updated = [...prev];
        if (updated.length > 0 && updated[updated.length - 1].sender === "AI") {
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            streaming: false,
            text: updated[updated.length - 1].text || "Generation cancelled."
          };
        }
        return updated;
      });
    }
  };

  // SEND MESSAGE WITH COMPLIANT SSE STREAM PARSER
  const sendMessage = async () => {
    if (!message.trim() || isGenerating) return;

    const currentMessage = message;
    setMessage("");
    setIsGenerating(true);

    let chatId = currentChatId;

    if (!chatId) {
      const title = currentMessage.slice(0, 30);
      chatId = await addChat(title);
      if (!chatId) {
        setIsGenerating(false);
        return;
      }
      setCurrentChatId(chatId);
      localStorage.setItem("activeChatId", String(chatId));
    }

    setMessages((prev) => [
      ...prev,
      { sender: "User", text: currentMessage },
      {
        sender: "AI",
        text: "",
        streaming: true,
        statusText: "Searching uploaded study materials…",
        displayNote: null,
        correctedQuery: null,
        sources: [],
        confidence: "grounded"
      }
    ]);

    // Save user message in background
    axios.post(`${API_BASE_URL}/save-message`, null, {
      params: {
        session_id: chatId,
        sender: "User",
        message: currentMessage
      }
    }).catch((e) => console.error("Failed to save user message:", e));

    let recentHistory = "";
    if (Array.isArray(messages) && messages.length > 0) {
      recentHistory = messages
        .slice(-4)
        .filter((m) => m && m.text && typeof m.text === "string" && !m.text.includes("cannot find information"))
        .map((m) => `${m.sender === "User" ? "User" : "Assistant"}: ${m.text.slice(0, 150)}`)
        .join("\n");
    }

    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(`${RAG_BASE_URL}/api/query/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: abortControllerRef.current.signal,
        body: JSON.stringify({
          query: currentMessage,
          history: recentHistory,
          model_name: (model === "Llama" || model === "Llama 3.2") ? "llama3.2:1b" : "qwen2.5:1.5b"
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let fullTargetText = "";
      let currentSources = [];
      let displayNote = null;
      let correctedQuery = null;
      let confidence = "grounded";
      let statusText = "Searching uploaded study materials…";
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        // Split complete events using blank lines (\n\n or \r\n\r\n)
        const events = buffer.split(/\r?\n\r?\n/);
        buffer = events.pop() || "";

        for (const evt of events) {
          if (!evt.trim()) continue;
          const lines = evt.split(/\r?\n/);
          let eventType = "token";
          let dataStr = "";

          for (const line of lines) {
            if (line.startsWith("event:")) {
              eventType = line.slice(6).trim();
            } else if (line.startsWith("data:")) {
              const payloadLine = line.slice(5).trim();
              dataStr += dataStr ? "\n" + payloadLine : payloadLine;
            }
          }

          if (!dataStr) continue;

          try {
            const payload = JSON.parse(dataStr);

            if (eventType === "status") {
              statusText = payload.message || "Searching uploaded study materials…";
            } else if (eventType === "meta") {
              if (payload.display_note) displayNote = payload.display_note;
              if (payload.corrected_query !== undefined) correctedQuery = payload.corrected_query;
              if (payload.sources) currentSources = payload.sources;
            } else if (eventType === "token") {
              const token = payload.token ?? payload.text ?? "";
              if (token) {
                fullTargetText += token;
                statusText = null; // hide status indicator as soon as first token arrives
              }
            } else if (eventType === "final") {
              if (payload.answer) fullTargetText = payload.answer;
              if (payload.sources) currentSources = payload.sources;
              if (payload.confidence) confidence = payload.confidence;
              if (payload.display_note) displayNote = payload.display_note;
              if (payload.corrected_query !== undefined) correctedQuery = payload.corrected_query;
            }
          } catch (pErr) {
            console.warn("Invalid SSE JSON payload:", dataStr, pErr);
          }

          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              sender: "AI",
              text: fullTargetText,
              streaming: true,
              statusText: statusText,
              displayNote: displayNote,
              correctedQuery: correctedQuery,
              sources: currentSources,
              confidence: confidence
            };
            return updated;
          });
        }
      }

      if (!fullTargetText || !fullTargetText.trim()) {
        fullTargetText = "I can answer only from the uploaded study materials. I could not find enough relevant information in the available documents for this question.";
        confidence = "refused";
      }

      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          sender: "AI",
          text: fullTargetText,
          streaming: false,
          statusText: null,
          displayNote: displayNote,
          correctedQuery: correctedQuery,
          sources: currentSources,
          confidence: confidence
        };
        return updated;
      });

      // Save AI answer in database
      if (fullTargetText && fullTargetText.trim()) {
        axios.post(`${API_BASE_URL}/save-message`, null, {
          params: {
            session_id: chatId,
            sender: "AI",
            message: fullTargetText
          }
        }).catch((e) => console.error("Failed to save AI message:", e));
      }

    } catch (error) {
      if (error.name !== "AbortError") {
        console.error("CHAT ERROR:", error);
        setMessages((prev) => {
          const updated = [...prev];
          if (updated.length > 0 && updated[updated.length - 1].sender === "AI") {
            updated[updated.length - 1] = {
              sender: "AI",
              text: "I can answer only from the uploaded study materials. I could not find enough relevant information in the available documents for this question.",
              streaming: false,
              confidence: "refused"
            };
          }
          return updated;
        });
      }
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div style={{ display: "flex", height: "100vh", width: "100vw", background: "#212121", overflow: "hidden" }}>
      <MobileSidebar
        chatHistory={chatHistory}
        startNewChat={startNewChat}
        selectChat={selectChat}
        deleteChat={handleDeleteChat}
        togglePin={togglePin}
        currentChatId={currentChatId}
      />

      <div style={{ flex: 1, display: "flex", flexDirection: "column", background: "#212121", position: "relative" }}>
        <div ref={chatContainerRef} style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column" }}>
          <ChatWindow messages={messages} />
        </div>

        <div style={{ padding: "15px 20px", background: "#212121" }}>
          <ChatInput
            message={message}
            setMessage={setMessage}
            sendMessage={sendMessage}
            model={model}
            setModel={setModel}
            isGenerating={isGenerating}
            stopGeneration={stopGeneration}
          />
        </div>
      </div>
    </div>
  );
}
