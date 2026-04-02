import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { api } from "@/api/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Progress } from "@/components/ui/progress"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Textarea } from "@/components/ui/textarea"
import { toast } from "@/hooks/use-toast"
import { formatDt, statusBadgeVariant } from "@/lib/format"
import type { ApplicantDetail, ApplicantProfile, EssayReview } from "@/types"
import { useAuthStore } from "@/store/authStore"

export default function ApplicantDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const me = useAuthStore((s) => s.user)
  const [detail, setDetail] = useState<ApplicantDetail | null>(null)
  const [note, setNote] = useState("")
  const [loading, setLoading] = useState(false)
  const [confirm, setConfirm] = useState<null | "accept" | "reject">(null)

  const load = async () => {
    if (!id) return
    const { data } = await api.get<ApplicantDetail>(`/admin/applicants/${id}`)
    setDetail(data)
  }

  useEffect(() => {
    void load()
  }, [id])

  async function patchStatus(status: "under_review" | "accepted" | "rejected") {
    if (!id) return
    setLoading(true)
    try {
      await api.patch<ApplicantProfile>(`/admin/applicants/${id}/status`, {
        status,
        decision_note: note || null,
      })
      toast({ title: "Updated" })
      await load()
      setConfirm(null)
    } finally {
      setLoading(false)
    }
  }

  if (!detail) return <div className="p-6">Loading…</div>

  const p = detail.profile
  const latest = detail.essay_reviews[0]

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4 md:p-8">
      <Button variant="ghost" onClick={() => navigate(-1)}>
        ← Back
      </Button>
      <h1 className="text-2xl font-semibold">{p.full_name || "Applicant"}</h1>

      <Card>
        <CardHeader>
          <CardTitle>Candidate info</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 text-sm sm:grid-cols-2">
          <Field label="Email" value={detail.email} />
          <Field label="Full name" value={p.full_name} />
          <Field label="IIN" value={p.iin} />
          <Field label="City" value={p.city} />
          <Field label="GPA" value={p.gpa != null ? Number(p.gpa).toFixed(2) : "—"} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Essay</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="max-h-64 overflow-y-auto rounded-md border bg-muted/30 p-3 text-sm whitespace-pre-wrap">
            {p.essay_text || "—"}
          </div>
          {latest ? <EssayCriteria review={latest} /> : <p className="text-sm text-muted-foreground">No review</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Video</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {detail.video_presigned_url ? (
            <video className="w-full max-h-96 rounded-md bg-black" controls src={detail.video_presigned_url} />
          ) : (
            <p className="text-sm text-muted-foreground">No video uploaded</p>
          )}
          <details className="rounded-md border p-3 text-sm">
            <summary className="cursor-pointer font-medium">Show transcript</summary>
            <p className="mt-2 whitespace-pre-wrap text-muted-foreground">
              {(p as ApplicantProfile & { video_transcript?: string }).video_transcript || "—"}
            </p>
          </details>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>AI candidate report</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p className="text-3xl font-bold">
            {p.final_ai_score != null ? Number(p.final_ai_score).toFixed(1) : "—"}
          </p>
          <div className="grid gap-2 sm:grid-cols-3">
            <Breakdown label="Essay (0–50)" value={detail.essay_component_score} />
            <Breakdown label="Video (0–30)" value={detail.video_component_score} />
            <Breakdown label="Profile (0–20)" value={detail.profile_component_score} />
          </div>
          <p className="whitespace-pre-wrap">{p.ai_summary || "—"}</p>
          <p className="text-xs text-muted-foreground">
            This score is based solely on essay content, spoken interview quality, and academic GPA. Demographic data
            is not used in scoring.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Decision
            <Badge variant={statusBadgeVariant(p.application_status)} className="capitalize">
              {p.application_status.replace("_", " ")}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <p className="text-sm font-medium">Decision note</p>
            <Textarea value={note} onChange={(e) => setNote(e.target.value)} rows={3} />
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" disabled={loading} onClick={() => void patchStatus("under_review")}>
              Mark as Under Review
            </Button>
            <Button className="bg-green-600 hover:bg-green-700" disabled={loading} onClick={() => setConfirm("accept")}>
              Accept
            </Button>
            <Button variant="destructive" disabled={loading} onClick={() => setConfirm("reject")}>
              Reject
            </Button>
          </div>
          {detail.latest_decision ? (
            <div className="rounded-md border bg-muted/40 p-3 text-xs text-muted-foreground">
              <p>
                Last decision: {detail.latest_decision.decision} by {detail.latest_decision.decided_by}
                {me && detail.latest_decision.decided_by === me.id ? " (you)" : ""}
              </p>
              <p>{formatDt(detail.latest_decision.decided_at)}</p>
              {detail.latest_decision.decision_note ? <p>Note: {detail.latest_decision.decision_note}</p> : null}
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Dialog open={confirm === "accept"} onOpenChange={() => setConfirm(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Accept applicant?</DialogTitle>
            <DialogDescription>This updates the application status to accepted.</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirm(null)}>
              Cancel
            </Button>
            <Button className="bg-green-600" disabled={loading} onClick={() => void patchStatus("accepted")}>
              Confirm Accept
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={confirm === "reject"} onOpenChange={() => setConfirm(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject applicant?</DialogTitle>
            <DialogDescription>This updates the application status to rejected.</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirm(null)}>
              Cancel
            </Button>
            <Button variant="destructive" disabled={loading} onClick={() => void patchStatus("rejected")}>
              Confirm Reject
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function Field({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="font-medium">{value || "—"}</p>
    </div>
  )
}

function Breakdown({ label, value }: { label: string; value?: number | null }) {
  return (
    <div className="rounded-md border p-2">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-lg font-semibold">{value != null ? Number(value).toFixed(1) : "—"}</p>
    </div>
  )
}

function EssayCriteria({ review }: { review: EssayReview }) {
  return (
    <div className="overflow-x-auto">
      <p className="mb-2 text-sm font-medium">Latest essay review — {Number(review.overall_score).toFixed(1)} / 10</p>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Criterion</TableHead>
            <TableHead>Score</TableHead>
            <TableHead>Recommendation</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {review.review_json.map((r) => (
            <TableRow key={r.criteria}>
              <TableCell className="capitalize">{r.criteria.replaceAll("_", " ")}</TableCell>
              <TableCell>
                <div className="w-32 space-y-1">
                  <span className="text-xs">
                    {r.score}/{r.max_score}
                  </span>
                  <Progress value={(r.score / r.max_score) * 100} />
                </div>
              </TableCell>
              <TableCell className="max-w-xs text-xs">{r.recommendation}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
