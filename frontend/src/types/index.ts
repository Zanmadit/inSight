export interface User {
  id: string
  email: string
  role: string
}

export interface EssayReview {
  id: string
  overall_score: number
  summary_feedback: string
  review_json: Array<{
    criteria: string
    score: number
    max_score: number
    status: string
    recommendation: string
  }>
  strongest_points: string[]
  weakest_points: string[]
  final_suggestion: string
  created_at: string
}

export interface ApplicantProfile {
  id: string
  user_id: string
  full_name: string | null
  iin: string | null
  city: string | null
  gpa: number | null
  essay_text: string | null
  video_url: string | null
  video_filename: string | null
  application_status: string
  is_locked: boolean
  submitted_at: string | null
  final_ai_score: number | null
  ai_summary: string | null
  latest_essay_review: EssayReview | null
  created_at: string
  updated_at: string
}

export interface ApplicantDetail {
  profile: ApplicantProfile & { video_transcript?: string | null }
  email: string
  essay_reviews: EssayReview[]
  latest_decision: {
    id: string
    applicant_profile_id: string
    decision: string
    decision_note: string | null
    decided_by: string
    decided_at: string
  } | null
  video_presigned_url: string | null
  essay_component_score?: number | null
  video_component_score?: number | null
  profile_component_score?: number | null
}

export interface ApplicantListItem {
  id: string
  user_id: string
  email: string
  full_name: string | null
  city: string | null
  gpa: number | null
  application_status: string
  final_ai_score: number | null
  submitted_at: string | null
  created_at: string
}
