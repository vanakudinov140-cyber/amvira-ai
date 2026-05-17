import { useCallback, useEffect, useState } from "react";

export type ToastVariant = "default" | "success" | "destructive";

export interface ToastItem {
  id: string;
  title: string;
  description?: string;
  variant?: ToastVariant;
}

type Listener = (toasts: ToastItem[]) => void;

let memoryState: ToastItem[] = [];
const listeners = new Set<Listener>();

function emit() {
  listeners.forEach((l) => l(memoryState));
}

export function toast({
  title,
  description,
  variant = "default",
}: Omit<ToastItem, "id">) {
  const id = crypto.randomUUID();
  memoryState = [{ id, title, description, variant }, ...memoryState].slice(0, 5);
  emit();
  window.setTimeout(() => dismiss(id), 4500);
  return id;
}

export function dismiss(id: string) {
  memoryState = memoryState.filter((t) => t.id !== id);
  emit();
}

export function useToast() {
  const [state, setState] = useState<ToastItem[]>(memoryState);

  useEffect(() => {
    listeners.add(setState);
    return () => {
      listeners.delete(setState);
    };
  }, []);

  const dismissToast = useCallback((id: string) => dismiss(id), []);

  return { toasts: state, dismiss: dismissToast };
}
