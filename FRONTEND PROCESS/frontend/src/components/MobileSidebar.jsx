import { useState } from "react";
import { useNavigate } from "react-router-dom";

import {
FiMenu,
FiEdit3,
FiMessageSquare,
FiBookOpen,
FiUser,
FiUsers,
FiBarChart2,
FiTrash2,
FiLogOut,
FiPaperclip,
} from "react-icons/fi";



export default function MobileSidebar({
chatHistory = [],
startNewChat,
deleteChat,
openChat,
togglePin,
}) {


  const [isOpen, setIsOpen] = useState(false);

  const navigate = useNavigate();


  const role =
    (localStorage.getItem("role") || "")
      .toLowerCase()
      .trim();


  const email =
    localStorage.getItem("email") || "";


  const isAdmin =
    role === "admin";


  const isStaff =
    role === "staff";


  console.log(
    "MOBILE SIDEBAR ROLE:",
    role
  );



  const logout = () => {

  localStorage.removeItem("token");
  localStorage.removeItem("role");
  localStorage.removeItem("email");

  // IMPORTANT
  localStorage.removeItem("activeChatId");

  navigate("/");

};



  return (

    <>

      {/* TOP BAR */}

      <div
        style={{
          position:"fixed",
          top:0,
          left:0,
          right:0,
          height:"60px",
          background:"#212121",
          color:"white",
          display:"flex",
          alignItems:"center",
          padding:"0 20px",
          borderBottom:"1px solid #2f2f2f",
          zIndex:1000,
        }}
      >

        <button
          onClick={() =>
            setIsOpen(true)
          }
          style={{
            background:"none",
            border:"none",
            color:"white",
            fontSize:"22px",
            cursor:"pointer",
          }}
        >
          <FiMenu />
        </button>


        <img
          src="/hallow-full-logo.png"
          alt="HALLOW.AI"
          style={{
            height: "46px",
            width: "auto",
            objectFit: "contain",
            marginLeft: "12px",
          }}
        />


      </div>





      {
        isOpen && (

          <>


            {/* OVERLAY */}

            <div
              onClick={() =>
                setIsOpen(false)
              }
              style={{
                position:"fixed",
                top:"60px",
                left:0,
                right:0,
                bottom:0,
                background:"rgba(0,0,0,0.35)",
                zIndex:998,
              }}
            />





            {/* SIDEBAR */}

            <div
              style={{
                position:"fixed",
                top:"60px",
                left:0,
                width:"280px",
                height:"calc(100vh - 60px)",
                background:"#212121",
                color:"white",
                padding:"15px",
                overflowY:"auto",
                borderRight:"1px solid #2f2f2f",
                zIndex:999,
              }}
            >




              {/* NEW CHAT */}

              <button
                onClick={() => {

                  startNewChat();
                  setIsOpen(false);

                }}
                style={{
                  width:"100%",
                  padding:"14px",
                  background:"#2a2a2a",
                  color:"white",
                  border:"1px solid #3a3a3a",
                  borderRadius:"12px",
                  cursor:"pointer",
                  marginBottom:"25px",
                  display:"flex",
                  alignItems:"center",
                  gap:"10px",
                }}
              >

                <FiEdit3 />

                New Chat

              </button>





              {/* RECENT CHATS */}

              <h4
                style={{
                  color:"#9ca3af",
                  textAlign:"center",
                  marginBottom:"15px",
                }}
              >
                Recent Chats
              </h4>




              {
                chatHistory.length === 0 ? (

                  <p
                    style={{
                      textAlign:"center",
                      color:"#9ca3af",
                    }}
                  >
                    No chats yet
                  </p>


                ) : (


                  chatHistory.map(

  (chat) => (

   <div
  key={chat.id}
  style={{
    padding:"12px",

    background:
  chat.pinned
    ? "#3a3a3a"
    : "#2a2a2a",

    border:
      chat.pinned
        ? "1px solid #4b5563"
        : "1px solid transparent",

    borderRadius:"10px",
    marginBottom:"8px",
    display:"flex",
    justifyContent:"space-between",
    alignItems:"center",
  }}
>

      <div
        onClick={() => {

          openChat(chat);

          setIsOpen(false);

        }}
        style={{
          cursor:"pointer",
          display:"flex",
          gap:"10px",
          alignItems:"center",
          flex:1,
        }}
      >

        <FiMessageSquare />

        <span>

          {chat.title}

        </span>

      </div>





      <div
        style={{
          display:"flex",
          gap:"12px",
          alignItems:"center",
        }}
      >

        <FiPaperclip
          onClick={() =>
            togglePin(chat.id)
          }
          style={{
            cursor:"pointer",

            color:
  chat.pinned
    ? "#e5e7eb"
    : "#6b7280",
          }}
        />



        <FiTrash2
          onClick={() =>
            deleteChat(chat.id)
          }
          style={{
            cursor:"pointer",
            color:"#9ca3af",
               }}
            />

             </div>

           </div>

        )

      )


    )
  }







              <hr
                style={{
                  border:"1px solid #2f2f2f",
                  margin:"20px 0",
                }}
              />





              {/* MENU */}

              <div
                style={{
                  display:"flex",
                  flexDirection:"column",
                  gap:"18px",
                }}
              >




                <div
                  onClick={() => {

                    navigate("/chat");
                    setIsOpen(false);

                  }}
                  style={{
                    display:"flex",
                    gap:"12px",
                    alignItems:"center",
                    cursor:"pointer",
                  }}
                >

                  <FiMessageSquare />

                  Chat

                </div>





                <div
                  onClick={() => {

                    navigate("/library");
                    setIsOpen(false);

                  }}
                  style={{
                    display:"flex",
                    gap:"12px",
                    alignItems:"center",
                    cursor:"pointer",
                  }}
                >

                  <FiBookOpen />

                  Library

                </div>






                <div
                  onClick={() => {

                    navigate("/profile");
                    setIsOpen(false);

                  }}
                  style={{
                    display:"flex",
                    gap:"12px",
                    alignItems:"center",
                    cursor:"pointer",
                  }}
                >

                  <FiUser />

                  Profile

                </div>






                {/* FEEDBACK REVIEW */}

                {
                  (isAdmin || isStaff) && (

                    <div
                      onClick={() => {

                        navigate("/feedback-review");
                        setIsOpen(false);

                      }}
                      style={{
                        display:"flex",
                        gap:"12px",
                        alignItems:"center",
                        cursor:"pointer",
                      }}
                    >

                      <FiMessageSquare />

                      Feedback Review

                    </div>

                  )
                }






                {/* ADMIN ONLY */}

                {
                  isAdmin && (

                    <>


                      <div
                        onClick={() => {

                          navigate("/users");
                          setIsOpen(false);

                        }}
                        style={{
                          display:"flex",
                          gap:"12px",
                          alignItems:"center",
                          cursor:"pointer",
                        }}
                      >

                        <FiUsers />

                        Users

                      </div>




                      <div
                        onClick={() => {

                          navigate("/logs");
                          setIsOpen(false);

                        }}
                        style={{
                          display:"flex",
                          gap:"12px",
                          alignItems:"center",
                          cursor:"pointer",
                        }}
                      >

                        <FiBarChart2 />

                        Logs

                      </div>



                    </>

                  )
                }



              </div>







              <hr
                style={{
                  border:"1px solid #2f2f2f",
                  margin:"20px 0",
                }}
              />






              {/* USER INFO */}

              <p>
                👤 {email}
              </p>


              <p
                style={{
                  color:"#9ca3af",
                }}
              >
                {role}
              </p>




              <button
                onClick={logout}
                style={{
                  width:"100%",
                  padding:"12px",
                  background:"#2a2a2a",
                  color:"white",
                  border:"none",
                  borderRadius:"10px",
                  cursor:"pointer",
                  display:"flex",
                  justifyContent:"center",
                  alignItems:"center",
                  gap:"10px",
                }}
              >

                <FiLogOut />

                Logout

              </button>



            </div>


          </>

        )
      }


    </>

  );

}