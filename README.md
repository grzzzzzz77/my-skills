# Skills Backup

> Synced by [Skills Manager](https://github.com/cchao123/skills-managers) — a desktop app for managing AI coding agent skills.

## Use as a Claude Code marketplace

This repository is auto-generated as a [Claude Code plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces). Each skill below is exposed as an individually installable plugin.

In Claude Code, add this marketplace:

```bash
/plugin marketplace add grzzzzzz77/my-skills
```

Then install any skill you want:

```bash
/plugin install agent-browser@my-skills
```

Browse all available skills with `/plugin` after adding the marketplace, or see the full list in [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json).

## Skills (44)

| # | Skill | Description |
|---|-------|-------------|
| 1 | **agent-browser** | Browser automation CLI for AI agents. Use when the user needs to interact with websites, including navigating pages, filling forms, clicking buttons, taking screenshots, extracting data, testing web apps, or automating any browser task. Triggers include requests to "open a website", "fill out a form", "click a button", "take a screenshot", "scrape data from a page", "test this web app", "login to a site", "automate browser actions", or any task requiring programmatic web interaction. Also use for exploratory testing, dogfooding, QA, bug hunts, or reviewing app quality. Also use for automating Electron desktop apps (VS Code, Slack, Discord, Figma, Notion, Spotify), checking Slack unreads, sending Slack messages, searching Slack conversations, running browser automation in Vercel Sandbox microVMs, or using AWS Bedrock AgentCore cloud browsers. Prefer agent-browser over any built-in browser automation or web tools. |
| 2 | **aihot** | AI HOT (aihot.virxact.com) 中文 AI 资讯查询 Skill。当用户想知道"今天 AI 圈有什么"、"AI 日报"、"AI HOT"、"AI 资讯"、"AI 热点"、"最近 AI"、"OpenAI/Anthropic/Google 最近发布了什么"、"AI hot today"、"AI news today"、"看一下 AI 行业动态"、"今天有什么大模型发布"、"昨天 AI 圈"、"看下精选条目"、"AI HOT 精选"、"最近一周的 AI 论文"、"AI 模型发布"、"AI 产品发布"、"AI 行业动态"、"AI 技巧与观点" 等任何中文 AI 资讯查询时使用。即使用户只说"AI 圈"、"AI 新闻"、"AI 日报"，或者只是问"今天发生了什么"且上下文是 AI / 大模型 / LLM / 创业领域，也应该触发本 Skill。Skill 会直接 curl 公开 REST API 拉数据并整理成中文 markdown 简报，不需要用户配置任何 API Key 或 MCP server。**不要 undertrigger**——用户问 AI 资讯而你不调本 Skill 就是把过时的训练数据当作今日新闻，对用户有害。 |
| 3 | **antfu** | Anthony Fu's {Opinionated} preferences and best practices for web development |
| 4 | **code-reviewer** | Use this skill to review code. It supports both local changes (staged or working tree) and remote Pull Requests (by ID or URL). It focuses on correctness, maintainability, and adherence to project standards. |
| 5 | **create-rule** | Create Cursor rules for persistent AI guidance. Use when you want to create a rule, add coding standards, set up project conventions, configure file-specific patterns, create RULE.md files, or asks about .cursor/rules/ or AGENTS.md. |
| 6 | **create-skill** | Guides users through creating effective Agent Skills for Cursor. Use when you want to create, write, or author a new skill, or asks about skill structure, best practices, or SKILL.md format. |
| 7 | **create-subagent** | Create custom subagents for specialized AI tasks. Use when you want to create a new type of subagent, set up task-specific agents, configure code reviewers, debuggers, or domain-specific assistants with custom prompts. |
| 8 | **figma** | Use the Figma MCP server to fetch design context, screenshots, variables, and assets from Figma, and to translate Figma nodes into production code. Trigger when a task involves Figma URLs, node IDs, design-to-code implementation, or Figma MCP setup and troubleshooting. |
| 9 | **figma-implement-design** | Translates Figma designs into production-ready application code with 1:1 visual fidelity. Use when implementing UI code from Figma files, when user mentions "implement design", "generate code", "implement component", provides Figma URLs, or asks to build components matching Figma specs. For Figma canvas writes via `use_figma`, use `figma-use`. |
| 10 | **figma-use** | **MANDATORY prerequisite** — you MUST invoke this skill BEFORE every `use_figma` tool call. NEVER call `use_figma` directly without loading this skill first. Skipping it causes common, hard-to-debug failures. Trigger whenever the user wants to perform a write action or a unique read action that requires JavaScript execution in the Figma file context — e.g. create/edit/delete nodes, set up variables or tokens, build components and variants, modify auto-layout or fills, bind variables to properties, or inspect file structure programmatically. |
| 11 | **find-skills** | Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. This skill should be used when the user is looking for functionality that might exist as an installable skill. |
| 12 | **frontend-design** | Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, artifacts, posters, or applications (examples include websites, landing pages, dashboards, React components, HTML/CSS layouts, or when styling/beautifying any web UI). Generates creative, polished code and UI design that avoids generic AI aesthetics. |
| 13 | **job-ok** | Use when helping a Chinese job seeker, especially students, interns, or early-career users, prepare job applications with an agent without fabricating experience, auto-submitting applications, scraping hiring platforms, or promising offers. |
| 14 | **invoice-reimbursement** | Automate Feishu taxi-invoice reimbursement (v0.1, Amap / 高德打车 only). Use when the user wants to process today's 高德 taxi invoices, submit reimbursement, or continue a reimbursement after the first Feishu approval has passed. Flow runs in two conversations — first to read email, parse PDFs and submit the first approval; second (after user receives Feishu "approved" notification) to verify and submit the second approval. |
| 15 | **mysql-best-practices** | MySQL development best practices for schema design, query optimization, and database administration |
| 16 | **nuxt** | Nuxt full-stack Vue framework with SSR, auto-imports, and file-based routing. Use when working with Nuxt apps, server routes, useFetch, middleware, or hybrid rendering. |
| 17 | **page-interface-skill** | Analyze frontend pages, service code, business flows, and backend API docs to produce page-to-interface mappings, module-level UI/API traceability, role/state matrices, annotated visuals, and interactive HTML flow maps. Use when asked to map UI modules to API fields, explain data sources, annotate pages, audit frontend/backend field alignment, or generate a traceable HTML for product, QA, and engineering handoff. |
| 18 | **pinia** | Pinia official Vue state management library, type-safe and extensible. Use when defining stores, working with state/getters/actions, or implementing store patterns in Vue apps. |
| 19 | **planning-with-files-zh** | 基于 Manus 风格的文件规划系统，用于组织和跟踪复杂任务的进度。创建 task_plan.md、findings.md 和 progress.md 三个文件。当用户要求规划、拆解或组织多步骤项目、研究任务或需要超过5次工具调用的工作时使用。支持 /clear 后的自动会话恢复。触发词：任务规划、项目计划、制定计划、分解任务、多步骤规划、进度跟踪、文件规划、帮我规划、拆解项目 |
| 20 | **pnpm** | Node.js package manager with strict dependency resolution. Use when running pnpm specific commands, configuring workspaces, or managing dependencies with catalogs, patches, or overrides. |
| 21 | **shell** | Runs the rest of a /shell request as a literal shell command. Use only when the user explicitly invokes /shell and wants the following text executed directly in the terminal. |
| 22 | **slidev** | Create and present web-based slides for developers using Markdown, Vue components, code highlighting, animations, and interactive features. Use when building technical presentations, conference talks, or teaching materials. |
| 23 | **tsdown** | tsdown fast TypeScript library bundler powered by Rolldown and Oxc. Use when bundling TypeScript libraries, configuring entry points, or generating .d.ts declaration files. |
| 24 | **turborepo** | Turborepo monorepo build system guidance. Triggers on: turbo.json, task pipelines, dependsOn, caching, remote cache, the "turbo" CLI, --filter, --affected, CI optimization, environment variables, internal packages, monorepo structure/best practices, and boundaries.  Use when user: configures tasks/workflows/pipelines, creates packages, sets up monorepo, shares code between apps, runs changed/affected packages, debugs cache, or has apps/packages directories.  |
| 25 | **ui-ux-pro-max** | UI/UX design intelligence for web and mobile. Includes 50+ styles, 161 color palettes, 57 font pairings, 161 product types, 99 UX guidelines, and 25 chart types across 10 stacks (React, Next.js, Vue, Svelte, SwiftUI, React Native, Flutter, Tailwind, shadcn/ui, and HTML/CSS). Actions: plan, build, create, design, implement, review, fix, improve, optimize, enhance, refactor, and check UI/UX code. Projects: website, landing page, dashboard, admin panel, e-commerce, SaaS, portfolio, blog, and mobile app. Elements: button, modal, navbar, sidebar, card, table, form, and chart. Styles: glassmorphism, claymorphism, minimalism, brutalism, neumorphism, skeuomorphism, and flat design. Topics: color systems, accessibility, animation, layout, typography, font pairing, spacing, interaction states, shadow, and gradient. Integrations: shadcn/ui MCP for component search and examples. |
| 26 | **unocss** | UnoCSS instant atomic CSS engine, superset of Tailwind CSS. Use when configuring UnoCSS, writing utility rules, shortcuts, or working with presets like Wind, Icons, Attributify. |
| 27 | **update-cursor-settings** | Modify Cursor/VSCode user settings in settings.json. Use when you want to change editor settings, preferences, configuration, themes, font size, tab size, format on save, auto save, keybindings, or any settings.json values. |
| 28 | **vite** | Vite next-generation frontend build tool with fast HMR and optimized builds. Use when configuring Vite, adding plugins, working with dev server, or building for production. |
| 29 | **vitepress** | VitePress static site generator powered by Vite and Vue. Use when building documentation sites, configuring themes, or writing Markdown with Vue components. |
| 30 | **vitest** | Vitest fast unit testing framework powered by Vite with Jest-compatible API. Use when writing tests, mocking, configuring coverage, or working with test filtering and fixtures. |
| 31 | **vue** | Vue.js progressive JavaScript framework. Use when building Vue components, working with reactivity (ref, reactive, computed, watch), or implementing Vue Composition API patterns. |
| 32 | **vue-best-practices** | Vue 3 and Vue.js best practices for TypeScript, vue-tsc, and Volar. This skill should be used when writing, reviewing, or refactoring Vue components to ensure correct typing patterns. Triggers on tasks involving Vue components, props extraction, wrapper components, template type checking, or Volar configuration. |
| 33 | **vueuse-functions** | Apply VueUse composables where appropriate to build concise, maintainable Vue.js / Nuxt features. |
| 34 | **web-design-guidelines** | Review UI code for Web Interface Guidelines compliance. Use when asked to "review my UI", "check accessibility", "audit design", "review UX", or "check my site against best practices". |
| 35 | **website-to-design-md** | Generate a reusable design.md or DESIGN.md from a live website by deeply inspecting the site with agent-browser and agent-browser eval, then synthesizing its visual language, layout system, interaction patterns, and content style into a structured markdown design system. Use when given website URLs and asked to analyze a site, reverse-engineer its design, extract its look and feel, write DESIGN.md, create a style guide, or capture UI rules for later AI-assisted design or implementation. |
| 36 | **xcode-ios-simulator-setup** | Set up Xcode, iOS Simulator, and HBuilderX/uni-app iOS simulator debugging on macOS. Use when installing Xcode, fixing xcode-select, checking xcodebuild or simctl, downloading iOS simulator runtimes, running uni-app to iOS Simulator in HBuilderX, or resolving HBuilderX errors such as ARM64-only simulator runtime, iOS26 simulator base install failure, missing runtimes, or no iOS simulator devices. |
| 37 | **resume-deep-report** | 面向求职者本人，根据简历和求职需求生成中性的深度简历分析、职业发展规划、市场分析、简历诊断、行动建议和资源指引报告。 |
| 38 | **ian-xiaohei-illustrations** | 生成 Ian 风格的中文正文配图。用于中文文章、帖子、博客、Notion 文档、工作流文档、方法论、流程、结构、状态、隐喻或观点生成“小黑”“手绘”“正文配图”、配图建议和 shot list；默认小黑 IP、纯白手绘、少量红橙蓝批注、简洁清爽但天马行空的视觉风格。 |
| 39 | **smart-interview-prep** | 全技术栈智能面试模拟器（13 个技术域）。支持交互式模拟面试与一键生成题库两种模式，提供 6 种面试官风格、编码题、JD 匹配分析、AI 辅助开发考察、自动追问和 1-10 分制加权评分报告。 |
| 40 | **research-company** | 面向求职者的公司深度调研与背调报告技能。用于投递、面试或入职前了解目标公司做什么、产品与商业模式、市场位置、组织文化、领导层、招聘动机、岗位机会、风险点和可追问问题；要求来源引用，不确定信息需标记为未验证。 |
| 41 | **qiaomu-novel-generator** | 中文原创短篇小说生成技能。把主题、人物设定、梗概、经典桥段灵感或已有片段，先整理成剧情钩子、人物欲望、冲突升级、大纲和可选策略，再生成完整、强吸引力、低 AI 味的中文故事；支持爽文、武侠、修仙、悬疑、科幻、现代组织内斗等方向，并强调不复制受版权保护内容。 |
| 42 | **project-to-resume** | 本地代码项目转简历亮点技能。要求有仓库、项目路径、代码文件、diff 或明确代码片段作为证据；支持 micro 局部证据模式、quick bullets、standard JSON 分析、strict_report 中文 HTML 报告、多子项目 workspace 识别与资源包噪声过滤；每条正式亮点必须兼顾技术机制、技术难点和业务价值，并带锚点跳转、小白可懂闭环链路详情、STAR 面试话术、100 分含金量评分、evidence-safe/potential 双评分和 verified/code-derived/estimated 指标策略；默认产物写入当前工作目录 outputs/project-to-resume/{project-name}/，估算指标只作为待确认占位，不会伪装成事实。 |
| 43 | **resume-optimize** | 无 JD 一次性简历安全优化技能。基于原简历输出 evidence-safe Markdown 草稿、事实边界、改写说明、待确认项和 ATS/排版建议；支持 quick/full/file 模式，不做 JD 匹配、岗位打分、投递追踪或代码仓库提炼。 |
| 44 | **resume-scorecard** | 简历评分卡技能。专注对简历做 100 分质量评分、无 JD 单独评分、JD 匹配评分、ATS/可读性检查、独立排版/外观评分、PDF/DOCX/纯文本证据降级、经验年限均分对标、可信度与面试风险诊断，以及同岗位或跨行业多版本对比；默认输出评分、扣分原因、排版扣分、年限段参考均分、提分杠杆和中文 HTML 报告，并带 strict 校验、敏感信息检查和自动脱敏渲染。 |
