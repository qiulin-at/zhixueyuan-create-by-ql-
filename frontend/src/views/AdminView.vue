<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Briefcase, DataLine, Reading, Refresh, Search, ShoppingCart, Star, User } from '@element-plus/icons-vue'
import { adminApi } from '../api'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const PAGE_SIZE = 10

const role = computed(() => userStore.user?.role || '')
const isAdmin = computed(() => role.value === 'admin')
const isTeacher = computed(() => role.value === 'teacher')
const ready = ref(false)

const roleLabel = { student: '学生', teacher: '教师', admin: '管理员' }
const levelLabel = {
  beginner: '初级',
  intermediate: '中级',
  advanced: '高级',
  co_build: '专业共建',
}
const typeLabel = { theory: '理论', practice: '实训', certification: '认证' }
const statusLabel = { published: '已上架', offline: '已下架', draft: '草稿' }
const orderStatusLabel = { pending: '待支付', paid: '已支付', refunded: '已退款' }
const orderStatusTag = { pending: 'warning', paid: 'success', refunded: 'info' }
const applyStatusLabel = { applied: '已投递', interview: '面试中', offer: '已录用', rejected: '未通过' }
const applyStatusTag = { applied: 'info', interview: 'warning', offer: 'success', rejected: 'danger' }

const stats = ref(null)
const loading = reactive({ stats: false, courses: false, users: false, orders: false, applications: false })
const loaded = reactive({ users: false, orders: false, applications: false })

const tab = ref('courses')

const courses = reactive({ items: [], total: 0, page: 1, keyword: '', status: '' })
const users = reactive({ items: [], total: 0, page: 1, keyword: '' })
const orders = reactive({ items: [], total: 0, page: 1 })
const applications = reactive({ items: [], total: 0, page: 1 })

const courseIndex = ref(new Map())
const userIndex = ref(new Map())
const indexReady = ref(false)

const formatTime = (value) => {
  if (!value) return '—'
  return `${value.slice(0, 10)} ${value.slice(11, 16)}`
}
const formatMoney = (value) => `¥ ${Number(value || 0).toFixed(2)}`
const formatCount = (value) => (value >= 10000 ? `${(value / 10000).toFixed(1)} 万` : String(value ?? 0))

const courseName = (id) => courseIndex.value.get(id) || `课程 #${id}`
const userName = (id) => userIndex.value.get(id) || `用户 #${id}`

const loadStats = async () => {
  if (!isAdmin.value) return
  loading.stats = true
  try {
    stats.value = await adminApi.stats()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.stats = false
  }
}

const loadCourses = async () => {
  loading.courses = true
  try {
    const data = await adminApi.courses({
      keyword: courses.keyword.trim(),
      status: courses.status,
      page: courses.page,
      page_size: PAGE_SIZE,
    })
    courses.items = data.items
    courses.total = data.total
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.courses = false
  }
}

const loadUsers = async () => {
  loading.users = true
  try {
    const data = await adminApi.users({
      keyword: users.keyword.trim(),
      page: users.page,
      page_size: PAGE_SIZE,
    })
    users.items = data.items
    users.total = data.total
    loaded.users = true
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.users = false
  }
}

const loadOrders = async () => {
  loading.orders = true
  try {
    const data = await adminApi.orders({ page: orders.page, page_size: PAGE_SIZE })
    orders.items = data.items
    orders.total = data.total
    loaded.orders = true
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.orders = false
  }
}

const loadApplications = async () => {
  loading.applications = true
  try {
    const data = await adminApi.applications({ page: applications.page, page_size: PAGE_SIZE })
    applications.items = data.items
    applications.total = data.total
    loaded.applications = true
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.applications = false
  }
}

// 订单/申请接口只返 ID，这里额外拉一份索引用于展示名称（失败则回退为 ID）
const loadIndexes = async () => {
  if (indexReady.value) return
  try {
    const [courseData, userData] = await Promise.all([
      adminApi.courses({ page: 1, page_size: 50 }),
      adminApi.users({ page: 1, page_size: 50 }),
    ])
    courseIndex.value = new Map(courseData.items.map((item) => [item.id, item.title]))
    userIndex.value = new Map(userData.items.map((item) => [item.id, item.nickname || item.username]))
    indexReady.value = true
  } catch (error) {
    indexReady.value = false
  }
}

const onTabChange = async (name) => {
  if (name === 'users' && !loaded.users) await loadUsers()
  if (name === 'orders') {
    await loadIndexes()
    if (!loaded.orders) await loadOrders()
  }
  if (name === 'applications' && !loaded.applications) await loadApplications()
}

const searchCourses = () => {
  courses.page = 1
  loadCourses()
}

const searchUsers = () => {
  users.page = 1
  loadUsers()
}

const changeCourseStatus = async (row, value) => {
  if (value === row.status) return
  const previous = row.status
  row.status = value
  try {
    await adminApi.updateCourseStatus(row.id, value)
    ElMessage.success(`《${row.title}》已${statusLabel[value]}`)
  } catch (error) {
    row.status = previous
    ElMessage.error(error.message)
  }
}

const changeUserRole = async (row, value) => {
  if (value === row.role) return
  const previous = row.role
  row.role = value
  try {
    await adminApi.updateRole(row.id, value)
    ElMessage.success(`${row.nickname || row.username} 已设为${roleLabel[value]}`)
  } catch (error) {
    row.role = previous
    ElMessage.error(error.message)
  }
}

const refreshAll = async () => {
  await Promise.all([loadStats(), loadCourses()])
  if (isAdmin.value) {
    if (loaded.users) await loadUsers()
    if (loaded.orders) await loadOrders()
    if (loaded.applications) await loadApplications()
  }
  ElMessage.success('数据已刷新')
}

const statCards = computed(() => {
  if (!stats.value) return []
  return [
    { key: 'users', label: '平台用户', value: stats.value.users, sub: '含学生 / 教师 / 管理员', icon: User, tone: 'blue' },
    { key: 'courses', label: '课程总数', value: stats.value.courses, sub: `已上架 ${stats.value.published_courses} 门`, icon: Reading, tone: 'green' },
    { key: 'orders', label: '订单数', value: stats.value.orders, sub: '全平台课程订单', icon: ShoppingCart, tone: 'purple' },
    { key: 'applications', label: '职位申请', value: stats.value.applications, sub: `在招职位 ${stats.value.jobs} 个`, icon: Briefcase, tone: 'orange' },
    { key: 'favorites', label: '收藏记录', value: stats.value.favorites, sub: '学生收藏课程次数', icon: Star, tone: 'amber' },
    { key: 'learning', label: '学习记录', value: stats.value.learning_records, sub: `课程评论 ${stats.value.comments} 条`, icon: DataLine, tone: 'cyan' },
  ]
})

const courseTabLabel = computed(() => (isTeacher.value ? '我的课程' : '课程管理'))

onMounted(async () => {
  if (!userStore.isLoggedIn) {
    router.replace({ name: 'login', query: { redirect: '/admin' } })
    return
  }
  if (!userStore.user?.role) {
    try {
      await userStore.fetchMe()
    } catch (error) {
      router.replace({ name: 'login', query: { redirect: '/admin' } })
      return
    }
  }
  if (!['admin', 'teacher'].includes(userStore.user?.role)) {
    ElMessage.error('该页面仅管理员与教师可访问')
    router.replace('/')
    return
  }
  ready.value = true
  await Promise.all([loadStats(), loadCourses()])
  if (isAdmin.value) {
    await Promise.all([loadUsers(), loadOrders(), loadApplications()])
  }
})
</script>

<template>
  <div v-if="ready" class="admin-page">
    <div class="zx-container">
      <section class="admin-hero">
        <div>
          <span class="eyebrow">ADMIN CONSOLE</span>
          <h1>后台管理</h1>
          <p v-if="isAdmin">平台运营数据，以及用户、课程、订单与职位申请的统一管理入口。</p>
          <p v-else>教师工作台：仅可查看并上下架本人创建的课程。</p>
        </div>
        <div class="hero-side">
          <div class="role-pill" :class="role">
            <span class="dot"></span>
            {{ roleLabel[role] }}视角
          </div>
          <el-button :icon="Refresh" :loading="loading.courses || loading.stats" @click="refreshAll">
            刷新数据
          </el-button>
        </div>
      </section>

      <section v-if="isAdmin" v-loading="loading.stats" class="stat-grid">
        <article v-for="card in statCards" :key="card.key" class="stat-card zx-card">
          <div class="stat-icon" :class="card.tone">
            <el-icon><component :is="card.icon" /></el-icon>
          </div>
          <div class="stat-body">
            <span class="stat-label">{{ card.label }}</span>
            <strong class="stat-value">{{ formatCount(card.value) }}</strong>
            <span class="stat-sub">{{ card.sub }}</span>
          </div>
        </article>
      </section>

      <section v-else class="teacher-summary zx-card">
        <div class="ts-main">
          <span class="stat-label">我的课程</span>
          <strong>{{ courses.total }} <em>门</em></strong>
        </div>
        <p>当前账号为教师角色，课程列表已由后端按 <code>teacher_id</code> 过滤，只能对本人课程执行上下架。</p>
      </section>

      <section class="panel zx-card">
        <el-tabs v-model="tab" class="admin-tabs" @tab-change="onTabChange">
          <el-tab-pane :label="courseTabLabel" name="courses">
            <div class="toolbar">
              <el-input
                v-model="courses.keyword"
                class="toolbar-search"
                placeholder="搜索课程名称，如：Hadoop"
                clearable
                :prefix-icon="Search"
                @keyup.enter="searchCourses"
                @clear="searchCourses"
              />
              <el-select v-model="courses.status" class="toolbar-select" placeholder="全部状态" clearable @change="searchCourses">
                <el-option label="已上架" value="published" />
                <el-option label="已下架" value="offline" />
                <el-option label="草稿" value="draft" />
              </el-select>
              <el-button type="primary" class="zx-gradient-button" @click="searchCourses">查询</el-button>
              <span class="toolbar-tip">共 {{ courses.total }} 门</span>
            </div>

            <div class="table-wrap">
              <el-table v-loading="loading.courses" :data="courses.items" row-key="id" size="default">
                <el-table-column prop="id" label="ID" width="64" />
                <el-table-column prop="title" label="课程名称" min-width="200" show-overflow-tooltip />
                <el-table-column label="类型" width="82">
                  <template #default="{ row }">{{ typeLabel[row.course_type] || row.course_type }}</template>
                </el-table-column>
                <el-table-column prop="tech_system" label="技术体系" width="98" />
                <el-table-column label="等级" width="92">
                  <template #default="{ row }">{{ levelLabel[row.level] || row.level }}</template>
                </el-table-column>
                <el-table-column label="收费" width="82">
                  <template #default="{ row }">
                    <span class="zx-tag" :class="row.is_free ? 'free' : 'paid'">{{ row.is_free ? '免费' : '付费' }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="学习人数" width="94" align="right">
                  <template #default="{ row }">{{ formatCount(row.study_count) }}</template>
                </el-table-column>
                <el-table-column label="评分" width="72" align="right">
                  <template #default="{ row }">{{ Number(row.rating).toFixed(1) }}</template>
                </el-table-column>
                <el-table-column label="状态" width="132">
                  <template #default="{ row }">
                    <el-select
                      :model-value="row.status"
                      size="small"
                      class="status-select"
                      @change="(value) => changeCourseStatus(row, value)"
                    >
                      <el-option label="已上架" value="published" />
                      <el-option label="已下架" value="offline" />
                      <el-option label="草稿" value="draft" />
                    </el-select>
                  </template>
                </el-table-column>
                <el-table-column label="创建时间" width="132">
                  <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
                </el-table-column>
                <template #empty>
                  <div class="table-empty">没有符合条件的课程</div>
                </template>
              </el-table>
            </div>

            <div v-if="courses.total > PAGE_SIZE" class="pager">
              <el-pagination
                v-model:current-page="courses.page"
                background
                layout="total, prev, pager, next"
                :page-size="PAGE_SIZE"
                :total="courses.total"
                @current-change="loadCourses"
              />
            </div>
          </el-tab-pane>

          <el-tab-pane v-if="isAdmin" label="用户管理" name="users">
            <div class="toolbar">
              <el-input
                v-model="users.keyword"
                class="toolbar-search"
                placeholder="搜索用户名 / 昵称 / 邮箱"
                clearable
                :prefix-icon="Search"
                @keyup.enter="searchUsers"
                @clear="searchUsers"
              />
              <el-button type="primary" class="zx-gradient-button" @click="searchUsers">查询</el-button>
              <span class="toolbar-tip">共 {{ users.total }} 人</span>
            </div>

            <div class="table-wrap">
              <el-table v-loading="loading.users" :data="users.items" row-key="id">
                <el-table-column prop="id" label="ID" width="64" />
                <el-table-column prop="username" label="用户名" min-width="130" />
                <el-table-column prop="nickname" label="昵称" min-width="120" />
                <el-table-column prop="email" label="邮箱" min-width="200" show-overflow-tooltip />
                <el-table-column prop="major" label="专业" min-width="120" show-overflow-tooltip />
                <el-table-column label="角色" width="132">
                  <template #default="{ row }">
                    <el-select
                      :model-value="row.role"
                      size="small"
                      class="status-select"
                      :disabled="row.id === userStore.user?.id"
                      :title="row.id === userStore.user?.id ? '不能修改自己的角色' : '调整角色'"
                      @change="(value) => changeUserRole(row, value)"
                    >
                      <el-option label="学生" value="student" />
                      <el-option label="教师" value="teacher" />
                      <el-option label="管理员" value="admin" />
                    </el-select>
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="86">
                  <template #default="{ row }">
                    <el-tag :type="row.is_active ? 'success' : 'info'" size="small" effect="light">
                      {{ row.is_active ? '正常' : '停用' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="注册时间" width="132">
                  <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
                </el-table-column>
                <template #empty>
                  <div class="table-empty">没有匹配的用户</div>
                </template>
              </el-table>
            </div>

            <div v-if="users.total > PAGE_SIZE" class="pager">
              <el-pagination
                v-model:current-page="users.page"
                background
                layout="total, prev, pager, next"
                :page-size="PAGE_SIZE"
                :total="users.total"
                @current-change="loadUsers"
              />
            </div>
          </el-tab-pane>

          <el-tab-pane v-if="isAdmin" label="订单管理" name="orders">
            <div class="table-wrap">
              <el-table v-loading="loading.orders" :data="orders.items" row-key="id">
                <el-table-column prop="id" label="ID" width="64" />
                <el-table-column prop="order_no" label="订单号" min-width="170" />
                <el-table-column label="用户" min-width="120">
                  <template #default="{ row }">{{ userName(row.user_id) }}</template>
                </el-table-column>
                <el-table-column label="课程" min-width="220" show-overflow-tooltip>
                  <template #default="{ row }">{{ courseName(row.course_id) }}</template>
                </el-table-column>
                <el-table-column label="金额" width="110" align="right">
                  <template #default="{ row }">{{ formatMoney(row.amount) }}</template>
                </el-table-column>
                <el-table-column label="状态" width="96">
                  <template #default="{ row }">
                    <el-tag :type="orderStatusTag[row.status] || 'info'" size="small" effect="light">
                      {{ orderStatusLabel[row.status] || row.status }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="创建时间" width="132">
                  <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
                </el-table-column>
                <template #empty>
                  <div class="table-empty">暂无订单数据</div>
                </template>
              </el-table>
            </div>

            <div v-if="orders.total > PAGE_SIZE" class="pager">
              <el-pagination
                v-model:current-page="orders.page"
                background
                layout="total, prev, pager, next"
                :page-size="PAGE_SIZE"
                :total="orders.total"
                @current-change="loadOrders"
              />
            </div>
          </el-tab-pane>

          <el-tab-pane v-if="isAdmin" label="职位申请" name="applications">
            <div class="table-wrap">
              <el-table v-loading="loading.applications" :data="applications.items" row-key="id">
                <el-table-column prop="id" label="ID" width="64" />
                <el-table-column prop="user_name" label="申请人" min-width="120" />
                <el-table-column prop="job_title" label="职位" min-width="220" show-overflow-tooltip />
                <el-table-column prop="company" label="公司" min-width="220" show-overflow-tooltip />
                <el-table-column label="状态" width="96">
                  <template #default="{ row }">
                    <el-tag :type="applyStatusTag[row.status] || 'info'" size="small" effect="light">
                      {{ applyStatusLabel[row.status] || row.status }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="申请时间" width="132">
                  <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
                </el-table-column>
                <template #empty>
                  <div class="table-empty">暂无职位申请</div>
                </template>
              </el-table>
            </div>

            <div v-if="applications.total > PAGE_SIZE" class="pager">
              <el-pagination
                v-model:current-page="applications.page"
                background
                layout="total, prev, pager, next"
                :page-size="PAGE_SIZE"
                :total="applications.total"
                @current-change="loadApplications"
              />
            </div>
          </el-tab-pane>
        </el-tabs>
      </section>
    </div>
  </div>
</template>

<style scoped>
.admin-page {
  padding-top: 28px;
  padding-bottom: 16px;
}

.admin-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.eyebrow {
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 11px;
  letter-spacing: 0.2em;
  color: var(--zx-accent);
  font-weight: 600;
}

.admin-hero h1 {
  margin-top: 8px;
  font-size: 30px;
  letter-spacing: -0.02em;
}

.admin-hero p {
  margin-top: 6px;
  font-size: 13.5px;
  color: var(--zx-muted-fg);
}

.hero-side {
  display: flex;
  align-items: center;
  gap: 10px;
}

.role-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 6px 13px;
  border-radius: 999px;
  font-size: 12.5px;
  font-weight: 600;
  border: 1px solid var(--zx-border);
  background: #fff;
  color: var(--zx-muted-fg);
}

.role-pill .dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}

.role-pill.admin {
  color: #b91c1c;
  border-color: #fecaca;
  background: #fef2f2;
}

.role-pill.teacher {
  color: #b45309;
  border-color: #fde68a;
  background: #fffbeb;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  min-height: 96px;
  margin-bottom: 18px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
}

.stat-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-size: 20px;
  flex-shrink: 0;
}

.stat-icon.blue {
  color: #0052ff;
  background: #e8efff;
}

.stat-icon.green {
  color: #047857;
  background: #ecfdf5;
}

.stat-icon.purple {
  color: #6d28d9;
  background: #f3e8ff;
}

.stat-icon.orange {
  color: #c2410c;
  background: #fff7ed;
}

.stat-icon.amber {
  color: #b45309;
  background: #fffbeb;
}

.stat-icon.cyan {
  color: #0e7490;
  background: #ecfeff;
}

.stat-body {
  display: flex;
  flex-direction: column;
  line-height: 1.35;
  min-width: 0;
}

.stat-label {
  font-size: 12px;
  color: var(--zx-muted-fg);
}

.stat-value {
  font-size: 23px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--zx-fg);
}

.stat-sub {
  font-size: 11px;
  color: #94a3b8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.teacher-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 18px 22px;
  margin-bottom: 18px;
  flex-wrap: wrap;
}

.ts-main {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.ts-main strong {
  font-size: 26px;
  color: var(--zx-fg);
}

.ts-main em {
  font-style: normal;
  font-size: 13px;
  color: var(--zx-muted-fg);
  font-weight: 500;
}

.teacher-summary p {
  font-size: 12.5px;
  color: var(--zx-muted-fg);
  max-width: 520px;
}

.teacher-summary code {
  padding: 1px 5px;
  border-radius: 5px;
  background: var(--zx-muted);
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 11.5px;
}

.panel {
  padding: 8px 22px 22px;
}

.admin-tabs :deep(.el-tabs__header) {
  margin-bottom: 14px;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.toolbar-search {
  width: 280px;
}

.toolbar-select {
  width: 130px;
}

.toolbar-tip {
  font-size: 12px;
  color: var(--zx-muted-fg);
  margin-left: auto;
}

.table-wrap {
  width: 100%;
  overflow-x: auto;
}

.status-select {
  width: 100%;
}

.table-empty {
  padding: 26px 0;
  color: #94a3b8;
  font-size: 13px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

@media (max-width: 1100px) {
  .stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .admin-hero {
    align-items: flex-start;
  }

  .stat-grid {
    grid-template-columns: 1fr;
  }

  .toolbar-search {
    width: 100%;
  }

  .toolbar-tip {
    margin-left: 0;
  }

  .panel {
    padding: 4px 12px 18px;
  }
}
</style>
