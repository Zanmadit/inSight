import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { api } from "@/api/client"
import { ApplicantDisclaimer } from "@/components/ApplicantDisclaimer"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { formatDt, statusBadgeVariant } from "@/lib/format"
import type { ApplicantProfile } from "@/types"

export default function StatusPage() {
  const [profile, setProfile] = useState<ApplicantProfile | null>(null)

  useEffect(() => {
    void (async () => {
      const { data } = await api.get<ApplicantProfile>("/applicant/profile")
      setProfile(data)
    })()
  }, [])

  if (!profile) return <div className="p-6">Loading…</div>

  const submitted = profile.application_status !== "draft"

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-4 md:p-8">
      <ApplicantDisclaimer />
      <h1 className="text-2xl font-semibold">Application status</h1>

      {!submitted ? (
        <Card>
          <CardContent className="pt-6 text-sm">
            You haven&apos;t submitted your application yet.{" "}
            <Link className="text-primary underline" to="/essay">
              Go to essay
            </Link>
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Status
            <Badge variant={statusBadgeVariant(profile.application_status)} className="capitalize">
              {profile.application_status.replace("_", " ")}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {profile.submitted_at ? <p>Submitted: {formatDt(profile.submitted_at)}</p> : null}
          {profile.final_ai_score != null ? (
            <p>
              <span className="font-medium">AI Advisory Score:</span>{" "}
              {Number(profile.final_ai_score).toFixed(1)}
            </p>
          ) : (
            <p className="text-muted-foreground">AI advisory score is processing or unavailable.</p>
          )}
          {profile.ai_summary ? (
            <div className="rounded-md border bg-muted/40 p-3">
              <p className="text-xs font-medium text-muted-foreground">AI summary</p>
              <p className="mt-1 whitespace-pre-wrap">{profile.ai_summary}</p>
            </div>
          ) : null}
          {profile.latest_essay_review ? (
            <div>
              <p className="font-medium">Latest essay review</p>
              <p className="text-muted-foreground">
                Overall: {Number(profile.latest_essay_review.overall_score).toFixed(1)} / 10
              </p>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  )
}
