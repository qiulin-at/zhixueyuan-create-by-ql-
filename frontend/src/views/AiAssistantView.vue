<script setup>
import { nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatDotRound, Promotion } from '@element-plus/icons-vue'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { aiApi, courseApi } from '../api'

marked.setOptions({ breaks: true, gfm: true })

const route = useRoute()
const tab = ref('chat')
const mode = ref('mock')

const courseOptions = ref([])
const selectedCourseId = ref(null)
const conversations = ref([])
const activeConversation = ref(null)
const messages = ref([])
const input = ref('')
const sending = ref(false)
const messageArea = ref(null)

const pathForm = reactive({
  goal: '三个月拿下 HCIA-AI 认证',
  weekly_hours: 8,
  weak_points: '深度学习与模型调优',
})
const pathResult = ref(null)
const pathList = ref([])
const pathLoading = ref(false)
const pathActionLoading = ref(false)
const pathStatusLabel = {
  draft: '草稿',
  active: '已启用',
  adjusted: '已调整',
  rejected: '已放弃',
}

const gradeForm = reactive({
  title: '两数之和',
  language: 'python',
  code: 'def two_sum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target - n], i]\n        seen[n] = i\n    return []\n',
})
const gradeResult = ref(null)
const gradeLoading = ref(false)

const suggestions = [
  'HDFS 的副本机制是怎么工作的？',
  'pandas 分组聚合怎么写？',
  '如何判断模型是否过拟合？',
]

const renderMarkdown = (text) => DOMPurify.sanitize(marked.parse(text || ''))

const scrollToBottom = async () => {
  await nextTick()
  if (messageArea.value) {
    messageArea.value.scrollTop = messageArea.value.scrollHeight
  }
}

const loadCourses = async () => {
  try {
    const data = await courseApi.list({ page_size: 50, sort: 'rating' })
    courseOptions.value = data.items
    if (route.query.courseId) {
      selectedCourseId.value = Number(route.query.courseId)
    }
  } catch (error) {
    courseOptions.value = []
  }
}

const refreshConversations = async () => {
  try {
    const data = await aiApi.conversations()
    conversations.value = data.items
  } catch (error) {
    conversations.value = []
  }
}

const openConversation = async (item) => {
  try {
    const data = await aiApi.conversation(item.id)
    activeConversation.value = data
    messages.value = data.messages
    selectedCourseId.value = data.course_id
    tab.value = 'chat'
    await scrollToBottom()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const newConversation = () => {
  activeConversation.value = null
  messages.value = []
  input.value = ''
  tab.value = 'chat'
}

const send = async (preset) => {
  const text = (preset || input.value).trim()
  if (!text || sending.value) return
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  sending.value = true
  await scrollToBottom()
  try {
    const payload = { message: text }
    if (activeConversation.value) {
      payload.conversation_id = activeConversation.value.id
    } else if (selectedCourseId.value) {
      payload.course_id = selectedCourseId.value
    }
    const data = await aiApi.chat(payload)
    mode.value = data.mode
    messages.value.push({
      role: 'assistant',
      id: data.message_id,
      content: data.answer,
      insufficient: data.insufficient,
      citations: data.citations || [],
      feedback: null,
    })
    if (!activeConversation.value) {
      activeConversation.value = { id: data.conversation_id, course_id: data.course_id }
      await refreshConversations()
    }
  } catch (error) {
    ElMessage.error(error.message)
    messages.value.push({ role: 'assistant', content: `抱歉，本次回答失败：${error.message}` })
  } finally {
    sending.value = false
    await scrollToBottom()
  }
}

const submitFeedback = async (message, helpful) => {
  if (!message.id) return
  try {
    const data = await aiApi.feedback(message.id, {
      helpful,
      reason: helpful ? '' : '回答需要改进',
    })
    message.feedback = data.helpful ? 'helpful' : 'unhelpful'
    ElMessage.success('反馈已记录')
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const loadPathList = async () => {
  try {
    const data = await aiApi.learningPaths()
    pathList.value = data.items
  } catch (error) {
    pathList.value = []
  }
}

const loadPath = (item) => {
  pathResult.value = item
}

const generatePath = async () => {
  if (!pathForm.goal.trim()) {
    ElMessage.warning('请填写学习目标')
    return
  }
  pathLoading.value = true
  try {
    const data = await aiApi.learningPath({
      goal: pathForm.goal.trim(),
      weekly_hours: pathForm.weekly_hours,
      weak_points: pathForm.weak_points,
    })
    pathResult.value = data
    mode.value = data.mode
    await loadPathList()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    pathLoading.value = false
  }
}

const applyPathAction = async (action) => {
  if (!pathResult.value) return
  pathActionLoading.value = true
  try {
    const data = await aiApi.updateLearningPath(pathResult.value.id, { action })
    pathResult.value = { ...pathResult.value, ...data }
    ElMessage.success(action === 'accept' ? '路径已启用' : '路径已放弃')
    await loadPathList()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    pathActionLoading.value = false
  }
}

const moveStage = async (index, direction) => {
  if (!pathResult.value) return
  const stages = [...pathResult.value.stages]
  const target = index + direction
  if (target < 0 || target >= stages.length) return
  ;[stages[index], stages[target]] = [stages[target], stages[index]]
  pathResult.value.stages = stages
  pathActionLoading.value = true
  try {
    const data = await aiApi.updateLearningPath(pathResult.value.id, {
      action: 'adjust',
      stages,
    })
    pathResult.value = { ...pathResult.value, ...data }
    ElMessage.success('路径顺序已保存')
    await loadPathList()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    pathActionLoading.value = false
  }
}

const runGrade = async () => {
  if (!gradeForm.code.trim()) {
    ElMessage.warning('请粘贴需要批改的代码')
    return
  }
  gradeLoading.value = true
  try {
    const data = await aiApi.grade({ ...gradeForm })
    gradeResult.value = data.result
    mode.value = data.mode
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    gradeLoading.value = false
  }
}

const severityLabel = { high: '严重', medium: '中等', low: '建议' }

onMounted(async () => {
  await loadCourses()
  await refreshConversations()
  await loadPathList()
  if (route.query.tab === 'path') {
    tab.value = 'path'
  }
  if (conversations.value.length && !route.query.courseId) {
    await openConversation(conversations.value[0])
  }
})
</script>

<template>
  <div class="ai-page">
    <div class="zx-container">
      <div class="ai-hero">
        <div>
          <span class="eyebrow">AI LEARNING COPILOT</span>
          <h1>AI 学习助手</h1>
          <p>绑定课程上下文的多轮答疑、个性化学习路径、代码作业批改，一个入口全部搞定。</p>
        </div>
        <div class="mode-pill" :class="mode">
          <span class="dot"></span>
          {{ mode === 'online' ? '在线大模型' : 'Mock 演示模式' }}
        </div>
      </div>

      <div class="ai-grid">
        <aside class="session-panel zx-card">
          <div class="session-head">
            <span>我的对话</span>
            <el-button size="small" type="primary" plain @click="newConversation">新建</el-button>
          </div>
          <div class="session-list">
            <button
              v-for="item in conversations"
              :key="item.id"
              type="button"
              :class="['session-item', { active: activeConversation?.id === item.id }]"
              @click="openConversation(item)"
            >
              <span class="session-title">{{ item.title }}</span>
              <span class="session-meta">{{ item.course_title }}</span>
            </button>
            <div v-if="!conversations.length" class="session-empty">暂无对话，开始你的第一个提问</div>
          </div>
          <div class="session-foot">
            <el-icon><ChatDotRound /></el-icon>
            <span>对话自动保存，可随时切换</span>
          </div>
        </aside>

        <section class="assistant-panel zx-card">
          <el-tabs v-model="tab">
            <el-tab-pane label="智能答疑" name="chat">
              <div class="chat-toolbar">
                <el-select v-model="selectedCourseId" placeholder="绑定课程（可选）" clearable size="default" style="width: 260px">
                  <el-option v-for="course in courseOptions" :key="course.id" :label="course.title" :value="course.id" />
                </el-select>
                <span class="toolbar-hint">绑定课程后，AI 会结合课程简介与当前学习章节回答</span>
              </div>

              <div ref="messageArea" class="message-area">
                <div v-if="!messages.length" class="chat-welcome">
                  <div class="welcome-icon">
                    <el-icon><ChatDotRound /></el-icon>
                  </div>
                  <h2>你好，我是智学 AI 助教</h2>
                  <p>可以问我课程概念、代码问题，也可以让我帮你规划学习路径。试试下面的问题：</p>
                  <div class="suggestion-list">
                    <button v-for="item in suggestions" :key="item" type="button" @click="send(item)">
                      {{ item }}
                    </button>
                  </div>
                </div>

                <div v-for="(message, index) in messages" :key="index" :class="['message', message.role]">
                  <div v-if="message.role === 'assistant'" class="ai-avatar">AI</div>
                  <div class="bubble">
                    <div v-if="message.insufficient" class="insufficient-tag">课程资料暂未覆盖</div>
                    <div class="markdown-body" v-html="renderMarkdown(message.content)"></div>
                    <div v-if="message.citations && message.citations.length" class="citation-list">
                      <span
                        v-for="(citation, cIndex) in message.citations"
                        :key="cIndex"
                        class="citation-item"
                      >
                        {{ citation.title }}
                        <em v-if="citation.section">{{ citation.section }}</em>
                      </span>
                    </div>
                    <div v-if="message.role === 'assistant' && message.id" class="feedback-row">
                      <button
                        type="button"
                        :class="{ active: message.feedback === 'helpful' }"
                        @click="submitFeedback(message, true)"
                      >
                        有帮助
                      </button>
                      <button
                        type="button"
                        :class="{ active: message.feedback === 'unhelpful' }"
                        @click="submitFeedback(message, false)"
                      >
                        需要改进
                      </button>
                    </div>
                  </div>
                </div>

                <div v-if="sending" class="message assistant">
                  <div class="ai-avatar">AI</div>
                  <div class="bubble typing">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>

              <div class="composer">
                <el-input
                  v-model="input"
                  type="textarea"
                  :rows="2"
                  resize="none"
                  placeholder="输入你的问题，Enter 发送，Shift + Enter 换行"
                  @keydown.enter.exact.prevent="send()"
                />
                <el-button type="primary" class="zx-gradient-button send-btn" :loading="sending" @click="send()">
                  <el-icon><Promotion /></el-icon>
                  发送
                </el-button>
              </div>
            </el-tab-pane>

            <el-tab-pane label="学习路径" name="path">
              <div class="tool-grid">
                <div class="tool-form">
                  <h3>生成个性化学习路径</h3>
                  <p class="form-desc">系统会读取你的学习记录、进度与已完成课程，生成只包含平台已上架课程的分阶段路径。</p>
                  <label class="field">
                    <span>学习目标</span>
                    <el-input v-model="pathForm.goal" placeholder="例如：三个月拿下 HCIA-AI 认证" />
                  </label>
                  <label class="field">
                    <span>每周可投入：{{ pathForm.weekly_hours }} 小时</span>
                    <el-slider v-model="pathForm.weekly_hours" :min="1" :max="30" :step="1" />
                  </label>
                  <label class="field">
                    <span>薄弱点</span>
                    <el-input v-model="pathForm.weak_points" placeholder="例如：深度学习、模型调优" />
                  </label>
                  <el-button type="primary" class="zx-gradient-button" :loading="pathLoading" @click="generatePath">
                    生成学习路径
                  </el-button>
                </div>

                <div class="tool-result">
                  <div v-if="pathResult" class="path-result">
                    <div class="path-head">
                      <div>
                        <h3>{{ pathResult.goal }}</h3>
                        <p>
                          每周 {{ pathResult.weekly_hours }} 小时 · 版本 v{{ pathResult.version }} ·
                          {{ pathStatusLabel[pathResult.status] || pathResult.status }}
                        </p>
                      </div>
                      <div class="path-actions">
                        <el-button
                          size="small"
                          type="primary"
                          plain
                          :loading="pathActionLoading"
                          @click="applyPathAction('accept')"
                        >
                          接受路径
                        </el-button>
                        <el-button size="small" :loading="pathActionLoading" @click="applyPathAction('reject')">
                          放弃
                        </el-button>
                      </div>
                    </div>

                    <div v-if="pathResult.resource_gap" class="path-gap">
                      资源缺口：{{ pathResult.resource_gap }}
                    </div>

                    <div v-for="(stage, index) in pathResult.stages" :key="index" class="path-stage">
                      <div class="path-stage-head">
                        <strong>阶段 {{ index + 1 }} · {{ stage.goal }}</strong>
                        <div class="path-stage-tools">
                          <el-button link size="small" :disabled="index === 0" @click="moveStage(index, -1)">
                            上移
                          </el-button>
                          <el-button
                            link
                            size="small"
                            :disabled="index === pathResult.stages.length - 1"
                            @click="moveStage(index, 1)"
                          >
                            下移
                          </el-button>
                        </div>
                      </div>
                      <div class="path-courses">
                        <span v-for="course in stage.courses" :key="course.course_id" class="path-course">
                          {{ course.title }} · {{ course.hours }}h
                        </span>
                        <span v-if="!stage.courses.length" class="path-course muted">平台暂无匹配课程</span>
                      </div>
                      <p class="path-meta">检查点：{{ stage.checkpoint || '—' }}</p>
                      <p class="path-reason">{{ stage.reason }}</p>
                    </div>

                    <div class="path-inputs">
                      <span>依据：{{ pathResult.inputs?.records?.length || 0 }} 门在学课程</span>
                      <span v-if="pathResult.inputs?.completed_courses?.length">
                        已完成 {{ pathResult.inputs.completed_courses.length }} 门
                      </span>
                      <span v-if="pathResult.inputs?.weak_points">
                        自述薄弱点：{{ pathResult.inputs.weak_points }}
                      </span>
                    </div>
                  </div>
                  <div v-else class="result-placeholder">
                    <span class="placeholder-icon">🗺️</span>
                    <p>填写目标后，这里会展示基于真实学习记录的分阶段路径，可接受、调整顺序或放弃</p>
                  </div>

                  <div v-if="pathList.length" class="path-history">
                    <h4>历史路径</h4>
                    <div
                      v-for="item in pathList"
                      :key="item.id"
                      class="path-history-row"
                      @click="loadPath(item)"
                    >
                      <span>{{ item.goal }}</span>
                      <em>{{ pathStatusLabel[item.status] || item.status }} · v{{ item.version }}</em>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="作业批改" name="grade">
              <div class="tool-grid grade-grid">
                <div class="tool-form">
                  <h3>代码作业智能批改</h3>
                  <p class="form-desc">粘贴代码，AI 从正确性、可读性、健壮性三个维度评分并给出修改建议。</p>
                  <label class="field">
                    <span>题目</span>
                    <el-input v-model="gradeForm.title" placeholder="例如：两数之和" />
                  </label>
                  <label class="field">
                    <span>语言</span>
                    <el-select v-model="gradeForm.language" style="width: 100%">
                      <el-option label="Python" value="python" />
                      <el-option label="JavaScript" value="javascript" />
                      <el-option label="Java" value="java" />
                      <el-option label="C++" value="cpp" />
                    </el-select>
                  </label>
                  <label class="field">
                    <span>代码</span>
                    <el-input v-model="gradeForm.code" type="textarea" :rows="12" placeholder="粘贴你的代码..." />
                  </label>
                  <el-button type="primary" class="zx-gradient-button" :loading="gradeLoading" @click="runGrade">
                    开始批改
                  </el-button>
                </div>

                <div class="tool-result">
                  <template v-if="gradeResult">
                    <div class="score-card">
                      <div class="score-ring" :style="{ '--score': `${gradeResult.score}%` }">
                        <span>{{ gradeResult.score }}</span>
                        <em>总分</em>
                      </div>
                      <p class="summary">{{ gradeResult.summary }}</p>
                    </div>
                    <div class="dimension-list">
                      <div v-for="(value, name) in gradeResult.dimension_scores" :key="name" class="dimension">
                        <div class="dimension-head">
                          <span>{{ name }}</span>
                          <strong>{{ value }}</strong>
                        </div>
                        <div class="dimension-bar">
                          <span :style="{ width: `${value}%` }"></span>
                        </div>
                      </div>
                    </div>
                    <div class="issue-list">
                      <div v-for="(issue, index) in gradeResult.issues" :key="index" class="issue-item">
                        <span class="severity" :class="issue.severity">{{ severityLabel[issue.severity] }}</span>
                        <span class="issue-line">行 {{ issue.line || '—' }}</span>
                        <p>{{ issue.suggestion }}</p>
                      </div>
                    </div>
                  </template>
                  <div v-else class="result-placeholder">
                    <span class="placeholder-icon">📝</span>
                    <p>提交代码后，这里会展示分数、维度评分与逐条修改建议</p>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ai-page {
  padding-top: 30px;
}

.ai-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 22px;
  flex-wrap: wrap;
}

.eyebrow {
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 11px;
  letter-spacing: 0.2em;
  color: var(--zx-accent);
  font-weight: 600;
}

.ai-hero h1 {
  margin-top: 8px;
  font-size: 30px;
  letter-spacing: -0.02em;
}

.ai-hero p {
  margin-top: 6px;
  font-size: 14px;
  color: var(--zx-muted-fg);
}

.mode-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 999px;
  font-size: 12px;
  border: 1px solid var(--zx-border);
  background: #fff;
  color: var(--zx-muted-fg);
}

.mode-pill .dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #10b981;
}

.mode-pill.mock .dot {
  background: #f59e0b;
}

.ai-grid {
  display: grid;
  grid-template-columns: 270px 1fr;
  gap: 18px;
  align-items: stretch;
}

.session-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  max-height: 640px;
}

.session-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid var(--zx-border);
  font-size: 14px;
  font-weight: 600;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.session-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  padding: 10px 12px;
  border: none;
  background: transparent;
  border-radius: 9px;
  cursor: pointer;
  text-align: left;
  transition: background 0.18s ease;
}

.session-item:hover {
  background: var(--zx-muted);
}

.session-item.active {
  background: #eef3ff;
}

.session-title {
  width: 100%;
  font-size: 13px;
  font-weight: 500;
  color: var(--zx-fg);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-item.active .session-title {
  color: var(--zx-accent);
}

.session-meta {
  font-size: 11px;
  color: var(--zx-muted-fg);
}

.session-empty {
  padding: 30px 12px;
  text-align: center;
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.7;
}

.session-foot {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 16px;
  border-top: 1px solid var(--zx-border);
  font-size: 11px;
  color: #94a3b8;
}

.assistant-panel {
  padding: 6px 22px 20px;
  min-height: 640px;
}

.assistant-panel :deep(.el-tabs__header) {
  margin-bottom: 16px;
}

.chat-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.toolbar-hint {
  font-size: 12px;
  color: #94a3b8;
}

.message-area {
  height: 430px;
  overflow-y: auto;
  padding: 16px 6px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #fbfcff;
  border: 1px solid var(--zx-border);
  border-radius: 12px;
}

.chat-welcome {
  margin: auto;
  max-width: 520px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 20px;
}

.welcome-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  font-size: 26px;
  color: #fff;
  background: linear-gradient(135deg, var(--zx-accent), #7c9dff);
  box-shadow: var(--zx-shadow-accent);
}

.chat-welcome h2 {
  font-size: 20px;
}

.chat-welcome p {
  font-size: 13px;
  color: var(--zx-muted-fg);
  line-height: 1.7;
}

.suggestion-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 6px;
}

.suggestion-list button {
  border: 1px solid var(--zx-border);
  background: #fff;
  padding: 7px 13px;
  border-radius: 999px;
  font-size: 12.5px;
  color: var(--zx-fg);
  cursor: pointer;
  transition: all 0.18s ease;
}

.suggestion-list button:hover {
  border-color: #b3c8ff;
  color: var(--zx-accent);
  background: #eef3ff;
}

.message {
  display: flex;
  gap: 10px;
  padding: 0 12px;
}

.message.user {
  justify-content: flex-end;
}

.ai-avatar {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border-radius: 10px;
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(135deg, var(--zx-accent), #7c9dff);
}

.bubble {
  max-width: 78%;
  padding: 11px 15px;
  border-radius: 12px;
  font-size: 13.5px;
}

.message.assistant .bubble {
  background: #fff;
  border: 1px solid var(--zx-border);
  border-top-left-radius: 4px;
}

.message.user .bubble {
  background: linear-gradient(120deg, var(--zx-accent), #3d70ff);
  color: #fff;
  border-top-right-radius: 4px;
  box-shadow: var(--zx-shadow-accent);
}

.message.user .bubble :deep(p) {
  margin: 0;
}

.insufficient-tag {
  display: inline-block;
  margin-bottom: 8px;
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 11.5px;
  color: #b45309;
  background: #fffbeb;
  border: 1px solid #fde68a;
}

.citation-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.citation-item {
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 11.5px;
  color: #475569;
  background: #f1f5f9;
}

.citation-item em {
  margin-left: 4px;
  font-style: normal;
  color: #94a3b8;
}

.feedback-row {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.feedback-row button {
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid var(--zx-border);
  background: #fff;
  color: var(--zx-muted-fg);
  font-size: 11.5px;
  cursor: pointer;
}

.feedback-row button.active {
  color: #0052ff;
  border-color: #bfdbfe;
  background: #eff6ff;
}

.typing {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 16px;
}

.typing span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #94a3b8;
  animation: typing 1.2s infinite ease-in-out;
}

.typing span:nth-child(2) {
  animation-delay: 0.15s;
}

.typing span:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes typing {
  0%,
  60%,
  100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

.composer {
  display: flex;
  gap: 10px;
  margin-top: 12px;
  align-items: flex-end;
}

.composer .el-textarea {
  flex: 1;
}

.send-btn {
  height: 54px;
  padding: 0 24px;
}

.tool-grid {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 26px;
  min-height: 480px;
}

.tool-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.tool-form h3 {
  font-size: 17px;
}

.form-desc {
  font-size: 12.5px;
  color: var(--zx-muted-fg);
  line-height: 1.7;
  margin-bottom: 4px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field > span {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--zx-fg);
}

.tool-result {
  border-left: 1px solid var(--zx-border);
  padding-left: 26px;
  min-height: 420px;
}

.result-placeholder {
  height: 100%;
  min-height: 380px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #94a3b8;
  text-align: center;
  padding: 20px;
}

.placeholder-icon {
  font-size: 40px;
}

.result-placeholder p {
  font-size: 13px;
  max-width: 320px;
  line-height: 1.7;
}

.score-card {
  display: flex;
  align-items: center;
  gap: 22px;
  margin-bottom: 20px;
}

.score-ring {
  width: 104px;
  height: 104px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: conic-gradient(var(--zx-accent) var(--score), #e8efff 0);
  position: relative;
}

.score-ring::before {
  content: '';
  position: absolute;
  inset: 9px;
  border-radius: 50%;
  background: #fff;
}

.score-ring span {
  position: relative;
  font-size: 28px;
  font-weight: 800;
  color: var(--zx-accent);
  line-height: 1.1;
}

.score-ring em {
  position: relative;
  font-style: normal;
  font-size: 11px;
  color: var(--zx-muted-fg);
}

.summary {
  font-size: 13px;
  color: #334155;
  line-height: 1.75;
}

.dimension-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.dimension-head {
  display: flex;
  justify-content: space-between;
  font-size: 12.5px;
  color: var(--zx-muted-fg);
  margin-bottom: 4px;
}

.dimension-head strong {
  color: var(--zx-fg);
}

.dimension-bar {
  height: 6px;
  border-radius: 999px;
  background: var(--zx-muted);
  overflow: hidden;
}

.dimension-bar span {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--zx-accent), #7c9dff);
  transition: width 0.5s ease;
}

.issue-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.issue-item {
  display: grid;
  grid-template-columns: auto auto 1fr;
  align-items: start;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid var(--zx-border);
  border-radius: 10px;
  background: #fbfcff;
  font-size: 12.5px;
}

.severity {
  padding: 1px 7px;
  border-radius: 4px;
  font-size: 11px;
  background: #f1f5f9;
  color: var(--zx-muted-fg);
  white-space: nowrap;
}

.severity.high {
  background: #fef2f2;
  color: #b91c1c;
}

.severity.medium {
  background: #fffbeb;
  color: #b45309;
}

.severity.low {
  background: #eef3ff;
  color: var(--zx-accent);
}

.issue-line {
  color: #94a3b8;
  font-size: 11.5px;
  white-space: nowrap;
}

.issue-item p {
  color: #334155;
  line-height: 1.6;
}

@media (max-width: 960px) {
  .ai-grid {
    grid-template-columns: 1fr;
  }

  .session-panel {
    max-height: 220px;
  }

  .tool-grid {
    grid-template-columns: 1fr;
  }

  .tool-result {
    border-left: none;
    padding-left: 0;
    border-top: 1px solid var(--zx-border);
    padding-top: 20px;
  }

  .message-area {
    height: 360px;
  }
}

.path-result {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.path-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.path-head h3 {
  margin: 0;
  font-size: 15px;
}

.path-head p {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--zx-muted-fg);
}

.path-actions {
  display: flex;
  gap: 6px;
}

.path-gap {
  padding: 8px 10px;
  border-radius: 8px;
  background: #fffbeb;
  color: #b45309;
  font-size: 12px;
}

.path-stage {
  padding: 12px 14px;
  border: 1px solid var(--zx-border);
  border-radius: 10px;
  background: #fff;
}

.path-stage-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.path-stage-head strong {
  font-size: 13px;
}

.path-stage-tools {
  display: flex;
  gap: 2px;
}

.path-courses {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 8px 0;
}

.path-course {
  padding: 3px 8px;
  border-radius: 6px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 11.5px;
}

.path-course.muted {
  background: #f1f5f9;
  color: var(--zx-muted-fg);
}

.path-meta {
  margin: 4px 0;
  font-size: 12px;
  color: var(--zx-muted-fg);
}

.path-reason {
  margin: 4px 0 0;
  font-size: 12px;
  color: #475569;
}

.path-inputs {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 11.5px;
  color: var(--zx-muted-fg);
}

.path-history {
  margin-top: 16px;
  border-top: 1px solid var(--zx-border);
  padding-top: 10px;
}

.path-history h4 {
  margin: 0 0 6px;
  font-size: 12px;
  color: var(--zx-muted-fg);
}

.path-history-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding: 6px 0;
  font-size: 12px;
  cursor: pointer;
  border-bottom: 1px dashed var(--zx-border);
}

.path-history-row em {
  font-style: normal;
  color: var(--zx-muted-fg);
}
</style>