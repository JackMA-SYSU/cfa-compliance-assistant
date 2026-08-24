# -*- coding: utf-8 -*-
"""生成商策 PPT（B 赛道，13 页）。无岭院模版时先用通用深蓝金主题，内容可直接套用模版。"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

NAVY = RGBColor(0x0E, 0x1A, 0x33)
NAVY2 = RGBColor(0x1F, 0x35, 0x60)
GOLD = RGBColor(0xD4, 0xAF, 0x37)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
TEXT = RGBColor(0x1F, 0x2A, 0x44)
MUTED = RGBColor(0x6B, 0x72, 0x80)

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


def title_slide(title, subtitle):
    s = prs.slides.add_slide(BLANK)
    add_rect(s, 0, 0, prs.slide_width, prs.slide_height, NAVY)
    add_rect(s, 0, Inches(4.6), prs.slide_width, Pt(4), GOLD)
    add_text(s, Inches(0.8), Inches(1.6), Inches(11.7), Inches(2.2), title, 40, WHITE, bold=True)
    add_text(s, Inches(0.8), Inches(3.9), Inches(11.7), Inches(0.6), subtitle, 20, GOLD, bold=True)
    add_text(s, Inches(0.8), Inches(5.2), Inches(11.7), Inches(1.0),
             "暑假不回家队\n国元证券 · CFA 商业策划大赛 B 赛道", 14, RGBColor(0xB0, 0xBE, 0xD4))
    return s


def content_slide(title, bullets):
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
    return s


# 1 封面
title_slide("合规智盾 Agent", "基于 AI Agent 的金融合规智能自检与申报系统")

# 2 主题解读
content_slide("主题解读：为什么选「合规」场景", [
    "AI 正从「辅助分析工具」向「智能执行 Agent」范式跃迁",
    ("投资靠判断 · 风控靠数据 · 合规靠规则", 1, 16),
    ("CFA 准则 22 条子条款是可结构化、可枚举的规则集合", 1, 16),
    "合规场景最适合 Agent 落地：规则解析、制度比对、异常识别、报告生成",
    "愿景：构建安全、可靠、可解释、可落地的合规智能体",
])

# 3 痛点
content_slide("合规管理的三大痛点", [
    "判断门槛高：准则表述开放，一线员工判断因人、因时而异",
    "披露义务易遗漏：不知道该不该披露、向谁披露、披露什么",
    "申报与留痕割裂：传统工具只提示风险，不执行申报",
    ("数据佐证：230 题库中准则应用指南占 64.3%，错题集中在客户/雇主责任", 1, 16),
    "结论：员工不是不想合规，而是缺少可执行的决策工具",
])

# 4 方案概述
content_slide("方案概述：一个能「执行」的合规 Agent", [
    "员工用一句话描述行为 → Agent 自动识别准则、评估风险、执行申报",
    "产品形态：PWA 三视图（自检 / 准则速查 / 历史）+ 申报与自证弹窗",
    "不是问答机器人，而是能替你干活的 Agent",
    "支持语音输入、离线可用、多端适配",
])

# 5 四大能力映射
content_slide("Agent 四大核心能力 · 逐一落地", [
    ("自主感知 → 意图识别（关键词 + 正则 + 语义三级）", 0, 20),
    ("分析决策 → 风险评级 + 22 子条款匹配 + RAG 案例检索", 0, 20),
    ("任务执行 → 生成申报单 + 一键发邮件 + 自证声明", 0, 20),
    ("持续优化 → 增量知识库 + 结果缓存 + 行为留痕", 0, 20),
    "四大能力一个不落，且全部真实可运行",
])

# 6 技术架构
content_slide("技术架构：RAG 约束，结论有据可依", [
    "输入 → 意图分类 → 向量检索 Top-5 → 结构化输出 → 任务执行",
    ("技术栈：FastAPI + ChromaDB + RAG + PWA + SMTP", 1, 16),
    "关键决策一：RAG 约束而非裸 LLM（案例为依据，抑制幻觉）",
    "关键决策二：规则引擎兜底（没网、没 API 也能用）",
    "关键决策三：离线优先（数据不出本机，安全可落地）",
])

# 7 现场演示
content_slide("现场演示：从识别到邮件触达的闭环", [
    "输入：客户送我去打高尔夫，还承担我出差的机票和酒店费用",
    "① 高风险判定 + 红色风险拦截 + 准则匹配（I(B)/IV(B)/VI(A)）",
    "② 引用题库类似案例（M3-Q30 会议差旅招待）",
    "③ 生成带唯一编号的申报单",
    "④ 一键发送邮件 → 合规部门邮箱实时收到",
    "（现场投屏演示 / 播放录屏视频）",
])

# 8 数据基础
content_slide("数据基础：权威、规范、可追溯", [
    "230 道 CFA 一级道德题库（中英对照，含答案解析）",
    "22 条子条款全覆盖 · 8 类行为 · 161 个合规案例",
    "数据工程：PDF → 结构化字段（题号/准则/情景/标签/风险/动作）",
    "风险等级由准则映射 + 案例加权综合判定",
])

# 9 实证结果
content_slide("实证结果：测得过、跑得稳", [
    "29 项自动化测试全部通过（分类器 / RAG / API）",
    ("收礼招待 → I(B)/IV(B)/VI(A)，引用 M3-Q30", 1, 16),
    ("额外报酬 → IV(B)/VI(C)，引用 M3-Q12", 1, 16),
    ("无关输入 → 正确返回 uncertain，不误报", 1, 16),
])

# 10 五大挑战应对
content_slide("五大挑战 · 逐一工程化应对", [
    "模型幻觉 → RAG 约束 + 温度 0.3 + 规则引擎兜底",
    "数据安全 → 离线优先，数据不出本机 + 私有化部署",
    "可解释性 → 每个结论附带准则条款与题库案例",
    "权限管理 → 申报留痕、编号可追溯、审批流可扩展",
    "责任边界 → 辅助决策定位，高风险强制人工确认",
])

# 11 商业模式
content_slide("商业模式与落地路径", [
    "三层产品：个人免费 / 团队订阅 / 定制私有化",
    "四阶段落地：MVP → 机构试点 → 扩域（软美元/GIPS/反洗钱）→ 规模化",
    "收入来源：企业订阅 + 私有化授权 + 内容授权 + 培训增值",
])

# 12 创新点与结论
content_slide("创新点与结论", [
    "创新一：Agent 范式下沉到个人合规行为辅助（而非传统问答）",
    "创新二：规则驱动 + 案例引用，保证可解释",
    "创新三：离线优先架构，保证安全可落地",
    "结论：把抽象道德准则，变成可执行的合规闭环",
])

# 13 团队分工
content_slide("团队分工 · 感谢", [
    ("韩天翼（队长）：项目统筹 + 产品/架构设计 + 核心研发", 0, 18),
    ("彭德东：数据工程 + 行业调研 + 实证分析", 0, 18),
    ("禹夏航：系统测试 + 演示材料 + 现场支持", 0, 18),
    "感谢各位评委老师，欢迎提问",
])

out = r"D:\cfa-compliance-assistant\商策PPT_暑假不回家队.pptx"
prs.save(out)
print("已生成:", out)
