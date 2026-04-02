import { create } from "zustand"
import type { User } from "@/types"

const TOKEN_KEY = "invision_token"

interface AuthState {
  token: string | null
  user: User | null
  setAuth: (token: string, user: User) => void
  setUser: (user: User) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: typeof localStorage !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null,
  user: null,
  setAuth: (token, user) => {
    localStorage.setItem(TOKEN_KEY, token)
    set({ token, user })
  },
  setUser: (user) => set({ user }),
  logout: () => {
    localStorage.removeItem(TOKEN_KEY)
    set({ token: null, user: null })
  },
}))

export function getStoredToken(): string | null {
  if (typeof localStorage === "undefined") return null
  return localStorage.getItem(TOKEN_KEY)
}
