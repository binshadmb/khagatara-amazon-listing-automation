import type { Category, ProductDraft } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
  });

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;

    try {
      const body = await res.json();
      if (typeof body?.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // Keep the HTTP status message when the response is not JSON.
    }

    throw new Error(detail);
  }

  return res.json() as Promise<T>;
}

export type VariantOptionInput = {
  value: string;
  code: string;
};

export type VariantDimensionInput = {
  attribute: string;
  options: VariantOptionInput[];
};

export type VariantRequest = {
  base_sku: string;
  dimensions: VariantDimensionInput[];
  excluded_combinations?: Record<string, string>[];
};

export type VariantResult = {
  id: string;
  status: string;
  updatedAt: string;
  variants: {
    sku: string;
    attributes: Record<string, string>;
  }[];
};

export type ValidationIssue = {
  field: string;
  code: string;
  message: string;
};

export type ValidationResult = {
  valid: boolean;
  issues: ValidationIssue[];
};

export type MappingResult = {
  id: string;
  status: string;
  updatedAt: string;
  [key: string]: unknown;
};

export type PreviewResult = {
  id: string;
  sku: string;
  productType: string;
  payload: Record<string, unknown>;
  valid: boolean;
  issues: ValidationIssue[];
};

export type SubmissionResult = {
  id: string;
  status: string;
  submitted: boolean;
  [key: string]: unknown;
};

export type CreateProductRequest = {
  name?: string;
  category: string;
  description?: string;
  filename?: string;
  attributes?: Record<string, unknown>;
  upload_id?: string;
};

export type UploadResult = {
  id: string;
  filename: string;
  storedFilename: string;
  contentType: string;
  size: number;
  status: string;
};

export const api = {
  health: () =>
    request<{ status: string }>("/api/health"),

  categories: () =>
    request<{ categories: Category[] }>("/api/categories"),

  products: () =>
    request<{ products: ProductDraft[] }>("/api/products"),

  upload: async (file: File): Promise<UploadResult> => {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(`${API_URL}/api/uploads`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      let detail = `Upload failed (${res.status})`;

      try {
        const body = await res.json();

        if (typeof body?.detail === "string") {
          detail = body.detail;
        }
      } catch {
        // Keep the HTTP status message.
      }

      throw new Error(detail);
    }

    return res.json() as Promise<UploadResult>;
  },

  createProduct: (product: CreateProductRequest) =>
    request<ProductDraft>("/api/products", {
      method: "POST",
      body: JSON.stringify(product),
    }),

  product: (id: string) =>
    request<ProductDraft>(`/api/products/${id}`),

  ingest: (id: string) =>
    request<{
      product_id: string;
      upload_id: string;
      source_file: string;
      ingestion: {
        source_type: string;
        text: string;
        metadata: Record<string, unknown>;
      };
    }>(`/api/products/${id}/ingest`, {
      method: "POST",
    }),

  approve: (
    id: string,
    accept: string[],
    edits: Record<string, unknown>,
  ) =>
    request<ProductDraft>(
      `/api/products/${id}/review/approve`,
      {
        method: "POST",
        body: JSON.stringify({ accept, edits }),
      },
    ),

  generateVariants: (
    id: string,
    variantRequest: VariantRequest,
  ) =>
    request<VariantResult>(
      `/api/products/${id}/variants/generate`,
      {
        method: "POST",
        body: JSON.stringify(variantRequest),
      },
    ),

  map: (
    id: string,
    mappingRequest: Record<string, unknown>,
  ) =>
    request<MappingResult>(
      `/api/products/${id}/mapping`,
      {
        method: "POST",
        body: JSON.stringify(mappingRequest),
      },
    ),

  validate: (id: string) =>
    request<ValidationResult>(
      `/api/products/${id}/validate`,
    ),

  preview: (id: string) =>
    request<PreviewResult>(
      `/api/products/${id}/preview`,
    ),

  submit: (id: string) =>
    request<SubmissionResult>(
      `/api/products/${id}/submit`,
      {
        method: "POST",
      },
    ),

  API_URL,
};