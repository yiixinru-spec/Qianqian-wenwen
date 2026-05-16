# 从 0 到可提交的实现工作流程

这份流程用于把产品思路落成可体验智能体，并完成赛题提交材料。

## 阶段 1：确定 MVP 范围

本项目不做完整交易型理财 App，而是做一个智能体 MVP。

落地 3 个核心能力：

1. 我的理财起点
2. 热点雷达
3. 小额计划与复盘

风险护栏贯穿全流程。

## 阶段 2：准备智能体配置材料

已完成文件：

```text
agent/system_prompt.md
agent/workflow.md
agent/module_prompts.md
knowledge/
```

使用方式：

1. 把 `system_prompt.md` 复制到智能体平台的系统提示词。
2. 把 `knowledge/` 下的 5 个文档上传为知识库。
3. 把 `module_prompts.md` 中的 4 个快捷入口配置成按钮或工作流入口。

## 智能体技术架构建议

真正可用的版本不应该只靠固定话术。建议采用四层结构：

```text
大模型 LLM：负责自然对话、过来人式表达、追问和总结
RAG 知识库：负责基金、债券、费率、回撤、回测、风险等级等专业知识检索
实时工具：负责金融、财经、重大、科技新闻获取和热点雷达分析
规则护栏：负责贷款、杠杆、带单、保本高收益等风险行为拦截
```

本地 `server.py` 已提供一个简化版本：

- `/api/ask`：知识库检索问答，配置 `LLM_API_KEY` 后可走大模型 + RAG。
- `/api/news`：RSS 新闻获取，网络不可用时自动使用备用新闻演示。
- `/api/search`：知识库检索调试。

配置大模型时使用 OpenAI-compatible 接口：

```powershell
$env:LLM_API_KEY="你的 API Key"
$env:LLM_BASE_URL="https://api.openai.com/v1/chat/completions"
$env:LLM_MODEL="gpt-4o-mini"
python server.py
```

如果使用其他平台模型，只要兼容 OpenAI Chat Completions 格式，可以替换 `LLM_BASE_URL` 和 `LLM_MODEL`。

## 阶段 3：选择智能体平台

可选平台：

- 扣子
- Dify
- 通义智能体
- 智谱智能体
- 其他支持知识库和发布二维码的平台

平台能力优先级：

1. 能自定义系统提示词
2. 能上传知识库
3. 能配置快捷入口或工作流
4. 能发布体验链接和二维码
5. 最好能联网搜索新闻

如果暂时没有联网能力，可以先让用户粘贴新闻，智能体负责解读。这也能满足演示。

## 阶段 4：搭建智能体

### 1. 创建智能体

名称可暂用：

```text
钱前问问
```

一句话介绍：

```text
像懂行的过来人一样陪大学生建立理财起点、看懂财经热点、制定小额计划并复盘避险。
```

### 2. 粘贴系统提示词

复制 `agent/system_prompt.md` 中代码块内容。

### 3. 上传知识库

上传以下文档：

```text
knowledge/01_funds_classification.md
knowledge/02_glossary.md
knowledge/03_hot_news_radar.md
knowledge/04_risk_guardrails.md
knowledge/05_review_templates.md
```

### 4. 配置快捷入口

建议配置 4 个入口：

```text
我的理财起点
热点雷达
小额计划与复盘
风险护栏
```

对应提示词见 `agent/module_prompts.md`。

### 5. 配置新闻能力

优先方案：接入平台联网搜索或新闻插件，用于热点雷达。

备选方案：保留“粘贴新闻给 AI 解读”的入口。

## 阶段 5：测试智能体

用 `agent/evaluation_cases.md` 里的 6 个用例测试。

重点检查：

1. 是否能建立理财起点卡。
2. 是否能判断真正可用于理财学习的钱。
3. 是否能解读热点新闻，但不荐股。
4. 是否能生成小额计划和复盘问题。
5. 是否能在贷款、带单、杠杆、高收益骗局场景中触发风险护栏。

## 阶段 6：生成体验二维码

在智能体平台发布后，复制体验链接并生成二维码。

PPT 中需要放：

- 智能体二维码
- 一句话介绍
- 核心能力说明

## 阶段 7：制作 PPT

使用赛题模板 `AI产品经理赛道PPT模版.pptx`。

参考：

```text
docs/ppt_outline.md
docs/product_plan.md
```

控制在 12 页以内。使用 AI 生成或 AI 辅助改写的页面，右上角标红加粗“AI辅助”。

## 阶段 8：录制演示视频

参考：

```text
docs/demo_script.md
```

建议演示故事：

```text
用户拿到 3000 元奖学金，刷到 AI 科技热点，想全部投入相关基金。
智能体先建档，再判断资金，再解读热点，再生成小额计划。
当用户说“想用花呗多买一点”时，触发风险护栏。
```

视频要求：

- 3 分钟以内
- MP4
- 1080p
- 横屏
- 本人无需出镜

## 阶段 9：最终提交

提交材料：

1. PPT 转 PDF
2. 可体验二维码
3. 3 分钟演示视频
4. 可选 ZIP 附件：流程图、思维导图、智能体配置文档
