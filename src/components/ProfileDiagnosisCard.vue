<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

type Diagnosis = {
  profile?: { foundation_level?: string; target_band?: string; daily_time_budget_minutes?: number }
  strengths?: string[]
  gaps?: string[]
  risks?: Array<{ tag: string; count: number; module?: string }>
  diagnosis?: string
  evidence_records?: number
  mastery?: Array<{ module: string; title: string; score: number }>
}

const exam = ref(localStorage.getItem('examlex-active-exam') || 'CET4')
const data = ref<Diagnosis | null>(null)
const loading = ref(false)
const error = ref('')
const examLabels: Record<string, string> = { CET4: 'CET-4', CET6: 'CET-6', POSTGRADUATE_ENGLISH: '考研英语', TEM4: 'TEM-4', TEM8: 'TEM-8' }

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
  } finally { loading.value = false }
}

onMounted(load)
watch(exam, load)
watch(exam, value => localStorage.setItem('examlex-active-exam', value))
const topRisk = computed(() => data.value?.risks?.[0])
</script>

<template>
  <section class="card border-l-4 border-l-primary-500 space-y-3" data-testid="profile-diagnosis">
    <div class="flex items-start justify-between gap-3">
      <div>
        <div class="text-[10px] tracking-[0.16em] uppercase text-slate-400">Evidence portrait</div>
        <h2 class="section-title !mb-0 mt-1">我的备考画像</h2>
      </div>
      <select v-model="exam" class="input !w-auto !py-1.5 !text-xs" aria-label="选择考试">
        <option v-for="(label, id) in examLabels" :key="id" :value="id">{{ label }}</option>
      </select>
    </div>
    <div v-if="loading" class="text-xs text-slate-400">正在根据练习证据诊断…</div>
    <div v-else-if="error" class="text-xs text-amber-600">{{ error }}</div>
    <template v-else-if="data">
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
        <div class="rounded-lg bg-slate-50 dark:bg-slate-700/50 p-2"><div class="font-bold text-primary-500">{{ data.profile?.foundation_level || '未设置' }}</div><div class="text-[10px] text-slate-400">基础判断</div></div>
        <div class="rounded-lg bg-slate-50 dark:bg-slate-700/50 p-2"><div class="font-bold text-emerald-500">{{ data.profile?.target_band || '未设置' }}</div><div class="text-[10px] text-slate-400">目标分数</div></div>
        <div class="rounded-lg bg-slate-50 dark:bg-slate-700/50 p-2"><div class="font-bold text-amber-500">{{ data.evidence_records || 0 }}</div><div class="text-[10px] text-slate-400">有效练习记录</div></div>
        <div class="rounded-lg bg-slate-50 dark:bg-slate-700/50 p-2"><div class="font-bold text-violet-500">{{ data.profile?.daily_time_budget_minutes || 0 }}分</div><div class="text-[10px] text-slate-400">每日预算</div></div>
      </div>
      <p class="text-sm leading-6 text-slate-700 dark:text-slate-200">{{ data.diagnosis }}</p>
      <div class="grid sm:grid-cols-3 gap-2 text-xs">
        <div class="rounded-lg border border-emerald-100 dark:border-emerald-900/40 px-3 py-2"><span class="text-slate-400">优势：</span>{{ data.strengths?.join('、') || '待积累证据' }}</div>
        <div class="rounded-lg border border-amber-100 dark:border-amber-900/40 px-3 py-2"><span class="text-slate-400">短板：</span>{{ data.gaps?.join('、') || '待积累证据' }}</div>
        <div class="rounded-lg border border-rose-100 dark:border-rose-900/40 px-3 py-2"><span class="text-slate-400">风险：</span>{{ topRisk ? `${topRisk.tag}（${topRisk.count}次）` : '暂无重复风险' }}</div>
      </div>
      <div class="flex flex-wrap gap-1.5">
        <span v-for="item in data.mastery" :key="item.module" class="rounded-full bg-primary-50 dark:bg-primary-900/30 px-2.5 py-1 text-[10px] text-primary-700 dark:text-primary-300">{{ item.title }} {{ item.score }}%</span>
      </div>
    </template>
  </section>
</template>
