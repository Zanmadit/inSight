import { useEffect, useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import { api } from "@/api/client"
import { ApplicantDisclaimer } from "@/components/ApplicantDisclaimer"
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
import type { ApplicantProfile, EssayReview } from "@/types"

function canSubmit(p: ApplicantProfile, draftEssay: string): boolean {
  if (p.is_locked) return false
  if (!(p.full_name || "").trim()) return false
  if (!(p.iin || "").trim()) return false
  if (!(p.city || "").trim()) return false
  if (p.gpa == null) return false
  const essay = (draftEssay || p.essay_text || "").trim()
  if (essay.length < 100) return false
  if (!p.video_url) return false
  if (!p.latest_essay_review) return false
  return true
}

export default function EssayPage() {
  const [profile, setProfile] = useState<ApplicantProfile | null>(null)
  const [text, setText] = useState("")
  const [review, setReview] = useState<EssayReview | null>(null)
  const [loadingSave, setLoadingSave] = useState(false)
  const [loadingReview, setLoadingReview] = useState(false)
  const [loadingSubmit, setLoadingSubmit] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const navigate = useNavigate()

  const load = async () => {
    const { data } = await api.get<ApplicantProfile>("/applicant/profile")
    setProfile(data)
    setText(data.essay_text || "")
    if (data.latest_essay_review) setReview(data.latest_essay_review)
  }

  useEffect(() => {
    void load()
  }, [])

  const words = useMemo(() => (text.trim() ? text.trim().split(/\s+/).length : 0), [text])
  const chars = text.length

  async function saveDraft() {
    if (!profile || profile.is_locked) return
    setLoadingSave(true)
    try {
      const { data } = await api.patch<ApplicantProfile>("/applicant/essay", { essay_text: text })
      setProfile(data)
      if (data.latest_essay_review) setReview(data.latest_essay_review)
      toast({ title: "Draft saved" })
    } finally {
      setLoadingSave(false)
    }
  }

  async function checkEssay() {
    if (!profile || profile.is_locked) return
    await saveDraft()
    setLoadingReview(true)
    try {
      const { data } = await api.post<EssayReview>("/applicant/essay/review")
      setReview(data)
      await load()
      toast({ title: "AI feedback ready" })
    } finally {
      setLoadingReview(false)
    }
  }

  async function onUpload(f: File) {
    if (!profile || profile.is_locked) return
    setUploading(true)
    try {
      const fd = new FormData()
      fd.append("file", f)
      await api.post("/applicant/video", fd, { headers: { "Content-Type": "multipart/form-data" } })
      toast({ title: "Video uploaded", description: "Transcription in progress." })
      await load()
    } finally {
      setUploading(false)
    }
  }

  async function doSubmit() {
    setLoadingSubmit(true)
    try {
      await api.post("/applicant/submit")
      toast({ title: "Submitted" })
      navigate("/status")
    } finally {
      setLoadingSubmit(false)
      setConfirmOpen(false)
    }
  }

  if (!profile) return <div className="p-6">Loading…</div>

  const locked = profile.is_locked
  const submitEnabled = canSubmit(profile, text)

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4 md:p-8">
      <ApplicantDisclaimer />
      <h1 className="text-2xl font-semibold">Essay & submission</h1>
      {locked ? (
        <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm">
          Your application has been submitted and is now locked.
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Your essay</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              rows={12}
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={locked}
              className="min-h-[200px]"
            />
            <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
              <span>
                {words} words / recommended 300–800
              </span>
              <span>{chars} characters</span>
            </div>
            {!locked ? (
              <div className="flex flex-wrap gap-2">
                <Button variant="secondary" disabled={loadingSave} onClick={() => void saveDraft()}>
                  {loadingSave ? "Saving…" : "Save Draft"}
                </Button>
                <Button disabled={loadingReview} onClick={() => void checkEssay()}>
                  {loadingReview ? "Checking…" : "Check My Essay"}
                </Button>
              </div>
            ) : null}
            {!locked ? (
              <div className="space-y-2">
                <label className="text-sm font-medium">Upload video (MP4, WebM, QuickTime)</label>
                <InputFile onFile={(file) => void onUpload(file)} disabled={uploading || locked} />
                {uploading ? <p className="text-sm text-muted-foreground">Uploading…</p> : null}
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>AI review</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {!review ? (
              <p className="text-sm text-muted-foreground">
                Your AI feedback will appear here after you click &apos;Check My Essay&apos;.
              </p>
            ) : (
              <>
                <p className="text-2xl font-semibold">
                  {Number(review.overall_score).toFixed(1)} / 10
                </p>
                <p className="text-sm">{review.summary_feedback}</p>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Criterion</TableHead>
                        <TableHead>Score</TableHead>
                        <TableHead>Note</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {review.review_json.map((r) => (
                        <TableRow key={r.criteria}>
                          <TableCell className="capitalize">{r.criteria.replaceAll("_", " ")}</TableCell>
                          <TableCell>
                            <div className="space-y-1">
                              <span className="text-xs">
                                {r.score}/{r.max_score}
                              </span>
                              <Progress value={(r.score / r.max_score) * 100} />
                            </div>
                          </TableCell>
                          <TableCell className="max-w-xs text-xs text-muted-foreground">
                            {r.recommendation}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
                <div>
                  <p className="mb-1 text-sm font-medium text-green-700">Strongest points</p>
                  <ul className="list-inside list-disc text-sm">
                    {review.strongest_points.map((s) => (
                      <li key={s}>{s}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="mb-1 text-sm font-medium text-amber-700">Weakest points</p>
                  <ul className="list-inside list-disc text-sm">
                    {review.weakest_points.map((s) => (
                      <li key={s}>{s}</li>
                    ))}
                  </ul>
                </div>
                <div className="rounded-md border bg-muted/50 p-3 text-sm">{review.final_suggestion}</div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {!locked ? (
        <div className="flex justify-end border-t pt-6">
          <Button variant="destructive" disabled={!submitEnabled || loadingSubmit} onClick={() => setConfirmOpen(true)}>
            Submit Application
          </Button>
        </div>
      ) : null}

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Submit Your Application?</DialogTitle>
            <DialogDescription>
              After submission, you will not be able to edit your application. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" onClick={() => setConfirmOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" disabled={loadingSubmit} onClick={() => void doSubmit()}>
              {loadingSubmit ? "Submitting…" : "Submit Application"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function InputFile({ onFile, disabled }: { onFile: (f: File) => void; disabled?: boolean }) {
  return (
    <input
      type="file"
      accept="video/mp4,video/webm,video/quicktime"
      disabled={disabled}
      onChange={(e) => {
        const f = e.target.files?.[0]
        if (f) onFile(f)
        e.target.value = ""
      }}
    />
  )
}
