# -*- coding: utf-8 -*-
"""生成商策 PPT（B 赛道，16 页）+ 每页演讲备注。无岭院模版，用通用深蓝金主题。"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

NAVY = RGBColor(0x0E, 0x1A, 0x33)
NAVY2 = RGBColor(0x1F, 0x35, 0x60)
GOLD = RGBColor(0xD4, 0xAF, 0x37)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
TEXT = RGBColor(0x1F, 0x2A, 0x44)
MUTED = RGBColor(0x6B, 0x72, 0x80)
LIGHT = RGBColor(0xB0, 0xBE, 0xD4)

FONT = "微软雅黑"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def add_rect(slide, x, y, w, h, color):
    from pptx.enum.shapes import MSO_SHAPE
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


def add_text(slide, x, y, w, h, text, size, color, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = align
    r = p.runs[0]
    r.font.size = Pt(size)
    r.font.color.rgb = color
    r.font.bold = bold
    r.font.name = FONT
    return tb


def set_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def title_slide(title, subtitle, notes):
    s = prs.slides.add_slide(BLANK)
    add_rect(s, 0, 0, prs.slide_width, prs.slide_height, NAVY)
    add_rect(s, 0, Inches(4.6), prs.slide_width, Pt(4), GOLD)
    add_text(s, Inches(0.8), Inches(1.5), Inches(11.7), Inches(2.4), title, 42, WHITE, bold=True)
    add_text(s, Inches(0.8), Inches(3.9), Inches(11.7), Inches(0.6), subtitle, 20, GOLD, bold=True)
    add_text(s, Inches(0.8), Inches(5.2), Inches(11.7), Inches(1.0),
             "暑假不回家队\n国元证券 · CFA 商业策划大赛 B 赛道", 14, LIGHT)
    set_notes(s, notes)
    return s


def content_slide(title, bullets, notes):
    s = prs.slides.add_slide(BLANK)
    add_rect(s, 0, 0, prs.slide_width, Pt(3), GOLD)
    add_text(s, Inches(0.7), Inches(0.35), Inches(12), Inches(0.8), title, 28, NAVY, bold=True)
    tb = s.shapes.add_textbox(Inches(0.8), Inches(1.35), Inches(11.7), Inches(5.7))
    tf = tb.text_frame
    tf.word_wrap = True
    first = True
    for item in bullets:
        if isinstance(item, tuple):
            text, level, size = item
        else:
            text, level, size = item, 0, 18
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.text = ("• " if level == 0 else "– ") + text
        p.level = level
        r = p.runs[0]
        r.font.size = Pt(size)
        r.font.name = FONT
        r.font.color.rgb = TEXT if level == 0 else MUTED
        p.space_after = Pt(8)
    set_notes(s, notes)
    return s


# 1 封面
title_slide("合规智盾 Agent", "基于 AI Agent 的金融合规智能自检与申报系统",
"【开场 30 秒】\n语气：自信、平稳。\n先报队名和题目，一句话点题：'我们把 CFA 道德准则，变成一线员工随开随用的合规 Agent。'\n强调'Agent'这个词——这是本次大赛主题的关键词，第一句就要让评委记住你是紧扣主题的。")

# 2 执行摘要
content_slide("执行摘要：一句话 + 三个亮点", [
    "一句话：员工用一句话描述行为 → Agent 自动识别准则、评估风险、执行申报",
    ("亮点一：不是问答工具，而是能「执行任务」的 Agent", 1, 16),
    ("亮点二：RAG 约束，每个结论都有题库案例依据（可解释）", 1, 16),
    ("亮点三：离线优先 + 邮件触达，真正可落地（安全）", 1, 16),
],
"【45 秒】\n这页是总纲，先把三个亮点亮出来，后面逐页展开。\n讲法：'我们的核心，是把合规从「提建议」变成「替办事」。'")

# 3 灵感来源
content_slide("灵感来源：从一道题想到一个 Agent", [
    "备考 CFA 道德时的真实观察：错题不在「记不住条文」，而在「具体场景如何对号入座」",
    "核心洞察：道德合规的难点不是「知识」，而是「判断」与「行动」",
    "结合大赛主题：AI 从「回答问题」跃迁为「执行任务」，恰好补上合规缺失的一环",
    "于是：把 CFA 准则，变成一个能替你「做完该做的」的 Agent",
],
"【50 秒】\n这是故事性最强的一页，讲得生动一点。\n讲法：'我们做 230 道题时发现，错的不是背准则，是不知道怎么套场景——这背后是个真问题。'\n把一个'备考点'升华为'行业痛点'，是这页的目的，体现'灵感真实、接地气'。")

# 4 切题程度
content_slide("切题程度：三层严格对应", [
    "场景对应：三大场景选「合规」→ 规则解析/制度比对/异常识别/报告生成",
    "能力对应：自主感知/分析决策/任务执行/持续优化，逐条落地",
    "标准对应：准确性/可解释性/安全性/落地能力，逐条满足",
    "结论：方案始终紧扣主题，不跑题、可衡量",
],
"【50 秒】\n这页直接回应评委'你们切题吗'的疑问，主动把话说在前面。\n讲法：'赛道给了场景、能力、标准三把尺子，我们用这三把尺子量自己，每一把都对得上。'\n评委可能追问，提前把三层对应背熟。")

# 5 痛点
content_slide("合规管理的三大痛点", [
    "判断门槛高：准则表述开放，一线员工判断因人、因时而异",
    "披露义务易遗漏：不知道该不该披露、向谁披露、披露什么",
    "申报与留痕割裂：传统工具只提示风险，不执行申报",
    ("数据佐证：230 题库中准则应用指南占 64.3%，错题集中在客户/雇主责任", 1, 16),
],
"【45 秒】\n把痛点讲具体，让评委有画面感。\n讲法：'员工不是不想合规，是面对抽象准则，不知道该不该、向谁、披露什么。'\n最后一句点出：'所以我们要做的不只是提示，更是帮他办成。'")

# 6 方案概述
content_slide("方案概述：一个能「执行」的合规 Agent", [
    "员工用一句话描述行为 → Agent 自动识别准则、评估风险、执行申报",
    "产品形态：PWA 三视图（自检 / 准则速查 / 历史）+ 申报与自证弹窗",
    "支持语音输入、离线可用、多端适配",
    "关键定位：不是问答机器人，而是能替你干活的 Agent",
],
"【45 秒】\n介绍产品形态，点到为止，细节留给演示页。\n讲法：'它长这样——一个随开随用的网页应用，手机电脑都能用，断网也能用。'\n为后面的现场演示做铺垫。")

# 7 四大能力
content_slide("Agent 四大核心能力 · 逐一落地", [
    ("自主感知 → 意图识别（关键词 + 正则 + 语义三级）", 0, 20),
    ("分析决策 → 风险评级 + 22 子条款匹配 + RAG 案例检索", 0, 20),
    ("任务执行 → 生成申报单 + 一键发邮件 + 自证声明", 0, 20),
    ("持续优化 → 增量知识库 + 结果缓存 + 行为留痕", 0, 20),
    "四大能力一个不落，且全部真实可运行",
],
"【60 秒】★核心页，务必讲透\n这页是'切题'最硬的证据。讲法：'赛道要求 Agent 四大能力，我们一个不落——感知、决策、执行、优化，而且全部真实可运行，不是 PPT 概念。'\n每讲一个能力，可以稍停一下，让评委看到对应关系。")

# 8 Agent 的作用
content_slide("Agent 起到了什么作用", [
    "对员工：从「凭感觉」到「有依据」，一句话换来判断+清单+申报单",
    "对合规部门：从「被动审查」到「主动申报+留痕可查」",
    "对机构：合规知识沉淀为统一底座，降本增效",
    "对行业：证明「规则驱动+案例约束+任务执行」范式可行",
],
"【45 秒】\n讲清 Agent 的'价值升维'。\n讲法：'关键在最后一环——任务执行。一般的 AI 只给建议，我们的 Agent 替你把申报发出去、把留痕存下来。这一步，就是从工具到 Agent 的本质。'")

# 9 技术架构
content_slide("技术架构：RAG 约束，结论有据可依", [
    "输入 → 意图分类 → 向量检索 Top-5 → 结构化输出 → 任务执行",
    ("技术栈：FastAPI + ChromaDB + RAG + PWA + SMTP", 1, 16),
    "决策一：RAG 约束而非裸 LLM（案例为依据，抑制幻觉）",
    "决策二：规则引擎兜底（没网、没 API 也能用）",
    "决策三：离线优先（数据不出本机，安全可落地）",
],
"【50 秒】\n技术页不要念技术名词，要讲'为什么这么选'。\n讲法：'我们不裸用大模型，而是用 RAG 让每个结论都有案例兜底；再加规则引擎，没网也能跑。这些设计，都是冲着「安全、可解释、可落地」去的。'")

# 10 现场演示
content_slide("现场演示：从识别到邮件触达的闭环", [
    "输入：客户送我去打高尔夫，还承担我出差的机票和酒店费用",
    "① 高风险判定 + 红色风险拦截 + 准则匹配（I(B)/IV(B)/VI(A)）",
    "② 引用题库类似案例（M3-Q30 会议差旅招待）",
    "③ 生成带唯一编号的申报单",
    "④ 一键发送邮件 → 合规部门邮箱实时收到",
    "（现场投屏演示 / 播放录屏视频）",
],
"【90 秒】★记忆点页，全场最值得花时间\n讲法：边操作边讲，节奏放慢。\n'大家看，输入这句话，系统立刻给出高风险和拦截，还引用了题库案例；点前往申报，自动生成带编号的申报单；点一键发送，邮件直接到合规部邮箱。'\n最后展示邮箱实时收到，强调'这就是从识别到行动的完整闭环'。\n若现场网络不稳，立即切到提前录好的视频，保证不冷场。")

# 11 数据与实证
content_slide("数据基础与实证结果", [
    "230 道 CFA 题库 · 22 子条款全覆盖 · 8 类行为 · 161 合规案例",
    "29 项自动化测试全部通过（分类器 / RAG / API）",
    ("收礼招待 → I(B)/IV(B)/VI(A)，引用 M3-Q30", 1, 16),
    ("额外报酬 → IV(B)/VI(C)，引用 M3-Q12", 1, 16),
    ("无关输入 → 正确返回 uncertain，不误报", 1, 16),
],
"【45 秒】\n用数据证明'做得出来、测得过'。\n讲法：'数据来源权威、处理规范，而且 29 项测试全过，边界情况也不会误报。'")

# 12 五大挑战
content_slide("五大挑战 · 逐一工程化应对", [
    "模型幻觉 → RAG 约束 + 温度 0.3 + 规则引擎兜底",
    "数据安全 → 离线优先，数据不出本机 + 私有化部署",
    "可解释性 → 每个结论附带准则条款与题库案例",
    "权限管理 → 申报留痕、编号可追溯、审批流可扩展",
    "责任边界 → 辅助决策定位，高风险强制人工确认",
],
"【60 秒】★关键页，评委必问\n讲法：'赛道提了五大挑战，我们不是回避，是每一个都有工程实现。'\n逐条念，念完补一句：'这些不是纸面承诺，是已经在系统里落地的东西。'\n这页要和第六章的问答准备对上，评委追问时从这里展开。")

# 13 改进过程
content_slide("改进过程：从工具到 Agent 的六次迭代", [
    "① 数据筑基：230 题结构化，建知识底座",
    "② 感知决策：8 类意图分类 + 风险评级",
    "③ 可解释：引入 RAG 案例检索",
    "④ 关键跃迁：加入任务执行（申报+发邮件），变成 Agent",
    "⑤ 完善闭环：风险拦截 + 合规自证",
    "⑥ 落地优化：邮件改国内 SMTP + 界面优化 + 演示方案",
],
"【50 秒】\n这页呼应'持续优化'能力，也体现真实投入。\n讲法：'我们没有一步到位，而是经历了六次迭代，第四步是关键的质变——加上任务执行，它才真正从一个工具变成 Agent。'\n可点一句：'持续优化不是口号，是我们实际走过的路。'")

# 14 使用价值与可推广性
content_slide("使用价值与可推广性", [
    "使用价值：员工降风险 · 合规部降成本 · 机构建文化",
    "横向：CFA 准则 → 软美元 / GIPS / 反洗钱等更广合规域",
    "纵向：同一架构复用于投资研究、风险管理场景",
    "多智能体：自检 / 申报 / 审查 / 审计 Agent 协同",
    "跨行业：医药、法律、证券等强监管行业可复用",
],
"【45 秒】\n展示方案的想象空间和可复制性。\n讲法：'它不止解决 CFA 合规，这套「规则驱动+案例约束+任务执行」的方法论，可以复制到更广的合规域，甚至投资和风控场景。'")

# 15 商业模式
content_slide("商业模式与落地路径", [
    "三层产品：个人免费 / 团队订阅 / 定制私有化",
    "四阶段落地：MVP → 机构试点 → 扩域 → 规模化",
    "收入来源：企业订阅 + 私有化授权 + 内容授权 + 培训增值",
],
"【35 秒】\n简略带过，不要展开太多，时间留给演示和挑战应对。\n讲法：'商业模式上分三层，从免费引流到企业订阅和私有化部署。'")

# 16 结论 + 团队 + 感谢
content_slide("创新点 · 团队 · 感谢", [
    "创新一：Agent 范式下沉到个人合规行为辅助",
    "创新二：规则驱动 + 案例引用，保证可解释",
    "创新三：离线优先，保证安全可落地",
    "",
    "韩天翼（队长）：统筹+架构+核心研发 ｜ 彭德东：数据+调研 ｜ 禹夏航：测试+展示",
    "感谢各位评委老师，欢迎提问",
],
"【40 秒】\n收尾三连：创新点 → 团队 → 感谢。\n讲法：'我们的创新在于，把 Agent 从机构级下沉到个人合规辅助，用规则驱动保证可解释，用离线架构保证可落地。以上是暑假不回家队的汇报，感谢评委，欢迎提问。'\n说完站在原地等提问，不要急着下台。")

out = r"D:\cfa-compliance-assistant\商策PPT_暑假不回家队.pptx"
prs.save(out)
print("已生成:", out)
