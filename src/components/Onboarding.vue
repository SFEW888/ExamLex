<script setup lang="ts">
import { ref } from 'vue'
import { BookOpen, GraduationCap, Timer } from '@lucide/vue'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const step = ref(0)
const steps = [
  { icon: GraduationCap, title: '欢迎使用 ExamLex', desc: '记录英语学习、追踪证据、用 Agent 拆解写作、听力、阅读、翻译和词汇。' },
  { icon: BookOpen, title: '英语专项', desc: '写作、听力、阅读、翻译、词汇和基础知识各自成页，教材内容、练习记录和 Agent 分析互相联动。' },
  { icon: Timer, title: '番茄专注', desc: '25分钟番茄钟 + 白噪音，帮你保持专注，统计每日专注时长。' },
]

function finish() {
  store.updateSettings({ onboarded: true })
}
</script>

<template>
  <div class="fixed inset-0 z-[70] bg-black/50 flex items-center justify-center p-6">
    <div class="card !p-8 max-w-sm w-full text-center animate-pop">
      <div class="mb-4 flex justify-center">
        <component :is="steps[step].icon" class="w-16 h-16 text-primary-500" />
      </div>
      <h2 class="text-lg font-bold mb-2">{{ steps[step].title }}</h2>
      <p class="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">{{ steps[step].desc }}</p>
      <div class="flex justify-center gap-1.5 my-5">
        <span v-for="(s, i) in steps" :key="i" class="w-2 h-2 rounded-full" :class="i === step ? 'bg-primary-500' : 'bg-slate-200 dark:bg-slate-600'"></span>
      </div>
      <div class="flex gap-2 justify-center">
        <button v-if="step < steps.length - 1" class="btn-ghost" @click="finish">跳过</button>
        <button v-if="step < steps.length - 1" class="btn-primary" @click="step++">下一步</button>
        <button v-else class="btn-primary" @click="finish">开始使用</button>
      </div>
    </div>
  </div>
</template>
