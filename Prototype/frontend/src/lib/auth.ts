const ACCESS_KEY = 'ann_token'
const REFRESH_KEY = 'ann_refresh'

export function getToken(): string | null {
  return localStorage.getItem(ACCESS_KEY)
}

export function setToken(token: string) {
  localStorage.setItem(ACCESS_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY)
}

export function setRefreshToken(token: string) {
  localStorage.setItem(REFRESH_KEY, token)
}

