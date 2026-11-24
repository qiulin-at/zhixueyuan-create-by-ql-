<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { userApi } from '../api'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const tab = ref('profile')
const saving = ref(false)
const form = reactive({ nickname: '', major: '', avatar: '', password: '' })

const favorites = reactive({ items: [], total: 0, loading: false, loaded: false })
const learning = reactive({ items: [], totalMinutes: 0, avgProgress: 0, loading: false, loaded: false })
const orders = reactive({ items: [], totalAmount: 0, loading: false, loaded: false })

const orderStatusLabel = { pending: '待支付', paid: '已支付', refunded: '已退款', cancelled: '已取消' }
const orderStatusTag = { pending: 'warning', paid: 'success', refunded: 'info', cancelled: 'info' }

const llm = reactive({
  loading: false,
  saving: false,
  testing: false,
  configured: false,
  enabled: true,
  provider: 'deepseek',
  base_url: 'https://api.deepseek.com/v1',
  model: 'deepseek-chat',
  api_key: '',
  masked_key: '',
  last_tested_at: null,
  last_test_ok: null,
})
const llmProviders = [
  { value: 'deepseek', label: 'DeepSeek', base_url: 'https://api.deepseek.com/v1', model: 'deepseek-chat' },
  {
    value: 'dashscope',
    label: '通义千问（DashScope）',
    base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    model: 'qwen-plus',
  },
  { value: 'zhipu', label: '智谱 GLM', base_url: 'https://open.bigmodel.cn/api/paas/v4', model: 'glm-4-flash' },
  { value: 'moonshot', label: 'Moonshot Kimi', base_url: 'https://api.moonshot.cn/v1', model: 'moonshot-v1-8k' },
  { value: 'openai', label: 'OpenAI', base_url: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
  { value: 'custom', label: '自定义（OpenAI 兼容）', base_url: '', model: '' },
]

const avatarText = computed(() => (userStore.displayName || '同').slice(0, 1))
const formatDate = (value) => (value ? value.slice(0, 10) : '—')
const formatMoney = (value) => `¥ ${Number(value || 0).toFixed(2)}`
const coverStyle = (item) =>
  item.cover
    ? { backgroundImage: `url(${item.cover})` }
    : { backgroundImage: 'linear-gradient(135deg, #0052ff 0%, #4d7cff 55%, #80a3ff 100%)' }

const syncForm = () => {
  const user = userStore.user || {}
  form.nickname = user.nickname || ''
  form.major = user.major || ''
  form.avatar = user.avatar || ''
  form.password = ''
}

const saveProfile = async () => {
  if (form.password && form.password.length < 6) {
    ElMessage.warning('新密码至少 6 位')
    return
  }
  saving.value = true
  try {
    const payload = { nickname: form.nickname, major: form.major, avatar: form.avatar }
    if (form.password) payload.password = form.password
    await userApi.update(payload)
    await userStore.fetchMe()
    form.password = ''
    ElMessage.success('资料已更新')
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    saving.value = false
  }
}

const loadFavorites = async () => {
  if (favorites.loading || favorites.loaded) return
  favorites.loading = true
  try {
    const data = await userApi.favorites()
    favorites.items = data.items
    favorites.total = data.total
    favorites.loaded = true
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    favorites.loading = false
  }
}

const loadLearning = async () => {
  if (learning.loading || learning.loaded) return
  learning.loading = true
  try {
    const data = await userApi.learning()
    learning.items = data.items
    learning.totalMinutes = data.total_minutes
    learning.avgProgress = data.avg_progress
    learning.loaded = true
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    learning.loading = false
  }
}

const loadOrders = async () => {
  if (orders.loading || orders.loaded) return
  orders.loading = true
  try {
    const data = await userApi.orders()
    orders.items = data.items
    orders.totalAmount = data.total_amount
    orders.loaded = true
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    orders.loading = false
  }
}

const onTabChange = (name) => {
  if (name === 'favorites') loadFavorites()
  if (name === 'learning') loadLearning()
  if (name === 'orders') loadOrders()
  if (name === 'llm') loadLLM()
}

const loadLLM = async () => {
  if (llm.loading) return
  llm.loading = true
  try {
    const data = await userApi.llmConfig()
    Object.assign(llm, {
      configured: data.configured,
      enabled: data.enabled,
      provider: data.provider || 'deepseek',
      base_url: data.base_url || 'https://api.deepseek.com/v1',
      model: data.model || 'deepseek-chat',
      masked_key: data.masked_key || '',
      last_tested_at: data.last_tested_at,
      last_test_ok: data.last_test_ok,
      api_key: '',
    })
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    llm.loading = false
  }
}

const onProviderChange = (value) => {
  const preset = llmProviders.find((item) => item.value === value)
  if (preset && preset.base_url) {
    llm.base_url = preset.base_url
    llm.model = preset.model
  }
}

const saveLLM = async () => {
  if (!llm.configured && !llm.api_key.trim()) {
    ElMessage.warning('首次配置请填写 API Key')
    return
  }
  llm.saving = true
  try {
    const data = await userApi.saveLLMConfig({
      provider: llm.provider,
      base_url: llm.base_url,
      model: llm.model,
      api_key: llm.api_key,
      enabled: llm.enabled,
    })
    Object.assign(llm, { ...data, api_key: '' })
    ElMessage.success('模型配置已保存')
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    llm.saving = false
  }
}

const testLLM = async () => {
  llm.testing = true
  try {
    await userApi.testLLMConfig()
    llm.last_test_ok = true
    llm.last_tested_at = new Date().toISOString()
    ElMessage.success('连接成功')
  } catch (error) {
    llm.last_test_ok = false
    llm.last_tested_at = new Date().toISOString()
    ElMessage.error(error.message)
  } finally {
    llm.testing = false
  }
}

const clearLLM = async () => {
  try {
    await userApi.deleteLLMConfig()
    Object.assign(llm, {
      configured: false,
      enabled: false,
      masked_key: '',
      api_key: '',
      last_tested_at: null,
      last_test_ok: null,
    })
    ElMessage.success('模型配置已清除')
  } catch (error) {
    ElMessage.error(error.message)
  }
}

onMounted(async () => {
  if (!userStore.user) {
    await userStore.fetchMe().catch(() => {})
  }
  syncForm()
})
</script>

<template>
  <div class="profile-page">
    <div class="zx-container">
      <header class="page-head">
        <div>
          <span class="eyebrow">MY ACCOUNT</span>
          <h1>个人中心</h1>
          <p>管理你的资料、收藏、学习进度与订单</p>
        </div>
        <div class="identity">
          <div class="avatar">{{ avatarText }}</div>
          <div class="identity-text">
            <strong>{{ userStore.displayName }}</strong>
            <span class="role">{{ userStore.roleLabel }}</span>
          </div>
        </div>
      </header>

      <el-tabs v-model="tab" class="profile-tabs" @tab-change="onTabChange">
        <el-tab-pane label="资料设置" name="profile">
          <div class="panel">
            <el-form label-width="88px" class="profile-form">
              <el-form-item label="昵称">
                <el-input v-model="form.nickname" maxlength="50" placeholder="怎么称呼你" />
              </el-form-item>
              <el-form-item label="专业">
                <el-input v-model="form.major" maxlength="100" placeholder="例如：计算机科学与技术" />
              </el-form-item>
              <el-form-item label="头像地址">
                <el-input v-model="form.avatar" maxlength="255" placeholder="https://…（留空则显示首字）" />
              </el-form-item>
              <el-form-item label="新密码">
                <el-input
                  v-model="form.password"
                  type="password"
                  show-password
                  maxlength="64"
                  placeholder="留空表示不修改"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" class="zx-gradient-button" :loading="saving" @click="saveProfile">
                  保存修改
                </el-button>
              </el-form-item>
            </el-form>
            <p class="tips">用户名与邮箱不可修改；如需变更请联系管理员。</p>
          </div>
        </el-tab-pane>

        <el-tab-pane label="我的收藏" name="favorites">
          <div v-loading="favorites.loading" class="panel panel-list">
            <div v-if="favorites.items.length" class="fav-grid">
              <article
                v-for="item in favorites.items"
                :key="item.id"
                class="fav-card"
                @click="router.push(`/courses/${item.id}`)"
              >
                <div class="fav-cover" :style="coverStyle(item)"></div>
                <div class="fav-body">
                  <span class="fav-tag">{{ item.tech_system }}</span>
                  <strong class="fav-title">{{ item.title }}</strong>
                  <div class="fav-meta">
                    <span>★ {{ item.rating }}</span>
                    <span>{{ item.study_count }} 人在学</span>
                  </div>
                </div>
              </article>
            </div>
            <el-empty v-else-if="favorites.loaded" description="还没有收藏课程" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="我的课程" name="learning">
          <div v-loading="learning.loading" class="panel panel-list">
            <div v-if="learning.items.length" class="summary">
              <span>在学 {{ learning.items.length }} 门</span>
              <span>累计 {{ learning.totalMinutes }} 分钟</span>
              <span>平均进度 {{ learning.avgProgress }}%</span>
            </div>
            <div v-if="learning.items.length" class="learn-list">
              <button
                v-for="item in learning.items"
                :key="item.course_id"
                type="button"
                class="learn-row"
                @click="router.push(`/courses/${item.course_id}`)"
              >
                <div class="learn-main">
                  <strong>{{ item.title }}</strong>
                  <span class="learn-meta">{{ item.tech_system }} · 更新于 {{ formatDate(item.updated_at) }}</span>
                </div>
                <el-progress
                  class="learn-progress"
                  :percentage="item.progress"
                  :stroke-width="6"
                  :show-text="false"
                />
                <span class="learn-percent">{{ item.progress }}%</span>
              </button>
            </div>
            <el-empty v-else-if="learning.loaded" description="还没有学习记录" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="我的订单" name="orders">
          <div v-loading="orders.loading" class="panel panel-list">
            <div v-if="orders.items.length" class="summary">
              <span>共 {{ orders.items.length }} 笔</span>
              <span>合计 {{ formatMoney(orders.totalAmount) }}</span>
            </div>
            <el-table v-if="orders.items.length" :data="orders.items" row-key="id">
              <el-table-column prop="order_no" label="订单号" min-width="170" />
              <el-table-column prop="title" label="课程" min-width="220" show-overflow-tooltip />
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
              <el-table-column label="下单时间" width="120">
                <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
              </el-table-column>
            </el-table>
            <el-empty v-else-if="orders.loaded" description="还没有订单" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="AI 模型" name="llm">
          <div v-loading="llm.loading" class="panel llm-panel">
            <div class="llm-head">
              <div>
                <h2>AI 模型接入</h2>
                <p>接入你自己订阅的 OpenAI 兼容模型；Key 加密存储，只用于你的 AI 请求。</p>
              </div>
              <el-switch v-model="llm.enabled" active-text="启用" inactive-text="停用" />
            </div>

            <el-alert
              type="warning"
              :closable="false"
              show-icon
              title="调用失败会自动回退平台模型，再回退 Mock；页面会提示实际使用的来源。"
            />

            <el-form label-position="top" class="llm-form">
              <el-form-item label="厂商">
                <el-select v-model="llm.provider" style="width: 100%" @change="onProviderChange">
                  <el-option
                    v-for="item in llmProviders"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="Base URL">
                <el-input v-model="llm.base_url" placeholder="https://api.example.com/v1" maxlength="255" />
              </el-form-item>
              <el-form-item label="模型名称">
                <el-input v-model="llm.model" placeholder="deepseek-chat" maxlength="80" />
              </el-form-item>
              <el-form-item label="API Key">
                <el-input
                  v-model="llm.api_key"
                  type="password"
                  show-password
                  maxlength="500"
                  :placeholder="
                    llm.configured
                      ? `已保存：${llm.masked_key}（留空保持不变）`
                      : '粘贴你的 API Key'
                  "
                />
              </el-form-item>
              <div class="llm-actions">
                <el-button type="primary" class="zx-gradient-button" :loading="llm.saving" @click="saveLLM">
                  保存配置
                </el-button>
                <el-button :loading="llm.testing" :disabled="!llm.configured" @click="testLLM">
                  测试连接
                </el-button>
                <el-button type="danger" plain :disabled="!llm.configured" @click="clearLLM">
                  清除
                </el-button>
              </div>
              <p v-if="llm.last_tested_at" class="llm-status">
                最近测试：{{ formatDate(llm.last_tested_at) }} ·
                <span :class="llm.last_test_ok ? 'ok' : 'fail'">
                  {{ llm.last_test_ok ? '连接成功' : '连接失败' }}
                </span>
              </p>
              <p class="llm-note">
                Key 不会回显，前端只看到掩码；Base URL 仅允许 https 公网域名，禁止内网地址。
              </p>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  padding: 30px 0 72px;
}

.page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 18px;
}

.eyebrow {
  display: inline-block;
  margin-bottom: 8px;
  font-size: 11px;
  letter-spacing: 0.16em;
  color: var(--zx-muted-fg);
}

.page-head h1 {
  margin: 0;
  font-size: 30px;
  letter-spacing: -0.02em;
}

.page-head p {
  margin: 8px 0 0;
  font-size: 13.5px;
  color: var(--zx-muted-fg);
}

.identity {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: var(--zx-card);
  border: 1px solid var(--zx-border);
  border-radius: 999px;
  box-shadow: var(--zx-shadow-sm);
}

.avatar {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: linear-gradient(135deg, #0052ff, #4d7cff);
  color: #fff;
  font-weight: 600;
}

.identity-text {
  display: flex;
  flex-direction: column;
  line-height: 1.35;
}

.identity-text strong {
  font-size: 13px;
}

.role {
  font-size: 11px;
  color: var(--zx-muted-fg);
}

.profile-tabs {
  padding: 6px 20px 20px;
  background: var(--zx-card);
  border: 1px solid var(--zx-border);
  border-radius: var(--zx-radius);
  box-shadow: var(--zx-shadow-md);
}

.panel {
  padding: 10px 2px 4px;
}

.panel-list {
  min-height: 180px;
}

.profile-form {
  max-width: 520px;
  padding-top: 6px;
}

.tips {
  margin: 6px 0 0 88px;
  font-size: 12px;
  color: #94a3b8;
}

.llm-panel {
  padding: 10px 2px 4px;
}

.llm-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

.llm-head h2 {
  margin: 0;
  font-size: 16px;
}

.llm-head p {
  margin: 4px 0 0;
  font-size: 12.5px;
  color: var(--zx-muted-fg);
}

.llm-form {
  max-width: 560px;
  margin-top: 14px;
}

.llm-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}

.llm-status {
  margin-top: 10px;
  font-size: 12px;
  color: var(--zx-muted-fg);
}

.llm-status .ok {
  color: #059669;
}

.llm-status .fail {
  color: #dc2626;
}

.llm-note {
  margin-top: 6px;
  font-size: 11.5px;
  line-height: 1.7;
  color: #94a3b8;
}

.fav-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.fav-card {
  overflow: hidden;
  border: 1px solid var(--zx-border);
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.fav-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--zx-shadow-md);
}

.fav-cover {
  height: 96px;
  background-size: cover;
  background-position: center;
}

.fav-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 14px 14px;
}

.fav-tag {
  align-self: flex-start;
  padding: 1px 8px;
  font-size: 10.5px;
  color: var(--zx-accent);
  background: #eef3ff;
  border-radius: 999px;
}

.fav-title {
  font-size: 13.5px;
  line-height: 1.45;
}

.fav-meta {
  display: flex;
  gap: 12px;
  font-size: 11.5px;
  color: var(--zx-muted-fg);
}

.summary {
  display: flex;
  gap: 20px;
  padding: 10px 2px 14px;
  font-size: 12.5px;
  color: var(--zx-muted-fg);
}

.learn-row {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 10px;
  border: none;
  border-bottom: 1px solid var(--zx-border);
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.learn-row:last-child {
  border-bottom: none;
}

.learn-row:hover {
  background: var(--zx-muted);
}

.learn-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  flex: 1;
}

.learn-main strong {
  font-size: 13px;
}

.learn-meta {
  font-size: 11.5px;
  color: var(--zx-muted-fg);
}

.learn-progress {
  width: 180px;
  flex-shrink: 0;
}

.learn-percent {
  width: 40px;
  font-size: 12px;
  color: var(--zx-muted-fg);
  text-align: right;
}

@media (max-width: 760px) {
  .page-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .learn-progress {
    width: 90px;
  }
}
</style>
