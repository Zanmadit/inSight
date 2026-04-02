import { Navigate, Route, Routes } from "react-router-dom"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import LoginPage from "@/pages/auth/LoginPage"
import RegisterPage from "@/pages/auth/RegisterPage"
import DashboardPage from "@/pages/applicant/DashboardPage"
import ApplicationFormPage from "@/pages/applicant/ApplicationFormPage"
import EssayPage from "@/pages/applicant/EssayPage"
import StatusPage from "@/pages/applicant/StatusPage"
import AdminDashboardPage from "@/pages/admin/AdminDashboardPage"
import ApplicantsListPage from "@/pages/admin/ApplicantsListPage"
import ApplicantDetailPage from "@/pages/admin/ApplicantDetailPage"

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route element={<ProtectedRoute role="applicant" />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/application" element={<ApplicationFormPage />} />
        <Route path="/essay" element={<EssayPage />} />
        <Route path="/status" element={<StatusPage />} />
      </Route>

      <Route element={<ProtectedRoute role="admin" />}>
        <Route path="/admin" element={<AdminDashboardPage />} />
        <Route path="/admin/applicants" element={<ApplicantsListPage />} />
        <Route path="/admin/applicants/:id" element={<ApplicantDetailPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}
