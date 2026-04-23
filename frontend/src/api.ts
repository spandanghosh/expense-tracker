const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface Expense {
  id: number;
  amount: string;
  category: string;
  description: string;
  date: string;
  created_at: string;
}

export interface ExpenseCreate {
  amount: string;
  category: string;
  description: string;
  date: string;
}

export interface ProblemDetail {
  type: string;
  title: string;
  status: number;
  detail: string;
}

async function fetchWithTimeout(url: string, options: RequestInit, timeoutMs = 10000): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(id);
  }
}

export async function createExpense(
  body: ExpenseCreate,
  idempotencyKey: string
): Promise<Expense> {
  const options: RequestInit = {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": idempotencyKey,
    },
    body: JSON.stringify(body),
  };

  let resp: Response;
  try {
    resp = await fetchWithTimeout(`${API_BASE}/expenses`, options);
  } catch (err) {
    // single retry on network error
    resp = await fetchWithTimeout(`${API_BASE}/expenses`, options);
  }

  if (!resp.ok) {
    const problem: ProblemDetail = await resp.json();
    throw new Error(problem.detail ?? `HTTP ${resp.status}`);
  }
  return resp.json();
}

export async function listExpenses(params: { category?: string; sort?: string }): Promise<Expense[]> {
  const qs = new URLSearchParams();
  if (params.category) qs.set("category", params.category);
  if (params.sort) qs.set("sort", params.sort);
  const url = `${API_BASE}/expenses${qs.toString() ? `?${qs}` : ""}`;
  const resp = await fetchWithTimeout(url, {});
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}
