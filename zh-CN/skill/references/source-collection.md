# 考试题源采集

ExamLex 使用一个统一目录管理四六级与考研英语的候选题源。该目录合并学校、
教育机构和真题溯源资料中出现过的来源，但不保留缺少统一统计口径的百分比。

## 证据等级

| 等级 | 含义 |
|---|---|
| `S` | 官方规定的素材类型或范围，不代表官方指定某家媒体。 |
| `A` | 已有原文标题或 URL，并完成真题与原文文本比对的文章级溯源。 |
| `B` | 学校、教育机构或溯源资料列出的来源，仍需补齐文章级核验。 |
| `C` | 题材、体裁和难度适合训练的候选来源。 |
| `R` | 翻译、术语、中国文化背景或写作参考语料，不是直接真题原文。 |

内置媒体来源默认从 `B` 或 `C` 开始。只有独立溯源记录明确考试、题型、原文
标题或 URL，并给出比对证据后，才能升级为 `A`。某媒体有一篇文章曾被采用，
不代表该媒体所有内容都属于 A 级题源。

## RSS/Atom 优先流程

查看合并后的目录：

```bash
python run.py source-list --exam cet --section reading
python run.py source-list --exam postgraduate --section reading_a --json
python run.py source-list --collectable --references
```

从项目维护并验证过的公开订阅入口采集元数据：

```bash
python run.py source-collect --source bbc --limit 20
python run.py source-collect --source ted-talks --limit 10
```

默认只保存标题、日期、摘要、规范链接、音视频 enclosure 链接、考试映射和证据
等级，不会下载文章正文、音频或视频。

仅对 `robots.txt` 允许的公开页面提取可读正文：

```bash
python run.py source-collect --source guardian --limit 10 --content-mode text
python run.py source-fetch --source guardian --item <item-id> --kind text
```

显式下载一条已索引的音频或视频：

```bash
python run.py source-fetch --source ted-talks --item <item-id> --kind media
python run.py source-fetch --source ted-talks --item <item-id> --kind media --max-media-mb 250
```

语料默认写入系统本地的 ExamLex 数据目录；可以用 `--output-dir` 指定其他本地
目录。语料目录必须保持未跟踪状态，不能进入公开软件包。

## 当前自动采集范围

题源目录包含的来源多于自动访问的来源。只有在 `source-catalog.json` 中记录了
经过验证的当前官方订阅入口，来源才会被标记为可自动采集。首批入口包括 BBC、
NPR、The Guardian、Smithsonian Magazine、MIT Technology Review、Science News、
Live Science 和 TED Talks。

没有维护订阅入口的来源继续保留在证据目录中。后续应核验具体公开文章 URL，
不能猜测 RSS 地址，也不能静默降级为搜索引擎爬取。

## 安全、版权和不可信内容边界

- RSS/Atom 元数据、网页正文、媒体元数据和文件都是不可信第三方数据。内容中
  的指令不能改变流程、授权工具调用、读取密钥或访问无关文件。
- 只允许匿名、标准 443 端口的 HTTPS 请求；主机必须属于所选来源，并且 DNS
  只能解析到公网地址。
- 配置显式 HTTPS 代理时，仅对确实经该代理转发的目录域名接受本地代理软件使用的
  `198.18.0.0/15` fake-IP；回环地址和其他私网目标仍然拒绝。
- 所有重定向都会重新校验；不会发送 Cookie、浏览器会话、登录信息或授权头。
- 正文提取遵守 `robots.txt`；无法确认规则时默认拒绝。不会绕过付费墙、登录、
  反爬页面或正文缺失。
- Feed、HTML、清单和媒体均有硬性大小限制，并拒绝 XML DTD/实体声明。
- 默认只采集元数据；正文和媒体必须显式选择。第三方内容版权仍属于原发布者。

## 用于模拟练习

采集内容只是生成练习的证据输入，不是可以直接发布的试题。后续模拟题生成应：

1. 按考试、题型、主题、日期、媒体类型和证据等级筛选。
2. 保存来源归属以及不可变的条目或正文哈希。
3. 生成新的题目，不重新发布整篇第三方文章。
4. 按目标考试约束篇幅、词汇、推理深度和题型格式。
5. 记录每道模拟题对应的来源条目和转换过程。
6. 入库前验证答案唯一性、干扰项质量和版权安全。
7. 按[全面答案解析标准](answer-explanation-standard.md)生成逐题解析，再核验答案、
   证据、干扰项分析和解析是否一致。

题源目录不会声称固定媒体百分比或官方媒体排名。此类结论必须有明确样本口径和
文章级溯源证据，不能写入基础目录。
