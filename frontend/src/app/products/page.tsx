"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "../../components/AppShell";
import { api } from "../../lib/api";
import type { ProductDraft } from "../../lib/types";

export default function ProductsPage() {
  const [products, setProducts] = useState<ProductDraft[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.products();
      setProducts(res.products);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load products from backend.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchProducts();
  }, [fetchProducts]);

  return (
    <AppShell>
      <div className="content">
        <div className="page-title">
          <div>
            <h1>Products</h1>
            <p>Manage product drafts, review status, and Amazon listing preparation.</p>
          </div>
          <Link href="/products/new" className="button primary">
            + New product
          </Link>
        </div>

        {loading && (
          <section className="panel">
            <p>Loading products from backend…</p>
          </section>
        )}

        {error && (
          <section className="panel">
            <p style={{ color: "var(--color-error, #d9534f)" }}>{error}</p>
            <button className="secondary" onClick={() => void fetchProducts()}>
              Retry
            </button>
          </section>
        )}

        {!loading && !error && products.length === 0 && (
          <section className="panel empty">
            <h2>No product drafts found</h2>
            <p>Create your first product draft or upload source files to get started.</p>
            <Link href="/products/new" className="button primary" style={{ marginTop: "1rem" }}>
              Create product draft
            </Link>
          </section>
        )}

        {!loading && !error && products.length > 0 && (
          <section className="panel">
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-color, #ccc)" }}>
                  <th style={{ padding: "0.75rem 0.5rem" }}>Product Name</th>
                  <th style={{ padding: "0.75rem 0.5rem" }}>Category</th>
                  <th style={{ padding: "0.75rem 0.5rem" }}>Status</th>
                  <th style={{ padding: "0.75rem 0.5rem" }}>Action Required</th>
                  <th style={{ padding: "0.75rem 0.5rem" }}>Last Updated</th>
                  <th style={{ padding: "0.75rem 0.5rem", textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {products.map((product) => (
                  <tr key={product.id} style={{ borderBottom: "1px solid var(--border-color, #eee)" }}>
                    <td style={{ padding: "0.75rem 0.5rem", fontWeight: 600 }}>{product.name}</td>
                    <td style={{ padding: "0.75rem 0.5rem" }}>{product.category}</td>
                    <td style={{ padding: "0.75rem 0.5rem" }}>
                      <span className={`status ${product.status.toLowerCase().replace(/\s+/g, "-")}`}>
                        {product.status}
                      </span>
                    </td>
                    <td style={{ padding: "0.75rem 0.5rem" }}>
                      {product.actionRequired && product.actionRequired.length > 0 ? (
                        <span>{product.actionRequired.join(", ")}</span>
                      ) : (
                        <span style={{ opacity: 0.6 }}>None</span>
                      )}
                    </td>
                    <td style={{ padding: "0.75rem 0.5rem", fontSize: "0.875rem", opacity: 0.8 }}>
                      {product.updatedAt}
                    </td>
                    <td style={{ padding: "0.75rem 0.5rem", textAlign: "right" }}>
                      <Link href={`/review?id=${product.id}`} className="button secondary">
                        Review &amp; Approve
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}
      </div>
    </AppShell>
  );
}
