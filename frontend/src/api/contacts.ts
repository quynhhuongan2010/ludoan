import { apiClient } from './client'
import type { ContactBook, ContactPage } from '../types/contact'

export const contactsApi = {
  listBooks: () => apiClient.get<ContactBook[]>('/contact-books'),

  getBook: (bookId: number) => apiClient.get<ContactBook>(`/contact-books/${bookId}`),

  importBook: (file: File, name = '', description = '') => {
    const form = new FormData()
    form.set('name', name)
    form.set('description', description)
    form.set('file', file)
    return apiClient.postForm<ContactBook>('/contact-books', form)
  },

  removeBook: (bookId: number) => apiClient.delete<void>(`/contact-books/${bookId}`),

  listContacts: (
    bookId: number,
    params?: { q?: string; skip?: number; limit?: number },
  ) => {
    const qs = new URLSearchParams()
    if (params?.q) qs.set('q', params.q)
    if (params?.skip !== undefined) qs.set('skip', String(params.skip))
    if (params?.limit !== undefined) qs.set('limit', String(params.limit))
    const s = qs.toString()
    return apiClient.get<ContactPage>(`/contact-books/${bookId}/contacts${s ? `?${s}` : ''}`)
  },
}
