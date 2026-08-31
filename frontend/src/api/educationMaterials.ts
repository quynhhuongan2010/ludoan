import { apiClient } from './client'
import type { EducationCategory, EducationMaterial, EducationMaterialCreate } from '../types/educationMaterial'

export const educationMaterialsApi = {
  list: (params?: { skip?: number; limit?: number; category?: EducationCategory }) => {
    const query = new URLSearchParams()
    if (params?.skip !== undefined) query.set('skip', String(params.skip))
    if (params?.limit !== undefined) query.set('limit', String(params.limit))
    if (params?.category) query.set('category', params.category)
    const qs = query.toString()
    return apiClient.get<EducationMaterial[]>(`/education-materials${qs ? `?${qs}` : ''}`)
  },
  get: (id: number) => apiClient.get<EducationMaterial>(`/education-materials/${id}`),
  create: (material: EducationMaterialCreate) =>
    apiClient.post<EducationMaterial>('/education-materials', material),
  update: (id: number, material: EducationMaterialCreate) =>
    apiClient.put<EducationMaterial>(`/education-materials/${id}`, material),
  remove: (id: number) => apiClient.delete<void>(`/education-materials/${id}`),
}
