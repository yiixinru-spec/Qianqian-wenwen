const state = { profile: null, news: [] };

const riskPattern =
  /贷款|借钱|花呗|借呗|信用卡|杠杆|合约|带单|保本|稳赚|月收益|翻倍|梭哈|全部|私聊|转账|陌生|高收益|币圈|虚拟货币/i;

const fallbackNews = [
  {
    title: "AI 算力需求持续升温，市场关注芯片与云服务产业链",
    source: "离线演示",
    category: "科技",
    published: "备用新闻",
    summary: "用于演示热点雷达分析结构。接入联网新闻源后，这里会替换为实时新闻。",
  },
  {
    title: "消费刺激政策继续释放，旅游、零售和餐饮修复受关注",
    source: "离线演示",
    category: "财经",
    published: "备用新闻",
    summary: "用于演示政策变量如何影响消费板块。",
  },
  {
    title: "利率变化影响债券价格和成长型资产估值",
    source: "离线演示",
    category: "金融",
    published: "备用新闻",
    summary: "用于演示利率、债券和估值之间的关系。",
  },
];

const danmakuItems = [
  { type: "focus", tag: "关注", text: "我也在看 AI 算力，但还没决定要不要加观察清单" },
  { type: "learn", tag: "学习", text: "刚搞懂最大回撤，发现热门板块也可能跌很多" },
  { type: "mood", tag: "状态", text: "看到同学赚钱有点心动，但先不急着冲" },
  { type: "risk", tag: "提醒", text: "生活费别拿去追热点，先留备用金" },
  { type: "focus", tag: "关注", text: "黄金上涨是不是和避险情绪有关？" },
  { type: "learn", tag: "学习", text: "今天才知道利好不等于马上上涨" },
  { type: "mood", tag: "状态", text: "我备用金还没攒够，先模拟观察" },
  { type: "risk", tag: "提醒", text: "有人私聊带单一定要小心" },
  { type: "focus", tag: "关注", text: "消费政策会不会影响旅游和零售？" },
  { type: "learn", tag: "学习", text: "正在补手续费和持有期，避免频繁买卖" },
  { type: "mood", tag: "状态", text: "基金跌过一次，现在更想先看懂再买" },
  { type: "risk", tag: "提醒", text: "看到热门新闻先问：是不是已经涨过了？" },
];

const money = (value) => `${Math.max(0, Math.round(value)).toLocaleString("zh-CN")} 元`;

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatText(value) {
  return escapeHtml(value).replace(/\n/g, "<br>");
}

function labelMap(value) {
  return (
    {
      newbie: "完全新手",
      basic: "了解一点",
      tried: "有过小额尝试",
      low: "偏低，亏 5% 会焦虑",
      mid: "中等，可接受 10% 波动",
      high: "较高，可承受 20% 波动",
      learn: "想学习理财",
      grow: "想让钱生钱",
      peer: "受同学/朋友影响",
      hot: "刷到热门板块",
      family: "家长建议",
    }[value] || value
  );
}

function readProfile() {
  const monthlyLiving = Number(document.querySelector("#monthlyLiving").value || 0);
  const currentFunds = Number(document.querySelector("#currentFunds").value || 0);
  const shortExpense = Number(document.querySelector("#shortExpense").value || 0);
  const emergencyFund = Number(document.querySelector("#emergencyFund").value || 0);
  const experience = document.querySelector("#experience").value;
  const riskFeeling = document.querySelector("#riskFeeling").value;
  const motivation = document.querySelector("#motivation").value;
  const oneMonthEmergencyGap = Math.max(0, monthlyLiving - emergencyFund);
  const requiredReserve = shortExpense + oneMonthEmergencyGap;
  const rawLearningMoney = Math.max(0, currentFunds - requiredReserve);
  const riskCap = riskFeeling === "low" ? 300 : riskFeeling === "mid" ? 600 : 1000;
  const learningMoney = Math.min(rawLearningMoney, riskCap);
  const level =
    learningMoney <= 0 ? "暂不适合实投" : riskFeeling === "low" ? "偏保守新手" : riskFeeling === "mid" ? "稳健学习型" : "可小额进阶观察";

  return {
    monthlyLiving,
    currentFunds,
    shortExpense,
    emergencyFund,
    experience,
    riskFeeling,
    motivation,
    oneMonthEmergencyGap,
    requiredReserve,
    rawLearningMoney,
    learningMoney,
    level,
  };
}

function renderProfile() {
  const profile = readProfile();
  state.profile = profile;
  const card = document.querySelector("#profileCard");
  card.innerHTML = `
    <div class="stat-row"><span>当前可支配资金</span><strong>${money(profile.currentFunds)}</strong></div>
    <div class="stat-row"><span>短期确定支出</span><strong>${money(profile.shortExpense)}</strong></div>
    <div class="stat-row"><span>1 个月备用金缺口</span><strong>${money(profile.oneMonthEmergencyGap)}</strong></div>
    <div class="stat-row"><span>可用于理财学习</span><strong>${money(profile.learningMoney)}</strong></div>
    <div class="stat-row"><span>理财经验</span><strong>${labelMap(profile.experience)}</strong></div>
    <div class="stat-row"><span>风险承受</span><strong>${labelMap(profile.riskFeeling)}</strong></div>
    <div class="stat-row"><span>当前动机</span><strong>${labelMap(profile.motivation)}</strong></div>
    <div class="${profile.learningMoney > 0 ? "highlight" : "warn-box"}">
      ${profile.learningMoney > 0
        ? `建议把真实投入控制在 ${money(profile.learningMoney)} 以内，目标是学习理财逻辑和波动。`
        : "建议先补齐备用金或做模拟观察，暂时不要把生活费、应急钱拿去实投。"}
    </div>
  `;
  renderMiniProfile(profile);
  renderPlan();
  return profile;
}

function renderMiniProfile(profile = state.profile || readProfile()) {
  document.querySelector("#miniProfile").innerHTML = `
    <div class="mini-stat"><span>可学习资金</span><strong>${money(profile.learningMoney)}</strong></div>
    <div class="mini-stat"><span>风险承受</span><strong>${labelMap(profile.riskFeeling)}</strong></div>
    <div class="mini-stat"><span>当前动机</span><strong>${labelMap(profile.motivation)}</strong></div>
  `;
}

function renderPlan() {
  const profile = state.profile || readProfile();
  const learningMoney = profile.learningMoney;
  const lowRisk = Math.round(learningMoney * 0.5);
  const observe = Math.round(learningMoney * 0.3);
  const keep = Math.max(0, learningMoney - lowRisk - observe);
  const steps =
    learningMoney > 0
      ? [
          `先保留 ${money(profile.shortExpense + profile.oneMonthEmergencyGap)} 作为短期支出和 1 个月备用金，不把这部分钱拿去投资。`,
          `用不超过 ${money(lowRisk)} 体验低风险、高流动性工具，理解到账、收益显示和流动性。`,
          `用约 ${money(observe)} 建立基金或板块观察清单，先观察波动，不追热点。`,
          `保留 ${money(keep)} 作为学习缓冲，每周复盘收益、波动、手续费和情绪变化。`,
        ]
      : [
          "先把应急备用金补到至少 1 个月最低生活费，再考虑真实投入。",
          "可以先做模拟观察，记录一个感兴趣板块的涨跌和新闻原因。",
          "每周学习一个基础概念，例如回测、回撤、净值、手续费、定投。",
          "复盘时重点看自己是否因为同学、短视频或热点产生冲动。",
        ];

  document.querySelector("#planCard").innerHTML = steps
    .map(
      (step, index) => `
      <div class="plan-step">
        <span class="step-no">${index + 1}</span>
        <p>${escapeHtml(step)}</p>
      </div>
    `,
    )
    .join("");
}

function renderPlanAnswer(data) {
  document.querySelector("#planCard").innerHTML = `<div class="analysis-output">${renderAnswer(data)}</div>`;
}

function setView(name) {
  document.querySelectorAll(".view").forEach((view) => {
    view.classList.toggle("is-active", view.id === `view-${name}`);
  });
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("is-active", item.dataset.view === name);
  });
}

function addMessage(role, html) {
  const template = document.querySelector("#messageTemplate");
  const node = template.content.firstElementChild.cloneNode(true);
  node.classList.add(role);
  node.querySelector(".avatar").textContent = role === "user" ? "我" : "钱";
  node.querySelector(".bubble").innerHTML = html;
  const log = document.querySelector("#chatLog");
  log.appendChild(node);
  log.scrollTop = log.scrollHeight;
}

function addLoadingMessage() {
  const id = `loading-${Date.now()}`;
  addMessage("bot", `<span id="${id}">正在检索知识库、新闻源和风险规则...</span>`);
  return document.querySelector(`#${id}`).closest(".message");
}

function renderAnswer(data) {
  const citations =
    data.citations && data.citations.length
      ? `<div class="citations">${data.citations.map((item) => `<span>${escapeHtml(item.title)}</span>`).join("")}</div>`
      : "";
  const llmError = data.llm_error
    ? `<div class="warn-box">${escapeHtml(data.llm_error)}</div>`
    : "";
  const modeLabel =
    {
      llm_rag: "大模型 + RAG",
      rag: "知识库检索",
      knowledge: "专业知识",
      news_analysis: "热点分析",
      plan: "学习计划",
      review: "行为复盘",
      risk: "风险护栏",
      chat: "追问引导",
    }[data.mode || "chat"] || "智能回复";
  return `<div class="answer-mode">${modeLabel}</div>${llmError}${formatText(data.answer || "")}${citations}`;
}

function localFallbackAnswer(text) {
  return {
    mode: "chat",
    answer:
      riskPattern.test(text)
        ? "这个问题触发了风险护栏。建议先暂停，不要用借来的钱、信用额度或杠杆去投资。可以回到小额、可承受、可复盘的学习路径。"
        : "后端智能体接口暂时没有连接成功。请确认使用 python server.py 启动，这样才能使用 RAG、新闻接口和可选大模型能力。",
    citations: [],
  };
}

function openRiskModal(text) {
  const modal = document.querySelector("#riskModal");
  document.querySelector("#riskModalBody").textContent = text;
  modal.classList.add("is-open");
  modal.setAttribute("aria-hidden", "false");
}

function closeRiskModal() {
  const modal = document.querySelector("#riskModal");
  modal.classList.remove("is-open");
  modal.setAttribute("aria-hidden", "true");
}

function openOnboarding() {
  const modal = document.querySelector("#onboardingModal");
  modal.classList.add("is-open");
  modal.setAttribute("aria-hidden", "false");
}

function closeOnboarding() {
  const modal = document.querySelector("#onboardingModal");
  modal.classList.remove("is-open");
  modal.setAttribute("aria-hidden", "true");
}

async function askBot(text) {
  const loading = addLoadingMessage();
  const submitButton = document.querySelector("#chatForm button");
  if (submitButton) {
    submitButton.disabled = true;
    submitButton.textContent = "生成中";
  }
  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: text, profile: state.profile || readProfile() }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    loading.querySelector(".bubble").innerHTML = renderAnswer(data);
    if (data.mode === "risk" || riskPattern.test(text) || /高风险信号|暂停键/.test(data.answer || "")) {
      openRiskModal("你现在提到的内容触发了风险护栏。对大学生来说，这类行为容易把“想学习理财”变成“用借来的钱承担不确定风险”。建议先暂停，回到小额、可承受、可复盘的学习路径。");
    }
  } catch {
    const fallback = localFallbackAnswer(text);
    loading.querySelector(".bubble").innerHTML = renderAnswer(fallback);
    if (riskPattern.test(text)) {
      openRiskModal("你现在提到的内容触发了风险护栏。建议先暂停，不要用贷款、花呗、借呗、信用卡或杠杆参与投资。");
    }
  } finally {
    if (submitButton) {
      submitButton.disabled = false;
      submitButton.textContent = "发送";
    }
  }
}

function renderNewsCards(items, meta = {}) {
  document.querySelector("#newsStatus").textContent = meta.online ? `实时 · ${meta.updated_at || ""}` : "备用新闻";
  document.querySelector("#newsCards").innerHTML = items
    .map(
      (item, index) => `
      <article class="news-item">
        <div class="news-meta">${escapeHtml(item.category || "热点")} · ${escapeHtml(item.source || "新闻源")}</div>
        <h5>${escapeHtml(item.title)}</h5>
        <p>${escapeHtml(item.summary || "点击分析可查看影响变量、相关板块和新手观察点。")}</p>
        <div class="news-preview">${escapeHtml(item.analysis_preview || "点击 AI 解读查看影响链条。")}</div>
        <div class="news-actions">
          <button type="button" data-news-index="${index}">AI 解读</button>
          ${
            item.link
              ? `<a href="${escapeHtml(item.link)}" target="_blank" rel="noopener noreferrer">查看原文</a>`
              : `<span>暂无原文</span>`
          }
        </div>
        <div class="inline-news-analysis empty-state" id="inlineNewsAnalysis-${index}"></div>
      </article>
    `,
    )
    .join("");
}

function updateFocusPanel(items = []) {
  const focusItems = (items.length ? items : fallbackNews).slice(0, 3);
  document.querySelector("#focusList").innerHTML = focusItems
    .map(
      (item, index) => `
      <article class="focus-item">
        <button type="button" class="focus-main" data-focus-index="${index}">
          <div class="focus-head">
            <span class="focus-tag">${escapeHtml(item.category || "热点")}</span>
            <em>${escapeHtml(item.source || "新闻源")}</em>
          </div>
          <strong>${escapeHtml(item.title)}</strong>
          <span>${escapeHtml(item.analysis_preview || item.summary || "查看热点雷达了解影响链条。")}</span>
        </button>
        ${
          item.link
            ? `<a class="focus-link" href="${escapeHtml(item.link)}" target="_blank" rel="noopener noreferrer">原文</a>`
            : ""
        }
      </article>
    `,
    )
    .join("");
}

async function loadNews() {
  try {
    const response = await fetch("/api/news?limit=6");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    state.news = data.items || fallbackNews;
    renderNewsCards(state.news, data);
    updateFocusPanel(state.news);
    return data;
  } catch {
    state.news = fallbackNews;
    renderNewsCards(state.news, { online: false });
    updateFocusPanel(state.news);
    return { items: state.news, online: false };
  }
}

function renderDanmaku() {
  const rows = [
    document.querySelector("#danmakuRowOne"),
    document.querySelector("#danmakuRowTwo"),
    document.querySelector("#danmakuRowThree"),
  ];
  rows.forEach((row, rowIndex) => {
    const items = [...danmakuItems.slice(rowIndex * 4, rowIndex * 4 + 4), ...danmakuItems];
    row.innerHTML = items
      .map(
        (item) => `
        <span class="danmaku-pill" data-type="${escapeHtml(item.type)}">
          <em>${escapeHtml(item.tag)}</em>${escapeHtml(item.text)}
        </span>
      `,
      )
      .join("");
  });
}

function renderNewsAnalysis(data, index = null) {
  const target = document.querySelector("#newsAnalysis");
  target.classList.remove("empty-state");
  target.innerHTML = renderAnswer(data);
  if (index !== null) {
    const inlineTarget = document.querySelector(`#inlineNewsAnalysis-${index}`);
    if (inlineTarget) {
      inlineTarget.classList.remove("empty-state");
      inlineTarget.innerHTML = renderAnswer(data);
    }
  }
}

async function analyzeNewsItem(news, index = null, button = null) {
  const target = document.querySelector("#newsAnalysis");
  target.classList.remove("empty-state");
  target.textContent = "正在结合新闻内容、知识库和你的理财档案分析...";
  if (index !== null) {
    const inlineTarget = document.querySelector(`#inlineNewsAnalysis-${index}`);
    if (inlineTarget) {
      inlineTarget.classList.remove("empty-state");
      inlineTarget.textContent = "正在生成这条新闻的 AI 解读...";
      inlineTarget.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  } else {
    target.scrollIntoView({ behavior: "smooth", block: "center" });
  }
  const oldText = button ? button.textContent : "";
  if (button) {
    button.disabled = true;
    button.textContent = "分析中...";
  }
  try {
    const response = await fetch("/api/analyze-news", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ news, profile: state.profile || readProfile() }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    renderNewsAnalysis(data, index);
  } catch {
    renderNewsAnalysis({
      mode: "news_analysis",
      answer: "当前热点分析接口没有连上。请确认你是通过 http://127.0.0.1:8000/ 打开的页面，并且 PowerShell 里的 python -u server.py 没有关掉。",
      citations: [],
    }, index);
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = oldText || "AI 解读";
    }
  }
}

async function generatePlan() {
  const target = document.querySelector("#planCard");
  target.innerHTML = `<div class="analysis-output">正在结合你的理财档案刷新计划...</div>`;
  try {
    const response = await fetch("/api/review-plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile: state.profile || readProfile(), action: { kind: "plan" } }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    renderPlanAnswer(data);
  } catch {
    renderPlan();
  }
}

function collectReviewAction() {
  return {
    kind: "review",
    behavior: document.querySelector("#reviewBehavior").value,
    product: document.querySelector("#reviewProduct").value.trim(),
    amount: Number(document.querySelector("#reviewAmount").value || 0),
    moneySource: document.querySelector("#reviewMoneySource").value,
    infoSource: document.querySelector("#reviewInfoSource").value,
    reason: document.querySelector("#reviewReason").value,
    mood: document.querySelector("#reviewMood").value,
    holding: document.querySelector("#reviewHolding").value,
    lossLimit: Number(document.querySelector("#reviewLossLimit").value || 0),
    outcome: document.querySelector("#reviewOutcome").value.trim(),
    notes: document.querySelector("#reviewNotes").value.trim(),
  };
}

async function submitReview() {
  const action = collectReviewAction();
  const target = document.querySelector("#reviewResult");
  target.classList.remove("empty-state");
  target.textContent = "正在结合你的档案和这次行为做复盘...";
  try {
    const response = await fetch("/api/review-plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile: state.profile || readProfile(), action }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    target.innerHTML = renderAnswer(data);
    const joined = Object.values(action).join(" ");
    if (
      action.moneySource === "borrowed" ||
      action.infoSource === "group" ||
      riskPattern.test(joined) ||
      /建议暂停|高风险/.test(data.answer || "")
    ) {
      openRiskModal("这次复盘里出现了需要先停一下的信号。先把资金安全、情绪稳定和可承受范围确认清楚，再决定是否继续。");
    }
  } catch {
    target.innerHTML = renderAnswer({
      mode: "review",
      answer: "复盘接口暂时没有连接成功。先确认后端正在运行，再重新提交这次操作。",
      citations: [],
    });
  }
}

function init() {
  renderProfile();
  renderDanmaku();
  updateFocusPanel(fallbackNews);
  loadNews();
  addMessage(
    "bot",
    "你好，我是钱前问问。你可以问我理财概念、财经热点、资金怎么分配，或者让我帮你做小额学习计划。遇到贷款、杠杆、带单这类高风险行为，我会先帮你按暂停键。",
  );

  document.querySelectorAll(".nav-item").forEach((button) => {
    button.addEventListener("click", () => setView(button.dataset.view));
  });
  document.querySelectorAll("[data-open-view]").forEach((button) => {
    button.addEventListener("click", () => setView(button.dataset.openView));
  });
  document.querySelectorAll("[data-open-profile-modal]").forEach((button) => {
    button.addEventListener("click", openOnboarding);
  });
  document.querySelectorAll("[data-prompt]").forEach((button) => {
    button.addEventListener("click", async () => {
      const prompt = button.dataset.prompt;
      addMessage("user", escapeHtml(prompt));
      await askBot(prompt);
    });
  });

  document.querySelector("#profileForm").addEventListener("submit", (event) => {
    event.preventDefault();
    const profile = renderProfile();
    closeOnboarding();
    setView("chat");
    addMessage("user", "帮我生成我的理财起点卡");
    addMessage(
      "bot",
      `<div class="answer-mode">理财起点</div>
      当前可支配资金：${money(profile.currentFunds)}<br>
      短期确定支出：${money(profile.shortExpense)}<br>
      1 个月备用金缺口：${money(profile.oneMonthEmergencyGap)}<br>
      可用于理财学习：${money(profile.learningMoney)}<br><br>
      ${profile.learningMoney > 0 ? "可以小额开始，但目标是学习和复盘，不是追收益。" : "建议先补备用金或做模拟观察，暂时不要实投。"}`,
    );
  });

  document.querySelector("#chatForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = document.querySelector("#chatInput");
    const text = input.value.trim();
    if (!text) return;
    addMessage("user", escapeHtml(text));
    input.value = "";
    await askBot(text);
  });

  document.querySelector("#pushNews").addEventListener("click", async () => {
    const data = await loadNews();
    const first = (data.items || fallbackNews)[0];
    if (first) await analyzeNewsItem(first, 0, document.querySelector("[data-news-index='0']"));
  });

  document.querySelector("#newsCards").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-news-index]");
    if (!button) return;
    const item = state.news[Number(button.dataset.newsIndex)];
    if (item) await analyzeNewsItem(item, Number(button.dataset.newsIndex), button);
  });

  document.querySelector("#focusList").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-focus-index]");
    if (!button) return;
    const item = state.news[Number(button.dataset.focusIndex)] || fallbackNews[Number(button.dataset.focusIndex)];
    if (!item) return;
    setView("radar");
    await analyzeNewsItem(item, Number(button.dataset.focusIndex));
  });

  document.querySelector("#analyzeNews").addEventListener("click", async () => {
    const text = document.querySelector("#newsInput").value.trim();
    if (!text) return;
    await analyzeNewsItem({ title: text, summary: "", source: "用户输入", category: "自选" });
  });

  document.querySelector("#refreshPlan").addEventListener("click", generatePlan);
  document.querySelector("#reviewForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    await submitReview();
  });
  document.querySelector("#closeRiskModal").addEventListener("click", closeRiskModal);
  document.querySelector("#riskClose").addEventListener("click", closeRiskModal);
  document.querySelector("#riskKeepLearning").addEventListener("click", () => {
    closeRiskModal();
    setView("review");
  });
  document.querySelector("#riskModal").addEventListener("click", (event) => {
    if (event.target.classList.contains("risk-backdrop")) closeRiskModal();
  });
  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeRiskModal();
  });
}

init();
