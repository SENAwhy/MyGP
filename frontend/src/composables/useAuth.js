import { ref } from 'vue'
import { getToken, setToken, removeToken, setOnUnauthorized } from '@/api'

const isLoggedIn = ref(!!getToken())
const loginUser = ref('')
const loginPass = ref('')
const loginError = ref('')
const isLoggingIn = ref(false)

export function useAuth() {
  function doLogout() {
    removeToken()
    isLoggedIn.value = false
    loginError.value = ''
  }

  async function doLogin() {
    isLoggingIn.value = true
    loginError.value = ''
    try {
      const body = new URLSearchParams()
      body.append('username', loginUser.value)
      body.append('password', loginPass.value)

      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString(),
      })

      if (!res.ok) {
        const data = await res.json()
        loginError.value = data.detail || '用户名或密码错误'
        isLoggingIn.value = false
        return
      }

      const data = await res.json()
      setToken(data.access_token)
      isLoggedIn.value = true
    } catch (e) {
      loginError.value = '无法连接到服务器，请检查后端是否启动。'
    } finally {
      isLoggingIn.value = false
    }
  }

  // Register 401 interceptor callback
  setOnUnauthorized(() => {
    isLoggedIn.value = false
  })

  return {
    isLoggedIn,
    loginUser,
    loginPass,
    loginError,
    isLoggingIn,
    doLogin,
    doLogout,
  }
}
