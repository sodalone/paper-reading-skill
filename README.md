<div align="center">

<!-- # 📘 paper-reading-skill -->
![header](https://capsule-render.vercel.app/api?type=wave&color=auto&height=260&section=header&text=paper-reading-skill&fontSize=60)

[![GitHub stars](https://img.shields.io/github/stars/sodalone/paper-reading-skill?style=social)](https://github.com/sodalone/paper-reading-skill/stargazers)
[![GitHub watchers](https://img.shields.io/github/watchers/sodalone/paper-reading-skill?style=social)](https://github.com/sodalone/paper-reading-skill/watchers)
[![GitHub forks](https://img.shields.io/github/forks/sodalone/paper-reading-skill?style=social)](https://github.com/sodalone/paper-reading-skill/network/members)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](#license)
[![Markdown](https://img.shields.io/badge/output-Markdown-0A66C2)](#输出结构)
[![ArXiv](https://img.shields.io/badge/input-arXiv-b31b1b)](#运行方式)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-10a37f)](#paper-reading-skill)

**一个面向论文精读的可执行 Codex Skill**  
输出 **自包含**、**固定章节**、**reviewer-level**、**公式友好** 的高质量论文阅读报告。

</div>

---

## ✨ 项目简介

`paper-reading-skill` 是一套终版增强后的 **可执行版 Codex Skill**。  
它的目标不是简单“总结论文”，而是生成一份真正适合深入阅读、复盘、引用和二次研究的论文报告。

最终唯一主体交付物为：

```text
{arxiv_id}/{arxiv_id}_阅读报告.md
```

这份报告强调：

- **自包含**：只看主报告，也能大致掌握论文核心内容
- **固定章节**：阅读结构稳定，适合长期批量使用
- **reviewer-level**：偏审稿人视角，强调论证链路、贡献边界与实验支撑
- **公式友好**：对关键公式做分级、翻译、拆解与工程映射
- **图表齐全**：核心图、主结果表、消融表、相关工作表都会进入主报告
- **上下文插入**：图、表、公式解释都尽量放在最适合的阅读位置

---

## 🚀 这个 Skill 能做什么

### 1. 生成一份真正可读的论文精读报告

不是只有“摘要 + 方法 + 实验”的粗略总结，而是强调：

- 研究动机
- 问题定义
- 核心主张
- 方法逻辑链
- 关键公式解释
- 实验支撑力度
- 消融结果
- 相关工作定位
- 局限性与边界

### 2. 强化公式阅读体验

本版本最重要的增强点是 **公式理解增强**。

#### 公式优先级分级

- **A级**：必须看懂
- **B级**：建议理解
- **C级**：知道用途即可

#### 公式理解卡

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

#### 三层翻译

每个关键公式尽量给出三层解释：

- **一句话直译**
- **技术拆解**
- **工程映射**

#### Toy Example

对最关键的 **1–3 个公式**，尽量给出极简数值例子，帮助快速建立直觉。

### 3. 让图、表、公式真正“就地可读”

这个 Skill 不追求把信息堆到附录，而是追求阅读流畅度。

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

## 🌟 v4 新增重点

在 final 版基础上，本版重点增强了 **公式理解能力**：

### 新增内容

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
   - 训练/推理作用
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

## 📌 继承保留的核心约束

除了公式增强，本版依旧保留以下关键约束：

- 主报告必须 **自包含**
- 图片必须 **按上下文插入**
- **相关论文表、主结果表、消融表、外部文献清单** 都必须写进主报告
- `hjfy / papers.cool` 状态 **不展示在最终报告里**

---

## 🧠 v3 / v4 的关键设计原则

### v3：关键表格不得缺失

这一版进一步强调：

- 只要某张表支撑正文核心结论，就必须转写进主报告
- 如果表太宽，可以拆表
- 如果抽取不完整，必须回到 PDF / HTML 手工核对补齐
- 不允许出现：
  > 正文讨论了 Table 3 / Table 5 / Table 9，但主报告中没有对应表格

### v4：公式解释必须就地插入

这一版修复了 v3 中“公式理解卡集中堆放”的问题：

- 不再建议单独做一个公式集中区
- 关键公式解释应像图片一样，插入到最合适的上下文位置
- 目标是提升连续阅读体验，而不是制造跳读成本

---

## ⚙️ 运行方式

### 1. 初始化

```bash
bash scripts/bootstrap.sh
```

### 2. 运行 pipeline

支持传入 arXiv 链接：

```bash
bash scripts/run_pipeline.sh "https://arxiv.org/abs/2510.12796"
```

也支持直接传入 arXiv ID：

```bash
bash scripts/run_pipeline.sh "2510.12796"
```

---

## 📂 输出结构

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

## 🎯 设计目标

这个 Skill 的目标不是“做一份普通摘要”，而是尽量做到：

- **只看主报告，就能理解论文大致全貌**
- **只看主报告，就能定位关键图表与公式**
- **只看主报告，就能对论文贡献和边界形成判断**
- **只看主报告，就能辅助工程实现和后续复现**

---

## 🧩 适用场景

这个项目尤其适合：

- 论文精读
- reviewer-level 学术分析
- 公式密集型论文阅读
- 批量论文阅读与沉淀
- 写 related work / survey 前的前置分析
- 做方法复现前的结构化理解
- 训练研究生 / 新成员建立系统阅读习惯

---

## 📖 推荐阅读体验

建议按以下顺序使用：

1. 运行 pipeline 生成主报告
2. 先快速阅读主报告整体结构
3. 优先阅读：
   - 研究问题
   - 核心主张
   - 方法设计
   - 关键公式解释
   - 主结果表
   - 消融实验
   - 局限性分析
4. 再回看原论文 PDF，对照图、表、公式细节

这样可以大幅降低“直接啃原文”的阅读阻力。

---

## 🛠️ 核心特性总结

- ✅ 固定章节输出
- ✅ 主报告自包含
- ✅ reviewer-level 分析风格
- ✅ 公式分级与公式理解卡
- ✅ 三层公式翻译
- ✅ Toy Example
- ✅ 图片按上下文插入
- ✅ 主结果表 / 消融表 / 相关工作表不缺失
- ✅ 更适合工程映射与实现理解
- ✅ 适合长期批量论文阅读沉淀

---

## 🔮 后续可扩展方向

未来可以继续扩展：

- 多论文横向对比模式
- 自动生成 related work 矩阵
- 自动提取实验设置差异
- 自动汇总指标口径
- 方法模块与代码仓库的更强映射
- 面向特定领域的专用阅读模板

---

## 📁 项目结构示意

```text
paper-reading-skill/
├── AGENTS.md
├── SKILL.md
├── README.md
├── scripts/
│   ├── bootstrap.sh
│   └── run_pipeline.sh
├── templates/
├── references/
└── outputs/
```

---

## 🤝 License

本项目根据 [MIT License](LICENSE).

---




## ⭐ 如果这个项目对你有帮助

欢迎点一个 **Star / Watch / Fork** 支持一下项目发展。

[![GitHub stars](https://img.shields.io/github/stars/sodalone/paper-reading-skill?style=social)](https://github.com/sodalone/paper-reading-skill/stargazers)
[![GitHub watchers](https://img.shields.io/github/watchers/sodalone/paper-reading-skill?style=social)](https://github.com/sodalone/paper-reading-skill/watchers)
[![GitHub forks](https://img.shields.io/github/forks/sodalone/paper-reading-skill?style=social)](https://github.com/sodalone/paper-reading-skill/network/members)

---

