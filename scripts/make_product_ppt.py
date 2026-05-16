from __future__ import annotations

import html
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "campus-finance-buddy"
OUT = PROJECT / "docs" / "钱前问问_产品方案报告.pptx"
TEMPLATE = next(ROOT.glob("*PPT*.pptx"))

W = 12_192_000
H = 6_858_000
NAVY = "08254D"
RED = "C00000"
SOFT_BLUE = "EEF3F8"
LIGHT_LINE = "D8E1EC"
TEXT = "243033"
MUTED = "5F6D7A"


def emu(value: float) -> int:
    return int(value * 914400)


def esc(value: str) -> str:
    return html.escape(str(value), quote=True)


class SlideBuilder:
    def __init__(self, title: str, page: int):
        self.title = title
        self.page = page
        self.parts: list[str] = []
        self.sid = 20

    def next_id(self) -> int:
        self.sid += 1
        return self.sid

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: str = "FFFFFF",
        line: str = "DDE7E1",
        radius: bool = True,
        alpha: int | None = None,
    ) -> None:
        shape_id = self.next_id()
        geom = "roundRect" if radius else "rect"
        alpha_xml = f'<a:alpha val="{alpha}"/>' if alpha else ""
        fill_xml = f'<a:solidFill><a:srgbClr val="{fill}">{alpha_xml}</a:srgbClr></a:solidFill>'
        line_xml = '<a:ln><a:noFill/></a:ln>' if not line else f'<a:ln w="9525"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>'
        self.parts.append(
            f"""
            <p:sp>
              <p:nvSpPr><p:cNvPr id="{shape_id}" name="Shape {shape_id}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
              <p:spPr><a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
                <a:prstGeom prst="{geom}"><a:avLst/></a:prstGeom>{fill_xml}{line_xml}</p:spPr>
              <p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody>
            </p:sp>
            """
        )

    def shape(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        prst: str,
        fill: str = "FFFFFF",
        line: str = "DDE7E1",
        alpha: int | None = None,
    ) -> None:
        shape_id = self.next_id()
        alpha_xml = f'<a:alpha val="{alpha}"/>' if alpha else ""
        fill_xml = f'<a:solidFill><a:srgbClr val="{fill}">{alpha_xml}</a:srgbClr></a:solidFill>'
        line_xml = '<a:ln><a:noFill/></a:ln>' if not line else f'<a:ln w="12700"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>'
        self.parts.append(
            f"""
            <p:sp>
              <p:nvSpPr><p:cNvPr id="{shape_id}" name="Shape {shape_id}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
              <p:spPr><a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
                <a:prstGeom prst="{prst}"><a:avLst/></a:prstGeom>{fill_xml}{line_xml}</p:spPr>
              <p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody>
            </p:sp>
            """
        )

    def line(self, x: float, y: float, w: float, color: str = "8AA79A", height: float = 0.02) -> None:
        self.rect(x, y, w, height, fill=color, line="", radius=False)

    def text(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        paragraphs: list[str] | str,
        size: int = 18,
        color: str = "243033",
        bold: bool = False,
        fill: str | None = None,
        line: str = "",
        align: str = "l",
        valign: str = "t",
        name: str = "Text",
        radius: bool = True,
    ) -> None:
        shape_id = self.next_id()
        if isinstance(paragraphs, str):
            paragraphs = [paragraphs]
        fill_xml = "<a:noFill/>" if fill is None else f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
        line_xml = '<a:ln><a:noFill/></a:ln>' if not line else f'<a:ln w="9525"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>'
        paras = []
        for p in paragraphs:
            p = p.rstrip()
            if not p:
                paras.append("<a:p/>")
                continue
            paras.append(
                f"""
                <a:p>
                  <a:pPr algn="{align}"/>
                  <a:r>
                    <a:rPr lang="zh-CN" sz="{size * 100}" b="{'1' if bold else '0'}">
                      <a:solidFill><a:srgbClr val="{color}"/></a:solidFill>
                      <a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/><a:cs typeface="Microsoft YaHei"/>
                    </a:rPr>
                    <a:t>{esc(p)}</a:t>
                  </a:r>
                </a:p>
                """
            )
        self.parts.append(
            f"""
            <p:sp>
              <p:nvSpPr><p:cNvPr id="{shape_id}" name="{esc(name)} {shape_id}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
              <p:spPr><a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
                <a:prstGeom prst="{'roundRect' if radius else 'rect'}"><a:avLst/></a:prstGeom>{fill_xml}{line_xml}</p:spPr>
              <p:txBody><a:bodyPr wrap="square" lIns="91440" tIns="45720" rIns="91440" bIns="45720" anchor="{valign}"/><a:lstStyle/>
                {''.join(paras)}
              </p:txBody>
            </p:sp>
            """
        )

    def header(self, section: str) -> None:
        self.text(0.62, 0.28, 2.2, 0.28, section, size=11, color=RED, bold=True)
        self.text(11.45, 6.98 - 0.55, 0.45, 0.25, f"{self.page:02d}", size=9, color="8A9898", bold=True, align="r")
        self.line(0.62, 0.64, 0.72, RED, 0.025)

    def title_block(self, title: str, subtitle: str = "") -> None:
        self.text(0.62, 0.78, 7.7, 0.48, title, size=25, color=NAVY, bold=True)
        if subtitle:
            self.text(0.64, 1.28, 8.0, 0.38, subtitle, size=12, color=MUTED)

    def xml(self) -> str:
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      {''.join(self.parts)}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def card(slide: SlideBuilder, x: float, y: float, w: float, h: float, title: str, bullets: list[str], tag: str = "", fill: str = "FFFFFF") -> None:
    slide.rect(x, y, w, h, fill=fill, line=LIGHT_LINE)
    if tag:
        slide.text(x + 0.18, y + 0.16, 0.7, 0.25, tag, size=9, color=RED, bold=True, fill="FFF0F0", line="")
    slide.text(x + 0.18, y + 0.45, w - 0.36, 0.35, title, size=15, color=NAVY, bold=True)
    slide.text(x + 0.18, y + 0.88, w - 0.36, h - 1.0, [f"• {b}" for b in bullets], size=10, color=MUTED)


def arrow(slide: SlideBuilder, x: float, y: float, label: str = "") -> None:
    slide.text(x, y, 0.36, 0.3, "→", size=22, color=RED, bold=True)
    if label:
        slide.text(x - 0.22, y + 0.36, 0.8, 0.22, label, size=8, color=MUTED, align="c")


def phone_frame(slide: SlideBuilder, x: float, y: float, w: float, h: float, title: str) -> None:
    slide.rect(x, y, w, h, fill="FFFFFF", line=NAVY)
    slide.rect(x + 0.12, y + 0.12, w - 0.24, 0.42, fill=NAVY, line=NAVY)
    slide.text(x + 0.22, y + 0.19, w - 0.44, 0.16, title, size=9, color="FFFFFF", bold=True)


def wire_button(slide: SlideBuilder, x: float, y: float, w: float, text: str, fill: str = SOFT_BLUE, color: str = NAVY) -> None:
    slide.text(x, y, w, 0.28, text, size=8, color=color, bold=True, fill=fill, line=LIGHT_LINE, align="c", valign="ctr")


def pill(slide: SlideBuilder, x: float, y: float, w: float, text: str, fill: str = SOFT_BLUE, color: str = NAVY) -> None:
    slide.text(x, y, w, 0.28, text, size=8, color=color, bold=True, fill=fill, line="", align="c", valign="ctr")


def browser_frame(slide: SlideBuilder, x: float, y: float, w: float, h: float, title: str) -> None:
    slide.rect(x, y, w, h, fill="FFFFFF", line=NAVY)
    slide.rect(x, y, w, 0.48, fill=NAVY, line=NAVY, radius=True)
    slide.shape(x + 0.16, y + 0.17, 0.13, 0.13, "ellipse", fill=RED, line=RED)
    slide.shape(x + 0.36, y + 0.17, 0.13, 0.13, "ellipse", fill="F4B400", line="F4B400")
    slide.shape(x + 0.56, y + 0.17, 0.13, 0.13, "ellipse", fill="34A853", line="34A853")
    slide.text(x + 0.86, y + 0.14, w - 1.1, 0.18, title, size=9, color="FFFFFF", bold=True)


def sidebar_proto(slide: SlideBuilder, x: float, y: float, w: float, h: float) -> None:
    slide.rect(x, y, 1.18, h, fill=NAVY, line=NAVY, radius=False)
    slide.text(x + 0.18, y + 0.28, 0.78, 0.22, "钱前问问", size=8, color="FFFFFF", bold=True, align="c")
    for i, item in enumerate(["对话", "起点", "热点", "复盘"]):
        fill = RED if i == 0 else "12345F"
        slide.text(x + 0.16, y + 0.85 + i * 0.46, 0.82, 0.24, item, size=7, color="FFFFFF", bold=True, fill=fill, line="", align="c", valign="ctr")


def chat_bubble(slide: SlideBuilder, x: float, y: float, w: float, text: str, who: str = "ai") -> None:
    fill = "F8FAFD" if who == "ai" else "FFF8F8"
    color = NAVY if who == "ai" else RED
    slide.text(x, y, w, 0.34, text, size=8, color=color, bold=False, fill=fill, line=LIGHT_LINE)


def metric_node(slide: SlideBuilder, x: float, y: float, w: float, title: str, value: str, fill: str = "F8FAFD") -> None:
    slide.rect(x, y, w, 0.7, fill=fill, line=LIGHT_LINE)
    slide.text(x + 0.12, y + 0.12, w - 0.24, 0.16, title, size=7, color=MUTED, bold=True)
    slide.text(x + 0.12, y + 0.37, w - 0.24, 0.18, value, size=10, color=NAVY, bold=True)


def hex_node(slide: SlideBuilder, x: float, y: float, w: float, h: float, title: str, sub: str, fill: str = "F8FAFD") -> None:
    slide.shape(x, y, w, h, "hexagon", fill=fill, line=LIGHT_LINE)
    slide.text(x + 0.12, y + 0.22, w - 0.24, 0.2, title, size=9, color=NAVY, bold=True, align="c")
    slide.text(x + 0.12, y + 0.5, w - 0.24, 0.18, sub, size=7, color=MUTED, align="c")


def add_cover(slide: SlideBuilder) -> None:
    slide.rect(0.0, 0.0, 13.34, 7.5, fill="FFFFFF", line="", radius=False)
    slide.rect(0.0, 0.0, 3.95, 7.5, fill=NAVY, line="", radius=False)
    slide.rect(3.95, 0.0, 0.08, 7.5, fill=RED, line="", radius=False)
    slide.text(0.72, 1.2, 2.6, 0.42, "AI 产品经理赛道", size=16, color="FFFFFF", bold=True)
    slide.text(0.72, 1.82, 2.7, 1.0, "钱前问问", size=35, color="FFFFFF", bold=True)
    slide.text(0.78, 2.92, 2.7, 0.88, "大学生入门理财陪伴 AI 智能体", size=18, color="FFFFFF", bold=True)
    slide.text(0.78, 5.95, 2.6, 0.34, "动钱之前，先把问题问清楚", size=12, color="FFFFFF")
    slide.text(4.75, 1.25, 6.9, 0.55, "从“想理财”到“会判断”的产品方案", size=28, color=NAVY, bold=True)
    slide.text(4.78, 2.05, 6.5, 0.68, "以学长学姐式智能体为入口，融合理财起点建档、RAG 知识问答、热点雷达、行为复盘与风险护栏，帮助大学生完成低门槛、非营销、可复盘的入门理财学习。", size=15, color=MUTED)
    card(slide, 4.82, 3.25, 2.25, 1.3, "用户", ["在校大学生", "生活费/奖学金/兼职收入"], "01", "FFFFFF")
    card(slide, 7.34, 3.25, 2.25, 1.3, "场景", ["动钱前提问", "看热点 / 想买入 / 亏损后"], "02", "FFFFFF")
    card(slide, 9.86, 3.25, 2.25, 1.3, "交付", ["网页智能体", "可体验二维码路径"], "03", "FFFFFF")
    slide.text(4.82, 6.35, 6.6, 0.28, "方案报告｜不含姓名、手机号、身份证等个人信息", size=10, color="8A9898")


def make_slides() -> list[str]:
    slides: list[SlideBuilder] = []

    s = SlideBuilder("封面", 1)
    add_cover(s)
    slides.append(s)

    s = SlideBuilder("产品画布", 2)
    s.header("PRODUCT CANVAS")
    s.title_block("产品画布：以大学生每一次“动钱前的困惑”为服务原点", "核心不是推荐理财产品，而是陪用户建立判断力")
    card(s, 0.65, 1.82, 3.8, 3.85, "问题和困扰", [
        "信息很多但真假难辨，用户最后仍独自承担决策",
        "看得到别人赚钱，看不到完整经验链条和亏损过程",
        "亏损金额不大，但可能放大焦虑、回本冲动和借钱风险",
        "缺少非营销、非带单、非攀比的理财学习搭子"
    ], "痛点", "F8FAFD")
    card(s, 4.75, 1.82, 3.8, 3.85, "解决方案", [
        "理财起点建档，先判断钱能不能动",
        "RAG + 大模型解释基础知识和理财黑话",
        "实时新闻 + 热点雷达训练市场理解能力",
        "计划复盘 + 风险护栏纠正冲动行为"
    ], "方案", "FFFFFF")
    card(s, 8.85, 1.82, 3.8, 3.85, "独特价值", [
        "用“学长学姐式过来人”身份建立继续聊天的欲望",
        "从“买什么”转向“是否理解、是否承受、是否可复盘”",
        "轻互动社区沉淀同类关注和学习状态",
        "高危行为以浮窗打断，而不是普通风险文案"
    ], "价值", "FFF8F8")
    slides.append(s)

    s = SlideBuilder("用户画像", 3)
    s.header("USER PERSONA")
    s.title_block("用户画像：有一点闲钱、想入门、但缺少经验和陪伴", "用 persona + JTBD 说明目标用户的真实决策环境")
    card(s, 0.75, 1.65, 3.15, 3.75, "画像 A：奖学金新手", [
        "资金：奖学金/生活费结余 1000-5000 元",
        "目标：想让钱别只是放着",
        "痛点：不知道哪些钱是真闲钱",
        "需要：低压力解释和资金边界"
    ], "A", "F8FAFD")
    card(s, 4.05, 1.65, 3.15, 3.75, "画像 B：热点刺激型", [
        "触发：短视频、财经热搜、同学收益截图",
        "目标：怕错过上涨机会",
        "痛点：看不懂板块逻辑和风险",
        "需要：热点降温和影响链条"
    ], "B", "FFFFFF")
    card(s, 7.35, 1.65, 3.15, 3.75, "画像 C：小额实践型", [
        "行为：已经买过基金/黄金/货币基金",
        "目标：想总结经验继续学习",
        "痛点：只看盈亏，不会复盘",
        "需要：行为复盘和下一步计划"
    ], "C", "FFF8F8")
    s.rect(10.72, 1.65, 1.55, 3.75, fill=NAVY, line=NAVY)
    s.text(10.92, 1.95, 1.15, 0.3, "JTBD", size=13, color="FFFFFF", bold=True, align="c")
    s.text(10.93, 2.52, 1.12, 1.7, "当我准备动一笔钱时，帮我判断这笔钱能不能动、这个信息能不能信、这个动作会不会让我失控。", size=10, color="FFFFFF", bold=True)
    s.text(0.82, 5.75, 11.0, 0.35, "用户不是没有需求，而是在专业知识、同伴经验、情绪承受和现金流稳定性上同时不足。", size=14, color=NAVY, bold=True)
    slides.append(s)

    s = SlideBuilder("用户旅程", 4)
    s.header("JOURNEY MAP")
    s.title_block("用户旅程泳道图：把理财冲动转化为学习闭环", "展示场景、情绪、产品触点和 AI 能力如何协同")
    lanes = [("用户行为", "奖学金到账", "刷到热点", "搜索/提问", "准备操作", "涨跌后复盘"),
             ("用户情绪", "兴奋", "怕错过", "困惑", "犹豫/冲动", "焦虑/总结"),
             ("产品触点", "建档弹窗", "今日关注", "知识问答", "行为复盘", "复盘卡"),
             ("AI 能力", "真假闲钱识别", "热点雷达", "RAG 解释", "风险判断", "计划调整")]
    y0 = 1.72
    for r, lane in enumerate(lanes):
        y = y0 + r * 0.9
        s.text(0.68, y + 0.12, 1.2, 0.26, lane[0], size=10, color="FFFFFF", bold=True, fill=NAVY if r % 2 == 0 else RED, line="")
        for c in range(1, 6):
            x = 2.0 + (c - 1) * 1.95
            s.rect(x, y, 1.55, 0.52, fill="F8FAFD" if r % 2 == 0 else "FFF8F8", line=LIGHT_LINE)
            s.text(x + 0.08, y + 0.12, 1.36, 0.18, lane[c], size=9, color=NAVY if r != 1 else RED, bold=(r in [0, 3]), align="c")
            if r == 0 and c < 5:
                arrow(s, x + 1.62, y + 0.08)
    s.rect(0.82, 5.55, 11.25, 0.55, fill="FFF8F8", line="F0D6D6")
    s.text(1.0, 5.68, 10.85, 0.22, "PM 结论：产品触点必须前置到“动钱前”，用建档、热点降温和复盘机制降低冲动交易概率。", size=13, color=NAVY, bold=True)
    slides.append(s)

    s = SlideBuilder("产品定位", 5)
    s.header("POSITIONING")
    s.title_block("产品定位：有专业知识的“过来人式”入门理财搭子", "不做投顾，不制造交易冲动，陪用户建立理财判断力")
    s.rect(0.78, 1.68, 4.0, 3.95, fill=NAVY, line=NAVY)
    s.text(1.05, 2.0, 3.45, 0.38, "一句话定位", size=14, color="FFFFFF", bold=True)
    s.text(1.05, 2.62, 3.35, 1.1, "面向大学生的入门理财陪伴 AI 智能体，帮助学生在动钱之前完成资金判断、知识学习、热点理解和行为复盘。", size=16, color="FFFFFF", bold=True)
    s.text(1.05, 4.35, 3.35, 0.56, "产品承诺：不荐股、不代投、不承诺收益。", size=12, color="FFFFFF")
    card(s, 5.15, 1.68, 2.1, 3.95, "身份", ["像学长学姐", "懂基础理财", "先共情再拆解"], "01", "F8FAFD")
    card(s, 7.55, 1.68, 2.1, 3.95, "能力", ["知识解释", "热点判断", "计划复盘", "风险识别"], "02", "FFFFFF")
    card(s, 9.95, 1.68, 2.1, 3.95, "边界", ["不推荐具体产品", "不做收益承诺", "不鼓励贷款杠杆"], "03", "FFF8F8")
    slides.append(s)

    s = SlideBuilder("产品架构", 6)
    s.header("PRODUCT ARCHITECTURE")
    s.title_block("产品架构：对话总入口 + 三个核心模块 + 风险护栏贯穿", "结构简单，但每个模块都能形成可演示闭环")
    s.rect(0.7, 1.65, 11.5, 0.62, fill=NAVY, line=NAVY)
    s.text(1.0, 1.82, 10.8, 0.22, "钱前问问 App Shell：侧边导航 / 固定聊天框 / 今日关注 / 风险浮窗", size=13, color="FFFFFF", bold=True, align="c")
    modules = [
        ("理财起点", ["沉浸式问卷", "资金分层", "真假闲钱识别"]),
        ("热点雷达", ["实时新闻", "AI 解读", "同频弹幕"]),
        ("计划复盘", ["小额计划", "行为复盘", "经验沉淀"]),
    ]
    for i, (m, subs) in enumerate(modules):
        x = 1.0 + i * 3.75
        card(s, x, 3.0, 3.05, 1.75, m, subs, f"M{i+1}", "FFFFFF")
        arrow(s, x + 3.14, 3.55) if i < 2 else None
    s.rect(2.45, 5.35, 8.2, 0.62, fill="FFF8F8", line="F0D6D6")
    s.text(2.65, 5.51, 7.8, 0.22, "风险护栏：贷款 / 杠杆 / 带单 / 保本高收益 / 回本冲动 → 浮窗打断", size=12, color=RED, bold=True, align="c")
    slides.append(s)

    s = SlideBuilder("智能体架构", 7)
    s.header("AGENT ARCHITECTURE")
    s.title_block("智能体技术架构：LLM + RAG + 新闻工具 + 风控规则", "体现不是写死问答，而是多能力编排")
    s.rect(0.75, 1.75, 2.2, 3.95, fill="F8FAFD", line=LIGHT_LINE)
    s.text(1.02, 2.05, 1.6, 0.26, "用户输入", size=14, color=NAVY, bold=True, align="c")
    s.text(0.98, 2.58, 1.7, 1.4, ["聊天问题", "点击新闻", "提交复盘", "触发风险词"], size=10, color=MUTED, align="c")
    arrow(s, 3.1, 3.3)
    s.rect(3.55, 1.75, 2.35, 3.95, fill=NAVY, line=NAVY)
    s.text(3.85, 2.05, 1.8, 0.26, "意图路由器", size=14, color="FFFFFF", bold=True, align="c")
    s.text(3.85, 2.62, 1.7, 1.2, ["知识问答", "热点分析", "计划复盘", "风险护栏"], size=10, color="FFFFFF", align="c")
    arrow(s, 6.08, 3.3)
    for i, (name, detail) in enumerate([
        ("RAG 知识库", "概念/资产/风险/费率"),
        ("新闻工具", "财经/金融/科技 RSS"),
        ("规则引擎", "贷款/杠杆/带单拦截"),
        ("智谱 LLM", "自然语言与个性化分析"),
    ]):
        y = 1.58 + i * 1.05
        s.rect(6.5, y, 2.4, 0.78, fill="FFFFFF", line=LIGHT_LINE)
        s.text(6.72, y + 0.12, 1.85, 0.2, name, size=11, color=NAVY, bold=True)
        s.text(6.72, y + 0.42, 1.85, 0.16, detail, size=8, color=MUTED)
    arrow(s, 9.15, 3.3)
    s.rect(9.55, 1.75, 2.45, 3.95, fill="FFF8F8", line="F0D6D6")
    s.text(9.85, 2.05, 1.85, 0.26, "智能输出", size=14, color=RED, bold=True, align="c")
    s.text(9.85, 2.62, 1.8, 1.4, ["解释", "拆解", "计划", "复盘", "风险弹窗"], size=10, color=MUTED, align="c")
    slides.append(s)

    s = SlideBuilder("核心原型", 8)
    s.header("INTERACTION PROTOTYPE")
    s.title_block("交互原型：钱前问问主界面中保真线框", "把智能体体验画出来：建档、对话、今日关注、风险护栏都在同一产品界面内发生")
    browser_frame(s, 0.7, 1.48, 11.65, 4.95, "钱前问问 Web App / Agent Workspace")
    sidebar_proto(s, 0.7, 1.96, 1.18, 4.47)
    s.rect(2.08, 2.12, 5.65, 3.72, fill="FFFFFF", line=LIGHT_LINE)
    s.text(2.28, 2.32, 2.5, 0.24, "对话智能体", size=13, color=NAVY, bold=True)
    pill(s, 5.82, 2.3, 0.85, "RAG", "EEF3F8", NAVY)
    pill(s, 6.78, 2.3, 0.55, "LLM", "FFF0F0", RED)
    chat_bubble(s, 2.35, 2.78, 3.75, "我有 3000 元奖学金，想开始理财", "user")
    chat_bubble(s, 2.35, 3.28, 4.8, "先别急着买。我们先看这笔钱是不是真闲钱。", "ai")
    chat_bubble(s, 2.35, 3.98, 4.25, "最近 AI 和芯片很火，会影响哪些板块？", "user")
    chat_bubble(s, 2.35, 4.48, 4.95, "热点雷达会拆：影响变量、相关板块、利好利空和新手观察点。", "ai")
    s.rect(2.35, 5.25, 4.75, 0.34, fill="F8FAFD", line=LIGHT_LINE)
    s.text(2.52, 5.33, 2.5, 0.12, "输入问题 / 粘贴新闻 / 描述准备操作", size=7, color=MUTED)
    wire_button(s, 6.55, 5.28, 0.55, "发送", RED, "FFFFFF")
    s.rect(7.95, 2.12, 3.9, 1.55, fill="F8FAFD", line=LIGHT_LINE)
    s.text(8.15, 2.32, 1.8, 0.2, "理财起点卡", size=12, color=NAVY, bold=True)
    metric_node(s, 8.16, 2.68, 1.05, "可学习", "300 元")
    metric_node(s, 9.38, 2.68, 1.05, "风险", "偏低")
    metric_node(s, 10.6, 2.68, 1.05, "动机", "看热点")
    s.rect(7.95, 3.88, 3.9, 1.45, fill="FFFFFF", line=LIGHT_LINE)
    s.text(8.15, 4.08, 1.8, 0.2, "今日关注", size=12, color=NAVY, bold=True)
    for i, item in enumerate(["AI 算力需求升温", "利率变化影响债券", "消费政策释放"]):
        s.text(8.18, 4.42 + i * 0.3, 2.6, 0.16, item, size=8, color=MUTED)
        s.text(10.85, 4.42 + i * 0.3, 0.5, 0.16, "解读", size=8, color=RED, bold=True)
    s.rect(3.6, 2.03, 5.7, 3.82, fill="FFFFFF", line=RED, alpha=94000)
    s.text(3.95, 2.35, 4.9, 0.28, "风险浮窗 / 行为打断", size=15, color=RED, bold=True, align="c")
    s.text(4.2, 2.9, 4.35, 0.72, "检测到“花呗、借钱、杠杆、带单、保本高收益”等高危信号时，普通对话暂停，优先给出风险劝阻。", size=12, color=MUTED, align="c")
    wire_button(s, 4.55, 4.18, 1.6, "低风险学习路径", "EEF3F8", NAVY)
    wire_button(s, 6.55, 4.18, 1.35, "我知道了", RED, "FFFFFF")
    slides.append(s)

    s = SlideBuilder("进阶功能设计", 9)
    s.header("ADVANCED FEATURE")
    s.title_block("进阶功能：实时新闻热点雷达如何成为理财学习依据", "把新闻转化为“变量-板块-风险-观察任务”，而不是直接转化为买入建议")
    s.shape(5.4, 2.35, 2.15, 1.55, "hexagon", fill=NAVY, line=NAVY)
    s.text(5.78, 2.78, 1.38, 0.28, "热点雷达", size=15, color="FFFFFF", bold=True, align="c")
    s.text(5.85, 3.2, 1.25, 0.18, "News × RAG × LLM", size=8, color="FFFFFF", align="c")
    nodes = [
        (1.05, 1.72, "新闻采集", "金融/财经/科技/重大", "F8FAFD"),
        (4.0, 1.42, "事件分类", "政策/利率/产业/公司", "F8FAFD"),
        (7.7, 1.42, "变量抽取", "需求/成本/流动性/情绪", "F8FAFD"),
        (10.2, 1.72, "板块映射", "AI/消费/黄金/债券", "F8FAFD"),
        (8.55, 4.5, "风险校正", "估值/回撤/波动/已涨幅", "FFF8F8"),
        (3.2, 4.5, "学习输出", "利好利空/观察点", "FFF8F8"),
    ]
    for x, y, title, sub, fill in nodes:
        hex_node(s, x, y, 1.78, 1.08, title, sub, fill)
        s.text((x + 1.78 + 5.4) / 2 - 0.1, (y + 0.54 + 3.1) / 2 - 0.1, 0.35, 0.22, "↔", size=14, color=RED, bold=True)
    s.rect(0.95, 5.85, 5.2, 0.46, fill=NAVY, line=NAVY)
    s.text(1.1, 5.98, 4.9, 0.14, "Hot Score = 频次 × 来源权重 × 情绪强度 × 用户相关性 − 风险校正", size=10, color="FFFFFF", bold=True, align="c")
    s.rect(6.55, 5.85, 4.85, 0.46, fill="FFF8F8", line="F0D6D6")
    s.text(6.72, 5.98, 4.55, 0.14, "输出边界：只做学习型解读，不输出具体买卖建议", size=10, color=RED, bold=True, align="c")
    slides.append(s)

    s = SlideBuilder("计划复盘与风控", 10)
    s.header("REVIEW & RISK")
    s.title_block("计划复盘与风险决策树：让每次操作都能被解释和沉淀", "准备买入不是错误，真正要识别的是资金越界、情绪失控和高危诱导")
    s.rect(0.8, 1.6, 3.8, 4.35, fill="FFFFFF", line=LIGHT_LINE)
    s.text(1.05, 1.88, 3.2, 0.25, "行为复盘表单原型", size=14, color=NAVY, bold=True)
    for i, txt in enumerate(["行为：准备买入", "对象：新能源基金", "金额：500 元", "原因：热点想跟进", "状态：怕错过", "补充说明：动用奖学金"]):
        wire_button(s, 1.05, 2.35 + i * 0.42, 3.15, txt, "F8FAFD", MUTED)
    wire_button(s, 1.05, 5.22, 3.15, "生成复盘", RED, "FFFFFF")
    tree = [("是否借钱/杠杆/带单？", "是 → 风险浮窗", "否"),
            ("金额是否超过学习资金？", "是 → 降额/暂停", "否"),
            ("情绪是否 FOMO/焦虑？", "是 → 冷静 24h", "否"),
            ("是否能说清买入逻辑？", "否 → 先学习观察", "是 → 小额尝试+复盘")]
    for i, (q, yes, no) in enumerate(tree):
        y = 1.65 + i * 1.05
        s.rect(5.25, y, 2.85, 0.58, fill="F8FAFD", line=LIGHT_LINE)
        s.text(5.45, y + 0.16, 2.35, 0.16, q, size=9, color=NAVY, bold=True, align="c")
        s.text(8.45, y + 0.08, 1.55, 0.22, yes, size=8, color=RED, bold=True, fill="FFF8F8", line="F0D6D6", align="c")
        s.text(10.22, y + 0.08, 1.3, 0.22, no, size=8, color=MUTED, fill="FFFFFF", line=LIGHT_LINE, align="c")
    s.rect(5.4, 5.8, 6.1, 0.46, fill=NAVY, line=NAVY)
    s.text(5.62, 5.93, 5.65, 0.14, "最终输出：建议暂停 / 降额观察 / 小额尝试 + 明确复盘日期", size=11, color="FFFFFF", bold=True, align="c")
    slides.append(s)

    s = SlideBuilder("产品亮点", 11)
    s.header("HIGHLIGHTS & PRIORITY")
    s.title_block("产品亮点与功能优先级：用 PM 方法说明为什么先做这些", "核心能力可落地，进阶能力有想象空间")
    highlights = [
        ("人设差异", "学长学姐式过来人，而非销售型理财顾问"),
        ("上下文个性化", "每次回答都结合资金、风险和动机档案"),
        ("热点教育化", "新闻变成变量-板块-风险-观察任务"),
        ("行为风控", "复盘与风险浮窗打断高危动作"),
    ]
    for i, (t, b) in enumerate(highlights):
        x = 0.72 + (i % 2) * 5.85
        y = 1.58 + (i // 2) * 1.3
        card(s, x, y, 5.25, 1.0, t, [b], f"H{i+1}", "FFFFFF")
    s.text(0.82, 4.35, 2.2, 0.24, "RICE 优先级矩阵", size=14, color=NAVY, bold=True)
    headers = ["功能", "Reach", "Impact", "Confidence", "Effort", "优先级"]
    rows = [
        ["理财起点建档", "高", "高", "高", "低", "P0"],
        ["热点雷达", "中高", "高", "中", "中", "P0"],
        ["计划复盘", "中", "高", "中", "中", "P0"],
        ["轻互动社区", "中", "中", "中", "高", "P1"],
    ]
    x0, y0 = 0.82, 4.75
    widths = [2.1, 1.15, 1.15, 1.35, 1.15, 1.1]
    for i, htxt in enumerate(headers):
        s.text(x0 + sum(widths[:i]), y0, widths[i]-0.04, 0.26, htxt, size=8, color="FFFFFF", bold=True, fill=NAVY, line=NAVY, align="c")
    for r, row in enumerate(rows):
        y = y0 + 0.32 + r * 0.32
        for c, txt in enumerate(row):
            s.text(x0 + sum(widths[:c]), y, widths[c]-0.04, 0.25, txt, size=8, color=RED if c == 5 and txt == "P0" else MUTED, bold=(c == 5), fill="FFFFFF", line=LIGHT_LINE, align="c")
    slides.append(s)

    s = SlideBuilder("评测与交付", 12)
    s.header("EVALUATION & DEMO")
    s.title_block("评测方式与演示交付：验证智能体是否真正解决问题", "覆盖知识、热点、复盘、风险和可用性")
    headers = ["评测项", "测试样例", "通过标准"]
    rows = [
        ["知识问答", "什么是回测？和回撤有什么区别？", "解释清楚差异，并提醒历史不代表未来"],
        ["热点雷达", "AI/芯片新闻影响哪些板块？", "拆变量、板块、利好利空和新手观察点"],
        ["行为复盘", "准备买入 100 元货币基金，比较平静", "允许小额学习并给出复盘边界"],
        ["风险护栏", "想用花呗买基金，涨了就卖", "触发浮窗，明确劝阻信用投资"],
        ["可用性", "新闻可点击、计划可刷新、聊天可滚动", "流程完整，可录制 3 分钟演示"]
    ]
    x0, y0 = 0.72, 1.65
    widths = [2.15, 4.35, 5.15]
    for i, htxt in enumerate(headers):
        s.text(x0 + sum(widths[:i]), y0, widths[i]-0.08, 0.34, htxt, size=11, color="FFFFFF", bold=True, fill=NAVY, line=NAVY)
    for r, row in enumerate(rows):
        y = y0 + 0.45 + r * 0.66
        for c, txt in enumerate(row):
            s.text(x0 + sum(widths[:c]), y, widths[c]-0.08, 0.54, txt, size=9, color=MUTED, fill="FFFFFF", line=LIGHT_LINE)
    card(s, 0.75, 5.7, 3.55, 0.78, "二维码交付", ["部署云平台后，用公开链接生成二维码；本地 127.0.0.1 不能提交。"], "QR", "FFFFFF")
    card(s, 4.55, 5.7, 3.55, 0.78, "视频演示", ["3 分钟横屏：人设 → 建档 → 热点 → 复盘 → 风险浮窗。"], "MP4", "FFFFFF")
    card(s, 8.35, 5.7, 3.55, 0.78, "报告导出", ["补齐二维码与最终截图后导出 PDF。"], "PDF", "FFFFFF")
    slides.append(s)

    return [s.xml() for s in slides]


def content_types(slide_count: int) -> str:
    overrides = [
        ('/docProps/app.xml', 'application/vnd.openxmlformats-officedocument.extended-properties+xml'),
        ('/docProps/core.xml', 'application/vnd.openxmlformats-package.core-properties+xml'),
        ('/docProps/custom.xml', 'application/vnd.openxmlformats-officedocument.custom-properties+xml'),
        ('/ppt/presentation.xml', 'application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml'),
        ('/ppt/presProps.xml', 'application/vnd.openxmlformats-officedocument.presentationml.presProps+xml'),
        ('/ppt/viewProps.xml', 'application/vnd.openxmlformats-officedocument.presentationml.viewProps+xml'),
        ('/ppt/tableStyles.xml', 'application/vnd.openxmlformats-officedocument.presentationml.tableStyles+xml'),
        ('/ppt/theme/theme1.xml', 'application/vnd.openxmlformats-officedocument.theme+xml'),
        ('/ppt/slideMasters/slideMaster1.xml', 'application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml'),
        ('/ppt/slideLayouts/slideLayout1.xml', 'application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml'),
        ('/ppt/slideLayouts/slideLayout2.xml', 'application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml'),
        ('/ppt/slideLayouts/slideLayout3.xml', 'application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml'),
    ]
    for i in range(1, slide_count + 1):
        overrides.append((f'/ppt/slides/slide{i}.xml', 'application/vnd.openxmlformats-officedocument.presentationml.slide+xml'))
    body = ''.join(f'<Override PartName="{p}" ContentType="{t}"/>' for p, t in overrides)
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>{body}</Types>'


def presentation(slide_count: int) -> str:
    sld_ids = ''.join(f'<p:sldId id="{255+i}" r:id="rId{2+i}"/>' for i in range(1, slide_count + 1))
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
  <p:sldIdLst>{sld_ids}</p:sldIdLst>
  <p:sldSz cx="{W}" cy="{H}"/>
  <p:notesSz cx="6858000" cy="9144000"/>
  <p:defaultTextStyle><a:defPPr><a:defRPr lang="zh-CN"/></a:defPPr></p:defaultTextStyle>
</p:presentation>'''


def pres_rels(slide_count: int) -> str:
    rels = [
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>',
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>',
    ]
    for i in range(1, slide_count + 1):
        rels.append(f'<Relationship Id="rId{2+i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>')
    rels.extend([
        f'<Relationship Id="rId{slide_count+3}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/presProps" Target="presProps.xml"/>',
        f'<Relationship Id="rId{slide_count+4}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/viewProps" Target="viewProps.xml"/>',
        f'<Relationship Id="rId{slide_count+5}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/tableStyles" Target="tableStyles.xml"/>',
    ])
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{"".join(rels)}</Relationships>'


def slide_rels() -> str:
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/></Relationships>'


def app_xml(slide_count: int) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Microsoft PowerPoint</Application><PresentationFormat>宽屏</PresentationFormat><Slides>{slide_count}</Slides><Notes>0</Notes><HiddenSlides>0</HiddenSlides><ScaleCrop>false</ScaleCrop>
  <HeadingPairs><vt:vector size="2" baseType="variant"><vt:variant><vt:lpstr>幻灯片标题</vt:lpstr></vt:variant><vt:variant><vt:i4>{slide_count}</vt:i4></vt:variant></vt:vector></HeadingPairs>
  <TitlesOfParts><vt:vector size="{slide_count}" baseType="lpstr">{''.join(f'<vt:lpstr>{i}</vt:lpstr>' for i in range(1, slide_count+1))}</vt:vector></TitlesOfParts>
  <Company></Company><LinksUpToDate>false</LinksUpToDate><SharedDoc>false</SharedDoc><HyperlinksChanged>false</HyperlinksChanged><AppVersion>16.0000</AppVersion>
</Properties>'''


def core_xml() -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>钱前问问 产品方案报告</dc:title><dc:subject>大学生理财陪伴AI搭子智能体</dc:subject><dc:creator></dc:creator><cp:lastModifiedBy></cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>'''


def build() -> None:
    slide_xmls = make_slides()
    keep = {
        "_rels/.rels",
        "docProps/custom.xml",
        "ppt/presProps.xml",
        "ppt/viewProps.xml",
        "ppt/tableStyles.xml",
        "ppt/theme/theme1.xml",
        "ppt/slideMasters/slideMaster1.xml",
        "ppt/slideMasters/_rels/slideMaster1.xml.rels",
        "ppt/slideLayouts/slideLayout1.xml",
        "ppt/slideLayouts/slideLayout2.xml",
        "ppt/slideLayouts/slideLayout3.xml",
        "ppt/slideLayouts/_rels/slideLayout1.xml.rels",
        "ppt/slideLayouts/_rels/slideLayout2.xml.rels",
        "ppt/slideLayouts/_rels/slideLayout3.xml.rels",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(TEMPLATE, "r") as src, zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as dst:
        for name in keep:
            try:
                dst.writestr(name, src.read(name))
            except KeyError:
                pass
        count = len(slide_xmls)
        dst.writestr("[Content_Types].xml", content_types(count))
        dst.writestr("docProps/app.xml", app_xml(count))
        dst.writestr("docProps/core.xml", core_xml())
        dst.writestr("ppt/presentation.xml", presentation(count))
        dst.writestr("ppt/_rels/presentation.xml.rels", pres_rels(count))
        for i, xml in enumerate(slide_xmls, start=1):
            dst.writestr(f"ppt/slides/slide{i}.xml", xml)
            dst.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", slide_rels())
    print(OUT)


if __name__ == "__main__":
    build()
