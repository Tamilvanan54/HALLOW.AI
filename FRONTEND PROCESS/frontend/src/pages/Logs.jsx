import { useEffect, useState } from "react";
import axios from "axios";
import { API_BASE_URL } from "../config/api";

export default function Logs() {

  const [logs, setLogs] =
    useState([]);

  const [totalLogins, setTotalLogins] =
    useState(0);

  useEffect(() => {

    fetchLogs();

    const interval =
      setInterval(
        fetchLogs,
        5000
      );

    return () =>
      clearInterval(
        interval
      );

  }, []);

  const fetchLogs = async () => {

    try {

      const response =
        await axios.get(
          `${API_BASE_URL}/logs`
        );

      setTotalLogins(
        response.data.total_logins || 0
      );

      setLogs(
        response.data.recent_logs || []
      );

    } catch (error) {

      console.error(
        "LOG FETCH ERROR:",
        error
      );

    }
  };

  const formatDateTime = (
    timestamp
  ) => {

    if (!timestamp)
      return "-";

    const date =
      new Date(
        timestamp + "Z"
      );

    return date.toLocaleString(
      "en-IN",
      {
        timeZone:
          "Asia/Kolkata",
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: true,
      }
    );
  };

  return (
    <div
      style={{
        padding: "30px",
        color: "white",
        minHeight: "100vh",
        background: "#111827",
      }}
    >
      <h1>
        📊 Audit Logs
      </h1>

      <div
        style={{
          background: "#1e293b",
          padding: "20px",
          borderRadius: "12px",
          width: "250px",
          marginTop: "20px",
          marginBottom: "25px",
        }}
      >
        <h2>
          {totalLogins}
        </h2>

        <p>
          Total Logins
        </p>
      </div>

      <table
        style={{
          width: "100%",
          borderCollapse:
            "collapse",
          background:
            "#1e293b",
        }}
      >
        <thead>
          <tr>
            <th style={thStyle}>
              Date & Time
            </th>

            <th style={thStyle}>
              Action
            </th>

            <th style={thStyle}>
              Email
            </th>

            <th style={thStyle}>
              Role
            </th>
          </tr>
        </thead>

        <tbody>
          {logs.length > 0 ? (

            logs.map(
              (
                log,
                index
              ) => (
                <tr
                  key={
                    index
                  }
                >
                  <td
                    style={
                      tdStyle
                    }
                  >
                    {
                      formatDateTime(
                        log.timestamp
                      )
                    }
                  </td>

                  <td
                    style={
                      tdStyle
                    }
                  >
                    {
                      log.action
                    }
                  </td>

                  <td
                    style={
                      tdStyle
                    }
                  >
                    {
                      log.email
                    }
                  </td>

                  <td
                    style={
                      tdStyle
                    }
                  >
                    {
                      log.role
                    }
                  </td>
                </tr>
              )
            )

          ) : (

            <tr>
              <td
                colSpan="4"
                style={{
                  ...tdStyle,
                  textAlign:
                    "center",
                }}
              >
                No Logs Found
              </td>
            </tr>

          )}
        </tbody>
      </table>
    </div>
  );
}

const thStyle = {
  border:
    "1px solid #334155",
  padding: "12px",
  background:
    "#0f172a",
  textAlign: "left",
  fontSize: "16px",
};

const tdStyle = {
  border:
    "1px solid #334155",
  padding: "12px",
  fontSize: "15px",
};
