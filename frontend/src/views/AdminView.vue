<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
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

const toggleUserStatus = async (row) => {
  const next = !row.is_active
  try {
    await adminApi.updateUserStatus(row.id, next)
    row.is_active = next
    ElMessage.success(`${row.nickname || row.username} 已${next ? '启用' : '停用'}`)
  } catch (error) {
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

const teachers = ref([])
const courseDialog = reactive({ visible: false, mode: 'create', id: null, saving: false })
const courseForm = reactive({
  title: '',
  cover: '',
  course_type: 'theory',
  tech_system: '',
  tech_direction: '',
  level: 'beginner',
  is_free: true,
  price: 0,
  teacher_id: null,
  intro: '',
  status: 'published',
})
const chapterDialog = reactive({
  visible: false,
  courseId: null,
  courseTitle: '',
  items: [],
  loading: false,
  saving: false,
})
const chapterForm = reactive({ title: '', content_type: 'video', duration_min: 30, sort: 1 })

const blankCourse = () => ({
  title: '',
  cover: '',
  course_type: 'theory',
  tech_system: '',
  tech_direction: '',
  level: 'beginner',
  is_free: true,
  price: 0,
  teacher_id: null,
  intro: '',
  status: 'published',
})

const loadTeachers = async () => {
  if (!isAdmin.value) return
  try {
    teachers.value = (await adminApi.teachers()).items
  } catch (error) {
    // 讲师列表失败不阻塞课程编辑
  }
}

const openCreateCourse = () => {
  Object.assign(courseForm, blankCourse())
  courseDialog.mode = 'create'
  courseDialog.id = null
  courseDialog.visible = true
  loadTeachers()
}

const openEditCourse = async (row) => {
  courseDialog.mode = 'edit'
  courseDialog.id = row.id
  courseDialog.visible = true
  loadTeachers()
  try {
    const data = await adminApi.courseDetail(row.id)
    Object.assign(courseForm, {
      title: data.title,
      cover: data.cover,
      course_type: data.course_type,
      tech_system: data.tech_system,
      tech_direction: data.tech_direction,
      level: data.level,
      is_free: data.is_free,
      price: data.price,
      teacher_id: data.teacher_id,
      intro: data.intro,
      status: data.status,
    })
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const submitCourse = async () => {
  if (courseForm.title.trim().length < 2) {
    ElMessage.warning('课程名称至少 2 个字')
    return
  }
  courseDialog.saving = true
  try {
    const payload = {
      ...courseForm,
      title: courseForm.title.trim(),
      price: Number(courseForm.price) || 0,
    }
    if (isAdmin.value) {
      payload.teacher_id = courseForm.teacher_id || null
    } else {
      delete payload.teacher_id
    }
    if (courseDialog.mode === 'create') {
      await adminApi.createCourse(payload)
      ElMessage.success('课程已创建')
    } else {
      await adminApi.updateCourse(courseDialog.id, payload)
      ElMessage.success('课程已更新')
    }
    courseDialog.visible = false
    await loadCourses()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    courseDialog.saving = false
  }
}

const removeCourse = async (row) => {
  try {
    await ElMessageBox.confirm(
      `删除《${row.title}》？已有学习记录或订单的课程会被拒绝。`,
      '删除课程',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch (error) {
    return
  }
  try {
    await adminApi.deleteCourse(row.id)
    ElMessage.success('课程已删除')
    await loadCourses()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const openChapters = async (row) => {
  chapterDialog.visible = true
  chapterDialog.courseId = row.id
  chapterDialog.courseTitle = row.title
  chapterDialog.loading = true
  chapterForm.title = ''
  try {
    const data = await adminApi.courseDetail(row.id)
    chapterDialog.items = data.chapters
    chapterForm.sort = data.chapters.length + 1
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    chapterDialog.loading = false
  }
}

const addChapter = async () => {
  if (!chapterForm.title.trim()) {
    ElMessage.warning('请填写章节标题')
    return
  }
  chapterDialog.saving = true
  try {
    const chapter = await adminApi.createChapter(chapterDialog.courseId, {
      ...chapterForm,
      title: chapterForm.title.trim(),
      duration_min: Number(chapterForm.duration_min) || 0,
      sort: Number(chapterForm.sort) || 0,
    })
    chapterDialog.items.push(chapter)
    chapterForm.title = ''
    chapterForm.sort = chapterDialog.items.length + 1
    ElMessage.success('章节已添加')
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    chapterDialog.saving = false
  }
}

const removeChapter = async (chapter) => {
  try {
    await adminApi.deleteChapter(chapter.id)
    chapterDialog.items = chapterDialog.items.filter((item) => item.id !== chapter.id)
    ElMessage.success('章节已删除')
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const changeOrderStatus = async (row, status) => {
  try {
    await adminApi.updateOrderStatus(row.id, status)
    row.status = status
    ElMessage.success('订单状态已更新')
  } catch (error) {
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
              <el-button type="primary" plain @click="openCreateCourse">新建课程</el-button>
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
                <el-table-column label="操作" width="164" fixed="right">
                  <template #default="{ row }">
                    <el-button link size="small" @click="openEditCourse(row)">编辑</el-button>
                    <el-button link size="small" @click="openChapters(row)">章节</el-button>
                    <el-button link size="small" type="danger" @click="removeCourse(row)">删除</el-button>
                  </template>
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
                <el-table-column label="操作" width="92" fixed="right">
                  <template #default="{ row }">
                    <el-button
                      link
                      size="small"
                      :type="row.is_active ? 'danger' : 'success'"
                      :disabled="row.id === userStore.user?.id"
                      @click="toggleUserStatus(row)"
                    >
                      {{ row.is_active ? '停用' : '启用' }}
                    </el-button>
                  </template>
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
                <el-table-column label="操作" width="132" fixed="right">
                  <template #default="{ row }">
                    <el-button
                      v-if="row.status === 'pending'"
                      link
                      size="small"
                      type="success"
                      @click="changeOrderStatus(row, 'paid')"
                    >
                      标记已支付
                    </el-button>
                    <el-button
                      v-if="row.status === 'paid'"
                      link
                      size="small"
                      type="warning"
                      @click="changeOrderStatus(row, 'refunded')"
                    >
                      退款
                    </el-button>
                    <span v-if="!['pending', 'paid'].includes(row.status)">—</span>
                  </template>
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

      <el-dialog
        v-model="courseDialog.visible"
        :title="courseDialog.mode === 'create' ? '新建课程' : '编辑课程'"
        width="640px"
        destroy-on-close
      >
        <el-form label-width="88px" class="course-form">
          <el-form-item label="课程名称">
            <el-input v-model="courseForm.title" maxlength="120" placeholder="例如：Python 数据分析实战" />
          </el-form-item>
          <el-form-item label="封面地址">
            <el-input v-model="courseForm.cover" maxlength="255" placeholder="https://…（可留空）" />
          </el-form-item>
          <div class="form-grid">
            <el-form-item label="类型">
              <el-select v-model="courseForm.course_type">
                <el-option label="理论" value="theory" />
                <el-option label="实训" value="practice" />
              </el-select>
            </el-form-item>
            <el-form-item label="等级">
              <el-select v-model="courseForm.level">
                <el-option label="初级" value="beginner" />
                <el-option label="中级" value="intermediate" />
                <el-option label="高级" value="advanced" />
              </el-select>
            </el-form-item>
            <el-form-item label="技术体系">
              <el-input v-model="courseForm.tech_system" maxlength="30" placeholder="如：AI" />
            </el-form-item>
            <el-form-item label="技术方向">
              <el-input v-model="courseForm.tech_direction" maxlength="30" placeholder="如：机器学习" />
            </el-form-item>
          </div>
          <el-form-item label="免费">
            <el-switch v-model="courseForm.is_free" />
            <span class="form-hint">免费课程无需填写价格</span>
          </el-form-item>
          <el-form-item v-if="!courseForm.is_free" label="价格">
            <el-input-number
              v-model="courseForm.price"
              :min="0"
              :max="99999"
              :precision="2"
              controls-position="right"
            />
          </el-form-item>
          <el-form-item v-if="isAdmin" label="讲师">
            <el-select v-model="courseForm.teacher_id" clearable placeholder="未指派">
              <el-option
                v-for="teacher in teachers"
                :key="teacher.id"
                :label="`${teacher.nickname || teacher.username}（${teacher.course_count} 门）`"
                :value="teacher.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="courseForm.status">
              <el-option label="已上架" value="published" />
              <el-option label="已下架" value="offline" />
              <el-option label="草稿" value="draft" />
            </el-select>
          </el-form-item>
          <el-form-item label="简介">
            <el-input v-model="courseForm.intro" type="textarea" :rows="3" maxlength="500" show-word-limit />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="courseDialog.visible = false">取消</el-button>
          <el-button type="primary" :loading="courseDialog.saving" @click="submitCourse">保存</el-button>
        </template>
      </el-dialog>

      <el-dialog
        v-model="chapterDialog.visible"
        :title="`章节维护 · ${chapterDialog.courseTitle}`"
        width="680px"
      >
        <div v-loading="chapterDialog.loading">
          <el-table :data="chapterDialog.items" size="small" max-height="300">
            <el-table-column prop="sort" label="#" width="52" />
            <el-table-column prop="title" label="章节标题" min-width="200" />
            <el-table-column label="时长（分）" width="100">
              <template #default="{ row }">{{ row.duration_min }}</template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button link size="small" type="danger" @click="removeChapter(row)">删除</el-button>
              </template>
            </el-table-column>
            <template #empty>
              <div class="table-empty">还没有章节</div>
            </template>
          </el-table>
          <div class="chapter-add">
            <el-input v-model="chapterForm.title" placeholder="新章节标题" maxlength="150" />
            <el-input-number
              v-model="chapterForm.duration_min"
              :min="0"
              :max="600"
              controls-position="right"
            />
            <el-input-number v-model="chapterForm.sort" :min="0" controls-position="right" />
            <el-button type="primary" :loading="chapterDialog.saving" @click="addChapter">添加</el-button>
          </div>
        </div>
      </el-dialog>
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

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 16px;
}

.form-hint {
  margin-left: 10px;
  font-size: 12px;
  color: var(--zx-muted-fg);
}

.course-form :deep(.el-select) {
  width: 100%;
}

.chapter-add {
  display: grid;
  grid-template-columns: 1fr 130px 100px auto;
  gap: 10px;
  margin-top: 14px;
}
</style>
