# 智学云 · 面向教育平台的智能体开发（项目二样板）

华为 ICT 学院《基于 Python 的 AI 项目实践》课程项目二的可运行样板工程。
技术栈：**FastAPI + SQLAlchemy + MySQL/SQLite + Vue3 + Vite + Element Plus + OpenAI 兼容大模型（Mock 兜底）**。

- 方案与文档：[docs/01-项目方案设计.md](docs/01-项目方案设计.md)
- 需求规格：[docs/02-需求规格说明书.md](docs/02-需求规格说明书.md)
- 架构设计：[docs/03-系统架构设计.md](docs/03-系统架构设计.md)
- 答辩 / 项目管理模板：`docs/04` ~ `docs/05`
- 接口文档（运行后）：<http://127.0.0.1:8000/docs>

## 已实现功能

| 模块 | 功能 |
|---|---|
| 用户系统 | 注册、登录（JWT）、密码重置（演示验证码）、三角色权限 |
| 个人中心 | 资料修改（昵称/专业/头像/改密）、我的收藏、我的课程（进度）、我的订单 |
| 课程资源 | 技术体系/方向/等级/免费多维筛选、综合/最新/学习人数/评分排序、课程名+讲师名搜索、课程详情、收藏、章节进度 |
| 学习社区 | 课程评价（一人一课一条）、回复与楼中楼、点赞 |
| AI 学习助手 | 智能答疑（多轮对话、课程上下文、课程资料 RAG 检索与引用）、学习路径推荐、作业批改（JSON 评分）、学习报告生成；无 Key 自动 Mock 兜底 |
| 实习就业 | 职位分类筛选、职位/公司搜索、职位详情、申请职位 |
| 后台管理 | 课程新建/编辑/删除与章节维护、讲师指派、账号启停、订单状态流转、用户/课程/订单/申请列表、平台统计（前端 `/admin` 页） |
| 通知提醒 | 站内通知（收藏课程更新、学习进度停滞提醒）、SSE 实时未读数（60s 轮询兜底）、顶栏未读角标、单条/全部已读 |
| 工程质量 | pytest 接口测试 57 项（行覆盖 90%）、统一响应与错误码、全局异常处理、健康检查 |

## 目录结构

```
├── docs/                     # 方案与交付文档模板
├── docker-compose.yml        # 容器编排（mysql + backend + nginx）
├── backend/
│   ├── app/
│   │   ├── main.py           # 应用入口
│   │   ├── config.py         # 环境配置
│   │   ├── models.py         # ORM 模型
│   │   ├── security.py       # PBKDF2 + JWT
│   │   ├── routers/          # auth/users/courses/jobs/ai/notifications/admin/meta
│   │   └── services/         # LLM 网关 + Mock 引擎 + Prompt + RAG 检索
│   ├── tests/                # pytest 接口测试
│   ├── seed.py               # 18 门课程 / 8 个职位 / 20 条课程资料
│   ├── seed_materials.py     # 幂等补资料（已有库升级用）
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── views/            # 登录、课程列表、课程详情、AI 助手、学习报告、职位、后台管理、个人中心
│       ├── layouts/          # 顶栏布局
│       ├── api/              # Axios 封装
│       └── stores/           # Pinia 用户态
└── .venv/                    # 本地虚拟环境（已在根目录创建）
```

## 快速启动

### 1. 后端

```bash
cd backend
../.venv/Scripts/python.exe seed.py                 # 初始化演示数据（Windows）
../.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
# 开发时可临时加 --reload；演示/验证请用 run.bat（无 reload，改代码后需重启）
```

Windows 也可以直接双击 `backend/run.bat`（或在项目根执行 `.\backend\run.bat`）：脚本会自动切到 `backend/`、用 `.venv` 启动 8000 端口，并在缺虚拟环境或端口被占用时给出提示。

首次在其他机器运行：

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r backend/requirements.txt
```

### 2. 前端

```bash
cd frontend
npm install --registry=https://registry.npmmirror.com   # 国内网络建议使用镜像
npm run dev        # http://localhost:5173
```

Vite 已配置 `/api` 代理到 `http://127.0.0.1:8000`，并监听 `0.0.0.0`，同一局域网内可用 `http://<本机IP>:5173` 访问，方便课堂演示。

### 3. Docker Compose（已在本机实测，需 WSL2）

```bash
cd frontend && npm run build && cd ..   # 前端镜像使用预构建 dist
cp .env.example .env                     # 按需修改 MySQL 密码、JWT、LLM Key
docker compose up -d --build
# 前端 http://localhost:8080，健康检查 http://localhost:8080/api/health
```

- 首次启动且 `users` 表为空时自动导入演示数据；已有数据不会覆盖（设 `SEED_ON_START=false` 可关闭）。
- 2026-11-24 实测：三容器 healthy，health 返回 `database=up`，演示账号可登录。
- 已有数据升级 RAG：`docker compose exec backend python seed_materials.py`（会写库，先确认）。
- 若 Docker Desktop 未运行，先启动并保持窗口；本机 Linux 引擎依赖 WSL2。

### 4. 演示账号（密码均为 `123456`）

| 角色 | 账号 | 邮箱 |
|---|---|---|
| 管理员 | admin | admin@zhixueyun.cn |
| 教师 | teacher_wang | wang@zhixueyun.cn |
| 教师 | teacher_li | li@zhixueyun.cn |
| 学生 | student | student@zhixueyun.cn |

## AI 双模式

默认 `LLM_API_KEY` 为空，四类 AI 功能走本地 Mock 引擎，**离线也能完整演示**。

接入真实模型（OpenAI 兼容协议，DeepSeek/通义/智谱/Moonshot 均可）：

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env：
LLM_API_KEY=sk-xxxx
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

任一调用失败会自动降级为 Mock，不影响演示。

## 切换 MySQL

```bash
# backend/.env
DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/zhixueyun?charset=utf8mb4
```

建库后执行 `python seed.py` 即可（SQLAlchemy 自动建表）。开发默认使用 SQLite，答辩环境建议 MySQL 8.0。

## 测试

```bash
cd backend
../.venv/Scripts/python.exe -m pytest tests -q
```

测试使用独立的 `backend/tests/test_zhixueyun.db`，不会污染演示数据。

## 常用接口速查

| 场景 | 接口 |
|---|---|
| 注册/登录 | `POST /api/auth/register`、`POST /api/auth/login` |
| 课程列表 | `GET /api/courses?tech_system=人工智能&level=beginner&sort=rating&keyword=Python` |
| 课程详情 | `GET /api/courses/1` |
| 收藏 | `POST /api/courses/1/favorite` |
| 学习进度 | `PUT /api/courses/1/progress` |
| 课程评论 | `GET/POST /api/courses/1/comments` |
| 回复/点赞 | `GET/POST /api/courses/1/comments/{commentId}/replies`、`POST /api/courses/1/comments/{commentId}/like` |
| AI 答疑 | `POST /api/ai/chat` |
| 学习路径 | `POST /api/ai/learning-path` |
| 作业批改 | `POST /api/ai/grade` |
| 学习报告 | `POST /api/ai/study-report` |
| 通知列表 | `GET /api/notifications`、`GET /api/notifications/unread-count` |
| 通知已读 | `POST /api/notifications/{id}/read`、`POST /api/notifications/read-all` |
| 通知流 | `GET /api/notifications/stream?token=<JWT>`（SSE，15s 推送未读数） |
| 我的订单 | `GET /api/users/me/orders` |
| 账号启停 | `PATCH /api/admin/users/{id}/status`（仅管理员） |
| 课程维护 | `POST/PUT/DELETE /api/admin/courses`、`POST /api/admin/courses/{id}/chapters` |
| 讲师与订单 | `GET /api/admin/teachers`、`PATCH /api/admin/orders/{id}/status` |
| 健康检查 | `GET /api/health` |

## 后续迭代建议（对应指导书 P1/P2）

1. 独立问答板块（当前由课程评论回复承载）
2. 订单支付流程（当前仅展示订单，未接支付通道）
3. SSE 流式输出
4. 前端容器内 npm 构建优化（当前使用宿主预构建 `dist` 规避容器内 npm 故障）
5. 移动端响应式适配（Element Plus 栅格 + 媒体查询）

## AI 工具使用声明

本样板由 AI 辅助生成，提交课程作业时请在实践报告中标注 AI 工具辅助范围（代码生成、文档润色等），并完成逐行 Review 与自测。