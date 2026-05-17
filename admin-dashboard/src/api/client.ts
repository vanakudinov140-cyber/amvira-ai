import axios, { AxiosError } from "axios";

const PRODUCTION_API_URL = "https://retention-v2-ivankudinov.amvera.io";

const configuredUrl =
  import.meta.env.VITE_API_URL?.trim() ||
  import.meta.env.VITE_API_BASE_URL?.trim() ||
  "";

const baseURL =
  configuredUrl ||
  (import.meta.env.PROD ? PRODUCTION_API_URL : "http://127.0.0.1:8000");

if (import.meta.env.DEV) {
  console.info("[retention-admin] API baseURL:", baseURL);
}

export const apiClient = axios.create({
  baseURL,
  timeout: 120000,
  headers: {
    "Content-Type": "application/json",
  },
});

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{
      detail?: string | { msg?: string }[];
      error?: string;
    }>;
    const data = axiosError.response?.data;
    if (typeof data?.error === "string") return data.error;
    const detail = data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
    if (axiosError.message) return axiosError.message;
  }
  if (error instanceof Error) return error.message;
  return "Неизвестная ошибка";
}
