import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { api } from "@/api/client"
import { ApplicantDisclaimer } from "@/components/ApplicantDisclaimer"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { toast } from "@/hooks/use-toast"
import { useAuthStore } from "@/store/authStore"

export default function RegisterPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [role, setRole] = useState<"applicant" | "admin">("applicant")
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    const next: Record<string, string> = {}
    if (!email) next.email = "Email is required"
    if (password.length < 6) next.password = "Password must be at least 6 characters"
    setErrors(next)
    if (Object.keys(next).length) return
    setLoading(true)
    try {
      const { data } = await api.post("/auth/register", { email, password, role })
      setAuth(data.access_token, data.user)
      toast({ title: "Account created" })
      navigate(role === "admin" ? "/admin" : "/dashboard")
    } catch {
      /* toast via interceptor */
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-4">
      {role === "applicant" ? <ApplicantDisclaimer /> : null}
      <Card>
        <CardHeader>
          <CardTitle>Register</CardTitle>
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
            <div className="space-y-2">
              <Label>Role</Label>
              <Select value={role} onValueChange={(v) => setRole(v as "applicant" | "admin")}>
                <SelectTrigger>
                  <SelectValue placeholder="Role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="applicant">Applicant</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Please wait…" : "Register"}
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-muted-foreground">
            <Link className="text-primary underline" to="/login">
              Login
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
