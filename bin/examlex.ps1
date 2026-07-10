# ============================================================
# examlex.ps1 — ExamLex 统一命令行入口 (PowerShell)
#
# 用法: .\examlex.ps1 <命令> [参数...]
# 运行 .\examlex.ps1 -Help 查看所有命令
# ============================================================
param(
    [Parameter(Position=0)]
    [string]$Command,

    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$PythonCmd = if ($env:EXAMLEX_PYTHON) { $env:EXAMLEX_PYTHON } else { "python" }
$CliEntry = "examlex"

function Show-Help {
    @"
英语考试 AI 助教 — 命令行工具 (PowerShell)

用法: .\examlex.ps1 <命令> [参数...]

📋 备考闭环（按工作流顺序）
  check    <档案>              校验学习者档案
  plan     <档案> [选项]         生成每日计划
  log      <台账> [选项]         记录练习数据
  tag      <错误文本> [选项]      错误标签归因
  errors   <台账> [选项]         汇总错误统计
  update   <画像> <台账>         更新能力画像
  trends   <台账> [选项]         分析练习趋势
  write    <作文ID> [选项]       作文版本管理
  score    <作文> [选项]         作文评分估算

📥 知识管理
  ingest   <文件> [选项]         摄入策略到策略库
  strategies [选项]              列出/搜索策略库

💾 数据管理
  backup   <数据目录> [选项]      备份学习数据
  restore  <备份文件> <目录>      恢复学习数据
  report   [选项]                生成进度可视化报告

📊 词汇
  vocab    [选项]                词汇量抽样估算

示例:
  .\examlex.ps1 check learner-profile.json
  .\examlex.ps1 plan learner-profile.json --ability ability-profile.json
  .\examlex.ps1 errors practice-ledger.json --output errors.json
  .\examlex.ps1 backup .\local\data --output backup-2026-07-05.tar.gz
  .\examlex.ps1 report --ledger practice-ledger.json --ability ability-history.json

注意:
  大多数情况下不需要手动运行——在 Agent 对话中说自然语言即可。
  此 CLI 主要用于调试、脚本集成和脱离 Agent 的独立使用。
"@
}

function Invoke-ExamLex {
    Set-Location $ProjectRoot
    & $PythonCmd -m $CliEntry @Args
}

# 主入口
if (-not $Command -or $Command -eq "--help" -or $Command -eq "-h" -or $Command -eq "-Help") {
    Show-Help
    exit 0
}

$RemainingArgs = $Args

switch ($Command) {
    # 备考闭环 — 别名命令走 cli.py ALIASES 以触发选项预添加
    "check"    { Invoke-ExamLex check @RemainingArgs }
    "plan"     { Invoke-ExamLex plan @RemainingArgs }
    "log"      { Invoke-ExamLex log @RemainingArgs }
    "tag"      { Invoke-ExamLex tag @RemainingArgs }
    "errors"   { Invoke-ExamLex errors @RemainingArgs }
    "update"   { Invoke-ExamLex update @RemainingArgs }
    "trends"   { Invoke-ExamLex trends @RemainingArgs }
    "write"    { Invoke-ExamLex write @RemainingArgs }
    "score"    { Invoke-ExamLex score @RemainingArgs }

    # 知识管理
    "ingest"     { Invoke-ExamLex ingest @RemainingArgs }
    "strategies" { Invoke-ExamLex strategies @RemainingArgs }
    "extract"    { Invoke-ExamLex extract @RemainingArgs }
    "validate"   { Invoke-ExamLex validate-strategies @RemainingArgs }
    "commit"     { Invoke-ExamLex commit-strategies @RemainingArgs }
    "check-deps" { Invoke-ExamLex check-deps @RemainingArgs }
    "ops-check"  { Invoke-ExamLex ops-check @RemainingArgs }

    # 数据管理
    "backup"   { Invoke-ExamLex backup @RemainingArgs }
    "restore"  { Invoke-ExamLex restore @RemainingArgs }
    "report"   { Invoke-ExamLex visualize @RemainingArgs }

    # 词汇
    "vocab"    { Invoke-ExamLex vocab-estimate @RemainingArgs }

    # 直通模式
    default    { Invoke-ExamLex $Command @RemainingArgs }
}
