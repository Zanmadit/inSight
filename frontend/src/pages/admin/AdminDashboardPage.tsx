import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { api } from "@/api/client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface Stats {
  total: number
  draft: number
  submitted: number
  under_review: number
  accepted: number
  rejected: number
}

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null)

  useEffect(() => {
    void (async () => {
      const { data } = await api.get<Stats>("/admin/stats")
      setStats(data)
    })()
  }, [])

  if (!stats) return <div className="p-6">Loading…</div>

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-4 md:p-8">
      <h1 className="text-2xl font-semibold">Admin dashboard</h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Applicants</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats.total}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Submitted</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats.submitted}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Under Review</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats.under_review}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Accepted / Rejected</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {stats.accepted} <span className="text-muted-foreground">/</span> {stats.rejected}
            </p>
            <p className="text-xs text-muted-foreground">Accepted vs rejected</p>
          </CardContent>
        </Card>
      </div>
      <Link className="text-primary underline" to="/admin/applicants">
        View All Applicants →
      </Link>
    </div>
  )
}
