import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import MainLayout from '../layouts/MainLayout.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: '', name: 'courses', component: () => import('../views/CourseListView.vue') },
      { path: 'courses/:id', name: 'course-detail', component: () => import('../views/CourseDetailView.vue') },
      {
        path: 'ai',
        name: 'ai',
        component: () => import('../views/AiAssistantView.vue'),
        meta: { auth: true },
      },
      {
        path: 'report',
        name: 'report',
        component: () => import('../views/ReportView.vue'),
        meta: { auth: true },
      },
      { path: 'jobs', name: 'jobs', component: () => import('../views/JobListView.vue') },
      {
        path: 'admin',
        name: 'admin',
        component: () => import('../views/AdminView.vue'),
        meta: { auth: true, roles: ['admin', 'teacher'] },
      },
    ],
  },
  { path: '/login', name: 'login', component: () => import('../views/LoginView.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to) => {
  const token = localStorage.getItem('zx_token')
  if (to.meta.auth && !token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.roles) {
    let role = ''
    try {
      role = JSON.parse(localStorage.getItem('zx_user') || 'null')?.role || ''
    } catch (error) {
      role = ''
    }
    // 角色已知且不在允许列表内则拦截；角色缺失时放行，由页面 fetchMe 后二次校验
    if (role && !to.meta.roles.includes(role)) {
      ElMessage.warning('该页面仅管理员与教师可访问')
      return { name: 'courses' }
    }
  }
  if (to.name === 'login' && token) {
    return { name: 'courses' }
  }
  return true
})

export default router