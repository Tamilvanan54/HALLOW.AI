import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function Profile() {
  const navigate = useNavigate();

  const [user, setUser] = useState({
    name: "",
    email: "",
    role: "",
    created_at: "",
    last_login: "",
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const email = localStorage.getItem("email");

      const response = await axios.get(
        "http://127.0.0.1:8000/profile",
        {
          params: { email },
        }
      );

      console.log(
        "PROFILE DATA =",
        JSON.stringify(response.data, null, 2)
      );

      setUser(response.data);
    } catch (error) {
      console.error(
        "PROFILE ERROR =",
        error
      );
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    navigate("/");
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#212121",
        color: "white",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "30px",
      }}
    >
      <div
        style={{
          width: "650px",
          background: "#2f2f2f",
          borderRadius: "20px",
          padding: "40px",
        }}
      >
        <div
          style={{
            textAlign: "center",
            marginBottom: "35px",
          }}
        >
          <div
            style={{
              fontSize: "80px",
            }}
          >
            👤
          </div>

          <h1
            style={{
              color: "#3b82f6",
            }}
          >
            My Profile
          </h1>
        </div>

        <div
          style={{
            background: "#3a3a3a",
            padding: "18px",
            borderRadius: "12px",
            marginBottom: "15px",
          }}
        >
          <b>Name:</b> {user.name}
        </div>

        <div
          style={{
            background: "#3a3a3a",
            padding: "18px",
            borderRadius: "12px",
            marginBottom: "15px",
          }}
        >
          <b>Email:</b> {user.email}
        </div>

        <div
          style={{
            background: "#3a3a3a",
            padding: "18px",
            borderRadius: "12px",
            marginBottom: "15px",
          }}
        >
          <b>Role:</b> {user.role}
        </div>

        <div
          style={{
            background: "#3a3a3a",
            padding: "18px",
            borderRadius: "12px",
            marginBottom: "15px",
          }}
        >
          <b>Joined Date:</b>{" "}
          {user.created_at
            ? new Date(
                user.created_at.replace(
                  " ",
                  "T"
                )
              ).toLocaleString("en-IN", {
                timeZone: "Asia/Kolkata",
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
                hour12: true,
              })
            : "Not Available"}
        </div>

        <div
          style={{
            background: "#3a3a3a",
            padding: "18px",
            borderRadius: "12px",
            marginBottom: "25px",
          }}
        >
          <b>Last Login:</b>{" "}
          {user.last_login
            ? new Date(
                user.last_login.replace(
                  " ",
                  "T"
                )
              ).toLocaleString("en-IN", {
                timeZone: "Asia/Kolkata",
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
                hour12: true,
              })
            : "Not Available"}
        </div>

        <button
          onClick={handleLogout}
          style={{
            width: "100%",
            padding: "14px",
            border: "none",
            borderRadius: "12px",
            background: "#dc2626",
            color: "white",
            fontSize: "16px",
            cursor: "pointer",
          }}
        >
          🚪 Logout
        </button>
      </div>
    </div>
  );
}