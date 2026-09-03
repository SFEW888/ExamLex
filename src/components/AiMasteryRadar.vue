<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useChart, chartTextColor } from '../composables/useChart'

const props = defineProps<{ exam?: string }>()
const exam = ref(props.exam || localStorage.getItem('examlex-active-exam') || 'CET4')
const mastery = ref<Array<{ module: string; title: string; score: number }>>([])
const assessmentRounds = ref(0)
const assessmentRequiredRounds = ref(3)
const assessmentReady = ref(false)
const loading = ref(true)
const labels: Record<string, string> = { writing: '写作', listening: '听力', reading: '阅读', translation: '翻译', vocabulary: '词汇', basics: '基础知识' }
async function load() {
  loading.value = true
  try {
    const response = await fetch(`/api/profile/diagnosis?exam=${exam.value}`)
    const payload = await response.json()
    mastery.value = response.ok ? (payload.mastery || []) : []
    assessmentRounds.value = response.ok ? Number(payload.system_stats?.assessment_rounds ?? payload.system_assessment?.evidence_records ?? 0) : 0
    assessmentRequiredRounds.value = response.ok ? Number(payload.system_assessment?.assessment_required_rounds || payload.system_stats?.assessment_required_rounds || 3) : 3
    assessmentReady.value = response.ok && payload.system_assessment?.assessment_ready === true
  } catch { mastery.value = [] }
  finally { loading.value = false }
}
onMounted(load)
watch(() => props.exam, value => {
  if (value && value !== exam.value) exam.value = value
})
watch(exam, load)
watch(exam, value => localStorage.setItem('examlex-active-exam', value))
const radarItems = computed(() => mastery.value.length ? mastery.value : Object.keys(labels).map(module => ({ module, title: labels[module], score: 0 })))
const hasEvidence = computed(() => assessmentReady.value && mastery.value.some(item => item.score > 0))
const { el } = useChart(() => ({
  radar: { indicator: radarItems.value.map(item => ({ name: labels[item.module] || item.title, max: 100 })), splitNumber: 4, axisName: { color: chartTextColor(), fontSize: 11 }, splitLine: { lineStyle: { color: ['#e2e8f0', '#cbd5e1', '#94a3b8', '#64748b'] } }, splitArea: { areaStyle: { color: ['rgba(14,165,233,0.03)', 'rgba(14,165,233,0.06)'] } } },
  series: [{ type: 'radar', data: [{ value: radarItems.value.map(item => item.score), name: '系统掌握度', areaStyle: { color: assessmentReady.value ? 'rgba(14,165,233,0.18)' : 'rgba(148,163,184,0.12)' }, lineStyle: { color: assessmentReady.value ? '#0ea5e9' : '#94a3b8', width: 2 }, itemStyle: { color: assessmentReady.value ? '#0ea5e9' : '#94a3b8' } }] }],
  tooltip: { trigger: 'item' }
}), [mastery, assessmentReady, assessmentRounds])
</script>

<template>
  <section class="card" data-testid="ai-mastery-radar">
    <div class="flex items-center justify-between gap-3"><div><div class="text-[10px] tracking-[0.16em] uppercase text-slate-400">Evidence mastery</div><h2 class="section-title !mb-0 mt-1">英语专项掌握度雷达</h2></div><select v-model="exam" class="input !w-auto !py-1.5 !text-xs" aria-label="选择考试"><option value="CET4">CET-4</option><option value="CET6">CET-6</option><option value="POSTGRADUATE_ENGLISH">考研英语</option><option value="TEM4">TEM-4</option><option value="TEM8">TEM-8</option></select></div>
    <div v-if="loading" class="h-56 flex items-center justify-center text-xs text-slate-400">正在计算掌握度…</div>
    <template v-else><div ref="el" class="h-56"></div><p v-if="!assessmentReady" class="text-[10px] text-slate-400 text-center">系统评估：无。完成真题或模拟卷测试 {{ assessmentRounds }}/{{ assessmentRequiredRounds }} 轮后生成掌握度。</p><p v-else-if="!hasEvidence" class="text-[10px] text-slate-400 text-center">已完成卷测，但暂未形成可用专项掌握度证据。</p><p v-else class="text-[10px] text-slate-400 text-center">分数由提交的题目、正确率和错误证据计算，不采纳主观自评。</p></template>
  </section>
</template>
