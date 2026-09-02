# ExamLex Web Workspace Implementation

状态：Local-first MVP implemented

## Implemented tracks

考试顺序固定为 `CET4 -> CET6 -> POSTGRADUATE_ENGLISH -> TEM4 -> TEM8`。
CET-4/CET-6 使用用户资料整理后的详细内容草稿；考研英语、TEM-4、TEM-8
保留完整功能入口与官方题型框架，并明确标记为 `foundation_release`。

## Implemented workflow

- 学习档案：考试、目标分数、基础和每日时间预算。
- 今日计划：复用 ExamLex `generate_daily_plan`，接收能力、错误和已批准策略。
- 五项学习与基础知识：写作、听力、阅读、翻译、词汇；词性、句型、语音。
- 学习热力图：默认自然月，按年月查询并保留历史；颜色依据明确的 activity score。
- Practice evidence：练习题数、正确数、耗时和错误标签。
- Memory Ribbon：可拖动查看练习、错误和复习结点。
- 错误复盘、结点分析、趋势与能力变化。
- Ebbinghaus 记忆卡：Again / Hard / Good / Easy 与幂等 review event。
- 上传隔离与主题路由；Provider 配置只保存环境变量名，不保存原始密钥。
- 健康检查；source collection、视频处理和备份恢复保留为后台能力。

## Upload routing

路由优先使用文件主题，再使用可提取内容中的强主题短语：

- 历年真题 -> `candidate_official_past_paper`，必须经过题目级来源核验。
- 模拟题 -> `simulation_not_official`，仅进入私有模拟训练。
- 作文金句、模板、范文 -> `writing_content`。
- 翻译常用词语、句子和表达 -> `translation_content`。
- 听力、阅读、词汇资料 -> 对应模块的 draft queue。
- 方法论 -> ExamLex continuous learning 的 `extract -> distill -> validate -> commit` 队列。

零散句子或词语没有明确文件主题时不会猜测板块，而是进入人工确认。

## Safety boundaries

- Web 服务默认仅监听 `127.0.0.1`，静态资源与 API 同源。
- 上传限制扩展名、请求大小、解压预览大小和目标路径，文件只进入 quarantine。
- 私有 OCR 索引和用户原始教材不在静态目录内，也不复制到公开仓库。
- OCR 或用户资料整理内容在人工复核前保持 draft；真题和模拟题来源状态不可混淆。
- 页面发送 CSP、`nosniff` 和禁止 frame embedding 响应头。
