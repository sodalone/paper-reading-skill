<div align="center">

![header](https://capsule-render.vercel.app/api?type=waving&color=0:0f172a,100:2563eb&height=280&section=header&text=paper-reading-skill&fontSize=58&fontColor=ffffff&desc=Reviewer-level%20paper%20reading%20reports&descAlignY=68)

[![GitHub stars](https://img.shields.io/github/stars/sodalone/paper-reading-skill?style=social)](https://github.com/sodalone/paper-reading-skill/stargazers)
[![GitHub watchers](https://img.shields.io/github/watchers/sodalone/paper-reading-skill?style=social)](https://github.com/sodalone/paper-reading-skill/watchers)
[![GitHub forks](https://img.shields.io/github/forks/sodalone/paper-reading-skill?style=social)](https://github.com/sodalone/paper-reading-skill/network/members)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](#license)
[![Markdown](https://img.shields.io/badge/output-Markdown-0A66C2)](#输出结构)
[![ArXiv](https://img.shields.io/badge/input-arXiv-b31b1b)](#运行方式)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-10a37f)](#paper-reviewer-final-v4-skill)

<p>
  <strong>一个面向论文精读、审稿式分析与公式理解增强的可执行 Codex Skill</strong>
</p>

<p>
  输出 <strong>自包含</strong>、<strong>固定章节</strong>、<strong>严格 reviewer-level</strong>、<strong>公式友好</strong> 的高质量论文阅读报告
</p>


</div>

`Paper Reading` 是一个面向单篇 AI 论文的可执行 Codex skill。它会先运行内置脚本完成 arXiv 版本解析、网页与 PDF 抓取、参考文献与图片预处理，再基于这些材料生成一份 reviewer-level 的自包含 Markdown 阅读报告。

这个目录里有两类文档：
- `SKILL.md`：给模型执行时读取的规则与工作流。
- `README.md`：给人看的发布说明，帮助你快速理解、安装和使用这个 skill。

## 适用场景
- 单篇 arXiv 论文或 PDF 的系统性精读
- 需要 reviewer-level 的理论、方法、实验和相关工作分析
- 希望输出固定结构、可继续编辑的 Markdown 报告
- 需要把关键图片、结果表、消融表和公式解释直接落到正文

## 不适用场景
- 纯摘要改写
- 多论文综述或 survey 式横向整理
- 没有原文依据的自由发挥
- 只想要一个很短的口语化总结

## 核心特性
- 自动解析最新 arXiv 版本，并准备 `raw/`、`images/`、`cache/` 等工作区
- 输出唯一主报告：`{arxiv_id}/{arxiv_id}_阅读报告.md`
- 要求关键图片、主结果表、消融表、相关论文表直接写入主报告
- 强化公式阅读：关键公式需要就地解释，并统一数学公式格式
- 支持补充 hjfy、papers.cool 和真实外部文献线索，但最终交付物仍是单一 Markdown 报告

## 目录结构
```text
paper-reading-skill/
├── SKILL.md
├── README.md
├── requirements.txt
├── agents/
├── examples/
├── references/
├── scripts/
└── templates/
```

运行 pipeline 后，会在当前工作目录生成：

```text
{arxiv_id}/
├── {arxiv_id}_阅读报告.md
├── metadata.json
├── raw/
├── images/
├── cache/
└── logs/
```

## 依赖与安装
建议先在支持 `bash` 和 `python3` 的环境中安装依赖：

```bash
bash scripts/bootstrap.sh
```

它会创建 skill 自己的虚拟环境并安装 `requirements.txt` 中的依赖。

如果你是把它作为 Codex skill 发布或分发，保留当前目录名 `paper-reading-skill/` 即可；公开调用名统一使用 `$paper-reading`。

## 最小使用方式
在触发 skill 的 prompt 中明确指定论文输入，例如：

```text
使用 $paper-reading 阅读这篇论文：https://arxiv.org/abs/2510.12796
```

若你需要手动预跑流水线，可在 skill 根目录执行：

```bash
bash scripts/run_pipeline.sh "https://arxiv.org/abs/2510.12796"
```

也可以直接传 arXiv ID：

```bash
bash scripts/run_pipeline.sh "2510.12796"
```

## 输出结果
最终交付物只有一个主文件：

```text
{arxiv_id}/{arxiv_id}_阅读报告.md
```

其余目录的作用如下：
- `raw/`：保存原始 PDF、网页和辅助抓取结果
- `images/`：保存抽取或裁剪后的插图素材
- `cache/`：保存中间结构化结果，便于补全报告
- `logs/`：保存运行日志与校验信息

## 关键约束
- 必须先跑脚本，再在生成的主报告上继续补全，不要新建平行报告
- 图片、表格和公式解释都应就地插入，不要集中堆到单独章节
- 主结果表、关键消融表、相关论文表不能只留在缓存或附录
- 数学公式统一使用 `$...$` 和独立的 `$$ ... $$` 公式块
- 公式编号写在正文里，不在公式块内使用 `\tag{}`
- 优先使用原始 PDF 和 arXiv 源码包中的 figure，不使用论文网页截图作为最终插图

## 常见工作流
1. 用 `$paper-reading` 指定目标论文。
2. 让 skill 运行 `scripts/run_pipeline.sh` 完成预处理。
3. 在 `{arxiv_id}/{arxiv_id}_阅读报告.md` 中补全分析正文。
4. 交付前重新检查图片、表格、公式和外部文献是否都已落到主报告。

## 面向发布的说明
- `SKILL.md` 保留给模型的执行指令，不建议把它当 README 直接复用。
- `agents/openai.yaml` 保存 UI 侧展示名、短描述和默认 prompt。
- `examples/` 提供最小示例提示词。
- `references/` 提供写作模板和补充规则，供模型按需读取。
