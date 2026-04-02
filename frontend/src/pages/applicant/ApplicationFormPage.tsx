import { useEffect, useState } from "react"
import { api } from "@/api/client"
import { ApplicantDisclaimer } from "@/components/ApplicantDisclaimer"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { toast } from "@/hooks/use-toast"
import type { ApplicantProfile } from "@/types"

export default function ApplicationFormPage() {
  const [profile, setProfile] = useState<ApplicantProfile | null>(null)
  const [fullName, setFullName] = useState("")
  const [iin, setIin] = useState("")
  const [city, setCity] = useState("")
  const [gpa, setGpa] = useState("")
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    void (async () => {
      const { data } = await api.get<ApplicantProfile>("/applicant/profile")
      setProfile(data)
      setFullName(data.full_name || "")
      setIin(data.iin || "")
      setCity(data.city || "")
      setGpa(data.gpa != null ? String(data.gpa) : "")
    })()
  }, [])

  async function save() {
    if (!profile) return
    const next: Record<string, string> = {}
    if (gpa && (Number(gpa) < 0 || Number(gpa) > 5)) next.gpa = "GPA must be between 0 and 5"
    setErrors(next)
    if (Object.keys(next).length) return
    setLoading(true)
    try {
      const { data } = await api.patch<ApplicantProfile>("/applicant/profile", {
        full_name: fullName || null,
        iin: iin || null,
        city: city || null,
        gpa: gpa === "" ? null : Number(gpa),
      })
      setProfile(data)
      toast({ title: "Saved" })
    } finally {
      setLoading(false)
    }
  }

  if (!profile) return <div className="p-6">Loading…</div>

  const locked = profile.is_locked

  return (
    <div className="mx-auto max-w-xl space-y-6 p-4 md:p-8">
      <ApplicantDisclaimer />
      <h1 className="text-2xl font-semibold">Application details</h1>
      {locked ? (
        <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm">
          Your application has been submitted and is now locked.
        </div>
      ) : null}
      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Full Name</Label>
            <Input value={fullName} onChange={(e) => setFullName(e.target.value)} disabled={locked} />
            {errors.full_name ? <p className="text-sm text-red-600">{errors.full_name}</p> : null}
          </div>
          <div className="space-y-2">
            <Label>IIN (Identity Number)</Label>
            <Input value={iin} onChange={(e) => setIin(e.target.value.slice(0, 12))} disabled={locked} maxLength={12} />
            {errors.iin ? <p className="text-sm text-red-600">{errors.iin}</p> : null}
          </div>
          <div className="space-y-2">
            <Label>City</Label>
            <Input value={city} onChange={(e) => setCity(e.target.value)} disabled={locked} />
            {errors.city ? <p className="text-sm text-red-600">{errors.city}</p> : null}
          </div>
          <div className="space-y-2">
            <Label>GPA</Label>
            <Input
              type="number"
              step="0.01"
              min={0}
              max={5}
              value={gpa}
              onChange={(e) => setGpa(e.target.value)}
              disabled={locked}
            />
            {errors.gpa ? <p className="text-sm text-red-600">{errors.gpa}</p> : null}
          </div>
          {!locked ? (
            <Button onClick={() => void save()} disabled={loading}>
              {loading ? "Saving…" : "Save Changes"}
            </Button>
          ) : null}
        </CardContent>
      </Card>
    </div>
  )
}
