import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { API_BASE_URL } from "../config/api";
import { FaEye, FaEyeSlash } from "react-icons/fa";

export default function Signup() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const roleParam = (searchParams.get("role") || "student").toLowerCase();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [role, setRole] = useState(roleParam);
  const [college, setCollege] = useState("");
  const [department, setDepartment] = useState("CSE");
  const [year, setYear] = useState("3rd Year");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (roleParam) {
      setRole(roleParam);
    }
  }, [roleParam]);

  const handleSignup = async () => {
    setError("");

    if (!name || !email || !password || !confirmPassword) {
      setError("Please fill all required fields");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match!");
      return;
    }

    try {
      setLoading(true);

      const response = await axios.post(
        `${API_BASE_URL}/signup`,
        null,
        {
          params: {
            name,
            email,
            password,
            role,
            college,
            department,
            year,
          },
        }
      );

      if (response.data.status) {
        alert("Account Created Successfully! Please login with your credentials.");
        navigate("/");
      } else {
        setError(response.data.message || "Failed to create account");
      }
    } catch (error) {
      console.error("SIGNUP ERROR:", error);
      setError(error.response?.data?.message || "Signup failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#0d0d0d",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        color: "white",
        padding: "30px 15px",
        boxSizing: "border-box"
      }}
    >
      <div
        style={{
          width: "440px",
          padding: "35px",
          borderRadius: "20px",
          background: "#171717",
          border: "1px solid #2f2f2f",
          boxShadow: "0px 0px 30px rgba(0,0,0,0.6)",
          boxSizing: "border-box"
        }}
      >
        {/* LOGO */}
        <div style={{ textAlign: "center", marginBottom: "20px" }}>
          <img
            src="/havox-full-logo.png"
            alt="HavoxAI Logo"
            style={{
              width: "auto",
              maxWidth: "100%",
              height: "75px",
              objectFit: "contain",
              display: "block",
              margin: "0 auto"
            }}
          />
        </div>

        <h2 style={{ textAlign: "center", margin: "0 0 6px 0", fontSize: "20px", color: "white" }}>
          Create Account
        </h2>
        <p style={{ textAlign: "center", margin: "0 0 20px 0", fontSize: "13px", color: "#9ca3af" }}>
          Registering as <strong style={{ color: "#38bdf8", textTransform: "capitalize" }}>{role}</strong>
        </p>

        {error && (
          <div
            style={{
              background: "#7f1d1d",
              color: "#fecaca",
              padding: "10px 14px",
              borderRadius: "10px",
              marginBottom: "15px",
              fontSize: "13px",
              textAlign: "center"
            }}
          >
            {error}
          </div>
        )}

        {/* FULL NAME */}
        <input
          type="text"
          placeholder="Full Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{
            width: "100%",
            padding: "12px 14px",
            marginBottom: "12px",
            background: "#262626",
            color: "white",
            border: "1px solid #404040",
            borderRadius: "10px",
            outline: "none",
            boxSizing: "border-box"
          }}
        />

        {/* EMAIL ID */}
        <input
          type="email"
          placeholder="Email ID"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{
            width: "100%",
            padding: "12px 14px",
            marginBottom: "12px",
            background: "#262626",
            color: "white",
            border: "1px solid #404040",
            borderRadius: "10px",
            outline: "none",
            boxSizing: "border-box"
          }}
        />

        {/* PASSWORD */}
        <div style={{ position: "relative", width: "100%", marginBottom: "12px" }}>
          <input
            type={showPassword ? "text" : "password"}
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{
              width: "100%",
              padding: "12px 42px 12px 14px",
              background: "#262626",
              color: "white",
              border: "1px solid #404040",
              borderRadius: "10px",
              outline: "none",
              boxSizing: "border-box"
            }}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            style={{
              position: "absolute",
              right: "12px",
              top: "50%",
              transform: "translateY(-50%)",
              background: "transparent",
              border: "none",
              color: "#9ca3af",
              cursor: "pointer",
              fontSize: "16px"
            }}
          >
            {showPassword ? <FaEyeSlash /> : <FaEye />}
          </button>
        </div>

        {/* CONFIRM PASSWORD */}
        <div style={{ position: "relative", width: "100%", marginBottom: "12px" }}>
          <input
            type={showConfirmPassword ? "text" : "password"}
            placeholder="Confirm Password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            style={{
              width: "100%",
              padding: "12px 42px 12px 14px",
              background: "#262626",
              color: "white",
              border: "1px solid #404040",
              borderRadius: "10px",
              outline: "none",
              boxSizing: "border-box"
            }}
          />
          <button
            type="button"
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            style={{
              position: "absolute",
              right: "12px",
              top: "50%",
              transform: "translateY(-50%)",
              background: "transparent",
              border: "none",
              color: "#9ca3af",
              cursor: "pointer",
              fontSize: "16px"
            }}
          >
            {showConfirmPassword ? <FaEyeSlash /> : <FaEye />}
          </button>
        </div>

        {/* COLLEGE NAME */}
        <input
          type="text"
          placeholder="College Name"
          value={college}
          onChange={(e) => setCollege(e.target.value)}
          style={{
            width: "100%",
            padding: "12px 14px",
            marginBottom: "12px",
            background: "#262626",
            color: "white",
            border: "1px solid #404040",
            borderRadius: "10px",
            outline: "none",
            boxSizing: "border-box"
          }}
        />

        {/* DEPARTMENT DROPDOWN */}
        <div style={{ marginBottom: "12px" }}>
          <label style={{ fontSize: "12px", color: "#9ca3af", display: "block", marginBottom: "4px" }}>
            Department
          </label>
          <select
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
            style={{
              width: "100%",
              padding: "12px 14px",
              background: "#262626",
              color: "white",
              border: "1px solid #404040",
              borderRadius: "10px",
              outline: "none",
              boxSizing: "border-box"
            }}
          >
            <option value="CSE">CSE (Computer Science & Engg)</option>
            <option value="ECE">ECE (Electronics & Comm Engg)</option>
            <option value="EEE">EEE (Electrical & Electronics Engg)</option>
            <option value="MECH">MECH (Mechanical Engg)</option>
            <option value="IT">IT (Information Technology)</option>
            <option value="CIVIL">CIVIL (Civil Engg)</option>
            <option value="AIDS">AIDS (AI & Data Science)</option>
            <option value="AIML">AIML (AI & Machine Learning)</option>
          </select>
        </div>

        {/* YEAR DROPDOWN */}
        <div style={{ marginBottom: "16px" }}>
          <label style={{ fontSize: "12px", color: "#9ca3af", display: "block", marginBottom: "4px" }}>
            Year (as per role)
          </label>
          <select
            value={year}
            onChange={(e) => setYear(e.target.value)}
            style={{
              width: "100%",
              padding: "12px 14px",
              background: "#262626",
              color: "white",
              border: "1px solid #404040",
              borderRadius: "10px",
              outline: "none",
              boxSizing: "border-box"
            }}
          >
            <option value="1st Year">1st Year</option>
            <option value="2nd Year">2nd Year</option>
            <option value="3rd Year">3rd Year</option>
            <option value="4th Year">4th Year</option>
          </select>
        </div>

        {/* SUBMIT BUTTON */}
        <button
          onClick={handleSignup}
          disabled={loading}
          style={{
            width: "100%",
            padding: "14px",
            borderRadius: "30px",
            border: "none",
            background: "#2563eb",
            color: "white",
            fontWeight: "600",
            fontSize: "15px",
            cursor: loading ? "not-allowed" : "pointer"
          }}
        >
          {loading ? "Creating Account..." : "Create Account"}
        </button>

        <p
          style={{
            textAlign: "center",
            marginTop: "16px",
            fontSize: "14px",
            color: "#9ca3af",
            cursor: "pointer"
          }}
          onClick={() => navigate("/")}
        >
          Already have an account? <span style={{ color: "#38bdf8", textDecoration: "underline" }}>Login</span>
        </p>
      </div>
    </div>
  );
}
