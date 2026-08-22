import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { API_BASE_URL, RAG_BASE_URL } from "../config/api";

import MobileSidebar from "../components/MobileSidebar";
import Sidebar from "../components/Sidebar";
import ChatWindow from "../components/ChatWindow";
import ChatInput from "../components/ChatInput";

import useChatHistory from "../hooks/useChatHistory";

const cleanAnswerText = (text) => {
  if (!text) return "";
  let cleaned = text.trim();
  // Normalize duplicate example headings into a single ### Example heading
  cleaned = cleaned.replace(/(?:\n*\s*###?\s*(?:Example|[A-Za-z0-9_\s]*Example):?\s*)+/gi, "\n\n### Example\n");
  return cleaned;
};

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

  const userMessageRefs = useRef({});

  // AUTO SCROLL - Align scroll to the START of the current user question / response block
  useEffect(() => {
    if (!messages || !messages.length) return;

    // Find index of the most recent User question
    let lastUserIndex = -1;
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i] && messages[i].sender === "User") {
        lastUserIndex = i;
        break;
      }
    }

    if (lastUserIndex !== -1 && userMessageRefs.current[lastUserIndex]) {
      userMessageRefs.current[lastUserIndex].scrollIntoView({
        behavior: "smooth",
        block: "start"
      });
    } else if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages.length, messages[messages.length - 1]?.text]);

  // NEW CHAT
  const startNewChat = () => {
    setMessages([]);
    setCurrentChatId(null);
    setMessage("");
    userMessageRefs.current = {};
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
  const selectChat = async (chatOrId) => {
    let rawId = typeof chatOrId === "object" ? (chatOrId.id || chatOrId._id || chatOrId.session_id) : chatOrId;
    if (!rawId) return;

    const chatId = parseInt(rawId, 10);
    if (isNaN(chatId)) return;

    setCurrentChatId(chatId);
    localStorage.setItem("activeChatId", String(chatId));

    try {
      const response = await axios.get(`${API_BASE_URL}/get-messages`, {
        params: { session_id: chatId }
      });

      const rawList = Array.isArray(response.data)
        ? response.data
        : (response.data?.messages || response.data?.data || []);

      if (Array.isArray(rawList)) {
        const formattedMessages = rawList.map((m) => ({
          sender: (m.sender && (m.sender.toLowerCase() === "user" || m.sender === "You")) ? "User" : "AI",
          text: m.text || m.message || "",
          streaming: false,
          status: false
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
            status: false,
            text: updated[updated.length - 1].text || "Generation cancelled."
          };
        }
        return updated;
      });
    }
  };

  // Helper to update only the current/last AI message in React state
  const updateCurrentAiMessage = (fields) => {
    setMessages((prev) => {
      if (!prev.length) return prev;
      const updated = [...prev];
      const lastIndex = updated.length - 1;
      if (updated[lastIndex].sender === "AI") {
        updated[lastIndex] = {
          ...updated[lastIndex],
          ...fields
        };
      }
      return updated;
    });
  };

  // SEND MESSAGE WITH W3C-COMPLIANT SSE STREAM ACCUMULATOR
  const sendMessage = async () => {
    if (!message.trim() || isGenerating) return;

    const currentMessage = message;
    setMessage("");
    setIsGenerating(true);

    let chatId = currentChatId;

    if (!chatId) {
      const title = currentMessage.slice(0, 30);
      const createdChat = await addChat(title);
      if (!createdChat) {
        setIsGenerating(false);
        return;
      }
      const rawNewId = typeof createdChat === "object" ? (createdChat.id || createdChat._id || createdChat.session_id) : createdChat;
      chatId = parseInt(rawNewId, 10);
      setCurrentChatId(chatId);
      localStorage.setItem("activeChatId", String(chatId));
    }

    // Initialize AI message state with EMPTY text during searching phase
    setMessages((prev) => [
      ...prev,
      { sender: "User", text: currentMessage },
      {
        sender: "AI",
        text: "",
        streaming: true,
        status: true,
        statusText: "Searching uploaded study materials…",
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
        console.error(`RAG API returned status ${response.status}`);
        updateCurrentAiMessage({
          text: "I can answer only from the uploaded study materials. I could not find enough relevant information in the available documents for this question.",
          streaming: false,
          status: false,
          confidence: "refused"
        });
        setIsGenerating(false);
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      let buffer = "";
      let currentAnswer = "";
      let sources = [];
      let correctedQuery = null;
      let currentEventName = null;
      let currentDataLines = [];

      const processSingleSseEvent = (eventName, dataStr) => {
        if (!dataStr) return;

        // Intercept any HTML error pages (e.g. 502 Bad Gateway) from Nginx
        if (dataStr.startsWith("<") || dataStr.includes("<html>") || dataStr.includes("502 Bad Gateway")) {
          console.warn("Received HTML error page from server:", dataStr);
          updateCurrentAiMessage({
            text: "I can answer only from the uploaded study materials. I could not find enough relevant information in the available documents for this question.",
            streaming: false,
            status: false,
            confidence: "refused"
          });
          return;
        }

        let payload;
        try {
          payload = JSON.parse(dataStr);
        } catch (e) {
          console.warn("Invalid SSE JSON payload ignored:", dataStr, e);
          return;
        }

        if (eventName === "status") {
          updateCurrentAiMessage({
            text: "",
            streaming: true,
            status: true,
            statusText: payload.message || "Searching uploaded study materials…",
            sources: []
          });
        } else if (eventName === "meta") {
          sources = payload.sources || sources;
          correctedQuery = payload.corrected_query || payload.display_note || correctedQuery;
          updateCurrentAiMessage({
            streaming: true,
            status: true,
            statusText: "Searching uploaded study materials…",
            correctedQuery: correctedQuery,
            sources: sources
          });
        } else if (eventName === "token") {
          const token = payload.token ?? payload.text ?? "";
          if (token) {
            currentAnswer += token;
            updateCurrentAiMessage({
              text: currentAnswer,
              streaming: true,
              status: false,
              statusText: null
            });
          }
        } else if (eventName === "final") {
          currentAnswer = cleanAnswerText(payload.answer || currentAnswer);
          sources = payload.sources || sources;
          correctedQuery = payload.corrected_query || payload.display_note || correctedQuery;

          updateCurrentAiMessage({
            text: currentAnswer,
            streaming: false,
            status: false,
            statusText: null,
            sources: sources,
            correctedQuery: correctedQuery,
            confidence: payload.confidence || "grounded",
            refusalReason: payload.refusal_reason
          });
        }
      };

      while (true) {
        const { value, done } = await reader.read();

        if (value) {
          buffer += decoder.decode(value, { stream: true });

          const lines = buffer.split(/\r?\n/);
          // Keep incomplete trailing line in buffer
          buffer = lines.pop() || "";

          for (const line of lines) {
            const trimmed = line.trim();

            if (trimmed.startsWith("event:")) {
              currentEventName = trimmed.slice(6).trim();
            } else if (trimmed.startsWith("data:")) {
              currentDataLines.push(trimmed.slice(5).trim());
            } else if (trimmed === "") {
              // Blank line signifies boundary of an SSE event block
              if (currentDataLines.length > 0) {
                const dataStr = currentDataLines.join("\n");
                const eventName = currentEventName || "message";

                processSingleSseEvent(eventName, dataStr);

                currentEventName = null;
                currentDataLines = [];
              }
            }
          }
        }

        if (done) break;
      }

      // Process any remaining event in buffer after stream ends
      if (currentDataLines.length > 0) {
        const dataStr = currentDataLines.join("\n");
        const eventName = currentEventName || "message";
        processSingleSseEvent(eventName, dataStr);
      }

      if (!currentAnswer || !currentAnswer.trim()) {
        currentAnswer = "I can answer only from the uploaded study materials. I could not find enough relevant information in the available documents for this question.";
      }

      currentAnswer = cleanAnswerText(currentAnswer);

      updateCurrentAiMessage({
        text: currentAnswer,
        streaming: false,
        status: false,
        statusText: null,
        sources: sources,
        correctedQuery: correctedQuery
      });

      // Save AI answer in database
      if (currentAnswer && currentAnswer.trim()) {
        axios.post(`${API_BASE_URL}/save-message`, null, {
          params: {
            session_id: chatId,
            sender: "AI",
            message: currentAnswer
          }
        }).catch((e) => console.error("Failed to save AI message:", e));
      }

    } catch (error) {
      if (error.name !== "AbortError") {
        console.error("CHAT ERROR:", error);
        updateCurrentAiMessage({
          text: "I can answer only from the uploaded study materials. I could not find enough relevant information in the available documents for this question.",
          streaming: false,
          status: false,
          confidence: "refused"
        });
      }
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div style={{ display: "flex", height: "100vh", width: "100vw", background: "#212121", overflow: "hidden" }}>
      <Sidebar
        chatHistory={chatHistory}
        startNewChat={startNewChat}
        selectChat={selectChat}
        openChat={selectChat}
        deleteChat={handleDeleteChat}
        togglePin={togglePin}
        currentChatId={currentChatId}
      />
      <MobileSidebar
        chatHistory={chatHistory}
        startNewChat={startNewChat}
        selectChat={selectChat}
        openChat={selectChat}
        deleteChat={handleDeleteChat}
        togglePin={togglePin}
        currentChatId={currentChatId}
      />

      <div style={{ flex: 1, display: "flex", flexDirection: "column", background: "#212121", position: "relative" }}>
        <div ref={chatContainerRef} style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column" }}>
          <ChatWindow messages={messages} userMessageRefs={userMessageRefs} />
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
