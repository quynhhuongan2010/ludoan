import { absolutizeStaticUrl } from './richContent'

// Phan loai tep theo duoi ten + tien ich mo xem truoc.
//  - PDF  -> mo lien ket /static xem truc tiep tren tab moi (browser tu render)
//  - DOCX / XLS(X) / CSV / PPTX -> xem bang thu vien trong <FileViewerModal>
//  - Anh / .txt -> hien thi truc tiep trong modal
//  - Office cu (.doc / .ppt) -> khong co thu vien xem phia client, bao tai ve

export type FileKind =
  | 'pdf'
  | 'docx'
  | 'doc'
  | 'xlsx'
  | 'xls'
  | 'pptx'
  | 'ppt'
  | 'image'
  | 'text'
  | 'other'

const IMAGE_EXT = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg', 'avif']
const TEXT_EXT = ['txt', 'md', 'markdown', 'log', 'csv']

export function getFileExt(fileName: string): string {
  const clean = fileName.split(/[?#]/)[0]
  const dot = clean.lastIndexOf('.')
  return dot >= 0 ? clean.slice(dot + 1).toLowerCase() : ''
}

export function getFileKind(fileName: string): FileKind {
  const ext = getFileExt(fileName)
  if (ext === 'pdf') return 'pdf'
  if (ext === 'docx') return 'docx'
  if (ext === 'doc') return 'doc'
  if (ext === 'xlsx') return 'xlsx'
  if (ext === 'xls') return 'xls'
  if (ext === 'pptx') return 'pptx'
  if (ext === 'ppt') return 'ppt'
  if (IMAGE_EXT.includes(ext)) return 'image'
  if (TEXT_EXT.includes(ext)) return 'text'
  return 'other'
}

/** True khi co the xem truoc (ke ca PDF mo tab moi). */
export function canPreviewFile(fileName: string): boolean {
  const kind = getFileKind(fileName)
  return kind !== 'doc' && kind !== 'ppt' && kind !== 'other'
}

/** Mo tep de xem: PDF sang tab moi, con lai bao cho caller mo modal.
 *  Tra ve true neu da xu ly (PDF), false neu caller can mo <FileViewerModal>. */
export function openFileForView(fileName: string, fileUrl: string): boolean {
  if (getFileKind(fileName) === 'pdf') {
    window.open(absolutizeStaticUrl(fileUrl), '_blank', 'noopener,noreferrer')
    return true
  }
  return false
}
