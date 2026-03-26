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

<p>
  <a href="#项目概览">项目概览</a> •
  <a href="#核心能力">核心能力</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#输出结构">输出结构</a> •
  <a href="#设计原则">设计原则</a> •
  <a href="#适用场景">适用场景</a>
</p>

</div>

---
## ✨ 项目概览

`paper-reviewer-final-v4-skill` 是终版增强后的 **可执行版 Codex Skill**。  
它的目标不是生成一份普通的论文摘要，而是构建一份真正适合 **系统精读、审稿式分析、公式理解、工程映射和研究复盘** 的论文阅读报告。

最终唯一主体交付物为：

```text
{arxiv_id}/{arxiv_id}_阅读报告.md
```

这份报告强调：

- **自包含**：只看主报告，也能把握论文全貌
- **固定章节**：适合长期批量化沉淀
- **严格 reviewer-level**：强调主张、证据、实验支撑、边界与局限
- **公式友好**：对关键公式做分级、翻译、拆解与工程映射
- **图表完整**：核心图、主结果表、消融表、相关工作表进入主报告
- **就地解释**：图、表、公式解释尽量插入最合适的上下文位置

---

## 🔥 为什么做这个项目

很多论文阅读工具只能输出“摘要式总结”，但对于真正需要深入理解论文的人来说，远远不够。

这个 Skill 更关注：

- 论文到底在解决什么问题
- 作者到底提出了哪些核心主张
- 这些主张分别由哪些理论或实验支撑
- 关键公式到底在做什么
- 这些公式在训练 / 推理 / 工程实现中分别起什么作用
- 哪些结论是真正被验证了的，哪些只是作者暗含的推断
- 如果做复现，最应该先抓哪些模块和实验设置

换句话说，它不是为了“快速看过”，而是为了“真正看懂”。

---

## 🚀 核心能力

### 1. Reviewer-level paper analysis

不是普通总结，而是更偏审稿人视角的阅读报告，尽量覆盖：

- 研究背景与动机
- 问题设定
- 核心主张
- 方法逻辑链
- 实验支撑强度
- 消融解释
- 相关工作定位
- 局限性与边界

---

### 2. Formula-aware reading enhancement

本版本最重要的增强点是 **公式理解增强**。

#### Key equation priority
- **A级**：必须看懂
- **B级**：建议理解
- **C级**：知道用途即可

#### Equation understanding card
对于关键公式，会尽量补充：

- 公式编号
- 公式原文
- 作用
- 符号表
- 自然语言翻译
- 分项拆解
- 与上下文公式的关系
- 训练 / 推理作用
- 代码对应
- Toy Example
- 删除该项后的影响
- 强假设
- 阅读难点提醒

#### Three-layer translation
每个关键公式尽量给出三层解释：

- **一句话直译**
- **技术拆解**
- **工程映射**

#### Toy Example
对最关键的 **1–3 个公式**，尽量给出极简数值例子，帮助建立直觉。

---

### 3. Context-aware inline insertion

这个 Skill 不追求把信息堆在附录，而是尽量提升连续阅读体验。

- **图片按上下文插入**
- **表格按论证链插入**
- **关键公式解释就地插入**
- **让读者在同一阅读位置看到：公式 + 图 + 表 + 解释**

例如：

- 问题定义公式 → `1.2 / 2.2`
- 损失函数、核心模块公式 → `2.3`
- 假设与边界相关公式 → `2.4`
- 与实验现象直接相关的公式 → `3.x` 附近

---

### 4. Main report as the only deliverable

最终重点不是一堆零散缓存文件，而是一份真正可阅读的主报告：

```text
{arxiv_id}/{arxiv_id}_阅读报告.md
```

报告目标是做到：

- **只看主报告，就能理解论文大致全貌**
- **只看主报告，就能定位关键图表与公式**
- **只看主报告，就能判断论文贡献和边界**
- **只看主报告，就能辅助工程实现与复现**

---

## 📌 v4 新增重点

在 final 版基础上，v4 新增了“**公式理解增强**”。


1. **关键公式优先级**
   - A级：必须看懂
   - B级：建议理解
   - C级：知道用途即可

2. **公式理解卡**
   - 公式编号
   - 公式原文
   - 作用
   - 符号表
   - 自然语言翻译
   - 分项拆解
   - 与上下文公式的关系
   - 训练 / 推理作用
   - 代码对应
   - Toy Example
   - 删除该项后的影响
   - 强假设
   - 阅读难点提醒

3. **三层翻译**
   - 一句话直译
   - 技术拆解
   - 工程映射

4. **Toy Example**
   - 对最关键的 1–3 个公式，尽量给出极简数值例子

---


## 🧠 设计原则

### v3: Key tables must not be missing

这一版强调：

- 只要某张表支撑正文核心结论，就必须转写进主报告
- 如果表太宽，可以拆表
- 如果抽取不完整，必须回到 PDF / HTML 手工核对补齐
- 不允许出现“正文讨论了某张关键表，但主报告没有对应表格”的情况

### v4: Equation explanations must be inline

这一版修复了 v3 中“公式理解卡集中堆放”的问题：

- 不再建议单独设置一个公式集中区
- 关键公式解释应像图片一样，插入到最适合的上下文位置
- 目标是让读者在同一阅读位置同时看到：

**公式 + 图 + 表 + 解释**

---

## ✅ 关键约束

除了 v4 的新增能力，本项目仍保留以下关键约束：

- 主报告必须 **自包含**
- 图片必须 **按上下文插入**
- **相关论文表、主结果表、消融表、外部文献清单** 都必须写进主报告
- `hjfy / papers.cool` 状态 **不展示在最终报告里**

---

## ⚡ 快速开始

### 1. Bootstrap

```bash
bash scripts/bootstrap.sh
```

### 2. Run with arXiv URL

```bash
bash scripts/run_pipeline.sh "https://arxiv.org/abs/2510.12796"
```

### 3. Run with arXiv ID

```bash
bash scripts/run_pipeline.sh "2510.12796"
```

---

## 📂 输出结构

输出目录结构如下：

```text
{arxiv_id}/
├── {arxiv_id}_阅读报告.md   # 唯一主体交付物
├── metadata.json
├── raw/
├── images/
├── cache/
└── logs/
```

其中最重要的是：

```text
{arxiv_id}/{arxiv_id}_阅读报告.md
```

这是最终交付给读者的主报告。

---

## 🧩 适用场景

这个项目尤其适合：

- 论文精读
- reviewer-level 学术分析
- 公式密集型论文阅读
- 批量论文阅读与沉淀
- 写 related work / survey 前的前置分析
- 做方法复现前的结构化理解
- 训练研究生或团队成员建立系统阅读习惯

---



## 🤝 License

这个项目根据[MIT License](LICENSE).


---

## ⭐ Support

如果这个项目对你有帮助，欢迎点一个 **Star / Watch / Fork** 支持一下项目发展。
