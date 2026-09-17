"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { AppShell } from "../../../components/AppShell";
import { api } from "../../../lib/api";

const steps = [
  "Source",
  "Category",
  "Auto-Fill",
  "Review",
  "Attributes",
  "Variants",
  "Amazon Mapping",
  "Validation",
  "Preview",
  "Submit",
];

const categories = [
  { value: "kerala_saree", label: "Kerala Saree" },
  { value: "saree", label: "Saree" },
  { value: "women_kurti", label: "Women's Kurti" },
  { value: "women_top", label: "Women's Top" },
];

function NewProductForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const uploadIdParam = searchParams.get("upload_id") ?? undefined;

  const [step, setStep] = useState(0);
  const [category, setCategory] = useState("kerala_saree");
  const [files, setFiles] = useState<File[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function createDraft() {
    if (!files.length && !uploadIdParam) {
      setError("Select at least one source file or upload ID.");
      return;
    }

    setSaving(true);
    setError("");

    try {
      const firstFile = files[0];
      const filename = firstFile ? firstFile.name : (uploadIdParam ? `upload_${uploadIdParam}` : "draft_source");

      const product = await api.createProduct({
        name: name.trim() || filename.replace(/\.[^/.]+$/, ""),
        category,
        description: description.trim() || filename,
        filename,
        upload_id: uploadIdParam,
      });

      router.push(`/review?id=${encodeURIComponent(product.id)}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create product draft.");
    } finally {
      setSaving(false);
    }
  }

  function continueStep() {
    if (step === 0) {
      if (!files.length && !uploadIdParam) {
        setError("Select at least one source file.");
        return;
      }

      setError("");
      setStep(1);
      return;
    }

    if (step === 1) {
      setError("");
      setStep(2);
      return;
    }

    if (step === 2) {
      void createDraft();
      return;
    }

    setStep(current => Math.min(9, current + 1));
  }

  return (
    <div className="content">
      <div className="page-title">
        <div>
          <h1>New product</h1>
          <p>
            Create a local product draft and move it into the review workflow.
          </p>
        </div>
      </div>

      <ol className="steps">
        {steps.map((label, index) => (
          <li
            className={
              index === step
                ? "active"
                : index < step
                  ? "complete"
                  : ""
            }
            key={label}
          >
            <button
              type="button"
              disabled={index > step}
              onClick={() => index <= step && setStep(index)}
            >
              {index + 1}
            </button>
            <span>{label}</span>
          </li>
        ))}
      </ol>

      <section className="panel form-panel">
        {step === 0 && (
          <>
            <h2>Upload source</h2>

            {uploadIdParam && (
              <div className="panel" style={{ marginBottom: "1rem" }}>
                <strong>Associated Upload ID:</strong> {uploadIdParam}
              </div>
            )}

            <label className="drop-zone">
              <input
                type="file"
                multiple
                accept="image/*,.pdf,.csv,.xlsx,.json,.txt"
                onChange={event =>
                  setFiles(Array.from(event.target.files ?? []))
                }
              />

              <b>Drop files here</b>
              <span>Images, PDF, CSV, Excel, JSON, text</span>
              <em>Browse files</em>
            </label>

            {files.map(file => (
              <div className="file-row" key={`${file.name}-${file.size}`}>
                <span>{file.name}</span>

                <span>
                  {Math.ceil(file.size / 1024)} KB
                </span>

                <button
                  type="button"
                  onClick={() =>
                    setFiles(current =>
                      current.filter(item => item !== file)
                    )
                  }
                >
                  Remove
                </button>
              </div>
            ))}
          </>
        )}

        {step === 1 && (
          <>
            <h2>Select category</h2>

            <label>
              Product category

              <select
                value={category}
                onChange={event => setCategory(event.target.value)}
              >
                {categories.map(item => (
                  <option value={item.value} key={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Product name

              <input
                value={name}
                onChange={event => setName(event.target.value)}
                placeholder="Example: Cream Kerala Cotton Kasavu Saree"
              />
            </label>

            <label>
              Description

              <textarea
                value={description}
                onChange={event => setDescription(event.target.value)}
                placeholder="Describe the product..."
                rows={5}
              />
            </label>
          </>
        )}

        {step === 2 && (
          <>
            <h2>Auto-Fill</h2>

            <p>
              The selected source and category will now create a local
              product draft. The existing backend autofill engine will
              populate reviewable fields.
            </p>

            <div className="panel">
              <strong>Category:</strong> {category}
              <br />
              <strong>Source:</strong> {files[0]?.name ?? uploadIdParam ?? "None"}
            </div>
          </>
        )}

        {step > 2 && (
          <>
            <h2>{steps[step]}</h2>

            <p>
              This product is now part of the persisted workflow. Continue
              from the product review screen to resolve the required fields.
            </p>
          </>
        )}

        {error && (
          <div className="panel">
            <strong>Unable to continue</strong>
            <p>{error}</p>
          </div>
        )}

        <div className="form-actions">
          <button
            type="button"
            className="secondary"
            disabled={!step || saving}
            onClick={() => setStep(current => current - 1)}
          >
            Back
          </button>

          <button
            type="button"
            className="primary"
            disabled={saving}
            onClick={continueStep}
          >
            {saving
              ? "Creating draft..."
              : step === 2
                ? "Create draft & open review"
                : "Continue"}
          </button>
        </div>
      </section>
    </div>
  );
}

export default function NewProduct() {
  return (
    <AppShell>
      <Suspense fallback={<div className="content"><p>Loading form...</p></div>}>
        <NewProductForm />
      </Suspense>
    </AppShell>
  );
}
