<div align="center">

![header](https://capsule-render.vercel.app/api?type=waving&color=0:0f172a,100:2563eb&height=280&section=header&text=paper-reading-skill&fontSize=58&fontColor=ffffff&desc=Reviewer-level%20paper%20reading%20reports&descAlignY=68)

[![GitHub stars](https://img.shields.io/github/stars/sodalone/paper-reading-skill?style=social)](https://github.com/sodalone/paper-reading-skill/stargazers)
[![GitHub watchers](https://img.shields.io/github/watchers/sodalone/paper-reading-skill?style=social)](https://github.com/sodalone/paper-reading-skill/watchers)
[![GitHub forks](https://img.shields.io/github/forks/sodalone/paper-reading-skill?style=social)](https://github.com/sodalone/paper-reading-skill/network/members)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](#license)
[![Markdown](https://img.shields.io/badge/output-Markdown-0A66C2)](#输出结构)
[![ArXiv](https://img.shields.io/badge/input-arXiv-b31b1b)](#运行方式)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-10a37f)](#paper-reading)

<p>
  <strong>一个面向多种论文类型的精读、证据审查与验证分析 Skill</strong>
</p>

<p>
  输出 <strong>自包含</strong>、<strong>主线清楚</strong>、<strong>核心内容完整</strong>、<strong>证据可追溯</strong> 的 Markdown 论文阅读报告
</p>


</div>

## 功能版本记录
| 日期 | 功能版本 | 对应分支 |
|---|---|---|
| 2026-08-05 | 通用论文模板、按论文类型选择证据载体、Claim 证据追溯与可读性验证 | `release_v2` / `main` |
| 2026-04-16 | 输出目录命名改为 `{arxiv_id}_{title}` | `release_v1.1` |
| 2026-03-23 | 初始版本 | `release_v1` |

当前 `main` 即 `release_v2`，两者指向同一个发布提交。

`Paper Reading` 是一个面向单篇 AI / 机器人论文的可执行 Codex skill。它会先运行内置脚本完成 arXiv 版本解析、网页与 PDF 抓取、参考文献与图片预处理，再识别论文类型，并生成一份 reviewer-level 的自包含 Markdown 阅读报告。

模板固定的是阅读问题和证据责任，不固定论文必须有什么内容。理论论文可以没有实验表，系统论文可以没有公式，原文无关键图片时可以不插图，短论文可以只有一条中心 Claim。不同论文使用不同证据载体：

- 理论论文：定义、假设、引理、定理、证明、反例与复杂度边界；
- 方法论文：机制、主结果、消融、泛化与代码语义；
- 系统 / 平台论文：接口、协议、系统测试、成本、失败案例与实现路径；
- 数据集 / benchmark：数据组成、划分、评测协议、覆盖、泄漏与公平性；
- 实证论文：对照、效应量、统计不确定性、稳健性与外推；
- 综述 / meta-analysis / 观点论文：范围、纳入标准、材料覆盖、综合或论证链、反方观点与遗漏。

这个目录里有两类文档：
- `SKILL.md`：给模型执行时读取的规则与工作流。
- `README.md`：给人看的发布说明，帮助你快速理解、安装和使用这个 skill。

## 适用场景
- 单篇 arXiv 论文的系统性精读
- 需要 reviewer-level 的理论、方法、系统、数据、实证、综述或观点分析
- 希望输出固定结构、可继续编辑的 Markdown 报告
- 需要把决定性证据及其原文定位写入同一份报告

## 不适用场景
- 纯摘要改写
- 多论文综述或 survey 式横向整理
- 没有原文依据的自由发挥
- 只想要一个很短的口语化总结

## 核心特性
- 自动解析最新 arXiv 版本，并准备 `raw/`、`images/`、`cache/` 等工作区
- 输出唯一主报告：`{arxiv_id}_{title}/{arxiv_id}_阅读报告.md`
- 按论文类型选择实验、证明、反例、协议、数据、系统测试或代码等证据载体，不设跨论文数量配额
- 关键图片、表格、公式、定理或协议仅在有助于理解或判断时就地解释；原文没有时不补造
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
{arxiv_id}_{title}/
├── {arxiv_id}_阅读报告.md
├── metadata.json
├── raw/
├── images/
├── cache/
└── logs/
```

其中 `{title}` 来自 arXiv 标题，会清洗为文件夹安全文本并把空格转为 `_`。

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
{arxiv_id}_{title}/{arxiv_id}_阅读报告.md
```

其余目录的作用如下：
- `raw/`：保存原始 PDF、网页和辅助抓取结果
- `images/`：保存抽取或裁剪后的插图素材
- `cache/`：保存中间结构化结果，便于补全报告
- `logs/`：保存运行日志与校验信息

## 关键约束
- 必须先跑脚本，再在生成的主报告上继续补全，不要新建平行报告
- 先识别论文类型，再选择匹配的证据载体；不得把方法/实验论文格式硬套到理论、系统、数据或观点论文
- 实际使用的图片、表格、公式、定理、证明链或协议应靠近其服务的解释；完整审计材料可进入同一报告的附录
- 所有核心 Claim 都必须进入 Claim—Evidence—Verdict 表，并在附录 D 独立定位
- 图片、公式、实验表、外部文献和 Claim 数量均不设统一配额；没有使用时应按模板说明不适用、原文未提供或检索边界
- 数学公式统一使用 `$...$` 和独立的 `$$ ... $$` 公式块
- 公式编号写在正文里，不在公式块内使用 `\tag{}`
- 优先使用原始 PDF 和 arXiv 源码包中的 figure，不使用论文网页截图作为最终插图

## 常见工作流
1. 用 `$paper-reading` 指定目标论文。
2. 让 skill 运行 `scripts/run_pipeline.sh` 完成预处理。
3. 在 `{arxiv_id}_{title}/{arxiv_id}_阅读报告.md` 中补全分析正文。
4. 交付前运行验证器，检查全部核心 Claim、决定性证据、必要细节和实际使用的外部文献是否都已落到主报告并可追溯。

## 面向发布的说明
- `SKILL.md` 保留给模型的执行指令，不建议把它当 README 直接复用。
- `agents/openai.yaml` 保存 UI 侧展示名、短描述和默认 prompt。
- `examples/` 提供最小示例提示词。
- `references/` 提供写作模板和补充规则，供模型按需读取。
