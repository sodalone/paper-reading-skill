#!/usr/bin/env python3
import argparse
from pathlib import Path

from common import get_workspace, read_json


SKELETON = """# 论文阅读报告

## 0. 基本信息
- 论文标题：
- 作者：
- 机构：
- 来源（会议 / arXiv / 期刊）：
- 年份：
- 原始输入链接：{input_url}
- 最终使用的 arXiv 版本化 ID：{paper_id_with_version}
- 原论文 arXiv 链接：{arxiv_abs_url}
- 幻觉翻译链接（hjfy）：{hjfy_url}
- Cool Papers 链接：{papers_cool_url}
- 论文研究方向：
- 本文一句话概括：

## 1. 论文核心观点与主张的系统梳理
### 1.1 研究背景与动机

### 1.2 问题设定

<!-- 若 cache/images_manifest.json 中存在任务设定图或整体流程图，
必须从 manifest 选择真实 saved_path 插入到本小节附近。
图后解释该图与问题设定的关系；不要把固定示例路径当成实际路径。 -->

### 1.3 核心观点（Claims）的逐条梳理

### 1.4 创新性与贡献边界

## 2. 关键论据、理论基础与数学方法的深度解析
### 2.1 理论基础与学术渊源

### 2.2 问题形式化与建模选择

### 2.3 核心推导与算法构造

<!-- 必须先读取 cache/images_manifest.json。
若存在 method_overview / model_architecture / module_detail 图，
必须从 manifest 选择真实 saved_path 插入到本小节附近。
图后必须解释：模块关系、输入输出、支撑哪条核心主张，以及不看图会漏掉什么机制。
不要只用文字描述模型结构，也不要把关键方法图留到文末。 -->

<!-- 关键公式解释应就地插入：
在 2.2 / 2.3 / 2.4 或 3.x 的相关位置，公式首次成为核心论点时，紧跟解释。

公式写法建议：
1. 能单行写完的 display 公式，优先单行：
   $$ E = mc^2 $$
2. 若必须多行，使用 aligned：
   $$
   \\begin{{aligned}}
   ...
   \\end{{aligned}}
   $$
3. 不要在公式块中使用 \tag{{}}
4. 不要在 display 公式中裸写行首 +
5. 若渲染环境不确定，补一行纯文本伪公式
-->

### 2.4 理论结论的适用范围

## 3. 实验设计与实验结果的充分性分析
### 3.1 实验目标与论文主张的对应关系

### 3.2 实验设置合理性

### 3.3 实验结果的解释力度

| 设置 / 数据集 | 方法 | 指标 | 数值 | 备注 |
|---|---|---|---|---|
| 待补充 | 待补充 | 待补充 | 待补充 | 待补充 |

<!-- 若正文在这里讨论主 benchmark、扩展指标、scaling law 或 additional experiments，
则对应表格必须直接插入到本小节相关段落附近，而不是只放附录。 -->

<!-- 若 cache/images_manifest.json 中存在主结果可视化、benchmark 对比、性能趋势或定性对比图，
必须从 manifest 选择真实 saved_path 插入到本小节附近，而不是集中堆放。 -->

### 3.4 潜在未讨论因素

| 消融项 | 变化设置 | 数据集 / 设置 | 指标 | 原始数值 | 变化后数值 | 结论 |
|---|---|---|---|---|---|---|
| 待补充 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 |

<!-- 若这里讨论消融、失败案例、边界条件或附加泛化实验，则对应表格必须直接出现在本小节附近。 -->

<!-- 若 cache/images_manifest.json 中存在失败案例图、消融图、边界条件图或附加泛化图，
必须从 manifest 选择真实 saved_path 插入到本小节对应分析段落附近。 -->

## 4. 与当前领域主流共识及反对观点的关系
### 4.1 与主流观点的一致性

### 4.2 与反对或竞争观点的分歧

### 4.3 论文在学术版图中的定位

### 4.4 文献检索说明
- 检索范围：
- 检索结论可信度：

### 4.5 相关论文补充表

| 序号 | 论文标题 | 作者 / 年份 | 来源 | 与原论文关系 | 一句话概述 |
|---|---|---|---|---|---|
| 1 |  |  |  |  |  |

## 5. 对论文理论体系的严肃反驳与系统性质疑
### 5.1 核心假设层面的质疑

### 5.2 数学推导与理论主张的边界

### 5.3 工程实现与实际适用性

### 5.4 整体理论体系的稳健性

## 6. 最终结论
### 6.1 论文价值总结

### 6.2 一句话总评

### 6.3 综合评分（10 分制）
- 创新性：
- 技术严谨性：
- 实验说服力：
- 工程价值：
- 总体评分：

### 6.4 最关键的三条优点
1.
2.
3.

### 6.5 最关键的三条问题
1.
2.
3.

## 附录 A：关键实验表与消融实验表
<!-- 附录 A 只做补充，不应替代正文中对应位置的关键表格。 -->
### A.1 主 benchmark 对比表
| 方法 | 设置 / 传感器 | 指标1 | 指标2 | 指标3 | 核心结论 |
|---|---|---|---|---|---|
| 待补充 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 |

### A.2 扩展指标 / 扩展 benchmark 表
| 方法 | 扩展指标1 | 扩展指标2 | 扩展指标3 | 结论 |
|---|---|---|---|---|
| 待补充 | 待补充 | 待补充 | 待补充 | 待补充 |

### A.3 数据规模 / scaling law / 泛化表
| 设置 | 数据规模 / 迁移设置 | 指标1 | 指标2 | 关键观察 |
|---|---|---|---|---|
| 待补充 | 待补充 | 待补充 | 待补充 | 待补充 |

### A.4 关键消融实验表
| 消融项 | 变化设置 | 指标 | 原始数值 | 变化后数值 | 结论 |
|---|---|---|---|---|---|
| 待补充 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 |

### A.5 其他支撑正文结论的关键表
| 表格主题 | 关键列 | 结论 |
|---|---|---|
| 待补充 | 待补充 | 待补充 |

## 附录 B：本报告引用的关键外部文献
1.
2.
3.
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    workspace, ids = get_workspace(root, args.input)
    metadata = read_json(workspace / "metadata.json")
    report_path = workspace / f"{ids['arxiv_id']}_阅读报告.md"

    report_path.write_text(
        SKELETON.format(
            input_url=metadata["input"],
            paper_id_with_version=metadata["paper_id_with_version"],
            arxiv_abs_url=metadata["arxiv_abs_url"],
            hjfy_url=metadata["hjfy_url"],
            papers_cool_url=metadata["papers_cool_url"],
        ),
        encoding="utf-8",
    )
    print("Report skeleton created:", report_path)


if __name__ == "__main__":
    main()
