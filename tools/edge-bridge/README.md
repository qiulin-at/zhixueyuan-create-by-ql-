# Edge Browser Bridge

用本机脚本 / AI 操控 Edge 的最小可用方案：**MV3 扩展 + 本地 Python 桥**。
不依赖 Playwright / Puppeteer / Selenium，只用 Python 标准库；可以接管你**已经登录**的普通 Edge 窗口。

```
脚本 / AI  ──HTTP :8766（X-Bridge-Token）──►  bridge/server.py  ──WS :8765（?token=）──►  Edge 扩展  ──►  页面
```

- 扩展负责「在页面里干活」：导航、点击、输入、滚动、读文本/HTML、截图。
- 桥负责「排队与转发」：一个扩展连接、多个脚本请求、超时与错误透传。
- 两个端口都只绑 `127.0.0.1`，WS 与 HTTP 都要 token。

---

## 1. 目录

```
tools/edge-bridge/
├── extension/            # 加载到 Edge 的扩展
│   ├── manifest.json
│   ├── background.js     # Service Worker：连接桥、执行命令
│   ├── popup.html/js/css # 弹窗：连接状态、token、截图、调试器授权
├── bridge/
│   ├── server.py         # 本地桥（WS + HTTP，标准库）
│   ├── ctl.py            # 命令行控制器
│   └── .token            # 首次启动自动生成，勿提交
└── README.md
```

---

## 2. 安装（约 1 分钟）

1. 启动桥：

```bash
cd tools/edge-bridge
python bridge/server.py
```

记下终端打印的 **Token**（也保存在 `bridge/.token`）。

2. 加载扩展：Edge 地址栏输入 `edge://extensions` → 打开左下角 **开发人员模式** → **加载解压缩的扩展** → 选择 `tools/edge-bridge/extension`。

3. 点扩展图标，填入 **端口 8765** 与上一步的 **Token**，点「保存并重连」。
   状态变成绿色 **已连接** 即可。

> 想执行任意 JS（`ctl.py eval`）时，再点弹窗里的「启用 JS 执行（调试器）」授权一次。
> Edge 会提示「正在调试此浏览器」，属正常现象；不授权也不影响其他命令。

---

## 3. 命令行用法

```bash
python bridge/ctl.py health                 # 桥 + 扩展连接状态
python bridge/ctl.py tabs                   # 列出所有标签页
python bridge/ctl.py goto http://127.0.0.1:5173/
python bridge/ctl.py info                   # URL / 标题 / 视口 / 滚动位置
python bridge/ctl.py text --limit 2000      # 页面纯文本
python bridge/ctl.py click ".course-card"   # CSS 选择器点击
python bridge/ctl.py click --text "登录"     # 按可见文本点击（更抗改版）
python bridge/ctl.py type "#username" student --append
python bridge/ctl.py scroll --y 800
python bridge/ctl.py shot out.png --width 1440 --height 900
python bridge/ctl.py eval "document.title"  # 需先授权调试器
python bridge/ctl.py call page.eval --params '{"code":"1+1"}'
python bridge/ctl.py wait 1.5
```

通用参数：`--raw` 只输出 data；`--base` 改控制接口地址；`--token` 覆盖默认 token。

---

## 4. HTTP 接口

```bash
TOKEN=$(cat bridge/.token)

curl -s http://127.0.0.1:8766/health

curl -s -X POST http://127.0.0.1:8766/cmd \
  -H "Content-Type: application/json" \
  -H "X-Bridge-Token: $TOKEN" \
  -d '{"action":"page.click","params":{"text":"免费注册"}}'
```

响应统一为：

```json
{ "ok": true, "data": { }, "elapsed": 0.12 }
{ "ok": false, "error": "未找到目标元素", "elapsed": 0.05 }
```

### 命令清单

| action | params | 说明 |
|---|---|---|
| `tabs.list` | — | 所有标签页 |
| `tabs.open` / `tabs.activate` / `tabs.close` | `url` / `tabId` | 标签页管理 |
| `nav.goto` | `url`、`tabId?` | 不传 tabId 则新开标签 |
| `nav.back` / `nav.forward` / `nav.reload` | `tabId?` | 前进后退刷新 |
| `page.info` | `tabId?` | URL、标题、视口、滚动高度 |
| `page.text` | `limit` | `innerText` 截断 |
| `page.html` | `limit` | 外层 HTML 截断 |
| `page.click` | `selector` 或 `text` | 先滚动到可视区再点击 |
| `page.type` | `selector`、`value`、`clear` | 走原生 setter + 派发 input/change，兼容 Vue/React |
| `page.scroll` | `y` 或 `selector` | 滚动页面 / 滚动到元素 |
| `shot.capture` | `tabId?`、`width?`、`height?` | 可视区截图，返回 dataURL，`ctl.py` 自动落盘 |
| `page.eval` | `code` | 需 debugger 授权，返回表达式结果 |
| `wait` | `seconds` | 桥侧等待，不占扩展 |

---

## 5. 权限与安全边界

| 权限 | 为什么需要 |
|---|---|
| `tabs` | 列出/激活/关闭标签、截图 |
| `scripting` + `<all_urls>` | 在目标页注入点击/输入/读取脚本 |
| `storage` | 保存端口与 token |
| `alarms` | MV3 Service Worker 休眠后自动重连 |
| `debugger`（**可选**） | 仅 `page.eval` 使用；MV3 禁止 `eval`，这是唯一合规通道 |

措施：

- 两个端口都绑定 `127.0.0.1`，局域网不可见。
- WS 握手与 HTTP 都校验 token（`bridge/.token` 首次启动随机生成，权限 600）。
- 不做任何外发请求；不收集页面内容。
- 需要停止时：关掉 `server.py`，扩展会自动重连失败；彻底移除则在扩展管理页删除。

风险提示：装上扩展后，任何能读到 `.token` 的本机程序都能驱动你的浏览器（含已登录会话）。这是本地自动化工具的固有代价，请勿在共享电脑上长期开启。

---

## 6. 已知限制

1. **截图只覆盖可视区**。需要整页时用 `--height` 放大窗口，或后续接 `Page.captureScreenshot`（`captureBeyondViewport`）。
2. `edge://`、`chrome://`、扩展商店等**受保护页面**无法注入脚本，命令会明确报错。
3. `page.eval` 必须先在弹窗授权 `debugger`；若 DevTools 正开着同一标签，会附加失败。
4. MV3 Service Worker 空闲会被回收，靠 `alarms` + 断线重连恢复，通常 2.5 秒内自动重连。
5. 修改扩展源码后需在 `edge://extensions` 点一次「重新加载」，否则跑的还是旧 Service Worker。

---

## 7. 故障排查

| 现象 | 原因 / 处理 |
|---|---|
| 弹窗一直「未连接」 | 桥没起 / 端口不是 8765 / token 不匹配；先 `ctl.py health` 看桥是否活着 |
| `token 不正确（403）` | 弹窗里的 token 与 `bridge/.token` 不一致，重新复制 |
| `未授权调试器` | 点弹窗「启用 JS 执行」；或改用 `page.text/html/click/type` |
| 命令超时 | 目标标签被关闭 / 页面弹了原生对话框 / 扩展被重载；重新执行即可 |
| 截图失败 | 窗口被最小化时可能取不到帧，恢复窗口后重试 |

---

## 8. 一段可直接跑的示例

```bash
cd tools/edge-bridge
python bridge/server.py &                 # 另开一个终端更清晰
python bridge/ctl.py goto http://127.0.0.1:5173/
python bridge/ctl.py click ".course-card"
python bridge/ctl.py --raw info           # 应看到 /courses/<id>
python bridge/ctl.py shot demo.png
```

配合本项目做验收时，可以用它依次登录三种角色、点开后台、截图留档，替代手工点击。
