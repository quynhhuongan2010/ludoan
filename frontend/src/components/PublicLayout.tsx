import { type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { CONTACT, UNIT } from '../config/unit'
import { Icon } from './Icon'

export function PublicLayout({ children }: { children: ReactNode }) {
  return (
    <div className="portal">
      <div className="main-header">
        <div className="container header-content">
          <div className="unit-brand">
            <span className="unit-logo" aria-hidden="true">
              <img src="/logo-bdbp.png" alt="" onError={(e) => (e.currentTarget.style.display = 'none')} />
              <Icon name="star" size={40} className="unit-logo-fallback" />
            </span>
            <div className="unit-titles">
              <p className="unit-kicker">{UNIT.shortName}</p>
              <h1>{UNIT.fullName}</h1>
              <p className="unit-slogan">{UNIT.slogan}</p>
            </div>
          </div>
          <div className="header-user public-cta">
            <Link to="/login" className="btn-ghost">
              <Icon name="user" size={13} /> Đăng nhập
            </Link>
            <Link to="/register" className="btn-solid">
              Đăng ký tài khoản
            </Link>
          </div>
        </div>
      </div>

      <div className="public-band">
        <div className="container">
          <Icon name="shield" size={14} /> Trang thông tin công khai. Đăng nhập để xem tin nội bộ, chỉ thị và
          tài liệu của đơn vị.
        </div>
      </div>

      <main className="container portal-main">{children}</main>

      <footer className="main-footer">
        <div className="container footer-grid">
          <div className="footer-col">
            <h4>{UNIT.shortName}</h4>
            <p>{UNIT.fullName}</p>
            <p>© Bản quyền nội bộ thuộc {UNIT.copyrightOwner}.</p>
          </div>
          <div className="footer-col">
            <h4>Thông tin liên hệ</h4>
            <p>Địa chỉ: {CONTACT.address}</p>
            <p>Điện thoại nội bộ: {CONTACT.internalPhone}</p>
            <p>Email: {CONTACT.email}</p>
          </div>
          <div className="footer-col">
            <h4>Truy cập</h4>
            <p>
              <Link to="/login">Đăng nhập hệ thống</Link>
            </p>
            <p>
              <Link to="/register">Đăng ký tài khoản mới</Link>
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
