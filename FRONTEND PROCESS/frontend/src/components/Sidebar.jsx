import { useNavigate } from "react-router-dom";


export default function Sidebar({
  chatHistory = [],
  startNewChat,
  deleteChat,
  openChat,
}) {

  const navigate = useNavigate();


  const role =
    (localStorage.getItem("role") || "")
      .toLowerCase()
      .trim();


  const email =
    localStorage.getItem("email") || "";


  const isAdmin = role === "admin";
  const isStaff = role === "staff";


  console.log("SIDEBAR ROLE:", role);



  const logout = () => {

    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("email");

    navigate("/");

  };



  return (

    <div
      style={{
        width:"260px",
        height:"100vh",
        background:"#171717",
        color:"white",
        display:"flex",
        flexDirection:"column",
        padding:"15px",
        borderRight:"1px solid #2f2f2f",
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
          padding:"12px",
          background:"#2f2f2f",
          color:"white",
          borderRadius:"8px",
          border:"1px solid #404040",
          cursor:"pointer",
          marginBottom:"20px",
        }}
      >
        ✏️ New Chat
      </button>




      <h4
        style={{
          textAlign:"center",
          color:"#9ca3af",
        }}
      >
        Recent Chats
      </h4>



      <div
        style={{
          flex:1,
          overflowY:"auto",
        }}
      >

      {
        chatHistory.length === 0 ? (

          <p
            style={{
              color:"#9ca3af",
              textAlign:"center",
            }}
          >
            No chats yet
          </p>

        ) : (

          chatHistory.map((chat)=>(

            <div
              key={chat.id}
              style={{
                background:"#2f2f2f",
                padding:"10px",
                borderRadius:"8px",
                marginBottom:"10px",
                display:"flex",
                justifyContent:"space-between",
              }}
            >

              <span
                onClick={() =>
                  openChat && openChat(chat)
                }
                style={{
                  cursor:"pointer",
                }}
              >
                💬 {chat.title}
              </span>


              <span
                onClick={() =>
                  deleteChat(chat.id)
                }
                style={{
                  cursor:"pointer",
                  color:"red",
                }}
              >
                🗑
              </span>


            </div>

          ))

        )
      }


      </div>




      {/* MENU */}

      <div
        style={{
          display:"flex",
          flexDirection:"column",
          gap:"18px",
          marginTop:"15px",
        }}
      >



        <div
          onClick={() => navigate("/chat")}
          style={{cursor:"pointer"}}
        >
          💬 Chat
        </div>




        <div
          onClick={() => navigate("/library")}
          style={{cursor:"pointer"}}
        >
          📄 Library
        </div>





        {
          isAdmin && (

            <>
              <div
                onClick={() => navigate("/users")}
                style={{cursor:"pointer"}}
              >
                👥 Users
              </div>


              <div
                onClick={() => navigate("/logs")}
                style={{cursor:"pointer"}}
              >
                📊 Logs
              </div>

            </>

          )
        }





        {
          (isAdmin || isStaff) && (

            <div
              onClick={() => navigate("/feedback-review")}
              style={{
                cursor:"pointer",
              }}
            >
              📢 Feedback Review
            </div>

          )
        }





        <div
          onClick={() => navigate("/profile")}
          style={{
            cursor:"pointer",
          }}
        >
          👤 Profile
        </div>



      </div>






      {/* USER INFO */}

      <div
        style={{
          borderTop:"1px solid #404040",
          marginTop:"15px",
          paddingTop:"15px",
          textAlign:"center",
        }}
      >


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
            padding:"10px",
            background:"#2f2f2f",
            color:"white",
            border:"none",
            borderRadius:"8px",
            cursor:"pointer",
          }}
        >
          ⇥ Logout
        </button>


      </div>



    </div>

  );

}