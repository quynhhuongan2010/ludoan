// Dong bo voi schema `UploadOut` trong openapi.yaml (POST /api/upload).

export interface UploadOut {
  status: 'success'
  /** Ten file da luu tren server, dang <uuid>.<ext>. */
  filename: string
  /** Duong dan phuc vu qua /static, vd /static/common/<uuid>.jpg. */
  url: string
}
