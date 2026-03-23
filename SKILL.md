---
name: paper-reading
description: Reviewer-level analysis for AI and ML papers with strict evidence grounding, claim mapping, mathematical derivation analysis, experiment-to-claim auditing, latest arXiv version resolution, hjfy link insertion, papers.cool related-paper retrieval, selected community blog roundup, and report-first outputs for local PDFs, arXiv papers, source tarballs, or pasted text.
---

# Paper Reading

## 概览

执行 AI / ML 论文的 reviewer-level 深读，先建立可追溯的事实层，再输出单文件报告或定向问答。

默认覆盖两类任务：

- `report`：面向整篇论文，生成 `outputs/<paper_id>/report.md`
- `qa`：面向定向提问，在对话中按固定证据结构回答，不强制写文件

## 选择模式

- 用户给整篇论文、PDF、arXiv、source tarball，或要求“精读 / 深读 / reviewer 分析 / 生成报告 / 判断是否值得复现”时，进入 `report` 模式
- 用户只问某一部分，例如“这个定理在什么假设下成立”“实验是否真的验证了主张”“有哪些反对观点”，进入 `qa` 模式
- 用户同时要报告和局部答疑时，先完成 `report`，再复用同一证据层回答局部问题

## 核心规则

始终遵守以下规则：

1. 先区分三类内容，再写结论
   - 作者显式主张
   - 原文支持的隐含主张
   - 你自己的推断
2. 第三类内容不得混入正式结论、表格或“论文贡献”表述
3. 所有判断都要能回溯到论文原文或真实文献；找不到就明确写“不确定 / 论文未提及 / 未检索到可靠文献”
4. 不要把“合理猜测”写成事实，不要替作者补齐动机、实验目的、公式含义或文献立场
5. 讨论实验时，优先问“这组实验究竟验证了哪条主张”，而不是只复述结果
6. 讨论相关工作时，只接受真实来源；优先 arXiv、OpenReview、会议官网、期刊页面与作者主页
7. 社区博客不是正式学术证据，只能作为“外部阅读入口”和“辅助理解材料”
8. 报告语言默认中文优先：除论文标题、作者名、公式符号、数据集 / 方法正式名称、必要缩写外，能用中文尽量用中文
9. 图片必须图随论证走，不再把结构图、训练曲线、定性图统一堆在顶部

按需读取：

- `references/reviewer_rubric.md`
- `references/uncertainty_policy.md`
- `references/literature_search.md`

## `report` 工作流

当任务是整篇论文深读时，按以下顺序执行：

1. 准备输入
   - 接受本地 PDF、PDF URL、arXiv URL / arXiv ID、粘贴全文、可选 source tarball
   - 若用户未给 `paper_id`，从 arXiv ID、文件名或 URL 自动解析

2. 运行 `scripts/prepare_paper.py`
   - 写出 `outputs/<paper_id>/paper.txt`
   - 有 source tarball 时，优先解包到 `outputs/<paper_id>/source/`
   - 优先保留源码图；不够时再尝试 PDF embedded images；仍不够时回退到整页截图
   - 生成 `outputs/<paper_id>/artifacts.json`
   - 若是 LaTeX source，额外提取 `figure_catalog`
   - `figure_catalog` 至少包含：
     - `figure_id`
     - `path`
     - `caption`
     - `label`
     - `source_tex_file`
     - `section_hint`
     - `placement_role`
     - `placement_confidence`

3. 运行 `scripts/fetch_report_context.py`
   - 从官方 arXiv `abs` 页解析最新版 `arxiv_idvN`
   - 访问一次 `https://hjfy.top/arxiv/<arxiv_idvN>`，不等待翻译完成
   - 抓取 `papers.cool` 论文页与 related-search 页面
   - 写出 `outputs/<paper_id>/report_context.json`

4. 运行 `scripts/build_report.py`
   - 读取 `artifacts.json` 与 `report_context.json`
   - 基于 `templates/report_template.md` 生成单文件 `report.md`
   - 自动插入：
     - 最新版 arXiv 链接
     - hjfy 最新版链接
     - papers.cool 论文页与 related-search 链接
     - papers.cool 相关论文表格
     - 就地插图槽位与图注摘要
   - 插图默认归位规则：
     - `overview` 放在“核心观点 / 总体结构”附近
     - `method_detail` 放在“方法 / 算法构造”附近
     - `stability_or_training`、`main_experiment`、`qualitative` 放在实验章节附近
     - `failure_case` 放在“潜在未讨论因素”或“系统性质疑”附近
   - 固定图槽名称使用中文：
     - `总体结构图`
     - `方法细节图`
     - `训练稳定性图`
     - `主实验相关图`
     - `定性结果图`
     - `失败案例图（如有）`

5. 联网补齐外部信息
   - 先按 `references/literature_search.md` 的规则自动检索社区解读博客
   - 社区检索必须独立完成，不要把用户给的链接当作社区区的发现来源
   - 社区区只允许两类页面：
     - `zhuanlan.zhihu.com` 的知乎专栏文章
     - `blog.csdn.net/.../article/details/...` 的 CSDN 博客文章
   - 社区检索采用“Google 风格的标题优先查询”，顺序固定为：
     - `zhihu "<paper full title>"`
     - `csdn "<paper full title>"`
     - `zhuanlan.zhihu.com "<paper full title>"`
     - `site:zhuanlan.zhihu.com "<paper full title>"`
     - `site:blog.csdn.net "<paper full title>"`
   - 只有当标题检索召回为零或明显不足时，才补充：
     - `zhihu <paper acronym>`
     - `csdn <paper acronym>`
     - `zhihu "<core title phrase>"`
     - `csdn "<core title phrase>"`
   - 每条候选都要经过页面类型过滤和“是否为论文解读文章”的判定
   - 排除知乎问题页、回答列表页、用户主页、CSDN 下载页、专栏目录页、聚合转载页，以及 alphaXiv、ChatPaper、Bytez、项目页、代码仓库、镜像阅读页
   - 只有标题或摘要片段足以表明“这是目标论文的解读文章”时，才可写入 `report.md` 顶部

6. 完成正式分析
   - 按模板章节结构写完分析正文
   - 第 2 章必须把对公式、目标分解、损失设计和理论外推的质疑直接写在相关理论小节里
   - 第 5 章只保留工程实现、实验外推、部署边界和失败模式
   - 第 6 章只保留整体反思、开放问题、复现前确认事项和最终判断
   - 填完“主张表”
   - 填完“实验-主张对应矩阵”
   - 把论文中的主结果表与关键消融表按原值转录为 Markdown 表格

## `report` 完成标准

以下条件未满足时，不算完成：

- 若输入可可靠解析为 arXiv 论文，`report.md` 顶部必须出现最新版 arXiv 链接和最新版 hjfy 链接
- `report.md` 顶部必须出现 papers.cool 论文页、related-search 链接和相关论文表格
- `report.md` 顶部的社区区必须命名为 `社区解读博客`
- 社区区只允许出现独立搜索得到的知乎专栏 / CSDN 博客文章
  - 不要把用户提供的链接算作独立搜索结果
  - 不要把 alphaXiv、ChatPaper、Bytez、GitHub、镜像阅读页、项目页写进去
  - 如果严格完成“标题优先检索 + 站点补检 + 简称补救”后仍无结果，就明确写“当前未独立检索到可核验的知乎 / CSDN 论文解读博客”
  - 如果有结果但不足 `5` 条，就明确写“当前仅独立检索到以下可核验的知乎 / CSDN 论文解读博客，数量不足 5 条”
- 报告中的标题与固定标签默认中文化；除专业专名外，能用中文尽量用中文
- 报告中不再保留独立的 `Key Figures` 板块
- 结构图必须出现在方法或总体结构分析附近
- 训练曲线、主实验图、定性图必须出现在对应实验章节附近
- 如果图片自动归位失败，要显式写出缺口，不允许继续把图堆在顶部
- 第 2 章必须包含：
  - `2.4 公式与核心理论的边界`
  - `2.5 理论假设、替代解释与未证成部分`
- 第 5 章只允许讨论工程与证据边界，不再作为理论质疑总包章节
- 第 6 章必须是最后的整体反思、开放问题与复现判断，不要把公式质疑延后到这里
- 第 3 节必须包含“主结果表”与“关键消融表”
- 主结果表与关键消融表必须转录原始数值，不能只写段落式总结
- “主张表”与“实验-主张对应矩阵”不能保留空行、占位行或 `TODO`

对非 arXiv 输入：

- 若无法可靠解析 arXiv ID，则 `hjfy` 与 `papers.cool` 相关区块显式写 `N/A`
- 不猜测，不伪造，不根据标题相似度硬匹配

## `qa` 模式

当任务是定向问题时，不要强制生成文件，但要沿用同一套证据标准。

回答固定用 4 段：

1. `直接结论`
2. `原文证据`
3. `相关文献对照`
4. `边界 / 不确定性`

执行方式：

- 先从论文原文中定位与问题直接相关的段落、公式、表格、实验或附录
- 再判断该问题属于哪一类：理论、实验、相关工作、复现价值、工程可用性
- 若问题需要外部文献，按 `references/literature_search.md` 联网检索真实论文
- 若证据不足，明确停在“无法确认”，不要用常识补齐

## 输出约定

`report` 模式默认输出：

- `outputs/<paper_id>/report.md`
- `outputs/<paper_id>/paper.txt`
- `outputs/<paper_id>/figures/`
- `outputs/<paper_id>/pages/`
- 可选 `outputs/<paper_id>/source/`
- `outputs/<paper_id>/artifacts.json`
- `outputs/<paper_id>/report_context.json`

`artifacts.json` 至少保留：

- `paper_id`
- `input_source`
- `text_extraction_method`
- `image_source`
- `image_list`
- `page_list`
- `source_dir`
- `selected_figures`
- `figure_catalog`
- `unresolved_gaps`

`report_context.json` 至少保留：

- `arxiv_id_base`
- `arxiv_id_versioned`
- `arxiv_abs_url`
- `hjfy_url`
- `hjfy_visited_at`
- `papers_cool_paper_url`
- `papers_cool_keywords`
- `papers_cool_related_query_url`
- `papers_cool_related_papers`

不要改变这些路径约定，除非用户明确要求更换目录结构。
