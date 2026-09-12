import { useState, type InputHTMLAttributes } from 'react'
import { Icon } from './Icon'

type PasswordInputProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'>

/**
 * O nhap mat khau kem nut con mat de an/hien noi dung.
 * Dung thay cho <input type="password" /> trong moi form co mat khau.
 */
export function PasswordInput(props: PasswordInputProps) {
  const [visible, setVisible] = useState(false)

  return (
    <span className="password-field">
      <input
        autoCapitalize="none"
        autoCorrect="off"
        spellCheck={false}
        {...props}
        type={visible ? 'text' : 'password'}
      />
      <button
        type="button"
        className="password-toggle"
        onClick={() => setVisible((v) => !v)}
        aria-label={visible ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
        title={visible ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
        tabIndex={-1}
      >
        <Icon name={visible ? 'eye-off' : 'eye'} size={16} />
      </button>
    </span>
  )
}
