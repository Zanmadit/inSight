import { useEffect, useState } from "react"
import { Navigate, Outlet, useLocation } from "react-router-dom"
import { api } from "@/api/client"
import { useAuthStore } from "@/store/authStore"
import type { User } from "@/types"

export function ProtectedRoute({ role }: { role: "applicant" | "admin" }) {
  const token = useAuthStore((s) => s.token)
  const setUser = useAuthStore((s) => s.setUser)
  const logout = useAuthStore((s) => s.logout)
  const user = useAuthStore((s) => s.user)
  const [checked, setChecked] = useState(false)
  const [me, setMe] = useState<User | null>(user)
  const location = useLocation()

  useEffect(() => {
    let cancelled = false
    async function run() {
      if (!token) {
        setChecked(true)
        return
      }
      try {
        const { data } = await api.get<User>("/auth/me")
        if (!cancelled) {
          setMe(data)
          setUser(data)
        }
      } catch {
        if (!cancelled) logout()
      } finally {
        if (!cancelled) setChecked(true)
      }
    }
    void run()
    return () => {
      cancelled = true
    }
  }, [token, setUser, logout])

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  if (!checked) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">Loading…</div>
    )
  }
  if (!me) {
    return <Navigate to="/login" replace />
  }
  if (me.role !== role) {
    return <Navigate to={me.role === "admin" ? "/admin" : "/dashboard"} replace />
  }
  return <Outlet />
}
