import {
  useEffect,
  useState
} from "react";

import {
  useParams,
  useNavigate
} from "react-router-dom";
import { API_BASE_URL } from "../config/api";

import axios from "axios";


export default function FeedbackDetails(){


  const { id } = useParams();

  const navigate = useNavigate();



  const [feedback,setFeedback] = useState(null);

  const [loading,setLoading] = useState(true);

  const [modifiedAnswer,setModifiedAnswer] = useState("");

  const [message,setMessage] = useState("");





  useEffect(()=>{


    const openFeedback = async()=>{


      await markAsReviewed();

      await loadFeedback();


    };


    openFeedback();


  },[]);







  // ==========================
  // MARK REVIEWED
  // ==========================


  const markAsReviewed = async()=>{


    try{


      await axios.put(

        `${API_BASE_URL}/feedbacks/${id}`

      );


    }
    catch(error){


      console.log(
        error
      );


    }


  };









  // ==========================
  // LOAD FEEDBACK
  // ==========================


  const loadFeedback = async()=>{


    try{


      const response = await axios.get(

        `${API_BASE_URL}/feedbacks/${id}`

      );



      setFeedback(
        response.data
      );



      setModifiedAnswer(

        response.data.modified_answer || ""

      );


    }
    catch(error){


      console.log(
        "Fetch Error",
        error
      );


    }
    finally{


      setLoading(false);


    }


  };








  // ==========================
  // DATE FORMAT
  // ==========================


  const formatDate=(date)=>{


    if(!date)

      return "-";



    const utcDate = new Date(
      date+"Z"
    );



    return utcDate.toLocaleString(

      "en-IN",

      {

        timeZone:"Asia/Kolkata",

        day:"2-digit",

        month:"short",

        year:"numeric",

        hour:"2-digit",

        minute:"2-digit",

        hour12:true

      }

    )+" IST";


  };
  // ==========================
  // SAVE CORRECTION
  // ==========================


  const saveCorrection = async()=>{


    try{


      await axios.put(

        `${API_BASE_URL}/feedbacks/${id}`,

        {

          modified_answer:
          modifiedAnswer,


          status:
          "Reviewed"

        }

      );



      setMessage(
        "Correction Saved Successfully"
      );



      setTimeout(()=>{


        navigate(
          "/feedback-review"
        );


      },1500);



    }
    catch(error){


      console.log(
        "Update Error",
        error
      );


    }


  };









  if(loading){


    return(


      <div

        style={{

          minHeight:"100vh",

          background:"#020617",

          color:"white",

          display:"flex",

          justifyContent:"center",

          alignItems:"center",

          fontSize:"16px"

        }}

      >


        Loading Feedback...


      </div>


    );


  }







  if(!feedback){


    return(


      <div

        style={{

          minHeight:"100vh",

          background:"#020617",

          color:"white",

          display:"flex",

          justifyContent:"center",

          alignItems:"center"

        }}

      >


        Feedback Not Found


      </div>


    );


  }









  return(


    <div


      style={{


        minHeight:"100vh",


        width:"100%",


        background:"#020617",


        padding:"25px",


        color:"white"



      }}


    >





      {
        message &&


        <div


          style={{


            background:"#166534",


            padding:"12px",


            borderRadius:"10px",


            marginBottom:"20px",


            fontSize:"14px"


          }}


        >


          {message}


        </div>

      }








      <button


        onClick={()=>navigate("/feedback-review")}


        style={{


          background:"#2563eb",


          color:"white",


          border:"none",


          padding:"10px 18px",


          borderRadius:"8px",


          cursor:"pointer",


          marginBottom:"25px"


        }}



      >


        ← Back


      </button>









      <h1


        style={{


          fontSize:"28px",


          marginBottom:"25px",


          color:"#38bdf8"


        }}



      >


        📄 Feedback Details


      </h1>









      {/* USER INFORMATION */}



      <div className="card">


        <h2>

          👤 User Information

        </h2>



        <p>

          <b>User:</b>

          {" "}

          {feedback.reported_by}

        </p>




        <p>


          <b>Status:</b>


          <span


            style={{


              marginLeft:"10px",

              background:"#16a34a",

              padding:"4px 12px",

              borderRadius:"20px",

              fontSize:"12px"


            }}


          >


            {feedback.status}


          </span>


        </p>





        <p>

          <b>Submitted:</b>

          {" "}

          {formatDate(feedback.created_at)}

        </p>



      </div>









      {/* QUESTION */}



      <div className="card">


        <h2>

          ❓ User Question

        </h2>




        <p>


          {feedback.question}


        </p>



      </div>









      {/* AI ANSWER */}



      <div className="card">


        <h2>

          🤖 AI Generated Answer

        </h2>



        <p>


          {feedback.answer || "No Answer"}


        </p>



      </div>
      
      {/* STUDENT FEEDBACK */}


      <div className="card">


        <h2>

          📝 Student Feedback

        </h2>



        <p


          style={{


            color:"#fca5a5"


          }}


        >


          {feedback.feedback || "No Feedback"}


        </p>



      </div>









      {/* ADMIN CORRECTION */}



      <div className="card">


        <h2>

          ✏️ Admin Correction

        </h2>



        <p


          style={{


            color:"#94a3b8",

            marginBottom:"15px"


          }}



        >


          Update the correct answer if AI response is wrong.


        </p>







        <textarea



          value={modifiedAnswer}



          onChange={(e)=>


            setModifiedAnswer(

              e.target.value

            )


          }




          placeholder="Enter corrected answer..."



          style={{



            width:"100%",



            minHeight:"160px",



            padding:"15px",



            background:"#020617",



            color:"white",



            border:"1px solid #334155",



            borderRadius:"10px",



            resize:"vertical",



            fontSize:"14px",



            lineHeight:"1.6"



          }}



        />



      </div>









      {/* SAVE BUTTON */}



      <button



        onClick={saveCorrection}



        style={{



          background:"#16a34a",



          color:"white",



          border:"none",



          padding:"12px 30px",



          borderRadius:"10px",



          cursor:"pointer",



          fontSize:"14px",



          fontWeight:"600",



          marginTop:"5px"



        }}



      >



        💾 Save Correction



      </button>







    </div>


  );


}
