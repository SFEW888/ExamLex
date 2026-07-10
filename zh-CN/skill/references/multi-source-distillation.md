# 多源蒸馏方法论

> 五种蒸馏路径全部内置于 examlex。无需外部 Skill 或工具（视频下载需要 yt-dlp + ffmpeg）。Agent 编排五阶段管线：提取 → 蒸馏 → 校验 → 评估 → 提交。

## 支持的来源类型

| source_type | 典型输入 | distillation_method | 管线 |
|-------------|---------|---------------------|------|
| `text` | Markdown/纯文本策略笔记 | `direct` | 提取(文本) → 蒸馏 → 校验 → 评估 → 提交 |
| `book` | 备考书籍 PDF/EPUB/DOCX | `book` | 提取(书籍) → RIA-TV++蒸馏 → 校验 → 评估 → 提交 |
| `video` | B站/YouTube 链接或字幕 | `video` | 提取(yt-dlp+ASR) → RIA-TV++蒸馏 → 校验 → 评估 → 提交 |
| `person` | 教师/专家姓名 | `person` | 提取(跳过) → 认知提取蒸馏 → 校验 → 评估 → 提交 |
| `conversation` | 对话笔记 | `manual` | 提取(文本) → 蒸馏 → 校验 → 评估 → 提交 |

## 管线阶段

### 阶段 1: 提取
```bash
examlex extract --input <url|file|name> [--type auto|video|book|text|person]
```
- **video**: yt-dlp下载 → ffmpeg音频提取 → SenseVoiceSmall/whisper ASR → transcript.txt
- **book**: 多格式解析器 → full_text.txt + 章节结构 + 术语表
- **text**: 读取 + 标准化 → full_text.txt
- **person**: 无需提取，直接进入蒸馏阶段

### 阶段 2: 蒸馏（Agent 推理）
- **book/video**: 遵循 `prompts/ria.py` — RIA-TV++ 六阶段管线
- **person**: 遵循 `prompts/cognitive.py` — 五层认知提取

输出: `distilled.json`

### 阶段 3: 校验
```bash
examlex validate --artifacts-dir <path>
```
- 格式检查: 步骤编号、Schema合规、RIA++完整性
- Darwin 结构评分: 6维度59分

### 阶段 4: 评估（Agent 推理）
效果评分: 维度7整体架构(12分) + 维度8实测表现(23分)

### 阶段 5: 提交
```bash
examlex commit --artifacts-dir <path> --library strategy-library.json
```
棘轮检查 + 原子写入 + 自动备份

## Darwin 评分体系

详见 [darwin-rubric.md](darwin-rubric.md)

## 会话管理

中间产物存储在 `~/.examlex/sessions/<日期>/<uuid>/`。
长任务可续跑: `examlex resume <session-id>`
