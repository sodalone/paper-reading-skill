# inline-table-and-formula-template.md

## 主结果表模板（应直接放入 3.3 或附录 A）
| 设置 / 数据集 | 方法 | 指标 | 数值 | 备注 |
|---|---|---|---|---|
|  |  |  |  |  |

## 消融表模板（应直接放入 3.4 或附录 A）
| 消融项 | 变化设置 | 数据集 / 设置 | 指标 | 原始数值 | 变化后数值 | 结论 |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## 相关论文表模板（应直接放入 4.5）
| 序号 | 论文标题 | 作者 / 年份 | 来源 | 与原论文关系 | 一句话概述 |
|---|---|---|---|---|---|
| 1 |  |  |  |  |  |

## 就地公式解释模板（应直接放在公式首次关键出现的位置附近，而不是集中堆在一节）
- 公式编号：
- 公式原文：
- 在论文中的位置：
- 这条公式要解决什么问题：
- 符号说明：
- 自然语言翻译：
- 分项拆解：
- 与上一条公式的关系：
- 与下一条公式的关系：
- 训练 / 推理中的作用：
- 代码中的典型对应：
- 极简数值例子：
- 若删去该项会怎样：
- 是否依赖强假设：
- 阅读难点提醒：


## 附加实验 / 泛化 / scaling law 表模板（应直接放入 3.3、3.4 或附录 A）
| 实验类型 | 设置 | 指标1 | 指标2 | 关键结论 |
|---|---|---|---|---|
|  |  |  |  |  |


## 数学公式格式示例
行内公式示例：
`损失函数写成 $\mathcal{L}_{total} = \mathcal{L}_{action} + \alpha \mathcal{L}_{wm}$`

跨行公式示例：
```markdown
$$
\mathcal{L}_{total} = \mathcal{L}_{action} + \alpha \mathcal{L}_{wm}
$$
```


## 公式编号推荐写法
推荐：
```markdown
式 (7) 定义了总奖励函数：

$$
R = \lambda_{\text{traj}} R_{\text{traj}}
 + \lambda_{\text{fmt}} R_{\text{fmt}}
 + \lambda_{\text{goal}} R_{\text{goal}}
$$
```

不推荐：
```markdown
$$
R = \lambda_{\text{traj}} R_{\text{traj}}
 + \lambda_{\text{fmt}} R_{\text{fmt}}
 + \lambda_{\text{goal}} R_{\text{goal}}
\tag{7}
$$
```


## 兼容性更高的公式写法

### 推荐：单行 display 公式
```markdown
式 (7) 定义总奖励函数：

$$ R = \lambda_{\text{traj}} R_{\text{traj}} + \lambda_{\text{fmt}} R_{\text{fmt}} + \lambda_{\text{goal}} R_{\text{goal}} $$
```

### 推荐：多行时使用 aligned
```markdown
式 (7) 定义总奖励函数：

$$
\begin{aligned}
R &= \lambda_{\text{traj}} R_{\text{traj}} \\
&\quad + \lambda_{\text{fmt}} R_{\text{fmt}} \\
&\quad + \lambda_{\text{goal}} R_{\text{goal}}
\end{aligned}
$$
```

### 兼容性降级写法
```text
式 (7)：
R = λ_traj * R_traj + λ_fmt * R_fmt + λ_goal * R_goal
```


## 图片定位建议
当有源码包时，图片定位优先依据：

1. `\includegraphics{文件名}`
2. figure 的 caption
3. figure 所在的 section / subsection
4. 正文首次引用该 figure 的位置

推荐在 `images_manifest.json` 中记录：
- 原始文件名
- 转换后文件名
- caption
- label
- section_hint
- first_reference_hint
