import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('zx_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code === 0) {
        return body.data
      }
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    return body
  },
  (error) => {
    const status = error.response?.status
    const message = error.response?.data?.message || error.message || '网络异常，请稍后重试'
    if (status === 401) {
      localStorage.removeItem('zx_token')
      localStorage.removeItem('zx_user')
      if (!window.location.pathname.startsWith('/login')) {
        const redirect = encodeURIComponent(window.location.pathname + window.location.search)
        window.location.href = `/login?redirect=${redirect}`
      }
    }
    return Promise.reject(new Error(message))
  },
)

export const authApi = {
  register: (payload) => api.post('/auth/register', payload),
  login: (payload) => api.post('/auth/login', payload),
  sendCode: (email) => api.post('/auth/send-code', { email }),
  resetPassword: (payload) => api.post('/auth/reset-password', payload),
}

export const userApi = {
  me: () => api.get('/users/me'),
  update: (payload) => api.put('/users/me', payload),
  favorites: () => api.get('/users/me/favorites'),
  learning: () => api.get('/users/me/learning'),
  orders: () => api.get('/users/me/orders'),
}

export const courseApi = {
  list: (params) => api.get('/courses', { params }),
  detail: (id) => api.get(`/courses/${id}`),
  toggleFavorite: (id) => api.post(`/courses/${id}/favorite`),
  getProgress: (id) => api.get(`/courses/${id}/progress`),
  updateProgress: (id, payload) => api.put(`/courses/${id}/progress`, payload),
  comments: (id, params) => api.get(`/courses/${id}/comments`, { params }),
  addComment: (id, payload) => api.post(`/courses/${id}/comments`, payload),
}

export const aiApi = {
  chat: (payload) => api.post('/ai/chat', payload),
  conversations: () => api.get('/ai/conversations'),
  conversation: (id) => api.get(`/ai/conversations/${id}`),
  learningPath: (payload) => api.post('/ai/learning-path', payload),
  grade: (payload) => api.post('/ai/grade', payload),
  report: (payload) => api.post('/ai/study-report', payload),
}

export const jobApi = {
  list: (params) => api.get('/jobs', { params }),
  detail: (id) => api.get(`/jobs/${id}`),
  apply: (id) => api.post(`/jobs/${id}/apply`),
}

export const metaApi = {
  filters: () => api.get('/meta/filters'),
}

export const adminApi = {
  stats: () => api.get('/admin/stats'),
  users: (params) => api.get('/admin/users', { params }),
  updateRole: (id, role) => api.patch(`/admin/users/${id}/role`, { role }),
  updateUserStatus: (id, isActive) => api.patch(`/admin/users/${id}/status`, { is_active: isActive }),
  courses: (params) => api.get('/admin/courses', { params }),
  courseDetail: (id) => api.get(`/admin/courses/${id}`),
  createCourse: (payload) => api.post('/admin/courses', payload),
  updateCourse: (id, payload) => api.put(`/admin/courses/${id}`, payload),
  deleteCourse: (id) => api.delete(`/admin/courses/${id}`),
  createChapter: (id, payload) => api.post(`/admin/courses/${id}/chapters`, payload),
  updateChapter: (chapterId, payload) => api.put(`/admin/chapters/${chapterId}`, payload),
  deleteChapter: (chapterId) => api.delete(`/admin/chapters/${chapterId}`),
  teachers: () => api.get('/admin/teachers'),
  updateCourseStatus: (id, status) => api.patch(`/admin/courses/${id}/status`, { status }),
  orders: (params) => api.get('/admin/orders', { params }),
  orderDetail: (id) => api.get(`/admin/orders/${id}`),
  updateOrderStatus: (id, status) => api.patch(`/admin/orders/${id}/status`, { status }),
  applications: (params) => api.get('/admin/applications', { params }),
}

export const notificationApi = {
  list: (params) => api.get('/notifications', { params }),
  unreadCount: () => api.get('/notifications/unread-count'),
  read: (id) => api.post(`/notifications/${id}/read`),
  readAll: () => api.post('/notifications/read-all'),
}

export default api