import json
import random
from datetime import UTC, datetime, timedelta

from app.database import Base, SessionLocal, engine
from app.models import (
    AiConversation,
    AiMessage,
    Chapter,
    Comment,
    Course,
    Favorite,
    Job,
    JobApplication,
    LearningRecord,
    Notification,
    Order,
    User,
)
from app.security import hash_password

random.seed(42)
PASSWORD = "123456"


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)

COURSES = [
    {
        "title": "Python 数据分析实战",
        "course_type": "theory",
        "tech_system": "人工智能",
        "tech_direction": "Python",
        "level": "beginner",
        "is_free": 1,
        "price": 0,
        "teacher": "王老师",
        "intro": "从 NumPy、pandas 到真实业务数据分析，零基础掌握数据分析全流程。",
        "description": "本课程以真实电商数据集为载体，讲解数据读取、清洗、聚合、可视化与报告输出的完整流程，帮助学员建立数据驱动的问题解决思路。",
        "objective": ["掌握 pandas 数据清洗与聚合", "独立完成探索性数据分析", "掌握 matplotlib 可视化", "输出一份规范的数据分析报告"],
        "rating": 4.8,
        "rating_count": 236,
        "study_count": 1203,
    },
    {
        "title": "Hadoop 大数据技术与应用",
        "course_type": "theory",
        "tech_system": "大数据",
        "tech_direction": "数据分析",
        "level": "intermediate",
        "is_free": 1,
        "price": 0,
        "teacher": "李老师",
        "intro": "理论 + 实践双线教学，掌握 HDFS、MapReduce 与 Hadoop 生态组件。",
        "description": "本课程以 Hadoop 大数据技术为核心，利用理论 + 实践的教学方式，注重培养学生们发散性思维和动手实践的能力。",
        "objective": ["搭建完全分布式 Hadoop 集群", "掌握 HDFS 与 MapReduce 原理", "完成 IDE 开发环境配置", "能够使用生态常用组件处理数据"],
        "rating": 4.6,
        "rating_count": 182,
        "study_count": 986,
    },
    {
        "title": "机器学习入门与实战",
        "course_type": "theory",
        "tech_system": "人工智能",
        "tech_direction": "前沿技术",
        "level": "beginner",
        "is_free": 1,
        "price": 0,
        "teacher": "王老师",
        "intro": "用 scikit-learn 打通分类、回归、聚类三大任务，建立机器学习思维。",
        "description": "课程从概念、原理到代码实践，配套 6 个真实数据集案例，帮助初学者理解模型评估与调优方法。",
        "objective": ["理解监督学习与无监督学习", "掌握 scikit-learn 常用 API", "能够完成模型训练与评估", "识别过拟合与欠拟合"],
        "rating": 4.7,
        "rating_count": 301,
        "study_count": 1532,
    },
    {
        "title": "深度学习与图像识别",
        "course_type": "theory",
        "tech_system": "人工智能",
        "tech_direction": "图像识别",
        "level": "advanced",
        "is_free": 0,
        "price": 199,
        "teacher": "王老师",
        "intro": "基于 PyTorch 的 CNN 实战，从图像分类到目标检测完整落地。",
        "description": "课程覆盖卷积神经网络、迁移学习、数据增强与模型部署，最终完成一个可上线的图像识别服务。",
        "objective": ["掌握 CNN 核心结构", "熟练使用 PyTorch 训练模型", "完成迁移学习实践", "部署图像识别推理服务"],
        "rating": 4.9,
        "rating_count": 168,
        "study_count": 864,
    },
    {
        "title": "语音识别技术应用",
        "course_type": "theory",
        "tech_system": "人工智能",
        "tech_direction": "语音识别",
        "level": "intermediate",
        "is_free": 0,
        "price": 159,
        "teacher": "王老师",
        "intro": "从声学特征到端到端模型，构建语音识别应用的技术全景。",
        "description": "介绍语音信号处理基础、MFCC 特征、CTC 与 Transformer 声学模型，并结合开源工具完成语音转写 Demo。",
        "objective": ["理解语音信号处理流程", "掌握特征提取方法", "了解端到端识别模型", "完成语音转写应用"],
        "rating": 4.5,
        "rating_count": 96,
        "study_count": 432,
    },
    {
        "title": "数据可视化与 BI 报表",
        "course_type": "theory",
        "tech_system": "大数据",
        "tech_direction": "数据可视化",
        "level": "beginner",
        "is_free": 1,
        "price": 0,
        "teacher": "李老师",
        "intro": "用 ECharts 与 BI 工具讲好数据故事，让报表会说话。",
        "description": "课程从可视化设计原则出发，结合 ECharts、Superset 等工具完成销售、运营、教学等多场景看板。",
        "objective": ["掌握图表选型原则", "熟练配置 ECharts 图表", "完成业务看板设计", "具备数据叙事能力"],
        "rating": 4.4,
        "rating_count": 121,
        "study_count": 745,
    },
    {
        "title": "云计算架构与运维",
        "course_type": "theory",
        "tech_system": "云计算",
        "tech_direction": "云原生",
        "level": "intermediate",
        "is_free": 0,
        "price": 129,
        "teacher": "李老师",
        "intro": "覆盖 IaaS 到云原生，掌握容器、Kubernetes 与高可用架构。",
        "description": "系统讲解云平台架构、虚拟化、容器编排与监控告警，配套实验环境完成一套容器化应用的部署。",
        "objective": ["理解云计算服务模型", "掌握 Docker 容器化", "能够部署 Kubernetes 集群", "设计基础高可用架构"],
        "rating": 4.6,
        "rating_count": 143,
        "study_count": 621,
    },
    {
        "title": "鸿蒙应用开发（ArkTS）",
        "course_type": "theory",
        "tech_system": "鸿蒙",
        "tech_direction": "移动应用",
        "level": "beginner",
        "is_free": 1,
        "price": 0,
        "teacher": "王老师",
        "intro": "ArkTS + ArkUI 从零开发 HarmonyOS 应用，打通端云一体能力。",
        "description": "面向鸿蒙生态入门者，讲解 ArkTS 语法、声明式 UI、状态管理、网络请求与打包上架全流程。",
        "objective": ["掌握 ArkTS 基础语法", "熟练使用 ArkUI 常用组件", "完成端云数据交互", "打包并运行 HAP 应用"],
        "rating": 4.8,
        "rating_count": 264,
        "study_count": 1105,
    },
    {
        "title": "通信网络基础",
        "course_type": "theory",
        "tech_system": "通信",
        "tech_direction": "前沿技术",
        "level": "beginner",
        "is_free": 1,
        "price": 0,
        "teacher": "李老师",
        "intro": "构建通信原理与网络协议的知识底座，为 5G 方向打基础。",
        "description": "介绍信号与系统基础、TCP/IP 协议栈、无线通信原理与 5G 网络架构，配套 Wireshark 抓包实验。",
        "objective": ["理解网络分层模型", "掌握 TCP/IP 协议分析", "了解 5G 网络架构", "完成抓包分析实验"],
        "rating": 4.3,
        "rating_count": 88,
        "study_count": 528,
    },
    {
        "title": "数通 HCIA 认证冲刺",
        "course_type": "certification",
        "tech_system": "数通",
        "tech_direction": "前沿技术",
        "level": "intermediate",
        "is_free": 0,
        "price": 299,
        "teacher": "李老师",
        "intro": "对标 HCIA-Datacom 考纲，理论串讲 + 题库精讲 + 实验强化。",
        "description": "围绕 HCIA-Datacom 考试大纲，系统梳理路由交换、网络安全与自动化基础，配套模拟题与实验手册。",
        "objective": ["覆盖 HCIA 考纲知识点", "掌握设备配置命令", "完成 10 个以上实验", "通过模拟考试"],
        "rating": 4.7,
        "rating_count": 112,
        "study_count": 399,
    },
    {
        "title": "HCIA-AI 认证课程",
        "course_type": "certification",
        "tech_system": "人工智能",
        "tech_direction": "前沿技术",
        "level": "intermediate",
        "is_free": 0,
        "price": 399,
        "teacher": "王老师",
        "intro": "华为 HCIA-AI 认证精讲，覆盖机器学习、深度学习与 MindSpore。",
        "description": "依据 HCIA-AI 认证大纲设计，包含数学基础、经典算法、深度学习框架与华为 AI 平台实践。",
        "objective": ["掌握认证核心考点", "熟悉 MindSpore 框架", "完成 3 个实验案例", "通过认证模拟测试"],
        "rating": 4.9,
        "rating_count": 205,
        "study_count": 678,
    },
    {
        "title": "大数据实训：电商用户行为分析",
        "course_type": "practice",
        "tech_system": "大数据",
        "tech_direction": "数据分析",
        "level": "intermediate",
        "is_free": 1,
        "price": 0,
        "teacher": "李老师",
        "intro": "以电商日志为数据源，完成从采集、清洗到指标看板的完整实训。",
        "description": "实训项目还原企业真实数据处理链路，学员分组完成数据采集、离线统计、漏斗分析与可视化汇报。",
        "objective": ["完成数据采集与清洗", "掌握离线统计流程", "设计用户行为漏斗", "输出分析看板与报告"],
        "rating": 4.7,
        "rating_count": 134,
        "study_count": 512,
    },
    {
        "title": "人工智能实训：智能客服问答机器人",
        "course_type": "practice",
        "tech_system": "人工智能",
        "tech_direction": "前沿技术",
        "level": "advanced",
        "is_free": 0,
        "price": 259,
        "teacher": "王老师",
        "intro": "基于大模型 API 构建企业级智能客服，覆盖 RAG、意图识别与评测。",
        "description": "以真实客服场景为背景，完成知识库构建、RAG 检索增强、多轮对话管理与效果评测的全流程实训。",
        "objective": ["搭建知识库与向量检索", "实现 RAG 问答链", "完成多轮对话设计", "产出评测报告"],
        "rating": 4.8,
        "rating_count": 87,
        "study_count": 733,
    },
    {
        "title": "云计算实训：容器化部署实战",
        "course_type": "practice",
        "tech_system": "云计算",
        "tech_direction": "云原生",
        "level": "intermediate",
        "is_free": 1,
        "price": 0,
        "teacher": "李老师",
        "intro": "把一个前后端分离项目完整容器化并部署到云服务器。",
        "description": "实训围绕 Dockerfile 编写、Compose 编排、Nginx 反向代理与 HTTPS 配置展开，最终交付可访问的部署环境。",
        "objective": ["编写规范 Dockerfile", "使用 Compose 编排服务", "配置 Nginx 反向代理", "完成上线与回滚演练"],
        "rating": 4.5,
        "rating_count": 76,
        "study_count": 468,
    },
    {
        "title": "Python Web 开发（FastAPI）",
        "course_type": "theory",
        "tech_system": "人工智能",
        "tech_direction": "Python",
        "level": "intermediate",
        "is_free": 1,
        "price": 0,
        "teacher": "王老师",
        "intro": "用 FastAPI 快速构建规范、可文档化的 RESTful 服务。",
        "description": "课程覆盖路由、依赖注入、Pydantic 校验、JWT 鉴权与数据库集成，并完成一个博客 API 项目。",
        "objective": ["掌握 FastAPI 核心用法", "设计 RESTful 接口", "实现 JWT 鉴权", "完成 API 项目部署"],
        "rating": 4.6,
        "rating_count": 198,
        "study_count": 889,
    },
    {
        "title": "互联网运营与增长",
        "course_type": "theory",
        "tech_system": "人工智能",
        "tech_direction": "互联网运营",
        "level": "beginner",
        "is_free": 1,
        "price": 0,
        "teacher": "李老师",
        "intro": "理解用户增长、内容运营与数据复盘的底层方法。",
        "description": "从 AARRR 模型出发，讲解用户分层、活动策划、内容运营与数据复盘的完整方法论。",
        "objective": ["掌握 AARRR 增长模型", "能够设计运营活动", "建立数据复盘机制", "完成一份运营方案"],
        "rating": 4.2,
        "rating_count": 64,
        "study_count": 356,
    },
    {
        "title": "工业软件与数字孪生",
        "course_type": "theory",
        "tech_system": "工业软件",
        "tech_direction": "前沿技术",
        "level": "advanced",
        "is_free": 0,
        "price": 189,
        "teacher": "王老师",
        "intro": "走进工业软件与数字孪生，理解智能制造的技术底座。",
        "description": "介绍 CAD/CAE/CAM 体系、工业数据采集与数字孪生建模，结合案例讲解制造业数字化转型路径。",
        "objective": ["理解工业软件体系", "掌握数字孪生基本概念", "了解工业数据采集", "完成案例分析报告"],
        "rating": 4.4,
        "rating_count": 42,
        "study_count": 215,
    },
    {
        "title": "专业共建：AI 工程实践",
        "course_type": "theory",
        "tech_system": "人工智能",
        "tech_direction": "前沿技术",
        "level": "co_build",
        "is_free": 1,
        "price": 0,
        "teacher": "王老师",
        "intro": "校企共建课程，按企业真实项目标准完成 AI 应用交付。",
        "description": "由企业工程师参与授课，按企业研发流程完成需求、设计、开发、测试与部署，训练工程化协作能力。",
        "objective": ["掌握企业研发流程", "完成团队项目交付", "通过代码评审", "完成项目答辩"],
        "rating": 4.9,
        "rating_count": 58,
        "study_count": 301,
    },
]

CHAPTER_TEMPLATES = {
    "人工智能": [
        ("课程导学与开发环境搭建", "video", 35),
        ("核心概念与算法原理", "video", 50),
        ("典型应用案例解析", "doc", 40),
        ("项目实战：端到端应用开发", "lab", 90),
        ("课程总结与能力测评", "video", 30),
    ],
    "大数据": [
        ("大数据技术生态概览", "video", 40),
        ("HDFS 与 MapReduce 原理", "video", 55),
        ("Spark 数据处理实战", "lab", 80),
        ("数仓分层建模案例", "doc", 45),
        ("综合项目与答辩", "lab", 100),
    ],
    "云计算": [
        ("云平台架构概览", "video", 40),
        ("容器与 Kubernetes 基础", "video", 50),
        ("CI/CD 流水线实践", "doc", 40),
        ("云原生项目实战", "lab", 90),
        ("课程总结与测评", "video", 30),
    ],
    "鸿蒙": [
        ("ArkTS 语言基础", "video", 45),
        ("ArkUI 布局与状态管理", "video", 50),
        ("网络请求与数据存储", "doc", 40),
        ("综合项目开发", "lab", 100),
        ("打包上架与验收", "video", 35),
    ],
    "通信": [
        ("通信网络基础概念", "video", 40),
        ("TCP/IP 协议分析", "video", 50),
        ("Wireshark 抓包实验", "lab", 70),
        ("5G 网络架构案例", "doc", 40),
        ("课程总结与测评", "video", 30),
    ],
    "数通": [
        ("路由交换基础", "video", 45),
        ("设备配置与调试", "lab", 80),
        ("网络安全基础", "video", 45),
        ("自动化运维入门", "doc", 35),
        ("认证模拟测试", "lab", 60),
    ],
    "工业软件": [
        ("工业软件体系概览", "video", 40),
        ("数字孪生建模方法", "video", 50),
        ("工业数据采集案例", "doc", 40),
        ("仿真项目实践", "lab", 90),
        ("课程总结与案例答辩", "video", 30),
    ],
}

JOBS = [
    {
        "title": "Python 后端开发工程师",
        "category": "技术",
        "company": "深圳昂楷信息技术有限公司",
        "salary": "10-18K",
        "city": "深圳",
        "address": "南山区科技园",
        "headcount": 3,
        "description": "负责教育平台后端服务开发，参与接口设计、性能优化与线上运维。",
        "requirement": "1. 熟悉 Python 与 FastAPI/Django；2. 熟悉 MySQL 与 Redis；3. 了解 Docker 部署；4. 有良好的代码规范意识。",
    },
    {
        "title": "前端开发工程师（Vue3）",
        "category": "技术",
        "company": "广州云智科技有限公司",
        "salary": "8-15K",
        "city": "广州",
        "address": "天河区珠江新城",
        "headcount": 2,
        "description": "负责教育类 SaaS 产品的前端开发与体验优化，与后端协作完成接口联调。",
        "requirement": "1. 熟悉 Vue3 + Pinia；2. 熟练使用 Element Plus；3. 了解前端工程化与性能优化；4. 有上线项目经验优先。",
    },
    {
        "title": "大数据开发工程师",
        "category": "技术",
        "company": "华为技术有限公司",
        "salary": "15-25K",
        "city": "东莞",
        "address": "松山湖基地",
        "headcount": 5,
        "description": "负责数据平台离线与实时链路的开发，支撑业务数据分析需求。",
        "requirement": "1. 熟悉 Hadoop/Spark/Flink；2. 熟练编写 SQL 与数据建模；3. 了解数据治理；4. 具备良好的问题定位能力。",
    },
    {
        "title": "AI 算法工程师（NLP）",
        "category": "技术",
        "company": "深圳智慧星光科技有限公司",
        "salary": "18-30K",
        "city": "深圳",
        "address": "福田区车公庙",
        "headcount": 2,
        "description": "负责大模型应用落地，包括 RAG 检索增强、对话系统与效果评测。",
        "requirement": "1. 熟悉 Python 与主流深度学习框架；2. 了解 Transformer 与 LLM 微调；3. 有 RAG 项目经验优先；4. 硕士优先。",
    },
    {
        "title": "技术支持工程师（偏售前）",
        "category": "技术",
        "company": "深圳昂楷信息技术有限公司",
        "salary": "8-12K",
        "city": "福州",
        "address": "鼓楼区宁德大厦1302",
        "headcount": 2,
        "description": "负责教育行业客户的技术方案支持、产品演示与实施交付，需接受短期出差。",
        "requirement": "1. 计算机相关专业本科；2. 熟悉 Linux 与数据库基础操作；3. 具备良好的沟通表达能力；4. 可接受出差。",
    },
    {
        "title": "产品经理（教育 SaaS）",
        "category": "产品",
        "company": "广州学而思教育科技有限公司",
        "salary": "12-20K",
        "city": "广州",
        "address": "越秀区中山五路",
        "headcount": 1,
        "description": "负责教育 SaaS 产品的需求分析与版本规划，推动跨团队协作落地。",
        "requirement": "1. 2 年以上 B 端产品经验；2. 熟悉原型工具与需求文档；3. 有教育行业经验优先。",
    },
    {
        "title": "UI/UX 设计师",
        "category": "设计",
        "company": "珠海横琴数字创意有限公司",
        "salary": "8-14K",
        "city": "珠海",
        "address": "横琴新区环岛东路",
        "headcount": 1,
        "description": "负责教育平台 Web 与移动端界面设计，参与设计规范建设。",
        "requirement": "1. 熟练使用 Figma；2. 具备完整的 B 端项目作品；3. 理解交互设计原则；4. 有动效能力加分。",
    },
    {
        "title": "鸿蒙应用开发工程师",
        "category": "技术",
        "company": "华为终端有限公司",
        "salary": "15-28K",
        "city": "深圳",
        "address": "龙岗区坂田华为基地",
        "headcount": 4,
        "description": "负责 HarmonyOS 应用开发与性能优化，参与端云一体化方案设计。",
        "requirement": "1. 熟悉 ArkTS 与 ArkUI；2. 了解 HarmonyOS 应用生命周期；3. 具备移动端开发经验；4. 有鸿蒙应用上架经验优先。",
    },
]


def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def build_users(db):
    users = {
        "admin": User(
            username="admin",
            email="admin@zhixueyun.cn",
            hashed_password=hash_password(PASSWORD),
            nickname="平台管理员",
            major="教育技术",
            role="admin",
        ),
        "teacher_wang": User(
            username="teacher_wang",
            email="wang@zhixueyun.cn",
            hashed_password=hash_password(PASSWORD),
            nickname="王老师",
            major="人工智能",
            role="teacher",
        ),
        "teacher_li": User(
            username="teacher_li",
            email="li@zhixueyun.cn",
            hashed_password=hash_password(PASSWORD),
            nickname="李老师",
            major="大数据",
            role="teacher",
        ),
        "student": User(
            username="student",
            email="student@zhixueyun.cn",
            hashed_password=hash_password(PASSWORD),
            nickname="陈同学",
            major="计算机科学与技术",
            role="student",
        ),
    }
    db.add_all(users.values())
    db.flush()
    return users


def build_courses(db, users):
    now = utcnow()
    courses = []
    chapter_map = {}
    for index, data in enumerate(COURSES):
        teacher_key = "teacher_wang" if data["teacher"] == "王老师" else "teacher_li"
        course = Course(
            title=data["title"],
            cover="",
            course_type=data["course_type"],
            tech_system=data["tech_system"],
            tech_direction=data["tech_direction"],
            level=data["level"],
            is_free=data["is_free"],
            price=float(data["price"]),
            teacher_id=users[teacher_key].id,
            intro=data["intro"],
            description=data["description"],
            objective=json.dumps(data["objective"], ensure_ascii=False),
            rating=float(data["rating"]),
            rating_count=data["rating_count"],
            study_count=data["study_count"],
            status="published",
            created_at=now - timedelta(days=index * 3),
        )
        db.add(course)
        courses.append(course)
    db.flush()
    for course in courses:
        template = CHAPTER_TEMPLATES.get(
            course.tech_system,
            [
                ("课程导学", "video", 35),
                ("核心概念讲解", "video", 50),
                ("典型案例解析", "doc", 40),
                ("项目实战", "lab", 90),
                ("总结与测评", "video", 30),
            ],
        )
        chapters = []
        for sort, (title, content_type, duration) in enumerate(template, start=1):
            chapter = Chapter(
                course_id=course.id,
                title=title,
                content_type=content_type,
                duration_min=duration,
                sort=sort,
            )
            db.add(chapter)
            chapters.append(chapter)
        chapter_map[course.id] = chapters
    db.flush()
    return courses, chapter_map


def build_jobs(db):
    db.add_all(
        [
            Job(
                title=data["title"],
                category=data["category"],
                company=data["company"],
                salary=data["salary"],
                city=data["city"],
                address=data["address"],
                headcount=data["headcount"],
                description=data["description"],
                requirement=data["requirement"],
                status="published",
            )
            for data in JOBS
        ]
    )


def build_demo_records(db, users, courses, chapter_map):
    student = users["student"]
    demo_progress = [
        (courses[0], 3, 320),
        (courses[2], 2, 180),
        (courses[7], 5, 260),
    ]
    for course, completed_count, minutes in demo_progress:
        completed = [chapter.id for chapter in chapter_map[course.id][:completed_count]]
        total = len(chapter_map[course.id])
        db.add(
            LearningRecord(
                user_id=student.id,
                course_id=course.id,
                progress=round(len(completed) / total * 100),
                study_minutes=minutes,
                completed_chapters=json.dumps(completed),
                last_chapter_id=completed[-1] if completed else None,
                updated_at=utcnow() - timedelta(days=random.randint(0, 5)),
            )
        )
    db.add_all(
        [
            Favorite(user_id=student.id, course_id=courses[0].id),
            Favorite(user_id=student.id, course_id=courses[7].id),
        ]
    )
    db.add(
        Order(
            order_no="ZX20261101001",
            user_id=student.id,
            course_id=courses[3].id,
            amount=199.0,
            status="paid",
            created_at=utcnow() - timedelta(days=12),
        )
    )
    db.add_all(
        [
            Comment(course_id=courses[0].id, user_id=student.id, rating=5, content="老师讲得很清楚，示例数据也很真实。"),
            Comment(course_id=courses[1].id, user_id=users["teacher_wang"].id, rating=4, content="课程结构完整，建议补充集群调优案例。"),
        ]
    )
    db.add_all(
        [
            Notification(
                user_id=student.id,
                type="system",
                title="欢迎来到智学云",
                content="完善专业信息后，AI 学习助手会给出更贴合的学习路径。",
                link="/report",
                is_read=1,
                created_at=utcnow() - timedelta(days=3),
            ),
            Notification(
                user_id=student.id,
                type="course_update",
                title=f"《{courses[0].title}》新增实验章节",
                content="补充了「pandas 时间序列」实验，建议从第 4 章继续学习。",
                link=f"/courses/{courses[0].id}",
                created_at=utcnow() - timedelta(days=1),
            ),
        ]
    )
    conversation = AiConversation(
        user_id=student.id,
        course_id=courses[0].id,
        title="pandas 分组聚合怎么用？",
    )
    db.add(conversation)
    db.flush()
    db.add_all(
        [
            AiMessage(conversation_id=conversation.id, role="user", content="pandas 分组聚合怎么用？"),
            AiMessage(
                conversation_id=conversation.id,
                role="assistant",
                content="用 groupby 先分组，再通过 agg 聚合，例如 df.groupby('city')['sales'].sum()。知识点拓展：可以了解 pivot_table 的透视表用法。",
            ),
        ]
    )


def main():
    reset_database()
    db = SessionLocal()
    try:
        users = build_users(db)
        courses, chapter_map = build_courses(db, users)
        build_jobs(db)
        build_demo_records(db, users, courses, chapter_map)
        db.commit()
        print("种子数据初始化完成")
        print(f"课程 {len(courses)} 门，职位 {len(JOBS)} 个")
        print("演示账号（密码均为 123456）：")
        print("  管理员  admin / admin@zhixueyun.cn")
        print("  教师    teacher_wang / wang@zhixueyun.cn")
        print("  教师    teacher_li / li@zhixueyun.cn")
        print("  学生    student / student@zhixueyun.cn")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()