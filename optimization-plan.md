# ExamLex — 完整技术规格文档

> P0 → P3 逐项展开：命令签名、JSON Schema、函数伪代码、文件清单、测试规格、集成矩阵。
> 实施前请结合当前 `common.py` 和 `cli.py` 的实际代码确认接口兼容性。

---

## 目录

- [P0 — 策略库校验脚本](#p0--策略库校验脚本)
- [P1.1 — 专四/专八支持](#p11--专四专八支持)
- [P1.2 — 词汇量估算](#p12--词汇量估算)
- [P1.3 — 预置词汇库](#p13--预置词汇库)
- [P2.1 — 计时训练模式](#p21--计时训练模式)
- [P2.2 — 间隔复习机制](#p22--间隔复习机制)
- [P2.3 — 常见错误库](#p23--常见错误库)
- [P3.1 — 进度可视化](#p31--进度可视化)
- [P3.2 — 作文范文库](#p32--作文范文库)
- [P3.3 — 数据备份与迁移](#p33--数据备份与迁移)
- [附录 A：全局常量汇总](#附录-a全局常量汇总)
- [附录 B：CLI 命令注册汇总](#附录-bcli-命令注册汇总)
- [附录 C：测试用例汇总](#附录-c测试用例汇总)
- [附录 D：实施顺序与依赖关系](#附录-d实施顺序与依赖关系)

---

## P0 — 策略库校验脚本

### 1. 命令设计

```bash
python -m examlex validate-strategy \
  --library <path>                    # 策略库 JSON 文件路径（必填）
  [--schema <path>]                   # 自定义 Schema 路径（可选，默认使用内置 Schema）
  [--strict]                          # WARNING 升级为 ERROR（可选）
  [--json]                            # JSON 格式输出（可选，默认人类可读）
```

**退出码**:

| 退出码 | 含义 |
|:------:|------|
| 0 | 全部通过 |
| 1 | 存在 WARNING（`--strict` 下升级为 2） |
| 2 | 存在 ERROR |

**输出示例（人类可读）**:

```text
PASS   strategy_id: "cet4-reading-speed-001" — 格式合法，唯一
PASS   title: "四级阅读快速定位法" — 非空
PASS   exam_types: ["CET4","CET6"] — 所有值在合法集合内
ERROR  modules: ["readding"] — "readding" 不在合法集合内 (合法值: vocabulary, listening, reading, translation, writing)
WARN   ability_nodes: ["快速阅读"] — "快速阅读" 不在 reading 模块的合法节点内 (合法值: 阅读速度, 定位能力, 长难句, 推理判断)
PASS   content: 非空，56 字符
PASS   steps: 3 项，全部非空
PASS   source_file: "四级阅读技巧.md" — 非空
ERROR  added_at: "2026/07/05" — 格式错误，应为 ISO 8601 (YYYY-MM-DD)

结果: 6 PASS, 1 WARN, 2 ERROR — 校验未通过
```

**输出示例（`--json`）**:

```json
{
  "file": "strategy-library.json",
  "total_strategies": 5,
  "results": [
    {
      "strategy_id": "cet4-reading-speed-001",
      "checks": [
        {"field": "strategy_id",   "status": "PASS",   "message": "格式合法，唯一"},
        {"field": "exam_types",     "status": "PASS",   "message": "所有值在合法集合内"},
        {"field": "modules",        "status": "ERROR",  "message": "\"readding\" 不在合法集合内"},
        {"field": "ability_nodes",  "status": "WARN",   "message": "\"快速阅读\" 不在 reading 模块合法节点内"},
        {"field": "added_at",       "status": "ERROR",  "message": "格式错误，应为 ISO 8601"}
      ],
      "pass": 6, "warn": 1, "error": 2
    }
  ],
  "summary": {"total_pass": 28, "total_warn": 1, "total_error": 2, "passed": false}
}
```

### 2. JSON Schema 定义

```json
{
  "$id": "strategy-library.schema.json",
  "title": "Strategy Library",
  "type": "object",
  "required": ["strategies"],
  "properties": {
    "strategies": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["strategy_id", "title", "exam_types", "modules", "content", "source_file", "added_at"],
        "properties": {
          "strategy_id": {
            "type": "string",
            "pattern": "^[a-z]+-[a-z]+-[a-z0-9-]+-\\d{3}$",
            "description": "格式: {exam-abbr}-{module}-{keyword}-{seq}, e.g. cet4-reading-speed-001"
          },
          "title": {
            "type": "string",
            "minLength": 1,
            "maxLength": 200
          },
          "source_file": {
            "type": "string",
            "minLength": 1
          },
          "added_at": {
            "type": "string",
            "format": "date",
            "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
          },
          "exam_types": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "string",
              "enum": ["CET4", "CET6", "POSTGRADUATE_ENGLISH", "TEM4", "TEM8"]
            }
          },
          "modules": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "string",
              "enum": ["vocabulary", "listening", "reading", "translation", "writing", "language-knowledge", "proofreading", "dictation"]
            }
          },
          "ability_nodes": {
            "type": "array",
            "items": { "type": "string", "minLength": 1 }
          },
          "content": {
            "type": "string",
            "minLength": 20
          },
          "steps": {
            "type": "array",
            "items": { "type": "string", "minLength": 1 }
          },
          "tags": {
            "type": "array",
            "items": { "type": "string" }
          }
        }
      }
    }
  }
}
```

### 3. 函数伪代码

```python
# examlex/scripts/validate_strategy.py

def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    library = load_data(args.library)

    if "strategies" not in library or not isinstance(library["strategies"], list):
        report_fatal("顶层缺少 'strategies' 数组")
        return 2

    results = []
    seen_ids: set[str] = set()
    all_pass = True
    has_warning = False

    for i, strategy in enumerate(library["strategies"]):
        checks = []
        sid = strategy.get("strategy_id", f"<条目 #{i+1} 缺少 strategy_id>")

        # 1. strategy_id: 必填 + 格式 + 唯一
        if not strategy.get("strategy_id"):
            checks.append(Check("strategy_id", "ERROR", "缺少 strategy_id"))
        elif not STRATEGY_ID_PATTERN.match(strategy["strategy_id"]):
            checks.append(Check("strategy_id", "ERROR",
                f"'{strategy['strategy_id']}' 格式不合法，应为 {{exam}}-{{module}}-{{keyword}}-{{seq}}"))
        elif strategy["strategy_id"] in seen_ids:
            checks.append(Check("strategy_id", "ERROR", f"'{strategy['strategy_id']}' 重复"))
        else:
            seen_ids.add(strategy["strategy_id"])
            checks.append(Check("strategy_id", "PASS", "格式合法，唯一"))

        # 2. title: 必填 + 非空
        checks.append(check_required_nonempty(strategy, "title", 1, 200))

        # 3. exam_types: 必填 + 数组 + 值合法性
        checks.append(check_enum_array(strategy, "exam_types", ALL_EXAM_TYPES, "考试类型"))

        # 4. modules: 必填 + 数组 + 值合法性 (来自 ABILITY_TREE keys)
        checks.append(check_enum_array(strategy, "modules", set(ABILITY_TREE.keys()), "模块"))

        # 5. ability_nodes: 可选 + 值跨模块校验 (WARNING)
        if "ability_nodes" in strategy:
            for node in strategy["ability_nodes"]:
                valid = any(node in nodes for nodes in ABILITY_TREE.values())
                level = "WARN" if not valid else "PASS"
                checks.append(Check("ability_nodes", level,
                    f"'{node}' {'不在任何模块的合法节点内' if not valid else '合法'}"))

        # 6. content: 必填 + 最少 20 字符
        checks.append(check_required_nonempty(strategy, "content", 20, 5000))

        # 7. steps: 可选 + 数组项非空
        if "steps" in strategy:
            for j, step in enumerate(strategy["steps"]):
                if not step or not step.strip():
                    checks.append(Check("steps", "WARN", f"steps[{j}] 为空"))

        # 8. source_file: 必填 + 非空
        checks.append(check_required_nonempty(strategy, "source_file", 1, 500))

        # 9. added_at: 必填 + ISO 8601 日期格式
        checks.append(check_iso_date(strategy, "added_at"))

        # 汇总
        errors = sum(1 for c in checks if c.status == "ERROR")
        warns  = sum(1 for c in checks if c.status == "WARN")
        passes = sum(1 for c in checks if c.status == "PASS")

        if args.strict:
            errors += warns
            warns = 0

        results.append({
            "strategy_id": sid,
            "checks": [c.to_dict() for c in checks],
            "pass": passes, "warn": warns, "error": errors
        })

        if errors > 0:
            all_pass = False
        if warns > 0:
            has_warning = True

    # 输出
    if args.json:
        print_json_results(results, all_pass)
    else:
        print_human_results(results)

    if not all_pass:
        return 2
    if has_warning:
        return 1
    return 0
```

### 4. 涉及文件（精确路径）

```
新增 (3 files):
  skills/examlex/scripts/validate_strategy.py
  examlex/scripts/validate_strategy.py   # 镜像
  skills/examlex/assets/schemas/strategy-library.schema.json

修改 (4 files):
  examlex/cli.py                          # +1 命令注册
  examlex/scripts/common.py               # +常量 +校验函数
  skills/examlex/scripts/ingest_strategy.py      # 写入后自动校验
  scripts/validate_repo.py                                      # + --check-strategies
```

### 5. CLI 注册（cli.py 修改）

```python
# 在 COMMANDS dict 中追加:
"validate-strategy": ("Validate a strategy library file.", validate_strategy.main),
```

### 6. 测试规格

```
tests/test_validate_strategy.py

class TestValidateStrategy:
    def test_all_valid(self):
        """全部合法 → 退出码 0"""

    def test_missing_strategy_id(self):
        """缺少 strategy_id → ERROR → 退出码 2"""

    def test_duplicate_strategy_id(self):
        """重复 strategy_id → ERROR → 退出码 2"""

    def test_invalid_exam_type(self):
        """exam_types 含 'TOEFL' → ERROR → 退出码 2"""

    def test_invalid_module(self):
        """modules 含 'speaking' → ERROR → 退出码 2"""

    def test_unknown_ability_node(self):
        """ability_nodes 含未知节点 → WARNING → 退出码 1"""

    def test_strict_mode(self):
        """--strict 下 WARNING → ERROR → 退出码 2"""

    def test_invalid_date_format(self):
        """added_at = '2026/07/05' → ERROR"""

    def test_content_too_short(self):
        """content < 20 字符 → ERROR"""

    def test_empty_library(self):
        """strategies 数组为空 → 退出码 0（不报错，但也不通过校验）"""

    def test_missing_top_level_key(self):
        """JSON 缺少 'strategies' → ERROR → 退出码 2"""

    def test_steps_with_empty_item(self):
        """steps 中存在空字符串 → WARNING"""
```

---

## P1.1 — 专四/专八支持

### 1. 命令设计

无新增 CLI 命令。所有现有脚本通过 `common.py` 中的扩展常量自动支持 TEM-4/8。

**行为变化验证**:

```bash
# 验证 TEM-4 档案可被校验
python -m examlex validate-profile \
  --profile tests/fixtures/tem4-learner-profile.json
# → 应通过（exit 0）

# 验证 TEM-8 计划可被生成
python -m examlex daily-plan \
  --profile tests/fixtures/tem8-learner-profile.json \
  --ability tests/fixtures/tem8-ability-profile.json \
  --output /tmp/tem8-plan.json
# → 应生成包含 dictation / proofreading 模块的计划
```

### 2. common.py 完整修改

```python
# ============================================================
# 考试类型扩展
# ============================================================
EXAM_TYPES = {"CET4", "CET6", "POSTGRADUATE_ENGLISH", "TEM4", "TEM8"}

# ============================================================
# 目标区间扩展
# ============================================================
TEM_TARGET_BANDS = {"60~69", "70~79", "80+"}

def target_bands_for(exam_type: str) -> set[str]:
    if exam_type in {"CET4", "CET6"}:
        return CET_TARGET_BANDS
    if exam_type == "POSTGRADUATE_ENGLISH":
        return POSTGRADUATE_TARGET_BANDS
    if exam_type in {"TEM4", "TEM8"}:
        return TEM_TARGET_BANDS
    return set()

# ============================================================
# 能力树扩展
# ============================================================
ABILITY_TREE = {
    "vocabulary":          ["词义识别", "拼写", "听音辨词", "语境使用"],
    "listening":           ["关键词捕捉", "连读弱读", "数字时间", "主旨推断"],
    "reading":             ["阅读速度", "定位能力", "长难句", "推理判断"],
    "translation":         ["语法准确度", "词汇选择", "中式英语", "句式多样性"],
    "writing":             ["任务完成度", "结构逻辑", "语言准确性", "表达丰富度"],
    # --- TEM-4/8 专属 ---
    "language-knowledge":  ["语法选择", "词汇辨析"],          # TEM-4
    "proofreading":        ["冠词错误", "搭配错误", "逻辑错误"], # TEM-8
    "dictation":           ["听写准确率", "拼写速度"],         # TEM-4
}

# ============================================================
# 错误标签扩展
# ============================================================
ERROR_TAG_TO_ABILITY = {
    # ... 现有标签保持不变 ...

    # TEM-4 language-knowledge
    "LANG_GRAMMAR_SELECT_FAIL":      ("language-knowledge", "语法选择"),
    "LANG_VOCAB_DISCRIMINATE_FAIL":  ("language-knowledge", "词汇辨析"),

    # TEM-8 proofreading
    "PROOFREAD_ARTICLE_MISS":        ("proofreading", "冠词错误"),
    "PROOFREAD_COLLOCATION_FAIL":    ("proofreading", "搭配错误"),
    "PROOFREAD_LOGIC_INCOHERENT":    ("proofreading", "逻辑错误"),

    # TEM-4 dictation
    "DICTATION_ACCURACY_LOW":        ("dictation", "听写准确率"),
    "DICTATION_SPELLING_SPEED_LOW":  ("dictation", "拼写速度"),
}
```

### 3. 考试时间模板

```python
# ============================================================
# 计时训练时间模板（TEM-4/8 专属）
# ============================================================
EXAM_TIME_LIMITS = {
    # ... CET-4/6/POSTGRAD 保持不变 ...

    "TEM4": {
        "dictation":             15,
        "listening":             20,
        "language-knowledge":    10,
        "cloze":                 10,
        "reading":               25,
        "writing":               35,
    },
    "TEM8": {
        "listening":             25,   # mini-lecture + interview
        "reading":               30,
        "language-knowledge":    15,   # （如果有语法题，实际 TEM-8 无独立语法题则省略）
        "translation":           25,   # 英译汉 + 汉译英（TEM-8 两者都有）
        "writing":               45,   # 命题作文 + 材料作文
        "proofreading":          15,
    },
}
```

### 4. 涉及文件（精确路径）

```
修改 (10 files):
  examlex/scripts/common.py
  examlex/scripts/validate_profile.py     # 校验 TEM 目标区间
  examlex/scripts/generate_daily_plan.py  # 处理新模块
  examlex/scripts/summarize_errors.py     # 新标签统计
  examlex/scripts/update_ability_profile.py
  examlex/scripts/analyze_trends.py
  examlex/references/exam-profiles.md
  examlex/references/error-taxonomy.md
  examlex/assets/templates/learner-profile.yaml
  examlex/assets/templates/ability-profile.yaml

新增 (4 files):
  docs/tem4.md
  docs/tem8.md
  zh-CN/docs/tem4.md
  zh-CN/docs/tem8.md
```

### 5. 测试规格

```
tests/test_tem_support.py  (或扩展现有测试)

class TestTEMSupport:
    def test_tem4_profile_validation(self):
        """TEM-4 档案校验通过"""

    def test_tem8_profile_validation(self):
        """TEM-8 档案校验通过"""

    def test_tem4_invalid_band_rejected(self):
        """TEM-4 用 '550+' → 校验失败"""

    def test_tem8_invalid_band_rejected(self):
        """TEM-8 用 '90+' → 校验失败"""

    def test_tem4_daily_plan_includes_new_modules(self):
        """TEM-4 计划包含 dictation 和 language-knowledge 模块"""

    def test_tem8_daily_plan_includes_proofreading(self):
        """TEM-8 计划包含 proofreading 模块"""

    def test_tem4_error_tags_mapped_correctly(self):
        """DICTATION_ACCURACY_LOW → dictation / 听写准确率"""

    def test_tem8_proofread_tags_mapped_correctly(self):
        """PROOFREAD_ARTICLE_MISS → proofreading / 冠词错误"""

    def test_tem_target_bands_helper(self):
        """target_bands_for('TEM4') → {'60~69','70~79','80+'}"""
```

---

## P1.2 — 词汇量估算

### 1. 命令设计

```bash
python -m examlex vocab-estimate \
  --wordlist <path>              # 用户标注的词表 JSON（非交互模式，必填，与 --interactive 互斥）
  [--output <path>]              # 结果输出路径（默认 stdout）
  [--reference <path>]           # 测试词表文件（默认使用内置词表）

python -m examlex vocab-estimate \
  --interactive                  # 交互模式：逐词输出，通过 stdin/stdout 交互
  [--bands <bands>]              # 仅测试指定频率段，逗号分隔（默认全部 6 段）
  [--samples-per-band <n>]       # 每段真词数（默认 10）
  [--nonwords-per-band <n>]      # 每段假词数（默认 2）
  [--output <path>]
  [--reference <path>]

# Agent 使用示例
python -m examlex vocab-estimate \
  --interactive --bands 1-1000,1001-2000,2001-3000 \
  --samples-per-band 5 --output vocab-result.json
```

**`--wordlist` 输入格式**（用户填写后传入）:

```json
{
  "learner_id": "learner-001",
  "test_date": "2026-07-05",
  "answers": [
    {"word": "abandon",      "band": "1-1000",    "is_real": true,  "known": true},
    {"word": "bracket",      "band": "2001-3000",  "is_real": true,  "known": false},
    {"word": "flompery",     "band": "1-1000",    "is_real": false, "known": true},
    {"word": "sophisticated","band": "4001-6000",  "is_real": true,  "known": true}
  ]
}
```

**`--interactive` 模式交互流程** (Agent 逐个询问用户):

```
Agent 显示: 你认识这个词吗？ "abandon"  [y/n]
用户输入: y
Agent 显示: 你认识这个词吗？ "flompery"  [y/n]
用户输入: y  (← 虚报！此词不存在)
...
```

### 2. JSON Schema（输出）

```json
{
  "$id": "vocab-estimate-result.schema.json",
  "type": "object",
  "required": ["learner_id", "test_date", "method", "estimated_vocabulary", "confidence_interval", "false_alarm_rate", "by_band"],
  "properties": {
    "learner_id":           { "type": "string" },
    "test_date":            { "type": "string", "format": "date" },
    "method":               { "const": "yes-no-sampling" },
    "estimated_vocabulary": { "type": "integer", "minimum": 0, "maximum": 30000 },
    "confidence_interval": {
      "type": "array",
      "minItems": 2, "maxItems": 2,
      "items": { "type": "integer" }
    },
    "false_alarm_rate": {
      "type": "number", "minimum": 0, "maximum": 1,
      "description": "对假词回答'认识'的比例，用于修正虚报偏差"
    },
    "by_band": {
      "type": "object",
      "patternProperties": {
        "^\\d+-\\d+\\+?$": {
          "type": "object",
          "required": ["tested", "claimed", "estimated"],
          "properties": {
            "tested":    { "type": "integer", "minimum": 0 },
            "claimed":   { "type": "integer", "minimum": 0 },
            "estimated": { "type": "integer", "minimum": 0 }
          }
        }
      }
    }
  }
}
```

### 3. 内置测试词表结构

```json
{
  "bands": {
    "1-1000": {
      "real_words": ["abandon", "ability", "absent", ...],
      "non_words": ["flompery", "trikkle", ...]
    },
    "1001-2000": {
      "real_words": ["bachelor", "backup", "bacteria", ...],
      "non_words": ["plosticate", "wrentle", ...]
    }
  },
  "meta": {
    "total_real_words": 600,
    "total_non_words": 120,
    "source": "基于 COCA / BNC / CET 考纲频率统计（public domain）"
  }
}

```

### 4. 估算算法伪代码

```python
# estimate_vocabulary.py 核心逻辑

def estimate(bands_data: dict, answers: list[dict]) -> VocabResult:
    """
    对每段频率区间独立估算，然后求和得到总词汇量。
    使用 Yes/No 测试标准校正公式：
        adjusted_rate = (H - FA) / (1 - FA)
        where H = claimed_known / tested_real
              FA = claimed_false_known / tested_nonword
    """
    total_estimated = 0
    total_false_alarms = 0
    total_nonword_tests = 0
    band_results = {}

    for band_label, band in bands_data.items():
        real_answers  = [a for a in answers if a["band"] == band_label and a["is_real"]]
        fake_answers  = [a for a in answers if a["band"] == band_label and not a["is_real"]]

        tested_real   = len(real_answers)
        claimed_real  = sum(1 for a in real_answers if a["known"])
        tested_fake   = len(fake_answers)
        claimed_fake  = sum(1 for a in fake_answers if a["known"])

        if tested_real == 0:
            continue

        H  = claimed_real / tested_real          # hit rate
        FA = claimed_fake / tested_fake if tested_fake > 0 else 0  # false alarm rate
        adjusted = max(0, (H - FA) / (1 - FA)) if FA < 1 else 0

        band_size = get_band_size(band_label)    # e.g. "1-1000" → 1000
        estimated = round(adjusted * band_size)

        total_estimated += estimated
        total_false_alarms += claimed_fake
        total_nonword_tests += tested_fake

        band_results[band_label] = {
            "tested": tested_real,
            "claimed": claimed_real,
            "hit_rate": round(H, 3),
            "false_alarm_rate": round(FA, 3),
            "adjusted_rate": round(adjusted, 3),
            "estimated": estimated,
        }

    # 95% 置信区间简算
    se = math.sqrt(total_estimated * (1 - adjusted)) if adjusted else 0
    ci_low  = max(0, round(total_estimated - 1.96 * se))
    ci_high = round(total_estimated + 1.96 * se)

    overall_fa = total_false_alarms / total_nonword_tests if total_nonword_tests > 0 else 0

    return VocabResult(
        learner_id=answers[0].get("learner_id", ""),
        test_date=datetime.date.today().isoformat(),
        estimated_vocabulary=total_estimated,
        confidence_interval=[ci_low, ci_high],
        false_alarm_rate=round(overall_fa, 3),
        by_band=band_results,
    )
```

### 5. 与现有脚本集成

```
validate_profile.py:
  新增 --suggest-foundation 标志：
    如果未提供 foundation_level，根据 estimated_vocabulary 自动建议：
      vocab < 2000  → "基础偏弱"
      vocab 2000-4000 → "中等基础"
      vocab > 4000  → "基础较好"

generate_daily_plan.py:
  新增 --vocab-estimate <path> 参数：
    vocabulary 模块能力节点初始化时，用估算结果的 by_band 数据替代默认值

update_ability_profile.py:
  探测到 vocab-estimate 输出文件时，自动更新 vocabulary 模块的 level 值
```

### 6. 涉及文件（精确路径）

```
新增 (5 files):
  skills/examlex/scripts/estimate_vocabulary.py
  examlex/scripts/estimate_vocabulary.py
  skills/examlex/assets/data/vocab-test-words.json
  skills/examlex/assets/schemas/vocab-estimate-result.schema.json
  tests/test_estimate_vocabulary.py

修改 (3 files):
  examlex/cli.py                  # +1 命令
  examlex/scripts/validate_profile.py  # + --suggest-foundation
  examlex/scripts/generate_daily_plan.py  # + --vocab-estimate
```

### 7. 测试规格

```
tests/test_estimate_vocabulary.py

class TestEstimateVocabulary:
    def test_perfect_score(self):
        """全部真词认识、假词不认识 → 估算 ≈ 总词数"""

    def test_zero_knowledge(self):
        """全部不认识 → 估算 ≈ 0"""

    def test_false_alarm_correction(self):
        """假词全部答'认识'（FA=1.0）→ 修正后估算大幅降低"""

    def test_partial_knowledge(self):
        """模拟 2000-3000 词量 → 估算在合理范围"""

    def test_single_band_only(self):
        """--bands 1-1000 → 只测试一段"""

    def test_output_json_format(self):
        """--output 输出符合 Schema"""

    def test_cli_registered(self):
        """examlex vocab-estimate --help 可运行"""
```

---

## P1.3 — 预置词汇库

### 1. 命令设计

无独立 CLI 命令。词汇库通过数据文件直接使用。`generate_daily_plan.py` 新增 `--vocab-pool` 参数引用。

```bash
# 计划生成时引用预置词表
python -m examlex daily-plan \
  --profile learner-profile.json \
  --ability ability-profile.json \
  --vocab-pool skills/examlex/assets/data/vocabulary/cet4-core-2000.json \
  --output daily-plan.json
```

### 2. JSON Schema（词条）

```json
{
  "$id": "vocab-entry.schema.json",
  "type": "object",
  "required": ["word", "meaning_cn", "frequency_rank"],
  "properties": {
    "word":              { "type": "string", "minLength": 1 },
    "phonetic":          { "type": "string" },
    "pos":               { "type": "string", "description": "词性缩写: n. / v. / adj. / adv. / prep. / conj." },
    "meaning_cn":        { "type": "string", "minLength": 1 },
    "frequency_rank":    { "type": "integer", "minimum": 1 },
    "example":           { "type": "string" },
    "cet_level":         { "enum": ["CET4", "CET6", "POSTGRADUATE"] },
    "collocations":      { "type": "array", "items": { "type": "string" } },
    "synonyms":          { "type": "array", "items": { "type": "string" } },
    "confusable_words":  { "type": "array", "items": { "type": "string" } }
  }
}
```

### 3. 词条示例

```json
{
  "word": "abandon",
  "phonetic": "/əˈbændən/",
  "pos": "v.",
  "meaning_cn": "放弃；抛弃；遗弃",
  "frequency_rank": 312,
  "example": "The crew abandoned the sinking ship.",
  "cet_level": "CET4",
  "collocations": ["abandon oneself to", "abandon a plan"],
  "synonyms": ["give up", "desert", "forsake"],
  "confusable_words": ["abundant"]
}
```

### 4. 词表文件结构

```
skills/examlex/assets/data/vocabulary/
├── cet4-core-2000.json              # 四级高频 2000 词（按 frequency_rank 升序）
├── cet6-core-1500.json              # 六级增量 1500 词（不含四级已覆盖）
├── postgraduate-core-1000.json      # 考研增量 1000 词
├── tem4-core-2000.json              # 专四高频 2000 词
├── tem8-core-2000.json              # 专八高频 2000 词
└── index.json                       # 索引：各词表词数、覆盖等级、来源说明
```

### 5. `index.json`

```json
{
  "cet4-core-2000": {
    "path": "cet4-core-2000.json",
    "count": 2000,
    "exam_types": ["CET4"],
    "description": "四级高频核心词汇，按真题出现频率降序排列",
    "source": "基于 CET-4 历年真题词频统计（public domain 数据源）"
  },
  "cet6-core-1500": {
    "path": "cet6-core-1500.json",
    "count": 1500,
    "exam_types": ["CET6"],
    "description": "六级增量高频词汇，假设用户已掌握四级词表",
    "source": "基于 CET-6 历年真题词频统计"
  },
  "postgraduate-core-1000": {
    "path": "postgraduate-core-1000.json",
    "count": 1000,
    "exam_types": ["POSTGRADUATE_ENGLISH"],
    "description": "考研英语增量高频词汇",
    "source": "基于考研英语(一/二)历年真题词频统计"
  }
}
```

### 6. `generate_daily_plan.py` 词汇池集成

```python
def select_daily_vocab(
    vocab_pool: list[dict],
    ability_profile: dict,
    daily_time_budget: int,
    count: int = 20
) -> list[dict]:
    """
    从词表中按频率 + 能力状态选择当日词汇任务。
    优先选: 1) 低频词（用户可能不认识） 2) 能力画像中标注 needs_work 的
    """
    # 1. 按能力状态排序
    vocab_status = ability_profile.get("modules", {}).get("vocabulary", [])
    weak_words = set()
    for node in vocab_status:
        if node.get("status") == "needs_work":
            # 提取该节点的词汇特征（如拼写弱 → 选含易错拼写的词）
            weak_words.update(find_words_by_weakness(vocab_pool, node["node"]))

    # 2. 从未练习过的词中按频率 rank 从低到高选
    candidates = [w for w in vocab_pool if w["word"] in weak_words]
    if len(candidates) < count:
        # 从全量词表中补足
        used = {w["word"] for w in candidates}
        candidates += [w for w in vocab_pool if w["word"] not in used][:count - len(candidates)]

    # 3. 按频率 rank 排序后取前 count 个
    candidates.sort(key=lambda w: w["frequency_rank"])
    return candidates[:count]
```

### 7. 涉及文件（精确路径）

```
新增 (7 files):
  skills/examlex/assets/data/vocabulary/cet4-core-2000.json
  skills/examlex/assets/data/vocabulary/cet6-core-1500.json
  skills/examlex/assets/data/vocabulary/postgraduate-core-1000.json
  skills/examlex/assets/data/vocabulary/tem4-core-2000.json
  skills/examlex/assets/data/vocabulary/tem8-core-2000.json
  skills/examlex/assets/data/vocabulary/index.json
  skills/examlex/assets/schemas/vocab-entry.schema.json

修改 (1 file):
  examlex/scripts/generate_daily_plan.py  # + --vocab-pool
```

### 8. 测试规格

```
tests/test_vocab_pool.py

class TestVocabPool:
    def test_index_loads(self):
        """index.json 可正常加载，所有路径存在"""

    def test_all_entries_valid(self):
        """所有词条通过 vocab-entry.schema.json 校验"""

    def test_cet4_sorted_by_frequency(self):
        """cet4-core-2000.json 按 frequency_rank 升序"""

    def test_daily_vocab_selection_respects_count(self):
        """select_daily_vocab 返回 <= count 条"""

    def test_daily_vocab_prioritizes_needs_work(self):
        """needs_work 节点的词优先被选中"""

    def test_cet6_no_overlap_with_cet4(self):
        """cet6-core-1500 和 cet4-core-2000 无重复词条"""
```

---

## P2.1 — 计时训练模式

### 1. 命令设计

无新增 CLI 命令。`record_practice.py` 扩展以支持计时字段。

```bash
# 计时练习记录
python -m examlex record-practice \
  --ledger practice-ledger.json \
  --date 2026-07-05 \
  --exam-type CET4 \
  --module reading \
  --task-id timed-reading-001 \
  --duration 40 \
  --total 20 \
  --correct 14 \
  --timed \                            # ← 启用计时模式
  --time-limit 35 \                    # ← 考试规定时间（分钟）
  --overtime-items 3 \                 # ← 超时后完成的题目数
  --overtime-correct 1 \               # ← 超时题目中做对的
  --error-tags READING_SPEED_LOW,READING_INFERENCE_FAIL

# 自动获取时间限制（从 EXAM_TIME_LIMITS 查找）
python -m examlex record-practice \
  --ledger practice-ledger.json \
  --timed --exam-type CET4 --module reading \
  --task-id timed-reading-001 \
  --duration 40 --total 20 --correct 14 \
  --overtime-items 3 --overtime-correct 1
  # ↑ --time-limit 未指定时，自动从 EXAM_TIME_LIMITS["CET4"]["reading"] 获取 → 35
```

### 2. 练习记录 Schema 扩展

```json
{
  "$id": "exercise-record.schema.json",
  "type": "object",
  "required": ["date", "exam_type", "module", "task_id", "duration_minutes", "total_items", "correct_items"],
  "properties": {
    "date":             { "type": "string", "format": "date" },
    "exam_type":        { "enum": ["CET4","CET6","POSTGRADUATE_ENGLISH","TEM4","TEM8"] },
    "module":           { "type": "string" },
    "task_id":          { "type": "string" },
    "duration_minutes": { "type": "integer", "minimum": 1 },
    "total_items":      { "type": "integer", "minimum": 1 },
    "correct_items":    { "type": "integer", "minimum": 0 },

    "timed":               { "type": "boolean", "default": false },
    "time_limit_minutes":  { "type": "integer", "minimum": 1 },
    "overtime_items":      { "type": "integer", "minimum": 0 },
    "overtime_correct":    { "type": "integer", "minimum": 0 },

    "error_tags": { "type": "array", "items": { "type": "string" } }
  }
}
```

### 3. `summarize_errors.py` 扩展

```python
# 错误汇总新增维度
def summarize_errors(ledger: list[dict]) -> dict:
    # ... 现有归因逻辑 ...

    # 新增：计时训练专项统计
    timed_records = [r for r in ledger if r.get("timed")]
    if timed_records:
        total_overtime_items   = sum(r.get("overtime_items", 0) for r in timed_records)
        total_overtime_correct = sum(r.get("overtime_correct", 0) for r in timed_records)
        overtime_accuracy = (total_overtime_correct / total_overtime_items
                             if total_overtime_items > 0 else 0)

        result["speed_analysis"] = {
            "timed_sessions": len(timed_records),
            "total_time_pressure_items": total_overtime_items,
            "overtime_accuracy": round(overtime_accuracy, 3),
            "verdict": (
                "速度是主要瓶颈" if overtime_accuracy > 0.6
                else "知识缺口是主要瓶颈" if overtime_accuracy < 0.3
                else "速度与知识均需提升"
            ),
            "by_module": {},  # 按模块拆分
        }
```

### 4. `common.py` 时间模板

```python
EXAM_TIME_LIMITS: dict[str, dict[str, int]] = {
    "CET4": {
        "writing":      30,
        "listening":    25,
        "reading":      40,
        "translation":  30,
    },
    "CET6": {
        "writing":      30,
        "listening":    30,
        "reading":      40,
        "translation":  30,
    },
    "POSTGRADUATE_ENGLISH": {
        "reading":      60,
        "writing":      50,
        "translation":  30,
        "cloze":        20,
    },
    "TEM4": {
        "dictation":            15,
        "listening":            20,
        "language-knowledge":   10,
        "cloze":                10,
        "reading":              25,
        "writing":              35,
    },
    "TEM8": {
        "listening":            25,
        "reading":              30,
        "translation":          25,
        "writing":              45,
        "proofreading":         15,
    },
}

def get_time_limit(exam_type: str, module: str) -> int | None:
    """获取指定考试 + 模块的规定时间（分钟），若未定义则返回 None"""
    return EXAM_TIME_LIMITS.get(exam_type, {}).get(module)
```

### 5. 涉及文件（精确路径）

```
修改 (5 files):
  examlex/scripts/record_practice.py
  examlex/scripts/summarize_errors.py
  examlex/scripts/common.py               # + EXAM_TIME_LIMITS
  examlex/assets/templates/exercise-record.json
  examlex/assets/schemas/exercise-record.schema.json

镜像同步 (2 files):
  examlex/scripts/record_practice.py
  examlex/scripts/summarize_errors.py
```

### 6. 测试规格

```
tests/test_timed_practice.py

class TestTimedPractice:
    def test_timed_record_accepted(self):
        """含 timed 字段的记录正常写入"""

    def test_time_limit_auto_lookup(self):
        """CET4 + reading → 自动获取 40min"""

    def test_overtime_stats_in_summary(self):
        """错误汇总包含 speed_analysis 字段"""

    def test_speed_vs_knowledge_verdict(self):
        """overtime_accuracy > 0.6 → '速度是主要瓶颈'"""

    def test_non_timed_record_no_overtime(self):
        """非计时记录不包含 overtime 字段不影响现有逻辑"""
```

---

## P2.2 — 间隔复习机制

### 1. 命令设计

无新增 CLI 命令。所有逻辑内置于 `generate_daily_plan.py` 和 `summarize_errors.py`。

### 2. `summarize_errors.py` 扩展

在输出的 `by_tag` 中每条记录新增 `last_practice_date` 和 `review_urgency`：

```python
def compute_review_urgency(
    tag: str,
    ledger: list[dict],
    base_weights: dict[str, float],
    today: datetime.date,
    window_days: int = 30
) -> tuple[str, float]:
    """
    计算某错误标签的复习紧迫度。

    base_weights: 从 common.py 的 ERROR_SEVERITY_WEIGHTS 获取
    """
    # 最近一次出现该标签的记录日期
    tagged = [r for r in ledger if tag in r.get("error_tags", [])]
    if not tagged:
        return (None, 0.0)

    last_date = max(datetime.date.fromisoformat(r["date"]) for r in tagged)
    days_since = (today - last_date).days

    # 最近 window_days 内出现频率
    recent = [r for r in tagged
              if (today - datetime.date.fromisoformat(r["date"])).days <= window_days]
    total_recent = len([r for r in ledger
                        if (today - datetime.date.fromisoformat(r["date"])).days <= window_days])
    error_freq = len(recent) / total_recent if total_recent > 0 else 0

    base_weight = base_weights.get(tag, 0.5)
    urgency = base_weight * (days_since / 7.0) * error_freq  # 以周为单位归一化
    urgency = min(urgency, 1.0)  # 上限 1.0

    return (last_date.isoformat(), round(urgency, 3))
```

### 3. `common.py` 错误严重性权重

```python
# 错误标签 → 基础严重性权重 (0.0 ~ 1.0)
# 权重越高的标签，越久未复习时紧迫度增长越快
ERROR_SEVERITY_WEIGHTS: dict[str, float] = {
    # 写作 — 高分值模块，错误影响大
    "WRITING_TASK_RESPONSE_WEAK":      0.9,
    "WRITING_STRUCTURE_LOGIC_WEAK":    0.9,
    "WRITING_LANGUAGE_ACCURACY_FAIL":  0.85,
    "WRITING_EXPRESSION_LIMITED":      0.7,
    "WRITING_ARTICLE_OMISSION":        0.6,

    # 阅读 — 分值高，速度 + 正确率并重
    "READING_SPEED_LOW":               0.8,
    "READING_LONG_SENTENCE_FAIL":      0.7,
    "READING_INFERENCE_FAIL":          0.75,
    "READING_LOCATION_FAIL":           0.65,
    "READING_PARAPHRASE_FAIL":         0.6,

    # 听力 — 一次错过不可逆
    "LISTENING_KEYWORD_MISS":          0.75,
    "LISTENING_MAIN_IDEA_FAIL":        0.7,
    "LISTENING_LINKING_WEAK_FORM_FAIL":0.65,
    "LISTENING_NUMBER_DATE_FAIL":      0.55,

    # 翻译
    "TRANSLATION_GRAMMAR_FAIL":        0.7,
    "TRANSLATION_CHINESE_ENGLISH":     0.65,
    "TRANSLATION_WORD_CHOICE_FAIL":    0.55,
    "TRANSLATION_SENTENCE_VARIETY_LOW":0.5,

    # 词汇
    "VOCAB_CONTEXT_MISUSE":            0.6,
    "VOCAB_MEANING_RECOGNITION_FAIL":  0.55,
    "VOCAB_SPELLING_FAIL":             0.5,
    "VOCAB_AUDIO_RECOGNITION_FAIL":    0.5,
}
```

### 4. `generate_daily_plan.py` 集成

```python
def generate_daily_plan(
    profile: dict,
    ability: dict,
    errors: dict | None = None,
    strategies: dict | None = None,
) -> dict:
    # ... 现有约束求解 ...

    # 间隔复习加权：对有 review_urgency > 阈值 的节点提高优先级
    REVIEW_URGENCY_THRESHOLD = 0.5
    if errors and "by_tag" in errors:
        for tag_entry in errors["by_tag"]:
            urgency = tag_entry.get("review_urgency", 0)
            if urgency > REVIEW_URGENCY_THRESHOLD:
                # 找到该标签对应的模块和节点
                module, node = ERROR_TAG_TO_ABILITY.get(tag_entry["tag"], (None, None))
                if module and node:
                    # 在计划中为该节点分配最低保证时间
                    plan["modules"][module]["min_guaranteed_minutes"] = (
                        plan["modules"][module].get("min_guaranteed_minutes", 0) + 10
                    )
                    plan["modules"][module]["review_urgent_nodes"].append({
                        "node": node,
                        "tag": tag_entry["tag"],
                        "urgency": urgency,
                        "last_practice": tag_entry["last_practice_date"],
                    })

    return plan
```

### 5. 涉及文件（精确路径）

```
修改 (3 files):
  examlex/scripts/common.py               # + ERROR_SEVERITY_WEIGHTS
  examlex/scripts/summarize_errors.py     # + review_urgency
  examlex/scripts/generate_daily_plan.py  # + 复习加权

镜像同步 (3 files):
  examlex/scripts/common.py
  examlex/scripts/summarize_errors.py
  examlex/scripts/generate_daily_plan.py
```

### 6. 测试规格

```
tests/test_spaced_review.py

class TestSpacedReview:
    def test_urgency_zero_for_never_seen_tag(self):
        """从未出现过的 tag → review_urgency = 0"""

    def test_urgency_increases_with_days(self):
        """30 天未复习 > 7 天未复习"""

    def test_urgency_increases_with_frequency(self):
        """高频错误 > 低频错误"""

    def test_severity_weight_matters(self):
        """WRITING_TASK_RESPONSE_WEAK (0.9) > VOCAB_SPELLING_FAIL (0.5)"""

    def test_plan_includes_urgent_review(self):
        """review_urgency > 0.5 → 计划中出现 review_urgent_nodes"""

    def test_plan_min_guaranteed_time(self):
        """紧急节点获得最低保证时间分配"""

    def test_urgency_capped_at_one(self):
        """极端情况下 urgency 不超过 1.0"""
```

---

## P2.3 — 常见错误库

### 1. 命令设计

无新增 CLI 命令。数据文件直接使用。`tag_error.py` 新增 `--reference` 参数。

```bash
# 使用常见错误库辅助归因
python -m examlex tag-error \
  --text "I went to store." \
  --reference skills/examlex/assets/data/common-errors/chinese-learner-writing-errors.json \
  --output error-tags.json
```

### 2. JSON Schema（错误模式）

```json
{
  "$id": "error-pattern.schema.json",
  "type": "object",
  "required": ["error_patterns"],
  "properties": {
    "error_patterns": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["pattern_id", "tag", "description_cn", "typical_examples", "exam_types", "frequency_in_corpus"],
        "properties": {
          "pattern_id": {
            "type": "string",
            "pattern": "^CN-[A-Z]{2}-[A-Z]+-\\d{3}$",
            "description": "格式: CN-{module_abbr}-{pattern_name}-{seq}"
          },
          "tag":               { "type": "string" },
          "description_cn":    { "type": "string", "minLength": 1 },
          "typical_examples": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "required": ["incorrect", "correct"],
              "properties": {
                "incorrect":  { "type": "string", "minLength": 1 },
                "correct":    { "type": "string", "minLength": 1 },
                "note_cn":    { "type": "string" }
              }
            }
          },
          "exam_types": {
            "type": "array",
            "items": { "enum": ["CET4","CET6","POSTGRADUATE_ENGLISH","TEM4","TEM8"] }
          },
          "frequency_in_corpus": {
            "enum": ["very_high", "high", "medium", "low"]
          },
          "suggested_fix_strategy": { "type": "string" },
          "related_tags": {
            "type": "array",
            "items": { "type": "string" }
          }
        }
      }
    }
  }
}
```

### 3. 涉及文件（精确路径）

```
新增 (6 files):
  skills/examlex/assets/data/common-errors/chinese-learner-writing-errors.json
  skills/examlex/assets/data/common-errors/chinese-learner-translation-errors.json
  skills/examlex/assets/data/common-errors/chinese-learner-listening-errors.json
  skills/examlex/assets/data/common-errors/chinese-learner-reading-errors.json
  skills/examlex/assets/data/common-errors/chinese-learner-vocabulary-errors.json
  skills/examlex/assets/schemas/error-pattern.schema.json

修改 (1 file):
  examlex/scripts/tag_error.py  # + --reference
```

### 4. 测试规格

```
tests/test_common_errors_library.py

class TestCommonErrors:
    def test_all_patterns_valid_schema(self):
        """所有 .json 文件通过 error-pattern.schema.json 校验"""

    def test_tags_exist_in_error_taxonomy(self):
        """pattern.tag 全部在 ERROR_TAG_TO_ABILITY 中"""

    def test_exam_types_valid(self):
        """exam_types 值全部在 EXAM_TYPES 中"""
```

---

## P3.1 — 进度可视化

### 1. 命令设计

```bash
python -m examlex visualize \
  --ability-history <path>           # ability-history.json（必填）
  --ledger <path>                    # practice-ledger.json（必填）
  [--error-summary <path>]           # error-summary.json（可选）
  [--output <path>]                  # 输出 HTML 路径（默认 progress-report.html）
  [--days <n>]                       # 统计最近 N 天（默认 30）
  [--title <text>]                   # 报告标题（默认 "英语备考进度报告"）
```

**输出结构**:

```
progress-report.html    # 单文件，浏览器直接打开
├── <style>             # 内嵌 CSS（无外部依赖）
├── <svg id="radar">    # 能力雷达图（内联 SVG）
├── <svg id="trends">   # 学习曲线折线图
├── <svg id="heatmap">  # 错误热度图
├── <svg id="pie">      # 时间分配饼图
└── <div id="summary">  # 概览仪表板（纯 HTML table）
```

### 2. 图表规格

**雷达图** (`<svg id="radar">`):
```
五边形雷达图，5 个轴代表 vocabulary / listening / reading / translation / writing
- 蓝色填充: 当前能力值
- 灰色虚线: 上次评估值（对比用）
- 各轴标签: 模块名 + 数值
- 0-100 刻度环
```

**学习曲线** (`<svg id="trends">`):
```
折线图，X 轴 = 日期（7/30/90 天），Y 轴 = 正确率 (0-100%)
- 每条线代表一个模块，不同颜色
- 虚线: 总体正确率趋势
- 可选 --days 控制 X 轴范围
```

**错误热度图** (`<svg id="heatmap">`):
```
矩阵: 行 = 错误标签, 列 = 周
- 颜色深浅 = 出现次数（浅绿 → 深红）
- 一眼看出"哪些错误在消失，哪些在反复"
```

**时间分配饼图** (`<svg id="pie">`):
```
饼图（donut chart），按模块分色
- 内圈: 实际投入时间
- 外圈环: 计划建议时间（对比差距）
```

### 3. 函数伪代码

```python
# visualize_progress.py

def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    ability_history = load_data(args.ability_history)
    ledger = load_data(args.ledger)
    error_summary = load_data(args.error_summary) if args.error_summary else None

    html_parts = [
        render_html_head(args.title),
        render_css(),
        render_summary_dashboard(ledger, args.days),
        render_radar_chart(ability_history),
        render_trend_chart(ledger, args.days),
        render_heatmap(error_summary, args.days) if error_summary else "",
        render_pie_chart(ledger, args.days),
        render_html_foot(),
    ]

    output_path = Path(args.output) if args.output else Path("progress-report.html")
    output_path.write_text("\n".join(html_parts), encoding="utf-8")
    return 0


def render_radar_chart(history: dict) -> str:
    """生成内联 SVG 五边形雷达图"""
    # 计算五边形顶点坐标（基于 5 个模块的能力值）
    # 返回完整 <svg> 标签字符串
    ...

def render_trend_chart(ledger: list, days: int) -> str:
    """生成内联 SVG 折线图"""
    # 按日期分组计算各模块日均正确率
    # 生成 polyline 路径
    ...

def render_heatmap(errors: dict, days: int) -> str:
    """生成内联 SVG 错误热度图"""
    # 行 = tag, 列 = 周, 单元格颜色 = log(count+1) 映射到色阶
    ...

def render_pie_chart(ledger: list, days: int) -> str:
    """生成内联 SVG 环形图（donut）"""
    # 计算各模块时间占比
    # 生成 path 弧线段
    ...
```

### 4. 涉及文件（精确路径）

```
新增 (3 files):
  skills/examlex/scripts/visualize_progress.py
  examlex/scripts/visualize_progress.py  # 镜像
  tests/test_visualize_progress.py

修改 (1 file):
  examlex/cli.py  # +1 命令 ("visualize")
```

### 5. 测试规格

```
tests/test_visualize_progress.py

class TestVisualizeProgress:
    def test_generates_html_file(self):
        """输出 .html 文件存在且非空"""

    def test_html_contains_svg_elements(self):
        """HTML 包含 <svg> 标签"""

    def test_summary_dashboard_has_all_metrics(self):
        """仪表板含: 学习天数 / 总时长 / 总题数 / 正确率"""

    def test_empty_ledger_handled(self):
        """空台账不崩溃，输出空数据提示"""

    def test_svg_valid_xml(self):
        """SVG 元素可被 XML 解析器正常解析"""

    def test_respects_days_filter(self):
        """--days 7 只包含最近 7 天数据"""

    def test_cli_registered(self):
        """examlex visualize --help 可运行"""
```

---

## P3.2 — 作文范文库

### 1. 命令设计

无新增 CLI 命令。范文通过数据文件直接使用。`score_writing_rubric.py` 新增 `--reference-samples` 参数。

```bash
# 评分时引用范文库做锚定
python -m examlex score-writing \
  --exam-type CET4 \
  --essay essay.txt \
  --reference-samples skills/examlex/assets/data/sample-essays/cet4/ \
  --output score.json
```

### 2. JSON Schema（范文条目）

```json
{
  "$id": "sample-essay.schema.json",
  "type": "object",
  "required": ["sample_id", "exam_type", "module", "topic", "band", "essay_text", "rubric_scores"],
  "properties": {
    "sample_id":    { "type": "string", "pattern": "^(CET4|CET6|PG)-writing-\\d{3}-\\d{3}$" },
    "exam_type":    { "enum": ["CET4","CET6","POSTGRADUATE_ENGLISH"] },
    "module":       { "const": "writing" },
    "topic":        { "type": "string", "minLength": 1 },
    "band":         { "type": "string" },
    "prompt":       { "type": "string", "description": "作文原题/指令" },
    "essay_text":   { "type": "string", "minLength": 50 },
    "word_count":   { "type": "integer", "minimum": 50 },
    "rubric_scores": {
      "type": "object",
      "required": ["task_completion","structure_logic","language_accuracy","expression_richness","total","max"],
      "properties": {
        "task_completion":      { "type": "integer", "minimum": 0 },
        "structure_logic":      { "type": "integer", "minimum": 0 },
        "language_accuracy":    { "type": "integer", "minimum": 0 },
        "expression_richness":  { "type": "integer", "minimum": 0 },
        "total":                { "type": "integer", "minimum": 0 },
        "max":                  { "type": "integer", "minimum": 1 }
      }
    },
    "annotations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["highlight", "comment"],
        "properties": {
          "highlight":  { "type": "string", "minLength": 1 },
          "comment":    { "type": "string", "minLength": 1 },
          "dimension":  { "enum": ["task_completion","structure_logic","language_accuracy","expression_richness"] }
        }
      }
    }
  }
}
```

### 3. 文件结构

```
skills/examlex/assets/data/sample-essays/
├── index.json              # 索引
├── cet4/
│   ├── index.json
│   ├── band-425/
│   │   ├── 001.json
│   │   ├── 002.json
│   │   └── 003.json
│   ├── band-550/
│   └── band-600/
├── cet6/
│   ├── index.json
│   ├── band-425/
│   ├── band-550/
│   └── band-600/
└── postgraduate/
    ├── index.json
    ├── band-50/
    ├── band-70/
    └── band-90/
```

### 4. `score_writing_rubric.py` 锚定逻辑

```python
def score_with_anchor(
    essay_text: str,
    exam_type: str,
    reference_samples: list[dict]
) -> dict:
    """
    将待评作文与范文库中同考试类型、相邻分数段的范文比对，
    调整评分置信度。
    """
    # 1. 找同考试类型的范文
    same_exam = [s for s in reference_samples if s["exam_type"] == exam_type]
    if not same_exam:
        # 无范文时照常评分，并标注 "no_reference"
        result = rubric_score(essay_text, exam_type)
        result["anchor_quality"] = "no_reference"
        return result

    # 2. 基础评分
    result = rubric_score(essay_text, exam_type)

    # 3. 找最接近的范文分数段
    #    用词数、句式复杂度、高级词汇密度等作为比对特征
    features = extract_features(essay_text)
    closest_sample = find_closest_sample(features, same_exam)

    # 4. 置信度调整
    result["closest_reference_sample"] = closest_sample["sample_id"]
    result["closest_reference_band"]   = closest_sample["band"]
    result["anchor_quality"] = "single_reference"  # 可扩展为 multi-reference

    return result
```

### 5. 涉及文件（精确路径）

```
新增 (12 files):
  skills/examlex/assets/data/sample-essays/index.json
  skills/examlex/assets/data/sample-essays/cet4/index.json
  skills/examlex/assets/data/sample-essays/cet4/band-425/{001,002,003}.json
  skills/examlex/assets/data/sample-essays/cet4/band-550/{001,002,003}.json
  skills/examlex/assets/data/sample-essays/cet4/band-600/{001,002,003}.json
  skills/examlex/assets/data/sample-essays/cet6/index.json
  skills/examlex/assets/data/sample-essays/cet6/band-425/{001,002,003}.json
  skills/examlex/assets/data/sample-essays/cet6/band-550/{001,002,003}.json
  skills/examlex/assets/data/sample-essays/cet6/band-600/{001,002,003}.json
  skills/examlex/assets/data/sample-essays/postgraduate/index.json
  skills/examlex/assets/data/sample-essays/postgraduate/band-50/{001,002,003}.json
  skills/examlex/assets/data/sample-essays/postgraduate/band-70/{001,002,003}.json
  skills/examlex/assets/data/sample-essays/postgraduate/band-90/{001,002,003}.json
  skills/examlex/assets/schemas/sample-essay.schema.json

修改 (1 file):
  examlex/scripts/score_writing_rubric.py  # + --reference-samples
```

### 6. 测试规格

```
tests/test_sample_essays.py

class TestSampleEssays:
    def test_all_essays_valid_schema(self):
        """所有范文通过 sample-essay.schema.json 校验"""

    def test_index_matches_files(self):
        """index.json 条目与实际文件一一对应"""

    def test_all_exam_types_covered(self):
        """CET4/CET6/POSTGRADUATE 至少各 1 篇"""

    def test_all_bands_covered(self):
        """每个考试类型的每个分数段至少 1 篇"""

    def test_scoring_with_reference_returns_anchor(self):
        """有范文参照时评分结果包含 closest_reference_sample"""

    def test_scoring_without_reference_handled(self):
        """无范文时评分正常，anchor_quality = 'no_reference'"""
```

---

## P3.3 — 数据备份与迁移

### 1. 命令设计

```bash
# 备份
python -m examlex backup \
  --data-dir <path>                  # 数据目录（必填）
  [--output <path>]                  # 输出 .tar.gz 路径（默认 backup-{date}.tar.gz）
  [--exclude <patterns>]             # 排除模式，逗号分隔（默认排除 .env*,*private*）
  [--json]                           # JSON 格式输出

# 恢复
python -m examlex restore \
  --input <path>                     # 备份文件路径（必填）
  --data-dir <path>                  # 目标数据目录（必填）
  [--force]                          # 覆盖已有文件（默认跳过）
  [--dry-run]                        # 预览恢复内容，不实际写入
  [--json]

# 列出备份内容
python -m examlex backup \
  --list <path>                      # 列出备份文件内容
  [--json]
```

**输出示例**:

```bash
$ python -m examlex backup --list backup-2026-07-05.tar.gz

备份文件: backup-2026-07-05.tar.gz
创建时间: 2026-07-05T14:30:00
文件总数: 12
总大小:   2.3 MB
校验和:   sha256:abc123...

内容:
  learner-profiles/          2 文件
  ability-profiles/          2 文件
  practice-ledgers/          3 文件
  error-summaries/           2 文件
  writing-versions/          1 文件
  strategy-library.json      1 文件
  ability-history.json       1 文件
```

### 2. `backup-metadata.json` 结构

```json
{
  "backup_version": "1.0",
  "created_at": "2026-07-05T14:30:00",
  "total_files": 12,
  "total_size_bytes": 2410000,
  "checksum_sha256": "abc123def456...",
  "exclude_patterns": [".env*", "*private*"],
  "source_data_dir": "./local/data",
  "contents": {
    "learner-profiles/":      {"files": 2, "size_bytes": 4500},
    "ability-profiles/":      {"files": 2, "size_bytes": 8200},
    "practice-ledgers/":      {"files": 3, "size_bytes": 120000},
    "error-summaries/":       {"files": 2, "size_bytes": 34000},
    "writing-versions/":      {"files": 1, "size_bytes": 18000},
    "strategy-library.json":  {"files": 1, "size_bytes": 25000},
    "ability-history.json":   {"files": 1, "size_bytes": 15000}
  }
}
```

### 3. 函数伪代码

```python
# backup_data.py

def create_backup(data_dir: Path, output: Path, exclude: list[str]) -> dict:
    """
    打包 data_dir 下所有非排除文件为 .tar.gz
    """
    import tarfile
    import hashlib

    # 1. 扫描文件
    files = scan_files(data_dir, exclude)

    # 2. 生成 metadata
    metadata = {
        "backup_version": "1.0",
        "created_at": datetime.datetime.now().isoformat(),
        "total_files": len(files),
        "total_size_bytes": sum(f.stat().st_size for f in files),
        "exclude_patterns": exclude,
        "source_data_dir": str(data_dir),
        "contents": build_contents_tree(files, data_dir),
    }

    # 3. 写入 tar.gz
    with tarfile.open(output, "w:gz") as tar:
        # 先写 metadata
        meta_path = data_dir / "backup-metadata.json"
        meta_path.write_text(json.dumps(metadata, indent=2))
        tar.add(meta_path, arcname="backup-metadata.json")

        # 再写数据文件
        for f in files:
            tar.add(f, arcname=f.relative_to(data_dir))

        # 4. 计算校验和
        tar_file_bytes = output.read_bytes()
        metadata["checksum_sha256"] = hashlib.sha256(tar_file_bytes).hexdigest()

    # 5. 清理临时 metadata
    meta_path.unlink()
    return metadata


def restore_backup(input_path: Path, data_dir: Path, force: bool, dry_run: bool) -> dict:
    """
    从 .tar.gz 恢复到指定目录
    """
    import tarfile

    restored = []
    skipped  = []

    with tarfile.open(input_path, "r:gz") as tar:
        # 1. 校验 metadata
        meta_member = tar.getmember("backup-metadata.json")
        if meta_member is None:
            raise BackupError("备份文件缺少 backup-metadata.json，可能已损坏")

        # 2. 提取
        for member in tar.getmembers():
            if member.name == "backup-metadata.json":
                continue

            target = data_dir / member.name
            if target.exists() and not force:
                skipped.append(member.name)
                continue

            if not dry_run:
                tar.extract(member, data_dir)
            restored.append(member.name)

    return {"restored": restored, "skipped": skipped, "dry_run": dry_run}
```

### 4. 涉及文件（精确路径）

```
新增 (3 files):
  skills/examlex/scripts/backup_data.py
  examlex/scripts/backup_data.py   # 镜像
  tests/test_backup_data.py

修改 (1 file):
  examlex/cli.py                    # +2 命令 ("backup", "restore")
```

### 5. CLI 注册（cli.py）

```python
# 在 COMMANDS dict 中追加:
"backup":  ("Backup learner data to a tar.gz archive.", backup_data.backup_main),
"restore": ("Restore learner data from a backup archive.", backup_data.restore_main),
```

### 6. 测试规格

```
tests/test_backup_data.py

class TestBackup:
    def test_create_and_list(self):
        """备份 → --list → 内容一致"""

    def test_restore_roundtrip(self):
        """备份 → 删除原文件 → 恢复 → 文件复原"""

    def test_exclude_patterns(self):
        """--exclude .env → .env 不进入备份"""

    def test_skip_existing_on_restore(self):
        """目标文件存在 → 默认跳过"""

    def test_force_overwrite(self):
        """--force → 覆盖已有文件"""

    def test_dry_run_no_write(self):
        """--dry-run → 报告恢复内容但不实际写入"""

    def test_corrupted_backup_rejected(self):
        """缺少 backup-metadata.json → 恢复失败"""

    def test_checksum_verification(self):
        """备份文件的 checksum_sha256 可验证"""
```

---

## 附录 A：全局常量汇总

所有 P0-P3 新增的 `common.py` 常量一览：

```python
# ========== P0 ==========
VALID_STRATEGY_MODULES = set(ABILITY_TREE.keys())
VALID_STRATEGY_ABILITY_NODES = {
    module: set(nodes) for module, nodes in ABILITY_TREE.items()
}
STRATEGY_ID_PATTERN = re.compile(r"^[a-z]+-[a-z]+-[a-z0-9-]+-\d{3}$")

# ========== P1.1 ==========
EXAM_TYPES = {"CET4", "CET6", "POSTGRADUATE_ENGLISH", "TEM4", "TEM8"}
TEM_TARGET_BANDS = {"60~69", "70~79", "80+"}

# ========== P1.1 (能力树扩展) ==========
# ABILITY_TREE 新增: language-knowledge, proofreading, dictation

# ========== P1.1 (错误标签扩展) ==========
# ERROR_TAG_TO_ABILITY 新增 7 个标签

# ========== P2.1 ==========
EXAM_TIME_LIMITS: dict[str, dict[str, int]] = {...}

# ========== P2.2 ==========
ERROR_SEVERITY_WEIGHTS: dict[str, float] = {...}
REVIEW_URGENCY_THRESHOLD = 0.5

# ========== P1.2 (词汇量) ==========
VOCAB_BANDS = ["1-1000", "1001-2000", "2001-3000", "3001-4000", "4001-6000", "6000+"]
VOCAB_BAND_SIZES = {
    "1-1000": 1000, "1001-2000": 1000, "2001-3000": 1000,
    "3001-4000": 1000, "4001-6000": 2000, "6000+": 4000,
}
VOCAB_TO_FOUNDATION_MAP = {
    (0, 2000):    "基础偏弱",
    (2000, 4000): "中等基础",
    (4000, 99999): "基础较好",
}
```

---

## 附录 B：CLI 命令注册汇总

```python
# examlex/cli.py — COMMANDS dict 最终状态

COMMANDS: dict[str, tuple[str, CommandMain]] = {
    # 现有命令
    "validate-profile":   ("Validate a learner profile.",           validate_profile.main),
    "daily-plan":         ("Generate a constrained daily plan.",    generate_daily_plan.main),
    "record-practice":    ("Append a practice record.",             record_practice.main),
    "tag-error":          ("Infer deterministic error tags.",       tag_error.main),
    "summarize-errors":   ("Summarize error tags.",                 summarize_errors.main),
    "update-ability":     ("Update an ability profile.",            update_ability_profile.main),
    "writing-version":    ("Append a writing draft version.",       manage_writing_versions.main),
    "score-writing":      ("Score a writing draft.",                score_writing_rubric.main),
    "analyze-trends":     ("Analyze practice and ability trends.",  analyze_trends.main),

    # P0
    "validate-strategy":  ("Validate a strategy library file.",     validate_strategy.main),

    # P1.2
    "vocab-estimate":     ("Estimate vocabulary size via sampling.", estimate_vocabulary.main),

    # P3.1
    "visualize":          ("Generate progress visualization HTML.", visualize_progress.main),

    # P3.3
    "backup":             ("Backup learner data to tar.gz.",        backup_data.backup_main),
    "restore":            ("Restore learner data from backup.",     backup_data.restore_main),
}
```

---

## 附录 C：测试用例汇总

| 优先级 | 测试文件 | 用例数（预估） |
|:------:|---------|:------------:|
| P0 | `test_validate_strategy.py` | 12 |
| P1.1 | `test_tem_support.py` | 9 |
| P1.2 | `test_estimate_vocabulary.py` | 7 |
| P1.3 | `test_vocab_pool.py` | 6 |
| P2.1 | `test_timed_practice.py` | 5 |
| P2.2 | `test_spaced_review.py` | 7 |
| P2.3 | `test_common_errors_library.py` | 3 |
| P3.1 | `test_visualize_progress.py` | 7 |
| P3.2 | `test_sample_essays.py` | 6 |
| P3.3 | `test_backup_data.py` | 8 |
| **合计** | — | **70** |

---

## 附录 D：实施顺序与依赖关系

```
第 1 周
├── P0 策略库校验 (0.5天) ← 无依赖，立刻能做
├── P1.3 预置词汇库 (3天) ← 无依赖，纯数据文件
└── P1.2 词汇量估算 (1天)  ← 依赖 P1.3（需词表做测试词）

第 2 周
├── P1.2 词汇量估算 (1天收尾)
├── P1.1 专四/专八 (2天)   ← 依赖 P0（common.py 已稳定）
└── P2.3 常见错误库 (1天)   ← 无代码依赖，纯数据

第 3 周
├── P2.3 常见错误库 (1天收尾)
├── P2.1 计时训练 (1.5天)   ← 依赖 P1.1（EXAM_TIME_LIMITS 含 TEM）
└── P2.2 间隔复习 (1天)     ← 依赖 P2.1（summarize_errors 已扩展）

第 4 周
├── P3.3 数据备份 (1天)     ← 无依赖
└── P3.2 作文范文库 (3天)   ← 纯数据，无依赖

第 5 周
└── P3.2 作文范文库 (收尾)

第 6 周
├── P3.1 进度可视化 (3天)   ← 依赖 P1.1 + P2.1 + P2.2（所有数据格式已稳定）
└── 整体回归测试 (2天)
```

### 依赖图

```
                    ┌─────────────────┐
                    │  P0 策略库校验    │ ← 无依赖
                    └────────┬────────┘
                             │ common.py 稳定后
                    ┌────────▼────────┐
                    │  P1.1 专四/专八   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │ P2.1 计时   │  │ P2.2 间隔   │  │ P3.1 可视化  │
     │ (依赖P1.1)  │  │ (依赖P2.1)  │  │ (依赖全部)   │
     └────────────┘  └────────────┘  └────────────┘

P1.3 预置词汇库 ← 无依赖
P1.2 词汇量估算 ← 依赖 P1.3
P2.3 常见错误库 ← 无依赖
P3.2 作文范文库 ← 无依赖
P3.3 数据备份   ← 无依赖
```
