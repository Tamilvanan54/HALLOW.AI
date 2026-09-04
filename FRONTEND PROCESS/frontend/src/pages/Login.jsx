import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API_BASE_URL } from "../config/api";

export default function Login() {

  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async () => {

    setError("");

    if (!email || !password) {
      setError("Enter Email and Password");
      return;
    }

    try {

      setLoading(true);

      const response = await axios.post(
        `${API_BASE_URL}/login`,
        null,
        {
          params: {
            email,
            password,
          },
        }
      );

      if (response.data.status === true) {

        localStorage.setItem(
          "token",
          response.data.token
        );

        localStorage.setItem(
          "role",
          response.data.role
        );

        localStorage.setItem(
          "email",
          email
        );

        navigate("/chat");

      } else {

        setError(
          response.data.message
        );

      }

    } catch (error) {

      console.error(
        "LOGIN ERROR:",
        error
      );

      if (
        error.response &&
        error.response.data
      ) {

        setError(
          error.response.data.message ||
          "Login Failed"
        );

      } else {

        setError(
          "Server Not Responding"
        );

      }

    } finally {

      setLoading(false);

    }
  };

  return (

    <div
      style={{
        width: "100vw",
        height: "100vh",
        background: "#0d0d0d",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        color: "white",
        overflow: "hidden"
      }}
    >

      <div
        style={{
          width: "420px",
          padding: "40px",
          borderRadius: "20px",
          background: "#171717",
          border: "1px solid #2f2f2f",
          boxShadow:
            "0px 0px 30px rgba(0,0,0,0.6)"
        }}
      >

        {/* LOGO */}

        <div
          style={{
            textAlign: "center",
            marginBottom: "30px"
          }}
        >
          <img
            src="/havox-full-logo.png"
            alt="HavoxAI Logo"
            style={{
              width: "auto",
              maxWidth: "100%",
              height: "100px",
              objectFit: "contain",
              display: "block",
              margin: "0 auto"
            }}
          />
        </div>

        {error && (
          <div
            style={{
              background: "#7f1d1d",
              color: "#fecaca",
              padding: "12px",
              borderRadius: "10px",
              marginBottom: "15px",
              textAlign: "center"
            }}
          >
            {error}
          </div>
        )}

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) =>
            setEmail(e.target.value)
          }
          style={{
            width: "100%",
            padding: "14px",
            marginBottom: "15px",
            background: "#262626",
            color: "white",
            border: "1px solid #404040",
            borderRadius: "10px",
            outline: "none",
            boxSizing: "border-box"
          }}
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) =>
            setPassword(
              e.target.value
            )
          }
          style={{
            width: "100%",
            padding: "14px",
            background: "#262626",
            color: "white",
            border: "1px solid #404040",
            borderRadius: "10px",
            outline: "none",
            boxSizing: "border-box"
          }}
        />

        <div
          style={{
            textAlign: "right",
            marginTop: "10px"
          }}
        >
          <span
            onClick={() =>
              navigate(
                "/forgot-password"
              )
            }
            style={{
              color: "#9ca3af",
              cursor: "pointer",
              fontSize: "14px"
            }}
          >
            Forgot Password?
          </span>
        </div>

        <button
          onClick={handleLogin}
          disabled={loading}
          style={{
            width: "100%",
            marginTop: "20px",
            padding: "14px",
            borderRadius: "30px",
            border: "none",
            background: "white",
            color: "black",
            fontWeight: "600",
            fontSize: "16px",
            cursor: "pointer"
          }}
        >
          {
            loading
              ? "Signing In..."
              : "Continue"
          }
        </button>

        <button
          onClick={() =>
            navigate("/signup")
          }
          style={{
            width: "100%",
            marginTop: "12px",
            padding: "14px",
            borderRadius: "30px",
            background: "transparent",
            border: "1px solid #404040",
            color: "white",
            cursor: "pointer"
          }}
        >
          Create Account
        </button>

      </div>

    </div>
  );
}
