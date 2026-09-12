// Sinh slug SEO tu chuoi tieng Viet: bo dau, ha thuong, thay khoang trang / ky
// tu la bang dau gach ngang. Khop voi _slugify o backend (post_service.py) - chi
// dung de goi y truoc cho nguoi dung; backend van la nguon sinh slug cuoi cung
// (va tu them hau to -2, -3... neu trung).
export function slugify(input: string): string {
  return (input || '')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '') // bo dau ket hop
    .replace(/[đ]/g, 'd') // đ
    .replace(/[Đ]/g, 'd') // Đ
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/-{2,}/g, '-')
    .replace(/^-+|-+$/g, '')
}
