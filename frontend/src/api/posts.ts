import { apiClient } from './client'
import type { Classification } from '../types/common'
import type { Post, PostCategory, PostCreate, PostReview } from '../types/post'

export const postsApi = {
  list: (params?: {
    skip?: number
    limit?: number
    category?: PostCategory
    classification?: Classification
    statusFilter?: string
  }) => {
    const query = new URLSearchParams()
    if (params?.skip !== undefined) query.set('skip', String(params.skip))
    if (params?.limit !== undefined) query.set('limit', String(params.limit))
    if (params?.category) query.set('category', params.category)
    if (params?.classification) query.set('classification', params.classification)
    if (params?.statusFilter) query.set('status_filter', params.statusFilter)
    const qs = query.toString()
    return apiClient.get<Post[]>(`/posts${qs ? `?${qs}` : ''}`)
  },
  get: (id: number) => apiClient.get<Post>(`/posts/${id}`),
  create: (post: PostCreate) => apiClient.post<Post>('/posts', post),
  update: (id: number, post: PostCreate) => apiClient.put<Post>(`/posts/${id}`, post),
  review: (id: number, payload: PostReview) => apiClient.post<Post>(`/posts/${id}/review`, payload),
  uploadThumbnail: (id: number, file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return apiClient.postForm<Post>(`/posts/${id}/thumbnail`, fd)
  },
  remove: (id: number) => apiClient.delete<void>(`/posts/${id}`),
}
