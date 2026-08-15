import {
  BrowserRouter,
  Routes,
  Route
} from "react-router-dom";


import Login from "./pages/Login";
import Signup from "./pages/Signup";


import Chat from "./pages/Chat";
import Library from "./pages/Library";
import Profile from "./pages/Profile";


import Users from "./pages/Users";
import Logs from "./pages/Logs";


import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";


import FeedbackReview from "./pages/FeedbackReview";


// 🔥 NEW IMPORT
import FeedbackDetails from "./pages/FeedbackDetails";



function App() {


  return (


    <BrowserRouter>


      <Routes>



        {/* Authentication */}



        <Route

          path="/"

          element={<Login />}

        />



        <Route

          path="/signup"

          element={<Signup />}

        />



        <Route

          path="/forgot-password"

          element={<ForgotPassword />}

        />



        <Route

          path="/reset-password"

          element={<ResetPassword />}

        />







        {/* Main Pages */}



        <Route

          path="/chat"

          element={<Chat />}

        />



        <Route

          path="/library"

          element={<Library />}

        />



        <Route

          path="/profile"

          element={<Profile />}

        />








        {/* Admin Pages */}



        <Route

          path="/users"

          element={<Users />}

        />



        <Route

          path="/logs"

          element={<Logs />}

        />





        {/* Feedback Review Page */}



        <Route

          path="/feedback-review"

          element={<FeedbackReview />}

        />





        {/* 🔥 Feedback Details Page */}

        <Route

          path="/feedback-review/:id"

          element={<FeedbackDetails />}

        />




      </Routes>


    </BrowserRouter>


  );


}


export default App;