---
name: paper-reading
description: Reviewer-level analysis for AI and ML papers with strict evidence grounding, claim mapping, mathematical derivation analysis, experiment-to-claim auditing, latest arXiv version resolution, clear explanatory handling of hjfy and papers.cool links, and report-first outputs for local PDFs, arXiv papers, source tarballs, or pasted text.
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
7. 报告语言默认中文优先：除论文标题、作者名、公式符号、数据集 / 方法正式名称、必要缩写外，能用中文尽量用中文
8. 图片必须图随论证走，不再把结构图、训练曲线、定性图统一堆在顶部
9. 默认不要在 `report.md` 里输出原始块级 LaTeX 公式，如 `\[...\]`、`$$...$$`
    - 优先写成“公式含义 + 纯 Markdown 兼容表示”
    - 需要保留原文记号时，优先使用简短行内代码或 fenced `text` 代码块
    - 优先使用 ASCII 友好的公式记法，如 `p_theta`、`sum`、`prod`、`lambda_a`
    - 目标是让普通 Markdown 渲染器、编辑器预览和聊天界面都能稳定阅读
10. 处理外部资源链接时，不要把 `hjfy`、`papers.cool`、`related-search` 一股脑堆在报告最顶部
    - `hjfy` 链接要明确说明：这是中文翻译阅读入口
    - `papers.cool` 论文页要明确说明：这是论文卡片与检索入口
    - `papers.cool related-search` 要明确说明：这是查找关联论文 / 相关方向论文的入口
    - 这些链接应放在“阅读入口”“延伸阅读”“相关工作线索”之类的小节，或首次提及时就地解释
    - 若报告有“先给结论”小节，默认把上述入口放在“先给结论”之前
    - 除非用户明确要求，否则不要只给裸链接，不要把链接用途留给用户自己猜

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
   - 外部链接插入规则：
     - 不要把 arXiv、hjfy、papers.cool、related-search 全堆在文档开头做成一排链接
     - 若保留顶部入口，最多保留 `arXiv` 原文链接
     - `hjfy` 应放在“阅读入口”或“阅读辅助”处，并注明“中文翻译阅读入口”
     - `papers.cool` 与 `related-search` 应放在“延伸阅读”“相关工作线索”或相邻位置，并注明它们用于查找关联论文
     - `papers.cool` 相关论文表格应紧跟在上述说明后，不要孤立悬挂在报告顶部
     - 若正文采用“先给结论”的结构，默认把该链接小节放在“先给结论”之前
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
   - 若 `figure_catalog` 缺失或为空，但 `image_list` / `selected_figures` / `pages` 中已经存在可渲染图片，必须自动走 fallback，把图片插入报告
   - 只要 `figures/` 中已有可渲染图片，就不能继续交付“无图片的最终报告”

5. 运行 `scripts/validate_report.py`
   - 校验 `report.md` 中确实嵌入了 Markdown 图片
   - 校验 `report.md` 中至少有一张图片对应 `artifacts.json` 中的可渲染图片路径
   - 若校验失败，不得继续交付；必须回到图片提取或报告构建步骤修复

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

- 若输入可可靠解析为 arXiv 论文，`report.md` 中必须出现最新版 arXiv 链接与最新版 hjfy 链接，但不要求二者都在顶部
- `report.md` 中必须出现 papers.cool 论文页、related-search 链接和相关论文表格，但不要求它们堆在顶部
- `hjfy` 链接附近必须说明它用于看中文翻译
- `papers.cool` 与 `related-search` 链接附近必须说明它们用于查询关联论文或扩展相关工作
- 报告中的标题与固定标签默认中文化；除专业专名外，能用中文尽量用中文
- 报告中不再保留独立的 `Key Figures` 板块
- 结构图必须出现在方法或总体结构分析附近
- 训练曲线、主实验图、定性图必须出现在对应实验章节附近
- 如果图片自动归位失败，要显式写出缺口，不允许继续把图堆在顶部
- 如果 `figure_catalog` 为空，但 `figures/` 中已经存在可渲染图片，必须通过 fallback 继续插图，不能交付无图报告
- 必须运行 `scripts/validate_report.py --artifacts outputs/<paper_id>/artifacts.json --report outputs/<paper_id>/report.md` 并通过；未通过即视为未完成
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
