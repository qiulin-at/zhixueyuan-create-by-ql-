<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Location, Search } from '@element-plus/icons-vue'
import { jobApi } from '../api'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const categories = ['全部', '技术', '产品', '设计', '运营', '市场', '人事/财务/行政', '高级管理']
const activeCategory = ref('')
const scope = ref('job')
const keyword = ref('')
const jobs = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const loading = ref(false)

const drawerVisible = ref(false)
const currentJob = ref(null)
const detailLoading = ref(false)
const applying = ref(false)

const fetchJobs = async () => {
  loading.value = true
  try {
    const data = await jobApi.list({
      category: activeCategory.value,
      keyword: keyword.value.trim(),
      scope: scope.value,
      page: page.value,
      page_size: pageSize,
    })
    jobs.value = data.items
    total.value = data.total
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

const selectCategory = (category) => {
  activeCategory.value = category === '全部' ? '' : category
  page.value = 1
  fetchJobs()
}

const search = () => {
  page.value = 1
  fetchJobs()
}

const changePage = (value) => {
  page.value = value
  fetchJobs()
  window.scrollTo({ top: 320, behavior: 'smooth' })
}

const openDetail = async (job) => {
  currentJob.value = { ...job, applied: false, requirement: '' }
  drawerVisible.value = true
  detailLoading.value = true
  try {
    currentJob.value = await jobApi.detail(job.id)
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    detailLoading.value = false
  }
}

const apply = async () => {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('登录后才能申请职位')
    drawerVisible.value = false
    router.push({ name: 'login', query: { redirect: '/jobs' } })
    return
  }
  applying.value = true
  try {
    await jobApi.apply(currentJob.value.id)
    currentJob.value.applied = true
    ElMessage.success('申请成功，请留意面试通知')
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    applying.value = false
  }
}

const comingSoon = () => {
  ElMessage.info('该功能将在后续迭代中上线，可在答辩中作为演进方向')
}

onMounted(fetchJobs)
</script>

<template>
  <div class="job-page">
    <section class="job-hero">
      <div class="zx-container">
        <div class="hero-head">
          <span class="eyebrow">CAREER CENTER</span>
          <h1>热门企业岗位</h1>
          <p>面向学生的实习与就业机会，边学边投，打通「学习—就业」最后一公里。</p>
        </div>
        <div class="search-bar">
          <el-select v-model="scope" class="scope-select" size="large">
            <el-option label="职位" value="job" />
            <el-option label="公司" value="company" />
          </el-select>
          <el-input
            v-model="keyword"
            size="large"
            class="search-input"
            placeholder="搜索职位 / 公司，如：Python、昂楷"
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
        <div class="hero-stats">
          <span>{{ total }} 个在招职位</span>
          <span>7 大职能分类</span>
          <span>支持在线申请</span>
        </div>
      </div>
    </section>

    <div class="zx-container">
      <div class="category-bar">
        <button
          v-for="item in categories"
          :key="item"
          type="button"
          :class="['category-chip', { active: (item === '全部' && !activeCategory) || activeCategory === item }]"
          @click="selectCategory(item)"
        >
          {{ item }}
        </button>
      </div>

      <div v-loading="loading" class="job-list">
        <article v-for="job in jobs" :key="job.id" class="job-card zx-card" @click="openDetail(job)">
          <div class="job-logo">{{ job.company.slice(0, 1) }}</div>
          <div class="job-main">
            <div class="job-title-row">
              <h3>{{ job.title }}</h3>
              <span class="salary">{{ job.salary }}</span>
            </div>
            <div class="job-company">
              <span>{{ job.company }}</span>
              <span class="divider"></span>
              <span class="city"><el-icon><Location /></el-icon>{{ job.city }}</span>
            </div>
            <p class="job-desc">{{ job.description }}</p>
            <div class="job-tags">
              <span class="zx-tag accent">{{ job.category }}</span>
              <span class="zx-tag">{{ job.city }}</span>
              <span class="zx-tag">招 {{ job.headcount }} 人</span>
            </div>
          </div>
          <div class="job-actions">
            <el-button size="small" plain type="primary" @click.stop="openDetail(job)">查看详情</el-button>
            <el-button size="small" type="primary" class="zx-gradient-button" @click.stop="openDetail(job)">
              申请职位
            </el-button>
          </div>
        </article>

        <div v-if="!loading && !jobs.length" class="zx-empty">
          <el-icon class="zx-empty-icon"><Search /></el-icon>
          <span>没有找到匹配的职位，换个关键词试试</span>
          <el-button text type="primary" @click="selectCategory('全部')">查看全部职位</el-button>
        </div>
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

    <el-drawer v-model="drawerVisible" size="520px" :with-header="false" class="job-drawer">
      <div v-if="currentJob" v-loading="detailLoading" class="drawer-body">
        <div class="drawer-head">
          <div class="drawer-title-row">
            <h2>{{ currentJob.title }}</h2>
            <span class="salary">{{ currentJob.salary }}</span>
          </div>
          <p class="drawer-company">{{ currentJob.company }} · {{ currentJob.city }}</p>
          <div class="drawer-tags">
            <span class="zx-tag accent">{{ currentJob.category }}</span>
            <span class="zx-tag">招 {{ currentJob.headcount }} 人</span>
            <span class="zx-tag">全职</span>
          </div>
        </div>

        <div class="drawer-actions">
          <el-button
            type="primary"
            class="zx-gradient-button"
            size="large"
            :disabled="currentJob.applied"
            :loading="applying"
            @click="apply"
          >
            {{ currentJob.applied ? '已申请' : '申请职位' }}
          </el-button>
          <el-button size="large" @click="comingSoon">感兴趣</el-button>
          <el-button size="large" plain type="primary" @click="comingSoon">数字人面试</el-button>
        </div>

        <div class="info-block">
          <h4>基本信息</h4>
          <p><el-icon><Location /></el-icon>{{ currentJob.address || currentJob.city }} · 招聘 {{ currentJob.headcount }} 人</p>
        </div>

        <div class="info-block">
          <h4>岗位职责</h4>
          <p class="paragraph">{{ currentJob.description }}</p>
        </div>

        <div class="info-block">
          <h4>任职要求</h4>
          <p class="paragraph">{{ currentJob.requirement || '详见岗位说明，欢迎投递简历沟通。' }}</p>
        </div>

        <div class="company-card">
          <div class="company-logo">{{ currentJob.company.slice(0, 1) }}</div>
          <div>
            <strong>{{ currentJob.company }}</strong>
            <p>IT 互联网 · 教育/企业服务 · {{ currentJob.city }}</p>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.job-page {
  padding-bottom: 40px;
}

.job-hero {
  background: linear-gradient(180deg, #ffffff 0%, #f5f8ff 100%);
  border-bottom: 1px solid var(--zx-border);
  padding: 44px 0 34px;
  margin-bottom: 22px;
}

.hero-head {
  text-align: center;
}

.eyebrow {
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 11px;
  letter-spacing: 0.2em;
  color: var(--zx-accent);
  font-weight: 600;
}

.hero-head h1 {
  margin-top: 8px;
  font-size: 34px;
  letter-spacing: -0.02em;
}

.hero-head p {
  margin-top: 8px;
  font-size: 14px;
  color: var(--zx-muted-fg);
}

.search-bar {
  display: flex;
  gap: 10px;
  max-width: 720px;
  margin: 24px auto 0;
  background: #fff;
  padding: 8px;
  border: 1px solid var(--zx-border);
  border-radius: 16px;
  box-shadow: var(--zx-shadow-md);
}

.scope-select {
  width: 110px;
  flex-shrink: 0;
}

.scope-select :deep(.el-select__wrapper),
.search-input :deep(.el-input__wrapper) {
  box-shadow: none;
  background: transparent;
}

.search-input {
  flex: 1;
}

.hero-stats {
  display: flex;
  justify-content: center;
  gap: 22px;
  margin-top: 16px;
  font-size: 12px;
  color: var(--zx-muted-fg);
}

.hero-stats span {
  position: relative;
}

.hero-stats span + span::before {
  content: '';
  position: absolute;
  left: -11px;
  top: 50%;
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: #cbd5e1;
}

.category-bar {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--zx-border);
  margin-bottom: 18px;
}

.category-chip {
  padding: 6px 14px;
  border: 1px solid transparent;
  border-radius: 999px;
  background: transparent;
  font-size: 13px;
  color: var(--zx-muted-fg);
  cursor: pointer;
  transition: all 0.18s ease;
}

.category-chip:hover {
  color: var(--zx-accent);
  background: #eef3ff;
}

.category-chip.active {
  color: #fff;
  background: var(--zx-fg);
  font-weight: 500;
}

.job-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 240px;
}

.job-card {
  display: flex;
  gap: 16px;
  padding: 18px 20px;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.job-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--zx-shadow-md);
  border-color: #cbd9ff;
}

.job-logo {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-size: 20px;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(135deg, #0f172a, #475569);
  flex-shrink: 0;
}

.job-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.job-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.job-title-row h3 {
  font-size: 16px;
}

.salary {
  font-size: 15px;
  font-weight: 800;
  color: #b45309;
  white-space: nowrap;
}

.job-company {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
  color: var(--zx-muted-fg);
}

.divider {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: #cbd5e1;
}

.city {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

.job-desc {
  font-size: 12.5px;
  color: var(--zx-muted-fg);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.job-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.job-actions {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
  flex-shrink: 0;
}

.job-actions .el-button + .el-button {
  margin-left: 0;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 26px;
}

.drawer-body {
  padding: 28px 26px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 400px;
}

.drawer-head {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--zx-border);
}

.drawer-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.drawer-title-row h2 {
  font-size: 22px;
  line-height: 1.35;
}

.drawer-company {
  font-size: 13px;
  color: var(--zx-muted-fg);
}

.drawer-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 4px;
}

.drawer-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.drawer-actions .el-button + .el-button {
  margin-left: 0;
}

.info-block h4 {
  font-size: 14px;
  margin-bottom: 6px;
}

.info-block p {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--zx-muted-fg);
}

.info-block .paragraph {
  display: block;
  line-height: 1.8;
  color: #334155;
  white-space: pre-line;
}

.company-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--zx-border);
  border-radius: 12px;
  background: #fbfcff;
}

.company-logo {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  color: #fff;
  font-weight: 800;
  background: linear-gradient(135deg, #0f172a, #475569);
}

.company-card strong {
  font-size: 13.5px;
}

.company-card p {
  font-size: 11.5px;
  color: var(--zx-muted-fg);
}

@media (max-width: 760px) {
  .job-card {
    flex-wrap: wrap;
  }

  .job-actions {
    flex-direction: row;
    width: 100%;
    justify-content: flex-end;
  }

  .search-bar {
    flex-direction: column;
  }

  .scope-select {
    width: 100%;
  }
}
</style>