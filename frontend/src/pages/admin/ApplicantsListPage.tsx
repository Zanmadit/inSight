import { useEffect, useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { api } from "@/api/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { formatDt, statusBadgeVariant } from "@/lib/format"
import type { ApplicantListItem } from "@/types"

interface ListResp {
  items: ApplicantListItem[]
  total: number
  page: number
  page_size: number
}

export default function ApplicantsListPage() {
  const [data, setData] = useState<ListResp | null>(null)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState("")
  const [debounced, setDebounced] = useState("")
  const [tab, setTab] = useState<string>("all")

  useEffect(() => {
    const t = setTimeout(() => setDebounced(search), 300)
    return () => clearTimeout(t)
  }, [search])

  useEffect(() => {
    void (async () => {
      const params: Record<string, string | number> = { page, page_size: 20 }
      if (debounced) params.search = debounced
      if (tab !== "all") params.status = tab
      const { data: d } = await api.get<ListResp>("/admin/applicants", { params })
      setData(d)
    })()
  }, [page, debounced, tab])

  const totalPages = useMemo(() => (data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1), [data])

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4 md:p-8">
      <h1 className="text-2xl font-semibold">Applicants</h1>
      <Card>
        <CardContent className="space-y-4 pt-6">
          <Input
            placeholder="Search name or email…"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(1)
            }}
          />
          <Tabs value={tab} onValueChange={(v) => { setTab(v); setPage(1) }}>
            <TabsList className="flex flex-wrap h-auto gap-1">
              {["all", "draft", "submitted", "under_review", "accepted", "rejected"].map((s) => (
                <TabsTrigger key={s} value={s} className="capitalize">
                  {s.replace("_", " ")}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>

          {!data ? (
            <p>Loading…</p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>City</TableHead>
                    <TableHead>GPA</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>AI Score</TableHead>
                    <TableHead>Submitted</TableHead>
                    <TableHead />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.items.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell>{row.full_name || "—"}</TableCell>
                      <TableCell className="max-w-[180px] truncate">{row.email}</TableCell>
                      <TableCell>{row.city || "—"}</TableCell>
                      <TableCell>{row.gpa != null ? Number(row.gpa).toFixed(2) : "—"}</TableCell>
                      <TableCell>
                        <Badge variant={statusBadgeVariant(row.application_status)} className="capitalize">
                          {row.application_status.replace("_", " ")}
                        </Badge>
                      </TableCell>
                      <TableCell>{row.final_ai_score != null ? Number(row.final_ai_score).toFixed(1) : "—"}</TableCell>
                      <TableCell>{formatDt(row.submitted_at)}</TableCell>
                      <TableCell>
                        <Button asChild size="sm" variant="outline">
                          <Link to={`/admin/applicants/${row.id}`}>View</Link>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}

          <div className="flex items-center justify-between gap-2">
            <span className="text-sm text-muted-foreground">
              Page {data?.page ?? 1} of {totalPages} ({data?.total ?? 0} total)
            </span>
            <div className="flex gap-2">
              <Button variant="outline" disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>
                Previous
              </Button>
              <Button
                variant="outline"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
