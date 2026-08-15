import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";


export default function FeedbackReview(){


const navigate = useNavigate();


const [feedbacks,setFeedbacks] = useState([]);

const [loading,setLoading] = useState(true);

const [search,setSearch] = useState("");

const [message,setMessage] = useState("");

const [total,setTotal] = useState(0);

const [pending,setPending] = useState(0);

const [reviewed,setReviewed] = useState(0);





useEffect(()=>{

loadFeedbacks();

},[]);





const loadFeedbacks = async()=>{


try{


setLoading(true);


const response = await axios.get(
"http://127.0.0.1:8000/feedbacks"
);



const data = response.data;


setFeedbacks(data);



setTotal(data.length);



setPending(

data.filter(

(item)=>

(item.status || "Pending")

==="Pending"

).length

);



setReviewed(

data.filter(

(item)=>

(item.status || "Pending")

==="Reviewed"

).length

);



}

catch(error){

console.log(
"Feedback Load Error",
error
);

}


finally{

setLoading(false);

}


};







// IST TIME FORMAT FIX

const formatDate = (date)=>{


if(!date)

return "-";



const utcDate = new Date(
date + "Z"
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

second:"2-digit",

hour12:true

}

)+" IST";



};

const handleViewFeedback = async (id) => {

  try {

    await axios.put(
      `http://127.0.0.1:8000/feedback/${id}`
    );

    await loadFeedbacks();

    navigate(
      `/feedback-review/${id}`
    );

  } catch (error) {

    console.log(
      "Update Error",
      error
    );

  }

};

const filteredFeedbacks = feedbacks.filter(

(item)=>

JSON.stringify(item)

.toLowerCase()

.includes(

search.toLowerCase()

)

);









return (

<div
  style={{
    minHeight: "100vh",
    width: "100vw",
    background: "#0f172a",
    color: "white",
    padding: "30px",
    boxSizing: "border-box",
    margin: 0,
    position: "absolute",
    top: 0,
    left: 0
  }}
>

{

message &&

<div

style={{

position:"fixed",

top:"20px",

right:"20px",

background:"#16a34a",

padding:"12px 20px",

borderRadius:"10px",

zIndex:9999

}}

>

{message}

</div>

}





<div

style={{

display:"flex",

justifyContent:"space-between",

alignItems:"center",

marginBottom:"25px"

}}

>


<div>


<h1

style={{

color:"#38bdf8"

}}

>

📢 Feedback Review

</h1>



<p

style={{

color:"#94a3b8"

}}

>

Manage and monitor user feedback

</p>



</div>

<button

onClick={() =>
  handleViewFeedback(
    item.id
  )
}

style={{

padding:"8px 15px",

background:"#0ea5e9",

color:"white",

border:"none",

borderRadius:"8px",

cursor:"pointer",

fontWeight:"bold"

}}

>

View

</button>








</div>






<div

style={{

display:"grid",

gridTemplateColumns:"repeat(3,1fr)",

gap:"20px",

marginBottom:"25px"

}}

>


<Card

title="Total Feedback"

value={total}

icon="📋"

/>



<Card

title="Pending"

value={pending}

icon="🟡"

/>



<Card

title="Reviewed"

value={reviewed}

icon="🟢"

/>



</div>





<input


placeholder="🔍 Search feedback..."


value={search}


onChange={(e)=>

setSearch(e.target.value)

}


style={{

width:"100%",

padding:"14px",

marginBottom:"20px",

borderRadius:"10px",

border:"1px solid #475569",

background:"#1e293b",

color:"white",

fontSize:"16px"

}}


/>
<div

style={{

background:"#1e293b",

padding:"20px",

borderRadius:"15px",

overflowX:"auto"

}}

>


{

loading ?


(

<h3>

Loading Feedbacks...

</h3>

)



:


filteredFeedbacks.length === 0 ?


(

<h3>

No Feedback Found

</h3>

)



:


(


<table


style={{

width:"100%",

borderCollapse:"collapse"

}}


>


<thead>


<tr

style={{

background:"#334155"

}}

>


<th style={tableHead}>
ID
</th>


<th style={tableHead}>
User
</th>


<th style={tableHead}>
Question
</th>


<th style={tableHead}>
Feedback
</th>


<th style={tableHead}>
Status
</th>


<th style={tableHead}>
Submitted Time
</th>


<th style={tableHead}>
Action
</th>


</tr>


</thead>





<tbody>


{

filteredFeedbacks.map((item)=>(


<tr key={item.id}>


<td style={tableData}>

{item.id}

</td>




<td style={tableData}>

{item.reported_by}

</td>





<td style={tableData}>

{item.question}

</td>





<td style={tableData}>

{item.feedback}

</td>





<td style={tableData}>


<span

style={{

padding:"6px 12px",

borderRadius:"20px",

background:

(item.status || "Pending")==="Pending"

?

"#854d0e"

:

"#166534"

}}

>


{item.status || "Pending"}


</span>


</td>







<td style={tableData}>


{

formatDate(item.created_at)

}


</td>







<td style={tableData}>


<button


onClick={()=>


navigate(

`/feedback-review/${item.id}`

)


}


style={{

padding:"8px 15px",

background:"#0ea5e9",

color:"white",

border:"none",

borderRadius:"8px",

cursor:"pointer",

fontWeight:"bold"

}}


>


View


</button>



</td>





</tr>


))


}


</tbody>


</table>


)


}



</div>



</div>


);


}









function Card({title,value,icon}){


return(


<div


style={{


background:"#1e293b",

padding:"20px",

borderRadius:"15px"


}}


>


<h2>

{icon} {value}

</h2>


<p

style={{

color:"#94a3b8"

}}

>

{title}

</p>


</div>


);


}








const tableHead = {


padding:"15px",

textAlign:"left",

borderBottom:"1px solid #475569",

whiteSpace:"nowrap"


};





const tableData = {


padding:"15px",

borderBottom:"1px solid #334155",

verticalAlign:"top"


};