"use client";

import { useCallback, useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { AppShell } from "../../components/AppShell";
import { ProductReview } from "../../components/ProductReview";
import { api } from "../../lib/api";
import type { ProductDraft } from "../../lib/types";

function ReviewContent() {
  const searchParams = useSearchParams();
  const selectedId = searchParams.get("id");

  const [products, setProducts] = useState<ProductDraft[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<ProductDraft | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.products();
      setProducts(res.products);

      if (selectedId) {
        const found = res.products.find((p) => p.id === selectedId);
        if (found) {
          setSelectedProduct(found);
        } else {
          // Fetch directly if not in list
          const p = await api.product(selectedId);
          setSelectedProduct(p);
        }
      } else if (res.products.length > 0) {
        setSelectedProduct(res.products[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load product for review.");
    } finally {
      setLoading(false);
    }
  }, [selectedId]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  return (
    <div className="content">
      <div className="page-title">
        <div>
          <h1>Review Queue</h1>
          <p>Approve, edit, or resolve detected attribute suggestions before Amazon mapping.</p>
        </div>
      </div>

      {loading && (
        <section className="panel">
          <p>Loading review queue...</p>
        </section>
      )}

      {error && (
        <section className="panel">
          <p style={{ color: "var(--color-error, #d9534f)" }}>{error}</p>
          <button className="secondary" onClick={() => void loadData()}>
            Retry
          </button>
        </section>
      )}

      {!loading && !error && products.length === 0 && (
        <section className="panel empty">
          <h2>Review Queue Empty</h2>
          <p>There are no products waiting for review at this time.</p>
        </section>
      )}

      {!loading && !error && products.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {products.length > 1 && (
            <div className="panel" style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
              <label htmlFor="product-select" style={{ fontWeight: 600 }}>Select Product:</label>
              <select
                id="product-select"
                value={selectedProduct?.id ?? ""}
                onChange={(e) => {
                  const p = products.find((prod) => prod.id === e.target.value);
                  if (p) setSelectedProduct(p);
                }}
                style={{ padding: "0.5rem", borderRadius: "4px", border: "1px solid var(--border-color, #ccc)" }}
              >
                {products.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.status})
                  </option>
                ))}
              </select>
            </div>
          )}

          {selectedProduct && <ProductReview draft={selectedProduct} />}
        </div>
      )}
    </div>
  );
}

export default function ReviewPage() {
  return (
    <AppShell>
      <Suspense fallback={<div className="content"><p>Loading page...</p></div>}>
        <ReviewContent />
      </Suspense>
    </AppShell>
  );
}
