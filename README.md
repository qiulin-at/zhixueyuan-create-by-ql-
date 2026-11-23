# 智学云 · 面向教育平台的智能体开发（项目二样板）

华为 ICT 学院《基于 Python 的 AI 项目实践》课程项目二的可运行样板工程。
技术栈：**FastAPI + SQLAlchemy + MySQL/SQLite + Vue3 + Vite + Element Plus + OpenAI 兼容大模型（Mock 兜底）**。

- 方案与文档：[docs/01-项目方案设计.md](docs/01-项目方案设计.md)
- 需求/架构/答辩/项目管理模板：`docs/02` ~ `docs/05`
- 接口文档（运行后）：<http://127.0.0.1:8000/docs>

## 已实现功能

| 模块 | 功能 |
|---|---|
| 用户系统 | 注册、登录（JWT）、密码重置（演示验证码）、个人资料修改、三角色权限 |
| 课程资源 | 技术体系/方向/等级/免费多维筛选、综合/最新/学习人数/评分排序、课程名+讲师名搜索、课程详情、收藏、章节进度 |
| AI 学习助手 | 智能答疑（多轮对话、课程上下文）、学习路径推荐、作业批改（JSON 评分）、学习报告生成；无 Key 自动 Mock 兜底 |
| 实习就业 | 职位分类筛选、职位/公司搜索、职位详情、申请职位 |
| 后台管理 | 用户列表与角色调整、课程上下架（教师只能管本人课程）、订单/职位申请列表、平台统计（前端 `/admin` 页） |
| 通知提醒 | 站内通知（收藏课程更新、学习进度停滞提醒）、顶栏未读角标、单条/全部已读 |
| 工程质量 | pytest 接口测试 37 项（行覆盖 89%）、统一响应与错误码、全局异常处理、健康检查 |

## 目录结构

```
├── docs/                     # 方案与交付文档模板
├── backend/
│   ├── app/
│   │   ├── main.py           # 应用入口
│   │   ├── config.py         # 环境配置
│   │   ├── models.py         # ORM 模型
│   │   ├── security.py       # PBKDF2 + JWT
│   │   ├── routers/          # auth/users/courses/jobs/ai/notifications/admin/meta
│   │   └── services/         # LLM 网关 + Mock 引擎 + Prompt
│   ├── tests/                # pytest 接口测试
│   ├── seed.py               # 18 门课程 / 8 个职位演示数据
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── views/            # 登录、课程列表、课程详情、AI 助手、学习报告、职位、后台管理
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
../.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
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

### 3. 演示账号（密码均为 `123456`）

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
| AI 答疑 | `POST /api/ai/chat` |
| 学习路径 | `POST /api/ai/learning-path` |
| 作业批改 | `POST /api/ai/grade` |
| 学习报告 | `POST /api/ai/study-report` |
| 通知列表 | `GET /api/notifications`、`GET /api/notifications/unread-count` |
| 通知已读 | `POST /api/notifications/{id}/read`、`POST /api/notifications/read-all` |
| 健康检查 | `GET /api/health` |

## 后续迭代建议（对应指导书 P1/P2）

1. 评论/问答社区（回复、点赞）、SSE 实时通知（当前通知为 60s 轮询）
2. 订单支付流程与个人中心订单展示
3. Dancer/SSE 流式输出、RAG 课程资料检索与引用
4. Docker Compose 一键部署 + Nginx 反向代理
5. 移动端响应式适配（Element Plus 栅格 + 媒体查询）

## AI 工具使用声明

本样板由 AI 辅助生成，提交课程作业时请在实践报告中标注 AI 工具辅助范围（代码生成、文档润色等），并完成逐行 Review 与自测。