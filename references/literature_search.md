# Literature Search Rules

## Source Priority

学术结论只接受真实、可核验来源，优先级从高到低：

1. 会议官网 / 期刊页面
2. OpenReview
3. arXiv
4. 作者主页或项目主页
5. 机构仓库或其他可核验镜像

不要把博客、随手笔记、营销稿、聚合站摘要当成正式学术证据。

## Search Strategy for Papers

每次只围绕一个技术问题检索，不要把多个问题混在一条查询里。

推荐查询维度：

- 方法族名称 + `limitation` / `critique` / `failure mode`
- 关键假设 + `alternative` / `challenge` / `counterexample`
- 任务设定 + benchmark + comparison
- 论文标题 / 作者 + `response` / `discussion`

## Search Strategy for Community Blogs

社区区只用于提供“论文解读博客”，不是正式学术证据。

### Community Search Goal

默认只收两类页面：

1. `zhuanlan.zhihu.com/p/<id>` 的知乎专栏文章
2. `blog.csdn.net/.../article/details/<id>` 的 CSDN 博客文章

不要把以下页面写进社区区：

- 知乎问题页、回答列表页、用户主页
- CSDN 下载页、专栏目录页、聚合页、转载页
- alphaXiv、ChatPaper、Bytez、项目页、代码仓库、镜像阅读入口

### Community Search Order

社区检索采用“Google 风格的标题优先查询”，先用论文标题，再用简称补救。

推荐顺序：

1. 主查询：平台名 + 论文完整标题
   - `zhihu "<paper full title>"`
   - `csdn "<paper full title>"`
2. 二级补检：站点名 + 论文完整标题
   - `zhuanlan.zhihu.com "<paper full title>"`
   - `site:zhuanlan.zhihu.com "<paper full title>"`
   - `site:blog.csdn.net "<paper full title>"`
3. 只有当标题检索召回为零或明显不足时，才补充简称或标题核心短语
   - `zhihu <paper acronym>`
   - `csdn <paper acronym>`
   - `zhihu "<core title phrase>"`
   - `csdn "<core title phrase>"`

如果运行环境无法稳定访问 Google，就沿用同样的查询串，改走可访问的搜索后端；接受结果的过滤规则保持一致。

### Inclusion Rules

一条候选只有在满足以下条件时才可写入社区区：

- 页面类型属于知乎专栏或 CSDN 博客正文页
- 标题或摘要片段能明确对应目标论文，而不是只匹配某个常见缩写
- 标题或摘要片段能表明它是“解读 / 详解 / 论文阅读 / 阅读笔记 / 拆解 / review / 精读”等分析性文章，而不是单纯转发

如果抓不到正文：

- 仅当搜索结果标题和摘要片段已经足够表明“这是目标论文的解读文章”时才保留
- 否则直接丢弃，不要用“可能相关”补位

### User-Provided Links

用户给的链接可以用于后验比对覆盖率，但不能当作社区区的发现来源。

也就是说：

- 不要因为用户给了链接，就把它算作“独立搜索结果”
- 如果独立搜索没找到，同样要如实写“当前未独立检索到可核验的知乎 / CSDN 论文解读博客”
- 只有在单独的补充说明里，才可提及“用户另行提供了某链接”

### Dedup and Quality Filter

去重与筛选规则：

- 同一作者多平台重复发文，只保留信息密度更高的一份
- 排除无作者署名的搬运页
- 排除只复制摘要、机器翻译全文、没有分析的页面
- 排除聚合目录页、AI 批量洗稿页、营销页
- 优先保留真正有分析、有作者署名、能说明“为什么值得看”的条目

### Reporting Rule

`report.md` 顶部的社区区标题固定为 `社区解读博客`。

如果严格完成“标题优先检索 + 站点补检 + 简称补救”后：

- 没有结果：明确写“当前未独立检索到可核验的知乎 / CSDN 论文解读博客”
- 有结果但少于 `5` 条：明确写“当前仅独立检索到以下可核验的知乎 / CSDN 论文解读博客，数量不足 5 条”

不要再用其他阅读入口补位。

## What to Compare

文献对照至少覆盖两类：

1. 主流支持路径
   - 该论文延续了什么研究方向
   - 哪些代表工作与其结论一致
2. 竞争或反对路径
   - 是否已有工作质疑其假设
   - 是否有方法用更简单的机制解释同类结果

## Reporting Rules

- 明确写出论文名或作者名
- 只总结你确认过的结论
- 若无法判断是“支持”还是“平行相关”，就写成“相关但未形成直接支持证据”
- 若未检索到明确反对或支持证据，直接写“当前未检索到明确反对或支持证据”

## Minimal Citation Hygiene

- 优先引用与论文问题设定直接相关的工作
- 不要用无关但热门的论文凑“相关工作”
- 若引用 preprint，标清其为 `arXiv / preprint`
- 不要引用你没有真正打开和核对过的文献
