#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

import validate_report as validate_report_module
import validate_report_text as validate_report_text_module
from validate_report import validate_report


BASE_REPORT = """# 论文阅读报告：测试论文

## 0. 三分钟读懂
### 0.1 论文解决什么问题
这是一个具体且重要的问题，现有方法在组合任务中容易失败。本文试图用统一的表示和训练流程解决它，并把复杂任务拆成可观察的决策步骤。
### 0.2 核心办法是什么
方法先编码当前观测，再维护任务状态，最后预测下一步动作。直观上，它像一个会定期检查清单的导航员，而不是只根据当前画面反应。
### 0.3 最重要的结果
论文方法在主指标上高于最强可比基线，但绝对成功率仍然有限，复杂任务上的差距最大。
### 0.4 最终判断
方法提供了有价值的统一基线，主要证据来自主结果和逐阶段消融；最大缺口是缺少真实部署的规模化量化结果。
### 0.5 阅读路线
- 只判断价值读本章和第 4 章；学习方法继续读第 1–2 章；审查证据读第 3 章。
### 0.6 论文与链接
- 原始输入链接：https://arxiv.org/abs/2500.00001
- 最终使用的 arXiv 版本化 ID：2500.00001v1
- 原论文 arXiv 链接：https://arxiv.org/abs/2500.00001v1
- 幻觉翻译链接（hjfy）：https://hjfy.top/arxiv/2500.00001v1
- Cool Papers 链接：https://papers.cool/arxiv/2500.00001v1

## 1. 先建立直觉
### 1.1 用一个具体例子说明任务
具体例子。
### 1.2 一张图讲清方法全景
![方法图](images/figure_01.png)
### 1.3 必要术语
| 术语 | 一句话解释 | 为什么必须知道 |
|---|---|---|
| 状态 | 当前任务进度 | 决定下一步动作 |
### 1.4 与最接近方法的本质区别
区别说明。

## 2. 方法如何工作
### 2.1 输入、输出与核心流程
流程说明。
### 2.2 核心机制
机制说明。
### 2.3 决定性公式（按需）
本报告不需要正文公式。
### 2.4 训练、推理与实现边界
边界说明。

## 3. 证据是否成立
### 3.1 Claim—Evidence—Verdict 总表
| Claim | 原文位置 | 作者证据 | 支撑强度 | 最大缺口 | 本报告结论 |
|---|---|---|---|---|---|
| C1 | Sec. 4 | Table 1 | 部分支撑 | 缺方差 | 支持有效性 |
| C2 | Sec. 5 | Table 2 | 间接支撑 | 缺直接消融 | 不能归因 |
### 3.2 主结果
| 方法 | 主指标 | 结论 |
|---|---:|---|
| 本文 | 10 | 更高 |
### 3.3 关键消融与补充实验
消融说明。
### 3.4 证据没有覆盖什么
缺口说明。

## 4. 最终判断与适用边界
### 4.1 真正的新意
新意说明。
### 4.2 最重要的三个问题
1. 问题一
2. 问题二
3. 问题三
### 4.3 学术位置与竞争路线
位置说明。
### 4.4 是否值得精读或复现
- 阅读建议：值得浏览
- 复现建议：先做最小实验

## 5. 工程与复现（按需）
### 5.1 复现所需资产
资产说明。
### 5.2 论文与代码的一致性
一致性说明。
### 5.3 成本、风险与最小复现路径
路径说明。

## 附录 A：完整实验表
完整表格。
## 附录 B：数学与实现细节
补充细节。
## 附录 C：本报告实际使用的外部文献
1. 测试文献。
## 附录 D：证据定位
| Claim | 位置 |
|---|---|
| C1 | Sec. 4 |
"""


class ValidateReportTests(unittest.TestCase):
    def test_resolve_report_accepts_direct_file_under_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "2506.09839_阅读报告.md"
            report.write_text("test", encoding="utf-8")
            self.assertEqual(
                validate_report_module.resolve_report_path(root, report.name),
                report.resolve(),
            )

    def test_counts_bracketed_display_math_and_claim_suffix(self) -> None:
        text = BASE_REPORT.replace("| C1 |", "| C1：主张 |")
        text = text.replace("本报告不需要正文公式。", "\\[x = 1\\]")
        errors, _, metrics = validate_report_module.validate_report(text, final=True)
        self.assertEqual(metrics["main_formula_count"], 1)
        self.assertFalse(any("至少应包含两条" in error for error in errors))

    def test_text_validator_rejects_ambiguous_workspaces(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for name in ("2506.09839_a", "2506.09839_b"):
                workspace = root / name
                workspace.mkdir()
                (workspace / "2506.09839_阅读报告.md").write_text("test", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                validate_report_text_module.build_report_path(root, "2506.09839")
            expected = root / "2506.09839_b" / "2506.09839_阅读报告.md"
            self.assertEqual(
                validate_report_text_module.build_report_path(root, "2506.09839", "2506.09839_b"),
                expected,
            )

    def test_text_validator_scans_bracketed_display_math(self) -> None:
        issues = validate_report_text_module.collect_math_issues("\\[x = 1 \\tag{1}\\]")
        self.assertTrue(any("tag" in issue for issue in issues))

    def test_readable_final_report_passes(self):
        errors, _, metrics = validate_report(BASE_REPORT, final=True)
        self.assertEqual(errors, [])
        self.assertGreaterEqual(metrics["summary_chars"], 300)

    def test_missing_summary_fails(self):
        report = BASE_REPORT.replace("## 0. 三分钟读懂", "## 0. 摘要")
        errors, _, _ = validate_report(report, final=True)
        self.assertTrue(any("三分钟读懂" in error for error in errors))

    def test_named_markdown_links_do_not_satisfy_fixed_link_contract(self):
        report = BASE_REPORT.replace(
            "原论文 arXiv 链接：https://arxiv.org/abs/2500.00001v1",
            "[arXiv 原文](https://arxiv.org/abs/2500.00001v1)",
        )
        errors, _, _ = validate_report(report, final=True)
        self.assertTrue(any("固定格式" in error for error in errors))

    def test_link_section_rejects_extra_project_page(self):
        report = BASE_REPORT.replace(
            "- 幻觉翻译链接（hjfy）：",
            "- 项目页：https://example.com\n- 幻觉翻译链接（hjfy）：",
        )
        errors, _, _ = validate_report(report, final=True)
        self.assertTrue(any("只能包含五行" in error for error in errors))

    def test_internal_formula_label_fails(self):
        errors, _, _ = validate_report(BASE_REPORT + "\nA级公式 1\n", final=True)
        self.assertTrue(any("内部工作标签" in error for error in errors))

    def test_duplicate_long_paragraph_fails(self):
        paragraph = "这个重复段落用于验证去重规则。" * 12
        report = BASE_REPORT + f"\n{paragraph}\n\n{paragraph}\n"
        errors, _, _ = validate_report(report, final=True)
        self.assertTrue(any("重复段落" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
