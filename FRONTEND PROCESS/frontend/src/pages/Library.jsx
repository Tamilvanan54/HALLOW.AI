import { useState, useEffect } from "react";
import axios from "axios";
import { API_BASE_URL } from "../config/api";

export default function Library() {

  const role = localStorage
    .getItem("role")
    ?.toLowerCase();

  const [file, setFile] =
    useState(null);

  const [pdfs, setPdfs] =
    useState([]);

  const [uploading, setUploading] =
    useState(false);

  useEffect(() => {

    fetchPDFs();

  }, []);

  const fetchPDFs = async () => {

    try {

      const response =
        await axios.get(
          `${API_BASE_URL}/pdfs`
        );

      setPdfs(
        response.data.files
      );

    } catch (error) {

      console.error(error);

    }
  };

  const uploadPDF = async () => {

    if (!file) {
      alert("Please select a PDF file first!");
      return;
    }

    const formData =
      new FormData();

    formData.append(
      "pdf",
      file
    );

    try {

      setUploading(true);

      const response = await axios.post(
        `${API_BASE_URL}/upload-pdf`,
        formData,
        {
          headers: {
            "Content-Type":
              "multipart/form-data",
          },
        }
      );

      if (response.data && response.data.status === false) {
        alert(response.data.message || "Failed to upload PDF.");
      } else {
        await fetchPDFs();
        setFile(null);
        alert("PDF Uploaded and processed successfully!");
      }

    } catch (error) {

      console.error(error);
      alert("Failed to upload PDF. Please make sure the backend is running.");

    } finally {

      setUploading(false);

    }
  };

  const deletePDF = async (
    filename
  ) => {

    const confirmDelete =
      window.confirm(
        `Delete ${filename} ?`
      );

    if (!confirmDelete)
      return;

    try {

      await axios.delete(
        `${API_BASE_URL}/delete-pdf`,
        {
          params: {
            filename,
          },
        }
      );

      fetchPDFs();

    } catch (error) {

      console.error(error);

    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#212121",
        color: "white",
        padding: "30px",
      }}
    >
      <h1
        style={{
          color: "#3b82f6",
          marginBottom: "25px",
        }}
      >
        📚 PDF Library
      </h1>

      {(role === "admin" ||
        role === "staff") && (
        <div
          style={{
            background:
              "#2f2f2f",
            padding: "20px",
            borderRadius:
              "15px",
            marginBottom:
              "25px",
          }}
        >
          <input
            type="file"
            accept=".pdf"
            onChange={(e) =>
              setFile(
                e.target.files[0]
              )
            }
            style={{
              color: "white",
            }}
          />

          <br />
          <br />

          <button
            onClick={uploadPDF}
            disabled={uploading}
            style={{
              background:
                uploading ? "#6b7280" : "#2563eb",
              color: "white",
              border: "none",
              padding:
                "10px 20px",
              borderRadius:
                "10px",
              cursor:
                uploading ? "not-allowed" : "pointer",
            }}
          >
            {uploading ? "Uploading & Processing..." : "Upload PDF"}
          </button>

          {file && (
            <p
              style={{
                marginTop:
                  "15px",
              }}
            >
              📄 {file.name}
            </p>
          )}
        </div>
      )}

      <div
        style={{
          background: "#2f2f2f",
          borderRadius: "15px",
          padding: "20px",
        }}
      >
        <h2
          style={{
            color: "#3b82f6",
            marginBottom:
              "20px",
          }}
        >
          Uploaded Files
        </h2>

        {pdfs.length > 0 ? (
          pdfs.map(
            (
              pdf,
              index
            ) => (
              <div
                key={index}
                style={{
                  display:
                    "flex",
                  justifyContent:
                    "space-between",
                  alignItems:
                    "center",
                  background:
                    "#3a3a3a",
                  padding:
                    "15px",
                  borderRadius:
                    "10px",
                  marginBottom:
                    "10px",
                }}
              >
                <span>
  📄 {pdf}
</span>

<div
  style={{
    display: "flex",
    gap: "10px",
    alignItems: "center",
  }}
>

  <button
    onClick={() =>
      window.open(
        `${API_BASE_URL}/view-pdf/${pdf}`,
        "_blank"
      )
    }
    style={{
      background: "#2563eb",
      color: "white",
      border: "none",
      padding: "8px 15px",
      borderRadius: "8px",
      cursor: "pointer",
    }}
  >
    View PDF
  </button>

  {(role === "admin" ||
    role === "staff") && (
    <button
      onClick={() =>
        deletePDF(pdf)
      }
      style={{
        background: "#dc2626",
        color: "white",
        border: "none",
        padding: "8px 15px",
        borderRadius: "8px",
        cursor: "pointer",
      }}
    >
      Delete
    </button>
  )}

</div>
              </div>
            )
          )
        ) : (
          <div
            style={{
              textAlign:
                "center",
              padding:
                "20px",
              color:
                "#9ca3af",
            }}
          >
            No PDF Files Uploaded
          </div>
        )}
      </div>
    </div>
  );
}
