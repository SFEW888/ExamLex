<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

type PlanTask = { module: string; focus?: string; minutes?: number; reason?: string }
type EvidenceTask = { module: string; done: boolean; done_reason?: string }
const plan = ref<{ tasks?: PlanTask[]; total_planned_minutes?: number } | null>(null)
const evidence = ref<EvidenceTask[]>([])
const loading = ref(true)
const error = ref('')
const labels: Record<string, string> = { writing: '写作', listening: '听力', reading: '阅读', translation: '翻译', vocabulary: '词汇', basics: '基础知识' }
const exam = localStorage.getItem('examlex-active-exam') || 'CET4'
const doneCount = computed(() => (plan.value?.tasks || []).filter(item => evidence.value.some(task => task.module === item.module && task.done)).length)

onMounted(async () => {
  try {
    const [planResponse, bootResponse] = await Promise.all([
      fetch(`/api/plans?exam=${encodeURIComponent(exam)}&period=day`),
      fetch(`/api/bootstrap?exam=${encodeURIComponent(exam)}`)
    ])
    const planPayload = await planResponse.json()
    const bootPayload = await bootResponse.json()
    if (!planResponse.ok) throw new Error(planPayload.error || '今日计划暂不可用')
    plan.value = planPayload
    evidence.value = bootPayload.tasks || []
  } catch (err: any) {
    error.value = err?.message || '今日计划暂不可用'
  } finally { loading.value = false }
})
</script>

<template>
  <section class="card space-y-3" data-testid="ai-today-plan">
    <div class="flex items-center justify-between gap-3">
      <div><div class="text-[10px] tracking-[0.16em] uppercase text-slate-400">Agent planner</div><h2 class="section-title !mb-0 mt-1">AI 今日路线</h2></div>
      <span v-if="plan" class="text-xs font-semibold text-primary-500">{{ doneCount }}/{{ plan.tasks?.length || 0 }} 已由证据完成</span>
    </div>
    <div v-if="loading" class="text-xs text-slate-400">正在按画像和错误记录生成任务…</div>
    <div v-else-if="error" class="text-xs text-amber-600">{{ error }}</div>
    <template v-else-if="plan?.tasks?.length">
      <div v-for="(task, index) in plan.tasks" :key="`${task.module}-${index}`" class="flex items-center gap-3 border-t border-slate-100 dark:border-slate-700 pt-2.5">
        <span class="w-6 h-6 rounded-full bg-primary-50 dark:bg-primary-900/30 text-primary-600 text-xs font-bold flex items-center justify-center">{{ index + 1 }}</span>
        <div class="flex-1 min-w-0"><div class="text-sm font-medium">{{ labels[task.module] || task.module }} · {{ task.focus || '专项训练' }}</div><div class="text-[10px] text-slate-400">{{ task.minutes || 0 }} 分钟 · {{ task.reason || '基于当前证据' }}</div></div>
        <span class="text-[10px] rounded-full px-2 py-1" :class="evidence.some(item => item.module === task.module && item.done) ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-300' : 'bg-slate-100 text-slate-500 dark:bg-slate-700 dark:text-slate-300'">{{ evidence.some(item => item.module === task.module && item.done) ? '已完成' : '待完成' }}</span>
      </div>
      <p class="text-[10px] text-slate-400">完成对应专项练习或记忆卡复习后自动更新，不使用手动勾选作为完成依据。</p>
    </template>
  </section>
</template>
