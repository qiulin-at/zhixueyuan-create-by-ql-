<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatDotRound, CircleCheck, Clock, StarFilled, User } from '@element-plus/icons-vue'
import { courseApi } from '../api'
import { useUserStore } from '../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const course = ref(null)
const loading = ref(true)
const activeTab = ref('intro')
const completed = ref([])
const comments = ref([])
const commentsTotal = ref(0)
const commentText = ref('')
const commentRating = ref(5)
const submitting = ref(false)
const marking = ref(null)

const levelLabels = {
  beginner: '初级课程',
  intermediate: '中级课程',
  advanced: '高级课程',
  co_build: '专业共建合作课程',
}
const typeLabels = { theory: '理论课程', practice: '实训课程', certification: '认证课程' }
const contentLabels = { video: '视频', doc: '课件', lab: '实验' }
const coverThemes = {
  人工智能: 'cover-ai',
  大数据: 'cover-bigdata',
  云计算: 'cover-cloud',
  鸿蒙: 'cover-harmony',
  通信: 'cover-comm',
  数通: 'cover-network',
  工业软件: 'cover-industry',
}

const chapterStats = computed(() => {
  const list = course.value?.chapters || []
  return {
    video: list.filter((item) => item.content_type === 'video').length,
    doc: list.filter((item) => item.content_type === 'doc').length,
    lab: list.filter((item) => item.content_type === 'lab').length,
  }
})

const totalMinutes = computed(() =>
  (course.value?.chapters || []).reduce((sum, item) => sum + item.duration_min, 0),
)

const fetchDetail = async () => {
  loading.value = true
  try {
    course.value = await courseApi.detail(route.params.id)
    if (userStore.isLoggedIn) {
      const progress = await courseApi.getProgress(route.params.id)
      completed.value = progress.completed_chapters || []
    }
    await loadComments()
  } catch (error) {
    ElMessage.error(error.message)
    router.replace('/')
  } finally {
    loading.value = false
  }
}

const loadComments = async () => {
  try {
    const data = await courseApi.comments(route.params.id, { page: 1, page_size: 20 })
    comments.value = data.items
    commentsTotal.value = data.total
  } catch (error) {
    comments.value = []
  }
}

const requireLogin = () => {
  ElMessage.warning('请先登录后再操作')
  router.push({ name: 'login', query: { redirect: route.fullPath } })
}

const toggleFavorite = async () => {
  if (!userStore.isLoggedIn) {
    requireLogin()
    return
  }
  try {
    const data = await courseApi.toggleFavorite(course.value.id)
    course.value.is_favorite = data.is_favorite
    ElMessage.success(data.is_favorite ? '已加入收藏' : '已取消收藏')
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const startLearning = () => {
  if (!userStore.isLoggedIn) {
    requireLogin()
    return
  }
  activeTab.value = 'catalog'
  ElMessage.info('请选择章节开始学习，学完后点击「标记完成」')
}

const markCompleted = async (chapter) => {
  if (!userStore.isLoggedIn) {
    requireLogin()
    return
  }
  marking.value = chapter.id
  try {
    const data = await courseApi.updateProgress(course.value.id, {
      chapter_id: chapter.id,
      minutes: chapter.duration_min,
    })
    completed.value = data.completed_chapters
    course.value.progress = data.progress
    course.value.study_minutes = data.study_minutes
    ElMessage.success(`本章已完成，课程进度 ${data.progress}%`)
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    marking.value = null
  }
}

const askAi = () => {
  router.push({ name: 'ai', query: { courseId: course.value.id } })
}

const submitComment = async () => {
  if (!userStore.isLoggedIn) {
    requireLogin()
    return
  }
  if (!commentText.value.trim()) {
    ElMessage.warning('请填写评论内容')
    return
  }
  submitting.value = true
  try {
    await courseApi.addComment(course.value.id, {
      content: commentText.value.trim(),
      rating: commentRating.value,
    })
    commentText.value = ''
    commentRating.value = 5
    ElMessage.success('评论已发布')
    const detail = await courseApi.detail(course.value.id)
    course.value.rating = detail.rating
    course.value.rating_count = detail.rating_count
    await loadComments()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    submitting.value = false
  }
}

const formatDate = (value) => (value ? value.slice(0, 10) : '')

onMounted(fetchDetail)
</script>

<template>
  <div v-loading="loading" class="detail-page">
    <template v-if="course">
      <section class="detail-hero">
        <div class="hero-glow"></div>
        <div class="zx-container">
          <div class="breadcrumb">
            <router-link to="/">课程中心</router-link>
            <span>/</span>
            <span>{{ course.tech_system }}</span>
            <span>/</span>
            <span>{{ course.title }}</span>
          </div>

          <div class="hero-grid">
            <div class="hero-cover" :class="coverThemes[course.tech_system] || 'cover-default'">
              <div class="cover-ring"></div>
              <div class="cover-content">
                <span class="cover-system">{{ course.tech_system }}</span>
                <h2>{{ course.title }}</h2>
                <div class="cover-tags">
                  <span>{{ typeLabels[course.course_type] }}</span>
                  <span>{{ levelLabels[course.level] }}</span>
                </div>
              </div>
            </div>

            <div class="hero-info">
              <div class="tag-row">
                <span class="zx-tag accent">{{ course.tech_direction || '综合方向' }}</span>
                <span class="zx-tag">{{ levelLabels[course.level] }}</span>
                <span class="zx-tag" :class="course.is_free ? 'free' : 'paid'">
                  {{ course.is_free ? '免费课程' : `付费课程 ¥${course.price}` }}
                </span>
              </div>

              <h1>{{ course.title }}</h1>
              <p class="intro">{{ course.intro }}</p>

              <div class="meta-row">
                <span>
                  <el-icon><User /></el-icon>
                  {{ course.teacher.name }}
                </span>
                <span class="rating">
                  <el-icon><StarFilled /></el-icon>
                  {{ course.rating.toFixed(1) }}
                  <em>（{{ course.rating_count }} 人次评价）</em>
                </span>
                <span>{{ course.study_count }} 人在学</span>
              </div>

              <div class="stat-row">
                <div><strong>{{ chapterStats.doc }}</strong><span>课件</span></div>
                <div><strong>{{ chapterStats.video }}</strong><span>视频</span></div>
                <div><strong>{{ chapterStats.lab }}</strong><span>实验</span></div>
                <div><strong>{{ totalMinutes }}</strong><span>总时长 / 分钟</span></div>
              </div>

              <div v-if="userStore.isLoggedIn" class="progress-row">
                <div class="progress-text">
                  <span>学习进展</span>
                  <strong>{{ course.progress }}%</strong>
                </div>
                <el-progress :percentage="course.progress" :stroke-width="8" :show-text="false" />
                <span class="minutes">累计学习 {{ course.study_minutes }} 分钟</span>
              </div>

              <div class="action-row">
                <el-button type="primary" size="large" class="zx-gradient-button" @click="startLearning">
                  立即学习
                </el-button>
                <el-button size="large" :class="{ favorited: course.is_favorite }" @click="toggleFavorite">
                  <el-icon><StarFilled /></el-icon>
                  {{ course.is_favorite ? '已收藏' : '收藏' }}
                </el-button>
                <el-button size="large" plain type="primary" @click="askAi">
                  <el-icon><ChatDotRound /></el-icon>
                  问 AI 助教
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div class="zx-container">
        <div class="detail-body zx-card">
          <el-tabs v-model="activeTab">
            <el-tab-pane label="课程简介" name="intro">
              <div class="intro-grid">
                <div class="intro-main">
                  <h3 class="block-title">课程简介</h3>
                  <p class="desc">{{ course.description }}</p>

                  <h3 class="block-title">你将学到</h3>
                  <ul class="objective-list">
                    <li v-for="item in course.objectives" :key="item">
                      <el-icon><CircleCheck /></el-icon>
                      <span>{{ item }}</span>
                    </li>
                  </ul>
                </div>

                <aside class="teacher-card">
                  <el-avatar :size="56">{{ course.teacher.name.slice(0, 1) }}</el-avatar>
                  <strong>{{ course.teacher.name }}</strong>
                  <span class="teacher-major">{{ course.teacher.major || '平台认证讲师' }}</span>
                  <p>负责本课程的内容设计与答疑</p>
                  <el-button size="small" plain type="primary" @click="askAi">向讲师 / AI 提问</el-button>
                </aside>
              </div>
            </el-tab-pane>

            <el-tab-pane :label="`课程目录（${course.chapter_count}）`" name="catalog">
              <div class="catalog-head">
                <span>共 {{ course.chapter_count }} 个章节 · 预计 {{ totalMinutes }} 分钟</span>
                <span class="catalog-tip">完成章节后点击「标记完成」累计进度</span>
              </div>
              <div class="chapter-list">
                <div v-for="(chapter, index) in course.chapters" :key="chapter.id" class="chapter-row">
                  <span class="chapter-index">{{ String(index + 1).padStart(2, '0') }}</span>
                  <span class="chapter-type" :class="chapter.content_type">{{ contentLabels[chapter.content_type] }}</span>
                  <span class="chapter-title">{{ chapter.title }}</span>
                  <span class="chapter-duration">
                    <el-icon><Clock /></el-icon>
                    {{ chapter.duration_min }} 分钟
                  </span>
                  <span v-if="completed.includes(chapter.id)" class="chapter-done">
                    <el-icon><CircleCheck /></el-icon>
                    已完成
                  </span>
                  <el-button
                    v-else
                    size="small"
                    :loading="marking === chapter.id"
                    @click="markCompleted(chapter)"
                  >
                    标记完成
                  </el-button>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane :label="`课程评论（${commentsTotal}）`" name="comments">
              <div class="comment-editor">
                <div class="editor-head">
                  <span>发表评论</span>
                  <el-rate v-model="commentRating" />
                </div>
                <el-input
                  v-model="commentText"
                  type="textarea"
                  :rows="3"
                  maxlength="500"
                  show-word-limit
                  placeholder="分享你的学习感受，帮助更多同学了解这门课"
                />
                <div class="editor-foot">
                  <el-button type="primary" class="zx-gradient-button" :loading="submitting" @click="submitComment">
                    发布评论
                  </el-button>
                </div>
              </div>

              <div class="comment-list">
                <div v-for="item in comments" :key="item.id" class="comment-item">
                  <el-avatar :size="36">{{ item.user_name.slice(0, 1) }}</el-avatar>
                  <div class="comment-main">
                    <div class="comment-head">
                      <strong>{{ item.user_name }}</strong>
                      <el-rate :model-value="item.rating" disabled size="small" />
                      <span class="comment-time">{{ formatDate(item.created_at) }}</span>
                    </div>
                    <p>{{ item.content }}</p>
                  </div>
                </div>
                <el-empty v-if="!comments.length" description="还没有评论，来抢沙发" />
              </div>
            </el-tab-pane>

            <el-tab-pane label="课程答疑" name="qa">
              <div class="qa-panel">
                <div class="qa-icon">
                  <el-icon><ChatDotRound /></el-icon>
                </div>
                <h3>有疑问？让 AI 助教帮你</h3>
                <p>
                  AI 助教已加载《{{ course.title }}》的课程简介与当前学习章节，可以解答概念、代码和实验问题，并支持多轮追问。
                </p>
                <div class="qa-actions">
                  <el-button type="primary" class="zx-gradient-button" size="large" @click="askAi">
                    开始提问
                  </el-button>
                  <span class="qa-hint">无模型 Key 时自动使用本地 Mock 引擎，演示不中断</span>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.detail-page {
  min-height: 60vh;
}

.detail-hero {
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, #ffffff 0%, #f5f8ff 100%);
  border-bottom: 1px solid var(--zx-border);
  padding: 22px 0 34px;
}

.hero-glow {
  position: absolute;
  width: 460px;
  height: 460px;
  border-radius: 50%;
  right: -120px;
  top: -200px;
  background: radial-gradient(circle, rgba(0, 82, 255, 0.1), transparent 65%);
  filter: blur(18px);
  pointer-events: none;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--zx-muted-fg);
  margin-bottom: 20px;
  position: relative;
}

.breadcrumb a {
  color: var(--zx-muted-fg);
}

.breadcrumb a:hover {
  color: var(--zx-accent);
}

.breadcrumb span:last-child {
  color: var(--zx-fg);
  font-weight: 500;
}

.hero-grid {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 34px;
  position: relative;
}

.hero-cover {
  position: relative;
  height: 200px;
  border-radius: 18px;
  padding: 26px;
  color: #fff;
  overflow: hidden;
  box-shadow: var(--zx-shadow-lg);
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
  width: 210px;
  height: 210px;
  border: 1.5px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  right: -60px;
  bottom: -90px;
}

.cover-ring::after {
  content: '';
  position: absolute;
  width: 120px;
  height: 120px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 50%;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
}

.cover-content {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.cover-system {
  font-size: 11px;
  letter-spacing: 0.18em;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
}

.cover-content h2 {
  color: #fff;
  font-size: 22px;
  line-height: 1.35;
  max-width: 240px;
}

.cover-tags {
  display: flex;
  gap: 8px;
  font-size: 11px;
}

.cover-tags span {
  padding: 2px 9px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.14);
}

.hero-info h1 {
  margin-top: 14px;
  font-size: 30px;
  line-height: 1.25;
  letter-spacing: -0.02em;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.intro {
  margin-top: 10px;
  font-size: 14px;
  color: var(--zx-muted-fg);
  max-width: 720px;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 18px;
  margin-top: 14px;
  font-size: 13px;
  color: var(--zx-muted-fg);
}

.meta-row .el-icon {
  vertical-align: -2px;
  margin-right: 3px;
}

.meta-row .rating {
  color: #b45309;
}

.meta-row em {
  font-style: normal;
  color: var(--zx-muted-fg);
  font-size: 12px;
}

.stat-row {
  display: flex;
  gap: 28px;
  margin: 18px 0;
  padding: 12px 0;
  border-top: 1px dashed var(--zx-border);
  border-bottom: 1px dashed var(--zx-border);
}

.stat-row div {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.stat-row strong {
  font-size: 20px;
  color: var(--zx-fg);
}

.stat-row span {
  font-size: 12px;
  color: var(--zx-muted-fg);
}

.progress-row {
  margin-bottom: 16px;
  max-width: 520px;
}

.progress-text {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--zx-muted-fg);
  margin-bottom: 6px;
}

.progress-text strong {
  color: var(--zx-accent);
}

.minutes {
  display: block;
  margin-top: 5px;
  font-size: 11px;
  color: var(--zx-muted-fg);
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.action-row .el-button + .el-button {
  margin-left: 0;
}

.favorited {
  color: #b45309;
  border-color: #fde68a;
  background: #fffbeb;
}

.detail-body {
  margin-top: 24px;
  padding: 8px 28px 30px;
}

.detail-body :deep(.el-tabs__header) {
  margin-bottom: 22px;
}

.intro-grid {
  display: grid;
  grid-template-columns: 1fr 260px;
  gap: 40px;
}

.block-title {
  font-size: 16px;
  margin: 20px 0 10px;
}

.block-title:first-child {
  margin-top: 0;
}

.desc {
  color: #334155;
  line-height: 1.85;
  font-size: 14px;
}

.objective-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 20px;
}

.objective-list li {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  font-size: 13.5px;
  color: #334155;
}

.objective-list .el-icon {
  color: #10b981;
  margin-top: 3px;
  flex-shrink: 0;
}

.teacher-card {
  align-self: start;
  border: 1px solid var(--zx-border);
  border-radius: 14px;
  padding: 22px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 8px;
  background: #fbfcff;
}

.teacher-card strong {
  font-size: 15px;
}

.teacher-major {
  font-size: 12px;
  color: var(--zx-accent);
}

.teacher-card p {
  font-size: 12px;
  color: var(--zx-muted-fg);
  line-height: 1.6;
}

.catalog-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 13px;
  color: var(--zx-muted-fg);
  padding-bottom: 14px;
  border-bottom: 1px solid var(--zx-border);
}

.catalog-tip {
  font-size: 12px;
  color: #94a3b8;
}

.chapter-list {
  display: flex;
  flex-direction: column;
}

.chapter-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 6px;
  border-bottom: 1px dashed var(--zx-border);
}

.chapter-row:last-child {
  border-bottom: none;
}

.chapter-index {
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 12px;
  color: #94a3b8;
  width: 26px;
}

.chapter-type {
  padding: 1px 8px;
  border-radius: 5px;
  font-size: 11px;
  background: #eef3ff;
  color: var(--zx-accent);
  flex-shrink: 0;
}

.chapter-type.doc {
  background: #fff7ed;
  color: #c2410c;
}

.chapter-type.lab {
  background: #ecfdf5;
  color: #047857;
}

.chapter-title {
  flex: 1;
  font-size: 14px;
  color: var(--zx-fg);
}

.chapter-duration {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--zx-muted-fg);
}

.chapter-done {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #047857;
  width: 76px;
  justify-content: center;
}

.comment-editor {
  border: 1px solid var(--zx-border);
  border-radius: 12px;
  padding: 16px;
  background: #fbfcff;
  margin-bottom: 24px;
}

.editor-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: 600;
}

.editor-foot {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.comment-item {
  display: flex;
  gap: 12px;
}

.comment-main {
  flex: 1;
  border-bottom: 1px dashed var(--zx-border);
  padding-bottom: 14px;
}

.comment-head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.comment-head strong {
  font-size: 13.5px;
}

.comment-time {
  margin-left: auto;
  font-size: 11px;
  color: #94a3b8;
}

.comment-main p {
  margin-top: 6px;
  font-size: 13.5px;
  color: #334155;
  line-height: 1.7;
}

.qa-panel {
  max-width: 560px;
  margin: 20px auto;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.qa-icon {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  display: grid;
  place-items: center;
  font-size: 28px;
  color: #fff;
  background: linear-gradient(135deg, var(--zx-accent), #7c9dff);
  box-shadow: var(--zx-shadow-accent);
}

.qa-panel h3 {
  font-size: 20px;
}

.qa-panel p {
  font-size: 13.5px;
  color: var(--zx-muted-fg);
  line-height: 1.75;
}

.qa-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.qa-hint {
  font-size: 11.5px;
  color: #94a3b8;
}

@media (max-width: 960px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }

  .hero-cover {
    height: 180px;
  }

  .intro-grid {
    grid-template-columns: 1fr;
  }

  .teacher-card {
    width: 100%;
  }

  .objective-list {
    grid-template-columns: 1fr;
  }

  .hero-info h1 {
    font-size: 24px;
  }
}
</style>