# Agent 交接提示词（当前基线版）

> 用途：把本项目交接给另一个 AI 开发 Agent（同一台机器、同一项目目录）。
> 使用方法：复制下方「提示词正文」整段，粘贴到目标 Agent 的对话框。
> 更新时间：2026-11-23 21:25，对应提交 `11ed572`。

---

## 提示词正文

你接手「智学云 · 面向教育平台的智能体」项目（华为 ICT 学院《基于 Python 的 AI 项目实践》课程项目二）。项目已可运行、**46 项自动化测试通过、行覆盖 89%**，并已完成后台管理、通知、个人中心、课程/讲师/订单管理、测试补强五批工作，Git 有 4 条提交。

你的第一原则：**先读文档与代码、后动手；不破坏现状；每批可验证**。在跑通测试并读完 `docs/06-缺口清单.md` 之前，禁止修改任何代码。

### 一、事实基线（2026-11-23 实测，若与文件不一致以文件为准）

| 项 | 当前值 |
|---|---|
| 工作目录 | `C:\Users\qiulin\Desktop\项目二 面向教育平台的智能体开发`（Windows + Git Bash） |
| 后端 | FastAPI + SQLAlchemy 2.x，Python 3.14，依赖在根目录 `.venv` |
| 前端 | Vue 3.5 + Vite 6 + Element Plus 2.8.8 + Pinia + Router + Axios + ECharts（按需）+ marked + DOMPurify 3.2.4 |
| 数据库 | SQLite `backend/zhixueyun.db`，**13 张表** |
| 接口 | **42 条路径 / 49 个操作**（`/openapi.json` 可核对） |
| 页面 | 8 个：Login、CourseList、CourseDetail、AiAssistant、Report、JobList、Admin、Profile |
| 测试 | **46 passed**，`pytest-cov` 行覆盖 **89%**（1254 语句 / 136 未覆盖） |
| 仓库 | `git` 已初始化，分支 `main`，4 条提交，工作区干净；**未配远端** |
| 缺口 | 41 项中 **32 已实现 / 4 部分 / 5 缺失**（见 `docs/06-缺口清单.md` §6） |

已完成的能力（不要重复开发，只需维护）：

- 用户：注册、登录（JWT）、重置密码（验证码落表）、资料修改、三角色
- 课程：三维筛选、四维排序、模糊搜索、详情、收藏、章节进度、评论（一人一课一条）
- AI：多轮答疑、学习路径、作业批改、学习报告（Mock / 在线双模式，在线失败自动降级）
- 就业：职位筛选、详情、申请（防重复）
- 后台：统计、用户角色与启停、课程 CRUD 与章节维护、讲师列表与指派、订单详情与状态机、职位申请列表
- 通知：收藏课程更新、下架、7 天停滞提醒、未读角标与已读
- 个人中心：资料、收藏、我的课程、我的订单
- 工程：pytest 46 项、覆盖率报告、`backend/run.bat`、`docs/07`、`docs/08`

尚未完成（剩余 9 项，按优先级）：

| 编号 | 内容 | 状态 | 预估 |
|---|---|---|---|
| E6 | Docker Compose（mysql + backend + nginx） | 缺失 | 0.5–1 天 |
| E8 | RAG 课程资料检索（带引用，离线可跑） | 缺失 | 1.5–2 天 |
| D3 | 需求规格说明书（按真实功能重写） | 部分 | 1 天 |
| D4 | 架构设计文档（以 openapi.json 为准） | 部分 | 1 天 |
| D5 | 答辩 PPT（15 页） | 缺失 | 1 天 |
| D6 | 华为项目管理 4 表（成员/任务书/进度/≥4 次纪要） | 缺失 | 1 天 |
| D2 | 源码仓库远端推送 | 缺失（本地已就绪） | 0.2 天 |
| B2 | 学习社区（问答/回复/点赞） | 部分（现为课程评价） | 1 天，可选 |
| B4 | SSE 实时推送（现为 60s 轮询） | 部分 | 0.5 天，可选 |

### 二、必读文档（按顺序，最多 20 分钟）

1. `docs/06-缺口清单.md`——**唯一事实源**：41 项逐条状态、代码证据（文件:行号）、缺口与建议；§10 是各批次交付记录
2. `docs/08-缺口补全路线图.md`——剩余工作的批次拆解、验收标准、排期
3. `docs/07-测试与覆盖率报告.md`——46 用例、覆盖率明细、未覆盖原因
4. `README.md`——启动方式、演示账号、接口速查
5. `.workbuddy/memory/2026-11-23.md`——本次会话的决策与踩坑记录（若存在，建议先读）

### 三、启动与验证（先跑通，再动手）

```bash
# 后端（Windows 双击 backend\run.bat 亦可）
cd backend
../.venv/Scripts/python.exe seed.py     # 仅首次或需要重置演示数据时
../.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 前端
cd frontend
npm run dev                             # 默认 5173

# 验证
cd backend && ../.venv/Scripts/python.exe -m pytest tests -q        # 期望 46 passed
cd frontend && npm run build                                        # 期望 exit 0
curl http://127.0.0.1:8000/api/health                               # database=up, llm_mode=mock
```

演示账号（密码均 `123456`）：学生 `student`、管理员 `admin`、教师 `teacher_wang` / `teacher_li`。

接口契约（不得破坏）：统一响应 `{code, message, data}`；错误码 40001/40101/40301/40401/40901/50001；鉴权 `Authorization: Bearer <JWT>`；分页 `{items, total, page, page_size}`。

### 四、你的任务

**先做只读审计（禁止改代码）**：读上表文档与 `backend/app/routers/`、`backend/app/models.py`、`backend/tests/test_api.py`、`frontend/src/views/AdminView.vue`、`frontend/src/views/ProfileView.vue`；跑三条验证命令；核对接口/表/用例数是否与本节一致。**然后停下，等用户确认从哪批开始。**

后续按 `docs/08` 顺序推进，一次一批：

- **批次 C：Docker Compose**——`backend/Dockerfile`、`frontend/Dockerfile`（多阶段构建）、`docker-compose.yml`（mysql:8.0 + backend + nginx）、`.env.example`；nginx 托管 `dist` 并反代 `/api`。验收：`docker compose up -d --build` 后 `/api/health` 200。
- **批次 D：RAG**——新增 `course_materials` 表、种子资料、TF-IDF/BM25 检索（**不得引入付费 embedding**）、答疑注入 Top-3 片段并在回答末尾输出「参考章节」。验收：离线可用、有引用、有新增用例。
- **批次 F：交付物**——D3/D4 文档按真实接口重写（当前 42 路径/49 操作）、D5 15 页 PPT、D6 项目管理 4 表。**必须在 C/D 接口定稿后再写**。
- **批次 E（可选）：B2/B4**——社区问答与 SSE，时间不足则在文档中说明取舍。

### 五、硬性约束（违反即停止）

1. **不得修改或删除现有 46 个测试来"让测试通过"**；测试失败必须修业务代码
2. 不得改动 `.venv/`、`node_modules/`、`实验指导书(1).doc`、`.workbuddy/`
3. 不得破坏已有接口契约与页面；**46 项测试必须持续全绿**
4. 新增依赖需说明理由并锁定版本（Python 3.14 / Node 18.20.1）；npm 使用 npmmirror
5. 无 `LLM_API_KEY` 时全部 AI 功能必须 Mock 可用
6. **不得直接改动演示库 `backend/zhixueyun.db`**：测试用 `backend/tests/test_zhixueyun.db`，UI 联调请复制副本（如 `backend/tests/ui_demo.db`）并在结束后删除
7. 后端**没有 `--reload`**：改完后端代码必须重启进程才生效；重启前先确认 8000 端口占用
8. `backend/run.bat` **必须保持纯 ASCII**：含中文会被 cmd 按缓冲区截断，出现「不是内部或外部命令」
9. 全程中文；不得把密钥/Token 写入代码、文档或对话
10. 一次只做一个批次，完成即停并汇报

### 六、完成标准（Done when）

1. `docs/06-缺口清单.md` 状态与代码一致，每条有可定位证据（`文件:行号`）
2. `pytest -q` 退出码 0、用例数 ≥ 46、新增功能有新增用例
3. `npm run build` 退出码 0
4. 新增接口用真实请求验证（给出命令与响应摘要）
5. `docker-compose.yml` 存在且可启动（或明确记录环境阻塞）
6. 文档无模板占位符，接口数与 `openapi.json` 一致
7. 交付《交接说明》：改动文件、验证命令与结果、遗留风险
8. **每批一次 git 提交**，信息写清批次与内容

### 七、停止条件（任一出现立即停止并汇报）

- 现有 46 项测试失败且无法在不改测试的前提下修复
- 需要新增付费 API 或云服务（embedding、短信、对象存储）才能继续
- 需要删除/重建 `backend/zhixueyun.db` 或导致演示账号失效
- 需要降级 Python/Node 或修改已锁定依赖
- 端口 8000/5173 被占用且无法安全更换
- 本机无 Docker 却必须完成容器验证（应先记录阻塞，不得伪造）
- 同一问题连续 2 次修复失败
- 需要访问项目目录以外的文件

### 八、汇报格式（每批结束必须按此输出）

```
批次：C / D / F ...
完成内容：文件清单（新增 / 修改）
验证：命令 + 结果（通过数 / 退出码 / 请求摘要）
风险 / 遗留：
下一步建议：
```

---

## 使用提示

- 先只发「提示词正文」+ 一句「先做只读审计，不要改代码」，确认它读到的基线（46/89%/42 路径/13 表）与你看到的一致，再放行开发。
- 若目标 Agent 不能访问本地文件，把 `README.md`、`docs/06`、`docs/07`、`docs/08`、`backend/app/`、`backend/tests/test_api.py` 一起投喂。
- 换 Agent 前确认 `git status` 干净；新 Agent 的第一批改动应是一次独立提交，便于回滚。
