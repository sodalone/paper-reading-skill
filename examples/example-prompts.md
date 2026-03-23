# example-prompts.md

使用 $paper-reviewer-final-v4 阅读这篇论文：
https://arxiv.org/abs/2510.12796

要求：
1. 先运行 skill 自带 scripts
2. 输出到对应 arxiv_id 文件夹
3. 主报告保存为 {arxiv_id}_阅读报告.md
4. 最终只交付一份自包含的 Markdown 报告
5. 相关论文表、主结果表、消融表都要直接写入主报告
6. 图片必须按内容插入恰当位置，不能集中堆在一个章节
7. 不要在最终报告中展示 hjfy / papers.cool 的状态说明行
8. 重点加强公式理解：对关键公式输出公式理解卡，并尽量给 toy example

9. 正文里提到的关键实验表不要漏，主结果表、scaling law 表、关键消融表、附加实验表都要尽量转写进报告

10. 公式解释不要集中堆在一节里，要像图片一样，插入到对应方法/理论/实验位置附近
