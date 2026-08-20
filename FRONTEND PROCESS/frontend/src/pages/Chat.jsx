import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { API_BASE_URL, RAG_BASE_URL } from "../config/api";

import MobileSidebar from "../components/MobileSidebar";
import ChatWindow from "../components/ChatWindow";
import ChatInput from "../components/ChatInput";

import useChatHistory from "../hooks/useChatHistory";


export default function Chat() {


  const [message,setMessage] =
  useState("");


  const [model,setModel] =
useState("Qwen");


  const [messages,setMessages] =
  useState([]);


  const [currentChatId,setCurrentChatId] =
  useState(null);


  const chatContainerRef =
  useRef(null);



  const {
  chatHistory,
  addChat,
  deleteChat,
  togglePin,
  fetchChats
} = useChatHistory();

useEffect(() => {

  localStorage.removeItem(
    "activeChatId"
  );

}, []);



  // AUTO SCROLL

  useEffect(()=>{


    if(chatContainerRef.current){

      chatContainerRef.current.scrollTop =
      chatContainerRef.current.scrollHeight;

    }


  },[messages]);







  // NEW CHAT

const startNewChat = ()=>{

setMessages([]);

setCurrentChatId(null);

setMessage("");

localStorage.removeItem(
"activeChatId"
);

};







  // DELETE CHAT

  const handleDeleteChat = (chatId)=>{


    deleteChat(chatId);



    if(currentChatId === chatId){


      setMessages([]);


      setCurrentChatId(null);


      setMessage("");

    }


  };







  // OPEN OLD CHAT

  const openChat = async(chat)=>{


    try{


      const response = await axios.get(

        `${API_BASE_URL}/get-messages`,

        {

          params:{

            session_id:chat.id

          }

        }

      );




      const formattedMessages =

      response.data.map((msg)=>({


        sender:

        msg.sender.toLowerCase() === "user"

        ?

        "User"

        :

        "AI",



        text:

        msg.message || msg.text


      }));





      setMessages(formattedMessages);



      setCurrentChatId(chat.id);



      setMessage("");



    }


    catch(error){


      console.error(

        "LOAD CHAT ERROR:",

        error

      );


    }


  };










  // SEND MESSAGE

  const sendMessage = async()=>{


    if(!message.trim())

      return;




    const currentMessage = message;



    // CLEAR INPUT

    setMessage("");





    let chatId = currentChatId || localStorage.getItem("activeChatId");






    // CREATE CHAT IF NEW
    if (!chatId) {
      const title = currentMessage.length > 25
        ? currentMessage.substring(0, 25) + "..."
        : currentMessage;
      const newChat = await addChat(title);
      fetchChats(); // Fetch chats list in background without blocking stream start

      if (!newChat || !newChat.id) {
        console.error("CHAT CREATE FAILED");
        return;
      }

      chatId = newChat.id;
      setCurrentChatId(chatId);
      localStorage.setItem("activeChatId", String(chatId));
    }

    // Capture recent chat history before appending current message
    const historyPayload = messages.slice(-6).map((m) => ({
      sender: m.sender,
      text: m.text
    }));

    // Immediately show User message AND AI Thinking placeholder at 0ms
    setMessages((prev) => [
      ...prev,
      {
        sender: "User",
        text: currentMessage
      },
      {
        sender: "AI",
        text: ""
      }
    ]);

    try {
      // Save user message in background without blocking stream start
      if (chatId) {
        axios.post(
          `${API_BASE_URL}/save-message`,
          null,
          {
            params: {
              session_id: chatId,
              sender: "User",
              message: currentMessage
            }
          }
        ).catch((e) => console.error("Failed to save user message:", e));
      }

      const response = await fetch(
        `${RAG_BASE_URL}/api/query/stream`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            query: currentMessage,
            history: historyPayload,
            model_name: (model === "Llama" || model === "Llama 3.2") ? "llama3.2:3b" : "qwen2.5:3b"
          })
        }
      );

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullTargetText = "";
      let displayedText = "";
      let streamFinished = false;

      // Progressive typewriter pump (renders smoothly in real-time)
      const typeWriterPromise = new Promise((resolve) => {
        const ticker = setInterval(() => {
          if (displayedText.length < fullTargetText.length) {
            const remaining = fullTargetText.slice(displayedText.length);
            const lag = remaining.length;

            // Adaptive step size: typing with speed catch-up if network buffer grows
            let step = 1;
            if (lag > 60) {
              step = Math.min(lag, 8);
            } else if (lag > 25) {
              step = Math.min(lag, 4);
            } else {
              const nextSpace = remaining.search(/\s/);
              step = (nextSpace !== -1 && nextSpace < 6) ? nextSpace + 1 : Math.min(2, remaining.length);
            }

            displayedText += remaining.slice(0, step);

            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1] = {
                sender: "AI",
                text: displayedText,
                streaming: true
              };
              return updated;
            });
          } else if (streamFinished) {
            clearInterval(ticker);
            resolve();
          }
        }, 12);
      });

      // Read incoming network stream chunks with instant first-token reveal
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        fullTargetText += chunk;

        // Reveal first token/word immediately for 0ms initial TTFT
        if (!displayedText && fullTargetText) {
          displayedText = fullTargetText;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              sender: "AI",
              text: displayedText,
              streaming: true
            };
            return updated;
          });
        }
      }
      streamFinished = true;

// Await completion of word-by-word typing animation
await typeWriterPromise;

if (!fullTargetText || !fullTargetText.trim()) {
  fullTargetText = "Sorry, I cannot find information regarding this question in the uploaded documents.";
}

setMessages((prev) => {
  const updated = [...prev];
  updated[updated.length - 1] = {
    sender: "AI",
    text: fullTargetText,
    streaming: false
  };
  return updated;
});

// Save AI answer after streaming finishes
if (fullTargetText && fullTargetText.trim()) {
  await axios.post(
    `${API_BASE_URL}/save-message`,
    null,
    {
      params: {
        session_id: chatId,
        sender: "AI",
        message: fullTargetText
      }
    }
  ).catch((e) => console.error("Failed to save AI message:", e));
}

}
catch(error){

  console.error(
    "CHAT ERROR:",
    error
  );

  setMessages((prev) => {
    const updated = [...prev];
    if (updated.length > 0 && updated[updated.length - 1].sender === "AI" && !updated[updated.length - 1].text) {
      updated[updated.length - 1] = {
        sender: "AI",
        text: "Error getting response from AI"
      };
      return updated;
    }
    return prev;
  });
}




  };

  return (

    <div

      style={{

        width:"100vw",

        height:"100vh",

        background:"#212121",

        color:"white",

        overflow:"hidden"

      }}

    >



      <MobileSidebar

        chatHistory={chatHistory}

        startNewChat={startNewChat}

        deleteChat={handleDeleteChat}

        openChat={openChat}

        togglePin={togglePin}

      />





      <div

        style={{

          position:"fixed",

          top:"60px",

          left:0,

          right:0,

          bottom:0,

          display:"flex",

          flexDirection:"column",

          background:"#212121"

        }}

      >





        <div

          ref={chatContainerRef}

          style={{

            flex:1,

            overflowY:"auto",

            overflowX:"hidden"

          }}

        >




          {

          messages.length === 0

          ?

          (

            <div

              style={{

                height:"100%",

                display:"flex",

                justifyContent:"center",

                alignItems:"center",

                flexDirection:"column"

              }}

            >


              <h1

                style={{

                  fontSize:"42px",

                  fontWeight:"600"

                }}

              >

                What can I help with?

              </h1>



              <p

                style={{

                  color:"#9ca3af",

                  fontSize:"18px"

                }}

              >

                Ask anything and start learning

              </p>



            </div>


          )


          :


          (

            <ChatWindow

              messages={messages}

            />


          )


          }



        </div>







        <div

          style={{

            padding:"15px 20px",

            background:"#212121"

          }}

        >



          <ChatInput

            message={message}

            setMessage={setMessage}

            sendMessage={sendMessage}

            model={model}

            setModel={setModel}

          />



        </div>



      </div>




    </div>


  );


}
