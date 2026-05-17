import axios, { AxiosError } from "axios";

const configuredUrl =
  import.meta.env.VITE_API_URL?.trim() || import.meta.env.VITE_API_BASE_URL?.trim() || "";

// Production demo: пустой URL → same-origin (nginx проксирует API)
const baseURL = configuredUrl || (import.meta.env.PROD ? "" : "http://127.0.0.1:8000");

if (import.meta.env.DEV) {
  console.info("[retention-admin] API baseURL:", baseURL || window.location.origin);
}

export const apiClient = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string | { msg?: string }[] }>;
    const detail = axiosError.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
    if (axiosError.message) return axiosError.message;
  }
  if (error instanceof Error) return error.message;
  return "Неизвестная ошибка";
}
