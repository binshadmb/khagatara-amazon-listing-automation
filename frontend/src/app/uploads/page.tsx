"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "../../components/AppShell";
import { api } from "../../lib/api";

const MAX_FILE_SIZE = 25 * 1024 * 1024;

const ACCEPTED = [
  ".jpg",
  ".jpeg",
  ".png",
  ".webp",
  ".gif",
  ".pdf",
  ".csv",
  ".xlsx",
  ".json",
  ".txt",
];

export default function UploadsPage() {
  const router = useRouter();

  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [uploaded, setUploaded] = useState<string[]>([]);

  function addFiles(selected: File[]) {
    setError("");

    const invalid = selected.find(file => {
      const extension =
        "." + file.name.split(".").pop()?.toLowerCase();

      return (
        !ACCEPTED.includes(extension) ||
        file.size > MAX_FILE_SIZE
      );
    });

    if (invalid) {
      const extension =
        "." + invalid.name.split(".").pop()?.toLowerCase();

      if (!ACCEPTED.includes(extension)) {
        setError(`Unsupported file type: ${invalid.name}`);
      } else {
        setError(`${invalid.name} exceeds the 25 MB limit.`);
      }

      return;
    }

    setFiles(current => [...current, ...selected]);
  }

  async function uploadFiles() {
    if (!files.length) {
      setError("Select at least one file.");
      return;
    }

    setUploading(true);
    setError("");

    try {
      const results = [];

      for (const file of files) {
        const result = await api.upload(file);
        results.push(result);
      }

      setUploaded(results.map(result => result.id));

      /*
       * The upload layer is now complete.
       * Product creation remains a separate workflow step.
       */
      const firstId = results[0]?.id;
      router.push(firstId ? `/products/new?upload_id=${encodeURIComponent(firstId)}` : "/products/new");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to upload source files.",
      );
    } finally {
      setUploading(false);
    }
  }

  return (
    <AppShell>
      <div className="content">
        <div className="page-title">
          <div>
            <h1>Uploads</h1>
            <p>
              Upload product source material for listing preparation.
            </p>
          </div>
        </div>

        <section className="panel form-panel">
          <h2>Source files</h2>

          <label className="drop-zone">
            <input
              type="file"
              multiple
              accept={ACCEPTED.join(",")}
              onChange={event =>
                addFiles(Array.from(event.target.files ?? []))
              }
            />

            <b>Drop files here</b>
            <span>
              Images, PDF, CSV, Excel, JSON, or text
            </span>
            <em>Browse files</em>
          </label>

          {files.map((file, index) => (
            <div
              className="file-row"
              key={`${file.name}-${file.size}-${index}`}
            >
              <span>{file.name}</span>

              <span>
                {Math.ceil(file.size / 1024)} KB
              </span>

              <button
                type="button"
                onClick={() =>
                  setFiles(current =>
                    current.filter((_, i) => i !== index),
                  )
                }
              >
                Remove
              </button>
            </div>
          ))}

          {error && (
            <div className="panel">
              <strong>Upload error</strong>
              <p>{error}</p>
            </div>
          )}

          {uploaded.length > 0 && (
            <div className="panel">
              <strong>Upload complete</strong>
              <p>
                {uploaded.length} source file
                {uploaded.length === 1 ? "" : "s"} uploaded.
              </p>
            </div>
          )}

          <div className="form-actions">
            <button
              type="button"
              className="secondary"
              onClick={() => router.push("/products")}
            >
              Cancel
            </button>

            <button
              type="button"
              className="primary"
              disabled={!files.length || uploading}
              onClick={() => void uploadFiles()}
            >
              {uploading ? "Uploading..." : "Upload & continue"}
            </button>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
