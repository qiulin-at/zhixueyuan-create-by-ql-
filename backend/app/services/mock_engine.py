import json


def mock_answer(question: str, course_title: str, chapter_title: str) -> str:
    text = question.lower()
    if "hdfs" in text or "hadoop" in text:
        return (
            f"针对《{course_title}》中的提问，先给结论：\n\n"
            "**HDFS 是面向大规模数据的分布式文件系统，设计思想是「一次写入、多次读取」。**\n\n"
            "核心要点：\n"
            "1. NameNode 管理元数据（目录树与块映射），DataNode 存储真实数据块，默认块大小 128MB；\n"
            "2. 默认 3 副本机制兼顾容错与读带宽；\n"
            "3. 适合顺序读写的大文件，不适合大量小文件与随机写。\n\n"
            "示例：`hdfs dfs -put local.csv /data/input/` 表示把本地文件写入 HDFS。\n\n"
            "知识点拓展：可进一步了解 HDFS Federation 如何缓解单 NameNode 的内存瓶颈。"
        )
    if "mapreduce" in text or "shuffle" in text:
        return (
            "**结论：MapReduce 把计算抽象为 Map → Shuffle → Reduce 三个阶段。**\n\n"
            "1. Map 阶段并行处理分片数据，输出键值对；\n"
            "2. Shuffle 按 key 分区、排序、合并，是性能瓶颈所在；\n"
            "3. Reduce 对相同 key 的值聚合，输出最终结果。\n\n"
            "示例：单词计数中 Map 输出 `(word, 1)`，Reduce 得到 `(word, total)`。\n\n"
            "知识点拓展：Shuffle 的 Combiner 预聚合可以显著减少网络传输量。"
        )
    if "pandas" in text or "dataframe" in text or "python" in text:
        return (
            "**结论：pandas 的核心是 DataFrame（二维表）与 Series（一维列），适合中等规模数据分析。**\n\n"
            "1. 用 `read_csv` 读入数据，`head/info/describe` 完成数据概览；\n"
            "2. 用 `groupby + agg` 做分组聚合，用 `merge` 完成表关联；\n"
            "3. 缺失值优先分析原因，再选择 `dropna` 或 `fillna`。\n\n"
            "示例：`df.groupby('city')['sales'].sum().sort_values(ascending=False)`\n\n"
            "知识点拓展：数据量超过内存时可改用 Polars 或 DuckDB。"
        )
    if "过拟合" in text or "正则" in text or "overfit" in text:
        return (
            "**结论：过拟合是模型把训练集噪声也学了进去，表现为训练集好、验证集差。**\n\n"
            "常用对策：\n"
            "1. 增加数据量或数据增强；\n"
            "2. L1/L2 正则化、Dropout、早停；\n"
            "3. 交叉验证评估泛化能力，简化模型结构。\n\n"
            "示例：`Ridge(alpha=1.0)` 即加入 L2 正则的线性回归。\n\n"
            "知识点拓展：偏差-方差分解能帮助判断当前是欠拟合还是过拟合。"
        )
    if "索引" in text or "sql" in text or "mysql" in text:
        return (
            "**结论：索引的本质是用额外空间换取查询速度，MySQL InnoDB 使用 B+ 树索引。**\n\n"
            "1. 主键索引即聚簇索引，叶子节点存放整行数据；\n"
            "2. 普通索引需要回表，覆盖索引可避免回表；\n"
            "3. 索引列上做函数运算、前导模糊查询会导致索引失效。\n\n"
            "示例：`CREATE INDEX idx_user_course ON favorites(user_id, course_id);`\n\n"
            "知识点拓展：联合索引遵循最左前缀原则，设计时把选择性高的列放前面。"
        )
    return (
        f"关于《{course_title}》的提问「{question[:60]}」，可以从三个层次理解：\n\n"
        "**结论：先建立概念边界，再理解运行机制，最后通过代码验证。**\n\n"
        "1. 概念层：明确该知识点解决什么问题、适用场景与限制；\n"
        "2. 原理层：梳理关键流程与核心数据结构，画一张流程图；\n"
        "3. 实践层：写一个最小可运行示例，观察输入输出变化。\n\n"
        f"结合当前章节《{chapter_title}》，建议先完成章节中的示例，再尝试改动参数观察结果差异。\n\n"
        "知识点拓展：把这个问题与已学章节建立联系，形成自己的知识图谱，比孤立记忆更有效。"
    )


def mock_learning_path(goal: str, weekly_hours: int, weak_points: str) -> str:
    hours = max(int(weekly_hours), 1)
    stage_weeks = max(1, round(6 / hours)) if hours <= 6 else 1
    goal_lower = goal.lower()
    if any(word in goal for word in ["AI", "人工智能", "大模型", "算法"]) or "ai" in goal_lower:
        stages = [
            ("基础夯实", "Python 语法、NumPy/pandas、数学基础", "完成 2 个数据分析小作业"),
            ("机器学习", "监督学习、模型评估、特征工程", "在公开数据集上完成一次完整建模"),
            ("深度学习", "PyTorch 基础、CNN/RNN、Transformer 入门", "复现一个图像分类项目"),
            ("项目实战", "LLM API 应用、RAG 检索问答、工程化部署", "交付一个可演示的 AI 应用"),
        ]
        advice = "每周至少留出 2 小时动手编码，避免只看视频；用项目驱动学习，每阶段产出一个可展示成果。"
    elif any(word in goal for word in ["大数据", "Hadoop", "Spark", "数据开发"]):
        stages = [
            ("基础夯实", "Python + SQL 基础、Linux 常用命令", "独立完成数据清洗脚本"),
            ("Hadoop 生态", "HDFS、MapReduce、YARN 原理与部署", "搭起 3 节点伪分布式集群"),
            ("Spark 计算", "Spark SQL、DataFrame、流处理入门", "完成亿级日志的离线统计"),
            ("项目实战", "数仓分层建模、调度与数据质量", "交付一个离线数仓小项目"),
        ]
        advice = "大数据重在环境与调优经验，建议边学边记录踩坑笔记；优先掌握 SQL 与 Spark SQL。"
    elif any(word in goal for word in ["鸿蒙", "HarmonyOS", "ArkTS"]):
        stages = [
            ("语言基础", "ArkTS 语法、声明式 UI 基础", "完成 3 个静态页面"),
            ("UI 与状态", "ArkUI 布局、状态管理、路由", "完成一个多页面应用"),
            ("端云一体", "网络请求、云函数、数据存储", "实现登录与列表数据拉取"),
            ("项目实战", "上架规范、性能优化、签名打包", "交付一个可安装的 HAP 应用"),
        ]
        advice = "鸿蒙生态迭代快，以官方文档为准；每学一个组件立即写 Demo，避免只读不写。"
    else:
        stages = [
            ("目标澄清", "明确目标岗位的 JD 与能力项", "输出一张能力差距清单"),
            ("基础补齐", "编程基础、数据库、计算机网络", "完成基础题库练习"),
            ("专项突破", "针对薄弱点做专题训练", "薄弱点正确率提升 30%"),
            ("项目实战", "完整项目从需求到部署", "交付可演示项目并复盘"),
        ]
        advice = "把大目标拆成每周可验证的小任务，按周复盘完成率；薄弱点优先补，不要回避。"
    rows = "\n".join(
        f"| {name} | {stage_weeks} 周 | {content} | {accept} |" for name, content, accept in stages
    )
    weak = weak_points.strip() or "暂未填写，建议先做一次自测定位薄弱点"
    return (
        f"## 你的个性化学习路径（目标：{goal}）\n\n"
        f"每周可投入：**{hours} 小时**　薄弱点：{weak}\n\n"
        "| 阶段 | 周期 | 学习内容 | 验收标准 |\n|---|---|---|---|\n"
        f"{rows}\n\n"
        "**执行建议：**\n"
        f"1. {advice}\n"
        "2. 每周日晚复盘完成率，低于 70% 时下调下周任务量而不是放弃计划。"
    )


def mock_grade(title: str, language: str, code: str) -> str:
    lines = [line for line in code.splitlines() if line.strip()]
    issues = []
    correct = 65
    readable = 70
    robust = 60
    if len(lines) < 5:
        issues.append({"line": 0, "severity": "high", "suggestion": "代码行数过少，可能未覆盖题目要求的完整逻辑。"})
        correct -= 15
    if any(token in code for token in ["def ", "function ", "class "]):
        correct += 10
        readable += 5
    if any(token in code for token in ["try", "except", "catch"]):
        robust += 15
    else:
        issues.append({"line": 0, "severity": "medium", "suggestion": "建议补充异常处理，避免非法输入导致程序崩溃。"})
    if "print(" in code:
        issues.append({"line": 0, "severity": "low", "suggestion": "调试输出建议使用日志或断言，交付版本移除多余 print。"})
        readable -= 5
    if any(name in code for name in [" a ", " b ", " x1 "]) or "temp" in code:
        issues.append({"line": 0, "severity": "low", "suggestion": "变量命名建议表达业务含义，如 user_count、total_price。"})
        readable -= 10
    else:
        readable += 10
    if "#" in code or "//" in code:
        readable += 5
    if not code.strip().endswith(("}", "return", "print)", "print(f\")")) and language == "python":
        issues.append({"line": len(lines), "severity": "medium", "suggestion": "请检查函数是否显式 return 结果，避免返回 None。"})
    score = max(40, min(95, round((correct * 0.5 + readable * 0.25 + robust * 0.25))))
    per_line = max(1, len(lines) - 2)
    if not issues:
        issues.append({"line": per_line, "severity": "low", "suggestion": "可在关键分支补充边界用例，提升健壮性。"})
    result = {
        "score": score,
        "dimension_scores": {
            "正确性": max(0, min(100, correct)),
            "可读性": max(0, min(100, readable)),
            "健壮性": max(0, min(100, robust)),
        },
        "issues": issues,
        "summary": f"《{title}》整体完成度尚可，建议优先处理高严重度问题，再优化命名与异常处理。",
    }
    return json.dumps(result, ensure_ascii=False)


def mock_study_report(stats: dict) -> str:
    total_minutes = int(stats.get("total_minutes", 0))
    course_count = int(stats.get("course_count", 0))
    avg_progress = int(stats.get("avg_progress", 0))
    weak_points = stats.get("weak_points") or "暂无明显薄弱点"
    hours = round(total_minutes / 60, 1)
    if total_minutes == 0:
        highlight = "本周尚无学习记录，建议从收藏课程中选择一门开始，先完成第一章建立节奏。"
    elif total_minutes < 120:
        highlight = f"本周学习 {hours} 小时，已形成起步习惯，但学习时长偏短，建议固定每天 30 分钟。"
    else:
        highlight = f"本周学习 {hours} 小时、覆盖 {course_count} 门课程，投入度良好，平均进度达到 {avg_progress}%。"
    return (
        f"## 本周概览\n"
        f"- 学习总时长：**{hours} 小时**（{total_minutes} 分钟）\n"
        f"- 学习课程数：**{course_count} 门**\n"
        f"- 平均进度：**{avg_progress}%**\n\n"
        f"## 学习亮点\n{highlight}\n\n"
        f"## 薄弱点分析\n当前薄弱点为「{weak_points}」。建议回看对应章节的示例代码，并完成配套练习题验证理解。\n\n"
        "## 下周建议\n"
        "1. 保持每天固定的学习时段，优先推进进度最低的一门课程；\n"
        "2. 对薄弱知识点采用「看一遍 → 写一遍 → 讲一遍」的方式巩固；\n"
        "3. 周末用 AI 助手做一次章节问答自测，把错题整理进笔记。"
    )