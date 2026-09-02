<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useChart, chartTextColor } from '../composables/useChart'

const exam = ref(localStorage.getItem('examlex-active-exam') || 'CET4')
const mastery = ref<Array<{ module: string; title: string; score: number }>>([])
const loading = ref(true)
const labels: Record<string, string> = { writing: '写作', listening: '听力', reading: '阅读', translation: '翻译', vocabulary: '词汇', basics: '基础知识' }
async function load() {
  loading.value = true
  try {
    const response = await fetch(`/api/profile/diagnosis?exam=${exam.value}`)
    const payload = await response.json()
    mastery.value = response.ok ? (payload.mastery || []) : []
  } catch { mastery.value = [] }
  finally { loading.value = false }
}
onMounted(load)
watch(exam, load)
watch(exam, value => localStorage.setItem('examlex-active-exam', value))
const hasEvidence = computed(() => mastery.value.some(item => item.score > 0))
const { el } = useChart(() => mastery.value.length ? ({
  radar: { indicator: mastery.value.map(item => ({ name: labels[item.module] || item.title, max: 100 })), splitNumber: 4, axisName: { color: chartTextColor(), fontSize: 11 }, splitLine: { lineStyle: { color: ['#e2e8f0', '#cbd5e1', '#94a3b8', '#64748b'] } }, splitArea: { areaStyle: { color: ['rgba(14,165,233,0.03)', 'rgba(14,165,233,0.06)'] } } },
  series: [{ type: 'radar', data: [{ value: mastery.value.map(item => item.score), name: '系统掌握度', areaStyle: { color: 'rgba(14,165,233,0.18)' }, lineStyle: { color: '#0ea5e9', width: 2 }, itemStyle: { color: '#0ea5e9' } }] }],
  tooltip: { trigger: 'item' }
}) : null, [mastery])
</script>

<template>
  <section class="card" data-testid="ai-mastery-radar">
    <div class="flex items-center justify-between gap-3"><div><div class="text-[10px] tracking-[0.16em] uppercase text-slate-400">Evidence mastery</div><h2 class="section-title !mb-0 mt-1">英语专项掌握度雷达</h2></div><select v-model="exam" class="input !w-auto !py-1.5 !text-xs" aria-label="选择考试"><option value="CET4">CET-4</option><option value="CET6">CET-6</option><option value="POSTGRADUATE_ENGLISH">考研英语</option><option value="TEM4">TEM-4</option><option value="TEM8">TEM-8</option></select></div>
    <div v-if="loading" class="h-56 flex items-center justify-center text-xs text-slate-400">正在计算掌握度…</div>
    <template v-else><div ref="el" class="h-56"></div><p v-if="!hasEvidence" class="text-[10px] text-slate-400 text-center">当前没有可用练习证据，雷达保持为零；完成专项训练后自动更新。</p><p v-else class="text-[10px] text-slate-400 text-center">分数由提交的题目、正确率和错误证据计算，不采纳主观自评。</p></template>
  </section>
</template>
