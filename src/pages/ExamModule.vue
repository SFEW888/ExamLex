<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'
import { BUILTIN_TEMPLATES } from '../data/englishTemplates'
import { uid } from '../utils/date'
import Modal from '../components/Modal.vue'
import { FileCheck2, FileText, Sparkles, Upload } from '@lucide/vue'

type Lesson = { id: string; title: string; summary: string; checkpoints?: string[] }
type ModuleContent = { title: string; overview: string; source_status?: string; lessons?: Lesson[] }
type PracticeSource = { id?: string; upload_id?: string; filename?: string; title?: string; module?: string; target_module?: string; content_kind?: string; status?: string; source_status?: string }

const route = useRoute()
const router = useRouter()
const store = useAppStore()
const exam = ref(String(route.query.exam || localStorage.getItem('examlex-active-exam') || 'CET4'))
const content = ref<ModuleContent | null>(null)
const loading = ref(true)
const exams = ref<{ id: string; title: string; short_title?: string }[]>([])
const moduleQueue = ref<PracticeSource[]>([])
const pastPaperSources = ref<PracticeSource[]>([])
const simulationSources = ref<PracticeSource[]>([])
const uploadFiles = ref<Record<string, PracticeSource>>({})
const moduleKey = computed(() => String(route.params.module || 'writing'))
const labels: Record<string, string> = { writing: '写作', listening: '听力', reading: '阅读', translation: '翻译', vocabulary: '词汇', basics: '基础知识' }
const moduleStages: Record<string, string[]> = {
  writing: ['题型分析', '结构搭建', '高分表达', '二次写作'],
  listening: ['预测题型', '捕捉信息', '精听拆解', '跟读复现'],
  reading: ['题型识别', '定位证据', '排除干扰', '错因回溯'],
  translation: ['信息分块', '词性转换', '句法重组', '错漏诊断'],
  vocabulary: ['分层建库', '真题语境', '易混辨析', '间隔复习'],
  basics: ['词性', '基础句型', '复合句', '语音规则']
}
const stageLabels = computed(() => moduleStages[moduleKey.value] || [])

const writingTab = ref<'lessons' | 'templates'>('lessons')
const templateCategories = ['议论文', '图表文', '信件文', '自定义']
const showTemplate = ref(false)
const templateForm = ref<{ id: string; title: string; content: string; level: number; category: string }>({ id: '', title: '', content: '', level: 0, category: '自定义' })
const templateGroups = computed(() => templateCategories
  .map(category => ({ category, items: store.english.templates.filter(t => (t.category || '自定义') === category) }))
  .filter(group => group.items.length))

function openTemplate(template?: typeof templateForm.value) {
  templateForm.value = template
    ? { id: template.id, title: template.title, content: template.content, level: template.level, category: template.category || '自定义' }
    : { id: '', title: '', content: '', level: 0, category: '自定义' }
  showTemplate.value = true
}
function saveTemplate() {
  if (!templateForm.value.title.trim() || !templateForm.value.content.trim()) return
  const value = { ...templateForm.value, title: templateForm.value.title.trim() }
  if (value.id) {
    const existing = store.english.templates.find(item => item.id === value.id)
    if (existing) Object.assign(existing, value)
  } else {
    store.english.templates.push({ ...value, id: uid() })
  }
  store.save()
  showTemplate.value = false
}
function deleteTemplate(id: string) {
  if (!window.confirm('确认删除这套作文模板？')) return
  store.english.templates = store.english.templates.filter(item => item.id !== id)
  store.save()
  showTemplate.value = false
}
function generateTemplates() {
  const existing = new Set(store.english.templates.map(item => item.title))
  let added = 0
  for (const template of BUILTIN_TEMPLATES) {
    if (existing.has(template.title)) continue
    store.english.templates.push({ ...template, id: uid(), level: 0 })
    added++
  }
  if (added) store.save()
}

type PracticeChoice = 'ai' | 'past' | 'simulation' | 'upload'
const showPracticeChooser = ref(false)
const practiceChoice = ref<PracticeChoice>('ai')
const selectedPracticeSource = ref('')
const practiceForm = ref({ difficulty: 'standard', questionCount: 5, focus: '' })
const practiceFileInput = ref<HTMLInputElement>()
const uploadingPractice = ref(false)
const uploadMessage = ref('')

const practiceChoiceMeta: Array<{ id: PracticeChoice; title: string; description: string }> = [
  { id: 'ai', title: 'AI 模拟出题', description: '结合当前考试、专项与 ExamLex RAG 资料生成，非官方。' },
  { id: 'past', title: '官方真题整卷', description: '已核验的历年真题，按考试整卷进入并启动倒计时。' },
  { id: 'simulation', title: '模拟题整卷', description: '已通过 pipeline 的私有模拟卷，整卷倒计时，非官方。' },
  { id: 'upload', title: '上传的专项试题', description: '你上传并完成解析校验的专项题，按来源回溯。' },
]

const selectedSources = computed(() => {
  if (practiceChoice.value === 'past') return pastPaperSources.value
  if (practiceChoice.value === 'simulation') return simulationSources.value
  if (practiceChoice.value === 'upload') return moduleQueue.value.filter(item => ['ready_private', 'committed'].includes(String(item.status || '')))
  return []
})

function openPracticeChooser() {
  practiceChoice.value = 'ai'
  selectedPracticeSource.value = ''
  practiceForm.value = { difficulty: 'standard', questionCount: 5, focus: '' }
  uploadMessage.value = ''
  showPracticeChooser.value = true
}

function choosePracticeSource(choice: PracticeChoice) {
  practiceChoice.value = choice
  selectedPracticeSource.value = ''
  if (choice !== 'ai' && selectedSources.value.length) selectedPracticeSource.value = String(selectedSources.value[0].id || selectedSources.value[0].upload_id || '')
}

function beginPractice() {
  if (practiceChoice.value === 'ai') {
    showPracticeChooser.value = false
    routerPushPractice('ai', '', {
      question_count: String(Math.min(20, Math.max(1, practiceForm.value.questionCount))),
      difficulty: practiceForm.value.difficulty,
      focus: practiceForm.value.focus.trim(),
    })
    return
  }
  if (!selectedPracticeSource.value) return
  showPracticeChooser.value = false
  const kind = practiceChoice.value === 'past' ? 'past' : practiceChoice.value === 'simulation' ? 'upload' : 'upload'
  routerPushPractice(kind, selectedPracticeSource.value)
}

function routerPushPractice(kind: string, sourceId = '', options: Record<string, string> = {}) {
  router.push({ path: '/practice/session', query: { exam: exam.value, kind, module: moduleKey.value, source_id: sourceId, ...options } })
}

async function uploadPracticeFile(file?: File) {
  if (!file || uploadingPractice.value) return
  uploadingPractice.value = true
  uploadMessage.value = ''
  try {
    const body = new FormData()
    body.append('file', file)
    const response = await fetch(`/api/upload?exam=${encodeURIComponent(exam.value)}&module=${encodeURIComponent(moduleKey.value)}`, { method: 'POST', body })
    const payload = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(payload.error || '上传失败')
    const uploadId = String(payload.upload?.id || '')
    if (uploadId) {
      const pipelineResponse = await fetch('/api/pipeline/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ upload_id: uploadId, action: 'auto' }) })
      const pipeline = await pipelineResponse.json().catch(() => ({}))
      if (!pipelineResponse.ok) throw new Error(pipeline.error || '解析失败')
      if (pipeline.pipeline?.current_stage !== 'complete') {
        uploadMessage.value = pipeline.pipeline?.errors?.[0] || '文件已隔离，等待可用的文本解析或校验后才能开始训练。'
        await load()
        practiceChoice.value = 'upload'
        return
      }
    }
    uploadMessage.value = '文件已完成隔离解析与校验，请在下方选择它开始训练。'
    await load()
    practiceChoice.value = 'upload'
    const match = moduleQueue.value.find(item => item.upload_id === uploadId && ['ready_private', 'committed'].includes(String(item.status || '')))
    if (match) selectedPracticeSource.value = String(match.id || match.upload_id || '')
  } catch (error: any) {
    uploadMessage.value = error?.message || '上传失败，请重试。'
  } finally {
    uploadingPractice.value = false
    if (practiceFileInput.value) practiceFileInput.value.value = ''
  }
}

function onPracticeFileChange(event: Event) {
  uploadPracticeFile((event.target as HTMLInputElement).files?.[0])
}

async function load() {
  loading.value = true
  try {
    if (!exams.value.length) {
      const directory = await fetch('/api/exams').then(r => r.ok ? r.json() : null).catch(() => null)
      if (directory?.exams) exams.value = directory.exams
    }
    if (moduleKey.value === 'basics') {
      const boot = await fetch(`/api/bootstrap?exam=${exam.value}`).then(r => r.json())
      content.value = { title: '基础知识', overview: '词性、句型与语音拆解为可重复训练的小节点。', lessons: (boot.shared_basics?.groups || []).map((item: any) => ({ id: item.id, title: item.title, summary: (item.items || []).join('；'), checkpoints: item.items || [] })), source_status: 'available_all_tracks' }
    } else {
      const payload = await fetch(`/api/content?exam=${exam.value}&module=${moduleKey.value}`).then(r => r.json())
      content.value = payload.modules?.[moduleKey.value] || null
    }
    const uploads = await fetch(`/api/uploads?exam=${encodeURIComponent(exam.value)}`).then(r => r.json()).catch(() => null)
    uploadFiles.value = Object.fromEntries((uploads?.uploads || []).map((item: PracticeSource) => [String(item.id), item]))
    moduleQueue.value = (uploads?.module_content_queue || [])
      .filter((item: PracticeSource) => item.target_module === moduleKey.value)
      .map((item: PracticeSource) => ({ ...item, filename: uploadFiles.value[String(item.upload_id)]?.filename }))
    pastPaperSources.value = (uploads?.past_paper_candidates || [])
      .filter((item: PracticeSource) => item.status === 'verified_official')
      .map((item: PracticeSource) => ({ ...item, filename: item.filename || uploadFiles.value[String(item.upload_id)]?.filename }))
    simulationSources.value = (uploads?.simulations || [])
      .filter((item: PracticeSource) => item.status === 'ready_private')
      .map((item: PracticeSource) => ({ ...item, filename: item.filename || uploadFiles.value[String(item.upload_id)]?.filename }))
  } catch (error: any) {
    console.error(error)
  } finally { loading.value = false }
}

onMounted(load)
watch([exam, moduleKey], load)
watch(exam, value => localStorage.setItem('examlex-active-exam', value))
</script>

<template>
  <div class="p-4 md:p-6 max-w-6xl mx-auto space-y-4">
    <div class="flex items-end justify-between gap-3 flex-wrap">
      <div>
        <div class="text-xs tracking-[0.18em] text-slate-400 uppercase">ExamLex · {{ moduleKey }}</div>
        <h1 class="page-title mt-1">{{ content?.title || labels[moduleKey] || '英语专项' }}</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-2 max-w-3xl">{{ content?.overview || '加载对应教材内容…' }}</p>
      </div>
      <select v-model="exam" class="input !w-auto min-w-36">
        <option v-for="item in exams" :key="item.id" :value="item.id">{{ item.short_title || item.title }}</option>
      </select>
      <button class="btn-primary shrink-0" type="button" @click="openPracticeChooser">开始专项训练</button>
    </div>

    <div v-if="loading" class="card py-12 text-center text-sm text-slate-400">正在读取教材内容…</div>
    <template v-else>
      <div class="card">
        <div class="flex items-center justify-between gap-3 flex-wrap">
          <div>
            <div class="section-title !mb-1">专项学习路线</div>
            <p class="text-xs text-slate-400">按“{{ stageLabels.join(' → ') }}”推进，练习记录会回流到错题与记忆卡。</p>
          </div>
          <div class="flex items-center gap-1.5 text-[10px] text-slate-400">
            <span v-for="(stage, index) in stageLabels" :key="stage" class="flex items-center gap-1.5">
              <span class="w-5 h-5 rounded-full bg-primary-50 text-primary-600 dark:bg-primary-900/30 dark:text-primary-300 flex items-center justify-center font-semibold">{{ index + 1 }}</span>
              <span class="hidden sm:inline">{{ stage }}</span>
              <span v-if="index < stageLabels.length - 1" class="text-slate-300">›</span>
            </span>
          </div>
        </div>
      </div>

      <div v-if="moduleKey === 'writing'" class="flex gap-1 bg-slate-100 dark:bg-slate-800 rounded-xl p-1 w-fit">
        <button class="px-3 py-1.5 text-xs rounded-lg" :class="writingTab === 'lessons' ? 'bg-white dark:bg-slate-700 shadow-sm font-medium' : 'text-slate-500'" @click="writingTab = 'lessons'">写作路线</button>
        <button class="px-3 py-1.5 text-xs rounded-lg" :class="writingTab === 'templates' ? 'bg-white dark:bg-slate-700 shadow-sm font-medium' : 'text-slate-500'" @click="writingTab = 'templates'">作文模板</button>
      </div>

      <div v-if="moduleKey !== 'writing' || writingTab === 'lessons'" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <article v-for="(lesson, index) in content?.lessons || []" :key="lesson.id" class="card min-h-44 flex gap-5">
          <div class="text-3xl font-bold text-slate-300 dark:text-slate-600 tabular-nums">{{ String(index + 1).padStart(2, '0') }}</div>
          <div class="min-w-0">
            <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100">{{ lesson.title }}</h2>
            <p class="text-sm text-slate-500 dark:text-slate-400 leading-7 mt-2">{{ lesson.summary }}</p>
            <div class="flex flex-wrap gap-1.5 mt-3">
              <span v-for="tag in lesson.checkpoints || []" :key="tag" class="text-[11px] px-2 py-1 rounded-full bg-primary-50 text-primary-600 dark:bg-primary-900/30 dark:text-primary-300">{{ tag }}</span>
            </div>
          </div>
        </article>
      </div>

      <section v-if="moduleQueue.length" class="card space-y-2">
        <div class="flex items-center justify-between"><div><div class="section-title !mb-0">已分流到本专项的资料</div><p class="text-[10px] text-slate-400 mt-1">上传内容仍处于隔离/草稿状态，确认后可进入专项训练。</p></div><span class="text-xs text-slate-400">{{ moduleQueue.length }} 条</span></div>
        <div v-for="item in moduleQueue" :key="item.id" class="flex items-center gap-3 border-t border-slate-100 dark:border-slate-700 pt-2 text-xs"><span class="flex-1 truncate">{{ item.filename || item.content_kind || '专项内容' }}</span><span class="text-slate-400">{{ item.status || 'draft' }}</span><button class="btn-primary !py-1 !text-[10px]" type="button" :disabled="!['ready_private', 'committed'].includes(String(item.status || ''))" @click="selectedPracticeSource = String(item.id || item.upload_id || ''); practiceChoice = 'upload'; showPracticeChooser = true">开始训练</button></div>
      </section>

      <!-- 作文模板是独立标签内容，不能在“写作路线”下重复出现。 -->
      <div v-if="moduleKey === 'writing' && writingTab === 'templates'" class="space-y-3">
        <div class="card flex items-center justify-between gap-3 flex-wrap">
          <div><div class="section-title !mb-1">作文模板库</div><p class="text-xs text-slate-400">模板只提供可迁移结构，完成题目后请进行二次改写。</p></div>
          <div class="flex gap-2"><button class="btn-ghost !py-1.5 text-xs" @click="generateTemplates">生成内置模板</button><button class="btn-primary !py-1.5 text-xs" @click="openTemplate()">+ 自定义模板</button></div>
        </div>
        <div v-if="!templateGroups.length" class="card text-xs text-slate-400 text-center py-8">暂无模板，先生成内置模板或添加自定义模板。</div>
        <div v-for="group in templateGroups" :key="group.category" class="card">
          <div class="flex items-center gap-2 mb-3"><span class="text-xs font-semibold text-primary-600 dark:text-primary-300">{{ group.category }}</span><span class="text-[10px] text-slate-400">{{ group.items.length }} 套</span></div>
          <div class="grid sm:grid-cols-2 gap-2">
            <button v-for="template in group.items" :key="template.id" class="text-left border border-slate-100 dark:border-slate-700 rounded-lg p-3 hover:border-primary-200 dark:hover:border-primary-800" @click="openTemplate(template)">
              <div class="flex items-center justify-between gap-2"><span class="font-medium text-xs truncate">{{ template.title }}</span><span class="text-[10px] text-amber-400 shrink-0">{{ template.level ? '★'.repeat(template.level) : '未评级' }}</span></div>
              <p class="text-[11px] text-slate-400 line-clamp-3 mt-1.5 whitespace-pre-line">{{ template.content }}</p>
            </button>
          </div>
        </div>
      </div>

      <div class="text-xs text-slate-400">全局 Agent 可从右下角打开，会自动识别当前模块。</div>
    </template>

    <Modal title="选择专项训练题源" :show="showPracticeChooser" @close="showPracticeChooser = false">
      <div class="space-y-4">
        <p class="text-xs text-slate-500 dark:text-slate-400">先选择题源，再进入答题页。不同考试和专项的真题、模拟题与上传材料相互隔离。</p>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <button v-for="item in practiceChoiceMeta" :key="item.id" type="button" class="text-left rounded-xl border p-3 transition-colors" :class="practiceChoice === item.id ? 'border-primary-400 bg-primary-50 dark:bg-primary-900/20' : 'border-slate-200 dark:border-slate-700 hover:border-primary-200'" @click="choosePracticeSource(item.id)">
            <div class="flex items-center gap-2 text-sm font-semibold"><Sparkles v-if="item.id === 'ai'" :size="15" class="text-violet-500" /><FileCheck2 v-else-if="item.id === 'past'" :size="15" class="text-emerald-500" /><FileText v-else-if="item.id === 'simulation'" :size="15" class="text-sky-500" /><Upload v-else :size="15" class="text-amber-500" />{{ item.title }}</div>
            <p class="text-[11px] text-slate-500 dark:text-slate-400 mt-1.5 leading-5">{{ item.description }}</p>
          </button>
        </div>
        <template v-if="practiceChoice === 'ai'">
          <div class="grid grid-cols-2 gap-3"><div><label class="label">难度</label><select v-model="practiceForm.difficulty" class="input"><option value="basic">基础</option><option value="standard">标准</option><option value="advanced">进阶</option></select></div><div><label class="label">题目数量</label><input v-model.number="practiceForm.questionCount" class="input" type="number" min="1" max="20" /></div></div>
          <div><label class="label">生成要求（可选）</label><textarea v-model="practiceForm.focus" class="input" rows="3" placeholder="例如：重点训练定位证据和同义替换"></textarea></div>
        </template>
        <template v-else>
          <div v-if="practiceChoice === 'upload'" class="flex items-center justify-between gap-3 rounded-lg border border-dashed border-primary-200 bg-primary-50/60 dark:bg-primary-900/10 px-3 py-3"><div class="text-xs text-slate-500 dark:text-slate-300">可直接上传当前{{ labels[moduleKey] || '专项' }}题目；系统会先隔离解析、校验，再允许开始训练。</div><button class="btn-ghost !py-1.5 !text-xs shrink-0" type="button" :disabled="uploadingPractice" @click="practiceFileInput?.click"><Upload :size="14" />{{ uploadingPractice ? '解析中…' : '上传专项试题' }}</button></div>
          <div v-if="uploadMessage" class="rounded-lg bg-sky-50 dark:bg-sky-900/20 px-3 py-2 text-xs text-sky-700 dark:text-sky-300">{{ uploadMessage }}</div>
          <div v-if="selectedSources.length"><label class="label">选择{{ practiceChoice === 'past' ? '真题' : practiceChoice === 'simulation' ? '模拟卷' : '上传试题' }}</label><select v-model="selectedPracticeSource" class="input"><option v-for="item in selectedSources" :key="item.id || item.upload_id" :value="item.id || item.upload_id">{{ item.filename || item.title || item.content_kind || '未命名题源' }}</option></select></div>
          <div v-else class="rounded-lg bg-slate-50 dark:bg-slate-700/40 px-3 py-3 text-xs text-slate-500 dark:text-slate-300">当前{{ practiceChoice === 'past' ? '专项暂无已核验真题' : practiceChoice === 'simulation' ? '专项暂无已通过校验的模拟卷' : '暂无已完成解析校验的上传试题' }}。请先到对应栏目上传或推进 pipeline。</div>
        </template>
      </div>
      <template #footer><button class="btn-ghost" type="button" @click="showPracticeChooser = false">取消</button><button class="btn-primary" type="button" :disabled="practiceChoice !== 'ai' && !selectedPracticeSource" @click="beginPractice">进入训练</button></template>
    </Modal>
    <input ref="practiceFileInput" type="file" class="hidden" accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.md,.markdown,image/*" @change="onPracticeFileChange" />

    <Modal title="作文模板" :show="showTemplate" @close="showTemplate = false">
      <div class="space-y-3">
        <input v-model="templateForm.title" class="input" placeholder="模板标题，如：现象分析型作文结构" />
        <div><label class="label">分类</label><div class="grid grid-cols-4 gap-1.5"><button v-for="category in templateCategories" :key="category" type="button" class="text-xs px-2 py-1.5 rounded-lg" :class="templateForm.category === category ? 'bg-primary-500 text-white' : 'bg-slate-100 dark:bg-slate-700 text-slate-500'" @click="templateForm.category = category">{{ category }}</button></div></div>
        <textarea v-model="templateForm.content" rows="10" class="input !text-xs font-mono" placeholder="模板内容…"></textarea>
        <div><label class="label">掌握程度</label><div class="flex gap-1"><button v-for="level in 5" :key="level" type="button" class="text-2xl" :class="level <= templateForm.level ? 'text-amber-400' : 'text-slate-300'" @click="templateForm.level = level">★</button></div></div>
      </div>
      <template #footer><button v-if="templateForm.id" class="btn-danger mr-auto" @click="deleteTemplate(templateForm.id)">删除</button><button class="btn-ghost" @click="showTemplate = false">取消</button><button class="btn-primary" @click="saveTemplate">保存</button></template>
    </Modal>
  </div>
</template>
