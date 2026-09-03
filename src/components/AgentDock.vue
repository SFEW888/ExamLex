<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { BookOpen, Send, Sparkles, X } from '@lucide/vue'

type ModelCapability = { id: string; label: string; level: string; provider?: string | null; model?: string | null; available: boolean; description: string }
type AgentRun = { module: string; mode: string; provider?: string | null; model?: string | null; output?: { findings?: string[]; next_action?: string; evidence?: unknown[] }; rag?: { results?: Array<{ source_id: string; title: string; source_status: string; source_type: string; snippet: string }> }; errors?: string[] }

const route = useRoute()
const EXAM_IDS = ['CET4', 'CET6', 'POSTGRADUATE_ENGLISH', 'TEM4', 'TEM8']
const open = ref(false)
const input = ref('')
const busy = ref(false)
const result = ref<AgentRun | null>(null)
const initialExam = String(route.query.exam || localStorage.getItem('examlex-active-exam') || 'CET4')
const exam = ref(EXAM_IDS.includes(initialExam) ? initialExam : 'CET4')
const agentMode = ref('global')
const selectedModelId = ref('offline')
const capabilities = ref<ModelCapability[]>([{ id: 'offline', label: 'ExamLex 本地模式', level: '基础', available: true, description: '无需密钥，使用本地证据检索和确定性教练规则。' }])

const modeOptions = [
  { id: 'global', label: '全局模式', description: '根据当前页面和你的问题自动选择专项 Agent。' },
  { id: 'writing', label: '写作模式', description: '审题、结构、论证、表达与二次写作。' },
  { id: 'listening', label: '听力模式', description: '关键词、转折、语音现象、精听与听写。' },
  { id: 'reading', label: '阅读模式', description: '定位证据、同义替换、干扰项与错因。' },
  { id: 'translation', label: '翻译模式', description: '信息分块、句法转换、搭配与漏译诊断。' },
  { id: 'vocabulary', label: '词汇模式', description: '词性、义项、搭配、易混词与真题语境。' }
]

const scene = computed(() => {
  const module = String(route.params.module || '').toLowerCase()
  if (['writing', 'listening', 'reading', 'translation', 'vocabulary', 'basics'].includes(module)) return module
  if (route.path.includes('error-book')) return 'error_review'
  if (route.path.includes('pomodoro') || route.path.includes('daily-summary') || route.path === '/' || route.path === '/english') return 'planner'
  return 'planner'
})
const sceneLabel = computed(() => ({ writing: '写作', listening: '听力', reading: '阅读', translation: '翻译', vocabulary: '词汇', basics: '基础知识', error_review: '错题复盘', planner: '学习规划' } as Record<string, string>)[scene.value] || '学习助手')
const activeModule = computed(() => agentMode.value === 'global' ? scene.value : agentMode.value)
const activeMode = computed(() => modeOptions.find(item => item.id === agentMode.value) || modeOptions[0])
const selectedCapability = computed(() => capabilities.value.find(item => item.id === selectedModelId.value) || capabilities.value[0])
const hasConfiguredModel = computed(() => selectedCapability.value?.id !== 'offline' && !!selectedCapability.value?.available)
const activeLabel = computed(() => agentMode.value === 'global' ? sceneLabel.value : activeMode.value.label.replace('模式', ''))

async function loadCapabilities() {
  try {
    const payload = await fetch('/api/agent/manifest').then(response => response.ok ? response.json() : null)
    if (payload?.capabilities?.models?.length) capabilities.value = payload.capabilities.models
  } catch { /* offline frontend still keeps local mode */ }
}

async function run() {
  if (!input.value.trim() || busy.value) return
  busy.value = true; result.value = null
  const capability = selectedCapability.value
  try {
    const response = await fetch('/api/agent/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ exam: exam.value, module: activeModule.value, path: route.path, input: input.value.trim(), use_model: hasConfiguredModel.value, provider: capability.provider, model: capability.model }),
    })
    const payload = await response.json()
    if (!response.ok) throw new Error(payload.error || 'Agent 运行失败')
    result.value = payload.run
  } catch (error: any) {
    result.value = { module: scene.value, mode: 'error', output: { findings: [error?.message || 'Agent 运行失败'] } }
  } finally { busy.value = false }
}

function onShortcut(event: KeyboardEvent) {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'j') { event.preventDefault(); open.value = true }
}

watch(() => route.path, () => { result.value = null })
watch(() => route.query.exam, value => {
  const next = String(value || '')
  if (EXAM_IDS.includes(next) && next !== exam.value) exam.value = next
})
watch(exam, value => localStorage.setItem('examlex-active-exam', value))
onMounted(() => { loadCapabilities(); window.addEventListener('keydown', onShortcut) })
onBeforeUnmount(() => window.removeEventListener('keydown', onShortcut))
</script>

<template>
  <div class="fixed bottom-20 md:bottom-5 right-4 z-40 flex flex-col items-end gap-2" data-testid="global-agent">
    <section v-if="open" class="w-[min(400px,calc(100vw-2rem))] card shadow-xl border-primary-200 dark:border-primary-800" role="dialog" aria-label="ExamLex 全局 AI 助手">
      <header class="flex items-start justify-between gap-3 mb-3">
        <div class="flex items-center gap-2">
          <span class="w-8 h-8 rounded-lg bg-primary-100 dark:bg-primary-900/40 text-primary-600 flex items-center justify-center"><Sparkles :size="16" /></span>
          <div><div class="section-title !mb-0">ExamLex AI 助手</div><div class="text-[10px] text-slate-400">{{ sceneLabel }}场景 · Ctrl/⌘ + J 唤醒</div></div>
        </div>
        <button class="btn-ghost !p-1.5" aria-label="关闭 AI 助手" @click="open = false"><X :size="15" /></button>
      </header>

      <div class="grid grid-cols-2 gap-2 mb-2">
        <label class="text-[10px] text-slate-400">考试
          <select v-model="exam" class="input !py-1.5 !text-xs mt-1"><option>CET4</option><option>CET6</option><option>POSTGRADUATE_ENGLISH</option><option>TEM4</option><option>TEM8</option></select>
        </label>
        <label class="text-[10px] text-slate-400">助手模式
          <select v-model="agentMode" class="input !py-1.5 !text-xs mt-1">
            <option v-for="item in modeOptions" :key="item.id" :value="item.id">{{ item.label }}</option>
          </select>
        </label>
      </div>
      <p class="text-[10px] text-slate-400 mb-2">{{ activeMode.description }} 当前模型：{{ selectedCapability.label }}。RAG 会优先检索教材、基础知识、练习、记忆卡和上传资料。</p>
      <label class="text-[10px] text-slate-400 block mb-2">模型能力
        <select v-model="selectedModelId" class="input !py-1.5 !text-xs mt-1"><option v-for="item in capabilities" :key="item.id" :value="item.id">{{ item.label }} · {{ item.available ? '可用' : '未配置' }}</option></select>
      </label>
      <div v-if="!hasConfiguredModel" class="rounded-lg bg-amber-50 dark:bg-amber-900/20 px-3 py-2 text-[10px] text-amber-700 dark:text-amber-300">未接入可用模型，当前使用本地 RAG。要使用模型能力，请到设置配置 Provider 和环境变量。</div>
      <textarea v-model="input" class="input min-h-24 resize-y !text-xs" :placeholder="`输入${activeLabel}材料、作答或错题，助手会先找证据再分析`" @keydown.ctrl.enter="run" @keydown.meta.enter="run"></textarea>
      <button class="btn-primary w-full mt-2 !text-xs" :disabled="busy || !input.trim()" @click="run"><Send :size="14" />{{ busy ? '检索并分析中…' : `分析${activeLabel}` }}</button>

      <div v-if="result" class="mt-3 pt-3 border-t border-slate-100 dark:border-slate-700 text-xs">
        <div class="flex items-center justify-between mb-1"><span class="font-semibold">{{ result.mode === 'model' ? '模型分析' : '本地证据分析' }}</span><span v-if="result.rag" class="text-[10px] text-slate-400">检索 {{ result.rag.results?.length || 0 }} 条</span></div>
        <ul class="list-disc pl-4 space-y-1"><li v-for="item in result.output?.findings || []" :key="item">{{ item }}</li></ul>
        <p v-if="result.output?.next_action" class="mt-2"><b>下一步：</b>{{ result.output.next_action }}</p>
        <div v-if="result.rag?.results?.length" class="mt-3 space-y-1.5">
          <div class="flex items-center gap-1 text-[10px] text-slate-400"><BookOpen :size="12" />证据来源</div>
          <div v-for="source in result.rag.results.slice(0, 4)" :key="source.source_id" class="rounded-lg bg-slate-50 dark:bg-slate-700/50 px-2 py-1.5">
            <div class="font-medium text-[11px]">{{ source.title }}</div><div class="text-[10px] text-slate-400 line-clamp-2">{{ source.snippet }}</div>
            <div class="text-[9px] text-slate-400 mt-0.5">{{ source.source_type }} · {{ source.source_status }}</div>
          </div>
        </div>
      </div>
    </section>
    <button class="w-12 h-12 rounded-full shadow-lg bg-primary-500 text-white flex items-center justify-center hover:bg-primary-600 focus:ring-2 focus:ring-primary-300" :aria-expanded="open" aria-label="打开 ExamLex 全局 AI 助手" title="ExamLex AI 助手（Ctrl/⌘+J）" @click="open = !open"><Sparkles :size="19" /></button>
  </div>
</template>
