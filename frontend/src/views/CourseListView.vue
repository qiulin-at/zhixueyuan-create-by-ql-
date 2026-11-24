<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, StarFilled, User } from '@element-plus/icons-vue'
import { courseApi, metaApi } from '../api'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const modules = ref([])
const activeModule = ref('theory')

const techSystems = ref([])
const techDirections = ref([])
const levels = ref([])
const sortOptions = [
  { label: '综合排序', value: 'default' },
  { label: '最新课程', value: 'latest' },
  { label: '最多学习', value: 'study' },
  { label: '最多评论', value: 'rating' },
]
const levelLabels = { beginner: '初级课程', intermediate: '中级课程', advanced: '高级课程', co_build: '专业共建课程' }
const typeLabels = { theory: '理论课程', practice: '实训课程', certification: '认证课程' }
const coverThemes = {
  人工智能: 'cover-ai',
  大数据: 'cover-bigdata',
  云计算: 'cover-cloud',
  鸿蒙: 'cover-harmony',
  通信: 'cover-comm',
  数通: 'cover-network',
  工业软件: 'cover-industry',
}

const filterState = ref({ tech_system: '', tech_direction: '', level: '', is_free: '' })
const keyword = ref('')
const sort = ref('default')
const courses = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 12
const loading = ref(false)

const loadMeta = async () => {
  try {
    const data = await metaApi.taxonomy()
    techSystems.value = data.tech_system || []
    techDirections.value = data.tech_direction || []
    levels.value = data.level || []
    if (data.course_type?.length) {
      modules.value = data.course_type.map((item) => ({ label: item.label, value: item.value }))
      if (!modules.value.some((item) => item.value === activeModule.value)) {
        activeModule.value = modules.value[0]?.value || 'theory'
      }
    }
  } catch (error) {
    techSystems.value = ['人工智能', '大数据', '云计算', '工业软件', '数通', '通信', '鸿蒙']
    levels.value = [
      { label: '初级课程', value: 'beginner' },
      { label: '中级课程', value: 'intermediate' },
      { label: '高级课程', value: 'advanced' },
      { label: '专业共建合作课程', value: 'co_build' },
    ]
    modules.value = [
      { label: '理论课程', value: 'theory' },
      { label: '实训课程', value: 'practice' },
      { label: '认证课程', value: 'certification' },
    ]
  }
}

const fetchCourses = async () => {
  loading.value = true
  try {
    const data = await courseApi.list({
      tech_system: filterState.value.tech_system,
      tech_direction: filterState.value.tech_direction,
      level: filterState.value.level,
      is_free: filterState.value.is_free,
      course_type: activeModule.value,
      keyword: keyword.value.trim(),
      sort: sort.value,
      page: page.value,
      page_size: pageSize,
    })
    courses.value = data.items
    total.value = data.total
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

const setFilter = (key, value) => {
  filterState.value[key] = value
  page.value = 1
  fetchCourses()
}

const switchModule = (value) => {
  if (activeModule.value === value) return
  activeModule.value = value
  page.value = 1
  fetchCourses()
}

const changeSort = (value) => {
  sort.value = value
  page.value = 1
  fetchCourses()
}

const search = () => {
  page.value = 1
  fetchCourses()
}

const changePage = (value) => {
  page.value = value
  fetchCourses()
  window.scrollTo({ top: 520, behavior: 'smooth' })
}

const openCourse = (course) => {
  router.push({ name: 'course-detail', params: { id: course.id } })
}

const toggleFavorite = async (course) => {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('登录后即可收藏课程')
    router.push({ name: 'login', query: { redirect: '/' } })
    return
  }
  try {
    const data = await courseApi.toggleFavorite(course.id)
    course.is_favorite = data.is_favorite
    ElMessage.success(data.is_favorite ? '已加入收藏' : '已取消收藏')
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const formatCount = (count) => (count >= 10000 ? `${(count / 10000).toFixed(1)}万` : String(count))

onMounted(() => {
  loadMeta()
  fetchCourses()
})
</script>

<template>
  <div class="course-page">
    <section class="hero">
      <div class="hero-glow"></div>
      <div class="zx-container hero-inner">
        <div class="hero-copy zx-fade-up">
          <span class="hero-eyebrow">SMART LEARNING PLATFORM</span>
          <h1>发现好课程，<span class="zx-gradient-text">成就更好的自己</span></h1>
          <p>理论、实训、认证三类课程体系，配套 AI 学习助手，从入门到项目实战一站式完成。</p>
        </div>
        <div class="hero-search zx-fade-up">
          <el-input
            v-model="keyword"
            size="large"
            placeholder="搜索课程名称或讲师名称，如：Hadoop、王老师"
            clearable
            @keyup.enter="search"
            @clear="search"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" size="large" class="zx-gradient-button" @click="search">搜索</el-button>
        </div>
        <div class="hero-points">
          <span>18 门精选课程</span>
          <span>4 项 AI 能力</span>
          <span>3 类学习模块</span>
        </div>
      </div>
    </section>

    <div class="zx-container">
      <div class="module-bar">
        <button
          v-for="item in modules"
          :key="item.value"
          type="button"
          :class="['module-tab', { active: activeModule === item.value }]"
          @click="switchModule(item.value)"
        >
          {{ item.label }}
        </button>
        <router-link class="module-tab link" to="/jobs">实习就业</router-link>
      </div>

      <div class="filter-panel zx-card">
        <div class="filter-row">
          <span class="filter-label">技术体系</span>
          <div class="filter-options">
            <button type="button" :class="['filter-chip', { active: !filterState.tech_system }]" @click="setFilter('tech_system', '')">全部</button>
            <button
              v-for="item in techSystems"
              :key="item"
              type="button"
              :class="['filter-chip', { active: filterState.tech_system === item }]"
              @click="setFilter('tech_system', item)"
            >
              {{ item }}
            </button>
          </div>
        </div>

        <div class="filter-row">
          <span class="filter-label">技术方向</span>
          <div class="filter-options">
            <button type="button" :class="['filter-chip', { active: !filterState.tech_direction }]" @click="setFilter('tech_direction', '')">全部</button>
            <button
              v-for="item in techDirections"
              :key="item"
              type="button"
              :class="['filter-chip', { active: filterState.tech_direction === item }]"
              @click="setFilter('tech_direction', item)"
            >
              {{ item }}
            </button>
          </div>
        </div>

        <div class="filter-row">
          <span class="filter-label">课程等级</span>
          <div class="filter-options">
            <button type="button" :class="['filter-chip', { active: !filterState.level }]" @click="setFilter('level', '')">全部</button>
            <button
              v-for="item in levels"
              :key="item.value"
              type="button"
              :class="['filter-chip', { active: filterState.level === item.value }]"
              @click="setFilter('level', item.value)"
            >
              {{ item.label }}
            </button>
          </div>
        </div>

        <div class="filter-row">
          <span class="filter-label">收费类型</span>
          <div class="filter-options">
            <button type="button" :class="['filter-chip', { active: !filterState.is_free }]" @click="setFilter('is_free', '')">全部</button>
            <button type="button" :class="['filter-chip', { active: filterState.is_free === '1' }]" @click="setFilter('is_free', '1')">免费</button>
            <button type="button" :class="['filter-chip', { active: filterState.is_free === '0' }]" @click="setFilter('is_free', '0')">付费</button>
          </div>
        </div>
      </div>

      <div class="list-toolbar">
        <div class="result-count">
          <strong>{{ total }}</strong> 门课程
          <span class="module-hint">{{ typeLabels[activeModule] }}</span>
        </div>
        <div class="sort-group">
          <span class="sort-label">排序</span>
          <button
            v-for="item in sortOptions"
            :key="item.value"
            type="button"
            :class="['sort-chip', { active: sort === item.value }]"
            @click="changeSort(item.value)"
          >
            {{ item.label }}
          </button>
        </div>
      </div>

      <div v-loading="loading" class="course-grid">
        <article
          v-for="(course, index) in courses"
          :key="course.id"
          class="course-card zx-fade-up"
          :style="{ animationDelay: `${index * 35}ms` }"
          @click="openCourse(course)"
        >
          <div class="cover" :class="coverThemes[course.tech_system] || 'cover-default'">
            <div class="cover-ring"></div>
            <div class="cover-system">
              <span class="system-name">{{ course.tech_system }}</span>
              <span class="direction-name">{{ course.tech_direction || '通识课程' }}</span>
            </div>
            <span v-if="course.is_free" class="cover-badge free">免费</span>
            <span v-else class="cover-badge paid">¥{{ course.price }}</span>
            <button
              type="button"
              class="fav-btn"
              :class="{ active: course.is_favorite }"
              :title="course.is_favorite ? '取消收藏' : '收藏课程'"
              @click.stop="toggleFavorite(course)"
            >
              <el-icon><StarFilled /></el-icon>
            </button>
          </div>

          <div class="card-body">
            <h3 class="card-title">{{ course.title }}</h3>
            <p class="card-intro">{{ course.intro }}</p>
            <div class="card-tags">
              <span class="zx-tag">{{ levelLabels[course.level] || course.level }}</span>
              <span class="zx-tag accent">{{ course.tech_direction || '综合' }}</span>
              <span class="zx-tag">{{ typeLabels[course.course_type] }}</span>
            </div>
            <div class="card-meta">
              <span class="teacher">
                <el-icon><User /></el-icon>
                {{ course.teacher_name }}
              </span>
              <span class="rating">
                <el-icon><StarFilled /></el-icon>
                {{ course.rating.toFixed(1) }}
              </span>
              <span class="study">{{ formatCount(course.study_count) }} 人在学</span>
            </div>
            <div class="card-foot">
              <span class="price" :class="{ free: course.is_free }">
                {{ course.is_free ? '免费学习' : `¥ ${course.price}` }}
              </span>
              <span class="go">查看详情 →</span>
            </div>
          </div>
        </article>
      </div>

      <div v-if="!loading && !courses.length" class="zx-empty">
        <el-icon class="zx-empty-icon"><Search /></el-icon>
        <span>没有找到符合条件的课程，换个筛选条件试试</span>
        <el-button text type="primary" @click="setFilter('tech_system', '')">重置筛选</el-button>
      </div>

      <div v-if="total > pageSize" class="pagination">
        <el-pagination
          background
          layout="prev, pager, next"
          :total="total"
          :page-size="pageSize"
          :current-page="page"
          @current-change="changePage"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.course-page {
  padding-top: 0;
}

.hero {
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, #ffffff 0%, #f5f8ff 100%);
  border-bottom: 1px solid var(--zx-border);
}

.hero-glow {
  position: absolute;
  width: 520px;
  height: 520px;
  border-radius: 50%;
  right: -140px;
  top: -260px;
  background: radial-gradient(circle, rgba(0, 82, 255, 0.13), transparent 65%);
  filter: blur(20px);
  pointer-events: none;
}

.hero-inner {
  position: relative;
  padding-top: 56px;
  padding-bottom: 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.hero-eyebrow {
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 11px;
  letter-spacing: 0.24em;
  color: var(--zx-accent);
  font-weight: 600;
}

.hero-copy h1 {
  margin-top: 12px;
  font-size: 42px;
  line-height: 1.2;
  letter-spacing: -0.03em;
}

.hero-copy p {
  margin-top: 14px;
  font-size: 15px;
  color: var(--zx-muted-fg);
  max-width: 620px;
  margin-left: auto;
  margin-right: auto;
}

.hero-search {
  margin-top: 28px;
  width: 100%;
  max-width: 680px;
  display: flex;
  gap: 10px;
  background: #fff;
  padding: 8px;
  border-radius: 16px;
  border: 1px solid var(--zx-border);
  box-shadow: var(--zx-shadow-md);
}

.hero-search .el-input {
  flex: 1;
}

.hero-search :deep(.el-input__wrapper) {
  box-shadow: none;
  background: transparent;
}

.hero-points {
  margin-top: 18px;
  display: flex;
  gap: 22px;
  font-size: 12px;
  color: var(--zx-muted-fg);
}

.hero-points span {
  position: relative;
}

.hero-points span + span::before {
  content: '';
  position: absolute;
  left: -11px;
  top: 50%;
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: #cbd5e1;
}

.module-bar {
  display: flex;
  gap: 6px;
  margin: 26px 0 16px;
  border-bottom: 1px solid var(--zx-border);
}

.module-tab {
  position: relative;
  padding: 10px 18px;
  border: none;
  background: transparent;
  font-size: 15px;
  font-weight: 500;
  color: var(--zx-muted-fg);
  cursor: pointer;
  border-radius: 8px 8px 0 0;
  transition: color 0.2s ease, background 0.2s ease;
}

.module-tab:hover {
  color: var(--zx-fg);
  background: var(--zx-muted);
}

.module-tab.active {
  color: var(--zx-accent);
  font-weight: 700;
}

.module-tab.active::after {
  content: '';
  position: absolute;
  left: 16px;
  right: 16px;
  bottom: -1px;
  height: 2px;
  background: linear-gradient(90deg, var(--zx-accent), var(--zx-accent-2));
  border-radius: 2px;
}

.module-tab.link {
  margin-left: auto;
  text-decoration: none;
}

.filter-panel {
  padding: 6px 22px;
}

.filter-row {
  display: flex;
  align-items: flex-start;
  gap: 18px;
  padding: 13px 0;
  border-bottom: 1px dashed var(--zx-border);
}

.filter-row:last-child {
  border-bottom: none;
}

.filter-label {
  flex-shrink: 0;
  width: 68px;
  padding-top: 4px;
  font-size: 13px;
  font-weight: 600;
  color: var(--zx-fg);
}

.filter-options {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.filter-chip {
  padding: 4px 12px;
  border: none;
  border-radius: 6px;
  background: transparent;
  font-size: 13px;
  color: var(--zx-muted-fg);
  cursor: pointer;
  transition: all 0.18s ease;
}

.filter-chip:hover {
  color: var(--zx-accent);
  background: #eef3ff;
}

.filter-chip.active {
  color: var(--zx-accent);
  background: #e8efff;
  font-weight: 600;
}

.list-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: 24px 0 14px;
  flex-wrap: wrap;
}

.result-count {
  font-size: 14px;
  color: var(--zx-muted-fg);
}

.result-count strong {
  font-size: 18px;
  color: var(--zx-fg);
  margin-right: 2px;
}

.module-hint {
  margin-left: 8px;
  padding: 1px 8px;
  font-size: 11px;
  color: var(--zx-accent);
  background: #e8efff;
  border-radius: 999px;
}

.sort-group {
  display: flex;
  align-items: center;
  gap: 4px;
}

.sort-label {
  font-size: 12px;
  color: var(--zx-muted-fg);
  margin-right: 4px;
}

.sort-chip {
  border: none;
  background: transparent;
  padding: 4px 10px;
  font-size: 12.5px;
  color: var(--zx-muted-fg);
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.18s ease;
}

.sort-chip:hover {
  color: var(--zx-fg);
}

.sort-chip.active {
  color: #fff;
  background: var(--zx-fg);
  font-weight: 500;
}

.course-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
  min-height: 200px;
}

.course-card {
  background: #fff;
  border: 1px solid var(--zx-border);
  border-radius: var(--zx-radius);
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
  display: flex;
  flex-direction: column;
}

.course-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--zx-shadow-lg);
  border-color: #cbd9ff;
}

.cover {
  position: relative;
  height: 132px;
  padding: 16px;
  color: #fff;
  overflow: hidden;
}

.cover-ai {
  background: linear-gradient(135deg, #0052ff, #4d7cff);
}

.cover-bigdata {
  background: linear-gradient(135deg, #0e7490, #22d3ee);
}

.cover-cloud {
  background: linear-gradient(135deg, #4338ca, #818cf8);
}

.cover-harmony {
  background: linear-gradient(135deg, #ea580c, #fbbf24);
}

.cover-comm {
  background: linear-gradient(135deg, #047857, #34d399);
}

.cover-network {
  background: linear-gradient(135deg, #7c3aed, #c4b5fd);
}

.cover-industry {
  background: linear-gradient(135deg, #334155, #94a3b8);
}

.cover-default {
  background: linear-gradient(135deg, #0f172a, #475569);
}

.cover-ring {
  position: absolute;
  width: 130px;
  height: 130px;
  border: 1.5px solid rgba(255, 255, 255, 0.22);
  border-radius: 50%;
  right: -36px;
  bottom: -56px;
}

.cover-ring::after {
  content: '';
  position: absolute;
  width: 74px;
  height: 74px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 50%;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
}

.cover-system {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.system-name {
  font-size: 19px;
  font-weight: 800;
  letter-spacing: -0.01em;
}

.direction-name {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.78);
  letter-spacing: 0.04em;
}

.cover-badge {
  position: absolute;
  left: 16px;
  bottom: 14px;
  padding: 2px 9px;
  font-size: 11px;
  font-weight: 600;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(6px);
  border: 1px solid rgba(255, 255, 255, 0.35);
}

.cover-badge.paid {
  background: rgba(15, 23, 42, 0.32);
}

.fav-btn {
  position: absolute;
  right: 12px;
  top: 12px;
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.16);
  color: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
}

.fav-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.06);
}

.fav-btn.active {
  color: #fbbf24;
  background: rgba(15, 23, 42, 0.35);
  border-color: rgba(251, 191, 36, 0.55);
}

.card-body {
  padding: 15px 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 9px;
  flex: 1;
}

.card-title {
  font-size: 15px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 42px;
}

.card-intro {
  font-size: 12px;
  color: var(--zx-muted-fg);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 38px;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 11.5px;
  color: var(--zx-muted-fg);
  padding-top: 4px;
  border-top: 1px dashed var(--zx-border);
}

.card-meta .el-icon {
  font-size: 12px;
  vertical-align: -2px;
}

.card-meta .rating {
  color: #b45309;
}

.card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
}

.price {
  font-size: 14px;
  font-weight: 700;
  color: #b45309;
}

.price.free {
  color: #047857;
}

.go {
  font-size: 12px;
  color: var(--zx-accent);
  font-weight: 500;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}

@media (max-width: 1100px) {
  .course-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 860px) {
  .hero-copy h1 {
    font-size: 32px;
  }

  .course-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .filter-row {
    flex-direction: column;
    gap: 6px;
  }

  .filter-label {
    width: auto;
  }
}

@media (max-width: 560px) {
  .course-grid {
    grid-template-columns: 1fr;
  }

  .hero-search {
    flex-direction: column;
  }

  .hero-points {
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>