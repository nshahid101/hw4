// Overridable per build via Vite's mode-specific .env files (.env.development
// for `npm run dev`, .env.production for `npm run build`), so the same code
// talks to a local backend in dev and the deployed Render backend in prod.
export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export interface SizeStock {
  size: string;
  quantity: number;
}

export interface Product {
  product_id: string;
  name: string;
  garment_type: string;
  description: string;
  colors: string[];
  search_tags: string[];
  image_url: string;
  price: number;
  inventory: SizeStock[];
  total_stock: number;
}

export interface ChatResponse {
  reply: string;
  products: Product[] | null;
}

export interface PageContext {
  page: "home" | "products" | "product_detail" | "about" | "login" | "create_account";
  product_id?: string;
}

export interface ChatHistoryEntry {
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export async function fetchProducts(): Promise<Product[]> {
  const res = await fetch(`${API_BASE}/api/products`);
  if (!res.ok) throw new Error(`Failed to load products (${res.status})`);
  return res.json();
}

export async function fetchProduct(productId: string): Promise<Product> {
  const res = await fetch(`${API_BASE}/api/products/${productId}`);
  if (!res.ok) throw new Error(`Failed to load product (${res.status})`);
  return res.json();
}

export interface User {
  id: number;
  first_name: string | null;
  last_name: string | null;
  name: string;
  email: string;
}

export interface SignupPayload {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  confirm_password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

async function parseErrorDetail(res: Response, fallback: string): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail) && body.detail[0]?.msg) return body.detail[0].msg;
  } catch {
    // ignore parse errors and fall back
  }
  return fallback;
}

export async function signup(payload: SignupPayload): Promise<User> {
  const res = await fetch(`${API_BASE}/api/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseErrorDetail(res, "Couldn't create account"));
  return res.json();
}

export async function login(payload: LoginPayload): Promise<User> {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseErrorDetail(res, "Couldn't log in"));
  return res.json();
}

export async function sendChatMessage(
  message: string,
  options?: { userId?: number; page?: PageContext }
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, user_id: options?.userId, page: options?.page }),
  });
  if (!res.ok) throw new Error(`Chat request failed (${res.status})`);
  return res.json();
}

export async function fetchChatHistory(userId: number): Promise<ChatHistoryEntry[]> {
  const res = await fetch(`${API_BASE}/api/chat/history?user_id=${userId}`);
  if (!res.ok) throw new Error(`Failed to load chat history (${res.status})`);
  return res.json();
}
