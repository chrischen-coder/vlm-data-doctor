# 数据检查解决哪些问题

适用于本地静态图片和文本 SFT。下面是可以复现的使用场景，不是客户案例。

## 1. 标注导出成功，数据却不能直接训练

合并多批标注或搬迁图片目录后，JSON 仍能解析，但图片可能缺失、损坏，或者 `<image>` 与路径数量不一致。
这时需要找到具体样本，而不只是知道预处理失败了。

检查器会完整解码图片，并把结构问题定位到行和字段。仓库故障样例的实际输出包括：

```text
ERROR image_token_mismatch train:1 images: Found 0 <image> markers and 1 image paths; align them.
ERROR missing_image train:2 images[0]: Reference an existing regular image file beneath the image root.
```

按记录补齐图片、修正占位符，再运行检查。若这条样本本来就是纯文本，应移除错误的图片引用。
不要为通过检查盲目添加 `<image>`。

```bash
vlm-data-doctor check examples/broken/train.jsonl --eval examples/broken/validation.jsonl --image-root examples/clean
```

这个命令返回 `1`，完整结果还有两条跨集合重叠发现。
[LlamaFactory 历史 issue #6135](https://github.com/hiyouga/LlamaFactory/issues/6135)记录过占位符数量报错。
该问题已关闭；这里引用的是故障类型，不是声称当前上游仍有这个缺陷。

## 2. 样本没有重复，评测却用了见过的文档

文档问答会从一份 PDF 生成多页图片、多条问答。按行随机拆分时，不同页面可能进入不同集合。
即使样本和图片都不重复，也不符合“评测未见过文档”的实验设计。

[可运行样例](../examples/document-split/README.zh-CN.md)保留 `document_id`，得到以下结果：

| 输入与配置 | 结果 | 原因 |
| --- | --- | --- |
| 手册 A 第 1 页训练、第 2 页评测；默认检查 | 0 错误、0 警告 | 对话和图片字节不同 |
| 同样的数据，增加 `--group-key document_id` | 1 个 `split_group_overlap` 错误 | 两条记录来自同一手册 |
| 训练用 A，评测改用 B；保留分组检查 | 0 错误、0 警告 | 样例中的文档组不再交叉 |

需要按源文档拆分，再从各自文档生成页面和问答；不要只改 ID 来消除告警。
如果研究的是同一文档上的新问题，允许共享文档可能是合理的。拆分单位由实验目标决定。
当前工具只核对给定的组 ID，不识别错误的来源标注，也不检测裁剪、重新压缩或语义近重复。

## 3. 模型换了，数据也改了，分数变化归因不清

一次实验修了答案、替换图片，另一次只更换模型，但两次数据都叫 `train.jsonl`。
只记文件名和样本数，不能确认比较时是否用了相同输入。

JSON 报告保存数据文件哈希、有效图片清单哈希、检查版本和配置。把它与数据快照、训练配置一起归档：

```bash
vlm-data-doctor check data/train.jsonl --eval data/test.jsonl --image-root data --group-key document_id --format json --output audit.json
```

比较 `provenance.dataset_sha256` 和 `provenance.decoded_image_inventory_sha256`，可以核对被记录的输入是否变化。
哈希不能解释改了哪条记录，也不能恢复旧数据；缺失和损坏图片的字节不在有效图片清单中。

## 研究时还缺哪些证据

当前解决的是结构排错、已定义的拆分检查和输入记录。要研究“清洗是否提升模型”，还需要：

- **独立问题标注：**规则开发集和测试集分开，统计真实数据上的漏检、误报和误删。
- **有效对照：**比较原始数据、基础规则、选定的已有方法和新方法；固定模型、测试集与训练预算，报告数据量和任务分布变化。
- **下游实验：**保留多随机种子的训练日志、评测结果和失败案例，同时记录数据处理开销。

[Lee 等，ACL 2022](https://aclanthology.org/2022.acl-long.577/)研究了文本语言模型的数据去重与训练／测试重叠。
这提供了研究动机，不能作为本工具对 VLM 有效的证据。
当前[合成回归与 CPU 测量](benchmarks.md)也不回答模型提升了多少。

接入真实训练流程后，值得记录的是实际发现了哪些问题、修复用了多久、误报了什么。
节省 GPU 时间和提高模型指标，都需要单独测量。

[返回 README](../README.zh-CN.md) · [规则与边界](checks.md) · [后续工作](roadmap.md)
