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

if(!chatId){

  const newChat = await addChat(

    currentMessage.length > 25
      ? currentMessage.substring(0,25) + "..."
      : currentMessage

  );

  await fetchChats();

console.log("NEW CHAT:", newChat);

console.log(
  "CHAT HISTORY AFTER ADD:",
  chatHistory
);

if(!newChat){

  console.error("CHAT CREATE FAILED");

  return;

}

  if(!newChat.id){

    console.error("CHAT ID MISSING:", newChat);

    return;

  }

  chatId = newChat.id;

  setCurrentChatId(chatId);

  localStorage.setItem(
    "activeChatId",
    String(chatId)
  );

}


    // User message immediately show
setMessages((prev) => [
  ...prev,
  {
    sender: "User",
    text: currentMessage
  }
]);

try {

  // Save user message
  await axios.post(
    `${API_BASE_URL}/save-message`,
    null,
    {
      params: {
        session_id: chatId,
        sender: "User",
        message: currentMessage
      }
    }
  );

  // Create empty AI message

setMessages((prev) => [
  ...prev,
  {
    sender: "AI",
    text: ""
  }
]);

const response = await fetch(
  `${RAG_BASE_URL}/api/query/stream`,
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      query: currentMessage,
      model_name: (model === "Llama" || model === "Llama 3.2") ? "llama3.2:3b" : "qwen2.5:3b"
    })
  }
);

const reader = response.body.getReader();

const decoder = new TextDecoder();

let aiAnswer = "";

while (true) {

  const { done, value } =
    await reader.read();

  if (done) {
    break;
  }

  const chunk =
    decoder.decode(value);

  aiAnswer += chunk;

  setMessages((prev) => {

    const updated = [...prev];

    updated[updated.length - 1] = {
      sender: "AI",
      text: aiAnswer
    };

    return updated;

  });
}

if (!aiAnswer || !aiAnswer.trim()) {
  aiAnswer = "Sorry, I cannot find information regarding this question in the uploaded documents.";
  setMessages((prev) => {
    const updated = [...prev];
    updated[updated.length - 1] = {
      sender: "AI",
      text: aiAnswer
    };
    return updated;
  });
}

// Save AI answer after streaming finishes

await axios.post(
  `${API_BASE_URL}/save-message`,
  null,
  {
    params: {
      session_id: chatId,
      sender: "AI",
      message: aiAnswer
    }
  }
);

}
catch(error){

  console.error(
    "CHAT ERROR:",
    error
  );

  setMessages((prev) => [
    ...prev,
    {
      sender:"AI",
      text:"Error getting response from AI"
    }
  ]);
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
