<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import Modal from './Modal.vue'

type ExamOption = { id: string; title: string; short_title?: string; target_bands?: string[] }
type Assessment = {
  configured?: boolean
  foundation_level?: string | null
  target_band?: string | null
  strengths?: string[]
  gaps?: string[]
  daily_time_budget_minutes?: number
  updated_at?: string | null
}
type Diagnosis = {
  profile?: { foundation_level?: string | null; target_band?: string | null; daily_time_budget_minutes?: number }
  self_assessment?: Assessment
  system_assessment?: {
    status?: string
    method?: string
    target_band?: string | null
    strengths?: string[]
    gaps?: string[]
    risks?: Array<{ tag: string; count: number; module?: string }>
    mastery?: Array<{ module: string; title: string; score: number }>
    evidence_records?: number
    practice_records?: number
    assessment_required_rounds?: number
    assessment_ready?: boolean
  }
  strengths?: string[]
  gaps?: string[]
  risks?: Array<{ tag: string; count: number; module?: string }>
  diagnosis?: string
  evidence_records?: number
  mastery?: Array<{ module: string; title: string; score: number }>
}

const FALLBACK_EXAMS: ExamOption[] = [
  { id: 'CET4', title: '大学英语四级', short_title: 'CET-4', target_bands: ['425~499', '500~550', '550+', '600+'] },
  { id: 'CET6', title: '大学英语六级', short_title: 'CET-6', target_bands: ['425~499', '500~550', '550+', '600+'] },
  { id: 'POSTGRADUATE_ENGLISH', title: '考研英语', short_title: '考研英语', target_bands: ['50+', '70~80', '80+', '90+'] },
  { id: 'TEM4', title: '英语专业四级', short_title: 'TEM-4', target_bands: ['60~69', '70~79', '80+'] },
  { id: 'TEM8', title: '英语专业八级', short_title: 'TEM-8', target_bands: ['60~69', '70~79', '80+'] },
]

const exam = ref(localStorage.getItem('examlex-active-exam') || 'CET4')
const exams = ref<ExamOption[]>([...FALLBACK_EXAMS])
const data = ref<Diagnosis | null>(null)
const loading = ref(false)
const loadingExams = ref(false)
const error = ref('')
const saveError = ref('')
const showEditor = ref(false)
const saving = ref(false)
const form = ref({ foundation_level: '', target_band: '', strengths: '', gaps: '', daily_time_budget_minutes: 90 })

const examLabels: Record<string, string> = { CET4: 'CET-4', CET6: 'CET-6', POSTGRADUATE_ENGLISH: '考研英语', TEM4: 'TEM-4', TEM8: 'TEM-8' }
const selectedExam = computed(() => exams.value.find(item => item.id === exam.value) || FALLBACK_EXAMS[0])
const targetBands = computed(() => selectedExam.value.target_bands || [])
const selfAssessment = computed(() => data.value?.self_assessment)
const systemAssessment = computed(() => data.value?.system_assessment)
const systemStrengths = computed(() => systemAssessment.value?.strengths || data.value?.strengths || [])
const systemGaps = computed(() => systemAssessment.value?.gaps || data.value?.gaps || [])
const risks = computed(() => systemAssessment.value?.risks || data.value?.risks || [])
const evidenceRecords = computed(() => systemAssessment.value?.evidence_records ?? data.value?.evidence_records ?? 0)
const assessmentRequiredRounds = computed(() => systemAssessment.value?.assessment_required_rounds ?? 3)
const assessmentReady = computed(() => systemAssessment.value?.assessment_ready === true)
const topRisk = computed(() => risks.value[0])
const hasEvidence = computed(() => assessmentReady.value && evidenceRecords.value >= assessmentRequiredRounds.value)

async function loadExamOptions() {
  loadingExams.value = true
  try {
    const response = await fetch('/api/exams')
    const payload = response.ok ? await response.json() : null
    const items = Array.isArray(payload) ? payload : payload?.exams
    if (Array.isArray(items) && items.length) {
      exams.value = items.filter((item: any) => item?.id && item?.title).map((item: any) => ({
        id: item.id,
        title: item.title,
        short_title: item.short_title,
        target_bands: Array.isArray(item.target_bands) ? item.target_bands : undefined,
      }))
      if (!exams.value.some(item => item.id === exam.value)) exam.value = exams.value[0]?.id || 'CET4'
    }
  } catch {
    // Local fallback keeps the self-assessment form usable when the API is offline.
  } finally {
    loadingExams.value = false
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const response = await fetch(`/api/profile/diagnosis?exam=${encodeURIComponent(exam.value)}`)
    const payload = await response.json()
    if (!response.ok) throw new Error(payload.error || '画像暂不可用')
    data.value = payload
  } catch (err: any) {
    error.value = err?.message || '画像暂不可用'
  } finally {
    loading.value = false
  }
}

function openEditor() {
  const assessment = selfAssessment.value
  form.value = {
    foundation_level: assessment?.configured ? assessment.foundation_level || '' : '',
    target_band: assessment?.configured ? assessment.target_band || '' : '',
    strengths: assessment?.strengths?.join('、') || '',
    gaps: assessment?.gaps?.join('、') || '',
    daily_time_budget_minutes: assessment?.daily_time_budget_minutes || data.value?.profile?.daily_time_budget_minutes || 90,
  }
  saveError.value = ''
  showEditor.value = true
}

async function saveSelfAssessment() {
  saveError.value = ''
  if (!form.value.foundation_level || !form.value.target_band) {
    saveError.value = '请先填写基础水平和目标分数。'
    return
  }
  saving.value = true
  try {
    const response = await fetch('/api/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        exam_type: exam.value,
        foundation_level: form.value.foundation_level,
        target_band: form.value.target_band,
        self_strengths: form.value.strengths,
        self_gaps: form.value.gaps,
        daily_time_budget_minutes: Number(form.value.daily_time_budget_minutes),
      }),
    })
    const payload = await response.json()
    if (!response.ok) throw new Error(payload.error || '保存失败')
    showEditor.value = false
    await load()
  } catch (err: any) {
    saveError.value = err?.message || '保存失败'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadExamOptions()
  await load()
})
watch(exam, value => {
  localStorage.setItem('examlex-active-exam', value)
  void load()
})
</script>

<template>
  <section class="card border-l-4 border-l-primary-500 space-y-4" data-testid="profile-diagnosis">
    <div class="flex items-start justify-between gap-3 flex-wrap">
      <div>
        <div class="text-[10px] tracking-[0.16em] uppercase text-slate-400">Learner profile</div>
        <h2 class="section-title !mb-0 mt-1">我的备考画像</h2>
        <p class="text-xs text-slate-400 mt-1">先填写你的主观起点，系统再用练习证据持续校准。</p>
      </div>
      <div class="flex items-center gap-2">
        <select v-model="exam" class="input !w-auto !py-1.5 !text-xs" :disabled="loadingExams" aria-label="选择考试">
          <option v-for="(label, id) in examLabels" :key="id" :value="id">{{ label }}</option>
        </select>
        <button type="button" class="btn-primary !py-1.5 !text-xs" @click="openEditor">{{ selfAssessment?.configured ? '修改自评' : '填写自评' }}</button>
      </div>
    </div>

    <div v-if="loading" class="text-xs text-slate-400">正在读取画像…</div>
    <div v-else-if="error" class="text-xs text-amber-600">{{ error }}</div>
    <template v-else-if="data">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div class="rounded-xl border border-slate-200 dark:border-slate-700 p-3 space-y-2">
          <div class="flex items-center justify-between"><h3 class="text-xs font-semibold">我的自评</h3><span class="text-[10px] text-slate-400">主观输入</span></div>
          <template v-if="selfAssessment?.configured">
            <div class="grid grid-cols-2 gap-2 text-xs"><div><span class="text-slate-400">基础水平：</span>{{ selfAssessment.foundation_level }}</div><div><span class="text-slate-400">目标分数：</span>{{ selfAssessment.target_band }}</div></div>
            <div class="text-xs"><span class="text-slate-400">优势：</span>{{ selfAssessment.strengths?.join('、') || '未填写' }}</div>
            <div class="text-xs"><span class="text-slate-400">短板：</span>{{ selfAssessment.gaps?.join('、') || '未填写' }}</div>
          </template>
          <p v-else class="text-xs text-slate-400">尚未填写自评，点击“填写自评”设定你的起点。</p>
        </div>
        <div class="rounded-xl border border-primary-100 dark:border-primary-900/50 p-3 space-y-2">
          <div class="flex items-center justify-between"><h3 class="text-xs font-semibold">系统评估</h3><span class="text-[10px] text-primary-500">练习证据</span></div>
          <p class="text-xs leading-5 text-slate-600 dark:text-slate-300">{{ data.diagnosis }}</p>
          <div class="grid grid-cols-2 gap-2 text-[10px] text-slate-400"><span>目标分数：{{ systemAssessment?.target_band || '无' }}</span><span>卷测进度：{{ evidenceRecords }}/{{ assessmentRequiredRounds }} 轮</span></div>
          <div class="text-[10px] text-slate-400">评估依据：{{ evidenceRecords }} 轮真题或模拟卷<span v-if="systemAssessment?.method"> · {{ systemAssessment.method }}</span></div>
        </div>
      </div>

      <div v-if="hasEvidence" class="grid sm:grid-cols-3 gap-2 text-xs">
        <div class="rounded-lg border border-emerald-100 dark:border-emerald-900/40 px-3 py-2"><span class="text-slate-400">系统优势：</span>{{ systemStrengths.join('、') || '暂无明显优势' }}</div>
        <div class="rounded-lg border border-amber-100 dark:border-amber-900/40 px-3 py-2"><span class="text-slate-400">系统短板：</span>{{ systemGaps.join('、') || '暂无明显短板' }}</div>
        <div class="rounded-lg border border-rose-100 dark:border-rose-900/40 px-3 py-2"><span class="text-slate-400">重复风险：</span>{{ topRisk ? `${topRisk.tag}（${topRisk.count} 次）` : '暂无重复风险' }}</div>
      </div>
      <div v-else class="rounded-lg bg-slate-50 dark:bg-slate-700/40 px-3 py-2 text-xs text-slate-500 dark:text-slate-300">系统评估暂不下结论：完成 3 轮真题或模拟卷后，AI Agent 才会根据正确率、耗时和错误标签更新优势、短板与风险。</div>
      <div v-if="hasEvidence" class="flex flex-wrap gap-1.5">
        <span v-for="item in (systemAssessment?.mastery || data.mastery || [])" :key="item.module" class="rounded-full bg-primary-50 dark:bg-primary-900/30 px-2.5 py-1 text-[10px] text-primary-700 dark:text-primary-300">{{ item.title }} {{ item.score }}%</span>
      </div>
    </template>
  </section>

  <Modal title="填写我的备考画像" :show="showEditor" @close="showEditor = false">
    <form class="space-y-4" @submit.prevent="saveSelfAssessment">
      <div>
        <label class="label" for="foundation-level">基础水平</label>
        <select id="foundation-level" v-model="form.foundation_level" class="input">
          <option value="" disabled>请选择你的自评基础</option>
          <option value="基础偏弱">基础偏弱</option>
          <option value="中等基础">中等基础</option>
          <option value="基础较好">基础较好</option>
        </select>
      </div>
      <div>
        <label class="label" for="target-band">目标分数</label>
        <select id="target-band" v-model="form.target_band" class="input">
          <option value="" disabled>请选择目标分数</option>
          <option v-for="band in targetBands" :key="band" :value="band">{{ band }}</option>
        </select>
      </div>
      <div>
        <label class="label" for="self-strengths">我认为的优势</label>
        <textarea id="self-strengths" v-model="form.strengths" class="input" rows="2" placeholder="可填写多个，用顿号或逗号分隔，例如：词汇、语法基础"></textarea>
      </div>
      <div>
        <label class="label" for="self-gaps">我认为的短板</label>
        <textarea id="self-gaps" v-model="form.gaps" class="input" rows="2" placeholder="可填写多个，用顿号或逗号分隔，例如：听力连读、阅读定位"></textarea>
      </div>
      <div>
        <label class="label" for="daily-budget">每天可投入时间（分钟）</label>
        <input id="daily-budget" v-model.number="form.daily_time_budget_minutes" class="input" type="number" min="10" max="1440" step="5" />
      </div>
      <p v-if="saveError" class="text-xs text-rose-600">{{ saveError }}</p>
      <div class="flex justify-end gap-2 pt-1">
        <button type="button" class="btn-ghost" @click="showEditor = false">取消</button>
        <button type="submit" class="btn-primary" :disabled="saving">{{ saving ? '保存中…' : '保存自评' }}</button>
      </div>
    </form>
  </Modal>
</template>
