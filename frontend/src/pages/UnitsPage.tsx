import { useEffect, useState, type FormEvent } from 'react'
import { ApiError } from '../api/client'
import { unitsApi } from '../api/units'
import { Field } from '../components/Field'
import { Icon } from '../components/Icon'
import { Modal } from '../components/Modal'
import { useConfirm } from '../context/ConfirmContext'
import { useRequiredFields } from '../hooks/useRequiredFields'
import { UNIT_KIND_LABELS, type Unit, type UnitCreate, type UnitKind } from '../types/unit'

const KINDS = Object.keys(UNIT_KIND_LABELS) as UnitKind[]

const emptyForm: UnitCreate = {
  name: '',
  unit_kind: 'phong_ban',
  description: '',
  is_active: true,
}

export function UnitsPage() {
  const [units, setUnits] = useState<Unit[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState<UnitCreate>(emptyForm)
  const [submitting, setSubmitting] = useState(false)
  const [busyId, setBusyId] = useState<number | null>(null)
  const [showAdd, setShowAdd] = useState(false)
  const confirm = useConfirm()
  const req = useRequiredFields(['name'] as const)

  function openAdd() {
    setForm(emptyForm)
    setError(null)
    req.reset()
    setShowAdd(true)
  }

  function loadUnits() {
    setLoading(true)
    unitsApi
      .list()
      .then(setUnits)
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Không thể tải danh sách đơn vị'),
      )
      .finally(() => setLoading(false))
  }

  useEffect(loadUnits, [])

  async function handleCreate(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (!req.validate({ name: form.name })) return
    setSubmitting(true)
    try {
      const created = await unitsApi.create({ ...form, description: form.description || null })
      setUnits((prev) => [...prev, created])
      setForm(emptyForm)
      setShowAdd(false)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể tạo đơn vị')
    } finally {
      setSubmitting(false)
    }
  }

  async function patch(u: Unit, changes: Partial<UnitCreate>) {
    setError(null)
    setBusyId(u.id)
    try {
      const updated = await unitsApi.update(u.id, {
        name: u.name,
        unit_kind: u.unit_kind,
        description: u.description,
        is_active: u.is_active,
        ...changes,
      })
      setUnits((prev) => prev.map((x) => (x.id === updated.id ? updated : x)))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không cập nhật được đơn vị')
    } finally {
      setBusyId(null)
    }
  }

  async function remove(u: Unit) {
    const ok = await confirm({
      message: (
        <>
          Xoá đơn vị <strong>{u.name}</strong>? Thao tác này không thể hoàn tác.
        </>
      ),
    })
    if (!ok) return
    setError(null)
    setBusyId(u.id)
    try {
      await unitsApi.remove(u.id)
      setUnits((prev) => prev.filter((x) => x.id !== u.id))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không xoá được đơn vị')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <section>
      <h1>Quản lý đơn vị</h1>

      {error ? (
        <p role="alert" className="form-error">
          {error}
        </p>
      ) : null}

      <p className="state-note">
        <Icon name="lock" size={12} /> Đơn vị dùng để gán cho tài khoản (Quản lý người dùng) và phân
        luồng ở Kênh Chỉ đạo – Báo cáo. Không xoá được đơn vị khi vẫn còn tài khoản trực thuộc.
      </p>

      <div className="actions-bar">
        <button type="button" className="btn-create" onClick={openAdd}>
          <Icon name="plus" size={16} /> Thêm đơn vị
        </button>
      </div>

      {showAdd ? (
        <Modal title="Thêm đơn vị" onClose={() => setShowAdd(false)}>
          <form onSubmit={handleCreate} className="entity-form">
            <Field label="Tên đơn vị" required req={req} name="name">
              <input
                type="text"
                maxLength={120}
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                onBlur={(e) => req.mark('name', e.target.value)}
                required
                autoFocus
              />
            </Field>
            <label>
              Loại đơn vị
              <select
                value={form.unit_kind}
                onChange={(e) => setForm((f) => ({ ...f, unit_kind: e.target.value as UnitKind }))}
              >
                {KINDS.map((k) => (
                  <option key={k} value={k}>
                    {UNIT_KIND_LABELS[k]}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Mô tả (tuỳ chọn)
              <input
                type="text"
                maxLength={255}
                value={form.description ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              />
            </label>
            {error ? (
              <p role="alert" className="form-note form-error">
                {error}
              </p>
            ) : null}
            <div className="form-actions">
              <button type="submit" className="btn-submit" disabled={submitting}>
                {submitting ? 'Đang thêm...' : 'Thêm đơn vị'}
              </button>
              <button type="button" className="btn-cancel" onClick={() => setShowAdd(false)}>
                Huỷ
              </button>
            </div>
          </form>
        </Modal>
      ) : null}

      {loading ? (
        <p>Đang tải...</p>
      ) : (
        <table className="users-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Tên đơn vị</th>
              <th>Loại</th>
              <th>Số tài khoản</th>
              <th>Hoạt động</th>
              <th>Hành động</th>
            </tr>
          </thead>
          <tbody>
            {units.map((u) => (
              <tr key={u.id}>
                <td>{u.id}</td>
                <td>{u.name}</td>
                <td>
                  <select
                    value={u.unit_kind}
                    disabled={busyId === u.id}
                    onChange={(e) => patch(u, { unit_kind: e.target.value as UnitKind })}
                  >
                    {KINDS.map((k) => (
                      <option key={k} value={k}>
                        {UNIT_KIND_LABELS[k]}
                      </option>
                    ))}
                  </select>
                </td>
                <td>{u.user_count}</td>
                <td>
                  <label className="switch-cell">
                    <input
                      type="checkbox"
                      checked={u.is_active}
                      disabled={busyId === u.id}
                      onChange={(e) => patch(u, { is_active: e.target.checked })}
                    />
                    {u.is_active ? 'Có' : 'Tạm dừng'}
                  </label>
                </td>
                <td className="row-actions">
                  <button
                    type="button"
                    className="btn-delete"
                    disabled={busyId === u.id || u.user_count > 0}
                    onClick={() => remove(u)}
                  >
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
