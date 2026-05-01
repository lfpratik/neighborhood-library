"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string };
  unstable_retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <html>
      <body>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "100vh",
            gap: "16px",
            fontFamily: "system-ui, sans-serif",
            textAlign: "center",
            padding: "24px",
          }}
        >
          <h2 style={{ fontSize: "20px", fontWeight: 600, color: "#1c1917" }}>
            Application error
          </h2>
          <p style={{ fontSize: "14px", color: "#78716c", maxWidth: "360px" }}>
            {error.message || "A critical error occurred. Please reload the page."}
          </p>
          {error.digest && (
            <p style={{ fontSize: "12px", color: "#a8a29e", fontFamily: "monospace" }}>
              Error ID: {error.digest}
            </p>
          )}
          <button
            onClick={() => unstable_retry()}
            style={{
              padding: "8px 16px",
              border: "1px solid #d6d3d1",
              borderRadius: "6px",
              background: "white",
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}
