from __future__ import annotations

import html
import json
import os
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "app"
KNOWLEDGE_DIR = ROOT / "knowledge"

NEWS_FEEDS = [
    {
        "name": "中新网财经",
        "url": "https://www.chinanews.com.cn/rss/finance.xml",
        "category": "财经",
    },
    {
        "name": "中新网即时",
        "url": "https://www.chinanews.com.cn/rss/scroll-news.xml",
        "category": "重大",
    },
    {
        "name": "新浪财经",
        "url": "https://rss.sina.com.cn/finance/roll.xml",
        "category": "金融",
    },
]

FALLBACK_NEWS = [
    {
        "title": "AI 算力需求持续升温，市场关注芯片与云服务产业链",
        "source": "演示备用新闻",
        "category": "科技",
        "published": "离线示例",
        "link": "",
        "summary": "当实时新闻源不可访问时，用于演示热点雷达分析结构。",
    },
    {
        "title": "消费刺激政策继续释放，市场关注旅游、零售和餐饮修复",
        "source": "演示备用新闻",
        "category": "财经",
        "published": "离线示例",
        "link": "",
        "summary": "当实时新闻源不可访问时，用于演示政策对板块影响的拆解。",
    },
    {
        "title": "利率变化影响债券价格和成长型资产估值",
        "source": "演示备用新闻",
        "category": "金融",
        "published": "离线示例",
        "link": "",
        "summary": "当实时新闻源不可访问时，用于演示金融变量对资产方向的影响。",
    },
]


@dataclass
class KnowledgeChunk:
    path: str
    title: str
    heading: str
    content: str


def read_knowledge() -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        title = path.stem
        for line in content.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        chunks.extend(split_markdown_chunks(path.name, title, content))
    return chunks


def split_markdown_chunks(path: str, title: str, content: str) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    current_heading = title
    current_lines: list[str] = []

    def flush():
        block = "\n".join(current_lines).strip()
        if block:
            chunks.append(
                KnowledgeChunk(
                    path=path,
                    title=title,
                    heading=current_heading,
                    content=block,
                )
            )

    for line in content.splitlines():
        if line.startswith("## "):
            flush()
            current_heading = line[3:].strip()
            current_lines = [line]
        else:
            current_lines.append(line)
    flush()

    if not chunks and content.strip():
        chunks.append(KnowledgeChunk(path=path, title=title, heading=title, content=content.strip()))
    return chunks


KNOWLEDGE_CHUNKS = read_knowledge()


def load_local_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_local_env()

LLM_API_KEY = os.environ.get("LLM_API_KEY", "").strip()
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1/chat/completions").strip()
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini").strip()
LLM_TIMEOUT = int(os.environ.get("LLM_TIMEOUT", "45") or "45")
LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "900") or "900")
LLM_LAST_ERROR = ""
LLM_COOLDOWN_UNTIL = 0.0
LLM_CACHE: dict[str, str] = {}
LLM_CACHE_MAX = 80


def normalize_llm_endpoint(base_url: str) -> str:
    """Accept either provider base_url or the full chat completions endpoint."""
    url = (base_url or "").strip().rstrip("/")
    if not url:
        return "https://api.openai.com/v1/chat/completions"
    if url.endswith("/chat/completions"):
        return url
    if url.endswith("/v1"):
        return f"{url}/chat/completions"
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc and parsed.path in ("", "/"):
        return f"{url}/v1/chat/completions"
    return url


def strip_tags(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value or "")
    return html.unescape(value).strip()


def fetch_url(url: str, timeout: int = 8) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "CampusFinanceBuddy/1.0 (+local demo)",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def parse_feed(xml_bytes: bytes, source: str, category: str) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    items: list[dict] = []

    rss_items = root.findall(".//item")
    if rss_items:
        for item in rss_items[:8]:
            title = strip_tags(item.findtext("title"))
            link = strip_tags(item.findtext("link"))
            summary = strip_tags(item.findtext("description"))
            published = strip_tags(item.findtext("pubDate"))
            if title:
                items.append(
                    {
                        "title": title,
                        "source": source,
                        "category": category,
                        "published": published,
                        "link": link,
                        "summary": summary[:180],
                    }
                )
        return items

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall(".//atom:entry", ns)[:8]:
        title = strip_tags(entry.findtext("atom:title", default="", namespaces=ns))
        link_el = entry.find("atom:link", ns)
        link = link_el.attrib.get("href", "") if link_el is not None else ""
        summary = strip_tags(entry.findtext("atom:summary", default="", namespaces=ns))
        published = strip_tags(entry.findtext("atom:updated", default="", namespaces=ns))
        if title:
            items.append(
                {
                    "title": title,
                    "source": source,
                    "category": category,
                    "published": published,
                    "link": link,
                    "summary": summary[:180],
                }
            )
    return items


def fetch_news(limit: int = 6) -> tuple[list[dict], bool, list[str]]:
    items: list[dict] = []
    errors: list[str] = []
    for feed in NEWS_FEEDS:
        try:
            xml_bytes = fetch_url(feed["url"])
            items.extend(parse_feed(xml_bytes, feed["name"], feed["category"]))
        except (urllib.error.URLError, TimeoutError, ET.ParseError, OSError) as exc:
            errors.append(f"{feed['name']}: {exc}")

    if not items:
        return FALLBACK_NEWS[:limit], False, errors

    deduped: list[dict] = []
    seen = set()
    for item in items:
        key = item["title"]
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped[:limit], True, errors


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]{2,}", text.lower())
    tokens: list[str] = []
    for word in words:
        if len(word) >= 2 and re.match(r"[\u4e00-\u9fff]+", word):
            tokens.append(word)
            tokens.extend(word[i : i + 2] for i in range(len(word) - 1))
        else:
            tokens.append(word)
    return tokens


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    query_tokens = set(tokenize(query))
    scored: list[tuple[int, KnowledgeChunk]] = []
    for chunk in KNOWLEDGE_CHUNKS:
        searchable = f"{chunk.title}\n{chunk.heading}\n{chunk.content}"
        chunk_tokens = set(tokenize(searchable))
        exact_bonus = 3 if query.strip() and query.strip("？?") in searchable else 0
        heading_bonus = 2 if any(token in chunk.heading.lower() for token in query_tokens) else 0
        score = len(query_tokens & chunk_tokens) + exact_bonus + heading_bonus
        if score:
            scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            "title": f"{chunk.title} / {chunk.heading}",
            "path": chunk.path,
            "snippet": make_snippet(chunk.content, query),
            "score": score,
        }
        for score, chunk in scored[:top_k]
    ]


def summarize_profile(profile: dict | None) -> str:
    if not isinstance(profile, dict):
        return "用户尚未提供完整理财档案。"

    fields = [
        ("每月最低生活费", "monthlyLiving"),
        ("当前可支配资金", "currentFunds"),
        ("未来 1-3 个月确定支出", "shortExpense"),
        ("现有应急备用金", "emergencyFund"),
        ("可用于理财学习资金", "learningMoney"),
        ("理财经验", "experience"),
        ("风险承受", "riskFeeling"),
        ("理财动机", "motivation"),
    ]
    lines = []
    for label, key in fields:
        if key in profile and profile[key] not in ("", None):
            lines.append(f"{label}：{profile[key]}")
    return "\n".join(lines) if lines else "用户尚未提供完整理财档案。"


def call_llm(question: str, citations: list[dict], mode_hint: str, profile: dict | None = None) -> str | None:
    global LLM_COOLDOWN_UNTIL, LLM_LAST_ERROR
    LLM_LAST_ERROR = ""
    if not LLM_API_KEY:
        LLM_LAST_ERROR = "未配置 LLM_API_KEY"
        return None

    cache_key = json.dumps(
        {
            "model": LLM_MODEL,
            "mode": mode_hint,
            "question": question,
            "profile": summarize_profile(profile),
            "citations": [item.get("title", "") for item in citations],
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    if cache_key in LLM_CACHE:
        return LLM_CACHE[cache_key]

    now = time.time()
    if now < LLM_COOLDOWN_UNTIL:
        wait_seconds = max(1, int(LLM_COOLDOWN_UNTIL - now))
        LLM_LAST_ERROR = f"MODEL_COOLDOWN:{wait_seconds}"
        return None

    context = "\n\n".join(
        f"【{item['title']}｜{item['path']}】\n{item['snippet']}" for item in citations
    )
    profile_text = summarize_profile(profile)
    mode_rules = {
        "热点雷达深度分析": (
            "请围绕新闻本身做投资教育型解读，必须包含：一句话翻译、影响链条、可能相关板块、"
            "偏利好/偏利空及不确定性、新手观察点、不能直接做的事。不要推荐具体个股、基金或币种。"
        ),
        "计划复盘": (
            "请根据用户档案和本次行为做复盘。不要因为用户选择“准备买入”就一律劝退；"
            "只有出现贷款、借钱、杠杆、带单、保本高收益、明显动用生活费/应急钱、金额严重越界时，才明确建议暂停。"
            "普通小额买入可以给出有条件尝试建议。必须包含：当前动作判断、资金安全性、认知/情绪风险、"
            "下一步建议、一个可执行的低风险替代动作。语气像有经验的学长学姐，不要说教。"
        ),
        "小额计划": (
            "请根据用户档案生成本周可执行的小额入门理财学习计划，重点是学习、观察、复盘，"
            "不是追求收益。必须给出金额边界、学习任务、观察对象、复盘问题和风险底线。"
        ),
    }
    system_prompt = (
        "你是一个面向大学生的入门理财陪伴型 AI 搭子，身份类似有经验的学长学姐。"
        "你不是投顾，不推荐具体股票、基金、币种，不承诺收益。"
        "你要用亲近、清楚、不说教的方式回答，结合大学生生活场景解释概念。"
        "遇到贷款、借钱、杠杆、带单、保本高收益等风险，要明确劝阻。"
        "如果上下文来自知识库，请优先依据知识库；如果信息不足，要说明需要用户补充。"
    )
    output_style_rule = (
        "输出格式要求：只输出普通中文文字，不要使用 Markdown。"
        "不要使用 #、##、-、*、1.、```、表格、加粗符号或项目符号。"
        "如果需要分层表达，用自然段换行即可，可以写成“第一点：”“第二点：”这样的普通文字。"
        "回答要像真实聊天里的学长学姐，不要像报告、PPT 或说明书。"
    )
    user_prompt = (
        f"用户问题：{question}\n"
        f"回答模式提示：{mode_hint}\n\n"
        f"本次模式要求：{mode_rules.get(mode_hint, '请自然回答，结论要具体，避免泛泛而谈。')}\n\n"
        f"用户理财档案：\n{profile_text}\n\n"
        f"可用知识库上下文：\n{context or '无'}\n\n"
        "请给出自然、具体、有学长学姐感的回答。不要公式化，不要用金融销售语气。"
    )
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": f"{system_prompt}\n{output_style_rule}"},
            {"role": "user", "content": f"{user_prompt}\n\n{output_style_rule}"},
        ],
        "temperature": 0.6,
        "max_tokens": LLM_MAX_TOKENS,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        normalize_llm_endpoint(LLM_BASE_URL),
        data=data,
        headers={
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=LLM_TIMEOUT) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8")[:280]
        except OSError:
            detail = ""
        if exc.code == 429:
            LLM_COOLDOWN_UNTIL = time.time() + 75
            LLM_LAST_ERROR = "MODEL_RATE_LIMIT:75"
        else:
            LLM_LAST_ERROR = f"HTTP {exc.code} {detail}".strip()
        return None
    except urllib.error.URLError as exc:
        LLM_LAST_ERROR = f"网络连接失败：{exc.reason}"
        return None
    except TimeoutError:
        LLM_LAST_ERROR = "请求大模型超时"
        return None
    except OSError as exc:
        LLM_LAST_ERROR = f"本地网络错误：{exc}"
        return None
    except json.JSONDecodeError:
        LLM_LAST_ERROR = "大模型返回不是有效 JSON"
        return None

    try:
        answer = result["choices"][0]["message"]["content"].strip()
        if len(LLM_CACHE) >= LLM_CACHE_MAX:
            LLM_CACHE.pop(next(iter(LLM_CACHE)))
        LLM_CACHE[cache_key] = answer
        return answer
    except (KeyError, IndexError, TypeError):
        LLM_LAST_ERROR = "大模型返回结构不符合 chat/completions 格式"
        return None


def with_llm_debug(payload: dict) -> dict:
    if LLM_API_KEY and payload.get("mode") != "llm_rag" and LLM_LAST_ERROR:
        if LLM_LAST_ERROR.startswith("MODEL_RATE_LIMIT"):
            seconds = LLM_LAST_ERROR.split(":", 1)[1] if ":" in LLM_LAST_ERROR else "60"
            payload["llm_error"] = f"智谱免费接口触发限流，约 {seconds} 秒后再试。当前先使用本地知识库兜底。"
            payload["llm_cooldown"] = int(seconds)
        elif LLM_LAST_ERROR.startswith("MODEL_COOLDOWN"):
            seconds = LLM_LAST_ERROR.split(":", 1)[1] if ":" in LLM_LAST_ERROR else "60"
            payload["llm_error"] = f"大模型正在冷却中，约 {seconds} 秒后可再次调用。当前先使用本地知识库兜底。"
            payload["llm_cooldown"] = int(seconds)
        else:
            payload["llm_error"] = LLM_LAST_ERROR
    return payload


def make_snippet(content: str, query: str) -> str:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    query_tokens = tokenize(query)
    for token in query_tokens:
        for index, line in enumerate(lines):
            if token in line.lower():
                return "\n".join(lines[max(0, index - 1) : index + 4])[:500]
    return "\n".join(lines[:5])[:500]


def analyze_news_text(text: str) -> str:
    source = text or "财经、金融、科技热点"
    variable = "政策、需求、成本、技术或市场情绪"
    sectors = "相关行业板块"
    leaning = "需要结合具体内容判断，不能只看标题"
    observation = "先观察市场是否已经提前反应，再看自己是否理解风险。"

    if re.search(r"AI|人工智能|芯片|半导体|算力|机器人|科技", source, re.I):
        variable = "技术预期、算力需求、产业链订单和市场情绪"
        sectors = "半导体、算力、云服务、AI 应用、机器人"
        leaning = "对相关科技链可能偏利好，但短期波动和估值风险也更高"
        observation = "不要因为“科技很火”就追入，先看相关基金是否已经涨了很多，以及最大回撤能不能承受。"
    elif re.search(r"降息|降准|利率|债券|汇率|银行", source):
        variable = "资金成本、市场流动性、债券价格和银行息差"
        sectors = "债券、银行、地产、成长型行业、黄金"
        leaning = "可能改善市场流动性，但不同资产反应方向不完全一样"
        observation = "重点学习利率如何影响债券价格和成长板块估值。"
    elif re.search(r"消费|旅游|零售|电商|餐饮|免税", source):
        variable = "居民消费意愿、收入预期和政策刺激"
        sectors = "食品饮料、旅游、零售、电商、餐饮"
        leaning = "对消费板块可能偏利好，但要区分短期修复和长期趋势"
        observation = "不要只看政策标题，要看实际消费数据是否持续改善。"
    elif re.search(r"油价|原油|能源|冲突|战争|黄金|避险", source):
        variable = "能源成本、避险情绪、通胀预期和供应链"
        sectors = "石油、黄金、航空、物流、化工、农业"
        leaning = "可能利好能源或避险资产，同时增加部分行业成本压力"
        observation = "重大事件影响复杂，短期波动更强，新手不适合因为情绪消息追高。"
    elif re.search(r"新能源|电动车|光伏|锂电|储能", source):
        variable = "政策支持、需求预期、原材料价格和产能竞争"
        sectors = "新能源车、锂电池、光伏、储能"
        leaning = "可能对产业链部分环节偏利好，但行业竞争和价格下行也可能压制利润"
        observation = "观察时不要只看销量，也要看企业利润、库存和价格竞争。"

    return (
        "热点雷达拆解：\n"
        f"一句话翻译：这条消息可能会改变市场对某些行业未来表现的预期，但不能直接等同于买入机会。\n"
        f"影响变量：{variable}\n"
        f"相关板块：{sectors}\n"
        f"利好/利空：{leaning}\n"
        f"新手观察：{observation}\n\n"
        "提醒：热点解读不是买入建议。你要训练的是看懂逻辑，而不是看到热词就立刻下手。"
    )


def news_preview(text: str) -> str:
    analysis = analyze_news_text(text)
    for line in analysis.splitlines():
        if line.startswith("相关板块："):
            return line.replace("相关板块：", "可能影响：")
    return "点击 AI 解读查看影响链条和新手观察点。"


def analyze_news_deep(news: dict, profile: dict | None = None) -> dict:
    title = str(news.get("title", "")).strip()
    summary = str(news.get("summary", "")).strip()
    source = str(news.get("source", "")).strip()
    category = str(news.get("category", "")).strip()
    text = "\n".join(part for part in [title, summary] if part)
    if not text:
        text = str(news.get("text", "")).strip()
    if not text:
        text = "财经、金融或科技热点"

    citations = retrieve(f"热点雷达 板块 利好 利空 行业 变量 {text}", top_k=4)
    base_answer = analyze_news_text(text)
    prompt = (
        f"新闻标题：{title or text}\n"
        f"新闻来源：{source or '未知'}\n"
        f"新闻类别：{category or '未知'}\n"
        f"新闻摘要：{summary or '无'}\n\n"
        f"基础分析：\n{base_answer}\n\n"
        "请把它解读成适合大学生入门理财学习的热点雷达。"
    )
    llm_answer = call_llm(prompt, citations, "热点雷达深度分析", profile)
    return with_llm_debug({
        "answer": llm_answer or base_answer,
        "mode": "llm_rag" if llm_answer else "news_analysis",
        "citations": citations,
        "preview": news_preview(text),
    })


def number_from_action(action: dict, key: str) -> float:
    try:
        return float(action.get(key, 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def local_study_plan(profile: dict | None) -> str:
    profile = profile if isinstance(profile, dict) else {}
    learning_money = float(profile.get("learningMoney", 0) or 0)
    short_expense = float(profile.get("shortExpense", 0) or 0)
    emergency_gap = float(profile.get("oneMonthEmergencyGap", 0) or 0)
    risk_feeling = str(profile.get("riskFeeling", "low"))
    motivation = str(profile.get("motivation", "learn"))
    max_real = min(learning_money, 300 if risk_feeling == "low" else 600 if risk_feeling == "mid" else 1000)

    if learning_money <= 0:
        return (
            "本周计划：先不实投，做模拟观察。\n\n"
            f"1. 先把短期支出和备用金缺口留出来，当前至少需要预留 {int(short_expense + emergency_gap)} 元。\n"
            "2. 选择 1 个你感兴趣的板块，只记录新闻、涨跌和原因，不下单。\n"
            "3. 学一个概念：回撤、手续费、持有期或债券基金为什么会跌。\n"
            "4. 周末复盘：这周有没有被同学、短视频或热门新闻影响情绪。\n\n"
            "底线：备用金没稳定前，不要把生活费拿去实投。"
        )

    reason_note = "你的动机里有热点/同伴影响，计划里要多加一道冷静检查。" if motivation in {"peer", "hot"} else "你的目标可以放在理解产品和建立习惯上。"
    return (
        "本周小额入门计划：\n\n"
        f"1. 真实投入上限：不超过 {int(max_real)} 元，超过这个金额就先暂停。\n"
        "2. 观察任务：选 1 个低风险工具或 1 个宽基/行业板块做观察清单，记录它为什么涨跌。\n"
        "3. 学习任务：搞懂申购费、赎回费、持有期和最大回撤，不看懂不加钱。\n"
        "4. 复盘任务：每周记录一次收益、波动、手续费和当时情绪。\n"
        f"5. 冷静提醒：{reason_note}\n\n"
        "底线：不贷款、不借钱、不加杠杆，不因为一天涨跌改变计划。"
    )


def local_review(profile: dict | None, action: dict) -> str:
    profile = profile if isinstance(profile, dict) else {}
    amount = number_from_action(action, "amount")
    learning_money = float(profile.get("learningMoney", 0) or 0)
    product = str(action.get("product", "")).strip() or "这次操作"
    behavior = str(action.get("behavior", "")).strip() or "准备操作"
    reason = str(action.get("reason", "")).strip()
    mood = str(action.get("mood", "")).strip()
    notes = str(action.get("notes", "")).strip()
    combined = " ".join([product, behavior, reason, mood, notes])

    hard_warnings = []
    soft_notes = []
    if risk_pattern := re.search(r"贷款|借钱|花呗|借呗|信用卡|杠杆|合约|带单|保本|稳赚|翻倍|梭哈|全部", combined):
        hard_warnings.append(f"出现“{risk_pattern.group(0)}”这类高风险信号，建议直接暂停。")
    if learning_money <= 0 and amount > 0:
        hard_warnings.append("你的档案显示当前不适合实投，这笔操作容易动到备用金或短期支出。")
    if learning_money > 0 and amount > learning_money * 1.5:
        hard_warnings.append(f"金额 {int(amount)} 元明显超过当前建议学习资金 {int(learning_money)} 元。")
    elif learning_money > 0 and amount > learning_money:
        soft_notes.append(f"金额 {int(amount)} 元略高于当前建议学习资金 {int(learning_money)} 元，可以考虑先降到建议范围内。")
    if reason in {"peer", "hot", "recover"}:
        soft_notes.append("操作动机里有同伴、热点或回本心理影响，建议先把理由写清楚，不要只凭情绪下单。")
    if mood in {"anxious", "fomo", "regret"}:
        soft_notes.append("你现在有焦虑、怕错过或后悔情绪，适合先冷静 24 小时再决定金额。")

    if hard_warnings:
        verdict = "建议暂停"
    elif soft_notes:
        verdict = "可以降额观察，不建议冲动买入"
    else:
        verdict = "可以小额尝试，但要先写下计划"

    risk_lines = hard_warnings + soft_notes
    risk_text = "\n".join(f"- {item}" for item in risk_lines) if risk_lines else "- 暂未发现明显越界信号，重点是控制金额、写清理由、按时复盘。"
    if hard_warnings:
        next_step = "先不下单，改成模拟观察 7 天；如果 7 天后仍能说清楚买入逻辑、最大可能亏损和退出条件，再考虑小额。"
    elif soft_notes:
        next_step = "把金额降到学习资金范围内，冷静 24 小时后再看。如果仍然想买，先写下买入理由、可承受亏损和复盘日期。"
    else:
        next_step = "可以把本次操作当成学习实验：控制在学习资金内，记录买入理由、预期持有时间、能接受的最大亏损和下次复盘日期。"

    return (
        f"复盘结论：{verdict}\n\n"
        f"本次行为：{behavior}，对象：{product}，金额：{int(amount)} 元。\n\n"
        "主要风险点：\n"
        f"{risk_text}\n\n"
        "下一步建议：\n"
        f"{next_step}\n\n"
        "复盘问题：如果这笔钱短期亏 10%，会不会影响你的生活费、考试报名、设备维修或情绪状态？"
    )


REVIEW_LABELS = {
    "reason": {
        "understand": "理解后想尝试",
        "hot": "看到热点想跟进",
        "peer": "同学朋友在买",
        "recover": "亏了想回本",
        "family": "家长建议",
    },
    "mood": {
        "calm": "比较平静",
        "fomo": "怕错过",
        "anxious": "有点焦虑",
        "regret": "有点后悔",
    },
    "moneySource": {
        "learning": "理财学习资金",
        "scholarship": "奖学金或兼职结余",
        "living": "生活费结余",
        "emergency": "备用金",
        "borrowed": "借来的钱或信用额度",
    },
    "infoSource": {
        "self": "自己研究后决定",
        "news": "财经新闻或公告",
        "social": "短视频或社交媒体",
        "peer": "同学朋友推荐",
        "family": "家人建议",
        "group": "群聊带单或私聊推荐",
    },
    "holding": {
        "unknown": "还没想清楚",
        "week": "一周内短线看看",
        "month": "至少一个月",
        "quarter": "三个月左右",
        "halfyear": "半年以上",
    },
}


def review_label(group: str, value: str) -> str:
    return REVIEW_LABELS.get(group, {}).get(value, value or "未填写")


def local_review(profile: dict | None, action: dict) -> str:
    profile = profile if isinstance(profile, dict) else {}
    action = action if isinstance(action, dict) else {}

    amount = number_from_action(action, "amount")
    loss_limit = number_from_action(action, "lossLimit")
    learning_money = float(profile.get("learningMoney", 0) or 0)
    current_funds = float(profile.get("currentFunds", 0) or 0)
    short_expense = float(profile.get("shortExpense", 0) or 0)
    emergency_gap = float(profile.get("oneMonthEmergencyGap", 0) or 0)

    product = str(action.get("product", "")).strip() or "这次操作对象"
    behavior = str(action.get("behavior", "")).strip() or "准备操作"
    reason = str(action.get("reason", "")).strip()
    mood = str(action.get("mood", "")).strip()
    money_source = str(action.get("moneySource", "")).strip()
    info_source = str(action.get("infoSource", "")).strip()
    holding = str(action.get("holding", "")).strip()
    outcome = str(action.get("outcome", "")).strip()
    notes = str(action.get("notes", "")).strip()
    combined = " ".join([product, behavior, reason, mood, money_source, info_source, holding, outcome, notes])

    hard_warnings: list[str] = []
    soft_notes: list[str] = []
    positives: list[str] = []

    if re.search(r"贷款|借钱|花呗|借呗|信用卡|杠杆|合约|带单|保本|稳赚|翻倍|梭哈|全部|陌生App|转账|私聊", combined, re.I):
        hard_warnings.append("内容里出现了贷款、借钱、杠杆、带单、保本高收益或陌生转账这类高危信号，这已经超出入门理财学习范围。")
    if money_source == "borrowed":
        hard_warnings.append("资金来源是借来的钱或信用额度，这一点要直接拦下，不能用负债去承担投资波动。")
    if money_source == "emergency":
        hard_warnings.append("这笔钱来自备用金，备用金的任务是应对生病、设备维修、考试报名这类突发支出，不适合拿去试风险。")
    if info_source == "group":
        hard_warnings.append("信息来源是群聊带单或私聊推荐，这类场景很容易把学习理财变成被诱导交易。")
    if learning_money <= 0 and amount > 0:
        hard_warnings.append("你的档案显示当前可用于理财学习的资金为 0 元，这次只要动真金白银，就可能挤占生活费、短期支出或备用金。")
    if learning_money > 0 and amount > learning_money * 1.5:
        hard_warnings.append(f"这次金额是 {int(amount)} 元，已经明显超过你当前建议的理财学习资金 {int(learning_money)} 元。")

    if learning_money > 0 and learning_money < amount <= learning_money * 1.5:
        soft_notes.append(f"金额比你的学习资金上限高一些。不是完全不能研究，但实投金额最好先回到 {int(learning_money)} 元以内。")
    if money_source == "living":
        soft_notes.append("资金来源是生活费结余，要确认它不是下个月饭费、通勤、话费或课程材料费的暂存。")
    if info_source in {"social", "peer"}:
        soft_notes.append(f"信息来源偏外部刺激，来自{review_label('infoSource', info_source)}。这里最容易出现只看到别人赚钱、没看到别人亏损的偏差。")
    if reason in {"hot", "peer", "recover"}:
        soft_notes.append(f"主要原因是{review_label('reason', reason)}，这说明本次操作里有情绪或比较心理，需要先把投资逻辑写清楚。")
    if mood in {"fomo", "anxious", "regret"}:
        soft_notes.append(f"你现在的状态是{review_label('mood', mood)}，这种状态下更容易追涨、割肉或加仓回本。")
    if holding in {"unknown", "week"}:
        soft_notes.append(f"预计持有时间是{review_label('holding', holding)}，如果没有持有周期和退出条件，后面每一次涨跌都会变成临时决策。")
    if amount > 0 and loss_limit <= 0:
        soft_notes.append("你没有写最多能接受亏多少。没有亏损边界，就很难判断这笔操作是不是自己真的承受得住。")
    elif amount > 0 and loss_limit > amount * 0.3:
        soft_notes.append(f"你能接受的亏损是 {int(loss_limit)} 元，已经超过本金的 30% 左右，说明这个操作波动可能会明显影响心态。")

    if info_source in {"self", "news"}:
        positives.append(f"信息来源是{review_label('infoSource', info_source)}，比单纯听同学或刷短视频更适合做学习型决策。")
    if reason == "understand":
        positives.append("你选择的是理解后想尝试，这比单纯跟热点更接近入门理财学习。")
    if mood == "calm":
        positives.append("你当前情绪比较平静，这有利于按计划行动，而不是被短期涨跌带着走。")
    if holding in {"month", "quarter", "halfyear"}:
        positives.append(f"你给了自己{review_label('holding', holding)}的观察周期，这比一两天内赌涨跌更健康。")
    if 0 < loss_limit <= max(1, amount * 0.15):
        positives.append(f"你写了 {int(loss_limit)} 元的亏损边界，这让复盘有了明确参照。")

    if hard_warnings:
        verdict = "这次建议先暂停，不是因为买入这个动作一定错，而是资金来源、信息来源或金额边界已经出现硬风险。"
    elif soft_notes:
        verdict = "这次不适合直接冲动下单，可以改成降额观察或延迟 24 小时后再决定。"
    else:
        verdict = "这次可以被设计成一次小额学习实验，但要先写清楚买入理由、亏损边界和复盘时间。"

    reserve_text = f"你的档案里，当前可支配资金约 {int(current_funds)} 元，短期确定支出约 {int(short_expense)} 元，备用金缺口约 {int(emergency_gap)} 元，系统估算的理财学习资金约 {int(learning_money)} 元。"
    action_text = (
        f"你这次复盘的是{behavior}，对象是{product}，金额是 {int(amount)} 元。"
        f"资金来源是{review_label('moneySource', money_source)}，信息来源是{review_label('infoSource', info_source)}，"
        f"主要原因是{review_label('reason', reason)}，当前状态是{review_label('mood', mood)}，"
        f"预计持有或观察时间是{review_label('holding', holding)}。"
    )

    if outcome:
        outcome_text = f"你补充的实际结果或成本是：{outcome}。这一点很重要，因为复盘不能只看想法，也要看真实行为之后的盈亏、手续费和情绪变化。"
    else:
        outcome_text = "你还没有填写已发生结果或成本。如果这是已经买入或卖出的操作，建议补上当前盈亏、手续费、持有天数和当时情绪。"

    risk_text = " ".join(hard_warnings + soft_notes) if hard_warnings or soft_notes else "目前没有明显越界信号，主要风险在于后续是否能按计划执行，而不是被短期新闻和涨跌带偏。"
    positive_text = " ".join(positives) if positives else "这次还缺少能证明它是学习型操作的依据，比如你为什么选它、准备观察什么指标、亏到多少会停止。"

    if hard_warnings:
        next_step = "下一步建议是先不要下单或继续加钱。把这次操作改成模拟观察 7 天，记录它为什么涨跌、你是否还想追、以及如果亏 10% 会不会影响生活。"
    elif soft_notes:
        capped = int(min(amount, learning_money)) if learning_money > 0 else 0
        if capped > 0:
            next_step = f"下一步建议是把金额先压到 {capped} 元以内，冷静 24 小时。冷静后如果还想做，就写下三个条件：为什么买、最多亏 {int(loss_limit) if loss_limit > 0 else '多少'} 元能接受、哪一天复盘。"
        else:
            next_step = "下一步建议是先不实投，改成观察清单。等备用金和短期支出不被影响后，再考虑小额体验。"
    else:
        next_step = "下一步可以小额执行，但要把它当作学习实验。执行后记录买入时间、价格、手续费、当时情绪和复盘日期，不要因为一天涨跌临时改变计划。"

    return (
        f"我先按你的真实操作来复盘：{verdict}\n\n"
        f"{reserve_text}\n\n"
        f"{action_text}\n\n"
        f"{outcome_text}\n\n"
        f"这次值得肯定的地方是：{positive_text}\n\n"
        f"需要注意的地方是：{risk_text}\n\n"
        f"{next_step}\n\n"
        "最后给你一个复盘问题：如果这笔钱短期亏到你写的承受线，或者连续三天刷到相反观点，你还会按原计划执行吗？如果答案是不确定，那这次更适合先观察，不适合加钱。"
    )


def build_plan_or_review(profile: dict | None, action: dict) -> dict:
    kind = str(action.get("kind", "review"))
    if kind == "plan":
        citations = retrieve("小额理财计划 资金分层 复盘 手续费 风险")
        base = local_study_plan(profile)
        prompt = f"请根据用户理财档案刷新一份本周入门理财计划。\n\n本地计划草稿：\n{base}"
        llm_answer = call_llm(prompt, citations, "小额计划", profile)
        return with_llm_debug({"answer": llm_answer or base, "mode": "llm_rag" if llm_answer else "plan", "citations": citations})

    citations = retrieve("投资行为复盘 风险 心理 贷款 杠杆 手续费")
    base = local_review(profile, action)
    prompt = (
        "用户提交了一次准备或已经发生的理财操作，请做个性化行为复盘。\n"
        "注意：准备买入不是天然错误；如果金额在学习资金范围内、没有借钱杠杆、用户能说清逻辑，可以允许“小额尝试 + 明确复盘”。\n"
        "请不要输出模板化的五点清单，要像学长学姐一样结合用户的具体金额、动机和情绪说人话。\n"
        "这次必须引用用户填写的实际字段做分析，包括资金来源、信息来源、预计持有时间、最多可承受亏损、已发生结果或成本。没有填写的地方要明确追问，不要假装知道。\n"
        "请给出一个具体判断：暂停、降额观察、延迟 24 小时、模拟观察，或小额学习实验。不要只说投资有风险。\n"
        f"用户行为：{json.dumps(action, ensure_ascii=False)}\n\n"
        f"本地复盘草稿：\n{base}"
    )
    llm_answer = call_llm(prompt, citations, "计划复盘", profile)
    answer = llm_answer or base
    mode = "llm_rag" if llm_answer else "review"
    return with_llm_debug({"answer": answer, "mode": mode, "citations": citations})


def risk_answer() -> str:
    return (
        "我先帮你按一下暂停键。\n\n"
        "你这句话里出现了高风险信号，例如贷款、借钱、杠杆、带单、保本高收益或短线翻倍。\n\n"
        "对大学生来说，这已经不是入门理财学习，而是可能失控的高风险投机。我的建议很明确：\n"
        "1. 不要贷款理财；\n"
        "2. 不要用花呗、借呗、信用卡投资；\n"
        "3. 不要相信保本高收益和私聊带单；\n"
        "4. 不要下载陌生 App 或转账给个人；\n"
        "5. 如果只是想学习，可以先用模拟观察或小额可承受资金。"
    )


def concept_answer(question: str) -> str | None:
    if "回测" in question:
        return (
            "回测是把一个投资想法或策略放回历史数据里模拟一遍，看看如果过去按这个方法操作，大概会出现什么结果。\n\n"
            "举个例子：你想知道“每个月固定买入某个指数基金”过去 3 年表现如何，就可以用历史数据做回测，观察收益、最大回撤、波动、连续亏损时间等。\n\n"
            "但回测不是预测未来。过去有效，不代表未来一定有效。很多策略看起来回测很好，可能只是刚好适合过去那段行情，或者参数被过度优化。\n\n"
            "你可以把回测当成学习工具：它帮你提前感受一个策略可能经历的波动，而不是证明它一定赚钱。"
        )
    if "回撤" in question:
        return (
            "回撤是账户从最高点往下跌了多少。\n\n"
            "比如 1000 元涨到 1200 元，又跌回 900 元，从 1200 到 900 的这段下跌就是回撤。"
            "它重要是因为回撤代表你真实会感受到的心理压力。新手常常只看收益，却低估自己看到亏损时会不会焦虑、会不会想立刻卖出或加仓回本。"
        )
    if "手续费" in question or "费率" in question:
        return (
            "手续费是买入、卖出或持有理财产品时产生的成本。\n\n"
            "频繁买卖不一定让你更赚钱，但手续费会先发生。对大学生新手来说，理解手续费很重要，因为有些短线操作还没赚到钱，费用已经先扣掉了。"
        )
    if "定投" in question:
        return (
            "定投是定期投入固定金额。它的作用不是保证赚钱，而是减少一次性买在高点的压力。\n\n"
            "定投更适合长期不用的钱，不适合拿生活费硬投。"
        )
    return None


def answer_question(question: str, profile: dict | None = None) -> dict:
    if re.search(r"贷款|借钱|花呗|借呗|信用卡|杠杆|合约|带单|保本|稳赚|月收益|翻倍|梭哈|全部投入|私聊|转账|陌生", question):
        citations = retrieve(question)
        llm_answer = call_llm(question, citations, "风险护栏", profile)
        return with_llm_debug({"answer": llm_answer or risk_answer(), "mode": "llm_rag" if llm_answer else "risk", "citations": citations})

    concept = concept_answer(question)
    if concept:
        citations = retrieve(question)
        llm_answer = call_llm(question, citations, "专业知识解释", profile)
        return with_llm_debug({"answer": llm_answer or concept, "mode": "llm_rag" if llm_answer else "knowledge", "citations": citations})

    if re.search(r"热点|新闻|AI|人工智能|芯片|半导体|算力|机器人|科技|降息|降准|利率|黄金|油价|新能源|消费|政策", question, re.I):
        return analyze_news_deep({"title": question, "summary": ""}, profile)

    if re.search(r"计划|复盘|买入|卖出|加仓|减仓|定投|观察清单|学习路径", question):
        return build_plan_or_review(profile, {"kind": "plan", "notes": question})

    citations = retrieve(question)
    if citations:
        llm_answer = call_llm(question, citations, "知识库检索问答", profile)
        answer = llm_answer or (
            "我按知识库先帮你拆一下：\n\n"
            f"{citations[0]['snippet']}\n\n"
            "如果放到大学生入门理财场景里，重点不是马上做操作，而是先确认这笔钱是否短期不用、亏损是否影响生活、自己是否理解产品风险。"
        )
        return with_llm_debug({"answer": answer, "mode": "llm_rag" if llm_answer else "rag", "citations": citations})

    return with_llm_debug({
        "answer": (
            "可以，我们先像学长学姐聊天一样拆开看。你可以告诉我三件事：\n"
            "1. 这笔钱从哪里来，大概多少钱；\n"
            "2. 未来 1-3 个月要不要用；\n"
            "3. 你是想学习理财，还是被同学、家长或热点影响了。"
        ),
        "mode": "chat",
        "citations": [],
    })


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(APP_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def write_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.write_json(
                {
                    "ok": True,
                    "llm_configured": bool(LLM_API_KEY),
                    "llm_model": LLM_MODEL if LLM_API_KEY else "",
                    "llm_endpoint": normalize_llm_endpoint(LLM_BASE_URL) if LLM_API_KEY else "",
                    "llm_timeout": LLM_TIMEOUT,
                    "llm_last_error": LLM_LAST_ERROR,
                    "llm_cooldown_seconds": max(0, int(LLM_COOLDOWN_UNTIL - time.time())),
                    "llm_cache_size": len(LLM_CACHE),
                    "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            return
        if parsed.path == "/api/news":
            query = parse_qs(parsed.query)
            limit = int(query.get("limit", ["6"])[0])
            items, online, errors = fetch_news(limit=limit)
            for item in items:
                item["analysis_preview"] = news_preview(f"{item.get('title', '')}\n{item.get('summary', '')}")
            self.write_json(
                {
                    "items": items,
                    "online": online,
                    "errors": errors,
                    "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            return
        if parsed.path == "/api/search":
            query = parse_qs(parsed.query).get("q", [""])[0]
            self.write_json({"results": retrieve(query)})
            return
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/ask":
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            try:
                payload = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                self.write_json({"error": "Invalid JSON"}, status=400)
                return
            question = str(payload.get("question", "")).strip()
            profile = payload.get("profile") if isinstance(payload.get("profile"), dict) else None
            self.write_json(answer_question(question, profile))
            return
        if parsed.path == "/api/analyze-news":
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            try:
                payload = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                self.write_json({"error": "Invalid JSON"}, status=400)
                return
            news = payload.get("news") if isinstance(payload.get("news"), dict) else {"text": str(payload.get("text", ""))}
            profile = payload.get("profile") if isinstance(payload.get("profile"), dict) else None
            self.write_json(analyze_news_deep(news, profile))
            return
        if parsed.path == "/api/review-plan":
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            try:
                payload = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                self.write_json({"error": "Invalid JSON"}, status=400)
                return
            profile = payload.get("profile") if isinstance(payload.get("profile"), dict) else None
            action = payload.get("action") if isinstance(payload.get("action"), dict) else {}
            self.write_json(build_plan_or_review(profile, action))
            return
        self.write_json({"error": "Not found"}, status=404)


def main():
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"钱前问问 running at http://127.0.0.1:{port}/", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
