import { useEffect, useState, type FormEvent } from 'react'
import { ApiError } from '../api/client'
import { itemsApi } from '../api/items'
import { EmptyState } from '../components/EmptyState'
import { Icon } from '../components/Icon'
import { useConfirm } from '../context/ConfirmContext'
import type { Item, ItemCreate } from '../types/item'

const emptyForm: ItemCreate = { name: '', description: '' }

export function ItemsPage() {
  const [items, setItems] = useState<Item[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [form, setForm] = useState<ItemCreate>(emptyForm)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const confirm = useConfirm()

  useEffect(() => {
    let active = true
    itemsApi
      .list()
      .then((data) => {
        if (active) setItems(data)
      })
      .catch((err: unknown) => {
        if (active) setError(err instanceof ApiError ? err.message : 'Failed to load items')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  function startEdit(item: Item) {
    setEditingId(item.id)
    setForm({ name: item.name, description: item.description ?? '' })
  }

  function cancelEdit() {
    setEditingId(null)
    setForm(emptyForm)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      if (editingId !== null) {
        const updated = await itemsApi.update(editingId, form)
        setItems((prev) => prev.map((it) => (it.id === editingId ? updated : it)))
        cancelEdit()
      } else {
        const created = await itemsApi.create(form)
        setItems((prev) => [...prev, created])
        setForm(emptyForm)
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể lưu item')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(id: number) {
    const item = items.find((it) => it.id === id)
    const ok = await confirm({
      message: (
        <>
          Xoá item <strong>{item?.name ?? `#${id}`}</strong>? Thao tác này không thể hoàn tác.
        </>
      ),
    })
    if (!ok) return
    setError(null)
    try {
      await itemsApi.remove(id)
      setItems((prev) => prev.filter((it) => it.id !== id))
      if (editingId === id) cancelEdit()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể xoá item')
    }
  }

  return (
    <section>
      <h1>Quản lý Item</h1>

      <form onSubmit={handleSubmit} className="entity-form">
        <label>
          Tên
          <input
            type="text"
            maxLength={255}
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            required
          />
        </label>
        <label>
          Mô tả
          <input
            type="text"
            maxLength={500}
            value={form.description ?? ''}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
          />
        </label>
        <div className="form-actions">
          <button type="submit" disabled={submitting}>
            {editingId !== null ? 'Cập nhật' : 'Thêm item'}
          </button>
          {editingId !== null ? (
            <button type="button" onClick={cancelEdit}>
              Huỷ
            </button>
          ) : null}
        </div>
      </form>

      {error ? <p role="alert" className="form-error">{error}</p> : null}

      {loading ? (
        <p>Đang tải...</p>
      ) : items.length === 0 ? (
        <EmptyState message="Chưa có item nào." />
      ) : (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Tên</th>
              <th>Mô tả</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td>{item.id}</td>
                <td>{item.name}</td>
                <td>{item.description ?? '—'}</td>
                <td className="row-actions">
                  <button type="button" className="btn-edit" onClick={() => startEdit(item)}>
                    <Icon name="edit" /> Sửa
                  </button>
                  <button type="button" className="btn-delete" onClick={() => handleDelete(item.id)}>
                    <Icon name="trash" /> Xoá
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
