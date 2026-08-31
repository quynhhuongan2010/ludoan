import { apiClient } from './client'
import type { Item, ItemCreate } from '../types/item'

export const itemsApi = {
  list: (skip = 0, limit = 100) => apiClient.get<Item[]>(`/items?skip=${skip}&limit=${limit}`),
  get: (id: number) => apiClient.get<Item>(`/items/${id}`),
  create: (item: ItemCreate) => apiClient.post<Item>('/items', item),
  update: (id: number, item: ItemCreate) => apiClient.put<Item>(`/items/${id}`, item),
  remove: (id: number) => apiClient.delete<void>(`/items/${id}`),
}
