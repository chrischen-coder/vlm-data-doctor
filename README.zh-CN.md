# VLM Data Doctor

**在启动多模态训练前，检查图文数据是否存在明显问题。**

[English](README.md) · [规则说明](docs/checks.md) · [选题调研与后续路线](docs/project-research.zh-CN.md)

这是一个在本地运行的小型 Python 工具，支持常见的 ShareGPT / messages 图文 SFT
数据格式。它检查对话结构、图片占位符、图片文件、重复样本和训练／评测集重叠。
运行时不需要 GPU、模型、API Key 或网络连接，也不会修改原始数据。

当前版本为 **v0.1.0，Alpha**。数据检查通过不等于模型训练、答案质量或评测方法一定正确。
目前没有模型训练结果或节省 GPU 费用的实测结论。

## 快速开始

需要 Python 3.10 或更新版本。本项目尚未宣称发布至 PyPI，请从仓库安装。

```bash
git clone https://github.com/chrischen-coder/vlm-data-doctor.git
cd vlm-data-doctor
python -m venv .venv
```

macOS/Linux 执行 `source .venv/bin/activate`，Windows PowerShell 执行
`.venv\Scripts\Activate.ps1`，然后运行：

```bash
python -m pip install .
vlm-data-doctor check examples/clean/train.jsonl --eval examples/clean/validation.jsonl --strict
```

预期结果：2 条训练样本、1 条评测样本、3 个图片文件，0 个错误、0 个警告。

体验故意设置的问题：

```bash
vlm-data-doctor check examples/broken/train.jsonl --eval examples/broken/validation.jsonl --image-root examples/clean
```

预期发现占位符数量不匹配、图片缺失和跨集合相同样本，返回退出码 1。
样例仅用于验证工具，不代表真实业务数据，也不是模型准确率基准。

## 可以检查什么

| 检查项 | 用途 |
| --- | --- |
| JSON/JSONL、字段类型 | 提前发现无法解析的数据 |
| human/gpt 或 user/assistant 对话 | 检查成对 SFT 对话、角色顺序和空答案 |
| `<image>` 与 images 数量 | 发现常见的图文对齐错误 |
| 图片存在性、解码、大小限制 | 发现缺失、损坏和超限图片 |
| 重复 ID、相同样本 | 提醒检查重复数据 |
| 训练／评测集交叉检查 | 发现完全相同的样本、相同输入和相同图片字节 |
| JSON、Markdown 报告和退出码 | 接入数据准备流程或 CI |

`images` 使用相对于数据文件目录的路径；可以通过 `--image-root` 指定公共目录，
或通过 `--eval-image-root` 单独指定评测图片目录。拒绝绝对路径、URL 和越出根目录的路径。

```bash
vlm-data-doctor check data/train.jsonl --eval data/test.jsonl --image-root data --strict --format json
vlm-data-doctor check data/train.jsonl --format markdown --output report.md
```

`--output` 只创建新报告，已有文件不会被覆盖。父目录必须已存在。
退出码：0 = 通过，1 = 存在数据错误（严格模式也包含警告），2 = 参数、文件读写或编码问题。
JSONL 行号是文件的实际行号；JSON 数组行号是从 1 开始的元素位置。

## 边界

目前仅支持本地静态图片和文本对话，不支持视频、音频、工具调用、DPO/RL、URL 图片、
结构化 content 数组或任意字段映射。还需单独验证模型模板、tokenizer、截断和真实训练行为。

图片通过 SHA-256 字节哈希比较，改文件名不会绕过检查，但重新压缩和裁剪可能绕过。
相同图片出现在不同集合只给警告，因为不同任务的拆分要求不同；完整样本重叠则报错。
相同样本比较保留角色顺序、大小写和内部空格，只做 NFC、换行和首尾空白规范化。

JSONL 逐行读取，但哈希索引和问题列表仍占内存；JSON 数组会整体读入。
默认图片上限为 4000 万像素，动画图片不支持。详见 [完整说明](README.md#scope-and-limitations)。

## 为什么做这个项目

[LlamaFactory 数据文档](https://github.com/hiyouga/LlamaFactory/blob/main/data/README.md)
明确要求图片数量与占位符数量对应。历史问题
[#6135](https://github.com/hiyouga/LlamaFactory/issues/6135) 展示了这类数据问题；该问题已关闭，
这里不将它描述为当前未解决的框架缺陷。

[Data-Juicer](https://github.com/datajuicer/data-juicer) 已有广泛的数据处理、清洗和去重能力。
本工具选择小范围切入：易安装、本地预检、逐行定位和拆分交叉检查。这是产品范围选择，
不宣称功能独占、算法创新或替代现有框架。

欢迎使用人工构造的最小样例反馈问题。请勿提交企业内部文档、客户日志或凭证。
代码和本项目生成的演示数据使用 MIT 许可证。
