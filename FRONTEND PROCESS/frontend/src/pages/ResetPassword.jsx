import { useState } from "react";
import axios from "axios";
import { API_BASE_URL } from "../config/api";

import {
  useNavigate,
  useLocation
} from "react-router-dom";

export default function ResetPassword() {

  const navigate =
    useNavigate();

  const location =
    useLocation();

  const email =
    location.state?.email;

  const [token, setToken] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [
    confirmPassword,
    setConfirmPassword
  ] = useState("");

  const [loading, setLoading] =
    useState(false);

  const handleReset = async () => {

    if (!token) {

      alert("Enter OTP");

      return;
    }

    if (!password) {

      alert(
        "Enter New Password"
      );

      return;
    }

    if (
      password !==
      confirmPassword
    ) {

      alert(
        "Passwords do not match"
      );

      return;
    }

    try {

      setLoading(true);

      const response =
        await axios.post(
          `${API_BASE_URL}/reset-password`,
          null,
          {
            params: {
              token,
              new_password:
                password
            }
          }
        );

      if (
        response.data.status
      ) {

        alert(
          "Password Reset Successful"
        );

        navigate("/");

      } else {

        alert(
          response.data.message
        );

      }

    } catch (error) {

      console.log(error);

      alert(
        "Reset Failed"
      );

    } finally {

      setLoading(false);

    }
  };

  return (
    <div
      style={{
        height: "100vh",
        background: "#212121",
        color: "white",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          width: "420px",
          padding: "30px",
          background: "#2a2a2a",
          borderRadius: "15px",
        }}
      >
        <h2
          style={{
            textAlign: "center"
          }}
        >
          Reset Password
        </h2>

        <p
          style={{
            color: "#9ca3af",
            textAlign: "center"
          }}
        >
          {email}
        </p>

        <input
          placeholder="Enter OTP"
          value={token}
          onChange={(e) =>
            setToken(
              e.target.value
            )
          }
          style={{
            width: "100%",
            padding: "12px",
            marginTop: "15px",
            boxSizing:
              "border-box",
          }}
        />

        <input
          type="password"
          placeholder="New Password"
          value={password}
          onChange={(e) =>
            setPassword(
              e.target.value
            )
          }
          style={{
            width: "100%",
            padding: "12px",
            marginTop: "12px",
            boxSizing:
              "border-box",
          }}
        />

        <input
          type="password"
          placeholder="Confirm Password"
          value={
            confirmPassword
          }
          onChange={(e) =>
            setConfirmPassword(
              e.target.value
            )
          }
          style={{
            width: "100%",
            padding: "12px",
            marginTop: "12px",
            boxSizing:
              "border-box",
          }}
        />

        <button
          onClick={
            handleReset
          }
          disabled={
            loading
          }
          style={{
            width: "100%",
            padding: "12px",
            marginTop: "20px",
            cursor: "pointer",
          }}
        >
          {
            loading
              ? "Resetting..."
              : "Reset Password"
          }
        </button>
      </div>
    </div>
  );
}
