import { useNavigate } from "react-router-dom";
import { FaGraduationCap, FaChalkboardTeacher, FaUserShield, FaChevronRight } from "react-icons/fa";

export default function SelectRole() {
  const navigate = useNavigate();

  const selectRole = (role) => {
    navigate(`/signup?role=${role}`);
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
          width: "440px",
          padding: "40px",
          borderRadius: "20px",
          background: "#171717",
          border: "1px solid #2f2f2f",
          boxShadow: "0px 0px 30px rgba(0,0,0,0.6)",
          textAlign: "center"
        }}
      >
        {/* LOGO */}
        <div style={{ marginBottom: "25px" }}>
          <img
            src="/havox-full-logo.png"
            alt="HavoxAI Logo"
            style={{
              width: "auto",
              maxWidth: "100%",
              height: "90px",
              objectFit: "contain",
              display: "block",
              margin: "0 auto"
            }}
          />
        </div>

        <h2 style={{ margin: "0 0 8px 0", fontSize: "22px", fontWeight: "600", color: "#f3f4f6" }}>
          Select Your Role
        </h2>
        <p style={{ margin: "0 0 25px 0", fontSize: "14px", color: "#9ca3af" }}>
          Choose your account type to proceed with registration
        </p>

        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          {/* STUDENT CARD */}
          <div
            onClick={() => selectRole("student")}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "16px 20px",
              borderRadius: "14px",
              background: "#262626",
              border: "1px solid #404040",
              cursor: "pointer",
              transition: "all 0.2s ease"
            }}
            onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#3576df")}
            onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#404040")}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
              <div
                style={{
                  width: "44px",
                  height: "44px",
                  borderRadius: "12px",
                  background: "#1e3a8a",
                  color: "#60a5fa",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "20px"
                }}
              >
                <FaGraduationCap />
              </div>
              <div style={{ textAlign: "left" }}>
                <div style={{ fontWeight: "600", fontSize: "16px", color: "white" }}>Student</div>
                <div style={{ fontSize: "12px", color: "#9ca3af", marginTop: "2px" }}>
                  Ask questions & view study materials for your department
                </div>
              </div>
            </div>
            <FaChevronRight style={{ color: "#6b7280", fontSize: "14px" }} />
          </div>

          {/* STAFF CARD */}
          <div
            onClick={() => selectRole("staff")}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "16px 20px",
              borderRadius: "14px",
              background: "#262626",
              border: "1px solid #404040",
              cursor: "pointer",
              transition: "all 0.2s ease"
            }}
            onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#10b981")}
            onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#404040")}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
              <div
                style={{
                  width: "44px",
                  height: "44px",
                  borderRadius: "12px",
                  background: "#065f46",
                  color: "#34d399",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "20px"
                }}
              >
                <FaChalkboardTeacher />
              </div>
              <div style={{ textAlign: "left" }}>
                <div style={{ fontWeight: "600", fontSize: "16px", color: "white" }}>Staff</div>
                <div style={{ fontSize: "12px", color: "#9ca3af", marginTop: "2px" }}>
                  Post documents for departments & manage study materials
                </div>
              </div>
            </div>
            <FaChevronRight style={{ color: "#6b7280", fontSize: "14px" }} />
          </div>

          {/* ADMIN CARD */}
          <div
            onClick={() => selectRole("admin")}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "16px 20px",
              borderRadius: "14px",
              background: "#262626",
              border: "1px solid #404040",
              cursor: "pointer",
              transition: "all 0.2s ease"
            }}
            onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#f59e0b")}
            onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#404040")}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
              <div
                style={{
                  width: "44px",
                  height: "44px",
                  borderRadius: "12px",
                  background: "#78350f",
                  color: "#fbbf24",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "20px"
                }}
              >
                <FaUserShield />
              </div>
              <div style={{ textAlign: "left" }}>
                <div style={{ fontWeight: "600", fontSize: "16px", color: "white" }}>Admin</div>
                <div style={{ fontSize: "12px", color: "#9ca3af", marginTop: "2px" }}>
                  Full administration, user management & system controls
                </div>
              </div>
            </div>
            <FaChevronRight style={{ color: "#6b7280", fontSize: "14px" }} />
          </div>
        </div>

        <button
          onClick={() => navigate("/")}
          style={{
            width: "100%",
            marginTop: "25px",
            padding: "12px",
            borderRadius: "30px",
            background: "transparent",
            border: "1px solid #404040",
            color: "#9ca3af",
            cursor: "pointer",
            fontSize: "14px"
          }}
        >
          ← Back to Login
        </button>
      </div>
    </div>
  );
}
