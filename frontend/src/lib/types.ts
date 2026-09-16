export type ReviewState = "manual" | "accepted" | "edited" | "rejected" | "pending" | "medium" | "conflicting";
export type ReviewField = { attribute: string; value: string | number | boolean | null; source: string; confidence: number | null; review_state: ReviewState };
export type ProductDraft = { id: string; name: string; category: string; status: string; updatedAt: string; fields: ReviewField[]; actionRequired: string[]; localIssues: string[] };
export type Category = { id: string; name: string };
