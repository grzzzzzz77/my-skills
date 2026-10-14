# 逐字稿精华

把分享、口播、教程、访谈、演讲、讨论、故事和混合素材转成统一风格的 Markdown／Obsidian 个人笔记，不限制为对话形式。

## 使用

示例请求：

> 提炼这份逐字稿的精华，保留上方原文，在下方按固定风格整理到我的笔记。标题短一些，不要关系图或三件事清单。

输入：完整逐字稿或可读取的转写文件，目标笔记路径；可选来源与作者信息。只有视频而无转写时，应先获取可读转写，不凭简介编总结。

## 固定结构

一个短标题 → 原文 → 精华笔记。精华始终依次为：

1. 内容主线
2. 核心认知
3. 关键区分
4. 自查问题
5. 原文摘录
6. 一句提醒

核心认知统一为“原文要点／理解／应用／边界”，点数取决于内容。不足以提炼时明确说明，不凑观点。默认无关系图、Mermaid、勾选任务清单。

## 文件

- [SKILL.md](SKILL.md)：触发条件、完整步骤与边界。
- [template.md](template.md)：统一笔记骨架。
- [evaluation.md](evaluation.md)：六维100分量表与多轮方法。
- [evaluation-report.md](evaluation-report.md)：本次创作的实测评审记录。
- [scripts/validate_note.py](scripts/validate_note.py)：标准库结构校验器。
- [tests/test_validator.py](tests/test_validator.py)：校验器回归。
- [tests/share.md](tests/share.md)、[tests/tutorial.md](tests/tutorial.md)、[tests/discussion.md](tests/discussion.md)、[tests/mixed.md](tests/mixed.md)、[tests/sparse.md](tests/sparse.md)：五类合成样例，仅为测试数据，不是真实来源。

```bash
python3 scripts/validate_note.py /path/to/note.md
python3 tests/test_validator.py
```

脚本检验默认模板结构，不验证语义忠实性、事实真伪或客户端界面；修改已有用户笔记时保留用户已确认内容，不强制为通过脚本重写一切。Obsidian 折叠默认是否收起由客户端决定，本技能不改客户端配置。
