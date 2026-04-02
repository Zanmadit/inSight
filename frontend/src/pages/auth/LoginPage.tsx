import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import axios from "axios"
import { api } from "@/api/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { toast } from "@/hooks/use-toast"
import { useAuthStore } from "@/store/authStore"

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    const next: Record<string, string> = {}
    if (!email) next.email = "Email is required"
    if (!password) next.password = "Password is required"
    setErrors(next)
    if (Object.keys(next).length) return
    setLoading(true)
    try {
      const body = new URLSearchParams()
      body.set("username", email)
      body.set("password", password)
      const { data } = await api.post("/auth/login", body, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      })
      setAuth(data.access_token, data.user)
      toast({ title: "Welcome back" })
      navigate(data.user.role === "admin" ? "/admin" : "/dashboard")
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        toast({ title: "Invalid email or password", variant: "destructive" })
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-4">
      <Card>
        <CardHeader>
          <CardTitle>Login</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={onSubmit}>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
              {errors.email ? <p className="text-sm text-red-600">{errors.email}</p> : null}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              {errors.password ? <p className="text-sm text-red-600">{errors.password}</p> : null}
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Please wait…" : "Login"}
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-muted-foreground">
            <Link className="text-primary underline" to="/register">
              Register
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
