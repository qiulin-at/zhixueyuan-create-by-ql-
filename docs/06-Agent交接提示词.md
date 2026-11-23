# Agent 交接提示词

> 用途：把本项目完整交接给另一个 AI 开发 Agent（同一台机器、同一项目目录）。
> 使用方法：复制下方「提示词正文」整段，粘贴到目标 Agent 的对话框；若对方支持 goal 模式，可直接作为长期目标。
> 可裁剪点：阶段 1-6 按需删除不需要的部分；「Done when」中未选择的阶段条目同步删除。

---

## 提示词正文

你接手「智学云 · 面向教育平台的智能体」项目（华为 ICT 学院《基于 Python 的 AI 项目实践》课程项目二）。项目当前已可运行、18 项自动化测试通过。你的第一原则：**先审计、后开发；不破坏现状；每步可验证**。禁止在读完项目并跑通测试之前修改任何代码。

### 一、项目现状（事实基线，若与实际文件不一致以文件为准）

- 工作目录：`C:\Users\qiulin\Desktop\项目二 面向教育平台的智能体开发`（Windows + git-bash）
- 后端：FastAPI + SQLAlchemy 2.x，Python 3.14，依赖已安装在根目录 `.venv`
- 前端：Vue 3.5 + Vite 6 + Element Plus 2.8.8 + Pinia + Vue Router + Axios + ECharts + marked
- 数据库：默认 SQLite（`backend/zhixueyun.db`）；在 `backend/.env` 设置 `DATABASE_URL` 可切 MySQL 8.0
- 大模型：OpenAI 兼容网关（`app/services/llm.py`）；`LLM_API_KEY` 为空时自动走 Mock（`app/services/mock_engine.py`）
- 已实现：
  - 用户系统：注册、登录（JWT）、重置密码（演示验证码）、资料修改、三角色权限
  - 课程模块：技术体系/方向/等级/免费筛选，最新/学习人数/评分排序，课程名+讲师名搜索，详情、收藏、章节进度、评论
  - AI 学习助手：多轮答疑、学习路径、代码批改、学习报告（Mock/在线双模式）
  - 实习就业：职位筛选/搜索/详情/申请
  - 后台管理：用户、课程上下架、订单、职位申请的**接口**（无前端页面）
- 尚未实现（本次要补）：后台管理前端、通知提醒、Docker 部署、RAG、文档实际化
- 已知验证基线：
  - `cd backend && ../.venv/Scripts/python.exe -m pytest tests -q` → 18 passed
  - `cd frontend && npm run build` → 构建成功（约 11s）
  - `GET http://127.0.0.1:8000/api/health` → `database: up, llm_mode: mock`

启动命令：

```bash
# 后端
cd backend
../.venv/Scripts/python.exe seed.py
../.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000

# 前端
cd frontend
npm install --registry=https://registry.npmmirror.com
npm run dev
```

演示账号（密码均为 `123456`）：学生 `student`、管理员 `admin`、教师 `teacher_wang`。

接口契约（不得破坏）：统一响应 `{code, message, data}`；错误码 40001/40101/40301/40401/40901/50001；鉴权 `Authorization: Bearer <JWT>`；分页数据 `{items, total, page, page_size}`。

指导书硬性要求（验收依据）：

- 基础必做：用户系统（注册/登录/密码重置/资料/三角色）、课程模块（三维筛选+四维排序+模糊搜索、详情/收藏/进度、后台课程/讲师/订单/用户管理）、四大模块（理论/实训/认证/实习就业）
- 进阶必做：AI 智能答疑（多轮）、学习路径推荐、作业自动批改、学习报告生成
- 加分项：学习提醒、学习社区、移动端适配、通知推送、订单信息展示
- 交付物：可运行系统（内网访问地址）、源码仓库、需求分析文档、架构设计文档、答辩 PPT、华为项目管理 4 表（成员/任务书/进度表/≥4 次会议纪要）
- 考核权重：平时 20% + 作品 40% + 答辩 40%

### 二、你的任务

**阶段 0：只读审计（必须先做，禁止改任何代码）**

1. 阅读：`README.md`、`docs/01-项目方案设计.md`、`backend/app/main.py`、`backend/app/models.py`、`backend/app/routers/` 全部文件、`backend/app/services/`、`backend/tests/test_api.py`、`frontend/src/router/index.js`、`frontend/src/api/index.js`、`frontend/src/views/` 全部页面
2. 执行并记录：pytest（命令 + 通过数）、`npm run build`（退出码）、`GET /api/health`（响应摘要）
3. 统计并报告：后端路由文件数与接口数、前端页面数、数据表数、测试用例数
4. 对照上方「指导书硬性要求」输出 `docs/06-缺口清单.md`：每项标注【已实现/部分实现/缺失】+ 代码证据（文件:行号）+ 修复建议 + 预估工作量
5. **停下，等待确认优先级后再进入阶段 1**

**阶段 1：后台管理前端（P1）**

- 新增 `/admin` 页面：仅 admin 可进；教师只看到本人课程的上下架；含统计卡片、用户列表（角色修改）、课程列表（上下架）、订单与职位申请列表
- 复用 `frontend/src/api/index.js` 的 Axios 实例与统一响应；顶栏按角色显示入口
- 验收：admin 能看到真实数据并操作成功；student 访问被拦截；`npm run build` 通过

**阶段 2：通知与学习提醒（P2）**

- 后端：notifications 表 + 列表/未读数/标记已读接口 + 触发逻辑（收藏课程更新、学习计划到期，可用登录时生成或定时任务）
- 前端：顶栏通知铃铛（未读角标）+ 列表弹层
- 验收：新接口有 pytest 用例；无网络/Mock 环境可用；页面可标记已读

**阶段 3：测试补强与覆盖率（P3）**

- 补异常路径（越权、非法参数、重复操作、AI 降级）与进度计算边界
- 安装 pytest-cov 并输出覆盖率报告，保存到 `docs/` 或 `backend/coverage/`
- 验收：pytest 全绿且用例数 > 18；覆盖率报告文件存在并记录关键数字

**阶段 4：Docker Compose 部署（P4）**

- 产出 `docker-compose.yml`（mysql:8.0 + backend + nginx）、`backend/Dockerfile`、前端构建后由 Nginx 托管并反代 `/api`
- 验收：`docker compose up -d --build` 后 `http://localhost:8080` 可访问、`/api/health` 正常；若本机无 Docker，跳过并记录阻塞原因

**阶段 5：RAG 课程资料检索答疑（P5）**

- 课程资料表与切片、本地检索（优先 TF-IDF 或关键词检索，默认不得依赖付费 embedding 服务）、答疑时注入检索片段并输出来源
- 验收：答疑接口返回引用来源；无 API Key 时仍可用；新增 pytest 用例

**阶段 6：文档与答辩材料（P6）**

- 基于 `docs/02-05` 模板产出真实内容：需求规格说明书、系统架构设计、测试报告、答辩 PPT，引用真实代码、接口与测试数据
- 验收：文档无 `[]` 占位符，与代码一致；答辩 PPT 覆盖 15 页大纲

### 三、硬性约束（违反即停止）

1. 禁止修改或删除现有测试来"让测试通过"；测试失败必须修业务代码
2. 禁止改动 `.venv/`、`node_modules/`、`.codeartsdoer/`、`实验指导书(1).doc`
3. 不得破坏现有接口契约与前端页面；现有 18 项测试必须保持通过
4. 新增依赖需先说明理由并锁定版本（兼容 Python 3.14 / Node 18.20.1）；npm 安装使用 npmmirror 镜像
5. 无 `LLM_API_KEY` 时所有 AI 功能必须 Mock 可用（答辩兜底）
6. 默认 SQLite 开箱即跑，MySQL 仅为可选；`seed.py` 必须保持可用，演示账号不得失效
7. 全程中文（界面、文档、汇报）；不得把密钥/Token 写入代码或文档
8. 一次只做一个阶段，完成即停并汇报；禁止跨阶段连续大改

### 四、完成标准（Done when）

1. `docs/06-缺口清单.md` 覆盖指导书全部必做项，且每项有代码证据
2. 阶段 1-6 每个阶段都有代码产物；`cd backend && ../.venv/Scripts/python.exe -m pytest tests -q` 退出码 0、用例数 ≥ 18、新增功能有新增用例
3. `cd frontend && npm run build` 退出码 0
4. 新增接口用 curl 验证通过（给出命令与响应摘要）
5. `docker-compose.yml` 存在且本机可启动（或明确记录环境阻塞）
6. 文档无模板占位符，答辩 PPT 覆盖 15 页大纲
7. 提交《交接说明》：改动文件清单、验证命令与结果、遗留问题与风险

### 五、停止条件（任一出现立即停止并汇报）

- 现有 18 项测试失败且无法在不修改测试的前提下修复
- 需要新增付费 API 或云服务（embedding、对象存储、短信/邮件）才能继续
- 需要删除/重建 `backend/zhixueyun.db` 或导致演示账号失效
- 需要修改已锁定版本的依赖，或降级 Node/Python
- 端口 8000/5173 被占用且无法安全更换端口
- 本机无 Docker 却必须完成部署验证
- 同一问题连续 2 次修复失败
- 需要访问或修改项目目录以外的文件

### 六、汇报格式（每阶段结束必须按此输出）

```
阶段：P?
完成内容：文件清单（新增 / 修改）
验证：命令 + 结果（通过数 / 退出码 / curl 摘要）
风险 / 遗留：
下一步建议：
```

---

## 使用提示

- 首次交接建议先只发「阶段 0」，确认审计结果可信后再逐阶段下发，避免一次性放开范围。
- 若目标 Agent 无法访问本地文件，把本提示词连同 `README.md`、`docs/01`、关键代码一起投喂。
- 每阶段结束后对照「完成标准」抽查，重点看验证命令的真实输出，而不是只看文字结论。