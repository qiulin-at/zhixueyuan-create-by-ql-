# Agent 交接提示词（当前基线版）

> 用途：把本项目交接给另一个 AI 开发 Agent（同一台机器、同一项目目录）。
> 使用方法：复制下方「提示词正文」整段，粘贴到目标 Agent 的对话框。
> 更新时间：2026-11-24（批次 C/D/E、D3/D4、D5/D6 与文档回填）。

---

## 提示词正文

你接手「智学云 · 面向教育平台的智能体」项目（华为 ICT 学院《基于 Python 的 AI 项目实践》课程项目二）。项目已可运行、**57 项自动化测试通过、行覆盖 90%**，并已完成后台管理、通知、个人中心、课程/讲师/订单管理、测试补强五批工作，以及 P0 口径校准、批次 C 容器实测、批次 D RAG 检索、D3/D4 正式文档、B4 SSE 通知、B2 学习社区、D5 答辩 PPT 与 D6 项目管理 4 表，Git 有 13 条功能提交（总提交数见 `git log`）。

你的第一原则：**先读文档与代码、后动手；不破坏现状；每批可验证**。在跑通测试并读完 `docs/06-缺口清单.md` 之前，禁止修改任何代码。

### 一、事实基线（2026-11-24 实测，若与文件不一致以文件为准）

| 项 | 当前值 |
|---|---|
| 工作目录 | `C:\Users\qiulin\Desktop\项目二 面向教育平台的智能体开发`（Windows + Git Bash） |
| 后端 | FastAPI + SQLAlchemy 2.x，Python 3.14，依赖在根目录 `.venv` |
| 前端 | Vue 3.5 + Vite 6 + Element Plus 2.8.8 + Pinia + Router + Axios + ECharts（按需）+ marked + DOMPurify 3.2.4 |
| 数据库 | 代码模型 **17 张表**（G1 新增 `operation_logs`）；测试库与演示库均 17 张；`backend/migrate_v2.py` 可幂等补表 |
| 接口 | **47 条路径 / 55 个操作**（`/openapi.json` 可核对；G1 新增审计日志与教师学情） |
| 页面 | 8 个：Login、CourseList、CourseDetail、AiAssistant、Report、JobList、Admin、Profile |
| 测试 | **62 passed**，`pytest-cov` 行覆盖 **91%**（1499 语句 / 135 未覆盖） |
| 仓库 | `git` 已初始化并推送 GitHub：`https://github.com/qiulin-at/zhixueyuan-create-by-ql-.git`（public，`main`；当前与 `origin/main` 同步，D2 推送提交 `a0be17b`，**13 条功能提交**，另有文档/口径回填提交见 `git log`）；`output/` 不入公开仓库（本地交付）；历史已重写移除 `output/`，旧历史备份 `.codeartsdoer/git-backup/zhixueyun-before-rewrite.bundle` |
| 容器编排 | `docker-compose.yml`、双 Dockerfile、`frontend/nginx.conf` 已实测：三容器 healthy，8080 health 200，student 登录 200 |
| 通知推送 | SSE `/api/notifications/stream` + EventSource，60s 轮询兜底 |
| 学习社区 | 课程评价 + 回复/楼中楼（`parent_id`）+ 点赞（一人一次） |
| 课程资料 | **20 条**（4 门课各 5 段）；测试库已导入，演示库/MySQL 需跑 `seed_materials.py` 补 |
| 缺口 | 一期 41 项 **41 已实现 / 0 部分 / 0 缺失**（见 `docs/06-缺口清单.md` §6）；二期 G1 已完成，G2–J2 为规划态，见 §11 |

已完成的能力（不要重复开发，只需维护）：

- 用户：注册、登录（JWT）、重置密码（验证码落表）、资料修改、三角色
- 课程：三维筛选、四维排序、模糊搜索、详情、收藏、章节进度、评论（一人一课一条）、回复/楼中楼/点赞
- AI：多轮答疑（含课程资料 RAG Top-3 检索与引用）、学习路径、作业批改、学习报告（Mock / 在线双模式，在线失败自动降级）
- 就业：职位筛选、详情、申请（防重复）
- 后台：统计、用户角色与启停、课程 CRUD 与章节维护、讲师列表与指派、订单详情与状态机、职位申请列表、操作日志（G1）、教师课程学情（G1）
- 通知：收藏课程更新、下架、7 天停滞提醒、未读角标与已读、SSE 实时未读数（60s 轮询兜底）
- 个人中心：资料、收藏、我的课程、我的订单
- 工程：pytest 57 项、覆盖率报告、`backend/run.bat`、`docs/07`、`docs/08`
- 文档：`docs/02-需求规格说明书.md`、`docs/03-系统架构设计.md`（2026-11-24，接口与表结构已对齐代码）
- 部署：`docker-compose.yml`、双 Dockerfile、`frontend/nginx.conf`、空库自动 seed 入口（2026-11-24 实测：三容器 healthy，8080 health 200，登录 200）
- 交付物：`output/邱麟_答辩PPT_v2.pptx`（18 页）、`output/邱麟_项目管理4表_v2.docx`（28 表 / 8 次纪要）；一期 15 页 PPT / 19 表 Word 保留

剩余工作：**一期 0 项**（D2 已于 2026-11-24 推送）；二期 11 批（G1–J2）为规划态，答辩后按 `docs/10` 执行。

| 编号 | 内容 | 状态 | 预估 |
|---|---|---|---|
| D2 | 源码仓库远端推送 | ✅ 已完成（2026-11-24，`a0be17b`） | — |

### 二、必读文档（按顺序，最多 20 分钟）

1. `docs/06-缺口清单.md`——**唯一事实源**：41 项逐条状态、代码证据（文件:行号）、缺口与建议；§10 是各批次交付记录
2. `docs/08-缺口补全路线图.md`——剩余工作的批次拆解、验收标准、排期
3. `docs/07-测试与覆盖率报告.md`——57 用例、覆盖率明细、未覆盖原因
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
cd backend && ../.venv/Scripts/python.exe -m pytest tests -q        # 期望 57 passed
cd frontend && npm run build                                        # 期望 exit 0
curl http://127.0.0.1:8000/api/health                               # 需先启动后端；期望 database=up, llm_mode=mock
```

演示账号（密码均 `123456`）：学生 `student`、管理员 `admin`、教师 `teacher_wang` / `teacher_li`。

接口契约（不得破坏）：统一响应 `{code, message, data}`；错误码 40001/40101/40301/40401/40901/50001；鉴权 `Authorization: Bearer <JWT>`；分页 `{items, total, page, page_size}`。

### 四、你的任务

**先做只读审计（禁止改代码）**：读上表文档与 `backend/app/routers/`、`backend/app/models.py`、`backend/tests/test_api.py`、`frontend/src/views/AdminView.vue`、`frontend/src/views/ProfileView.vue`；跑三条验证命令；核对接口/表/用例数是否与本节一致。**然后停下，等用户确认从哪批开始。**

后续按 `docs/08` 顺序推进，一次一批：

- **二期 G1：权限矩阵与操作审计**——✅ 已完成（2026-11-24）：`operation_logs` + 教师学情 + 前端双 Tab；62 passed / 91%；下一步 G2。

- **批次 C：Docker Compose**——✅ 已完成（2026-11-24 实测），勿重复；后续进入 D/F/E。
- **批次 D：RAG**——✅ 已完成（2026-11-24 实测），勿重复；后续进入 F/E。
- **批次 F：交付物**——✅ D3/D4/D5/D6 v2 均已完成（2026-11-24）；D2 已于 2026-11-24 推送 GitHub（`a0be17b`），一期无剩余项。
- **批次 E（可选）：B2/B4**——✅ B4 SSE、B2 学习社区均已完成（2026-11-24）。

### 五、硬性约束（违反即停止）

1. **不得修改或删除现有 57 个测试来"让测试通过"**；测试失败必须修业务代码
2. 不得改动 `.venv/`、`node_modules/`、`实验指导书(1).doc`、`.workbuddy/`
3. 不得破坏已有接口契约与页面；**57 项测试必须持续全绿**
4. 新增依赖需说明理由并锁定版本（Python 3.14 / Node 18.20.1）；npm 使用 npmmirror
5. 无 `LLM_API_KEY` 时全部 AI 功能必须 Mock 可用
6. **不得直接改动演示库 `backend/zhixueyun.db`**：测试用 `backend/tests/test_zhixueyun.db`，UI 联调请复制副本（如 `backend/tests/ui_demo.db`）并在结束后删除；`backend/seed_materials.py` 会写库，运行前需确认
7. 后端**没有 `--reload`**：改完后端代码必须重启进程才生效；重启前先确认 8000 端口占用
8. `backend/run.bat` **必须保持纯 ASCII**：含中文会被 cmd 按缓冲区截断，出现「不是内部或外部命令」
9. 全程中文；不得把密钥/Token 写入代码、文档或对话
10. 一次只做一个批次，完成即停并汇报

### 六、完成标准（Done when）

1. `docs/06-缺口清单.md` 状态与代码一致，每条有可定位证据（`文件:行号`）
2. `pytest -q` 退出码 0、用例数 ≥ 57、新增功能有新增用例
3. `npm run build` 退出码 0
4. 新增接口用真实请求验证（给出命令与响应摘要）
5. `docker-compose.yml` 存在且可启动（或明确记录环境阻塞）
6. 文档无模板占位符，接口数与 `openapi.json` 一致
7. 交付《交接说明》：改动文件、验证命令与结果、遗留风险
8. **每批一次 git 提交**，信息写清批次与内容

### 七、停止条件（任一出现立即停止并汇报）

- 现有 57 项测试失败且无法在不改测试的前提下修复
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

- 先只发「提示词正文」+ 一句「先做只读审计，不要改代码」，确认它读到的基线（57/90%/45 路径/16 表）与你看到的一致，再放行开发。
- 若目标 Agent 不能访问本地文件，把 `README.md`、`docs/06`、`docs/07`、`docs/08`、`backend/app/`、`backend/tests/test_api.py` 一起投喂。
- 换 Agent 前确认 `git status` 干净；新 Agent 的第一批改动应是一次独立提交，便于回滚。
