export interface Item {
  id: number
  name: string
  description: string | null
}

export interface ItemCreate {
  name: string
  description?: string | null
}
