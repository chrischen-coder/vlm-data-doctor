# 不同页面，同一份文档

[English](README.md)

这个样例演示：样本和图片不重复，仍可能不符合按文档隔离的评测要求。
所有页面均由 `examples/generate.py` 生成，用来展示检查规则，不是模型评测集。

| 文件 | 内容 | `document_id` |
| --- | --- | --- |
| `train.jsonl` | 手册 A 第 1 页，问负责团队 | `manual-a` |
| `validation.jsonl` | 手册 A 第 2 页，问复核周期 | `manual-a` |
| `validation-disjoint.jsonl` | 手册 B 第 1 页，问负责团队 | `manual-b` |

在仓库根目录安装工具后，依次运行：

## 1. 默认检查通过

```bash
vlm-data-doctor check examples/document-split/train.jsonl --eval examples/document-split/validation.jsonl
```

结果为 `Errors: 0 | Warnings: 0`，退出码 `0`。两个页面的图片字节、问题和答案不同。

## 2. 按文档检查，发现来源交叉

```bash
vlm-data-doctor check examples/document-split/train.jsonl --eval examples/document-split/validation.jsonl --group-key document_id
```

```text
VLM Data Doctor
Records: train=1, eval=1
Unique image files: 2
Errors: 1 | Warnings: 0
ERROR split_group_overlap eval:1 document_id: The selected group also appears at train:1; use a group-disjoint split.
```

退出码 `1` 是这个步骤的预期结果。若评测目标是新文档上的问答，A 的两页应放在同一集合。

## 3. 改用独立文档评测

```bash
vlm-data-doctor check examples/document-split/train.jsonl --eval examples/document-split/validation-disjoint.jsonl --group-key document_id --strict
```

结果为 `Errors: 0 | Warnings: 0`，退出码 `0`。这次评测来自手册 B。
这里只替换了演示用评测文件；真实数据应在生成页面和问答之前，先按源文档分配集合。
不要通过修改 `document_id` 掩盖交叉。

也可以在第 2 步命令后追加 `--format html --output document-split.html`，打开报告查看定位。
输出文件必须尚不存在；命令仍返回 `1`。

## 这个结果能说明什么

分组检查验证的是数据提供的 `document_id`，不会识别文档内容或核实来源。
如果任务允许在见过的文档上回答新问题，可以采用其他拆分策略。
本样例不证明重新拆分后模型分数会如何变化。

[返回项目](../../README.zh-CN.md) · [使用场景](../../docs/impact.zh-CN.md)
