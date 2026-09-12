import type { ReactNode } from 'react'
import { Icon, type IconName } from './Icon'

interface EmptyStateProps {
  message: ReactNode
  icon?: IconName
}

export function EmptyState({ message, icon = 'file' }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <Icon name={icon} size={40} />
      <p>{message}</p>
    </div>
  )
}
