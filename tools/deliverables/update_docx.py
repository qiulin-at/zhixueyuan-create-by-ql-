# -*- coding: utf-8 -*-
import copy
import docx
from docx.table import Table

SRC = r'output/邱麟_项目管理4表.docx'
DST = r'output/邱麟_项目管理4表_v2.docx'

d = docx.Document(SRC)


def set_text(par, text):
    if par.runs:
        par.runs[0].text = text
        for r in par.runs[1:]:
            r.text = ''
    else:
        par.add_run(text)


def set_cell(table, r, c, text):
    cell = table.rows[r].cells[c]
    p = cell.paragraphs[0]
    set_text(p, text)
    for extra in cell.paragraphs[1:]:
        set_text(extra, '')


# ---------- 1. 封面与说明 ----------
set_text(d.paragraphs[1], '项目二 · 项目管理 4 表（含二期优化提升）')
set_text(d.paragraphs[4], '编制日期：2026-11-24（二期方案）    答辩日期：2026-11-27')
set_text(d.paragraphs[5], '说明：本项目为 1 人独立完成，原模板 PM / 前端 / 后端 / AI+测试 四个角色由本人合并承担。'
                          '数据来自项目仓库、测试报告与例会记录；签字前请本人复核。二期方案见 docs/10-优化提升方案.md，'
                          '二期功能为计划态，答辩时明确区分「一期已交付」与「二期规划」。')

# ---------- 2. 策划任务书 ----------
t3 = d.tables[2]
set_cell(t3, 3, 1, '一期：业务闭环 + AI 赋能 + 工程规范，8 页面 / 45 路径 53 操作 / 16 表 / 57 测试 / 90% 行覆盖 / 3 容器。'
                   '二期：从「课程展示与学习记录平台」提升为「个性化学习与就业服务平台」，目标 27 表 / 约 79 路径 / 10 页面 / 100+ 测试。')
set_cell(t3, 4, 1, '一期 P0：用户 / 课程 / 后台；P1：AI 四功能 / 职位；P2：社区 / SSE / 移动端；交付物 D1–D6。'
                   '二期 4 阶段 11 批：G1–G3 课程主流程、H1–H4 AI 助手、I1–I2 就业服务、J1–J2 交付优化。')
set_cell(t3, 5, 1, 'M1 需求与架构 2026-11-23；M2 基础链路 2026-11-23；M3 业务与 AI 2026-11-24；M4 测试与部署 2026-11-24；'
                   'M5 答辩 2026-11-27；M6 二期方案定稿 2026-11-24；M7 二期功能完成 2026-12-07；M8 二期验收 2026-12-08。')
set_cell(t3, 6, 1, '一期：三角色可登录；课程筛选 / 排序 / 搜索 / 收藏 / 进度可用；AI 答疑多轮 + RAG 引用（含 Mock）；后台 CRUD / 订单状态机 / 用户启停可用；57 测试全绿。'
                   '二期：未报名不能学；学习事件与有效时长可追溯；答疑资料不足不编造；路径只推平台课程；批改区分正确/失败/超时且教师可复核；周月报按真实时间窗；职位申请可追踪；AI 面试含声明。')
set_cell(t3, 8, 1, '一期：LLM 不稳定 → Mock 兜底；Docker 代理 → host.docker.internal:7897 + Allow LAN；时间紧 → 任务 ≤ 2 天 / 批次；范围大 → 冻结 P0/P1/P2。'
                   '二期：沙箱不可用 → 降级静态分析并标注；新增 11 表 → 幂等迁移 + 迁移前备份；模型 JSON 不稳 → Schema 校验 + 重试 + Mock 结构化兜底。')

# ---------- 3. 进度计划表追加二期任务 ----------
t4 = d.tables[3]
tasks = [
    ('T13', 'G1 权限矩阵与操作审计', '11-26', '11-27', 'operation_logs + 教师学情', '二期·规划态'),
    ('T14', 'G2 课程资源与报名', '11-27', '11-28', 'course_materials 扩展 + enrollments', '二期·规划态'),
    ('T15', 'G3 学习事件与进度', '11-27', '11-29', 'learning_events + 有效时长', '二期·规划态'),
    ('T16', 'H1 RAG 可信闭环', '11-29', '11-30', '切分 + 资料不足 + 反馈', '二期·规划态'),
    ('T17', 'H2 学习路径 2.0', '11-29', '12-01', 'learning_paths + 课程校验', '二期·规划态'),
    ('T18', 'H3 作业批改与沙箱', '11-30', '12-02', 'assignments / submissions / sandbox', '二期·规划态'),
    ('T19', 'H4 学习报告 2.0', '12-02', '12-03', '时间窗 + 对比 + 知识点', '二期·规划态'),
    ('T20', 'I1 就业闭环', '12-03', '12-04', 'job_favorites + 申请状态机', '二期·规划态'),
    ('T21', 'I2 AI 面试', '12-04', '12-05', 'interview_sessions + 面试页', '二期·规划态'),
    ('T22', 'J1 加分项收口', '12-05', '12-06', '提醒偏好 + 举报审核', '二期·规划态'),
    ('T23', 'J2 二期回归与文档', '12-06', '12-07', 'docs/02/03/06/07 回填', '二期·规划态'),
    ('T24', '二期答辩材料更新', '12-07', '12-08', 'PPT 18 页 + 管理表', '二期·规划态'),
]
for t in tasks:
    tr = copy.deepcopy(t4.rows[-1]._tr)
    t4._tbl.append(tr)
    row = t4.rows[-1]
    vals = [t[0], t[1], '邱麟', t[2], t[3], '—', '0%', t[4], t[5]]
    for i, v in enumerate(vals):
        set_cell(t4, len(t4.rows) - 1, i, v)

# ---------- 4. 追加二期 3 次会议（插入检查表前） ----------
target = None
for p in d.paragraphs:
    if p.text.strip().startswith('附：文档提交检查表'):
        target = p._p
        break
assert target is not None

heading_tpl = d.paragraphs[54]._p      # 第 5 次标题
label1_tpl = d.paragraphs[56]._p       # 议程与结论
label2_tpl = d.paragraphs[58]._p       # 待办事项
risk_tpl = d.paragraphs[60]._p         # 风险与阻塞
meet_tpl = d.tables[16]._tbl
agenda_tpl = d.tables[17]._tbl
todo_tpl = d.tables[18]._tbl

meetings = [
    {
        'heading': '第 6 次：优化指导书解读会（二期）',
        'when': '2026-11-24 21:00 / 线上',
        'agenda': [
            ('解读九项优化点', '角色 / 课程 / 学习数据 / AI 四功能 / 就业 / 加分', '9 项全部部分实现，6 项大差距；二期范围冻结', '11-24'),
            ('目标与范围控制', '学习闭环优先、AI 围绕课程、数据可信、权限明确', '先课程主流程，再 AI，再就业，最后加分', '11-24'),
            ('材料与口径', '方案文档、答辩 PPT、项目管理表', '新增 docs/10；PPT 18 页；管理表追加二期计划', '11-24'),
        ],
        'todo': [
            ('A1', '输出优化方案初稿', '11-24', '已完成'),
            ('A2', '更新答辩 PPT 至 18 页', '11-25', '待执行'),
            ('A3', '更新项目管理 4 表', '11-25', '待执行'),
        ],
        'risk': '风险与阻塞：二期功能尚未实施，所有材料必须标注「规划态」；避免把规划讲成已完成。',
    },
    {
        'heading': '第 7 次：二期方案评审',
        'when': '2026-11-25 20:00 / 线上',
        'agenda': [
            ('差距矩阵与目标', '9 项部分实现 / 6 项大差距', '目标 27 表、约 79 路径、10 页面、100+ 测试', '11-25'),
            ('数据与接口设计', '11 张新表、约 34 条新路径', '幂等迁移，不重置演示库；接口以 openapi 实测回填', '11-25'),
            ('风险与取舍', '沙箱、迁移、模型 JSON', '沙箱不可用则降级并标注；不做向量库 / 支付 / 离线推送', '11-25'),
        ],
        'todo': [
            ('A1', '方案定稿 docs/10', '11-25', '已完成'),
            ('A2', '拆批 G1–G3 / H1–H4 / I1–I2 / J1–J2', '11-25', '已完成'),
            ('A3', '准备 migrate_v2.py 迁移脚本', '11-26', '待执行'),
        ],
        'risk': '风险与阻塞：11 表迁移与演示库一致性；沙箱依赖 Docker，答辩机可能不可用。',
    },
    {
        'heading': '第 8 次：二期启动会',
        'when': '2026-11-26 19:00 / 线上',
        'agenda': [
            ('批次计划与验收', '4 阶段 11 批', '每批固定动作：代码 / 测试 / 构建 / 回填 / 汇报', '11-26'),
            ('答辩口径', '一期已交付 vs 二期规划', 'PPT 第 1–13 页讲交付，第 14–17 页讲规划', '11-26'),
            ('数据安全', '演示库备份、不跑 seed 重置', '迁移前备份 zhixueyun.db，迁移后核对表数与数据量', '11-26'),
        ],
        'todo': [
            ('A1', '备份演示库', '11-26', '待执行'),
            ('A2', '启动 G1 权限与审计', '11-26', '待执行'),
            ('A3', 'docs/06 增加二期缺口表', '11-27', '待执行'),
        ],
        'risk': '风险与阻塞：答辩前只交付材料、不改代码；功能批次在答辩后按 G1–J2 顺序执行。',
    },
]

for m in meetings:
    h = copy.deepcopy(heading_tpl)
    target.addprevious(h)
    # 找到刚插入的标题段落并改文本
    inserted = [p for p in d.paragraphs if p._p is h][0]
    set_text(inserted, m['heading'])

    mt = copy.deepcopy(meet_tpl)
    target.addprevious(mt)
    m_table = Table(mt, d._body)
    set_cell(m_table, 1, 1, m['heading'].split('：', 1)[1])
    set_cell(m_table, 2, 1, m['when'])
    set_cell(m_table, 3, 1, '邱麟 / 邱麟')
    set_cell(m_table, 4, 1, '邱麟（1 人团队）')
    set_cell(m_table, 5, 1, '无')

    l1 = copy.deepcopy(label1_tpl)
    target.addprevious(l1)

    at = copy.deepcopy(agenda_tpl)
    target.addprevious(at)
    a_table = Table(at, d._body)
    for i, (topic, points, decision, due) in enumerate(m['agenda'], start=1):
        set_cell(a_table, i, 0, str(i))
        set_cell(a_table, i, 1, topic)
        set_cell(a_table, i, 2, points)
        set_cell(a_table, i, 3, decision)
        set_cell(a_table, i, 4, '邱麟')
        set_cell(a_table, i, 5, due)

    l2 = copy.deepcopy(label2_tpl)
    target.addprevious(l2)

    tt = copy.deepcopy(todo_tpl)
    target.addprevious(tt)
    t_table = Table(tt, d._body)
    for i, (no, task, due, status) in enumerate(m['todo'], start=1):
        set_cell(t_table, i, 0, no)
        set_cell(t_table, i, 1, task)
        set_cell(t_table, i, 2, '邱麟')
        set_cell(t_table, i, 3, due)
        set_cell(t_table, i, 4, status)

    rp = copy.deepcopy(risk_tpl)
    target.addprevious(rp)
    set_text([p for p in d.paragraphs if p._p is rp][0], m['risk'])

# ---------- 5. 检查表追加二期条目 ----------
last_check = None
for p in d.paragraphs:
    if p.text.strip().startswith('Git 仓库地址已在作业备注提交'):
        last_check = p._p
        break
assert last_check is not None
extra = [
    '二期优化方案（docs/10）：☑ 已定稿',
    '答辩 PPT 18 页（含二期方案）：☑ 已更新',
    '项目管理 4 表（含二期计划）：☑ 已更新',
    '二期功能实施：□ 待启动（按 G1–J2 批次执行）',
]
for text in extra:
    np = copy.deepcopy(last_check)
    last_check.addnext(np)
    set_text([p for p in d.paragraphs if p._p is np][0], text)
    last_check = np

# ---------- 6. 编制说明 ----------
for p in d.paragraphs:
    if p.text.strip().startswith('编制说明：'):
        set_text(p, '编制说明：本文件依据项目真实提交记录、测试报告与例会安排整理；一期进度为实际完成，'
                    '二期进度为计划态（2026-11-26 起按批次执行）。成员联系方式、签字与教师审批需本人/教师补填，未做代签。')
        break

# ---------- 7. 统计并保存 ----------
d.save(DST)
d2 = docx.Document(DST)
print('SAVED', DST)
print('paragraphs', len(d2.paragraphs), 'tables', len(d2.tables))
print('progress rows', len(d2.tables[3].rows))
print('meeting headings', [p.text for p in d2.paragraphs if p.style.name == 'Heading 2'])
print('checklist tail', [p.text for p in d2.paragraphs[-10:]])