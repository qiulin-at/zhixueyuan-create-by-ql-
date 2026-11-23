<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowRight, DataAnalysis, Reading, Timer, TrendCharts } from '@element-plus/icons-vue'
import * as echarts from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { aiApi, userApi } from '../api'

// 按需引入：只打包柱状图 + 网格 + 提示框，避免整包 echarts（约 1MB）
echarts.use([BarChart, GridComponent, TooltipComponent, CanvasRenderer])

const router = useRouter()

const learning = ref({ items: [], total: 0, total_minutes: 0, avg_progress: 0 })
const loading = ref(true)
const chartRef = ref(null)
let chartInstance = null

const period = ref('week')
const reportContent = ref('')
const reportMode = ref('mock')
const generating = ref(false)

const renderMarkdown = (text) => DOMPurify.sanitize(marked.parse(text || ''))

const hours = computed(() => (learning.value.total_minutes / 60).toFixed(1))

const truncate = (text, length) => (text.length > length ? `${text.slice(0, length)}…` : text)

const renderChart = () => {
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  const items = learning.value.items || []
  chartInstance.setOption(
    {
      grid: { left: 6, right: 40, top: 16, bottom: 6, containLabel: true },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params) => `${params[0].name}<br/>进度：${params[0].value}%`,
      },
      xAxis: {
        type: 'value',
        max: 100,
        axisLabel: { formatter: '{value}%', color: '#94a3b8', fontSize: 11 },
        splitLine: { lineStyle: { color: '#f1f5f9' } },
      },
      yAxis: {
        type: 'category',
        data: items.map((item) => truncate(item.title, 12)),
        axisLabel: { color: '#334155', fontSize: 11 },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [
        {
          type: 'bar',
          data: items.map((item) => item.progress),
          barWidth: 13,
          itemStyle: {
            borderRadius: [0, 7, 7, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: '#0052ff' },
              { offset: 1, color: '#7c9dff' },
            ]),
          },
          label: { show: true, position: 'right', formatter: '{c}%', color: '#0052ff', fontSize: 11, fontWeight: 600 },
        },
      ],
    },
    true,
  )
  chartInstance.resize()
}

const loadLearning = async () => {
  loading.value = true
  try {
    learning.value = await userApi.learning()
    await nextTick()
    renderChart()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

const generateReport = async () => {
  generating.value = true
  try {
    const data = await aiApi.report({ period: period.value })
    reportContent.value = data.content
    reportMode.value = data.mode
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    generating.value = false
  }
}

const continueLearning = (courseId) => {
  router.push(`/courses/${courseId}`)
}

const handleResize = () => {
  if (chartInstance) chartInstance.resize()
}

onMounted(() => {
  loadLearning()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<template>
  <div class="report-page">
    <div class="zx-container">
      <div class="page-head">
        <div>
          <span class="eyebrow">LEARNING ANALYTICS</span>
          <h1>学习报告</h1>
          <p>汇总你的学习时长、课程进度与 AI 生成的薄弱点分析。</p>
        </div>
        <div class="head-actions">
          <el-radio-group v-model="period" size="default">
            <el-radio-button label="week">本周</el-radio-button>
            <el-radio-button label="month">本月</el-radio-button>
          </el-radio-group>
          <el-button type="primary" class="zx-gradient-button" :loading="generating" @click="generateReport">
            生成 AI 报告
          </el-button>
        </div>
      </div>

      <div class="stat-grid">
        <div class="stat-card zx-card">
          <div class="stat-icon blue"><el-icon><Reading /></el-icon></div>
          <div>
            <span class="stat-label">在学课程</span>
            <strong>{{ learning.total }} <em>门</em></strong>
          </div>
        </div>
        <div class="stat-card zx-card">
          <div class="stat-icon green"><el-icon><Timer /></el-icon></div>
          <div>
            <span class="stat-label">累计学习时长</span>
            <strong>{{ hours }} <em>小时</em></strong>
          </div>
        </div>
        <div class="stat-card zx-card">
          <div class="stat-icon purple"><el-icon><TrendCharts /></el-icon></div>
          <div>
            <span class="stat-label">平均完成进度</span>
            <strong>{{ learning.avg_progress }} <em>%</em></strong>
          </div>
        </div>
        <div class="stat-card zx-card">
          <div class="stat-icon orange"><el-icon><DataAnalysis /></el-icon></div>
          <div>
            <span class="stat-label">学习记录</span>
            <strong>{{ learning.items.length }} <em>条</em></strong>
          </div>
        </div>
      </div>

      <div class="report-grid">
        <section class="panel zx-card">
          <div class="panel-head">
            <h2>我的课程</h2>
            <span class="panel-sub">按最近学习时间排序</span>
          </div>
          <div v-loading="loading" class="course-progress-list">
            <div v-for="item in learning.items" :key="item.course_id" class="progress-item">
              <div class="progress-top">
                <div class="progress-title">
                  <strong>{{ item.title }}</strong>
                  <span>{{ item.tech_system }} · 累计 {{ item.study_minutes }} 分钟</span>
                </div>
                <span class="progress-value">{{ item.progress }}%</span>
              </div>
              <el-progress :percentage="item.progress" :stroke-width="7" :show-text="false" />
              <div class="progress-foot">
                <span class="update-time">更新于 {{ item.updated_at ? item.updated_at.slice(0, 10) : '—' }}</span>
                <el-button text type="primary" size="small" @click="continueLearning(item.course_id)">
                  继续学习
                  <el-icon><ArrowRight /></el-icon>
                </el-button>
              </div>
            </div>
            <div v-if="!learning.items.length" class="zx-empty">
              <el-icon class="zx-empty-icon"><Reading /></el-icon>
              <span>还没有学习记录，先去选一门感兴趣的课程吧</span>
              <el-button type="primary" class="zx-gradient-button" @click="router.push('/')">去选课</el-button>
            </div>
          </div>
        </section>

        <section class="panel zx-card">
          <div class="panel-head">
            <h2>进度对比</h2>
            <span class="panel-sub">各课程完成度</span>
          </div>
          <div ref="chartRef" class="chart"></div>
          <div class="chart-tip">提示：进度由「标记完成」的章节数自动计算</div>
        </section>
      </div>

      <section v-if="reportContent" class="report-card zx-card">
        <div class="panel-head">
          <h2>AI 学习报告</h2>
          <span class="mode-tag" :class="reportMode">{{ reportMode === 'online' ? '在线模型生成' : 'Mock 引擎生成' }}</span>
        </div>
        <div class="markdown-body" v-html="renderMarkdown(reportContent)"></div>
      </section>

      <section v-else class="report-empty zx-card">
        <div class="report-empty-inner">
          <div class="report-empty-icon">📊</div>
          <div>
            <h3>生成一份属于你的学习报告</h3>
            <p>AI 会结合学习时长、课程进度与薄弱点，输出本周概览、学习亮点与下周建议。</p>
          </div>
          <el-button type="primary" class="zx-gradient-button" :loading="generating" @click="generateReport">
            立即生成
          </el-button>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.report-page {
  padding-top: 30px;
}

.page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.eyebrow {
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 11px;
  letter-spacing: 0.2em;
  color: var(--zx-accent);
  font-weight: 600;
}

.page-head h1 {
  margin-top: 8px;
  font-size: 30px;
  letter-spacing: -0.02em;
}

.page-head p {
  margin-top: 6px;
  font-size: 14px;
  color: var(--zx-muted-fg);
}

.head-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 18px;
}

.stat-card {
  padding: 18px;
  display: flex;
  align-items: center;
  gap: 14px;
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-size: 20px;
  flex-shrink: 0;
}

.stat-icon.blue {
  background: #e8efff;
  color: var(--zx-accent);
}

.stat-icon.green {
  background: #ecfdf5;
  color: #047857;
}

.stat-icon.purple {
  background: #f5f3ff;
  color: #6d28d9;
}

.stat-icon.orange {
  background: #fffbeb;
  color: #b45309;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: var(--zx-muted-fg);
}

.stat-card strong {
  font-size: 22px;
  color: var(--zx-fg);
  line-height: 1.3;
}

.stat-card em {
  font-style: normal;
  font-size: 12px;
  color: var(--zx-muted-fg);
  font-weight: 400;
}

.report-grid {
  display: grid;
  grid-template-columns: 1.35fr 1fr;
  gap: 18px;
}

.panel {
  padding: 20px 22px;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.panel-head h2 {
  font-size: 17px;
}

.panel-sub {
  font-size: 12px;
  color: #94a3b8;
}

.course-progress-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-height: 200px;
}

.progress-item {
  padding-bottom: 16px;
  border-bottom: 1px dashed var(--zx-border);
}

.progress-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.progress-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.progress-title {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.progress-title strong {
  font-size: 14px;
  color: var(--zx-fg);
}

.progress-title span {
  font-size: 11.5px;
  color: var(--zx-muted-fg);
}

.progress-value {
  font-size: 16px;
  font-weight: 800;
  color: var(--zx-accent);
}

.progress-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 4px;
}

.update-time {
  font-size: 11px;
  color: #94a3b8;
}

.chart {
  width: 100%;
  height: 280px;
}

.chart-tip {
  margin-top: 8px;
  font-size: 11px;
  color: #94a3b8;
  text-align: center;
}

.report-card {
  margin-top: 18px;
  padding: 22px 26px 26px;
}

.mode-tag {
  font-size: 11px;
  padding: 2px 9px;
  border-radius: 999px;
  background: #fffbeb;
  color: #b45309;
  border: 1px solid #fde68a;
}

.mode-tag.online {
  background: #ecfdf5;
  color: #047857;
  border-color: #a7f3d0;
}

.report-empty {
  margin-top: 18px;
  padding: 30px 26px;
}

.report-empty-inner {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.report-empty-icon {
  font-size: 40px;
}

.report-empty-inner h3 {
  font-size: 16px;
}

.report-empty-inner p {
  margin-top: 4px;
  font-size: 12.5px;
  color: var(--zx-muted-fg);
  line-height: 1.7;
}

.report-empty-inner .el-button {
  margin-left: auto;
}

@media (max-width: 1000px) {
  .stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .report-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .stat-grid {
    grid-template-columns: 1fr;
  }

  .report-empty-inner .el-button {
    margin-left: 0;
  }
}
</style>