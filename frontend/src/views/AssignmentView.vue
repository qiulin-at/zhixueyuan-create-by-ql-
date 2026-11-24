<template>
  <div class="assignment-page">
    <section class="zx-container page-head">
      <div>
        <el-button link @click="router.push(`/courses/${courseId}`)">← 返回课程</el-button>
        <h1>课程作业</h1>
        <p>提交后优先在隔离容器中执行测试；沙箱不可用时仅做静态分析，结果页会明确标注。</p>
      </div>
    </section>

    <section class="zx-container assignment-body">
      <aside class="assignment-list">
        <div
          v-for="item in assignments"
          :key="item.id"
          class="assignment-item"
          :class="{ active: selected && selected.id === item.id }"
          @click="selectAssignment(item)"
        >
          <div class="item-main">
            <strong>{{ item.title }}</strong>
            <span>
              {{ item.language }} ·
              {{ item.deadline ? `截止 ${formatTime(item.deadline)}` : '不限时' }}
            </span>
          </div>
          <el-tag :type="tagType(item.my_submission)" size="small" effect="light">
            {{ item.my_submission ? statusLabel[item.my_submission.status] : '未提交' }}
          </el-tag>
        </div>
        <div v-if="!assignments.length && !loading" class="empty">当前课程还没有作业</div>
      </aside>

      <div v-if="selected" class="assignment-detail zx-card">
        <div class="detail-head">
          <div>
            <h2>{{ selected.title }}</h2>
            <p>{{ selected.description || '暂无题目说明' }}</p>
          </div>
          <el-tag effect="plain">{{ selected.language }}</el-tag>
        </div>

        <div v-if="selected.sample_cases && selected.sample_cases.length" class="sample-box">
          <h3>公开样例</h3>
          <code v-for="(item, index) in selected.sample_cases" :key="index">
            solve({{ JSON.stringify(item.args) }}) → {{ JSON.stringify(item.expected) }}
          </code>
        </div>

        <div v-if="rubricDimensions.length" class="rubric-box">
          <h3>评分规则</h3>
          <span v-for="dimension in rubricDimensions" :key="dimension.key">
            {{ dimension.name }} {{ Math.round(dimension.weight * 100) }}%
          </span>
        </div>

        <el-input
          v-model="code"
          type="textarea"
          :rows="12"
          resize="none"
          placeholder="粘贴或编写代码，入口函数约定为 solve(...)"
        />
        <div class="submit-row">
          <el-button type="primary" class="zx-gradient-button" :loading="submitting" @click="submit">
            提交作业
          </el-button>
          <span class="hint">最终成绩以教师复核为准；未执行代码时客观分显示为空</span>
        </div>

        <div v-if="result" class="result-card">
          <div class="result-head">
            <el-tag :type="statusTag[result.status] || 'info'">
              {{ statusLabel[result.status] || result.status }}
            </el-tag>
            <span v-if="result.test_result && result.test_result.available === false" class="sandbox-warn">
              未执行代码：{{ result.test_result.reason || '沙箱不可用' }}
            </span>
          </div>

          <div class="score-grid">
            <div>
              <span>客观测试</span>
              <strong>{{ result.objective_score ?? '—' }}</strong>
            </div>
            <div>
              <span>AI 分析</span>
              <strong>{{ result.ai_score ?? '—' }}</strong>
            </div>
            <div>
              <span>教师复核</span>
              <strong>{{ result.final_score ?? '待复核' }}</strong>
            </div>
          </div>

          <p v-if="result.test_result && result.test_result.total" class="case-line">
            测试用例：{{ result.test_result.passed || 0 }} / {{ result.test_result.total }} 通过
          </p>

          <div v-if="result.ai_feedback && result.ai_feedback.summary" class="ai-box">
            <strong>AI 评语</strong>
            <p>{{ result.ai_feedback.summary }}</p>
            <ul v-if="result.ai_feedback.issues && result.ai_feedback.issues.length">
              <li v-for="(issue, index) in result.ai_feedback.issues" :key="index">
                {{ issue.suggestion }}
              </li>
            </ul>
          </div>

          <div v-if="result.review_comment" class="review-box">
            <strong>教师意见</strong>
            <p>{{ result.review_comment }}</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { assignmentApi } from '../api'

const route = useRoute()
const router = useRouter()
const courseId = Number(route.params.id)

const assignments = ref([])
const selected = ref(null)
const loading = ref(false)
const submitting = ref(false)
const code = ref('')
const result = ref(null)

const statusLabel = {
  passed: '测试通过',
  failed: '测试未通过',
  not_executed: '未执行代码',
  timeout: '执行超时',
  compile_error: '语法/编译错误',
  runtime_error: '运行异常',
}
const statusTag = {
  passed: 'success',
  failed: 'warning',
  not_executed: 'info',
  timeout: 'danger',
  compile_error: 'danger',
  runtime_error: 'danger',
}

const rubricDimensions = computed(() => selected.value?.rubric?.dimensions || [])

const tagType = (submission) => (submission ? statusTag[submission.status] || 'info' : 'info')

const formatTime = (value) =>
  value
    ? new Date(value).toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      })
    : '—'

const loadAssignments = async () => {
  loading.value = true
  try {
    const data = await assignmentApi.list(courseId)
    assignments.value = data.items
    if (!selected.value && data.items.length) {
      selectAssignment(data.items[0])
    }
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

const selectAssignment = async (item) => {
  selected.value = item
  code.value = ''
  result.value = null
  if (item.my_submission?.id) {
    try {
      result.value = await assignmentApi.submission(item.my_submission.id)
    } catch (error) {
      result.value = null
    }
  }
}

const submit = async () => {
  if (!code.value.trim()) {
    ElMessage.warning('请先填写代码')
    return
  }
  submitting.value = true
  try {
    result.value = await assignmentApi.submit(selected.value.id, { code: code.value })
    ElMessage.success('作业已提交')
    await loadAssignments()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    submitting.value = false
  }
}

onMounted(loadAssignments)
</script>

<style scoped>
.assignment-page {
  padding-top: 28px;
  padding-bottom: 40px;
}

.page-head {
  margin-bottom: 18px;
}

.page-head h1 {
  margin: 8px 0 6px;
  font-size: 28px;
}

.page-head p {
  margin: 0;
  color: var(--zx-muted-fg);
  font-size: 13px;
}

.assignment-body {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}

.assignment-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.assignment-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border: 1px solid var(--zx-border);
  border-radius: 10px;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.2s ease;
}

.assignment-item.active {
  border-color: var(--zx-accent);
  box-shadow: var(--zx-shadow-accent);
}

.item-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.item-main strong {
  font-size: 13.5px;
  color: var(--zx-fg);
}

.item-main span {
  font-size: 11.5px;
  color: var(--zx-muted-fg);
}

.empty {
  padding: 24px;
  text-align: center;
  color: var(--zx-muted-fg);
  font-size: 13px;
}

.assignment-detail {
  padding: 20px 22px;
}

.detail-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.detail-head h2 {
  margin: 0 0 6px;
  font-size: 19px;
}

.detail-head p {
  margin: 0;
  color: var(--zx-muted-fg);
  font-size: 13px;
}

.sample-box,
.rubric-box {
  margin: 16px 0;
}

.sample-box h3,
.rubric-box h3 {
  margin: 0 0 8px;
  font-size: 13px;
  color: var(--zx-fg);
}

.sample-box {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sample-box code {
  padding: 6px 10px;
  border-radius: 6px;
  background: #f1f5f9;
  color: #334155;
  font-size: 12px;
}

.rubric-box {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.rubric-box h3 {
  width: 100%;
}

.rubric-box span {
  padding: 3px 9px;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 11.5px;
}

.submit-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 14px;
}

.hint {
  font-size: 11.5px;
  color: var(--zx-muted-fg);
}

.result-card {
  margin-top: 20px;
  padding: 16px;
  border: 1px solid var(--zx-border);
  border-radius: 10px;
  background: #f8fafc;
}

.result-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.sandbox-warn {
  padding: 3px 9px;
  border-radius: 6px;
  background: #fffbeb;
  color: #b45309;
  font-size: 11.5px;
}

.score-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin: 14px 0;
}

.score-grid div {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid var(--zx-border);
}

.score-grid span {
  font-size: 11.5px;
  color: var(--zx-muted-fg);
}

.score-grid strong {
  font-size: 20px;
  color: var(--zx-fg);
}

.case-line {
  margin: 6px 0;
  font-size: 12.5px;
  color: #475569;
}

.ai-box,
.review-box {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid var(--zx-border);
}

.ai-box strong,
.review-box strong {
  font-size: 12.5px;
  color: var(--zx-fg);
}

.ai-box p,
.review-box p {
  margin: 6px 0;
  font-size: 12.5px;
  color: #475569;
}

.ai-box ul {
  margin: 6px 0 0;
  padding-left: 18px;
  font-size: 12px;
  color: #475569;
}

@media (max-width: 900px) {
  .assignment-body {
    grid-template-columns: 1fr;
  }
}
</style>