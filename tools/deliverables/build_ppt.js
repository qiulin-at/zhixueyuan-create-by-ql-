const PptxGenJS = require('pptxgenjs');

const F = 'Microsoft YaHei';
const TEAL = '0E7490';
const AMBER = 'F59E0B';
const DARK = '0F172A';
const MUTED = '94A3B8';
const BORDER = 'E2E8F0';
const LIGHT = 'E0F2FE';
const BG = 'F8FAFC';
const WHITE = 'FFFFFF';
const RED = 'DC2626';
const GREEN = '059669';
const TOTAL = 18;

const prs = new PptxGenJS();
prs.defineLayout({ name: 'CUSTOM', width: 10, height: 5.625 });
prs.layout = 'CUSTOM';
prs.author = '邱麟';
prs.company = '华为 ICT 学院';
prs.title = '智学云 · 面向教育平台的智能体开发（答辩 PPT）';
prs.subject = '项目二：面向教育平台的智能体开发 — 一期交付 + 二期优化提升方案';

function rect(s, x, y, w, h, color, radius) {
  s.addShape(radius ? prs.ShapeType.roundRect : prs.ShapeType.rect, {
    x, y, w, h, rectRadius: radius || 0,
    fill: { color }, line: { color, width: 0.5 },
  });
}

function card(s, x, y, w, h, fillColor, lineColor) {
  s.addShape(prs.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.03,
    fill: { color: fillColor || WHITE },
    line: { color: lineColor || BORDER, width: 0.75 },
  });
}

function txt(s, str, x, y, w, h, size, color, bold, align, valign) {
  s.addText(str, {
    x, y, w, h, fontFace: F, fontSize: size,
    color: color || DARK, bold: !!bold,
    align: align || 'left', valign: valign || 'top',
    margin: 0, breakLine: false,
  });
}

function contentSlide(kicker, title, page, tag) {
  const s = prs.addSlide();
  s.background = { color: BG };
  rect(s, 0, 0, 0.11, 5.625, TEAL);
  txt(s, kicker, 0.55, 0.27, 8.9, 0.22, 9.5, TEAL, true);
  txt(s, title, 0.55, 0.49, 8.9, 0.45, 25, DARK, true);
  if (tag) {
    s.addShape(prs.ShapeType.roundRect, {
      x: 7.90, y: 0.52, w: 1.50, h: 0.28, rectRadius: 0.06,
      fill: { color: LIGHT }, line: { color: 'BAE6FD', width: 0.5 },
    });
    txt(s, tag, 7.90, 0.52, 1.50, 0.28, 7.5, TEAL, true, 'center', 'middle');
  }
  txt(s, '智学云 · 面向教育平台的智能体  |  邱麟  |  2026-11-27', 0.55, 5.29, 7.4, 0.2, 8, MUTED);
  txt(s, String(page).padStart(2, '0') + ' / ' + TOTAL, 8.85, 5.29, 0.65, 0.2, 8, MUTED, false, 'right');
  return s;
}

/* ================= 1 封面 ================= */
{
  const s = prs.addSlide();
  s.background = { color: DARK };
  s.addShape(prs.ShapeType.ellipse, { x: 7.0, y: -1.35, w: 4.4, h: 4.4, fill: { color: TEAL, transparency: 86 }, line: { color: TEAL, transparency: 86 } });
  s.addShape(prs.ShapeType.ellipse, { x: 8.35, y: 2.55, w: 2.3, h: 2.3, fill: { color: AMBER, transparency: 88 }, line: { color: AMBER, transparency: 88 } });
  rect(s, 0.72, 1.18, 0.08, 2.55, AMBER);
  txt(s, '华为 ICT 学院 · 《基于 Python 的 AI 项目实践》项目二', 0.98, 0.90, 8.0, 0.30, 12, 'CBD5E1');
  txt(s, '智学云', 0.95, 1.28, 5.8, 0.98, 54, WHITE, true);
  txt(s, '面向教育平台的智能体开发', 0.98, 2.33, 6.8, 0.48, 24, LIGHT);
  txt(s, '用户 · 课程 · AI 学习助手 · 实习就业 · 后台管理', 0.98, 2.97, 6.8, 0.30, 11.5, '94A3B8');
  txt(s, 'FastAPI  ×  Vue 3  ×  OpenAI 兼容大模型（Mock 兜底）', 0.98, 3.48, 7.2, 0.30, 11.5, AMBER, true);
  rect(s, 0.72, 4.50, 4.5, 0.01, '475569');
  txt(s, '答辩人：邱麟  /  202502210379', 0.72, 4.70, 4.4, 0.26, 10.5, 'CBD5E1');
  txt(s, '2026-11-27', 0.72, 4.96, 3.0, 0.24, 10.5, 'CBD5E1');
  txt(s, '一期已交付：8 页面 · 45 路径 · 57 测试', 6.25, 4.62, 3.40, 0.22, 8.5, '94A3B8', false, 'right');
  txt(s, '二期方案：27 表 · 79 路径 · 100+ 测试', 6.25, 4.88, 3.40, 0.22, 8.5, AMBER, true, 'right');
}

/* ================= 2 团队与分工 ================= */
{
  const s = contentSlide('TEAM & OWNERSHIP', '团队与分工', 2, '1 人全栈 · 100%');
  card(s, 0.55, 1.12, 5.15, 2.35);
  rect(s, 0.80, 1.35, 0.95, 0.95, TEAL, 0.12);
  txt(s, '邱', 0.80, 1.35, 0.95, 0.95, 26, WHITE, true, 'center', 'middle');
  txt(s, '邱麟', 1.95, 1.31, 3.45, 0.30, 14, DARK, true);
  txt(s, '202502210379  ·  全栈开发 + 项目经理', 1.95, 1.65, 3.45, 0.24, 9.5, '475569');
  txt(s, '贡献占比 100%  ·  独立完成全链路', 1.95, 1.93, 3.45, 0.24, 9.5, '475569');
  rect(s, 0.80, 2.28, 4.60, 0.005, BORDER);
  const roles = [['PM', '需求 / 进度 / 文档 / 答辩'], ['前端', '8 页面 / 交互 / 联调 / 可视化'], ['后端', '8 router / 45 路径 / 16 表'], ['AI+测试', '4 项 AI / 57 用例 / 部署']];
  roles.forEach((r, i) => {
    const y = 2.40 + i * 0.24;
    rect(s, 0.82, y + 0.05, 0.11, 0.11, AMBER, 0.03);
    txt(s, r[0], 1.02, y, 0.90, 0.20, 9, TEAL, true);
    txt(s, r[1], 1.90, y, 3.50, 0.20, 9, '334155');
  });
  const stats = [['8', '页面'], ['45', '接口路径'], ['16', '数据表'], ['57', '测试用例'], ['90%', '行覆盖率'], ['3', '容器']];
  stats.forEach((v, i) => {
    const x = 5.95 + (i % 2) * 1.72;
    const y = 1.12 + Math.floor(i / 2) * 0.78;
    card(s, x, y, 1.62, 0.68);
    txt(s, v[0], x + 0.12, y + 0.07, 1.38, 0.34, 18, TEAL, true, 'center');
    txt(s, v[1], x + 0.12, y + 0.44, 1.38, 0.18, 8, MUTED, false, 'center');
  });
  card(s, 0.55, 3.62, 8.85, 1.32);
  txt(s, '一人全栈的取舍', 0.78, 3.75, 3.00, 0.24, 10, DARK, true);
  const cols = [['冻结范围', 'P0/P1/P2 分层，先闭环再加分项'], ['小步交付', '任务 ≤ 2 天，每批测试 + 构建'], ['可验证', '真实接口请求 + Docker 实测，不伪造']];
  cols.forEach((c, i) => {
    txt(s, c[0], 0.78 + i * 2.85, 4.08, 2.70, 0.22, 9, TEAL, true);
    txt(s, c[1], 0.78 + i * 2.85, 4.32, 2.70, 0.22, 8.5, '475569');
  });
}

/* ================= 3 需求与范围 ================= */
{
  const s = contentSlide('REQUIREMENTS & SCOPE', '需求洞察与范围', 3, '一期交付 → 二期提升');
  const pains = [['01', '学习路径不清晰', '不知道先学什么、学到什么程度'], ['02', '答疑等待久', '课后问题无人即时响应'], ['03', '学岗脱节', '课程内容与岗位要求对不上']];
  pains.forEach((p, i) => {
    const x = 0.55 + i * 2.95;
    card(s, x, 1.12, 2.85, 1.00);
    rect(s, x + 0.15, 1.27, 0.30, 0.30, LIGHT, 0.06);
    txt(s, p[0], x + 0.15, 1.27, 0.30, 0.30, 8, TEAL, true, 'center', 'middle');
    txt(s, p[1], x + 0.55, 1.24, 2.15, 0.24, 10, DARK, true);
    txt(s, p[2], x + 0.55, 1.55, 2.15, 0.35, 8.5, '475569');
  });
  txt(s, '范围演进：一期跑通闭环，二期按优化指导书提升', 0.55, 2.24, 5.50, 0.24, 10, DARK, true);
  const scopes = [
    ['一期 P0/P1/P2', '用户 / 课程 / 后台', 'AI 四功能 / 职位 / 社区', TEAL],
    ['二期 阶段一', '角色审计 / 课程资源', '学习事件 / 报名 / 作业', AMBER],
    ['二期 阶段二', 'RAG 可信闭环 / 路径 2.0', '批改沙箱 / 报告 2.0', AMBER],
    ['二期 阶段三/四', '职位收藏 / AI 面试', '举报审核 / 提醒偏好', AMBER],
  ];
  scopes.forEach((sc, i) => {
    const x = 0.55 + i * 2.25;
    card(s, x, 2.52, 2.12, 1.28);
    txt(s, sc[0], x + 0.12, 2.62, 1.90, 0.22, 9, sc[3], true);
    txt(s, sc[1], x + 0.12, 2.94, 1.88, 0.34, 8.5, DARK, true);
    txt(s, sc[2], x + 0.12, 3.32, 1.88, 0.38, 8, '475569');
  });
  card(s, 0.55, 3.95, 8.85, 0.90);
  txt(s, '本期不做（主动裁剪）', 0.76, 4.05, 2.50, 0.22, 9.5, DARK, true);
  txt(s, '真实支付  ·  离线推送  ·  向量数据库  ·  独立 App  ·  生产级 OJ  ·  招聘结论', 0.76, 4.33, 8.40, 0.24, 8.5, '475569');
  txt(s, '二期只做指导书明确要求的可信闭环；无法安全执行代码时降级并如实标注', 0.76, 4.58, 8.40, 0.20, 8, MUTED);
}

/* ================= 4 解决方案总览 ================= */
{
  const s = contentSlide('SOLUTION OVERVIEW', '解决方案总览', 4, '分层架构 + 二期增量');
  const layers = [
    ['客户端', 'Vue 3 + Vite + Element Plus + Pinia　｜　一期 8 页 → 二期 10 页'],
    ['API 层', 'FastAPI　｜　一期 8 router / 45 路径 → 二期 11 router / 约 79 路径'],
    ['服务层', 'LLM 网关 · RAG 检索 · 通知 · 安全　→　新增沙箱 / Rubric / 审计 / 路径规划'],
    ['数据层', 'SQLAlchemy 2.x　｜　一期 16 表 → 二期 27 表（新增事件/作业/路径/收藏/面试）'],
    ['部署', 'Docker Compose · MySQL + Backend + Nginx　｜　沙箱复用 Docker 一次性容器'],
  ];
  layers.forEach((l, i) => {
    const y = 1.13 + i * 0.72;
    card(s, 0.55, y, 6.00, 0.62);
    txt(s, l[0], 0.72, y + 0.07, 1.10, 0.22, 9, TEAL, true);
    txt(s, l[1], 1.80, y + 0.05, 4.55, 0.52, 8.5, DARK);
  });
  const picks = [['FastAPI', '自动 OpenAPI，接口文档即契约'], ['Vue 3', '组合式 API，页面开发效率高'], ['LLM 网关', '屏蔽厂商差异，统一鉴权与降级'], ['SQLite/MySQL', '演示零依赖，生产可切换']];
  picks.forEach((p, i) => {
    const y = 1.13 + i * 0.85;
    card(s, 6.78, y, 2.62, 0.74);
    txt(s, p[0], 6.92, y + 0.07, 2.35, 0.22, 9.5, DARK, true);
    txt(s, p[1], 6.92, y + 0.32, 2.35, 0.34, 8, '475569');
  });
  txt(s, '一期：8 router · 45 路径 / 53 操作 · 16 表 · 3 容器　　二期规划：+3 router · 约 79 路径 · 27 表 · 10 页面', 0.55, 4.95, 8.90, 0.22, 8.5, MUTED);
}

/* ================= 5 LLM 网关 ================= */
{
  const s = contentSlide('CORE INNOVATION', '核心创新 —— LLM 双模式网关', 5, '一期已实现');
  const nodes = [
    [0.55, 1.40, '业务请求', '课程上下文\n多轮会话', TEAL],
    [2.78, 1.40, 'LLM 网关', 'OpenAI 兼容\n统一鉴权', TEAL],
    [5.05, 0.95, '真实模型', 'DeepSeek / 通义\n智谱 / Moonshot', GREEN],
    [5.05, 1.95, 'Mock 引擎', '无 Key / 断网\n超时兜底', AMBER],
    [7.55, 1.40, '统一响应', '{code, message, data}\n业务无感', TEAL],
  ];
  nodes.forEach(n => {
    card(s, n[0], n[1], 1.78, 0.72);
    txt(s, n[2], n[0] + 0.12, n[1] + 0.08, 1.54, 0.22, 9, n[4], true, 'center');
    txt(s, n[3], n[0] + 0.12, n[1] + 0.32, 1.54, 0.34, 7.5, '475569', false, 'center');
  });
  txt(s, '→', 2.42, 1.55, 0.33, 0.30, 14, MUTED, true);
  txt(s, '→', 4.70, 1.00, 0.33, 0.30, 14, MUTED, true);
  txt(s, '→', 4.70, 2.05, 0.33, 0.30, 14, MUTED, true);
  txt(s, '→', 6.90, 1.55, 0.33, 0.30, 14, MUTED, true);
  txt(s, '在线失败 → 捕获异常 → Mock 返回 → 业务无感', 0.55, 2.72, 4.30, 0.24, 9, '475569');
  const adv = [['一套代码', '兼容 DeepSeek / 通义 / 智谱 / Moonshot'], ['自动降级', '断网、超时、无 Key 均不阻断演示'], ['可解释', '回答附 RAG 引用，Mock 也有课程上下文']];
  adv.forEach((a, i) => {
    const x = 0.55 + i * 2.98;
    card(s, x, 3.10, 2.85, 0.95);
    txt(s, a[0], x + 0.16, 3.20, 2.55, 0.24, 10, DARK, true);
    txt(s, a[1], x + 0.16, 3.48, 2.55, 0.40, 8.5, '475569');
  });
  card(s, 0.55, 4.25, 8.85, 0.62);
  txt(s, '演示价值：拔掉 Key 或断网，AI 答疑、学习路径、作业批改、学习报告仍可完整演示。', 0.75, 4.42, 8.45, 0.25, 9, DARK);
}

/* ================= 6 演示 1 ================= */
{
  const s = contentSlide('DEMO 01 · 90s', '演示 1 —— 课程发现与学习闭环', 6, '现场演示 90 秒');
  const steps = [
    ['1', '三维筛选', '技术体系 / 方向 / 等级 / 免费'],
    ['2', '四维排序', '综合 / 最新 / 学习人数 / 评分'],
    ['3', '搜索', '课程名 + 讲师名模糊匹配'],
    ['4', '详情', '大纲 / 讲师 / 评价 / 资料'],
    ['5', '收藏 / 报名', '收藏幂等；免费直报，付费校验订单'],
    ['6', '进度 / 继续学习', '章节完成 → 百分比 + 最近位置'],
  ];
  steps.forEach((st, i) => {
    const x = 0.55 + (i % 3) * 1.90;
    const y = 1.15 + Math.floor(i / 3) * 1.08;
    card(s, x, y, 1.78, 0.98);
    rect(s, x + 0.12, y + 0.12, 0.25, 0.25, LIGHT, 0.05);
    txt(s, st[0], x + 0.12, y + 0.12, 0.25, 0.25, 7.5, TEAL, true, 'center', 'middle');
    txt(s, st[1], x + 0.44, y + 0.10, 1.22, 0.22, 8.5, DARK, true);
    txt(s, st[2], x + 0.12, y + 0.43, 1.54, 0.34, 7.5, '475569');
  });
  card(s, 6.35, 1.15, 3.05, 2.75);
  txt(s, '验收点（一期）', 6.53, 1.26, 2.70, 0.24, 9, DARK, true);
  txt(s, '筛选组合结果正确 / 排序稳定\n课程与讲师均可命中 / 收藏幂等\n未报名不能写进度 / 刷新保留', 6.53, 1.56, 2.65, 0.72, 7.5, '475569');
  rect(s, 6.53, 2.50, 2.65, 0.005, BORDER);
  txt(s, '二期新增', 6.53, 2.60, 2.65, 0.20, 8.5, AMBER, true);
  txt(s, '资源区 / 报名权限\n最近位置 / 继续学习', 6.53, 2.72, 2.65, 0.55, 7.5, '475569');
  card(s, 0.55, 4.30, 8.85, 0.62);
  txt(s, '演示数据：18 门课程  ·  90 个章节  ·  8 个职位  ·  4 门课各 5 段 RAG 资料', 0.75, 4.47, 8.45, 0.24, 8.5, DARK);
}

/* ================= 7 演示 2 ================= */
{
  const s = contentSlide('DEMO 02 · 90s', '演示 2 —— AI 智能答疑（RAG）', 7, '多轮 + 引用 + 二期反馈');
  s.addShape(prs.ShapeType.roundRect, { x: 0.55, y: 1.18, w: 3.60, h: 0.52, rectRadius: 0.04, fill: { color: LIGHT }, line: { color: 'BAE6FD', width: 0.5 } });
  txt(s, '学生', 0.67, 1.25, 3.36, 0.16, 7.5, TEAL, true);
  txt(s, 'pandas 怎么做分组聚合？', 0.67, 1.42, 3.36, 0.22, 9, DARK);
  s.addShape(prs.ShapeType.roundRect, { x: 1.55, y: 1.78, w: 4.55, h: 0.95, rectRadius: 0.04, fill: { color: WHITE }, line: { color: BORDER, width: 0.75 } });
  txt(s, 'AI（一期）', 1.67, 1.85, 4.31, 0.16, 7.5, TEAL, true);
  txt(s, '用 groupby + agg 先按科目分组，再聚合成绩。\n参考：《Python 数据分析实战》第 3 章', 1.67, 2.02, 4.31, 0.65, 8.5, DARK);
  s.addShape(prs.ShapeType.roundRect, { x: 1.55, y: 2.88, w: 4.75, h: 0.75, rectRadius: 0.04, fill: { color: 'FFF7ED' }, line: { color: 'FED7AA', width: 0.75 } });
  txt(s, 'AI（二期：资料不足显式提示）', 1.67, 2.95, 4.51, 0.16, 7.5, AMBER, true);
  txt(s, '课程资料暂未覆盖「窗口函数」；以下为通用解释，可回到第 3 章核对。', 1.67, 3.13, 4.51, 0.40, 8, '475569');
  card(s, 6.62, 1.18, 2.78, 2.45);
  txt(s, '实现要点', 6.78, 1.28, 2.45, 0.22, 9.5, DARK, true);
  txt(s, '最近 10 条上下文\nRAG Top-3（bigram + TF-IDF）\n引用格式：参考：《课》第 N 章\n会话落库，可切历史\n无 Key / 失败走 Mock\n二期：相似度阈值 + 反馈闭环', 6.78, 1.58, 2.45, 1.85, 7.5, '475569');
  card(s, 0.55, 3.85, 5.85, 0.95);
  txt(s, '二期可信闭环', 0.72, 3.95, 5.40, 0.22, 9, AMBER, true);
  txt(s, '资料按标题/段落切 400–600 字；低相似度直接判「资料不足」；\n每条回答可 👍/👎 反馈；教师按低分问题补 FAQ。', 0.72, 4.22, 5.45, 0.50, 7.5, '475569');
  txt(s, '被追问准备：上下文如何截断？Prompt 如何防注入？为什么不用向量库？', 0.55, 4.98, 8.90, 0.20, 7.5, MUTED);
}

/* ================= 8 演示 3 ================= */
{
  const s = contentSlide('DEMO 03 · 60s', '演示 3 —— 学习路径与学习报告', 8, '一期能力 + 二期升级');
  const stages = [['01', '基础语法', '变量 / 函数 / 数据结构'], ['02', '数据分析', 'pandas / 可视化'], ['03', '项目实战', '端到端案例'], ['04', '认证冲刺', '真题 / 错题复盘']];
  stages.forEach((st, i) => {
    const x = 0.55 + i * 2.22;
    card(s, x, 1.12, 1.95, 0.95);
    rect(s, x + 0.13, 1.25, 0.28, 0.28, LIGHT, 0.05);
    txt(s, st[0], x + 0.13, 1.25, 0.28, 0.28, 8, TEAL, true, 'center', 'middle');
    txt(s, st[1], x + 0.48, 1.22, 1.35, 0.22, 9, DARK, true);
    txt(s, st[2], x + 0.13, 1.58, 1.70, 0.30, 8, '475569');
  });
  card(s, 0.55, 2.38, 4.30, 2.05);
  txt(s, '学习报告 4 模块（一期）', 0.72, 2.48, 3.90, 0.24, 9.5, DARK, true);
  const mods = [['时长趋势', '按周统计学习分钟'], ['薄弱点', '低进度课程与错题'], ['下周建议', 'AI 生成行动项'], ['课程进度', '已完成 / 总章节']];
  mods.forEach((m, i) => {
    const x = 0.72 + (i % 2) * 2.02;
    const y = 2.85 + Math.floor(i / 2) * 0.72;
    txt(s, m[0], x, y, 1.85, 0.20, 8, TEAL, true);
    txt(s, m[1], x, y + 0.22, 1.85, 0.28, 7.5, '475569');
  });
  card(s, 5.15, 2.38, 4.25, 2.05);
  txt(s, '实现要点与二期升级', 5.32, 2.48, 3.90, 0.24, 9.5, DARK, true);
  txt(s, '一期：目标 + 每周投入 + 手填薄弱点，生成 4 阶段文本\n一期：报告按 learning_records 全量统计，period 仅改文案\n二期：路径读真实进度/作业得分，结构化落库，可接受/调整\n二期：报告按事件时间窗统计，含周月对比与知识点掌握\n二期：路径 course_id 必须来自平台已上架课程', 5.32, 2.80, 3.85, 1.50, 7.5, '475569');
  card(s, 0.55, 4.55, 8.85, 0.55);
  txt(s, '现场演示 60 秒：路径生成 → 报告解读 → 下一步建议；二期演示位预留「接受/调整路径」', 0.73, 4.68, 8.50, 0.30, 8, DARK);
}

/* ================= 9 数据与接口 ================= */
{
  const s = contentSlide('DATA & CONTRACT', '数据库与接口设计', 9, '一期实测 + 二期规划');
  s.addTable([
    [{ text: '核心表（一期）', options: { bold: true, color: WHITE, fill: TEAL } }, { text: '作用', options: { bold: true, color: WHITE, fill: TEAL } }],
    ['users', '账号 / 角色 / 状态'],
    ['courses', '课程 / 讲师 / 统计 / 审核态'],
    ['chapters', '章节 / 时长 / 顺序'],
    ['comments', '评价 / 回复 / 点赞'],
    ['learning_records', '进度 / 时长 / 最近章节'],
    ['course_materials', 'RAG 资料 / 学习资源'],
  ], {
    x: 0.55, y: 1.12, w: 5.30, colW: [1.85, 3.45],
    fontFace: F, fontSize: 8, color: DARK, border: { type: 'solid', color: BORDER, pt: 0.75 },
    rowH: 0.30, valign: 'middle', margin: 0.04,
  });
  const kpis = [['16', '数据表（一期）'], ['45', '路径（一期）'], ['53', '操作（一期）'], ['8', 'router（一期）']];
  kpis.forEach((k, i) => {
    const x = 6.10 + (i % 2) * 1.65;
    const y = 1.12 + Math.floor(i / 2) * 0.78;
    card(s, x, y, 1.55, 0.70);
    txt(s, k[0], x + 0.10, y + 0.08, 1.35, 0.34, 17, TEAL, true, 'center');
    txt(s, k[1], x + 0.10, y + 0.46, 1.35, 0.18, 7, MUTED, false, 'center');
  });
  card(s, 6.10, 2.72, 3.20, 1.18);
  txt(s, '索引与约束', 6.24, 2.82, 2.90, 0.20, 8.5, DARK, true);
  txt(s, 'study_count / rating 索引；收藏、评论、点赞、报名、职位收藏均设唯一约束，避免重复计数。', 6.24, 3.06, 2.90, 0.85, 7.5, '475569');
  card(s, 0.55, 3.28, 5.30, 1.05);
  txt(s, '二期新增 11 表（规划）', 0.70, 3.38, 5.00, 0.22, 8.5, AMBER, true);
  txt(s, 'operation_logs · learning_events · enrollments · assignments\nsubmissions · learning_paths · job_favorites · interview_sessions\ncontent_reports · notification_preferences · taxonomy_terms', 0.70, 3.72, 5.00, 0.70, 7, '475569');
  card(s, 0.55, 4.55, 8.85, 0.52);
  txt(s, '统一契约：{code, message, data} · 40001/40101/40301/40401/40901/50001 · 分页 {items,total,page,page_size} · /docs 自动生成', 0.73, 4.68, 8.50, 0.28, 7.5, DARK);
}

/* ================= 10 工程质量 ================= */
{
  const s = contentSlide('ENGINEERING QUALITY', '工程质量保障', 10, '一期实测 / 二期目标');
  const kpis = [['57', 'pytest 用例'], ['90%', '行覆盖率'], ['1424', '语句'], ['137', '未覆盖']];
  kpis.forEach((k, i) => {
    const x = 0.55 + (i % 2) * 2.75;
    const y = 1.12 + Math.floor(i / 2) * 0.92;
    card(s, x, y, 2.55, 0.82);
    txt(s, k[0], x + 0.12, y + 0.08, 2.31, 0.34, 17, TEAL, true, 'center');
    txt(s, k[1], x + 0.12, y + 0.48, 2.31, 0.18, 8, MUTED, false, 'center');
  });
  txt(s, '测试增长（18 → 57）', 0.55, 3.02, 4.20, 0.22, 9, DARK, true);
  s.addChart(prs.ChartType.bar, [
    { name: 'pytest 用例', labels: ['阶段 0', 'P3', '交付'], values: [18, 46, 57] },
  ], {
    x: 0.55, y: 3.28, w: 4.20, h: 1.55,
    barDir: 'col', chartColors: [TEAL], showValue: true, dataLabelColor: DARK, dataLabelFontFace: F, dataLabelFontSize: 8,
    catAxisLabelFontFace: F, catAxisLabelFontSize: 7.5, catAxisLabelColor: '475569',
    valAxisLabelFontFace: F, valAxisLabelFontSize: 7, valAxisLabelColor: MUTED,
    valGridLine: { color: 'E2E8F0', style: 'dash', size: 0.5 },
    showLegend: false, barGapWidthPct: 70,
  });
  card(s, 5.20, 1.12, 4.20, 1.70);
  txt(s, '工程措施', 5.36, 1.22, 3.90, 0.22, 9.5, DARK, true);
  const eng = [['统一响应', '{code, message, data}'], ['异常处理', '全局 handler + 错误码映射'], ['安全', 'PBKDF2 + JWT + DOMPurify'], ['降级', '在线失败自动 Mock'], ['报告', 'term-missing + XML 落盘']];
  eng.forEach((e, i) => {
    const y = 1.50 + i * 0.25;
    txt(s, e[0], 5.36, y, 1.10, 0.20, 7.5, DARK, true);
    txt(s, e[1], 6.50, y, 2.80, 0.20, 7.5, '475569');
  });
  card(s, 5.20, 3.02, 4.20, 1.55);
  txt(s, '二期质量目标', 5.36, 3.12, 3.90, 0.22, 9, AMBER, true);
  txt(s, '用例 57 → 100+；行覆盖 ≥ 85%\n新增接口每条 1 正 1 反；越权与降级必测\n指导教师复核接口单独覆盖\n沙箱超时/编译失败/运行异常三类用例', 5.36, 3.40, 3.85, 1.05, 7.5, '475569');
  txt(s, '构建：npm run build 退出码 0（一期实测）；Docker 三容器 healthy', 0.55, 4.95, 8.90, 0.20, 7.5, MUTED);
}

/* ================= 11 项目管理 ================= */
{
  const s = contentSlide('PROJECT MANAGEMENT', '项目管理实践', 11, '一期 5 次 + 二期 3 次');
  const meetings = [
    ['11-23 19:30', '项目启动会', '定技术栈 / 定分工 / 冻结 P0-P2'],
    ['11-24 20:00', '需求 + 架构评审', '需求签字 / 接口契约冻结'],
    ['11-26 20:00', 'Sprint 评审', '演示 → 记缺陷 → 认领下轮'],
    ['11-27 18:20', '复盘会', '问题清单 / 一页复盘报告'],
    ['11-27 20:00', '答辩准备会', '掐表演练 / 环境兜底'],
  ];
  rect(s, 0.80, 1.42, 8.30, 0.01, BORDER);
  meetings.forEach((m, i) => {
    const x = 0.68 + i * 1.72;
    s.addShape(prs.ShapeType.ellipse, { x, y: 1.34, w: 0.17, h: 0.17, fill: { color: i < 5 ? TEAL : AMBER }, line: { color: i < 5 ? TEAL : AMBER } });
    txt(s, m[0], x - 0.10, 1.62, 1.60, 0.20, 7.5, MUTED);
    txt(s, m[1], x - 0.10, 1.84, 1.60, 0.22, 8, DARK, true);
    txt(s, m[2], x - 0.10, 2.10, 1.60, 0.50, 7, '475569');
  });
  txt(s, '二期 +3 次：指导书解读 / 方案评审 / 二期启动', 5.55, 2.64, 3.85, 0.22, 7, AMBER, true, 'right');
  const risks = [['LLM 额度 / 网络', 'Mock 兜底，演示不依赖在线 Key'], ['Docker 代理', 'host.docker.internal:7897 + Allow LAN'], ['时间与范围', '任务 ≤ 2 天，先 P0/P1 再 P2'], ['沙箱不可用', '降级静态分析，如实标注']];
  risks.forEach((r, i) => {
    const x = 0.55 + i * 2.22;
    card(s, x, 3.00, 2.12, 0.95);
    txt(s, r[0], x + 0.12, 3.10, 1.90, 0.20, 8, DARK, true);
    txt(s, r[1], x + 0.12, 3.34, 1.88, 0.55, 7.5, '475569');
  });
  card(s, 0.55, 4.25, 8.85, 0.62);
  txt(s, '过程产出：5 次会议纪要  ·  13 条功能提交  ·  57 项测试  ·  3 容器实测  ·  缺口清单逐条证据', 0.75, 4.42, 8.45, 0.25, 8.5, DARK);
}

/* ================= 12 测试与缺陷 ================= */
{
  const s = contentSlide('TEST & DEFECTS', '测试与缺陷', 12, '一期实测');
  s.addTable([
    [{ text: '模块', options: { bold: true, color: WHITE, fill: TEAL } }, { text: '主路径', options: { bold: true, color: WHITE, fill: TEAL } }, { text: '异常路径', options: { bold: true, color: WHITE, fill: TEAL } }],
    ['用户', '注册 / 登录 / 资料', '401 / 403 / 停用'],
    ['课程', '筛选 / 详情 / 收藏', '404 / 422 / 越权'],
    ['AI', '四功能 / RAG', '降级 / 越权 / 引用'],
    ['后台', 'CRUD / 状态机', '409 / 403 / 404'],
  ], {
    x: 0.55, y: 1.12, w: 5.60, colW: [1.10, 2.60, 1.90],
    fontFace: F, fontSize: 8, color: DARK, border: { type: 'solid', color: BORDER, pt: 0.75 },
    rowH: 0.34, valign: 'middle', margin: 0.05,
  });
  card(s, 6.45, 1.12, 3.05, 1.15);
  txt(s, '风险 / 缺陷处置', 6.62, 1.22, 2.75, 0.20, 8.5, DARK, true);
  txt(s, '识别 10 项  /  修复 9 项', 6.62, 1.48, 2.75, 0.28, 9.5, AMBER, true);
  txt(s, '保留 R10：「最多评论」排序文案，已记录原因。', 6.62, 1.78, 2.75, 0.40, 7.5, '475569');
  card(s, 6.45, 2.38, 3.05, 1.15);
  txt(s, 'Docker 部署验证', 6.62, 2.48, 2.75, 0.20, 8.5, DARK, true);
  txt(s, '3 容器 healthy', 6.62, 2.74, 2.75, 0.24, 9, GREEN, true);
  txt(s, '8080 health 200  ·  student 登录 200', 6.62, 3.04, 2.75, 0.30, 7.5, '475569');
  const kpis = [['57', '用例全绿'], ['90%', '行覆盖'], ['22', '异常路径用例'], ['0', '遗留失败']];
  kpis.forEach((k, i) => {
    const x = 0.55 + i * 2.25;
    card(s, x, 3.72, 2.12, 0.85);
    txt(s, k[0], x + 0.12, 3.82, 0.95, 0.34, 16, TEAL, true, 'center');
    txt(s, k[1], x + 1.05, 3.90, 0.95, 0.22, 7.5, MUTED, false, 'center');
  });
  txt(s, '二期 12 条测试场景（指导书）：三角色权限 / 组合筛选 / 报名学习 / 断点续学 / RAG 引用 / 资料不足 / 路径 / 批改三类 / 周月报 / 职位 / 面试 / 降级', 0.55, 4.82, 8.90, 0.30, 7, MUTED);
}

/* ================= 13 AI 声明 ================= */
{
  const s = contentSlide('AI USAGE & REVIEW', 'AI 工具使用声明', 13, '学术诚信');
  card(s, 0.55, 1.12, 4.30, 3.00);
  txt(s, '使用范围', 0.75, 1.26, 3.90, 0.24, 11, DARK, true);
  txt(s, '代码生成与补全\n单元测试生成与修复\n文档润色与结构整理\n答辩 PPT 版式辅助\n二期方案的结构化设计\n不用于伪造数据或结果', 0.75, 1.62, 3.85, 2.30, 9.5, '475569');
  card(s, 5.10, 1.12, 4.30, 3.00);
  txt(s, '人工校验', 5.30, 1.26, 3.90, 0.24, 11, DARK, true);
  txt(s, '逐行 Review 生成代码\n57 项 pytest 全绿\nnpm run build 退出码 0\n真实接口请求验证\nDocker 三容器实测\n二期方案已对照代码逐项审计', 5.30, 1.62, 3.85, 2.30, 9.5, '475569');
  card(s, 0.55, 4.25, 8.85, 0.72);
  txt(s, '原则：AI 是辅助，设计与取舍由人负责；密钥/Token 不写入代码与文档；作业已按要求标注 AI 使用范围。', 0.75, 4.42, 8.45, 0.32, 8.5, DARK);
}

/* ================= 14 指导书九项对照 ================= */
{
  const s = contentSlide('GUIDE GAP MATRIX', '指导书九项优化点对照', 14, '9 项均部分实现');
  s.addTable([
    [{ text: '指导书优化点', options: { bold: true, color: WHITE, fill: TEAL } },
     { text: '一期现状', options: { bold: true, color: WHITE, fill: TEAL } },
     { text: '二期目标', options: { bold: true, color: WHITE, fill: TEAL } },
     { text: '差距', options: { bold: true, color: WHITE, fill: TEAL } }],
    ['角色权限与审计', '三角色 + 接口守卫', '权限矩阵 + 操作日志 + 教师学情', '大'],
    ['课程资源与体验', '课程/章节/筛选可用', '资源区 + 报名 + 字典化 + 审核态', '大'],
    ['学习进度与数据', '完成率 + 手动上报时长', '学习事件 + 有效时长 + 续学', '大'],
    ['RAG 智能答疑', '资料 + TF-IDF + 引用', '资料不足判定 + 反馈 + FAQ', '中'],
    ['个性化路径', '三表单 + 文本生成', '真实数据 + 结构化 + 可调整', '大'],
    ['编程作业批改', '模型静态点评', 'Rubric + 沙箱 + 教师复核', '大'],
    ['学习报告', '全量统计 + 文案周月', '真实时间窗 + 对比 + 知识点', '中'],
    ['实习就业 / AI 面试', '搜索 / 申请可用', '收藏 + 状态机 + AI 面试', '大'],
    ['加分项', '通知 / 社区 / 响应式', '偏好 + 举报审核 + 职位通知', '中'],
  ], {
    x: 0.55, y: 1.10, w: 8.85, colW: [2.05, 2.35, 3.45, 1.00],
    fontFace: F, fontSize: 7.5, color: DARK, border: { type: 'solid', color: BORDER, pt: 0.75 },
    rowH: 0.30, valign: 'middle', margin: 0.04,
  });
  const rows = s._slideObjects;
  txt(s, '判定口径：主链路完整且可验证 = 已实现；有代码但缺关键能力 = 部分；无代码 = 缺失。一期无一项「缺失」，但无一项完全达到指导书要求。', 0.55, 4.38, 8.90, 0.34, 7.5, '475569');
  txt(s, '证据逐条见 docs/06-缺口清单.md；本页只做汇总，不改既有判定。', 0.55, 4.72, 8.90, 0.22, 7, MUTED);
}

/* ================= 15 二期技术方案 ================= */
{
  const s = contentSlide('PHASE 2 TECHNICAL PLAN', '二期技术方案（规划）', 15, '11 表 · 3 router');
  const blocks = [
    ['权限与审计', 'operation_logs\nGET /admin/operation-logs', '越权 403；管理动作可追溯'],
    ['学习数据', 'learning_events / enrollments\nPOST /courses/{id}/events', '有效时长；断点续学'],
    ['RAG 可信闭环', 'course_materials 切分 + 反馈\nPOST /ai/messages/{id}/feedback', '资料不足不编造'],
    ['路径 2.0', 'learning_paths\nPOST /ai/learning-path', '只推平台课程；可调整'],
    ['批改 2.0', 'assignments / submissions + sandbox\nPATCH /admin/submissions/{id}/review', '客观分 / AI 分 / 复核'],
    ['就业 + 面试', 'job_favorites / interview_sessions\nPOST /jobs/{id}/interview', '状态可追踪；含声明'],
  ];
  blocks.forEach((b, i) => {
    const x = 0.55 + (i % 3) * 2.98;
    const y = 1.12 + Math.floor(i / 3) * 1.52;
    card(s, x, y, 2.85, 1.38);
    rect(s, x, y, 0.06, 1.38, i < 3 ? TEAL : AMBER);
    txt(s, b[0], x + 0.18, y + 0.10, 2.55, 0.22, 9.5, DARK, true);
    txt(s, b[1], x + 0.18, y + 0.40, 2.55, 0.55, 7, '475569');
    txt(s, b[2], x + 0.18, y + 1.02, 2.55, 0.26, 7.5, i < 3 ? TEAL : AMBER, true);
  });
  card(s, 0.55, 4.22, 8.85, 0.78);
  txt(s, '沙箱边界：Docker 一次性容器 · --network none · 128m / 0.5 CPU · 5s 超时 · 只读挂载 + tmpfs；Docker 不可用时降级为静态分析 + 样例测试，并在结果页标注「未执行代码」。', 0.73, 4.36, 8.50, 0.52, 7.5, DARK);
  txt(s, '二期完成后预期：27 表 · 约 79 路径 / 92 操作 · 10 页面 · 100+ 测试（以实测回填，不提前定稿）', 0.55, 5.02, 8.90, 0.20, 7, MUTED);
}

/* ================= 16 二期路线图 ================= */
{
  const s = contentSlide('PHASE 2 ROADMAP', '二期路线图（4 阶段 / 11 批）', 16, '每批独立验收');
  const lanes = [
    ['阶段一 · 课程主流程', TEAL, [
      ['G1', '权限矩阵 / 审计 / 教师学情'],
      ['G2', '资源 / 报名 / 字典 / 审核态'],
      ['G3', '学习事件 / 有效时长 / 续学'],
    ]],
    ['阶段二 · AI 助手', AMBER, [
      ['H1', 'RAG 切分 / 不足判定 / 反馈'],
      ['H2', '路径真实数据 / 落库 / 调整'],
      ['H3', '作业 / Rubric / 沙箱 / 复核'],
      ['H4', '周月时间窗 / 对比 / 知识点'],
    ]],
    ['阶段三 · 就业服务', TEAL, [
      ['I1', '职位收藏 / 申请状态机'],
      ['I2', 'AI 面试 / 维度反馈'],
    ]],
    ['阶段四 · 交付优化', AMBER, [
      ['J1', '提醒偏好 / 举报审核 / 职位通知'],
      ['J2', '回归 / 文档 / PPT / 管理表'],
    ]],
  ];
  lanes.forEach((lane, i) => {
    const x = 0.55 + i * 2.24;
    card(s, x, 1.12, 2.06, 3.05);
    rect(s, x, 1.12, 2.06, 0.34, lane[1], 0.03);
    txt(s, lane[0], x + 0.08, 1.17, 1.90, 0.22, 7.5, WHITE, true, 'center');
    lane[2].forEach((b, j) => {
      const y = 1.58 + j * 0.62;
      rect(s, x + 0.10, y, 1.86, 0.52, 'F1F5F9', 0.02);
      txt(s, b[0], x + 0.18, y + 0.06, 0.32, 0.18, 7.5, lane[1] === AMBER ? 'B45309' : TEAL, true);
      txt(s, b[1], x + 0.50, y + 0.05, 1.40, 0.44, 6.3, '334155');
    });
  });
  card(s, 0.55, 4.30, 8.85, 0.70);
  txt(s, '每批固定动作：改代码 → 补 pytest → pytest -q + npm run build → 回填 docs/06 → 同步 README → 汇报；未通过不进入下一批。', 0.73, 4.44, 8.50, 0.44, 8, DARK);
  txt(s, '数据迁移：migrate_v2.py 幂等建表 + 补列；迁移前备份演示库；不运行 seed.py 重置。', 0.55, 5.08, 8.90, 0.20, 7, MUTED);
}

/* ================= 17 取舍与风险 ================= */
{
  const s = contentSlide('TRADE-OFFS & RISKS', '取舍与风险', 17, '答辩口径必须分清');
  card(s, 0.55, 1.12, 4.30, 2.90);
  txt(s, '主动不做（本期）', 0.75, 1.24, 3.90, 0.24, 10, DARK, true);
  const no = ['向量数据库：TF-IDF 足够且可解释', '真实支付：只做订单状态演示', '离线推送：SSE + 轮询已覆盖站内', '独立 App：优先移动端适配', '生产级 OJ：只做教学评测沙箱', '招聘结论：面试仅训练反馈'];
  no.forEach((n, i) => {
    rect(s, 0.77, 1.62 + i * 0.37, 0.07, 0.24, AMBER);
    txt(s, n, 0.95, 1.63 + i * 0.37, 3.70, 0.28, 8, '475569');
  });
  card(s, 5.10, 1.12, 4.30, 2.90);
  txt(s, '风险与对策', 5.30, 1.24, 3.90, 0.24, 10, DARK, true);
  const risks = [
    ['沙箱不可用', '降级静态分析 + 样例测试，结果页标注未执行代码'],
    ['新增 11 表', '幂等迁移 + 迁移前备份，不重置演示库'],
    ['事件写入放大', '30s 批量心跳；同章节同日聚合；联合索引'],
    ['模型 JSON 不稳', 'Schema 校验 + 重试 1 次 + Mock 结构化兜底'],
    ['测试量翻倍', '每批只测本批新增 + 越权/降级；不一次性铺开'],
  ];
  risks.forEach((r, i) => {
    const y = 1.58 + i * 0.47;
    txt(s, '●', 5.30, y, 0.16, 0.20, 7, AMBER, true);
    txt(s, r[0], 5.48, y, 1.05, 0.20, 7.5, DARK, true);
    txt(s, r[1], 6.52, y - 0.02, 2.75, 0.42, 7, '475569');
  });
  card(s, 0.55, 4.20, 8.85, 0.80);
  txt(s, '答辩口径：第 1–13 页讲「一期已交付」；第 14–17 页讲「二期方案（规划）」；不把规划讲成已完成，不把 Mock 讲成真实模型。', 0.75, 4.36, 8.50, 0.50, 8.5, DARK);
}

/* ================= 18 致谢 ================= */
{
  const s = prs.addSlide();
  s.background = { color: DARK };
  s.addShape(prs.ShapeType.ellipse, { x: 4.60, y: -1.55, w: 4.60, h: 4.60, fill: { color: TEAL, transparency: 86 }, line: { color: TEAL, transparency: 86 } });
  s.addShape(prs.ShapeType.ellipse, { x: 6.90, y: 2.50, w: 3.40, h: 3.40, fill: { color: AMBER, transparency: 90 }, line: { color: AMBER, transparency: 90 } });
  txt(s, 'THANK YOU', 0.72, 0.78, 4.00, 0.24, 10, AMBER, true);
  txt(s, '谢谢，请老师提问', 0.72, 1.10, 8.00, 0.70, 34, WHITE, true);
  txt(s, '从「课程展示与学习记录平台」到「个性化学习与就业服务平台」', 0.72, 1.92, 8.60, 0.32, 12, LIGHT);
  const sum = [['业务闭环', '8 页面 / 45 路径 / 53 操作'], ['AI 落地', '4 能力 + RAG + Mock 兜底'], ['工程规范', '57 测试 / 90% / Docker 实测']];
  sum.forEach((c, i) => {
    const x = 0.72 + i * 2.95;
    s.addShape(prs.ShapeType.roundRect, { x, y: 2.65, w: 2.75, h: 1.10, rectRadius: 0.04, fill: { color: '1E293B' }, line: { color: '334155', width: 0.75 } });
    txt(s, c[0], x + 0.18, 2.78, 2.40, 0.26, 9.5, AMBER, true);
    txt(s, c[1], x + 0.18, 3.08, 2.40, 0.40, 8.5, 'CBD5E1');
  });
  rect(s, 0.72, 4.25, 3.20, 0.01, '475569');
  txt(s, '邱麟  /  202502210379  /  2026-11-27', 0.72, 4.45, 5.50, 0.26, 11, 'CBD5E1');
  txt(s, '一期已交付 · 二期方案已定稿 · 按批次实施', 0.72, 4.78, 7.00, 0.24, 9, '94A3B8');
}

prs.writeFile({ fileName: 'C:/Users/qiulin/Desktop/项目二 面向教育平台的智能体开发/output/邱麟_答辩PPT_v2.pptx' })
  .then(() => console.log('PPT_GENERATED_OK'))
  .catch(err => { console.error('PPT_GENERATE_FAIL', err); process.exit(1); });