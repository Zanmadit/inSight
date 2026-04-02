import { Link } from "react-router-dom"
import { useEffect, useState } from "react"
import { api } from "@/api/client"
import { ApplicantDisclaimer } from "@/components/ApplicantDisclaimer"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import type { ApplicantProfile } from "@/types"
import { statusBadgeVariant } from "@/lib/format"

function progressPct(p: ApplicantProfile): number {
  let n = 0
  if (p.full_name?.trim()) n += 20
  if (p.iin?.trim()) n += 10
  if (p.city?.trim()) n += 10
  if (p.gpa != null) n += 10
  if ((p.essay_text || "").trim().length >= 100) n += 25
  if (p.video_url) n += 25
  return n
}

export default function DashboardPage() {
  const [profile, setProfile] = useState<ApplicantProfile | null>(null)

  useEffect(() => {
    void (async () => {
      const { data } = await api.get<ApplicantProfile>("/applicant/profile")
      setProfile(data)
    })()
  }, [])

  if (!profile) return <div className="p-6">Loading…</div>

  const pct = progressPct(profile)
  const st = profile.application_status

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4 md:p-8">
      <ApplicantDisclaimer />
      {st === "accepted" ? (
        <div className="rounded-md border border-green-200 bg-green-50 px-4 py-3 text-green-900">
          🎉 Congratulations! You have been accepted to inVision U.
        </div>
      ) : null}
      {st === "rejected" ? (
        <div className="rounded-md border bg-muted px-4 py-3 text-foreground">
          Your application has been reviewed. Thank you for applying to inVision U.
        </div>
      ) : null}

      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <Badge variant={statusBadgeVariant(st)} className="capitalize">
          {st.replace("_", " ")}
        </Badge>
      </div>

      <div className="space-y-2">
        <p className="text-sm text-muted-foreground">Profile completion</p>
        <Progress value={pct} />
        <p className="text-xs text-muted-foreground">{pct}%</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Link to="/application">
          <Card className="h-full transition hover:border-primary">
            <CardHeader>
              <CardTitle className="text-lg">Complete Your Profile</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">Personal details and GPA</CardContent>
          </Card>
        </Link>
        <Link to="/essay">
          <Card className="h-full transition hover:border-primary">
            <CardHeader>
              <CardTitle className="text-lg">Write Your Essay</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">Draft, AI feedback, video, submit</CardContent>
          </Card>
        </Link>
        <Link to="/status">
          <Card className="h-full transition hover:border-primary">
            <CardHeader>
              <CardTitle className="text-lg">Check Application Status</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">Scores and committee updates</CardContent>
          </Card>
        </Link>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Current status</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={statusBadgeVariant(st)} className="capitalize">
              {st.replace("_", " ")}
            </Badge>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
