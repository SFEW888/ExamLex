<script setup lang="ts">
import { computed } from 'vue'
import dayjs from 'dayjs'

const props = withDefaults(defineProps<{
  data: Record<string, number>
  weeks?: number
  year?: number
  annual?: boolean
  yearDays?: Array<{ date: string; minutes: number; score?: number; level?: number; tasks?: number; items?: number }>
}>(), { weeks: 20 })

/** 点击某个日期格子时触发，携带日期 YYYY-MM-DD */
const emit = defineEmits<{ select: [date: string] }>()

/** GitHub 风格贡献热力图 */
type HeatCell = { date: string; value: number; level: number; outside: boolean; tasks?: number; items?: number }

const colors = ['bg-slate-100 dark:bg-slate-700', 'bg-primary-200', 'bg-primary-300', 'bg-primary-500', 'bg-primary-700']

const cells = computed<HeatCell[][]>(() => {
  if (props.annual) {
    const year = props.year || dayjs().year()
    const first = dayjs(`${year}-01-01`)
    const last = dayjs(`${year}-12-31`)
    const byDate = new Map((props.yearDays || []).map(item => [item.date, item]))
    const result: HeatCell[][] = []
    let week: HeatCell[] = []
    // Sunday aligned columns make the annual view scan like a calendar.
    for (let d = first.subtract(first.day(), 'day'); !d.isAfter(last) || week.length; d = d.add(1, 'day')) {
      const key = d.format('YYYY-MM-DD')
      const inYear = d.year() === year
      const item = byDate.get(key)
      const value = inYear ? (item?.minutes || props.data[key] || 0) : 0
      const level = inYear
        ? (typeof item?.level === 'number' ? item.level : value <= 0 ? 0 : value < 60 ? 1 : value < 120 ? 2 : value < 240 ? 3 : 4)
        : 0
      week.push({ date: key, value, level, outside: !inYear, tasks: item?.tasks, items: item?.items })
      if (week.length === 7) { result.push(week); week = [] }
      if (d.isSame(last, 'day')) break
    }
    if (week.length) result.push(week)
    return result
  }

  const result: HeatCell[][] = []
  const end = dayjs()
  const start = end.subtract(props.weeks * 7 - 1, 'day')
  const startSunday = start.subtract(start.day(), 'day')
  let week: { date: string; value: number; level: number }[] = []
  for (let d = startSunday; !d.isAfter(end); d = d.add(1, 'day')) {
    const key = d.format('YYYY-MM-DD')
    const v = d.isAfter(end) ? -1 : (props.data[key] || 0)
    const level = v <= 0 ? 0 : v < 60 ? 1 : v < 120 ? 2 : v < 240 ? 3 : 4
    week.push({ date: key, value: v, level, outside: false })
    if (week.length === 7) { result.push(week); week = [] }
  }
  if (week.length) result.push(week)
  return result
})
</script>

<template>
  <div class="overflow-x-auto">
    <div v-if="annual" class="flex gap-[3px] w-max min-w-full" aria-label="全年学习热力图">
      <div v-for="(week, wi) in cells" :key="wi" class="flex flex-col gap-[3px]">
        <div class="h-4 text-[9px] text-slate-400 whitespace-nowrap">
          <span v-if="week.some(cell => !cell.outside && cell.date.endsWith('-01'))">{{ dayjs(week.find(cell => !cell.outside && cell.date.endsWith('-01'))?.date).format('M月') }}</span>
        </div>
        <div v-for="cell in week" :key="cell.date"
          class="w-3 h-3 rounded-sm transition-transform hover:scale-125"
          :class="[cell.outside ? 'opacity-0' : colors[cell.level], cell.outside ? '' : 'cursor-pointer']"
          :title="cell.outside ? '' : `${cell.date}：${cell.value}分钟${cell.tasks !== undefined ? `，${cell.tasks}项任务` : ''}${cell.items !== undefined ? `，${cell.items}题` : ''}`"
          @click="!cell.outside && emit('select', cell.date)">
        </div>
      </div>
    </div>
    <div v-else class="flex gap-[3px] w-max">
      <div v-for="(week, wi) in cells" :key="wi" class="flex flex-col gap-[3px]">
        <div v-for="cell in week" :key="cell.date"
          class="w-3 h-3 rounded-sm transition-transform hover:scale-125"
          :class="[cell.value < 0 ? 'opacity-0' : colors[cell.level], cell.value >= 0 ? 'cursor-pointer' : '']"
          :title="cell.value >= 0 ? `${cell.date}：${cell.value}分钟（点击查看明细）` : ''"
          @click="cell.value >= 0 && emit('select', cell.date)">
        </div>
      </div>
    </div>
    <div class="flex items-center gap-1 mt-2 text-[10px] text-slate-400">
      少 <span v-for="c in colors" :key="c" class="w-2.5 h-2.5 rounded-sm" :class="c"></span> 多
    </div>
  </div>
</template>
