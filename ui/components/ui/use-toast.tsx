// ui/components/ui/use-toast.ts
// Zustand store for managing toasts
import { create } from "zustand"
import { v4 as uuidv4 } from "uuid"

export type ToastProps = {
  id: string
  title?: string
  description?: string
  action?: React.ReactNode
  variant?: "default" | "destructive"
}

type ToastState = {
  toasts: ToastProps[]
  addToast: (toast: Omit<ToastProps, "id">) => void
  dismissToast: (id: string) => void
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  addToast: (toast) =>
    set((state) => ({
      toasts: [...state.toasts, { ...toast, id: uuidv4() }],
    })),
  dismissToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((toast) => toast.id !== id),
    })),
}))

export function useToast() {
  const { addToast, dismissToast, toasts } = useToastStore()

  return {
    toast: addToast,
    dismiss: dismissToast,
    toasts,
  }
}
