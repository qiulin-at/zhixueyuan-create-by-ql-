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
const loading = reactive({
  stats: false,
  courses: false,
  users: false,
  orders: false,
  applications: false,
  students: false,
  audit: false,
  resources: false,
  taxonomy: false,
})
const loaded = reactive({ users: false, orders: false, applications: false })

const tab = ref('courses')

const courses = reactive({ items: [], total: 0, page: 1, keyword: '', status: '' })
const users = reactive({ items: [], total: 0, page: 1, keyword: '' })
const orders = reactive({ items: [], total: 0, page: 1 })
const applications = reactive({ items: [], total: 0, page: 1 })
const auditLogs = reactive({ items: [], total: 0, page: 1, action: '', target_type: '' })
const studentScope = reactive({
  options: [],
  courseId: null,
  courseTitle: '',
  summary: { students: 0, avg_progress: 0, total_minutes: 0 },
  items: [],
})

const auditActionLabel = {
  'user.role': '调整角色',
  'user.status': '启停账号',
  'course.status': '课程上下架',
  'course.create': '新建课程',
  'course.update': '编辑课程',
  'course.delete': '删除课程',
  'chapter.create': '新增章节',
  'chapter.update': '编辑章节',
  'chapter.delete': '删除章节',
  'order.status': '订单状态',
}
const auditTargetLabel = { user: '用户', course: '课程', chapter: '章节', order: '订单' }

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

const loadStudentScopeOptions = async () => {
  try {
    const data = await adminApi.courses({ page: 1, page_size: 50 })
    studentScope.options = data.items
    if (!studentScope.courseId && data.items.length) {
      studentScope.courseId = data.items[0].id
    }
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const loadStudentScope = async () => {
  if (!studentScope.courseId) return
  loading.students = true
  try {
    const data = await adminApi.courseStudents(studentScope.courseId)
    studentScope.courseTitle = data.course_title
    studentScope.summary = data.summary
    studentScope.items = data.items
  } catch (error) {
    studentScope.items = []
    ElMessage.error(error.message)
  } finally {
    loading.students = false
  }
}

const loadAuditLogs = async () => {
  loading.audit = true
  try {
    const data = await adminApi.operationLogs({
      action: auditLogs.action,
      target_type: auditLogs.target_type,
      page: auditLogs.page,
      page_size: PAGE_SIZE,
    })
    auditLogs.items = data.items
    auditLogs.total = data.total
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.audit = false
  }
}

const formatDetail = (detail) => {
  if (!detail || typeof detail !== 'object') return '—'
  const parts = []
  if (detail.title) parts.push(detail.title)
  if (detail.fields?.length) parts.push(`字段：${detail.fields.join(', ')}`)
  if (detail.before !== undefined || detail.after !== undefined) {
    parts.push(`${detail.before ?? '—'} → ${detail.after ?? '—'}`)
  }
  if (detail.course_id) parts.push(`课程 #${detail.course_id}`)
  return parts.join('；') || JSON.stringify(detail)
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
  if (name === 'students') {
    if (!studentScope.options.length) await loadStudentScopeOptions()
    await loadStudentScope()
  }
  if (name === 'audit' && isAdmin.value) await loadAuditLogs()
  if (name === 'taxonomy' && isAdmin.value) await loadTaxonomy()
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
  audience: '',
  prerequisite: '',
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
  audience: '',
  prerequisite: '',
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
      audience: data.audience || '',
      prerequisite: data.prerequisite || '',
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

const reviewLabel = { draft: '未提交', pending: '待审核', published: '已通过', rejected: '已驳回' }
const reviewTag = { draft: 'info', pending: 'warning', published: 'success', rejected: 'danger' }

const changeCourseReview = async (row, status) => {
  try {
    await adminApi.reviewCourse(row.id, { review_status: status })
    row.review_status = status
    ElMessage.success(status === 'published' ? '审核已通过' : '课程已驳回')
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const submitCourseReview = async (row) => {
  try {
    await adminApi.submitReview(row.id)
    row.review_status = 'pending'
    ElMessage.success('已提交审核，等待管理员处理')
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const resourceDialog = reactive({
  visible: false,
  chapterId: null,
  chapterTitle: '',
  items: [],
  loading: false,
  saving: false,
})
const resourceForm = reactive({ title: '', resource_type: 'doc', url: '', content: '', sort: 1 })
const resourceTypeLabel = { video: '视频', doc: '文档', code: '代码', link: '链接', lab: '实验' }

const openResources = async (chapter) => {
  resourceDialog.visible = true
  resourceDialog.chapterId = chapter.id
  resourceDialog.chapterTitle = chapter.title
  resourceDialog.loading = true
  try {
    const data = await adminApi.chapterMaterials(chapter.id)
    resourceDialog.items = data.items
    resourceForm.sort = data.items.length + 1
  } catch (error) {
    resourceDialog.items = []
    ElMessage.error(error.message)
  } finally {
    resourceDialog.loading = false
  }
}

const addResource = async () => {
  if (!resourceForm.title.trim()) {
    ElMessage.warning('请填写资源标题')
    return
  }
  resourceDialog.saving = true
  try {
    const item = await adminApi.createMaterial(resourceDialog.chapterId, {
      ...resourceForm,
      title: resourceForm.title.trim(),
      url: resourceForm.url.trim(),
      sort: Number(resourceForm.sort) || 0,
    })
    resourceDialog.items.push(item)
    Object.assign(resourceForm, {
      title: '',
      resource_type: 'doc',
      url: '',
      content: '',
      sort: resourceDialog.items.length + 1,
    })
    ElMessage.success('资源已添加')
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    resourceDialog.saving = false
  }
}

const removeResource = async (item) => {
  try {
    await adminApi.deleteMaterial(item.id)
    resourceDialog.items = resourceDialog.items.filter((row) => row.id !== item.id)
    ElMessage.success('资源已删除')
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const taxonomy = reactive({ items: [], saving: false })
const taxonomyForm = reactive({ kind: 'course_type', code: '', name: '', sort: 0 })
const taxonomyKindLabel = {
  course_type: '课程类型',
  tech_system: '技术体系',
  tech_direction: '技术方向',
  level: '课程等级',
}

const loadTaxonomy = async () => {
  loading.taxonomy = true
  try {
    const data = await adminApi.taxonomy()
    taxonomy.items = data.items
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.taxonomy = false
  }
}

const addTaxonomy = async () => {
  if (!taxonomyForm.code.trim() || !taxonomyForm.name.trim()) {
    ElMessage.warning('请填写编码与名称')
    return
  }
  taxonomy.saving = true
  try {
    const item = await adminApi.createTaxonomy({
      ...taxonomyForm,
      code: taxonomyForm.code.trim(),
      name: taxonomyForm.name.trim(),
    })
    taxonomy.items.push(item)
    Object.assign(taxonomyForm, { kind: taxonomyForm.kind, code: '', name: '', sort: 0 })
    ElMessage.success('分类已添加')
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    taxonomy.saving = false
  }
}

const toggleTaxonomy = async (item) => {
  const next = !item.enabled
  try {
    const updated = await adminApi.updateTaxonomy(item.id, { enabled: next })
    item.enabled = updated.enabled
    ElMessage.success(next ? '分类已启用' : '分类已停用')
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const knowledgeDialog = reactive({
  visible: false,
  courseId: null,
  courseTitle: '',
  items: [],
  chapters: [],
  loading: false,
  saving: false,
})
const knowledgeForm = reactive({ title: '', content: '', keywords: '', chapter_id: null })

const openKnowledge = async (row) => {
  knowledgeDialog.visible = true
  knowledgeDialog.courseId = row.id
  knowledgeDialog.courseTitle = row.title
  knowledgeDialog.loading = true
  try {
    const [detail, data] = await Promise.all([
      adminApi.courseDetail(row.id),
      adminApi.knowledge(row.id),
    ])
    knowledgeDialog.chapters = detail.chapters
    knowledgeDialog.items = data.items
  } catch (error) {
    knowledgeDialog.items = []
    ElMessage.error(error.message)
  } finally {
    knowledgeDialog.loading = false
  }
}

const addKnowledge = async () => {
  if (!knowledgeForm.title.trim() || knowledgeForm.content.trim().length < 10) {
    ElMessage.warning('请填写标题，正文至少 10 字')
    return
  }
  knowledgeDialog.saving = true
  try {
    const item = await adminApi.createKnowledge(knowledgeDialog.courseId, {
      ...knowledgeForm,
      title: knowledgeForm.title.trim(),
      content: knowledgeForm.content.trim(),
      keywords: knowledgeForm.keywords.trim(),
      chapter_id: knowledgeForm.chapter_id || null,
    })
    knowledgeDialog.items.push(item)
    Object.assign(knowledgeForm, { title: '', content: '', keywords: '', chapter_id: null })
    ElMessage.success('知识库资料已添加')
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    knowledgeDialog.saving = false
  }
}

const removeKnowledge = async (item) => {
  try {
    await adminApi.deleteKnowledge(item.id)
    knowledgeDialog.items = knowledgeDialog.items.filter((row) => row.id !== item.id)
    ElMessage.success('知识库资料已删除')
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const assignmentDialog = reactive({
  visible: false,
  courseId: null,
  courseTitle: '',
  items: [],
  loading: false,
  saving: false,
})
const assignmentForm = reactive({
  title: '',
  description: '',
  language: 'python',
  deadline: '',
  sample_cases: '[{"args": [1, 2], "expected": 3}]',
  hidden_cases: '[]',
})
const submissionDialog = reactive({
  visible: false,
  assignmentId: null,
  assignmentTitle: '',
  items: [],
  loading: false,
})
const reviewInputs = reactive({})
const reviewSaving = ref(null)
const submissionLabel = {
  passed: '测试通过',
  failed: '测试未通过',
  not_executed: '未执行',
  timeout: '超时',
  compile_error: '语法错误',
  runtime_error: '运行异常',
}
const submissionTag = {
  passed: 'success',
  failed: 'warning',
  not_executed: 'info',
  timeout: 'danger',
  compile_error: 'danger',
  runtime_error: 'danger',
}

const openAssignments = async (row) => {
  assignmentDialog.visible = true
  assignmentDialog.courseId = row.id
  assignmentDialog.courseTitle = row.title
  assignmentDialog.loading = true
  try {
    const data = await adminApi.assignments(row.id)
    assignmentDialog.items = data.items
  } catch (error) {
    assignmentDialog.items = []
    ElMessage.error(error.message)
  } finally {
    assignmentDialog.loading = false
  }
}

const parseJsonField = (raw) => {
  try {
    const value = JSON.parse(raw || '[]')
    return Array.isArray(value) ? value : null
  } catch (error) {
    return null
  }
}

const createAssignment = async () => {
  if (!assignmentForm.title.trim()) {
    ElMessage.warning('请填写作业标题')
    return
  }
  const sample = parseJsonField(assignmentForm.sample_cases)
  const hidden = parseJsonField(assignmentForm.hidden_cases)
  if (sample === null || hidden === null) {
    ElMessage.warning('样例与隐藏用例必须是合法 JSON 数组')
    return
  }
  assignmentDialog.saving = true
  try {
    const item = await adminApi.createAssignment(assignmentDialog.courseId, {
      title: assignmentForm.title.trim(),
      description: assignmentForm.description,
      language: assignmentForm.language,
      deadline: assignmentForm.deadline || null,
      sample_cases: sample,
      hidden_cases: hidden,
    })
    assignmentDialog.items.push(item)
    Object.assign(assignmentForm, {
      title: '',
      description: '',
      language: 'python',
      deadline: '',
      sample_cases: '[{"args": [1, 2], "expected": 3}]',
      hidden_cases: '[]',
    })
    ElMessage.success('作业已创建')
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    assignmentDialog.saving = false
  }
}

const removeAssignment = async (item) => {
  try {
    await adminApi.deleteAssignment(item.id)
    assignmentDialog.items = assignmentDialog.items.filter((row) => row.id !== item.id)
    ElMessage.success('作业已删除')
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const openSubmissions = async (assignment) => {
  submissionDialog.visible = true
  submissionDialog.assignmentId = assignment.id
  submissionDialog.assignmentTitle = assignment.title
  submissionDialog.loading = true
  try {
    const data = await adminApi.assignmentSubmissions(assignment.id)
    submissionDialog.items = data.items
    data.items.forEach((item) => {
      reviewInputs[item.id] = {
        score: item.final_score ?? item.ai_score ?? 60,
        comment: item.review_comment || '',
      }
    })
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    submissionDialog.loading = false
  }
}

const saveReview = async (item) => {
  const input = reviewInputs[item.id]
  if (!input || input.score === null || input.score === undefined) {
    ElMessage.warning('请填写复核分数')
    return
  }
  reviewSaving.value = item.id
  try {
    const data = await adminApi.reviewSubmission(item.id, {
      final_score: Number(input.score),
      comment: input.comment || '',
    })
    Object.assign(item, data)
    ElMessage.success('复核已保存')
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    reviewSaving.value = null
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
  if (tab.value === 'students') await loadStudentScope()
  if (tab.value === 'audit' && isAdmin.value) await loadAuditLogs()
  if (tab.value === 'taxonomy' && isAdmin.value) await loadTaxonomy()
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
          <p v-else>教师工作台：查看本人课程学情，维护课程内容与上下架。</p>
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
                <el-table-column label="审核" width="96">
                  <template #default="{ row }">
                    <el-tag :type="reviewTag[row.review_status] || 'info'" size="small" effect="light">
                      {{ reviewLabel[row.review_status] || row.review_status }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="创建时间" width="132">
                  <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
                </el-table-column>
                <el-table-column label="操作" width="390" fixed="right">
                  <template #default="{ row }">
                    <el-button link size="small" @click="openEditCourse(row)">编辑</el-button>
                    <el-button link size="small" @click="openChapters(row)">章节</el-button>
                    <el-button link size="small" @click="openKnowledge(row)">知识库</el-button>
                    <el-button link size="small" @click="openAssignments(row)">作业</el-button>
                    <el-button
                      v-if="isAdmin && row.review_status === 'pending'"
                      link
                      size="small"
                      type="success"
                      @click="changeCourseReview(row, 'published')"
                    >
                      通过
                    </el-button>
                    <el-button
                      v-if="isAdmin && row.review_status === 'pending'"
                      link
                      size="small"
                      type="danger"
                      @click="changeCourseReview(row, 'rejected')"
                    >
                      驳回
                    </el-button>
                    <el-button
                      v-if="!isAdmin && ['pending', 'rejected'].includes(row.review_status)"
                      link
                      size="small"
                      type="primary"
                      @click="submitCourseReview(row)"
                    >
                      提交审核
                    </el-button>
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

          <el-tab-pane label="学情" name="students">
            <div class="toolbar">
              <el-select
                v-model="studentScope.courseId"
                class="toolbar-select-wide"
                placeholder="选择课程"
                @change="loadStudentScope"
              >
                <el-option
                  v-for="course in studentScope.options"
                  :key="course.id"
                  :label="course.title"
                  :value="course.id"
                />
              </el-select>
              <el-button :icon="Refresh" :loading="loading.students" @click="loadStudentScope">
                刷新学情
              </el-button>
              <span class="toolbar-tip">仅展示已报名或有学习记录的学生</span>
            </div>

            <div class="scope-summary">
              <div class="scope-card">
                <span>学生数</span>
                <strong>{{ studentScope.summary.students }}</strong>
              </div>
              <div class="scope-card">
                <span>平均进度</span>
                <strong>{{ studentScope.summary.avg_progress }}%</strong>
              </div>
              <div class="scope-card">
                <span>累计学习</span>
                <strong>{{ studentScope.summary.total_minutes }} <em>分钟</em></strong>
              </div>
            </div>

            <div class="table-wrap">
              <el-table v-loading="loading.students" :data="studentScope.items" row-key="user_id">
                <el-table-column prop="user_id" label="ID" width="64" />
                <el-table-column prop="user_name" label="学生" min-width="130" />
                <el-table-column prop="major" label="专业" min-width="160" show-overflow-tooltip />
                <el-table-column label="进度" width="150">
                  <template #default="{ row }">
                    <el-progress :percentage="row.progress" :stroke-width="8" />
                  </template>
                </el-table-column>
                <el-table-column label="学习时长" width="110" align="right">
                  <template #default="{ row }">{{ row.study_minutes }} 分钟</template>
                </el-table-column>
                <el-table-column label="最近章节" min-width="180" show-overflow-tooltip>
                  <template #default="{ row }">{{ row.last_chapter_title || '—' }}</template>
                </el-table-column>
                <el-table-column label="最近学习" width="140">
                  <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
                </el-table-column>
                <template #empty>
                  <div class="table-empty">该课程还没有学习记录</div>
                </template>
              </el-table>
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

          <el-tab-pane v-if="isAdmin" label="操作日志" name="audit">
            <div class="toolbar">
              <el-select
                v-model="auditLogs.action"
                class="toolbar-select-wide"
                placeholder="全部动作"
                clearable
                @change="loadAuditLogs"
              >
                <el-option
                  v-for="(label, key) in auditActionLabel"
                  :key="key"
                  :label="label"
                  :value="key"
                />
              </el-select>
              <el-select
                v-model="auditLogs.target_type"
                class="toolbar-select"
                placeholder="全部对象"
                clearable
                @change="loadAuditLogs"
              >
                <el-option
                  v-for="(label, key) in auditTargetLabel"
                  :key="key"
                  :label="label"
                  :value="key"
                />
              </el-select>
              <el-button type="primary" class="zx-gradient-button" @click="loadAuditLogs">
                查询
              </el-button>
              <span class="toolbar-tip">共 {{ auditLogs.total }} 条</span>
            </div>

            <div class="table-wrap">
              <el-table v-loading="loading.audit" :data="auditLogs.items" row-key="id">
                <el-table-column label="时间" width="150">
                  <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
                </el-table-column>
                <el-table-column prop="actor_name" label="操作者" width="120" />
                <el-table-column label="角色" width="90">
                  <template #default="{ row }">{{ roleLabel[row.actor_role] || row.actor_role }}</template>
                </el-table-column>
                <el-table-column label="动作" width="130">
                  <template #default="{ row }">{{ auditActionLabel[row.action] || row.action }}</template>
                </el-table-column>
                <el-table-column label="对象" width="110">
                  <template #default="{ row }">
                    {{ auditTargetLabel[row.target_type] || row.target_type }} #{{ row.target_id ?? '—' }}
                  </template>
                </el-table-column>
                <el-table-column label="详情" min-width="260" show-overflow-tooltip>
                  <template #default="{ row }">{{ formatDetail(row.detail) }}</template>
                </el-table-column>
                <template #empty>
                  <div class="table-empty">暂无操作日志</div>
                </template>
              </el-table>
            </div>

            <div v-if="auditLogs.total > PAGE_SIZE" class="pager">
              <el-pagination
                v-model:current-page="auditLogs.page"
                background
                layout="total, prev, pager, next"
                :page-size="PAGE_SIZE"
                :total="auditLogs.total"
                @current-change="loadAuditLogs"
              />
            </div>
          </el-tab-pane>

          <el-tab-pane v-if="isAdmin" label="分类字典" name="taxonomy">
            <div class="toolbar">
              <el-select v-model="taxonomyForm.kind" class="toolbar-select" placeholder="分类类型">
                <el-option
                  v-for="(label, key) in taxonomyKindLabel"
                  :key="key"
                  :label="label"
                  :value="key"
                />
              </el-select>
              <el-input v-model="taxonomyForm.code" class="toolbar-search" placeholder="编码，如 certification" />
              <el-input v-model="taxonomyForm.name" class="toolbar-search" placeholder="显示名称，如 认证课程" />
              <el-input-number v-model="taxonomyForm.sort" :min="0" controls-position="right" />
              <el-button type="primary" :loading="taxonomy.saving" @click="addTaxonomy">新增</el-button>
              <span class="toolbar-tip">共 {{ taxonomy.items.length }} 项</span>
            </div>
            <div class="table-wrap">
              <el-table v-loading="loading.taxonomy" :data="taxonomy.items" row-key="id" size="small">
                <el-table-column prop="id" label="ID" width="60" />
                <el-table-column label="类型" width="110">
                  <template #default="{ row }">{{ taxonomyKindLabel[row.kind] || row.kind }}</template>
                </el-table-column>
                <el-table-column prop="code" label="编码" min-width="140" />
                <el-table-column prop="name" label="名称" min-width="160" />
                <el-table-column prop="sort" label="排序" width="70" align="right" />
                <el-table-column label="状态" width="86">
                  <template #default="{ row }">
                    <el-tag :type="row.enabled ? 'success' : 'info'" size="small" effect="light">
                      {{ row.enabled ? '启用' : '停用' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="90" fixed="right">
                  <template #default="{ row }">
                    <el-button
                      link
                      size="small"
                      :type="row.enabled ? 'warning' : 'success'"
                      @click="toggleTaxonomy(row)"
                    >
                      {{ row.enabled ? '停用' : '启用' }}
                    </el-button>
                  </template>
                </el-table-column>
                <template #empty>
                  <div class="table-empty">暂无分类项</div>
                </template>
              </el-table>
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
                <el-option label="认证" value="certification" />
              </el-select>
            </el-form-item>
            <el-form-item label="等级">
              <el-select v-model="courseForm.level">
                <el-option label="初级" value="beginner" />
                <el-option label="中级" value="intermediate" />
                <el-option label="高级" value="advanced" />
                <el-option label="专业共建" value="co_build" />
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
          <el-form-item label="适用对象">
            <el-input v-model="courseForm.audience" maxlength="200" placeholder="如：具备 Python 基础的在校学生" />
          </el-form-item>
          <el-form-item label="先修要求">
            <el-input
              v-model="courseForm.prerequisite"
              type="textarea"
              :rows="2"
              placeholder="如：完成 Python 基础语法与函数学习"
            />
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
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button link size="small" @click="openResources(row)">资源</el-button>
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

      <el-dialog
        v-model="resourceDialog.visible"
        :title="`章节资源 · ${resourceDialog.chapterTitle}`"
        width="720px"
      >
        <div v-loading="resourceDialog.loading">
          <el-table :data="resourceDialog.items" size="small" max-height="280">
            <el-table-column label="类型" width="80">
              <template #default="{ row }">
                {{ resourceTypeLabel[row.resource_type] || row.resource_type }}
              </template>
            </el-table-column>
            <el-table-column prop="title" label="标题" min-width="180" />
            <el-table-column prop="url" label="链接" min-width="200" show-overflow-tooltip />
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button link size="small" type="danger" @click="removeResource(row)">删除</el-button>
              </template>
            </el-table-column>
            <template #empty>
              <div class="table-empty">本章节还没有资源</div>
            </template>
          </el-table>
          <div class="resource-add">
            <el-select v-model="resourceForm.resource_type" class="toolbar-select">
              <el-option
                v-for="(label, key) in resourceTypeLabel"
                :key="key"
                :label="label"
                :value="key"
              />
            </el-select>
            <el-input v-model="resourceForm.title" placeholder="资源标题" maxlength="150" />
            <el-input v-model="resourceForm.url" placeholder="链接（可留空）" maxlength="255" />
            <el-input-number v-model="resourceForm.sort" :min="0" controls-position="right" />
            <el-button type="primary" :loading="resourceDialog.saving" @click="addResource">
              添加
            </el-button>
          </div>
          <el-input
            v-model="resourceForm.content"
            type="textarea"
            :rows="2"
            placeholder="内嵌说明或代码片段（可选）"
          />
        </div>
      </el-dialog>

      <el-dialog
        v-model="knowledgeDialog.visible"
        :title="`课程知识库 · ${knowledgeDialog.courseTitle}`"
        width="760px"
      >
        <div v-loading="knowledgeDialog.loading">
          <el-table :data="knowledgeDialog.items" size="small" max-height="280">
            <el-table-column prop="title" label="标题" min-width="180" />
            <el-table-column label="章节" width="150">
              <template #default="{ row }">{{ row.chapter_title || '课程级' }}</template>
            </el-table-column>
            <el-table-column prop="keywords" label="关键词" min-width="150" show-overflow-tooltip />
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button link size="small" type="danger" @click="removeKnowledge(row)">删除</el-button>
              </template>
            </el-table-column>
            <template #empty>
              <div class="table-empty">暂无知识库资料</div>
            </template>
          </el-table>
          <div class="knowledge-form">
            <el-input v-model="knowledgeForm.title" placeholder="资料标题" maxlength="150" />
            <el-select
              v-model="knowledgeForm.chapter_id"
              clearable
              placeholder="课程级（可不选章节）"
            >
              <el-option
                v-for="chapter in knowledgeDialog.chapters"
                :key="chapter.id"
                :label="chapter.title"
                :value="chapter.id"
              />
            </el-select>
            <el-input
              v-model="knowledgeForm.keywords"
              placeholder="关键词，逗号分隔"
              maxlength="200"
            />
          </div>
          <el-input
            v-model="knowledgeForm.content"
            type="textarea"
            :rows="4"
            maxlength="10000"
            placeholder="资料正文（至少 10 字），将用于答疑检索"
          />
          <div class="knowledge-actions">
            <el-button type="primary" :loading="knowledgeDialog.saving" @click="addKnowledge">
              添加资料
            </el-button>
            <span>仅 kind=kb 的资料参与 AI 答疑检索</span>
          </div>
        </div>
      </el-dialog>

      <el-dialog
        v-model="assignmentDialog.visible"
        :title="`课程作业 · ${assignmentDialog.courseTitle}`"
        width="780px"
      >
        <div v-loading="assignmentDialog.loading">
          <el-table :data="assignmentDialog.items" size="small" max-height="260">
            <el-table-column prop="title" label="标题" min-width="160" />
            <el-table-column prop="language" label="语言" width="90" />
            <el-table-column label="截止" width="150">
              <template #default="{ row }">
                {{ row.deadline ? formatTime(row.deadline) : '不限时' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="130">
              <template #default="{ row }">
                <el-button link size="small" @click="openSubmissions(row)">提交</el-button>
                <el-button link size="small" type="danger" @click="removeAssignment(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
            <template #empty>
              <div class="table-empty">暂无作业</div>
            </template>
          </el-table>

          <div class="assignment-form">
            <el-input v-model="assignmentForm.title" placeholder="作业标题" maxlength="150" />
            <el-input
              v-model="assignmentForm.description"
              type="textarea"
              :rows="2"
              placeholder="题目说明，约定入口函数为 solve(...)"
              maxlength="5000"
            />
            <div class="assignment-form-row">
              <el-select v-model="assignmentForm.language" class="toolbar-select">
                <el-option label="Python" value="python" />
                <el-option label="JavaScript" value="javascript" />
                <el-option label="Java" value="java" />
                <el-option label="C++" value="cpp" />
              </el-select>
              <el-date-picker
                v-model="assignmentForm.deadline"
                type="datetime"
                placeholder="截止时间（可空）"
                value-format="YYYY-MM-DDTHH:mm:ss"
              />
            </div>
            <el-input
              v-model="assignmentForm.sample_cases"
              type="textarea"
              :rows="2"
              placeholder='公开样例 JSON：[{"args":[1,2],"expected":3}]'
            />
            <el-input
              v-model="assignmentForm.hidden_cases"
              type="textarea"
              :rows="2"
              placeholder='隐藏用例 JSON（学生不可见）'
            />
            <div class="assignment-actions">
              <el-button type="primary" :loading="assignmentDialog.saving" @click="createAssignment">
                创建作业
              </el-button>
              <span>仅 Python 会进入容器执行；其他语言仅做静态分析</span>
            </div>
          </div>
        </div>
      </el-dialog>

      <el-dialog
        v-model="submissionDialog.visible"
        :title="`提交与复核 · ${submissionDialog.assignmentTitle}`"
        width="860px"
      >
        <el-table v-loading="submissionDialog.loading" :data="submissionDialog.items" size="small" max-height="440">
          <el-table-column prop="user_name" label="学生" width="110" />
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag size="small" :type="submissionTag[row.status] || 'info'">
                {{ submissionLabel[row.status] || row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="客观" width="70" align="right">
            <template #default="{ row }">{{ row.objective_score ?? '—' }}</template>
          </el-table-column>
          <el-table-column label="AI" width="60" align="right">
            <template #default="{ row }">{{ row.ai_score ?? '—' }}</template>
          </el-table-column>
          <el-table-column label="最终" width="70" align="right">
            <template #default="{ row }">{{ row.final_score ?? '—' }}</template>
          </el-table-column>
          <el-table-column label="复核" width="250">
            <template #default="{ row }">
              <div class="review-cell">
                <el-input-number
                  v-model="reviewInputs[row.id].score"
                  :min="0"
                  :max="100"
                  size="small"
                  controls-position="right"
                />
                <el-input v-model="reviewInputs[row.id].comment" size="small" placeholder="意见" />
                <el-button
                  link
                  size="small"
                  type="primary"
                  :loading="reviewSaving === row.id"
                  @click="saveReview(row)"
                >
                  保存
                </el-button>
              </div>
            </template>
          </el-table-column>
          <template #empty>
            <div class="table-empty">暂无提交</div>
          </template>
        </el-table>
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

.toolbar-select-wide {
  width: 260px;
}

.scope-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.scope-card {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 12px 16px;
  border: 1px solid var(--zx-border);
  border-radius: 10px;
  background: #fff;
}

.scope-card span {
  font-size: 12px;
  color: var(--zx-muted-fg);
}

.scope-card strong {
  font-size: 20px;
  color: var(--zx-fg);
}

.scope-card em {
  font-style: normal;
  font-size: 12px;
  color: var(--zx-muted-fg);
  font-weight: 500;
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

  .toolbar-select-wide {
    width: 100%;
  }

  .scope-summary {
    grid-template-columns: 1fr;
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

.resource-add {
  display: grid;
  grid-template-columns: 110px 1fr 1fr 100px auto;
  gap: 8px;
  margin: 12px 0;
}

@media (max-width: 760px) {
  .resource-add {
    grid-template-columns: 1fr;
  }
}

.knowledge-form {
  display: grid;
  grid-template-columns: 1.2fr 1fr 1fr;
  gap: 8px;
  margin: 12px 0;
}

.knowledge-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
}

.knowledge-actions span {
  font-size: 11.5px;
  color: var(--zx-muted-fg);
}

.assignment-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.assignment-form-row {
  display: flex;
  gap: 8px;
}

.assignment-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.assignment-actions span {
  font-size: 11.5px;
  color: var(--zx-muted-fg);
}

.review-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.review-cell .el-input-number {
  width: 88px;
}

.review-cell .el-input {
  width: 92px;
}

@media (max-width: 760px) {
  .knowledge-form {
    grid-template-columns: 1fr;
  }
}
</style>
