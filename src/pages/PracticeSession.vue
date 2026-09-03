<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const exam = String(route.query.exam || 'CET4')
const kind = String(route.query.kind || 'mock')
const module = String(route.query.module || 'reading')
const sourceId = String(route.query.source_id || '')
const questionCount = Number(route.query.question_count || 5)
const difficulty = String(route.query.difficulty || 'standard')
const focus = String(route.query.focus || '')
const session = ref<any>(null)
const answers = ref<Record<string, string>>({})
const result = ref<any>(null)
const loading = ref(true)
const message = ref('')
const showExamNotice = ref(false)
const elapsed = ref(0)
const timedOut = ref(false)
const overtime = ref(false)
let timer: ReturnType<typeof setInterval> | null = null
const moduleLabels: Record<string, string> = { writing: '写作', listening: '听力', reading: '阅读', translation: '翻译', vocabulary: '词汇', basics: '基础知识', full_paper: '整卷' }
const timeText = computed(() => { const value = elapsed.value; const h = Math.floor(value / 3600); const m = Math.floor(value % 3600 / 60); const s = value % 60; return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}` })
const remainingText = computed(() => { const left = Math.max(0, Number(session.value?.limit_seconds || 0) - elapsed.value); const m = Math.floor(left / 60); const s = left % 60; return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}` })

async function create() {
  try {
    const response = await fetch('/api/practice/session', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ exam, kind, module, source_id: sourceId, question_count: questionCount, difficulty, focus }) })
    const payload = await response.json()
    if (!response.ok) throw new Error(payload.error || '无法创建练习')
    session.value = payload.session
    showExamNotice.value = session.value.timer_mode === 'countdown'
    if (!showExamNotice.value) startTimer()
  } catch (error: any) { message.value = error?.message || '无法创建练习' }
  finally { loading.value = false }
}
function beginExam() {
  showExamNotice.value = false
  startTimer()
}
function startTimer() {
  if (timer) clearInterval(timer)
  timer = setInterval(() => {
    elapsed.value += 1
    if (session.value?.timer_mode === 'countdown' && elapsed.value >= Number(session.value.limit_seconds || 0) && !timedOut.value && !result.value) {
      timedOut.value = true
      if (timer) clearInterval(timer)
    }
  }, 1000)
}
async function continueAfterTimeout() {
  overtime.value = true
  timedOut.value = false
  const response = await fetch('/api/practice/session/timeout', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: session.value.id, overtime_seconds: Math.max(0, elapsed.value - Number(session.value.limit_seconds || 0)) }) })
  const payload = await response.json()
  if (!response.ok) { message.value = payload.error || '无法继续答题'; return }
  startTimer()
}
async function submit() {
  if (!session.value || result.value) return
  if (timer) clearInterval(timer)
  const response = await fetch('/api/practice/session/submit', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: session.value.id, answers: answers.value }) })
  const payload = await response.json()
  if (!response.ok) { message.value = payload.error || '提交失败'; return }
  result.value = payload.result
  session.value = payload.session
  timedOut.value = false
}
onMounted(create)
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="p-4 md:p-6 max-w-4xl mx-auto space-y-4">
    <header class="flex items-end justify-between gap-3 flex-wrap"><div><div class="text-xs tracking-[0.18em] text-slate-400 uppercase">ExamLex · practice session</div><h1 class="page-title mt-1">{{ moduleLabels[module] || module }}训练</h1><p class="text-sm text-slate-500 dark:text-slate-400 mt-1">{{ kind === 'past' ? '来源已核验的官方真题' : kind === 'ai' ? 'AI 生成模拟题 · 非官方' : kind === 'module' ? '英语专项训练' : session?.source_status === 'learner_practice' ? '上传专项试题 · 已通过解析校验' : '上传模拟题 · 非官方' }}</p></div><button class="btn-ghost" @click="router.back()">返回</button></header>
    <div v-if="message" class="rounded-lg bg-amber-50 text-amber-700 px-3 py-2 text-xs">{{ message }}</div>
    <div v-if="loading" class="card py-12 text-center text-sm text-slate-400">正在准备题目…</div>
    <div v-if="showExamNotice" class="card border-primary-200 bg-primary-50 dark:bg-primary-900/20"><div class="font-semibold text-primary-700 dark:text-primary-300">整卷考试即将开始</div><p class="text-xs text-primary-700/80 dark:text-primary-200 mt-1">本试卷按 {{ Math.floor(Number(session.limit_seconds || 0) / 60) }} 分钟倒计时。时间到后答题会暂停，你可以结束考试并交卷，或继续答题并统计超时时间。</p><button class="btn-primary mt-3" type="button" @click="beginExam">开始考试</button></div>
    <template v-else-if="session && !result && !timedOut">
      <div class="card flex items-center justify-between gap-3 sticky top-2 z-10"><div class="text-xs text-slate-500">{{ session.module === 'full_paper' ? '整卷考试 · ' : '' }}{{ session.source_status }}</div><div class="text-right"><div class="text-[10px] text-slate-400">{{ session.timer_mode === 'countdown' && !overtime ? '剩余时间' : overtime ? '超时计时' : '用时' }}</div><div class="font-mono font-bold" :class="session.timer_mode === 'countdown' && elapsed >= session.limit_seconds ? 'text-rose-500' : 'text-primary-500'">{{ session.timer_mode === 'countdown' && !overtime ? remainingText : timeText }}</div></div></div>
      <div v-for="(question, index) in session.questions" :key="question.id" class="card space-y-3"><div class="text-sm font-semibold">{{ index + 1 }}. {{ question.prompt }}</div><div v-if="question.options?.length" class="grid sm:grid-cols-2 gap-2"><label v-for="(option, optionIndex) in question.options" :key="option" class="flex items-center gap-2 rounded-lg border border-slate-200 dark:border-slate-700 px-3 py-2 text-sm cursor-pointer"><input v-model="answers[question.id]" type="radio" :name="question.id" :value="optionIndex" />{{ option }}</label></div><textarea v-else v-model="answers[question.id]" rows="3" class="input" placeholder="输入你的答案…"></textarea></div>
      <button class="btn-primary w-full" @click="submit">提交并自动批改</button>
    </template>
    <div v-if="timedOut" class="card border-rose-200 bg-rose-50 dark:bg-rose-900/20"><div class="font-semibold text-rose-700 dark:text-rose-300">考试时间已到</div><p class="text-xs text-rose-600 dark:text-rose-300 mt-1">答题页面已暂停。结束考试会立即交卷并由 AI 批改；继续答题将切换为正计时并记录超时时间。</p><div class="flex gap-2 mt-3"><button class="btn-primary" @click="submit">结束考试并交卷</button><button class="btn-ghost" @click="continueAfterTimeout">继续答题</button></div></div>
    <template v-if="result"><div class="card border-emerald-200"><div class="flex items-center justify-between"><h2 class="section-title !mb-0">批改结果</h2><strong class="text-emerald-600">{{ result.correct }}/{{ result.total }} · {{ result.accuracy }}%</strong></div><div v-for="(item, index) in result.feedback" :key="item.question_id" class="border-t border-slate-100 dark:border-slate-700 mt-3 pt-3 text-sm"><div>{{ index + 1 }}. <span :class="item.correct ? 'text-emerald-600' : 'text-rose-600'">{{ item.correct ? '正确' : '需复盘' }}</span></div><p class="text-xs text-slate-500 mt-1">{{ item.explanation }}</p></div><button class="btn-primary w-full mt-4" @click="router.push('/error-book')">查看错题本</button></div></template>
  </div>
</template>
