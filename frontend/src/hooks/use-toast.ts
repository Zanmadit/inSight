import * as React from "react"

export type ToastMessage = {
  id: string
  title: string
  description?: string
  variant?: "default" | "destructive"
}

const listeners = new Set<React.Dispatch<React.SetStateAction<ToastMessage[]>>>()
let memory: ToastMessage[] = []

function notify() {
  listeners.forEach((l) => l([...memory]))
}

export function toast(msg: Omit<ToastMessage, "id">) {
  const id = crypto.randomUUID()
  memory = [...memory, { id, ...msg }]
  notify()
  setTimeout(() => {
    memory = memory.filter((t) => t.id !== id)
    notify()
  }, 4500)
}

export function useToast() {
  const [toasts, setToasts] = React.useState<ToastMessage[]>(memory)
  React.useEffect(() => {
    listeners.add(setToasts)
    return () => {
      listeners.delete(setToasts)
    }
  }, [])
  return { toasts }
}
