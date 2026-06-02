# storage-analyzer

macOS / Windows 只读存储分析 skill。用于扫描电脑磁盘占用，识别大目录、缓存、下载内容、开发缓存、应用数据等，并生成交互式 HTML 存储分析报告。

来源：

- GitHub: https://github.com/KKKKhazix/khazix-skills/tree/main/storage-analyzer
- 同步时间: 2026-06-02
- 源仓库 HEAD: f78992d0d9ea73f7844e2e27acdd5f5c5e3a13aa

## 安装位置

当前已同步到两个位置：

- Codex skills: `/Users/edy/.codex/skills/storage-analyzer`
- 本地技能库: `/Users/edy/Desktop/grzzz/skills/my-skills/storage-analyzer`

新增 skill 后，需要重启 Codex 才能在后续对话中自动识别和触发。

## 适用场景

当用户提到以下需求时使用：

- 存储分析
- 磁盘满了
- C 盘 / 硬盘满了
- 空间不够
- 清理磁盘
- 哪些东西占空间
- 帮我看看电脑存储
- 清缓存

注意：如果用户说的是运行内存 RAM，例如“哪个进程吃内存”“内存占用高”，不属于这个 skill。

## 文件结构

```text
storage-analyzer/
├── SKILL.md
├── README.md
├── assets/
│   └── report_template.html
├── references/
│   ├── macos.md
│   └── windows.md
└── scripts/
    ├── build_report.py
    ├── scan.py
    └── server.py
```

## 基本流程

1. 扫描磁盘，生成只读 JSON 数据。
2. 由 agent 根据扫描结果分析占用大户。
3. 将可处理项分为三类：
   - 绿色：可自动清理
   - 黄色：需要人工判断
   - 红色：谨慎清理，不建议直接手删
4. 生成交互式 HTML 报告。
5. 默认通过本地服务打开报告，支持在网页中对允许项执行移到废纸篓或直接删除。

## 命令参考

在 skill 目录下运行：

```bash
python3 scripts/scan.py > /tmp/storage_scan.json
```

生成报告服务：

```bash
python3 scripts/server.py /tmp/storage_analysis.json
```

如果只需要静态 HTML 文件：

```bash
python3 scripts/build_report.py /tmp/storage_analysis.json ~/Desktop/storage-report.html
```

## 安全原则

- 扫描阶段必须只读。
- 不允许在扫描阶段执行 `rm`、`mv`、`rmdir`、清空废纸篓、改权限等写操作。
- 报告中删除能力必须经过白名单和用户确认。
- 黄色项目优先打开文件管理器让用户自行判断。
- 红色项目只给卸载或处理建议，不提供直接删除按钮。

## 平台说明

- macOS：完整实现并有实测说明。
- Windows：脚本支持 Windows 路径、盘符和回收站逻辑，但原 skill 说明中标注“未在真实 Windows 上实测”，首次使用时需要谨慎核对。

