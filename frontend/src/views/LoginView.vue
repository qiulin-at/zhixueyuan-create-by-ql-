<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, Message, User } from '@element-plus/icons-vue'
import { authApi } from '../api'
import { useUserStore } from '../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const mode = ref('login')
const loading = ref(false)
const sending = ref(false)
const demoCode = ref('')

const loginForm = reactive({ account: '', password: '' })
const registerForm = reactive({ username: '', email: '', password: '', nickname: '' })
const resetForm = reactive({ email: '', code: '', newPassword: '' })

const gotoAfterAuth = () => {
  const redirect = route.query.redirect
  router.push(typeof redirect === 'string' && redirect ? redirect : '/')
}

const fillDemo = () => {
  loginForm.account = 'student'
  loginForm.password = '123456'
  mode.value = 'login'
}

const submitLogin = async () => {
  if (!loginForm.account || !loginForm.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  loading.value = true
  try {
    await userStore.login({ account: loginForm.account.trim(), password: loginForm.password })
    ElMessage.success('登录成功，欢迎回来')
    gotoAfterAuth()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

const submitRegister = async () => {
  if (!registerForm.username || !registerForm.email || !registerForm.password) {
    ElMessage.warning('请完整填写用户名、邮箱和密码')
    return
  }
  if (registerForm.password.length < 6) {
    ElMessage.warning('密码至少 6 位')
    return
  }
  loading.value = true
  try {
    await userStore.register({ ...registerForm, username: registerForm.username.trim() })
    ElMessage.success('注册成功，已为你自动登录')
    gotoAfterAuth()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

const sendCode = async () => {
  if (!resetForm.email) {
    ElMessage.warning('请先填写注册邮箱')
    return
  }
  sending.value = true
  try {
    const data = await authApi.sendCode(resetForm.email.trim())
    demoCode.value = data.demo_code
    ElMessage.success('验证码已生成，演示环境直接显示在下方')
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    sending.value = false
  }
}

const submitReset = async () => {
  if (!resetForm.email || !resetForm.code || !resetForm.newPassword) {
    ElMessage.warning('请填写邮箱、验证码和新密码')
    return
  }
  loading.value = true
  try {
    await authApi.resetPassword({
      email: resetForm.email.trim(),
      code: resetForm.code.trim(),
      new_password: resetForm.newPassword,
    })
    ElMessage.success('密码已重置，请使用新密码登录')
    loginForm.account = resetForm.email.trim()
    loginForm.password = ''
    mode.value = 'login'
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

const features = [
  { title: '智能答疑', desc: '绑定课程上下文，多轮追问不丢失记忆' },
  { title: '学习路径', desc: '按目标与每周投入时间生成阶段计划' },
  { title: 'AI 批改', desc: '代码作业自动评分，给出逐条修改建议' },
  { title: '学习报告', desc: '周/月学习数据自动汇总，定位薄弱点' },
]
</script>

<template>
  <div class="auth-page">
    <section class="auth-brand">
      <div class="brand-glow glow-one"></div>
      <div class="brand-glow glow-two"></div>
      <div class="brand-top">
        <div class="logo-mark">智</div>
        <span class="brand-name">智学云</span>
        <span class="brand-pill">AI EDU</span>
      </div>

      <div class="brand-copy">
        <h1>让每一次学习<br /><span class="grad">都有 AI 同行</span></h1>
        <p>面向教育平台的智能体 —— 选课、学习、答疑、就业，一条链路完成。</p>
        <ul class="feature-list">
          <li v-for="item in features" :key="item.title">
            <el-icon class="check-icon"><CircleCheckFilled /></el-icon>
            <div>
              <strong>{{ item.title }}</strong>
              <span>{{ item.desc }}</span>
            </div>
          </li>
        </ul>
      </div>

      <div class="brand-foot">
        <span>华为 ICT 学院 · 基于 Python 的 AI 项目实践</span>
        <button type="button" class="demo-entry" @click="fillDemo">使用演示账号 student / 123456</button>
      </div>
    </section>

    <section class="auth-panel">
      <div class="panel-card">
        <div class="panel-head">
          <h2>{{ mode === 'login' ? '欢迎回来' : mode === 'register' ? '创建账号' : '找回密码' }}</h2>
          <p>登录后即可收藏课程、记录进度并使用 AI 学习助手</p>
        </div>

        <div class="mode-switch">
          <button type="button" :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
          <button type="button" :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</button>
          <button type="button" :class="{ active: mode === 'reset' }" @click="mode = 'reset'">找回密码</button>
        </div>

        <div v-if="mode === 'login'" class="form">
          <label class="field">
            <span>账号</span>
            <el-input v-model="loginForm.account" size="large" placeholder="用户名或邮箱" :prefix-icon="User" @keyup.enter="submitLogin" />
          </label>
          <label class="field">
            <span>密码</span>
            <el-input
              v-model="loginForm.password"
              size="large"
              type="password"
              show-password
              placeholder="请输入密码"
              :prefix-icon="Lock"
              @keyup.enter="submitLogin"
            />
          </label>
          <el-button class="submit zx-gradient-button" type="primary" size="large" :loading="loading" @click="submitLogin">
            登录
          </el-button>
          <div class="helper">
            <span>没有账号？<a @click="mode = 'register'">立即注册</a></span>
            <a @click="mode = 'reset'">忘记密码</a>
          </div>
        </div>

        <div v-else-if="mode === 'register'" class="form">
          <label class="field">
            <span>用户名</span>
            <el-input v-model="registerForm.username" size="large" placeholder="字母、数字或下划线，3-30 位" :prefix-icon="User" />
          </label>
          <label class="field">
            <span>邮箱</span>
            <el-input v-model="registerForm.email" size="large" placeholder="用于找回密码" :prefix-icon="Message" />
          </label>
          <label class="field">
            <span>密码</span>
            <el-input v-model="registerForm.password" size="large" type="password" show-password placeholder="至少 6 位" :prefix-icon="Lock" />
          </label>
          <label class="field">
            <span>昵称（可选）</span>
            <el-input v-model="registerForm.nickname" size="large" placeholder="例如：陈同学" />
          </label>
          <el-button class="submit zx-gradient-button" type="primary" size="large" :loading="loading" @click="submitRegister">
            注册并登录
          </el-button>
          <div class="helper">
            <span>已有账号？<a @click="mode = 'login'">去登录</a></span>
          </div>
        </div>

        <div v-else class="form">
          <label class="field">
            <span>注册邮箱</span>
            <el-input v-model="resetForm.email" size="large" placeholder="请输入注册时使用的邮箱" :prefix-icon="Message" />
          </label>
          <label class="field">
            <span>验证码</span>
            <div class="code-row">
              <el-input v-model="resetForm.code" size="large" placeholder="6 位验证码" />
              <el-button size="large" :loading="sending" @click="sendCode">获取验证码</el-button>
            </div>
          </label>
          <div v-if="demoCode" class="demo-code">演示验证码：<strong>{{ demoCode }}</strong></div>
          <label class="field">
            <span>新密码</span>
            <el-input v-model="resetForm.newPassword" size="large" type="password" show-password placeholder="至少 6 位" :prefix-icon="Lock" />
          </label>
          <el-button class="submit zx-gradient-button" type="primary" size="large" :loading="loading" @click="submitReset">
            重置密码
          </el-button>
          <div class="helper">
            <span>想起密码了？<a @click="mode = 'login'">返回登录</a></span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>


<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  background: var(--zx-bg);
}

.auth-brand {
  position: relative;
  overflow: hidden;
  background: #0b1220;
  color: #e2e8f0;
  padding: 52px 64px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.auth-brand::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, #fff 1px, transparent 1px);
  background-size: 34px 34px;
  opacity: 0.035;
}

.brand-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  pointer-events: none;
}

.glow-one {
  width: 420px;
  height: 420px;
  background: rgba(0, 82, 255, 0.4);
  top: -120px;
  right: -80px;
}

.glow-two {
  width: 320px;
  height: 320px;
  background: rgba(124, 157, 255, 0.22);
  bottom: -100px;
  left: -60px;
}

.brand-top {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
}

.logo-mark {
  width: 44px;
  height: 44px;
  border-radius: 13px;
  display: grid;
  place-items: center;
  font-size: 21px;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(135deg, var(--zx-accent), #7c9dff);
  box-shadow: var(--zx-shadow-accent);
}

.brand-name {
  font-size: 19px;
  font-weight: 800;
  color: #fff;
  letter-spacing: -0.02em;
}

.brand-pill {
  padding: 2px 9px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: #bfdbfe;
  border: 1px solid rgba(124, 157, 255, 0.4);
  border-radius: 999px;
}

.brand-copy {
  position: relative;
  max-width: 460px;
}

.brand-copy h1 {
  font-size: 44px;
  line-height: 1.15;
  letter-spacing: -0.03em;
  color: #f8fafc;
}

.brand-copy .grad {
  background: linear-gradient(120deg, #7c9dff, #bfdbfe);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.brand-copy > p {
  margin-top: 18px;
  font-size: 15px;
  line-height: 1.7;
  color: #94a3b8;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 34px 0 0;
  display: grid;
  gap: 16px;
}

.feature-list li {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.check-icon {
  color: #4d7cff;
  font-size: 18px;
  margin-top: 2px;
}

.feature-list strong {
  display: block;
  font-size: 14px;
  color: #e2e8f0;
}

.feature-list span {
  font-size: 13px;
  color: #7c8ca3;
}

.brand-foot {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 12px;
  font-size: 12px;
  color: #64748b;
}

.demo-entry {
  align-self: flex-start;
  border: 1px dashed rgba(148, 163, 184, 0.4);
  background: rgba(255, 255, 255, 0.03);
  color: #cbd5e1;
  font-size: 12px;
  padding: 7px 14px;
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.2s ease, color 0.2s ease;
}

.demo-entry:hover {
  border-color: #7c9dff;
  color: #fff;
}

.auth-panel {
  display: grid;
  place-items: center;
  padding: 40px 24px;
}

.panel-card {
  width: 100%;
  max-width: 420px;
}

.panel-head h2 {
  font-size: 28px;
  letter-spacing: -0.02em;
}

.panel-head p {
  margin-top: 6px;
  color: var(--zx-muted-fg);
  font-size: 13px;
}

.mode-switch {
  display: inline-flex;
  gap: 4px;
  padding: 4px;
  margin: 26px 0 22px;
  border-radius: 10px;
  background: var(--zx-muted);
  border: 1px solid var(--zx-border);
}

.mode-switch button {
  border: none;
  background: transparent;
  padding: 7px 18px;
  font-size: 13px;
  font-weight: 500;
  color: var(--zx-muted-fg);
  border-radius: 7px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mode-switch button.active {
  background: #fff;
  color: var(--zx-accent);
  font-weight: 600;
  box-shadow: var(--zx-shadow-sm);
}

.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field > span {
  font-size: 13px;
  font-weight: 600;
  color: var(--zx-fg);
}

.submit {
  width: 100%;
  margin-top: 6px;
  font-weight: 600;
}

.helper {
  display: flex;
  justify-content: space-between;
  font-size: 12.5px;
  color: var(--zx-muted-fg);
}

.helper a {
  cursor: pointer;
  font-weight: 500;
}

.code-row {
  display: flex;
  gap: 8px;
}

.code-row .el-input {
  flex: 1;
}

.demo-code {
  padding: 8px 12px;
  border-radius: 8px;
  background: #eef3ff;
  border: 1px dashed #b3c8ff;
  color: #1e40af;
  font-size: 13px;
}

@media (max-width: 960px) {
  .auth-page {
    grid-template-columns: 1fr;
  }

  .auth-brand {
    padding: 34px 28px;
    min-height: 320px;
    gap: 24px;
  }

  .brand-copy h1 {
    font-size: 32px;
  }

  .feature-list {
    display: none;
  }
}
</style>