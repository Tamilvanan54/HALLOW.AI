import { useEffect, useState } from "react";
import axios from "axios";
import { API_BASE_URL } from "../config/api";

export default function Users() {

  const [users, setUsers] =
    useState([]);

  const [search, setSearch] =
    useState("");

  useEffect(() => {

    fetchUsers();

  }, []);

  const fetchUsers = async () => {

    try {

      const response =
        await axios.get(
          `${API_BASE_URL}/users`
        );

      setUsers(
        response.data
      );

    } catch (error) {

      console.error(error);

    }
  };

  const deleteUser = async (
    userId
  ) => {

    const confirmDelete =
      window.confirm(
        "Are you sure you want to delete this user?"
      );

    if (!confirmDelete)
      return;

    try {

      await axios.delete(
        `${API_BASE_URL}/delete-user/${userId}`
      );

      fetchUsers();

    } catch (error) {

      console.error(error);

    }
  };

  const filteredUsers =
    users.filter(
      (user) =>
        user.name
          .toLowerCase()
          .includes(
            search.toLowerCase()
          ) ||
        user.email
          .toLowerCase()
          .includes(
            search.toLowerCase()
          )
    );

  const getRoleColor = (
    role
  ) => {

    const r =
      role.toLowerCase();

    if (r === "admin")
      return "#ef4444";

    if (r === "staff")
      return "#f59e0b";

    return "#22c55e";
  };

  return (
    <div
      style={{
        padding: "30px",
        background:
          "#0f172a",
        minHeight: "100vh",
        color: "white",
      }}
    >
      <h1>
        👥 Users Management
      </h1>

      <div
        style={{
          background:
            "#1e293b",
          padding: "20px",
          borderRadius:
            "12px",
          width: "250px",
          marginTop: "20px",
          marginBottom:
            "25px",
        }}
      >
        <h2>
          {users.length}
        </h2>

        <p>
          Total Users
        </p>
      </div>
       
      <input
  type="text"
  placeholder="Search user by name or email..."
  value={search}
  onChange={(e) =>
    setSearch(
      e.target.value
    )
  }
  style={{
    width: "350px",
    padding: "12px",
    borderRadius: "10px",
    border: "none",
    outline: "none",
    marginBottom: "25px",

    color: "#000000",          // ADD THIS
  }}
/>

      <table
        style={{
          width: "100%",
          borderCollapse:
            "collapse",
          background:
            "#1e293b",
          borderRadius:
            "12px",
          overflow:
            "hidden",
        }}
      >
        <thead>
          <tr>
            <th style={thStyle}>
              ID
            </th>

            <th style={thStyle}>
              Name
            </th>

            <th style={thStyle}>
              Email
            </th>

            <th style={thStyle}>
              Role
            </th>

            <th style={thStyle}>
              Action
            </th>
          </tr>
        </thead>

        <tbody>
          {filteredUsers.length >
          0 ? (
            filteredUsers.map(
              (user) => (
                <tr
                  key={
                    user.id
                  }
                >
                  <td
                    style={
                      tdStyle
                    }
                  >
                    {
                      user.id
                    }
                  </td>

                  <td
                    style={
                      tdStyle
                    }
                  >
                    {
                      user.name
                    }
                  </td>

                  <td
                    style={
                      tdStyle
                    }
                  >
                    {
                      user.email
                    }
                  </td>

                  <td
                    style={
                      tdStyle
                    }
                  >
                    <span
                      style={{
                        background:
                          getRoleColor(
                            user.role
                          ),
                        padding:
                          "5px 12px",
                        borderRadius:
                          "20px",
                        fontSize:
                          "13px",
                      }}
                    >
                      {
                        user.role
                      }
                    </span>
                  </td>

                  <td
                    style={
                      tdStyle
                    }
                  >
                    <button
                      onClick={() =>
                        deleteUser(
                          user.id
                        )
                      }
                      style={{
                        background:
                          "#dc2626",
                        color:
                          "white",
                        border:
                          "none",
                        padding:
                          "8px 15px",
                        borderRadius:
                          "8px",
                        cursor:
                          "pointer",
                      }}
                    >
                      🗑 Delete
                    </button>
                  </td>
                </tr>
              )
            )
          ) : (
            <tr>
              <td
                colSpan="5"
                style={{
                  textAlign:
                    "center",
                  padding:
                    "20px",
                }}
              >
                No Users Found
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

const thStyle = {
  padding: "15px",
  textAlign: "left",
  borderBottom:
    "1px solid #334155",
};

const tdStyle = {
  padding: "15px",
  borderBottom:
    "1px solid #334155",
};
