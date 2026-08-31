import { CLASSIFICATION_LABELS, type Classification } from '../types/common'
import { Icon } from './Icon'

export function ClassificationBadge({ value }: { value: Classification }) {
  return (
    <span className={`class-badge class-${value}`}>
      {value === 'mat' ? <Icon name="lock" size={11} /> : null}
      {CLASSIFICATION_LABELS[value]}
    </span>
  )
}
