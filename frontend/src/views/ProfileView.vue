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
