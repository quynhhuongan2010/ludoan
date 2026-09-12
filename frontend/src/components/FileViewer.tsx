import { useEffect, useRef, useState } from 'react'
import DOMPurify from 'dompurify'
import { Icon } from './Icon'
import { absolutizeStaticUrl } from '../utils/richContent'
import { getFileKind } from '../utils/fileKind'

// Modal xem truoc noi dung tep ngay trong trinh duyet (PDF da duoc caller mo
// tab moi trong openFileForView, khong vao day):
//  - DOCX -> docx-preview (dung HTML)
//  - XLS/XLSX/CSV -> SheetJS (xlsx) doc va do ra bang HTML theo tung sheet
//  - PPTX -> pptx-preview (dung HTML/canvas)
//  - Anh / .txt -> hien thi truc tiep
//  - Office cu (.doc / .ppt) -> khong co thu vien xem phia client, bao tai ve

interface FileViewerModalProps {
  fileName: string
  fileUrl: string
  title?: string
  onClose: () => void
}

type LoadState = 'loading' | 'ready' | 'error'

export function FileViewerModal({ fileName, fileUrl, title, onClose }: FileViewerModalProps) {
  const kind = getFileKind(fileName)
  const hostRef = useRef<HTMLDivElement>(null)
  const [state, setState] = useState<LoadState>('loading')
  const [message, setMessage] = useState('')
  const absUrl = absolutizeStaticUrl(fileUrl)

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = prevOverflow
    }
  }, [onClose])

  useEffect(() => {
    let cancelled = false
    let pptxPreviewer: { destroy: () => void } | null = null
    const host = hostRef.current

    async function render() {
      setState('loading')
      setMessage('')
      if (!host) return
      host.replaceChildren()

      try {
        if (kind === 'doc' || kind === 'ppt') {
          throw new PreviewUnsupported(
            'Định dạng Office cũ (.doc/.ppt) không xem trực tiếp được. Vui lòng tải tệp về để mở bằng Word/PowerPoint.',
          )
        }

        if (kind === 'image') {
          const img = document.createElement('img')
          img.src = absUrl
          img.alt = title ?? fileName
          img.className = 'file-viewer-image'
          host.append(img)
          if (!cancelled) setState('ready')
          return
        }

        if (kind === 'text') {
          const res = await fetch(absUrl)
          if (!res.ok) throw new Error(String(res.status))
          const raw = await res.text()
          if (cancelled) return
          const pre = document.createElement('pre')
          pre.className = 'file-viewer-text'
          pre.textContent = raw
          host.append(pre)
          setState('ready')
          return
        }

        if (kind === 'pdf') {
          const frame = document.createElement('iframe')
          frame.src = absUrl
          frame.className = 'file-viewer-frame'
          frame.title = title ?? fileName
          host.append(frame)
          if (!cancelled) setState('ready')
          return
        }

        if (kind === 'docx') {
          const res = await fetch(absUrl)
          if (!res.ok) throw new Error(String(res.status))
          const blob = await res.blob()
          if (cancelled) return
          const { renderAsync } = await import('docx-preview')
          if (cancelled) return
          const styleHost = document.createElement('div')
          const bodyHost = document.createElement('div')
          bodyHost.className = 'file-viewer-docx'
          host.append(styleHost, bodyHost)
          await renderAsync(blob, bodyHost, styleHost, {
            className: 'docx',
            inWrapper: true,
            ignoreWidth: false,
            ignoreHeight: false,
            breakPages: true,
            experimental: true,
          })
          if (!cancelled) setState('ready')
          return
        }

        if (kind === 'xlsx' || kind === 'xls') {
          const res = await fetch(absUrl)
          if (!res.ok) throw new Error(String(res.status))
          const buf = await res.arrayBuffer()
          if (cancelled) return
          const XLSX = await import('xlsx')
          if (cancelled) return
          const wb = XLSX.read(new Uint8Array(buf), { type: 'array' })
          if (!wb.SheetNames.length) throw new PreviewUnsupported('Tệp bảng tính rỗng.')

          const tabs = document.createElement('div')
          tabs.className = 'file-viewer-xlsx-tabs'
          const panes: HTMLElement[] = []
          wb.SheetNames.forEach((name, idx) => {
            const btn = document.createElement('button')
            btn.type = 'button'
            btn.textContent = name
            btn.className = idx === 0 ? 'active' : ''
            btn.addEventListener('click', () => {
              tabs.querySelectorAll('button').forEach((b) => b.classList.remove('active'))
              btn.classList.add('active')
              panes.forEach((p, i) => (p.hidden = i !== idx))
            })
            tabs.append(btn)

            const pane = document.createElement('div')
            pane.className = 'file-viewer-sheet'
            pane.hidden = idx !== 0
            pane.innerHTML = DOMPurify.sanitize(XLSX.utils.sheet_to_html(wb.Sheets[name]))
            panes.push(pane)
          })
          host.append(tabs, ...panes)
          if (wb.SheetNames.length < 2) tabs.hidden = true
          if (!cancelled) setState('ready')
          return
        }

        if (kind === 'pptx') {
          const res = await fetch(absUrl)
          if (!res.ok) throw new Error(String(res.status))
          const buf = await res.arrayBuffer()
          if (cancelled) return
          const { init } = await import('pptx-preview')
          if (cancelled) return
          const width = Math.min(host.clientWidth || 960, 960)
          const previewer = init(host, {
            width,
            height: Math.round((width * 9) / 16),
            mode: 'list',
          })
          pptxPreviewer = previewer
          await previewer.preview(buf)
          if (!cancelled) setState('ready')
          return
        }

        throw new PreviewUnsupported('Không hỗ trợ xem trực tiếp định dạng này.')
      } catch (err) {
        if (cancelled) return
        host.replaceChildren()
        setMessage(
          err instanceof PreviewUnsupported
            ? err.message
            : 'Không dựng được bản xem cho tệp này. Bạn có thể tải tệp về để mở.',
        )
        setState('error')
      }
    }

    render()
    return () => {
      cancelled = true
      try {
        pptxPreviewer?.destroy()
      } catch {
        /* bo qua loi don dep */
      }
    }
  }, [absUrl, kind, fileName, title])

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-card file-viewer-card"
        role="dialog"
        aria-modal="true"
        aria-label={title ?? fileName}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-head">
          <h2>{title ?? fileName}</h2>
          <div className="file-viewer-head-actions">
            <a
              className="btn-approve file-viewer-dl"
              href={absUrl}
              target="_blank"
              rel="noreferrer"
              download={fileName}
            >
              <Icon name="download" size={14} /> Tải về
            </a>
            <button type="button" className="modal-close" aria-label="Đóng" onClick={onClose}>
              <Icon name="x" size={18} />
            </button>
          </div>
        </div>
        <div className="modal-body file-viewer-body">
          {state === 'loading' ? <p className="file-viewer-hint">Đang dựng bản xem…</p> : null}
          {state === 'error' ? <p className="form-error">{message}</p> : null}
          <div ref={hostRef} className="file-viewer-host" hidden={state !== 'ready'} />
        </div>
      </div>
    </div>
  )
}

class PreviewUnsupported extends Error {}
