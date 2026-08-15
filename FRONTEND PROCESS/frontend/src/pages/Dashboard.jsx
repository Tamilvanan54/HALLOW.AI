import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import Sidebar from "../components/Sidebar";

export default function Dashboard() {

  const navigate = useNavigate();

  const [totalUsers, setTotalUsers] = useState(0);
  const [totalLogins, setTotalLogins] = useState(0);
  const [totalPDFs, setTotalPDFs] = useState(0);

  const role =
    localStorage.getItem("role") || "";

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {

    try {

      const usersResponse =
        await axios.get(
          "http://127.0.0.1:8000/users"
        );

      setTotalUsers(
        usersResponse.data.length
      );

      const logsResponse =
        await axios.get(
          "http://127.0.0.1:8000/logs"
        );

      setTotalLogins(
        logsResponse.data.total_logins
      );

      const pdfResponse =
        await axios.get(
          "http://127.0.0.1:8000/pdfs"
        );

      setTotalPDFs(
        pdfResponse.data.files.length
      );

    } catch (error) {

      console.error(error);

    }
  };

  return (
    <div
      style={{
        display: "flex",
        background: "#0f172a",
        color: "white",
        minHeight: "100vh",
      }}
    >
      <Sidebar />

      <div
        style={{
          flex: 1,
          padding: "30px",
        }}
      >
        <h1>
          🚀 Welcome to STUDY AI
        </h1>

        <h3>
          Logged in as:{" "}
          {role.toUpperCase()}
        </h3>

        <button
          onClick={loadDashboardData}
          style={{
            marginTop: "10px",
            padding: "10px 20px",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
          }}
        >
          🔄 Refresh Dashboard
        </button>

        <div
          style={{
            display: "flex",
            gap: "20px",
            marginTop: "30px",
            flexWrap: "wrap",
          }}
        >
          <div
            style={{
              background: "#1e293b",
              padding: "25px",
              borderRadius: "12px",
              minWidth: "220px",
            }}
          >
            <h1>{totalUsers}</h1>
            <p>👥 Total Users</p>
          </div>

          <div
            style={{
              background: "#1e293b",
              padding: "25px",
              borderRadius: "12px",
              minWidth: "220px",
            }}
          >
            <h1>{totalLogins}</h1>
            <p>📊 Total Logins</p>
          </div>

          <div
            style={{
              background: "#1e293b",
              padding: "25px",
              borderRadius: "12px",
              minWidth: "220px",
            }}
          >
            <h1>{totalPDFs}</h1>
            <p>📄 Uploaded PDFs</p>
          </div>
        </div>

        {role.toLowerCase() === "admin" && (
          <div
            style={{
              marginTop: "40px",
              background: "#1e293b",
              padding: "25px",
              borderRadius: "12px",
            }}
          >
            <h2>
              🛠 Admin Control Panel
            </h2>

            <hr />

            <p>✅ Users Management</p>

            <p>✅ Audit Logs Monitoring</p>

            <p>✅ PDF Upload Control</p>

            <p>✅ Role Based Access</p>

            <button
              onClick={() =>
                navigate(
                  "/feedback-review"
                )
              }
              style={{
                marginTop: "15px",
                padding: "12px 20px",
                border: "none",
                borderRadius: "8px",
                cursor: "pointer",
                background: "#2563eb",
                color: "white",
                fontWeight: "bold",
              }}
            >
              📢 Feedback Review
            </button>

          </div>
        )}
      </div>
    </div>
  );
}