const $ = (id) => document.getElementById(id)

function log(message) {
  const el = $('log')
  const time = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  el.textContent = `[${time}] ${message}\n${el.textContent}`.slice(0, 600)
}

function renderStatus(state) {
  const badge = $('status')
  const text = $('statusText')
  badge.classList.toggle('on', Boolean(state?.connected))
  badge.classList.toggle('off', !state?.connected)
  text.textContent = state?.connected ? '已连接' : '未连接'
  if (state?.lastError) log(state.lastError)
}

async function refreshStatus() {
  try {
    const state = await chrome.runtime.sendMessage({ type: 'getStatus' })
    renderStatus(state)
    return state
  } catch (error) {
    renderStatus({ connected: false, lastError: '无法获取后台状态' })
    return null
  }
}

async function loadSettings() {
  const saved = await chrome.storage.local.get(['port', 'token'])
  $('port').value = saved.port || 8765
  $('token').value = saved.token || ''
}

async function loadCurrentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
  if (!tab) return
  $('tabTitle').textContent = tab.title || '（无标题）'
  $('tabUrl').textContent = tab.url || '—'
  return tab
}

$('save').addEventListener('click', async () => {
  const port = Number($('port').value) || 8765
  const token = $('token').value.trim()
  $('save').disabled = true
  $('save').textContent = '连接中…'
  try {
    const state = await chrome.runtime.sendMessage({ type: 'reconnect', port, token })
    renderStatus(state)
    log(state?.connected ? '已连接本地桥' : '仍未连接，请检查桥进程与 token')
  } catch (error) {
    log(`重连失败：${error.message}`)
  } finally {
    $('save').disabled = false
    $('save').textContent = '保存并重连'
  }
})

$('probe').addEventListener('click', async () => {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
    if (!tab) throw new Error('没有活动标签页')
    const [result] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => ({ title: document.title, url: location.href, readyState: document.readyState }),
    })
    log(`页面：${result.result.title}（${result.result.readyState}）`)
  } catch (error) {
    log(`读取失败：${error.message}`)
  }
})

$('shot').addEventListener('click', async () => {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
    if (!tab) throw new Error('没有活动标签页')
    const dataUrl = await chrome.tabs.captureVisibleTab(tab.windowId, { format: 'png' })
    $('previewImg').src = dataUrl
    $('preview').classList.remove('hidden')
    log('截图完成（可视区）')
  } catch (error) {
    log(`截图失败：${error.message}`)
  }
})

$('debug').addEventListener('click', async () => {
  try {
    const granted = await chrome.permissions.request({ permissions: ['debugger'] })
    if (granted) {
      log('已授权调试器，可使用 ctl.py eval 执行任意 JS')
      $('debug').textContent = '调试器已授权'
      $('debug').disabled = true
    } else {
      log('未授权调试器，eval 命令不可用（其他命令不受影响）')
    }
  } catch (error) {
    log(`授权失败：${error.message}`)
  }
})

chrome.runtime.onMessage.addListener((message) => {
  if (message?.type === 'statusChanged') renderStatus(message.state)
})

async function refreshDebugPermission() {
  try {
    const granted = await chrome.permissions.contains({ permissions: ['debugger'] })
    if (granted) {
      $('debug').textContent = '调试器已授权'
      $('debug').disabled = true
    }
  } catch (error) {
    /* ignore */
  }
}

loadSettings()
refreshStatus()
loadCurrentTab()
refreshDebugPermission()
setInterval(refreshStatus, 2000)
