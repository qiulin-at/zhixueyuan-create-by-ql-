<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { notificationApi } from '../api'
import { useUserStore } from '../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const baseNavs = [
  { name: '课程中心', path: '/', match: (path) => path === '/' || path.startsWith('/courses') },
  { name: '实习就业', path: '/jobs', match: (path) => path.startsWith('/jobs') },
  { name: 'AI 学习助手', path: '/ai', match: (path) => path.startsWith('/ai'), badge: 'AI' },
  { name: '学习报告', path: '/report', match: (path) => path.startsWith('/report') },
]

const canManage = computed(() => ['admin', 'teacher'].includes(userStore.user?.role))

const navs = computed(() => {
  if (!canManage.value) return baseNavs
  return [
    ...baseNavs,
    { name: '后台管理', path: '/admin', match: (path) => path.startsWith('/admin'), badge: 'ADMIN' },
  ]
})

const activePath = computed(() => navs.value.find((item) => item.match(route.path))?.path || '')

const go = (path) => {
  router.push(path)
}

const handleCommand = (command) => {
  if (command === 'logout') {
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/')
    return
  }
  if (command === 'admin') {
    router.push('/admin')
    return
  }
  if (command === 'profile') {
    router.push('/profile')
    return
  }
  router.push(command === 'ai' ? '/ai' : '/report')
}

const noticeTypeLabel = { system: '系统', course_update: '课程动态', study_reminder: '学习提醒' }

const unread = ref(0)
const notices = ref([])
const noticeLoading = ref(false)
const noticeVisible = ref(false)
let noticeTimer = null
let noticeStream = null
let noticeRetryTimer = null

const formatNoticeTime = (value) => {
  if (!value) return ''
  // 后端统一存储 naive UTC（isoformat 不带时区），这里补 Z 再解析，避免被当成本地时间而差 8 小时
  const normalized = /Z$|[+-]\d{2}:\d{2}$/.test(value) ? value : `${value}Z`
  const time = new Date(normalized)
  const diff = Date.now() - time.getTime()
  if (diff < 60 * 1000) return '刚刚'
  if (diff < 60 * 60 * 1000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 24 * 60 * 60 * 1000) return `${Math.floor(diff / 3600000)} 小时前`
  return `${time.getMonth() + 1}-${String(time.getDate()).padStart(2, '0')}`
}

const loadUnread = async () => {
  if (!userStore.isLoggedIn) {
    unread.value = 0
    return
  }
  try {
    const data = await notificationApi.unreadCount()
    unread.value = data.unread || 0
  } catch (error) {
    // 通知属于辅助信息，失败不打扰用户
  }
}

const stopNoticeStream = () => {
  if (noticeStream) {
    noticeStream.close()
    noticeStream = null
  }
  if (noticeRetryTimer) {
    clearTimeout(noticeRetryTimer)
    noticeRetryTimer = null
  }
}

const startNoticeStream = () => {
  stopNoticeStream()
  if (!userStore.isLoggedIn || typeof EventSource === 'undefined') return
  const token = localStorage.getItem('zx_token')
  if (!token) return
  noticeStream = new EventSource(`/api/notifications/stream?token=${encodeURIComponent(token)}`)
  noticeStream.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (typeof data.unread === 'number') unread.value = data.unread
    } catch (error) {
      // 单条事件解析失败忽略，轮询兜底
    }
  }
  noticeStream.onerror = () => {
    if (noticeStream) {
      noticeStream.close()
      noticeStream = null
    }
    noticeRetryTimer = setTimeout(startNoticeStream, 60000)
  }
}

const loadNotices = async () => {
  if (!userStore.isLoggedIn) return
  noticeLoading.value = true
  try {
    const data = await notificationApi.list({ page: 1, page_size: 8 })
    notices.value = data.items
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    noticeLoading.value = false
  }
  loadUnread()
}

const openNotice = async (item) => {
  if (!item.is_read) {
    try {
      const data = await notificationApi.read(item.id)
      item.is_read = true
      unread.value = data.unread
    } catch (error) {
      // 单条标记失败不影响跳转
    }
  }
  if (item.link) {
    noticeVisible.value = false
    router.push(item.link)
  }
}

const readAllNotices = async () => {
  try {
    await notificationApi.readAll()
    notices.value = notices.value.map((item) => ({ ...item, is_read: true }))
    unread.value = 0
    ElMessage.success('已全部标记为已读')
  } catch (error) {
    ElMessage.error(error.message)
  }
}

watch(noticeVisible, (visible) => {
  if (visible) loadNotices()
})

watch(
  () => userStore.isLoggedIn,
  (loggedIn) => {
    if (loggedIn) {
      loadUnread()
      startNoticeStream()
    } else {
      stopNoticeStream()
      unread.value = 0
      notices.value = []
      noticeVisible.value = false
    }
  },
)

onMounted(() => {
  if (userStore.isLoggedIn) {
    userStore.fetchMe().catch(() => {})
    loadUnread()
  }
  startNoticeStream()
  noticeTimer = setInterval(loadUnread, 60000)
})

onBeforeUnmount(() => {
  if (noticeTimer) clearInterval(noticeTimer)
  stopNoticeStream()
})
</script>

<template>
  <div class="layout">
    <header class="topbar">
      <div class="zx-container topbar-inner">
        <router-link class="brand" to="/">
          <div class="logo-mark">智</div>
          <div class="brand-text">
            <span class="brand-name">智学云</span>
            <span class="brand-sub">AI EDU PLATFORM</span>
          </div>
        </router-link>

        <nav class="nav">
          <button
            v-for="item in navs"
            :key="item.path"
            :class="['nav-item', { active: activePath === item.path }]"
            type="button"
            @click="go(item.path)"
          >
            {{ item.name }}
            <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
          </button>
        </nav>

        <div class="actions">
          <template v-if="userStore.isLoggedIn">
            <el-popover
              v-model:visible="noticeVisible"
              placement="bottom-end"
              :width="360"
              trigger="click"
              :teleported="false"
            >
              <template #reference>
                <button type="button" class="notice-btn" :title="unread ? `${unread} 条未读通知` : '通知'">
                  <el-badge :value="unread" :hidden="!unread" :max="99">
                    <el-icon :size="18"><Bell /></el-icon>
                  </el-badge>
                </button>
              </template>

              <div class="notice-panel">
                <div class="notice-head">
                  <strong>通知</strong>
                  <button v-if="unread" type="button" class="notice-all" @click="readAllNotices">全部已读</button>
                </div>
                <div v-loading="noticeLoading" class="notice-list">
                  <button
                    v-for="item in notices"
                    :key="item.id"
                    type="button"
                    :class="['notice-item', { unread: !item.is_read }]"
                    @click="openNotice(item)"
                  >
                    <span class="notice-dot"></span>
                    <span class="notice-body">
                      <span class="notice-meta">
                        <span class="notice-type" :class="item.type">{{ noticeTypeLabel[item.type] || '通知' }}</span>
                        <span class="notice-time">{{ formatNoticeTime(item.created_at) }}</span>
                      </span>
                      <strong class="notice-title">{{ item.title }}</strong>
                      <span class="notice-content">{{ item.content }}</span>
                    </span>
                  </button>
                  <div v-if="!noticeLoading && !notices.length" class="notice-empty">暂无通知</div>
                </div>
              </div>
            </el-popover>

            <el-dropdown trigger="click" @command="handleCommand">
              <div class="user-chip">
                <el-avatar :size="32" :src="userStore.user?.avatar || ''">
                  {{ userStore.displayName.slice(0, 1) }}
                </el-avatar>
                <div class="user-meta">
                  <span class="user-name">{{ userStore.displayName }}</span>
                  <span class="user-role">{{ userStore.roleLabel }}</span>
                </div>
                <el-icon class="user-arrow"><ArrowDown /></el-icon>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="ai">AI 学习助手</el-dropdown-item>
                  <el-dropdown-item command="report">学习报告</el-dropdown-item>
                  <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                  <el-dropdown-item v-if="canManage" command="admin">后台管理</el-dropdown-item>
                  <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <el-button text @click="go('/login')">登录</el-button>
            <el-button type="primary" round class="zx-gradient-button" @click="go('/login')">
              免费注册
            </el-button>
          </template>
        </div>
      </div>
    </header>

    <main class="main">
      <router-view />
    </main>

    <footer class="footer">
      <div class="zx-container footer-inner">
        <div class="footer-brand">
          <div class="logo-mark small">智</div>
          <div>
            <div class="footer-name">智学云 · 面向教育平台的智能体</div>
            <div class="footer-desc">华为 ICT 学院《基于 Python 的 AI 项目实践》项目二样板工程</div>
          </div>
        </div>
        <div class="footer-links">
          <a @click="go('/')">课程中心</a>
          <a @click="go('/jobs')">实习就业</a>
          <a @click="go('/ai')">AI 助手</a>
          <a @click="go('/report')">学习报告</a>
        </div>
        <div class="footer-tech">FastAPI · Vue 3 · MySQL · LLM Gateway</div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: saturate(180%) blur(14px);
  border-bottom: 1px solid var(--zx-border);
}

.topbar-inner {
  height: 68px;
  display: flex;
  align-items: center;
  gap: 32px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.logo-mark {
  width: 38px;
  height: 38px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  color: #fff;
  font-size: 19px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--zx-accent), #7c9dff);
  box-shadow: var(--zx-shadow-accent);
}

.logo-mark.small {
  width: 34px;
  height: 34px;
  font-size: 16px;
  box-shadow: none;
}

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}

.brand-name {
  font-size: 17px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--zx-fg);
}

.brand-sub {
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.16em;
  color: var(--zx-muted-fg);
}

.nav {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
}

.nav-item {
  position: relative;
  padding: 8px 14px;
  border: none;
  background: transparent;
  font-size: 14px;
  font-weight: 500;
  color: var(--zx-muted-fg);
  cursor: pointer;
  border-radius: 8px;
  transition: color 0.2s ease, background 0.2s ease;
}

.nav-item:hover {
  color: var(--zx-fg);
  background: var(--zx-muted);
}

.nav-item.active {
  color: var(--zx-accent);
  font-weight: 600;
}

.nav-item.active::after {
  content: '';
  position: absolute;
  left: 14px;
  right: 14px;
  bottom: -10px;
  height: 2px;
  border-radius: 2px;
  background: linear-gradient(90deg, var(--zx-accent), var(--zx-accent-2));
}

.nav-badge {
  margin-left: 4px;
  padding: 1px 5px;
  font-size: 9px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(120deg, var(--zx-accent), #7c9dff);
  border-radius: 999px;
  vertical-align: 2px;
}

.actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 10px 5px 6px;
  border-radius: 999px;
  border: 1px solid var(--zx-border);
  background: #fff;
  cursor: pointer;
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
  outline: none;
}

.user-chip:hover {
  border-color: #cbd9ff;
  box-shadow: var(--zx-shadow-sm);
}

.user-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--zx-fg);
}

.user-role {
  font-size: 11px;
  color: var(--zx-muted-fg);
}

.user-arrow {
  color: var(--zx-muted-fg);
  font-size: 12px;
}

.main {
  flex: 1;
  padding-bottom: 56px;
}

.footer {
  background: var(--zx-fg);
  color: #94a3b8;
  padding: 40px 0;
  position: relative;
  overflow: hidden;
}

.footer::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, #fff 1px, transparent 1px);
  background-size: 32px 32px;
  opacity: 0.03;
  pointer-events: none;
}

.footer-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 32px;
  flex-wrap: wrap;
  position: relative;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.footer-name {
  color: #f8fafc;
  font-size: 14px;
  font-weight: 600;
}

.footer-desc {
  font-size: 12px;
  margin-top: 2px;
}

.footer-links {
  display: flex;
  gap: 22px;
  font-size: 13px;
}

.footer-links a {
  color: #cbd5e1;
  cursor: pointer;
  transition: color 0.2s ease;
}

.footer-links a:hover {
  color: #fff;
}

.footer-tech {
  font-size: 11px;
  letter-spacing: 0.08em;
  color: #64748b;
  font-family: 'JetBrains Mono', Consolas, monospace;
}

@media (max-width: 900px) {
  .topbar-inner {
    gap: 16px;
  }

  .nav {
    overflow-x: auto;
    scrollbar-width: none;
  }

  .nav::-webkit-scrollbar {
    display: none;
  }

  .nav-item.active::after {
    bottom: -6px;
  }

  .user-meta {
    display: none;
  }

  .footer-inner {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
}

.notice-btn {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  padding: 0;
  border: 1px solid var(--zx-border);
  border-radius: 50%;
  background: #fff;
  color: var(--zx-muted-fg);
  cursor: pointer;
  transition: color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.notice-btn:hover {
  color: var(--zx-accent);
  border-color: #cbd9ff;
  box-shadow: var(--zx-shadow-sm);
}

.notice-btn :deep(.el-badge__content) {
  font-size: 10px;
  height: 15px;
  line-height: 15px;
  padding: 0 4px;
}

.notice-panel {
  width: 100%;
}

.notice-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2px 2px 10px;
  border-bottom: 1px solid var(--zx-border);
}

.notice-head strong {
  font-size: 13px;
  letter-spacing: -0.01em;
}

.notice-all {
  padding: 2px 4px;
  border: none;
  background: transparent;
  color: var(--zx-accent);
  font-size: 12px;
  cursor: pointer;
}

.notice-all:hover {
  text-decoration: underline;
}

.notice-list {
  max-height: 380px;
  overflow-y: auto;
  margin-top: 6px;
  min-height: 80px;
}

.notice-item {
  width: 100%;
  display: flex;
  gap: 8px;
  align-items: flex-start;
  padding: 10px 8px;
  border: none;
  background: transparent;
  border-radius: 8px;
  text-align: left;
  cursor: pointer;
  transition: background 0.16s ease;
}

.notice-item:hover {
  background: var(--zx-muted);
}

.notice-dot {
  width: 6px;
  height: 6px;
  margin-top: 6px;
  border-radius: 50%;
  background: #cbd5e1;
  flex-shrink: 0;
}

.notice-item.unread .notice-dot {
  background: var(--zx-accent);
  box-shadow: 0 0 0 3px rgba(0, 82, 255, 0.12);
}

.notice-body {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
  flex: 1;
}

.notice-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.notice-type {
  padding: 1px 6px;
  border-radius: 999px;
  font-size: 10px;
  color: var(--zx-accent);
  background: #eef3ff;
}

.notice-type.study_reminder {
  color: #b45309;
  background: #fffbeb;
}

.notice-type.system {
  color: #475569;
  background: #f1f5f9;
}

.notice-time {
  margin-left: auto;
  font-size: 10.5px;
  color: #94a3b8;
}

.notice-title {
  font-size: 12.5px;
  font-weight: 600;
  line-height: 1.5;
  color: var(--zx-fg);
}

.notice-content {
  font-size: 11.5px;
  line-height: 1.55;
  color: var(--zx-muted-fg);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notice-empty {
  padding: 28px 0;
  text-align: center;
  font-size: 12.5px;
  color: #94a3b8;
}
</style>