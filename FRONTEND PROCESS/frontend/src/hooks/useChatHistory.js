import { useState, useEffect } from "react";
import axios from "axios";

export default function useChatHistory() {

  const email = localStorage.getItem("email");

  const [chatHistory, setChatHistory] = useState([]);

  // =========================
  // LOAD CHATS
  // =========================

  useEffect(() => {

    if (email) {
      fetchChats();
    }

  }, [email]);

  const fetchChats = async () => {

    try {

      const response = await axios.get(
        "http://127.0.0.1:8000/get-chats",
        {
          params: {
            email
          }
        }
      );

      const chats = response.data || [];

      const formatted = chats.map((chat) => ({
        id: chat.id,
        title: chat.title,
        pinned: chat.pinned === "true"
      }));

      formatted.sort((a, b) => {

        if (a.pinned && !b.pinned) return -1;

        if (!a.pinned && b.pinned) return 1;

        return b.id - a.id;

      });

      setChatHistory(formatted);

    }
    catch (error) {

      console.error(
        "GET CHATS ERROR:",
        error
      );

    }

  };

  // =========================
  // CREATE CHAT
  // =========================

  const addChat = async (title) => {

    try {

      const response = await axios.post(
        "http://127.0.0.1:8000/save-chat",
        null,
        {
          params: {
            email,
            title
          }
        }
      );

      console.log(
        "SAVE CHAT RESPONSE:",
        response.data
      );

      const newChat = {

        id: response.data.id,

        title: response.data.title,

        pinned: response.data.pinned === "true"

      };

      setChatHistory((prev) => {

        const updated = [
          newChat,
          ...prev
        ];

        updated.sort((a, b) => {

          if (a.pinned && !b.pinned)
            return -1;

          if (!a.pinned && b.pinned)
            return 1;

          return b.id - a.id;

        });

        return updated;

      });

      return newChat;

    }
    catch (error) {

      console.error(
        "SAVE CHAT ERROR:",
        error
      );

      return null;

    }

  };

  // =========================
  // DELETE CHAT
  // =========================

  const deleteChat = async (id) => {

    try {

      await axios.delete(
        "http://127.0.0.1:8000/delete-chat",
        {
          params: {
            chat_id: id
          }
        }
      );

      setChatHistory((prev) =>
        prev.filter(
          (chat) => chat.id !== id
        )
      );

    }
    catch (error) {

      console.error(
        "DELETE CHAT ERROR:",
        error
      );

    }

  };

  // =========================
  // PIN / UNPIN CHAT
  // =========================

  const togglePin = async (id) => {

    try {

      console.log("PIN CLICKED:", id);

      const response = await axios.put(
        "http://127.0.0.1:8000/pin-chat",
        null,
        {
          params: {
            chat_id: id
          }
        }
      );

      console.log(
        "PIN RESPONSE:",
        response.data
      );

      setChatHistory((prev) => {

        const updated = prev.map((chat) =>

          chat.id === id
            ? {
                ...chat,
                pinned: !chat.pinned
              }
            : chat

        );

        updated.sort((a, b) => {

          if (a.pinned && !b.pinned)
            return -1;

          if (!a.pinned && b.pinned)
            return 1;

          return b.id - a.id;

        });

        return updated;

      });

    }
    catch (error) {

      console.error(
        "PIN ERROR:",
        error
      );

    }

  };

  return {

    chatHistory,

    addChat,

    deleteChat,

    togglePin,

    fetchChats

  };

}