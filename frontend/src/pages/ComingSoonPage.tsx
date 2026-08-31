import { Link } from 'react-router-dom'
import { Icon } from '../components/Icon'

export function ComingSoonPage({ title }: { title: string }) {
  return (
    <div className="block-section coming-soon">
      <Icon name="clipboard" size={40} />
      <h2>{title}</h2>
      <p>Giao diện màn hình này đang được xây dựng ở bước tiếp theo. Chức năng phía máy chủ (API) đã sẵn sàng.</p>
      <Link to="/" className="see-all">
        ← Về trang chủ
      </Link>
    </div>
  )
}
