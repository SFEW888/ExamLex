<script setup lang="ts">
import { computed, inject, onUnmounted, ref, watch } from 'vue'
import { useAppStore } from '../stores/app'
import { today, formatMinutes } from '../utils/date'
import { MOODS } from '../data/defaults'
import dayjs from 'dayjs'
import { useOverlayDismiss } from '../composables/useOverlayDismiss'

const store = useAppStore()
const activeExam = localStorage.getItem('examlex-active-exam') || 'CET4'
const toast = inject<(m: string) => void>('toast', () => {})

// 编辑区固定为「今日」总结；往日总结通过点击日历弹出悬浮卡片查看
// 定时器驱动：页面挂载跨午夜后自动切换到新的一天，并重载表单内容
const editDate = ref(today())
const dayTimer = setInterval(() => {
  if (editDate.value !== today()) editDate.value = today()
}, 60000)
onUnmounted(() => clearInterval(dayTimer))

const form = ref({ mood: '', harvest: '', improve: '', plan: '' })
const aiSummary = ref<any>(null)
const aiLoading = ref(false)
const aiError = ref('')
async function generateAiSummary() {
  aiLoading.value = true
  aiError.value = ''
  try {
    const response = await fetch(`/api/summary/ai?exam=${encodeURIComponent(activeExam)}&date=${encodeURIComponent(editDate.value)}`)
    const payload = await response.json()
    if (!response.ok) throw new Error(payload.error || 'AI 总结暂不可用')
    aiSummary.value = payload
  } catch (error: any) {
    aiError.value = error?.message || 'AI 总结暂不可用'
  } finally { aiLoading.value = false }
}
watch(editDate, (d, oldD) => {
  // 跨午夜切换时若存在未保存的编辑内容则保留，避免静默丢失用户输入
  // immediate 首次触发无旧值，oldD 为 undefined，直接跳过索引取 prev
  const prev = oldD === undefined ? undefined : store.summaries[oldD]
  const dirty = form.value.mood !== (prev?.mood || '')
    || form.value.harvest !== (prev?.harvest || '')
    || form.value.improve !== (prev?.improve || '')
    || form.value.plan !== (prev?.plan || '')
  if (dirty) {
    toast('已跨到新的一天，未保存的总结内容已保留，请及时保存')
    return
  }
  const s = store.summaries[d]
  form.value = {
    mood: s?.mood || '',
    harvest: s?.harvest || '',
    improve: s?.improve || '',
    plan: s?.plan || ''
  }
}, { immediate: true })

/** 聚合某日期的全维度数据概览 */
function aggregateDay(d: string) {
  const records = store.records.filter(r => r.date === d)
  const minutes = records.reduce((s, r) => s + r.minutes, 0)
  const problems = store.problemSessions.filter(p => p.date === d)
  const pTotal = problems.reduce((s, p) => s + p.total, 0)
  const pCorrect = problems.reduce((s, p) => s + p.correct, 0)
  const pomo = store.pomodoro.daily[d] || { count: 0, minutes: 0, interruptions: 0 }
  const bySubject: Record<string, number> = {}
  for (const r of records) bySubject[r.subjectId] = (bySubject[r.subjectId] || 0) + r.minutes
  return { minutes, pTotal, pCorrect, pomo, bySubject, accuracy: pTotal ? Math.round(pCorrect / pTotal * 100) : null }
}

// ---- 当日数据聚合 ----
const dayData = computed(() => aggregateDay(editDate.value))

/** 保存可选个人备注；客观结论由 AI 总结接口生成，不被主观文本覆盖。 */
function save(): boolean {
  if (!form.value.mood && !form.value.harvest.trim() && !form.value.improve.trim() && !form.value.plan.trim()) {
    toast('没有可保存的个人备注')
    return false
  }
  const isNew = !store.summaries[editDate.value]
  store.saveSummary({ date: editDate.value, ...form.value })
  toast(isNew ? '每日总结已保存' : '每日总结已更新')
  return true
}

// ---- 往日总结悬浮卡片 ----
const cardDate = ref('')
const { onOverlayMousedown: onCardMousedown, onOverlayClick: onCardClick } = useOverlayDismiss(() => { cardDate.value = '' })
/** 明日计划板块开关：用户可选择展示/隐藏，默认不强制显示 */
const showPlan = ref(false)
const cardData = computed(() => (cardDate.value ? aggregateDay(cardDate.value) : null))
const cardSummary = computed(() => (cardDate.value ? store.summaries[cardDate.value] : undefined))
/** 点击往日日期：弹出当日总结悬浮卡片；今日日期在页面直接编辑 */
function openDayCard(d: string) {
  if (d === today()) return
  cardDate.value = d
  showPlan.value = false
}

// Esc 关闭悬浮卡片
function onCardKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') cardDate.value = ''
}
watch(cardDate, v => {
  if (v) window.addEventListener('keydown', onCardKeydown)
  else window.removeEventListener('keydown', onCardKeydown)
})
onUnmounted(() => window.removeEventListener('keydown', onCardKeydown))

// ---- 日历 ----
const calMonth = ref(dayjs().format('YYYY-MM'))
// 跨午夜/跨月后日历自动切换到当前月
watch(editDate, d => {
  const m = dayjs(d).format('YYYY-MM')
  if (calMonth.value !== m) calMonth.value = m
})
const calendarDays = computed(() => {
  const start = dayjs(calMonth.value + '-01')
  const firstWeekday = start.day()
  const daysInMonth = start.daysInMonth()
  const cells: (string | null)[] = Array(firstWeekday).fill(null)
  for (let i = 1; i <= daysInMonth; i++) cells.push(start.date(i).format('YYYY-MM-DD'))
  return cells
})
function hasSummary(d: string | null) {
  if (!d) return false
  const s = store.summaries[d]
  return !!(s && (s.harvest || s.improve || s.plan || s.mood))
}
function hasRecord(d: string | null) {
  return d ? !!store.minutesByDate[d] : false
}

</script>

<template>
  <div class="p-4 md:p-6 max-w-5xl mx-auto space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="page-title">每日总结</h1>
      <span class="text-xs text-slate-400">仅保存在本地</span>
    </div>

    <div class="grid lg:grid-cols-3 gap-4">
      <!-- 编辑区 -->
      <div class="lg:col-span-2 space-y-4">
        <div class="card">
          <div class="flex items-center justify-between mb-3">
            <div class="section-title !mb-0">今日数据概览</div>
            <span class="text-xs text-slate-400">{{ editDate }}</span>
          </div>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
            <div class="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-2">
              <div class="font-black text-primary-500">{{ formatMinutes(dayData.minutes) }}</div>
              <div class="text-[10px] text-slate-400">学习时长</div>
            </div>
            <div class="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-2">
              <div class="font-black text-emerald-500">{{ dayData.pTotal }}</div>
              <div class="text-[10px] text-slate-400">刷题数</div>
            </div>
            <div class="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-2">
              <div class="font-black text-amber-500">{{ dayData.accuracy === null ? '—' : dayData.accuracy + '%' }}</div>
              <div class="text-[10px] text-slate-400">正确率</div>
            </div>
            <div class="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-2">
              <div class="font-black text-orange-500">{{ dayData.pomo.count }}</div>
              <div class="text-[10px] text-slate-400">番茄钟</div>
            </div>
          </div>
          <div v-if="Object.keys(dayData.bySubject).length" class="flex gap-2 mt-3 flex-wrap">
            <span v-for="(min, sid) in dayData.bySubject" :key="sid" class="text-xs px-2 py-1 rounded-full text-white"
              :style="{ background: store.subjectMap[sid]?.color || '#94a3b8' }">
              {{ store.subjectMap[sid]?.name }} {{ formatMinutes(min) }}
            </span>
          </div>
          <div class="mt-4 border-t border-slate-100 dark:border-slate-700 pt-3">
            <div class="flex items-center justify-between gap-2">
              <div><div class="text-sm font-semibold">AI 客观总结</div><div class="text-[10px] text-slate-400">只使用练习、错误、复习和计时数据生成</div></div>
              <button class="btn-primary !py-1.5 !text-xs" :disabled="aiLoading" @click="generateAiSummary">{{ aiLoading ? '分析中…' : '生成 AI 总结' }}</button>
            </div>
            <p v-if="aiError" class="text-xs text-amber-600 mt-2">{{ aiError }}</p>
            <div v-if="aiSummary" class="mt-2 rounded-lg bg-primary-50 dark:bg-primary-900/20 p-3 text-sm leading-6">
              <p>{{ aiSummary.summary }}</p>
              <div class="grid sm:grid-cols-3 gap-2 mt-3 text-xs">
                <div><span class="text-slate-400">明日：</span>{{ aiSummary.next_day?.total_planned_minutes || 0 }} 分钟</div>
                <div><span class="text-slate-400">下周：</span>{{ aiSummary.next_week?.total_planned_minutes || 0 }} 分钟</div>
                <div><span class="text-slate-400">下月：</span>{{ aiSummary.next_month?.total_planned_minutes || 0 }} 分钟</div>
              </div>
            </div>
          </div>
        </div>

        <div class="card space-y-4">
          <div class="text-[10px] text-slate-400">个人备注（不会覆盖 AI 统计结论）</div>
          <div>
            <label class="label">今日心情</label>
            <div class="grid grid-cols-4 sm:grid-cols-8 gap-1.5">
              <button v-for="m in MOODS" :key="m" class="btn !text-xs !px-1"
                :class="form.mood === m ? 'bg-primary-500 text-white' : 'bg-slate-100 dark:bg-slate-700'"
                @click="form.mood = m">{{ m }}</button>
            </div>
          </div>
          <div>
            <label class="label">今日收获</label>
            <textarea v-model="form.harvest" rows="3" class="input" placeholder="今天学到了什么？有什么进步？"></textarea>
          </div>
          <div>
            <label class="label">不足反思</label>
            <textarea v-model="form.improve" rows="3" class="input" placeholder="哪里做得不够好？如何改进？"></textarea>
          </div>
          <div>
            <label class="label">明日计划</label>
            <textarea v-model="form.plan" rows="3" class="input" placeholder="明天要完成什么？"></textarea>
          </div>
          <button class="btn-primary w-full" @click="save">保存个人备注</button>
        </div>
      </div>

      <!-- 历史日历 -->
      <div class="card h-fit">
        <div class="flex items-center justify-between mb-3">
          <button class="btn-ghost !p-1.5" @click="calMonth = dayjs(calMonth).subtract(1, 'month').format('YYYY-MM')">←</button>
          <span class="text-sm font-semibold">{{ dayjs(calMonth + '-01').format('YYYY年M月') }}</span>
          <button class="btn-ghost !p-1.5" @click="calMonth = dayjs(calMonth).add(1, 'month').format('YYYY-MM')">→</button>
        </div>
        <div class="grid grid-cols-7 gap-1 text-center text-[10px] text-slate-400 mb-1">
          <span v-for="w in ['日','一','二','三','四','五','六']" :key="w">{{ w }}</span>
        </div>
        <div class="grid grid-cols-7 gap-1">
          <button v-for="(d, i) in calendarDays" :key="i" :disabled="!d"
            class="aspect-square rounded-lg text-xs flex items-center justify-center relative transition-colors"
            :class="[
              !d ? '' : d === editDate ? 'bg-primary-500 text-white font-bold' : 'hover:bg-slate-100 dark:hover:bg-slate-700',
            ]"
            :title="d && d !== editDate ? '点击查看当日总结卡片' : ''"
            @click="d && openDayCard(d)">
            {{ d ? Number(d.slice(-2)) : '' }}
            <span v-if="hasSummary(d)" class="absolute bottom-0.5 w-1 h-1 rounded-full" :class="d === editDate ? 'bg-white' : 'bg-emerald-400'"></span>
            <span v-else-if="hasRecord(d)" class="absolute bottom-0.5 w-1 h-1 rounded-full" :class="d === editDate ? 'bg-white' : 'bg-primary-300'"></span>
          </button>
        </div>
        <div class="text-[10px] text-slate-400 mt-2 flex gap-3">
          <span><span class="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1"></span>已写总结</span>
          <span><span class="inline-block w-1.5 h-1.5 rounded-full bg-primary-300 mr-1"></span>有学习</span>
        </div>
        <p class="text-[10px] text-slate-400 mt-1">点击往日日期，弹出当日总结悬浮卡片</p>
      </div>
    </div>

    <!-- 往日总结悬浮卡片 -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="cardDate && cardData" class="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" @mousedown="onCardMousedown" @click="onCardClick">
          <div class="bg-white dark:bg-slate-800 rounded-2xl w-full max-w-md max-h-[85vh] overflow-y-auto shadow-2xl animate-pop"
            role="dialog" aria-modal="true" :aria-label="`${cardDate} 总结`">
            <div class="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-700 sticky top-0 bg-white dark:bg-slate-800">
              <h3 class="font-bold">{{ cardDate }} 总结</h3>
              <button class="text-slate-400 hover:text-slate-600 text-xl leading-none" @click="cardDate = ''" aria-label="关闭">×</button>
            </div>
            <div class="px-5 py-4 space-y-4">
              <!-- ① 当日全维度数据概览（必填） -->
              <div>
                <div class="text-xs font-semibold text-slate-400 mb-2">当日数据概览</div>
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                  <div class="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-2">
                    <div class="font-black text-primary-500">{{ formatMinutes(cardData.minutes) }}</div>
                    <div class="text-[10px] text-slate-400">学习时长</div>
                  </div>
                  <div class="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-2">
                    <div class="font-black text-emerald-500">{{ cardData.pTotal }}</div>
                    <div class="text-[10px] text-slate-400">刷题数</div>
                  </div>
                  <div class="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-2">
                    <div class="font-black text-amber-500">{{ cardData.accuracy === null ? '—' : cardData.accuracy + '%' }}</div>
                    <div class="text-[10px] text-slate-400">正确率</div>
                  </div>
                  <div class="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-2">
                    <div class="font-black text-orange-500">{{ cardData.pomo.count }}</div>
                    <div class="text-[10px] text-slate-400">番茄钟</div>
                  </div>
                </div>
                <div v-if="Object.keys(cardData.bySubject).length" class="flex gap-2 mt-2 flex-wrap">
                  <span v-for="(min, sid) in cardData.bySubject" :key="sid" class="text-xs px-2 py-1 rounded-full text-white"
                    :style="{ background: store.subjectMap[sid]?.color || '#94a3b8' }">
                    {{ store.subjectMap[sid]?.name }} {{ formatMinutes(min) }}
                  </span>
                </div>
              </div>
              <!-- ② 当日心情（必填） -->
              <div>
                <div class="text-xs font-semibold text-slate-400 mb-1">当日心情</div>
                <p class="text-sm">{{ cardSummary?.mood || '未填写' }}</p>
              </div>
              <!-- ③ 当日收获（必填） -->
              <div>
                <div class="text-xs font-semibold text-slate-400 mb-1">当日收获</div>
                <p class="text-sm whitespace-pre-wrap leading-relaxed">{{ cardSummary?.harvest || '未填写' }}</p>
              </div>
              <!-- ④ 当日反思（必填） -->
              <div>
                <div class="text-xs font-semibold text-slate-400 mb-1">当日反思</div>
                <p class="text-sm whitespace-pre-wrap leading-relaxed">{{ cardSummary?.improve || '未填写' }}</p>
              </div>
              <!-- 明日计划（可选配置：开关控制展示/隐藏） -->
              <div class="border-t border-slate-100 dark:border-slate-700 pt-3">
                <div class="flex items-center justify-between">
                  <span class="text-xs font-semibold text-slate-400">明日计划</span>
                  <button class="text-xs px-2.5 py-1 rounded-full transition-colors"
                    :class="showPlan ? 'bg-primary-500 text-white' : 'bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400'"
                    :aria-pressed="showPlan"
                    @click="showPlan = !showPlan">
                    {{ showPlan ? '已展示 · 点击隐藏' : '已隐藏 · 点击展示' }}
                  </button>
                </div>
                <p v-if="showPlan" class="text-sm whitespace-pre-wrap leading-relaxed mt-2">{{ cardSummary?.plan || '未填写' }}</p>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>
