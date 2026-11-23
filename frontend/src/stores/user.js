import { defineStore } from 'pinia'
import { authApi, userApi } from '../api'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('zx_token') || '',
    user: JSON.parse(localStorage.getItem('zx_user') || 'null'),
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.token),
    displayName: (state) => state.user?.nickname || state.user?.username || '同学',
    roleLabel: (state) => {
      const labels = { student: '学生', teacher: '教师', admin: '管理员' }
      return labels[state.user?.role] || '学生'
    },
  },
  actions: {
    setAuth(data) {
      this.token = data.access_token
      this.user = data.user
      localStorage.setItem('zx_token', data.access_token)
      localStorage.setItem('zx_user', JSON.stringify(data.user))
    },
    async login(payload) {
      const data = await authApi.login(payload)
      this.setAuth(data)
      return data
    },
    async register(payload) {
      const data = await authApi.register(payload)
      this.setAuth(data)
      return data
    },
    async fetchMe() {
      if (!this.token) return null
      const data = await userApi.me()
      this.user = data
      localStorage.setItem('zx_user', JSON.stringify(data))
      return data
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('zx_token')
      localStorage.removeItem('zx_user')
    },
  },
})