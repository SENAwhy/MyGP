const TOKEN_KEY = 'aiops_token'

let _onUnauthorized = null

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function removeToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export function setOnUnauthorized(cb) {
  _onUnauthorized = cb
}

export async function apiFetch(path, options = {}) {
  const token = getToken()
  const headers = { ...(options.headers || {}) }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  // Don't set Content-Type for form POST (login)
  if (!headers['Content-Type'] && options.method !== 'POST') {
    headers['Content-Type'] = 'application/json'
  }

  const res = await fetch(path, { ...options, headers })

  if (res.status === 401) {
    removeToken()
    if (_onUnauthorized) _onUnauthorized()
    throw new Error('认证过期')
  }

  return res.json()
}
