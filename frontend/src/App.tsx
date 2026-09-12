import { Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { PortalLayout } from './components/PortalLayout'
import { ProtectedRoute } from './components/ProtectedRoute'
import { useAuth } from './context/AuthContext'
import { AnnouncementsPage } from './pages/AnnouncementsPage'
import { ChangePasswordPage } from './pages/ChangePasswordPage'
import { ChiDaoBaoCaoPage } from './pages/ChiDaoBaoCaoPage'
import { DirectivesPage } from './pages/DirectivesPage'
import { DirectiveFormPage } from './pages/DirectiveFormPage'
import { DanhBaPage } from './pages/DanhBaPage'
import { DocumentsPage } from './pages/DocumentsPage'
import { DocumentFormPage } from './pages/DocumentFormPage'
import { DutyRosterPage } from './pages/DutyRosterPage'
import { EducationPage } from './pages/EducationPage'
import { EducationFormPage } from './pages/EducationFormPage'
import { GiaoNhiemVuPage } from './pages/GiaoNhiemVuPage'
import { HomePage } from './pages/HomePage'
import { HuongDanPage } from './pages/HuongDanPage'
import { KenhChiHuyPage } from './pages/KenhChiHuyPage'
import { DispatchFormPage } from './pages/DispatchFormPage'
import { ItemsPage } from './pages/ItemsPage'
import { LoginPage } from './pages/LoginPage'
import { PostsPage } from './pages/PostsPage'
import { PostFormPage } from './pages/PostFormPage'
import { ProfilePage } from './pages/ProfilePage'
import { PublicHomePage } from './pages/PublicHomePage'
import { RegisterPage } from './pages/RegisterPage'
import { UnitsPage } from './pages/UnitsPage'
import { UsersPage } from './pages/UsersPage'
import { AuditLogsPage } from './pages/AuditLogsPage'
import { TinNhanPage } from './pages/TinNhanPage'
import './App.css'

/** '/' : khách chưa đăng nhập -> trang công khai; đã đăng nhập -> bảng tin nội bộ. */
function Landing() {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <Navigate to="/bang-tin" replace /> : <PublicHomePage />
}

/** Chặn mọi màn hình nội bộ cho tới khi tài khoản đổi mật khẩu lần đầu. */
function PasswordGate() {
  const { mustChangePassword } = useAuth()
  if (mustChangePassword) return <Navigate to="/doi-mat-khau" replace />
  return <Outlet />
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route
        path="/doi-mat-khau"
        element={
          <ProtectedRoute>
            <ChangePasswordPage />
          </ProtectedRoute>
        }
      />

      <Route
        element={
          <ProtectedRoute>
            <PasswordGate />
          </ProtectedRoute>
        }
      >
        <Route element={<PortalLayout />}>
          <Route path="/bang-tin" element={<HomePage />} />
          <Route path="/tin-tuc" element={<PostsPage />} />
          <Route path="/tin-tuc/moi" element={<PostFormPage />} />
          <Route path="/tin-tuc/:id/sua" element={<PostFormPage />} />
          <Route path="/thong-bao" element={<AnnouncementsPage />} />
          <Route path="/lich-truc" element={<DutyRosterPage />} />
          <Route path="/danh-ba" element={<DanhBaPage />} />
          <Route path="/van-ban" element={<DocumentsPage />} />
          <Route path="/van-ban/moi" element={<DocumentFormPage />} />
          <Route path="/van-ban/:id/sua" element={<DocumentFormPage />} />
          <Route path="/giao-duc-chinh-tri" element={<EducationPage />} />
          <Route path="/giao-duc-chinh-tri/moi" element={<EducationFormPage />} />
          <Route path="/giao-duc-chinh-tri/:id/sua" element={<EducationFormPage />} />
          <Route path="/chi-thi-nhiem-vu" element={<DirectivesPage />} />
          <Route path="/chi-thi-nhiem-vu/moi" element={<DirectiveFormPage />} />
          <Route path="/chi-thi-nhiem-vu/:id/sua" element={<DirectiveFormPage />} />
          <Route path="/chi-dao-bao-cao" element={<ChiDaoBaoCaoPage />} />
          <Route path="/giao-nhiem-vu" element={<GiaoNhiemVuPage />} />
          <Route path="/kenh-chi-huy" element={<KenhChiHuyPage />} />
          <Route path="/kenh-chi-huy/cong-van/moi" element={<DispatchFormPage />} />
          <Route path="/kenh-chi-huy/cong-van/:id/sua" element={<DispatchFormPage />} />
          <Route path="/ho-so" element={<ProfilePage />} />
          <Route path="/huong-dan" element={<HuongDanPage />} />
          <Route path="/quan-ly-nguoi-dung" element={<UsersPage />} />
          <Route path="/quan-ly-don-vi" element={<UnitsPage />} />
          <Route path="/nhat-ky-an-ninh" element={<AuditLogsPage />} />
          <Route path="/tin-nhan" element={<TinNhanPage />} />
          <Route path="/items" element={<ItemsPage />} />
          <Route path="*" element={<Navigate to="/bang-tin" replace />} />
        </Route>
      </Route>
    </Routes>
  )
}

export default App
