<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { AlertTriangle, ArrowRight, FileCheck2, FileText, RefreshCw, ShieldCheck, Upload, Sparkles, Workflow } from '@lucide/vue'
import { useAppStore } from '../stores/app'
import Modal from '../components/Modal.vue'

type LibraryKind = 'past' | 'mock'
type UploadItem = { id?: string; upload_id?: string; filename?: string; title?: string; category?: string; status?: string; source_status?: string; created_at?: string; size_bytes?: number; module?: string; pipeline_stage?: string }

const props = defineProps<{ kind: LibraryKind }>()
const store = useAppStore()
const router = useRouter()
const exam = ref(localStorage.getItem('examlex-active-exam') || 'CET4')
const exams = ref<{ id: string; title: string; short_title?: string }[]>([])
const uploads = ref<UploadItem[]>([])
const candidates = ref<UploadItem[]>([])
const simulations = ref<UploadItem[]>([])
const pipelines = ref<any[]>([])
const loading = ref(true)
const uploading = ref(false)
const message = ref('')
const fileInput = ref<HTMLInputElement>()
const showAiGenerator = ref(false)
const aiForm = ref({ module: 'reading', difficulty: 'standard', questionCount: 5, focus: '' })
const showVerify = ref(false)
const verifyTarget = ref<UploadItem | null>(null)
const verifyForm = ref({ sourceName: '', sourceUrl: '', note: '' })

const isPast = computed(() => props.kind === 'past')
const title = computed(() => isPast.value ? '历年真题' : '模拟特训')
const subtitle = computed(() => isPast.value
  ? '只进入来源已核验的官方题目；上传材料先隔离，核验前不会发布为真题。'
  : '上传题目或使用 ExamLex 生成的训练材料，所有内容明确标记为非官方模拟。')
const recordedExams = computed(() => store.exams.filter(item => item.subjectId === 'english').slice().reverse())

async function load() {
  loading.value = true
  message.value = ''
  try {
    const [directory, library] = await Promise.all([
      fetch('/api/exams').then(r => r.ok ? r.json() : null),
      fetch(`/api/uploads?exam=${encodeURIComponent(exam.value)}`).then(r => r.ok ? r.json() : null)
    ])
    if (directory?.exams) exams.value = directory.exams
    uploads.value = library?.uploads || []
    candidates.value = library?.past_paper_candidates || []
    simulations.value = library?.simulations || []
    pipelines.value = library?.pipelines || []
  } catch {
    message.value = '本地题源服务暂不可用，仍可查看已记录的学习结果。'
  } finally { loading.value = false }
}

function pipelineFor(uploadId?: string) {
  return pipelines.value.find(item => item.upload_id === uploadId)
}

async function runPipeline(uploadId?: string) {
  if (!uploadId) return
  message.value = ''
  try {
    const response = await fetch('/api/pipeline/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ upload_id: uploadId, action: 'auto' }) })
    const payload = await response.json()
    if (!response.ok) throw new Error(payload.error || 'pipeline 执行失败')
    message.value = payload.pipeline?.current_stage === 'complete' ? '资料已完成校验并提交到对应队列。' : (payload.pipeline?.errors?.[0] || '资料已推进到下一处理阶段。')
    await load()
  } catch (error: any) { message.value = error?.message || 'pipeline 执行失败' }
}

function openVerify(item: UploadItem) {
  verifyTarget.value = item
  verifyForm.value = { sourceName: '', sourceUrl: '', note: '' }
  showVerify.value = true
}

async function verifyPastPaper() {
  const uploadId = verifyTarget.value?.upload_id
  if (!uploadId || !verifyForm.value.sourceName.trim()) return
  try {
    const response = await fetch('/api/pipeline/verify', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ upload_id: uploadId, evidence_level: 'S', source_name: verifyForm.value.sourceName.trim(), source_url: verifyForm.value.sourceUrl.trim(), note: verifyForm.value.note.trim() }) })
    const payload = await response.json()
    if (!response.ok) throw new Error(payload.error || '来源核验失败')
    showVerify.value = false
    message.value = '来源已记录，继续推进 pipeline 后才会进入真题训练。'
    await load()
  } catch (error: any) { message.value = error?.message || '来源核验失败' }
}

async function uploadFile(file?: File) {
  if (!file || uploading.value) return
  uploading.value = true
  message.value = ''
  try {
    const body = new FormData()
    body.append('file', file)
    const response = await fetch(`/api/upload?exam=${encodeURIComponent(exam.value)}`, { method: 'POST', body })
    const payload = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(payload.error || '上传失败')
    message.value = `${file.name} 已进入隔离解析队列，等待分类确认。`
    await load()
  } catch (error: any) {
    message.value = error?.message || '上传失败，请重试。'
  } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

function onFileChange(event: Event) {
  uploadFile((event.target as HTMLInputElement).files?.[0])
}

function startSession(kind: string, module = 'reading', sourceId = '', options: Record<string, string> = {}) {
  router.push({ path: '/practice/session', query: { exam: exam.value, kind, module, source_id: sourceId, ...options } })
}

function openAiGenerator() {
  aiForm.value = { module: 'reading', difficulty: 'standard', questionCount: 5, focus: '' }
  showAiGenerator.value = true
}

function generateSimulation() {
  showAiGenerator.value = false
  startSession('ai', aiForm.value.module, '', {
    question_count: String(Math.min(20, Math.max(1, aiForm.value.questionCount))),
    difficulty: aiForm.value.difficulty,
    focus: aiForm.value.focus.trim()
  })
}

onMounted(load)
watch(exam, load)
watch(exam, value => localStorage.setItem('examlex-active-exam', value))
watch(() => props.kind, load)
</script>

<template>
  <div class="p-4 md:p-6 max-w-6xl mx-auto space-y-4">
    <header class="flex items-end justify-between gap-4 flex-wrap">
      <div>
        <div class="text-xs tracking-[0.18em] text-slate-400 uppercase">ExamLex · practice library</div>
        <h1 class="page-title mt-1">{{ title }}</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-2 max-w-2xl">{{ subtitle }}</p>
      </div>
      <label class="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">考试
        <select v-model="exam" class="input !w-auto min-w-32 !py-1.5">
          <option v-for="item in exams" :key="item.id" :value="item.id">{{ item.short_title || item.title }}</option>
          <option v-if="!exams.length" value="CET4">CET-4</option>
        </select>
      </label>
    </header>

    <div v-if="message" class="rounded-xl border border-sky-100 bg-sky-50 px-4 py-3 text-xs text-sky-700 dark:border-sky-900/50 dark:bg-sky-900/20 dark:text-sky-300">{{ message }}</div>

    <section v-if="isPast" class="card border-l-4 border-l-emerald-500 space-y-3">
      <div class="flex items-start gap-3">
        <ShieldCheck class="text-emerald-500 shrink-0" :size="20" />
        <div>
          <h2 class="section-title !mb-1">官方来源边界</h2>
          <p class="text-xs text-slate-500 dark:text-slate-400 leading-6">真题可以上传，但上传后先进入隔离解析和来源核验队列。只有核验通过的题目才会进入官方真题练习，系统不会把用户资料或 AI 内容伪装成真题。</p>
        </div>
      </div>
      <div class="flex items-center justify-between gap-3 flex-wrap border-t border-slate-100 dark:border-slate-700 pt-3">
        <div class="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400"><Upload :size="16" class="text-emerald-500" />上传历年真题文件，等待核验后入库</div>
        <button class="btn-primary shrink-0" :disabled="uploading" @click="fileInput?.click()"><Upload :size="15" />{{ uploading ? '解析中…' : '上传真题' }}</button>
      </div>
    </section>

    <section v-if="!isPast" class="card flex items-center justify-between gap-4 flex-wrap">
      <div class="flex items-start gap-3">
        <Upload class="text-primary-500 shrink-0" :size="20" />
        <div><h2 class="section-title !mb-1">加入模拟材料</h2><p class="text-xs text-slate-500 dark:text-slate-400">支持 PDF、Word、Excel、TXT、Markdown 和图片；文件会先隔离解析，再进入模拟队列。</p></div>
      </div>
      <div class="flex gap-2"><button class="btn-primary shrink-0" @click="openAiGenerator"><Sparkles :size="15" />AI 生成模拟题</button><button class="btn-ghost shrink-0" :disabled="uploading" @click="fileInput?.click()"><Upload :size="15" />{{ uploading ? '解析中…' : '上传模拟题' }}</button></div>
    </section>

    <section v-if="loading" class="card py-12 text-center text-sm text-slate-400"><RefreshCw class="animate-spin inline-block mr-2" :size="15" />正在读取题源…</section>

    <template v-else-if="isPast">
      <section class="card space-y-3">
        <div class="flex items-center gap-2"><FileCheck2 class="text-emerald-500" :size="18" /><h2 class="section-title !mb-0">已记录的真题成绩</h2><span class="text-xs text-slate-400">{{ recordedExams.length }} 条</span></div>
        <div v-if="!recordedExams.length" class="py-8 text-center text-xs text-slate-400">暂无真题成绩记录。完成一套官方真题后，可在英语专项中记录成绩。</div>
        <div v-for="item in recordedExams" :key="item.id" class="flex items-center gap-3 border-t border-slate-100 dark:border-slate-700 py-3 text-sm">
          <FileText class="text-slate-400 shrink-0" :size="16" /><span class="flex-1 truncate">{{ item.title }}</span><span class="font-semibold">{{ item.score }}/{{ item.totalScore }}</span><span class="text-xs text-slate-400">{{ item.date }}</span>
        </div>
      </section>
      <section v-if="candidates.length" class="card space-y-3">
        <div class="flex items-center gap-2"><AlertTriangle class="text-amber-500" :size="18" /><h2 class="section-title !mb-0">待核验题源</h2><span class="text-xs text-amber-600">不可作为官方真题</span></div>
        <div v-for="item in candidates" :key="item.id" class="flex items-center gap-3 border-t border-slate-100 dark:border-slate-700 py-3 text-sm"><FileText class="text-slate-400" :size="16" /><span class="flex-1 truncate">{{ item.filename || item.title || '未命名文件' }}</span><span class="text-xs text-amber-600">{{ item.status === 'verified_official' ? '已核验' : '待核验' }}</span><button v-if="item.status !== 'verified_official'" class="btn-ghost !py-1 !text-xs" @click="openVerify(item)">来源核验</button><button class="btn-primary !py-1 !text-xs" :disabled="item.status !== 'verified_official'" @click="startSession('past', item.module || 'reading', item.id)">开始真题</button></div>
      </section>
    </template>

    <template v-else>
      <section class="card space-y-3">
        <div class="flex items-center gap-2"><FileText class="text-primary-500" :size="18" /><h2 class="section-title !mb-0">模拟特训队列</h2><span class="text-xs text-slate-400">{{ simulations.length }} 份</span></div>
        <div v-if="!simulations.length" class="py-8 text-center text-xs text-slate-400">暂无模拟题。上传文件后会出现在这里，并标记为“非官方模拟”。</div>
        <div v-for="item in simulations" :key="item.id" class="flex items-center gap-3 border-t border-slate-100 dark:border-slate-700 py-3 text-sm"><FileText class="text-slate-400 shrink-0" :size="16" /><span class="flex-1 truncate">{{ item.filename || item.title || '未命名模拟题' }}</span><span class="rounded-full bg-violet-50 px-2 py-1 text-[10px] text-violet-600 dark:bg-violet-900/30 dark:text-violet-300">非官方模拟</span><span v-if="item.status !== 'ready_private'" class="text-[10px] text-amber-600">{{ item.status || '待处理' }}</span><button v-if="item.status !== 'ready_private'" class="btn-ghost !py-1 !text-xs" @click="runPipeline(item.upload_id)"><Workflow :size="13" />推进解析</button><button class="btn-primary !py-1 !text-xs" :disabled="item.status !== 'ready_private'" @click="startSession('upload', item.module || 'reading', item.id)">开始训练</button><ArrowRight class="text-slate-300" :size="15" /></div>
      </section>
      <section v-if="uploads.length" class="card space-y-2"><h2 class="section-title">最近上传</h2><p class="text-xs text-slate-400">所有文件都按 ExamLex pipeline 处理：隔离 → 分类 → 提取 → 蒸馏 → 校验 → 提交。任一阶段未通过都不会伪装成可用题源。</p><div v-for="item in uploads" :key="item.id" class="flex items-center gap-3 border-t border-slate-100 dark:border-slate-700 py-2.5 text-xs"><span class="flex-1 truncate">{{ item.filename || item.title }}</span><span class="text-slate-400">{{ item.status || '隔离中' }}</span><span class="text-slate-400">{{ pipelineFor(item.id)?.current_stage || 'extract' }}</span><button class="btn-ghost !py-1 !text-[10px]" @click="runPipeline(item.id)">运行 pipeline</button></div></section>
    </template>

    <input ref="fileInput" type="file" class="hidden" accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.md,.markdown,image/*" @change="onFileChange" />

    <Modal title="AI 生成模拟题" :show="showAiGenerator" @close="showAiGenerator = false">
      <div class="space-y-3">
        <p class="text-xs text-slate-500 dark:text-slate-400">生成内容仅用于私人训练，明确标记为非官方模拟。题目会按考试和专项要求生成，并在提交后进入错题与记忆卡流程。</p>
        <div><label class="label">专项</label><select v-model="aiForm.module" class="input"><option value="writing">写作</option><option value="listening">听力</option><option value="reading">阅读</option><option value="translation">翻译</option><option value="vocabulary">词汇</option><option value="basics">基础知识</option></select></div>
        <div class="grid grid-cols-2 gap-3">
          <div><label class="label">难度</label><select v-model="aiForm.difficulty" class="input"><option value="basic">基础</option><option value="standard">标准</option><option value="advanced">进阶</option></select></div>
          <div><label class="label">题目数量</label><input v-model.number="aiForm.questionCount" type="number" min="1" max="20" class="input" /></div>
        </div>
        <div><label class="label">生成要求（可选）</label><textarea v-model="aiForm.focus" rows="3" class="input" placeholder="例如：重点训练定位证据和同义替换"></textarea></div>
      </div>
      <template #footer><button class="btn-ghost" @click="showAiGenerator = false">取消</button><button class="btn-primary" @click="generateSimulation"><Sparkles :size="15" />生成并开始</button></template>
    </Modal>

    <Modal title="真题来源核验" :show="showVerify" @close="showVerify = false">
      <div class="space-y-3">
        <p class="text-xs text-slate-500 dark:text-slate-400">请填写可追溯来源。这里记录的是你的核验依据，不代表系统替你确认文件真实性；提交后仍需运行 pipeline。</p>
        <div><label class="label">来源名称</label><input v-model="verifyForm.sourceName" class="input" placeholder="例如：全国大学英语四、六级考试委员会" /></div>
        <div><label class="label">来源 URL（可选）</label><input v-model="verifyForm.sourceUrl" class="input" placeholder="https://..." /></div>
        <div><label class="label">核验备注</label><textarea v-model="verifyForm.note" rows="3" class="input" placeholder="记录年份、试卷版本和核验依据"></textarea></div>
      </div>
      <template #footer><button class="btn-ghost" @click="showVerify = false">取消</button><button class="btn-primary" :disabled="!verifyForm.sourceName.trim()" @click="verifyPastPaper">记录核验依据</button></template>
    </Modal>
  </div>
</template>
