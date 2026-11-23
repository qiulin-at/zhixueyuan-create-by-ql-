/**
 * Browser Bridge - MV3 service worker
 * 职责：连接本机桥（ws://127.0.0.1:8765/ws?token=...），执行命令并回传结果。
 * 设计原则：所有页面操作都在目标标签页内用 chrome.scripting 注入自包含函数完成，
 *          不常驻 content script，避免污染用户页面。
 */

const DEFAULTS = { port: 8765, token: '' }
const state = { connected: false, port: DEFAULTS.port, token: '', lastError: '' }

let socket = null
let reconnectTimer = null

async function loadConfig() {
  const saved = await chrome.storage.local.get(['port', 'token'])
  state.port = Number(saved.port) || DEFAULTS.port
  state.token = saved.token || ''
}

function sendRaw(obj) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(obj))
  }
}

function scheduleReconnect() {
  if (reconnectTimer) return
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    connect()
  }, 2500)
}

function notifyPopup() {
  chrome.runtime.sendMessage({ type: 'statusChanged', state }).catch(() => {})
}

async function connect() {
  await loadConfig()
  if (socket) {
    try {
      socket.onclose = null
      socket.close()
    } catch (error) {
      /* ignore */
    }
    socket = null
  }
  const url = `ws://127.0.0.1:${state.port}/ws?token=${encodeURIComponent(state.token)}`
  try {
    socket = new WebSocket(url)
  } catch (error) {
    state.connected = false
    state.lastError = String(error)
    scheduleReconnect()
    return
  }

  socket.onopen = () => {
    state.connected = true
    state.lastError = ''
    sendRaw({ type: 'hello', name: 'edge-bridge', version: chrome.runtime.getManifest().version })
    notifyPopup()
  }

  socket.onmessage = async (event) => {
    let msg
    try {
      msg = JSON.parse(event.data)
    } catch (error) {
      return
    }
    if (msg.type === 'ping') {
      sendRaw({ type: 'pong', ts: Date.now() })
      return
    }
    if (!msg.id || !msg.action) return
    try {
      const data = await handle(msg.action, msg.params || {})
      sendRaw({ id: msg.id, ok: true, data })
    } catch (error) {
      sendRaw({ id: msg.id, ok: false, error: error?.message || String(error) })
    }
  }

  socket.onclose = () => {
    state.connected = false
    notifyPopup()
    scheduleReconnect()
  }

  socket.onerror = () => {
    state.lastError = '连接本地桥失败，请确认 bridge/server.py 已启动'
  }
}

async function getTab(tabId) {
  if (tabId) {
    const tab = await chrome.tabs.get(Number(tabId))
    if (!tab) throw new Error(`标签页 ${tabId} 不存在`)
    return tab
  }
  const [tab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true })
  if (!tab) throw new Error('没有活动标签页')
  return tab
}

async function withTimeout(promise, ms, label) {
  let timer = null
  const timeout = new Promise((resolve, reject) => {
    timer = setTimeout(() => reject(new Error(`${label}超时（${ms}ms）`)), ms)
  })
  try {
    return await Promise.race([promise, timeout])
  } finally {
    if (timer) clearTimeout(timer)
  }
}

async function runInTab(tabId, func, args = []) {
  const tab = await getTab(tabId)
  if (!tab.url || /^(edge|chrome|about|devtools):/i.test(tab.url)) {
    throw new Error(`受保护页面无法注入脚本：${tab.url}`)
  }
  const results = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func,
    args,
  })
  const first = results?.[0]
  if (!first) throw new Error('脚本执行无返回')
  if (first.error) throw new Error(String(first.error))
  return first.result
}

/* ---------- 注入到页面的自包含函数（不能引用外部变量） ---------- */

function pageInfo() {
  return {
    url: location.href,
    title: document.title,
    readyState: document.readyState,
    width: window.innerWidth,
    height: window.innerHeight,
    scrollY: Math.round(window.scrollY),
    scrollHeight: document.documentElement.scrollHeight,
  }
}

function pageText(limit) {
  const text = (document.body && document.body.innerText) || ''
  return text.slice(0, limit || 20000)
}

function pageHtml(limit) {
  return (document.documentElement.outerHTML || '').slice(0, limit || 50000)
}

function clickInPage(selector, text) {
  let el = null
  if (selector) {
    el = document.querySelector(selector)
  } else if (text) {
    const nodes = Array.from(
      document.querySelectorAll('a,button,[role="button"],input[type="submit"],label,li,td,span,div'),
    )
    el = nodes.find((node) => {
      const visible = node.offsetParent !== null || node.getClientRects().length > 0
      return visible && (node.innerText || node.value || '').trim().includes(text)
    })
  }
  if (!el) return { ok: false, reason: '未找到目标元素' }
  el.scrollIntoView({ block: 'center', inline: 'center' })
  el.click()
  return {
    ok: true,
    tag: el.tagName,
    text: (el.innerText || el.value || '').trim().slice(0, 80),
  }
}

function typeInPage(selector, value, clear) {
  const el = document.querySelector(selector)
  if (!el) return { ok: false, reason: '未找到输入框' }
  el.scrollIntoView({ block: 'center' })
  el.focus()
  const isTextarea = el instanceof HTMLTextAreaElement
  const isInput = el instanceof HTMLInputElement
  if (!isTextarea && !isInput) {
    el.textContent = value
    el.dispatchEvent(new Event('input', { bubbles: true }))
    return { ok: true, mode: 'textContent', value }
  }
  const proto = isTextarea ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype
  const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set
  const base = clear ? '' : el.value || ''
  const next = `${base}${value}`
  if (setter) setter.call(el, next)
  else el.value = next
  el.dispatchEvent(new Event('input', { bubbles: true }))
  el.dispatchEvent(new Event('change', { bubbles: true }))
  return { ok: true, value: el.value }
}

function scrollInPage(y, selector) {
  if (selector) {
    const el = document.querySelector(selector)
    if (!el) return { ok: false, reason: '未找到目标元素' }
    el.scrollIntoView({ block: 'center' })
    return { ok: true, scrollY: Math.round(window.scrollY) }
  }
  window.scrollTo({ top: y || 0, behavior: 'auto' })
  return { ok: true, scrollY: Math.round(window.scrollY) }
}

/* ---------- debugger 通道：唯一合规的任意 JS 执行方式 ---------- */
async function evalViaDebugger(tabId, code) {
  const granted = await chrome.permissions.contains({ permissions: ['debugger'] })
  if (!granted) {
    throw new Error('未授权调试器：请打开扩展弹窗，点击「启用 JS 执行」并同意授权')
  }
  const tab = await getTab(tabId)
  const target = { tabId: tab.id }
  try {
    await chrome.debugger.attach(target, '1.3')
  } catch (error) {
    throw new Error(`无法附加调试器（DevTools 是否正开着该标签？）：${error.message}`)
  }
  try {
    const result = await chrome.debugger.sendCommand(target, 'Runtime.evaluate', {
      expression: code,
      returnByValue: true,
      awaitPromise: true,
      userGesture: true,
    })
    if (result?.exceptionDetails) {
      const detail = result.exceptionDetails.exception?.description || result.exceptionDetails.text
      throw new Error(detail || '执行异常')
    }
    return { value: result?.result?.value ?? null, via: 'debugger' }
  } finally {
    try {
      await chrome.debugger.detach(target)
    } catch (error) {
      /* ignore */
    }
  }
}

/* ---------- 命令分发 ---------- */

async function handle(action, params) {
  switch (action) {
    case 'ping':
      return { pong: true, ts: Date.now() }

    case 'tabs.list': {
      const tabs = await chrome.tabs.query({})
      return tabs
        .filter((tab) => tab.id !== chrome.tabs.TAB_ID_NONE)
        .map((tab) => ({
          id: tab.id,
          windowId: tab.windowId,
          title: tab.title,
          url: tab.url,
          active: tab.active,
          status: tab.status,
        }))
    }

    case 'tabs.open': {
      const tab = await chrome.tabs.create({
        url: params.url || 'about:blank',
        active: params.active !== false,
      })
      return { id: tab.id, url: tab.url, title: tab.title }
    }

    case 'tabs.activate': {
      const tab = await getTab(params.tabId)
      await chrome.tabs.update(tab.id, { active: true })
      if (tab.windowId) await chrome.windows.update(tab.windowId, { focused: true })
      return { id: tab.id, url: tab.url, title: tab.title }
    }

    case 'tabs.close': {
      const tab = await getTab(params.tabId)
      await chrome.tabs.remove(tab.id)
      return { closed: tab.id }
    }

    case 'nav.goto': {
      if (!params.url) throw new Error('缺少 url 参数')
      if (params.tabId) {
        const tab = await chrome.tabs.update(Number(params.tabId), { url: params.url })
        return { id: tab.id, url: tab.url }
      }
      const tab = await chrome.tabs.create({ url: params.url, active: true })
      return { id: tab.id, url: tab.url }
    }

    case 'nav.back': {
      const tab = await getTab(params.tabId)
      await chrome.tabs.goBack(tab.id)
      return { ok: true }
    }

    case 'nav.forward': {
      const tab = await getTab(params.tabId)
      await chrome.tabs.goForward(tab.id)
      return { ok: true }
    }

    case 'nav.reload': {
      const tab = await getTab(params.tabId)
      await chrome.tabs.reload(tab.id, { bypassCache: Boolean(params.bypassCache) })
      return { ok: true }
    }

    case 'page.info':
      return runInTab(params.tabId, pageInfo)

    case 'page.text':
      return { text: await runInTab(params.tabId, pageText, [params.limit]) }

    case 'page.html':
      return { html: await runInTab(params.tabId, pageHtml, [params.limit]) }

    case 'page.click': {
      const result = await runInTab(params.tabId, clickInPage, [params.selector || '', params.text || ''])
      if (!result?.ok) throw new Error(result?.reason || '点击失败')
      return result
    }

    case 'page.type': {
      const result = await runInTab(params.tabId, typeInPage, [
        params.selector || '',
        params.value ?? '',
        Boolean(params.clear),
      ])
      if (!result?.ok) throw new Error(result?.reason || '输入失败')
      return result
    }

    case 'page.scroll':
      return runInTab(params.tabId, scrollInPage, [Number(params.y || 0), params.selector || ''])

    case 'page.eval': {
      if (!params.code) throw new Error('缺少 code 参数')
      return evalViaDebugger(params.tabId, params.code)
    }

    case 'shot.capture': {
      const tab = await getTab(params.tabId)
      await withTimeout(chrome.tabs.update(tab.id, { active: true }), 5000, '激活标签页')
      // 注意：无用户手势时 chrome.windows.update({focused:true}) 可能永不 resolve，绝不 await
      if (tab.windowId) {
        chrome.windows.update(tab.windowId, { focused: true }).catch(() => {})
        await new Promise((resolve) => setTimeout(resolve, 200))
      }

      let previous = null
      if (params.width && params.height) {
        try {
          const win = await withTimeout(chrome.windows.get(tab.windowId), 5000, '读取窗口')
          previous = { width: win.width, height: win.height, left: win.left, top: win.top }
          await withTimeout(
            chrome.windows.update(tab.windowId, {
              state: 'normal',
              width: Number(params.width),
              height: Number(params.height),
            }),
            5000,
            '调整窗口',
          )
          await new Promise((resolve) => setTimeout(resolve, 350))
        } catch (error) {
          previous = null
        }
      }

      const dataUrl = await withTimeout(
        chrome.tabs.captureVisibleTab(tab.windowId, { format: 'png' }),
        10000,
        '截图',
      )

      if (previous) {
        chrome.windows.update(tab.windowId, previous).catch(() => {})
      }
      return { dataUrl, tabId: tab.id, title: tab.title, url: tab.url }
    }

    default:
      throw new Error(`未知命令：${action}`)
  }
}

/* ---------- 生命周期 ---------- */

chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create('bridge-keepalive', { periodInMinutes: 0.5 })
  connect()
})

chrome.runtime.onStartup.addListener(() => {
  connect()
})

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name !== 'bridge-keepalive') return
  if (!state.connected) {
    connect()
  } else {
    sendRaw({ type: 'ping', ts: Date.now() })
  }
})

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === 'getStatus') {
    sendResponse({ ...state })
    return true
  }
  if (message?.type === 'reconnect') {
    ;(async () => {
      if (message.port) await chrome.storage.local.set({ port: message.port })
      if (typeof message.token === 'string') await chrome.storage.local.set({ token: message.token })
      await connect()
      sendResponse({ ...state })
    })()
    return true
  }
  return false
})

connect()
