import type { Announcement } from './announcement'
import type { Directive } from './directive'
import type { DocumentItem } from './document'
import type { EducationMaterial } from './educationMaterial'
import type { Post } from './post'

export interface HomeSummary {
  latest_posts: Post[]
  latest_education_materials: EducationMaterial[]
  latest_directives: Directive[]
  latest_announcements: Announcement[]
}

export interface PublicHome {
  featured_posts: Post[]
  public_announcements: Announcement[]
  public_documents: DocumentItem[]
}
