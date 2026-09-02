<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'
import SubjectPanel from '../components/SubjectPanel.vue'
import AiMasteryRadar from '../components/AiMasteryRadar.vue'

type ExamOption = {
  id: string
  title: string
  short_title?: string
}

const FALLBACK_EXAMS: ExamOption[] = [
  { id: 'CET4', title: '大学英语四级', short_title: 'CET-4' },
  { id: 'CET6', title: '大学英语六级', short_title: 'CET-6' },
  { id: 'POSTGRADUATE_ENGLISH', title: '考研英语', short_title: '考研英语' },
  { id: 'TEM4', title: '英语专业四级', short_title: 'TEM-4' },
  { id: 'TEM8', title: '英语专业八级', short_title: 'TEM-8' }
]

const store = useAppStore()
const route = useRoute()
const router = useRouter()
const subjectExists = computed(() => !!store.subjectMap.english)
const initialExam = String(route.query.exam || localStorage.getItem('examlex-active-exam') || 'CET4')
const exam = ref(FALLBACK_EXAMS.some(item => item.id === initialExam) ? initialExam : 'CET4')
const examOptions = ref<ExamOption[]>([...FALLBACK_EXAMS])
const loadingExams = ref(false)

const selectedExam = computed(() =>
  examOptions.value.find(item => item.id === exam.value) || FALLBACK_EXAMS[0]
)

async function loadExamOptions() {
  loadingExams.value = true
  try {
    const response = await fetch('/api/exams')
    if (!response.ok) return
    const payload = await response.json()
    const items = Array.isArray(payload) ? payload : payload?.exams
    if (!Array.isArray(items) || !items.length) return

    examOptions.value = items.filter((item: any) => item?.id && item?.title)
    if (!examOptions.value.some(item => item.id === exam.value)) {
      exam.value = examOptions.value[0]?.id || 'CET4'
    }
  } catch {
    // The local fallback keeps the selector usable when the content service is offline.
  } finally {
    loadingExams.value = false
  }
}

function persistExam(value: string) {
  if (!examOptions.value.some(item => item.id === value)) return
  localStorage.setItem('examlex-active-exam', value)
  if (route.path === '/english' && route.query.exam !== value) {
    router.replace({ query: { ...route.query, exam: value } })
  }
}

onMounted(loadExamOptions)
watch(exam, persistExam)
watch(() => route.query.exam, value => {
  if (typeof value === 'string' && examOptions.value.some(item => item.id === value) && value !== exam.value) {
    exam.value = value
  }
})
</script>

<template>
  <div class="p-4 md:p-6 max-w-6xl mx-auto space-y-4">
    <template v-if="subjectExists">
      <header class="flex items-end justify-between gap-4 flex-wrap">
        <div>
          <div class="text-xs tracking-[0.18em] text-slate-400 uppercase">ExamLex · English track</div>
          <h1 class="page-title mt-1">英语专项</h1>
          <p class="text-sm text-slate-500 dark:text-slate-400 mt-2 max-w-2xl">综合掌握学习进度；写作、听力、阅读、翻译、词汇和基础知识请从左侧英语专项栏目进入。</p>
        </div>
        <label class="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
          <span>考试</span>
          <select
            v-model="exam"
            class="input !w-auto min-w-32 !py-1.5"
            :disabled="loadingExams"
            :aria-label="`选择考试，当前为${selectedExam.title}`"
          >
            <option v-for="item in examOptions" :key="item.id" :value="item.id">
              {{ item.short_title || item.title }}
            </option>
          </select>
        </label>
      </header>

      <AiMasteryRadar />
      <SubjectPanel subject-id="english" :hide-mastery="true" />
    </template>

    <div v-else class="card text-center py-16 text-slate-400">
      <div class="text-4xl mb-2">EN</div>
      <p class="text-sm">「英语」科目已被删除，此页面已隐藏</p>
      <RouterLink to="/settings" class="text-primary-500 text-xs underline mt-2 inline-block">前往设置页管理科目 →</RouterLink>
    </div>
  </div>
</template>
