import { apiClient } from './client'
import type { UploadOut } from '../types/upload'

/**
 * Upload file dung chung (anh minh hoa / tai lieu dinh kem) khong gan module
 * nghiep vu cu the. Yeu cau JWT role `officer` hoac `commander`/`admin`.
 *
 * Dinh dang cho phep:
 *   - anh:      .jpg .jpeg .png .webp .gif
 *   - video:    .mp4 .webm .ogg .mov .m4v  (gioi han rieng MAX_VIDEO_UPLOAD_MB)
 *   - tai lieu: .pdf .doc .docx .xls .xlsx .ppt .pptx
 * Sai dinh dang / vuot gioi han dung luong / file rong -> 400.
 */
export const uploadsApi = {
  upload: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return apiClient.postForm<UploadOut>('/api/upload', fd)
  },
}
