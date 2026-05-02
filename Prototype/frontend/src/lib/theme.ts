const KEY = 'ann_theme'

export type Theme = 'light' | 'dark'

export function getTheme(): Theme {
  const t = localStorage.getItem(KEY)
  return t === 'dark' ? 'dark' : 'light'
}

export function setTheme(theme: Theme) {
  localStorage.setItem(KEY, theme)
  document.documentElement.dataset.theme = theme
}

export function initTheme() {
  document.documentElement.dataset.theme = getTheme()
}

