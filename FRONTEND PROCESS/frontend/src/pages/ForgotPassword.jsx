import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { API_BASE_URL } from "../config/api";

export default function ForgotPassword() {

  const navigate = useNavigate();

  const [email, setEmail] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const handleSubmit = async () => {

    if (!email) {

      alert(
        "Enter Email"
      );

      return;
    }

    try {

      setLoading(true);

      const response =
        await axios.post(
          `${API_BASE_URL}/forgot-password`,
          null,
          {
            params: {
              email
            }
          }
        );

      if (
        response.data.status
      ) {

        alert(
          "OTP Sent Successfully"
        );

        navigate(
          "/reset-password",
          {
            state: {
              email
            }
          }
        );

      } else {

        alert(
          response.data.message
        );

      }

    } catch (error) {

      console.log(error);

      alert(
        "Failed To Send OTP"
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
          width: "400px",
          padding: "30px",
          background: "#2a2a2a",
          borderRadius: "15px",
        }}
      >
        <h2
          style={{
            textAlign: "center",
          }}
        >
          Forgot Password
        </h2>

        <input
          type="email"
          placeholder="Enter Email"
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
            boxSizing:
              "border-box",
          }}
        />

        <button
          onClick={
            handleSubmit
          }
          disabled={
            loading
          }
          style={{
            width: "100%",
            marginTop: "20px",
            padding: "12px",
            cursor: "pointer",
          }}
        >
          {
            loading
              ? "Sending OTP..."
              : "Send OTP"
          }
        </button>

      </div>
    </div>
  );
}
