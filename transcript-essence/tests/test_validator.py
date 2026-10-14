import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('validator', Path(__file__).parents[1]/'scripts/validate_note.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

BASE = '''# 笔记

## 原文

原文内容。

## 精华笔记

> [!abstract] 一句话提炼
> 内容概括。

> [!info] 阅读边界
> 应用为整理者延伸。

### 1. 内容主线
内容。
### 2. 核心认知
#### ① 一个观点
**原文要点：** 内容。
**理解：** 内容。
**应用：** 内容。
**边界：** 内容。
### 3. 关键区分
暂无。
### 4. 自查问题
- 一个问题？
### 5. 原文摘录
> 原文内容。
### 6. 一句提醒
**提醒。**
'''

class ValidatorTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(module.validate(BASE), [])
    def test_nested_source_h1(self):
        self.assertTrue(module.validate(BASE.replace('原文内容。', '# 破坏折叠', 1)))
    def test_code_heading_untouched(self):
        self.assertEqual(module.validate(BASE.replace('原文内容。', '```python\n# 注释\nprint(1)\n```', 1)), [])
    def test_unclosed_fence(self):
        self.assertTrue(module.validate(BASE+'\n```python'))
    def test_long_title(self):
        self.assertTrue(module.validate(BASE.replace('# 笔记', '# '+'长'*17)))
    def test_missing_section(self):
        self.assertTrue(module.validate(BASE.replace('### 3. 关键区分','### 3. 别的标题')))
    def test_missing_field(self):
        self.assertTrue(module.validate(BASE.replace('**边界：**','**条件：**')))
    def test_checklist(self):
        self.assertTrue(module.validate(BASE.replace('- 一个问题？','- [ ] 做一件事')))
    def test_mermaid(self):
        self.assertTrue(module.validate(BASE+'\n```mermaid\ngraph TD\n```'))
    def test_heading_jump(self):
        self.assertTrue(module.validate(BASE.replace('#### ①','##### ①')))
    def test_indented_h1(self):
        self.assertTrue(module.validate(BASE.replace('原文内容。', '   # 逃出', 1)))
    def test_setext(self):
        self.assertTrue(module.validate(BASE.replace('原文内容。', '原标题\n====', 1)))
    def test_h5(self):
        self.assertTrue(module.validate(BASE+'\n##### 多余标题'))
    def test_extra_callout(self):
        self.assertTrue(module.validate(BASE+'\n> [!warning] 多余'))
    def test_fake_callout(self):
        self.assertTrue(module.validate(BASE.replace('> [!abstract]', '[!abstract]')))
    def test_tilde_mermaid(self):
        self.assertTrue(module.validate(BASE+'\n~~~mermaid\ngraph TD\n~~~'))
    def test_emphasis_setext(self):
        self.assertTrue(module.validate(BASE.replace('原文内容。', '*隐藏标题*\n====', 1)))
    def test_callouts_in_code(self):
        self.assertTrue(module.validate(BASE.replace('> [!abstract]', '```text\n> [!abstract]').replace('> 应用为整理者延伸。','> 应用为整理者延伸。\n```')))
    def test_merged_callouts(self):
        self.assertTrue(module.validate(BASE.replace('> 内容概括。\n\n> [!info]', '> 内容概括。\n> [!info]')))
    def test_zero_points(self):
        start=BASE.index('#### ①'); end=BASE.index('### 3.')
        text=BASE[:start]+'材料有限：没有足够依据提炼独立观点。\n'+BASE[end:]
        self.assertEqual(module.validate(text), [])
    def test_fields_in_code(self):
        text=BASE.replace('**原文要点：**','```text\n**原文要点：**').replace('**边界：** 内容。','**边界：** 内容。\n```')
        self.assertTrue(module.validate(text))
    def test_tilde_fence(self):
        self.assertEqual(module.validate(BASE.replace('原文内容。', '~~~python\n# 注释\n~~~', 1)), [])

if __name__ == '__main__':
    unittest.main()
