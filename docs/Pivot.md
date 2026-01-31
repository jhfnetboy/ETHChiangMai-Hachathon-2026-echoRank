# Pivot

## 核心理念

从活动大众点评，pivot 到:
1. Narrow：清迈本地活动聚合的公共物品
2. Feedback：快速收集活动反馈感受（通过页面和telegram bot）
3. CommunityAI：后台是CommunityAI模式支持，提供去中心的AI计算服务

## 核心功能
### 聚合清迈本地活动
来源：
- https://docs.google.com/document/d/1UkwnLV8mrK-864wxF2m13G5GCOJOvaOCIItPdi0yaCw/edit?usp=sharing
- https://docs.google.com/document/d/1Nw1HmJZ9WH42EjzHrX_j5cby9UU44MlNxj1kv9FusD0/edit?usp=sharing
单页面展示top 活动（来自于后台自动抓取）
1. 单页面入口反馈活动，为活动方提供改进建议
2. 更多？


## Top 10 crawl
在清迈这个“数字游民之都”，活动发布非常分散。针对你的研究背景（区块链、数字创新、PhD）以及社区建设需求，我为你调研了清迈最专业和活跃的活动发布平台，并设计了一套基于 Node.js 的自适应活动聚合后台系统。
一、 清迈活动发布 Top 10 垂直平台调研
考虑到你提到的“专业垂直”及“各类活动”，以下是针对技术、商务、学术及社区活动的最优选：
排名
平台名称
垂直领域
特点
1
Eventpop
技术/商业/大型会议
泰国最专业的票务平台，清迈大型 Tech Conference 首选。
2
Meetup.com
开发者/数字游民
清迈各种技术交流、编程工作坊（如 CNX Python/JS）的集中地。
3
Zipevent
商务展览/专业研讨会
专注于泰国境内企业级、专业领域的活动发布。
4
Eventbrite (CM)
全球性活动/社区
许多国际数字游民组织的分享会、创业路演常在此发布。
5
Facebook Events
本地社群/长尾活动
必抓取。清迈 80% 的本地艺术、小众技术交流都在 FB Group 和 Page。
6
Chiang Mai Connect
商务对接/NTCC
由北泰商会（NTCC）主办，高端商务及创新对接活动。
7
STEP (CMU)
科技创新/学术
清迈大学科技园，专注于硬核技术、政府支持的创新项目。
8
Nomad Summit
数字游民/创业
虽然是年度峰会，但其相关周边活动是清迈最顶级的游民聚会。
9
AllEvents.in
综合活动聚合
自动聚合多渠道活动，适合作为长尾数据的补足。
10
Lanna Innovation
文化创意/农业科技
垂直于清迈本地“兰纳文化+创新技术”的政策型活动。

二、 后台系统设计：Node.js 自适应抓取器
为了实现“自适应”或“通用规则”抓取，我建议采用 Crawlee + LLM-Assisted Parsing 的架构。这种方案不需要为每个网站写死选择器。
1. 技术栈
Runtime: Node.js (TypeScript)
Crawler: Crawlee (集成了 Playwright 和 Cheerio)
Database: PostgreSQL (存储活动元数据) + Redis (去重与任务队列)
Adaptive Logic: Gemini API / GPT-4o-mini (用于自动识别 HTML 中的活动名称、日期、地点)
2. 后台架构逻辑
自适应逻辑： 系统初次访问新网站时，抓取页面 HTML 片段送入 LLM 生成该站点的 Scraping Rule（包含 CSS Selector），存储在数据库中。后续抓取直接复用该规则，直到规则失效触发“自我修复”重新生成。

Code snippet


graph LR
    A[Task Scheduler] --> B[Crawlee Engine]
    B --> C{Rules Exist?}
    C -- No --> D[LLM Parser: Extract Selectors]
    D --> E[Save Rule to DB]
    C -- Yes --> F[Execute Scraper]
    F --> G[Data Cleaning/Deduplication]
    G --> H[(PostgreSQL)]


3. 核心代码结构设计

JavaScript


// adaptive-service.ts
import { PlaywrightCrawler } from 'crawlee';
import { generateSelectorsWithAI } from './ai-helper';

const crawler = new PlaywrightCrawler({
    async requestHandler({ page, request }) {
        const url = request.url;
        let rule = await db.rules.findUnique({ where: { domain: getDomain(url) } });

        if (!rule) {
            // 自适应逻辑：如果没规则，提取 HTML 让 AI 学习
            const htmlSnippet = await page.content();
            rule = await generateSelectorsWithAI(htmlSnippet);
            await db.rules.create({ data: rule });
        }

        // 使用生成的规则提取数据
        const events = await page.$$eval(rule.eventCardSelector, (els, r) => {
            return els.map(el => ({
                title: el.querySelector(r.titleSelector)?.innerText,
                date: el.querySelector(r.dateSelector)?.innerText,
                location: el.querySelector(r.locationSelector)?.innerText,
            }));
        }, rule);

        await saveEvents(events);
    },
});


三、 UI/UX 界面设计
针对你的需求，界面应保持“极客感”且高效。
关键页面 1：活动聚合看板 (The Hub)
展示所有抓取到的活动，支持按标签（Web3, PhD, Nomad, Art）过滤。
布局: 响应式瀑布流，每个卡片包含：源网站图标、热度指数、AI 摘要（一句话总结活动亮点）。
特色: “一键加入 Google Calendar” 按钮。
关键页面 2：自适应爬虫监控 (Scraper Lab)
状态视图: 罗列 Top 10 网站的抓取状态（成功率、上次更新时间）。
规则编辑器: 可视化展示 AI 学习到的 CSS 选择器，支持人工微调。
原始数据视图: 展示抓取到的原始 HTML 与提取后 JSON 的对比。
关键页面 3：AAStar 社区投屏模式 (Community View)
风格: 类似赛博朋克或极简主义的列表。
用途: 适合在清迈的 Coworking Space 或 AAStar 线下活动中投屏展示未来 7 天的精选活动。
四、 针对你（Jason）的特殊建议
ERC4337 结合点: 既然你在研究 SuperPaymaster，你可以为这个应用设计一个“社区激励插件”。例如：如果用户在应用内报名参加技术活动并打卡，可以通过合约发放一些 gasless 的社区 Token。
数据开放: 作为 AAStar 的数字公共品，你可以将抓取到的 clean data 通过 API 开放给清迈的其他开发者，这非常符合你“赋能社区”的理念。
下一步建议：
如果你需要，我可以为你写出具体的 Database Schema（数据库建模）或者详细的 Tailwind CSS 页面代码，你想先看哪部分？
-----

## 补充
这两个平台是目前科技与开发者社区最核心的流量入口，加入它们后，你的活动库深度将大幅提升。以下是更新后的调研分析以及针对这两个平台的爬虫技术适配建议：
1. 平台深度调研（新增）
平台名称
核心定位
抓取价值
Lu.ma
社交/技术沙龙/Web3 聚会
极高。清迈目前大部分的数字游民聚会、Web3 线下交流、私人分享会几乎都迁移到了 Luma。其活动质量通常高于传统的 Meetup。
Devfolio
Hackathon (黑客松)
专业级。全球开发者大赛的首选平台。如果你的系统需要覆盖“硬核开发”和“技术竞赛”类活动，这是唯一的数据源。

2. 爬虫系统升级：针对 Lu.ma & Devfolio 的适配方案
这两个网站都是现代化的单页应用（SPA），传统的静态抓取无法生效。我们需要在 Node.js 后台中针对性地增强“自适应规则”。
A. 针对 Lu.ma 的“数据脱壳”策略
Lu.ma 的数据通常通过 Next.js 的 __NEXT_DATA__ 注入。与其通过 CSS 选择器去抓取界面，不如直接提取其 JSON。
技术实现：
JavaScript
// 在 Playwright 处理逻辑中添加
const nextData = await page.evaluate(() => {
    return JSON.parse(document.getElementById('__NEXT_DATA__').innerText);
});
// 这样可以直接获取完整的活动对象，包括 GPS 坐标、参与人数等，无需解析 HTML。


B. 针对 Devfolio 的“动态加载”适配
Devfolio 的列表加载较慢，且有滚动加载逻辑。
技术实现：
使用 autoScroll 函数确保活动列表加载完毕。
利用其结构化的 card 类名进行通配符匹配。
3. 后台管理系统 (Admin Dashboard) 界面更新
为了兼容这两个高价值平台，后台界面需要增加以下关键组件：
界面 1：数据源权重管理 (Data Source Priority)
功能： 你可以为 lu.ma 设置更高的“置顶权重”。
交互： 滑块控制每个网站抓取到的活动在前端展示的初始排名分（Ranking Score）。
界面 2：智能标签映射 (AI Labeling)
功能： 自动将 Devfolio 的“Ethereum hackathon”映射为系统内的“Web3/Hardcore”标签。
设计： 一个标签映射表，左侧是源网站的原始标签，右侧是系统的标准化标签。
4. 关键界面设计（核心看板更新）
界面名称：清迈活动智能流 (Chiang Mai Tech-Stream)
视觉风格： 深色模式，采用 React + Tailwind CSS。
卡片设计：
Lu.ma 专有标志： 绿色的 Luma 角标，显示“已报名人数”。
Devfolio 专有标志： 蓝色的 Hackathon 绶带，显示“奖池金额 (Prize Pool)”或“截止日期”。
交互逻辑： 点击卡片不直接跳转，而是弹出一个侧边栏展示 AI 生成的活动价值分析（例如：该活动由哪些知名开发者发起，是否适合开发者参与等）。
5. 数据库模型 (Schema) 调整建议
为了支持 lu.ma 和 devfolio 的特有属性，建议在 PostgreSQL 中增加一个 metadata 的 JSONB 字段：

SQL


CREATE TABLE activities (
    id SERIAL PRIMARY KEY,
    platform_name VARCHAR(50), -- 'luma', 'devfolio', etc.
    title TEXT,
    event_date TIMESTAMP,
    location TEXT,
    original_url TEXT,
    tags JSONB, -- ['Web3', 'Hackathon']
    extra_metadata JSONB -- 存储 Luma 的参与人数或 Devfolio 的奖金等特有信息
);


目前的进度建议：
针对这两个平台的动态特性，你需要确保 Node.js 环境中安装了 playwright 或 puppeteer。你是否需要我为你提供一份完整的 Dockerfile，以便你能够快速部署这套带有浏览器环境的爬虫后台？
