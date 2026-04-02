import axios from "axios"
import { toast } from "@/hooks/use-toast"
import { useAuthStore } from "@/store/authStore"

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"

export const api = axios.create({ baseURL })

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        useAuthStore.getState().logout()
        return Promise.reject(error)
      }
      if (!error.response) {
        toast({
          title: "Unable to connect to the server. Please check your connection.",
          variant: "destructive",
        })
      } else {
        const detail = error.response.data?.detail
        const msg =
          typeof detail === "string"
            ? detail
            : Array.isArray(detail)
              ? detail.map((d: { msg?: string }) => d.msg).join("; ")
              : "Request failed"
        toast({ title: msg, variant: "destructive" })
      }
    }
    return Promise.reject(error)
  }
)
