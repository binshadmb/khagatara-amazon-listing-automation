"use client";

import { useCallback, useEffect, useState } from "react";
import { AppShell } from "../components/AppShell";
import { ProductReview } from "../components/ProductReview";
import { api } from "../lib/api";
import type { ProductDraft } from "../lib/types";

const workflow = ["Source", "Category", "Auto-Fill", "Review", "Attributes", "Variants", "Amazon Mapping", "Validation", "Preview", "Submit"];

export default function Home() {
  const [products, setProducts] = useState<ProductDraft[]>([]);
  const [connected, setConnected] = useState<"checking" | "connected" | "offline">("checking");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      await api.health();
      setConnected("connected");
      const result = await api.products();
      setProducts(result.products);
    } catch (reason) {
      setConnected("offline");
      setError(reason instanceof Error ? reason.message : "Could not reach the backend.");
      setProducts([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  const reviewRequired = products.filter(product => product.status === "Review required").length;
  const ready = products.filter(product => product.status === "Ready for Amazon").length;
  const draft = products[0];
  const cards = [
    ["Total Products", products.length, "info"],
    ["Review Required", reviewRequired, "warning"],
    ["Ready for Amazon", ready, "success"],
  ];

  return <AppShell><div className="content"><div className="page-title"><div><h1>Dashboard</h1><p>Prepare product listings without routine Seller Central data entry.</p></div><span className={`status ${connected}`}>{connected === "connected" ? "● Backend connected" : connected === "checking" ? "◌ Checking backend" : "● Backend unavailable"}</span></div><div className="cards">{cards.map(([name, value, kind]) => <article className={`card ${kind}`} key={String(name)}><span>{name}</span><strong>{value}</strong></article>)}</div><div className="grid"><section className="panel workflow"><h2>Product workflow</h2><ol>{workflow.map((step, index) => <li className={index < 3 ? "done" : index === 3 ? "current" : ""} key={step}><b>{index + 1}</b>{step}</li>)}</ol></section><section className="panel"><h2>Recent activity</h2>{products.slice(0, 2).map(product => <div className="activity" key={product.id}><b>{product.name}</b><span>{product.status}</span><em>{product.updatedAt}</em></div>)}{!loading && !products.length && <p>No product drafts yet.</p>}</section></div>{loading && <section className="panel"><p>Loading products…</p></section>}{error && <section className="panel"><p>Backend connection failed: {error}</p><button className="secondary" onClick={() => void refresh()}>Retry</button></section>}{draft && !loading && <ProductReview draft={draft}/>}</div></AppShell>;
}
