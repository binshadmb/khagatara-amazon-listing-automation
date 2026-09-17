"use client";

import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { ProductDraft, ReviewField } from "../lib/types";

const label = (key: string) => key.replaceAll("_", " ").replace(/\b\w/g, char => char.toUpperCase());

function Badge({ field }: { field: ReviewField }) {
  const state = field.review_state;
  const confidence = field.confidence;
  const text = state === "manual" ? "Manual" : state === "accepted" ? "Accepted" : state === "edited" ? "Edited" : state === "conflicting" ? "Conflict" : confidence === null ? "Pending" : confidence >= .9 ? "High" : confidence >= .7 ? "Medium" : "Low";
  return <span className={`badge ${state} ${confidence !== null && confidence < .9 && state !== "manual" ? "warning" : ""}`}>{text}{confidence !== null && state !== "manual" ? ` ${Math.round(confidence * 100)}%` : ""}</span>;
}

export function ProductReview({ draft }: { draft: ProductDraft }) {
  const [fields, setFields] = useState(draft.fields);
  const [notice, setNotice] = useState("");
  const [saving, setSaving] = useState(false);
  useEffect(() => setFields(draft.fields), [draft.id, draft.fields]);

  const update = (attribute: string, next: Partial<ReviewField>) => setFields(current => current.map(field => field.attribute === attribute ? { ...field, ...next } : field));
  const reviewCount = fields.filter(field => ["medium", "pending", "conflicting"].includes(field.review_state)).length;
  const acceptAll = () => setFields(current => current.map(field => ["medium", "pending"].includes(field.review_state) ? { ...field, review_state: "accepted" } : field));
  const saveApproval = async () => {
    setSaving(true);
    setNotice("");
    try {
      const accept = fields.filter(field => field.review_state === "accepted").map(field => field.attribute);
      const edits = Object.fromEntries(fields.filter(field => field.review_state === "edited").map(field => [field.attribute, field.value]));
      const saved = await api.approve(draft.id, accept, edits);
      setFields(saved.fields);
      setNotice(saved.status === "Ready for Amazon" ? "Approval saved. This product is ready for Amazon mapping." : "Saved. Some fields still need attention.");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Could not save the review.");
    } finally {
      setSaving(false);
    }
  };

  return <section className="review"><div className="section-head"><div><h1>{draft.name}</h1><p>{draft.category.replace("_", " ")} · {reviewCount ? `${reviewCount} fields require approval` : "All fields approved"}</p></div><div><button className="secondary" disabled={saving} onClick={saveApproval}>{saving ? "Saving…" : "Save review"}</button><button className="primary" disabled={!reviewCount || saving} onClick={acceptAll}>Accept all suggestions</button></div></div>{notice && <div className="toast success">✓ {notice}</div>}<div className="table-wrap"><table><thead><tr><th>Attribute</th><th>Value</th><th>Source</th><th>Confidence</th><th>Status</th><th>Action</th></tr></thead><tbody>{fields.map(field => <tr key={field.attribute}><td>{label(field.attribute)}</td><td><input value={String(field.value ?? "")} onChange={event => update(field.attribute, { value: event.target.value, review_state: "edited", source: "manual", confidence: 1 })}/></td><td>{field.source}</td><td>{field.confidence === null ? "—" : `${Math.round(field.confidence * 100)}%`}</td><td><Badge field={field}/></td><td><button className="link" onClick={() => update(field.attribute, { review_state: "accepted" })}>Accept</button><button className="link" onClick={() => { const value = window.prompt(`Edit ${label(field.attribute)}`, String(field.value ?? "")); if (value !== null) update(field.attribute, { value, review_state: "edited", source: "manual", confidence: 1 }); }}>Edit</button></td></tr>)}</tbody></table></div></section>;
}
