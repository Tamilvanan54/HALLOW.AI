import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API_BASE_URL } from "../config/api";

export default function Signup() {

  const navigate = useNavigate();

  const [name, setName] =
    useState("");

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [showPassword, setShowPassword] =
    useState(false);

  const [role, setRole] =
    useState("student");

  const handleSignup = async () => {

    try {

      const response =
        await axios.post(
          `${API_BASE_URL}/signup`,
          null,
          {
            params: {
              name,
              email,
              password,
              role,
            },
          }
        );

      if (
        response.data.status
      ) {

        navigate("/");

      } else {

        console.log(
          response.data.message
        );

      }

    } catch (error) {

      console.error(
        "SIGNUP ERROR:",
        error
      );

    }
  };

  return (
    <div
      style={{
        height: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        background: "#0f172a",
        color: "white",
      }}
    >
      <div
        style={{
          width: "400px",
          padding: "30px",
          borderRadius: "15px",
          background: "#1e293b",
        }}
      >
        <h1
          style={{
            textAlign: "center",
          }}
        >
          📚 STUDY AI
        </h1>

        <p
          style={{
            textAlign: "center",
          }}
        >
          Create New Account
        </p>

        <input
          type="text"
          placeholder="Full Name"
          value={name}
          onChange={(e) =>
            setName(
              e.target.value
            )
          }
          style={{
            width: "100%",
            padding: "12px",
            marginTop: "15px",
          }}
        />

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) =>
            setEmail(
              e.target.value
            )
          }
          style={{
            width: "100%",
            padding: "12px",
            marginTop: "15px",
          }}
        />

        <div style={{ position: "relative", width: "100%", marginTop: "15px" }}>
          <input
            type={showPassword ? "text" : "password"}
            placeholder="Password"
            value={password}
            onChange={(e) =>
              setPassword(
                e.target.value
              )
            }
            style={{
              width: "100%",
              padding: "12px 40px 12px 12px",
              boxSizing: "border-box"
            }}
          />
          <span
            onClick={() => setShowPassword(!showPassword)}
            style={{
              position: "absolute",
              right: "12px",
              top: "50%",
              transform: "translateY(-50%)",
              cursor: "pointer",
              fontSize: "18px",
              userSelect: "none"
            }}
            title={showPassword ? "Hide password" : "Show password"}
          >
            {showPassword ? "👁️" : "🙈"}
          </span>
        </div>

        <select
          value={role}
          onChange={(e) =>
            setRole(
              e.target.value
            )
          }
          style={{
            width: "100%",
            padding: "12px",
            marginTop: "15px",
          }}
        >
          <option value="student">
            Student
          </option>

          <option value="staff">
            Staff
          </option>
        </select>

        <button
          onClick={handleSignup}
          style={{
            width: "100%",
            padding: "12px",
            marginTop: "20px",
            background: "#2563eb",
            color: "white",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
          }}
        >
          Create Account
        </button>

        <p
          style={{
            marginTop: "15px",
            cursor: "pointer",
          }}
          onClick={() =>
            navigate("/")
          }
        >
          Already have an account?
          Login
        </p>
      </div>
    </div>
  );
}
