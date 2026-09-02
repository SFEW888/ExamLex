<script setup lang="ts">
import { computed, onMounted, provide, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from './stores/app'
import { restartReminder } from './services/reminder'
import { startTodoReminder, checkTodoReminders } from './services/todoReminder'
import Toast from './components/Toast.vue'
import Onboarding from './components/Onboarding.vue'
import UpdateDialog from './components/UpdateDialog.vue'
import AgentDock from './components/AgentDock.vue'
import { isDndActive } from './utils/dnd'
import { ChevronDown } from '@lucide/vue'

const store = useAppStore()
const route = useRoute()
const router = useRouter()

// ExamLex is a private, local-first workspace. Social, account and community
// destinations are intentionally absent from the primary navigation.
type NavItem = { path: string; icon: string; label: string; children?: NavItem[] }

const NAV: NavItem[] = [
  { path: '/', icon: '⌂', label: '首页' },
  {
    path: '/english', icon: 'EN', label: '英语专项', children: [
      { path: '/english/writing', icon: '✎', label: '写作' },
      { path: '/english/listening', icon: '◖', label: '听力' },
      { path: '/english/reading', icon: '▤', label: '阅读' },
      { path: '/english/translation', icon: '译', label: '翻译' },
      { path: '/english/vocabulary', icon: '词', label: '词汇' },
      { path: '/english/basics', icon: '⌘', label: '基础知识' }
    ]
  },
  { path: '/practice/past-papers', icon: '✓', label: '真题' },
  { path: '/practice/mock', icon: '◇', label: '模拟题' },
  { path: '/pomodoro', icon: '◷', label: '专注' },
  { path: '/notes', icon: '▧', label: '笔记' },
  { path: '/daily-summary', icon: '≡', label: '每日总结' },
  { path: '/statistics', icon: '∿', label: '统计' },
  { path: '/error-book', icon: '!', label: '错题本' },
  { path: '/habits', icon: '☑', label: '习惯' },
  { path: '/materials', icon: '▥', label: '资料' },
  { path: '/settings', icon: '⚙', label: '设置' }
]

const mobileNav = computed(() =>
  ['/','/english','/practice/past-papers','/practice/mock','/pomodoro','/settings']
    .map(path => NAV.find(item => item.path === path))
    .filter((item): item is typeof NAV[number] => !!item)
)

const ENGLISH_NAV_KEY = 'examlex-english-nav-open'
const englishNavOpen = ref(localStorage.getItem(ENGLISH_NAV_KEY) !== '0' || route.path.startsWith('/english/'))
function toggleEnglishNav() {
  englishNavOpen.value = !englishNavOpen.value
  localStorage.setItem(ENGLISH_NAV_KEY, englishNavOpen.value ? '1' : '0')
}
watch(() => route.path, path => {
  if (path.startsWith('/english/')) englishNavOpen.value = true
})

const toastRef = ref<InstanceType<typeof Toast>>()
provide('toast', (msg: string) => toastRef.value?.show(msg))

function applyTheme() {
  const t = store.settings.theme
  const dark = t === 'dark' || (t === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches)
  document.documentElement.classList.toggle('dark', dark)
}

watch(
  () => [store.settings.reminderEnabled, store.settings.reminderTime] as const,
  () => restartReminder(
    () => ({ enabled: store.settings.reminderEnabled, time: store.settings.reminderTime, suppressed: isDndActive(store.settings) }),
    shown => { if (!shown) toastRef.value?.show('提醒时间到！该开始学习啦') }
  ),
  { immediate: true }
)

onMounted(() => {
  applyTheme()
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applyTheme)
  startTodoReminder({
    getTodos: () => store.todos,
    onNotified: (ids, kind) => store.markTodosNotified(ids, kind),
    onFallback: msg => toastRef.value?.show(msg),
    isSuppressed: () => isDndActive(store.settings)
  })
})

watch(
  () => store.todos.map(t => `${t.id}:${t.startAt ?? ''}:${t.dueAt ?? ''}:${t.done ? 1 : 0}`).join('|'),
  () => checkTodoReminders()
)

const NAV_COLLAPSED_KEY = 'examlex-nav-collapsed'
const navCollapsed = ref(localStorage.getItem(NAV_COLLAPSED_KEY) === '1')
function toggleNav() {
  navCollapsed.value = !navCollapsed.value
  localStorage.setItem(NAV_COLLAPSED_KEY, navCollapsed.value ? '1' : '0')
}
provide('navCollapsed', navCollapsed)

const isFullscreenPage = computed(() => route.path === '/pomodoro')
const isNotesEditing = computed(() => route.path === '/notes' && (!!route.query.id || route.query.new === '1'))
const hideNav = computed(() => isFullscreenPage.value)
const showOnboarding = computed(() => !store.settings.onboarded && !isFullscreenPage.value)

function isNavActive(path: string) {
  if (path === '/') return route.path === '/'
  return route.path === path || route.path.startsWith(path + '/')
}

if (window.nav) window.nav.onNav((target) => router.push(target))
</script>

<template>
  <div class="min-h-screen">
    <aside v-if="!hideNav" class="hidden md:flex fixed inset-y-0 left-0 flex-col bg-white dark:bg-slate-800 border-r border-slate-100 dark:border-slate-700 z-30 transition-all duration-200" :class="navCollapsed ? 'w-16' : 'w-56'">
      <div class="px-5 py-5" :class="navCollapsed ? '!px-3' : ''">
        <div class="flex items-center gap-2 text-lg font-bold text-primary-600 dark:text-primary-400" :class="navCollapsed ? 'justify-center' : ''">
          <img src="/logo.png" alt="ExamLex" class="w-8 h-8 shrink-0" /><span v-if="!navCollapsed">ExamLex</span>
        </div>
        <div v-if="!navCollapsed" class="text-xs text-slate-400 mt-1">{{ store.settings.userName }} · 私人学习空间</div>
      </div>
      <div v-if="store.examCountdown !== null && !navCollapsed" class="mx-4 mb-3 rounded-xl bg-gradient-to-r from-primary-500 to-primary-600 text-white px-3 py-2 text-center">
        <div class="text-[10px] opacity-80">距考试还有</div>
        <div class="text-xl font-bold leading-tight">{{ store.examCountdown }} 天</div>
      </div>
      <nav class="flex-1 overflow-y-auto px-3 space-y-1 pb-4" :class="navCollapsed ? '!px-2' : ''">
        <template v-for="item in NAV" :key="item.path">
          <div v-if="item.children" class="space-y-1">
            <div class="flex items-center gap-1">
              <RouterLink :to="item.path" class="flex-1 flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors" :class="[isNavActive(item.path) ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 font-semibold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700', navCollapsed ? 'justify-center !px-2' : '']" :title="navCollapsed ? item.label : ''">
                <span class="text-sm font-semibold w-5 text-center">{{ item.icon }}</span><span v-if="!navCollapsed">{{ item.label }}</span>
              </RouterLink>
              <button v-if="!navCollapsed" class="w-7 h-7 shrink-0 rounded-lg text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 flex items-center justify-center" :aria-label="englishNavOpen ? '收起英语专项子栏目' : '展开英语专项子栏目'" :title="englishNavOpen ? '收起子栏目' : '展开子栏目'" @click="toggleEnglishNav">
                <ChevronDown :size="15" class="transition-transform" :class="englishNavOpen ? 'rotate-180' : ''" />
              </button>
            </div>
            <div v-if="englishNavOpen && !navCollapsed" class="ml-5 pl-3 border-l border-slate-200 dark:border-slate-700 space-y-0.5">
              <RouterLink v-for="child in item.children" :key="child.path" :to="child.path" class="flex items-center gap-2 rounded-lg px-2.5 py-2 text-xs transition-colors" :class="isNavActive(child.path) ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 font-semibold' : 'text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700'">
                <span class="w-4 text-center font-semibold">{{ child.icon }}</span><span>{{ child.label }}</span>
              </RouterLink>
            </div>
          </div>
          <RouterLink v-else :to="item.path" class="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors" :class="[isNavActive(item.path) ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 font-semibold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700', navCollapsed ? 'justify-center !px-2' : '']" :title="navCollapsed ? item.label : ''">
            <span class="text-sm font-semibold w-5 text-center">{{ item.icon }}</span><span v-if="!navCollapsed">{{ item.label }}</span>
          </RouterLink>
        </template>
      </nav>
      <button class="mx-3 mb-2 flex items-center gap-2 rounded-xl px-3 py-2 text-xs text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors" :class="navCollapsed ? 'justify-center !px-2' : ''" :title="navCollapsed ? '展开导航' : '收起导航'" @click="toggleNav">
        <span>{{ navCollapsed ? '»' : '«' }}</span><span v-if="!navCollapsed">收起导航</span>
      </button>
      <div v-if="!navCollapsed" class="mx-3 mb-3 rounded-xl bg-purple-50 dark:bg-purple-500/10 px-3 py-2 text-center">
        <div class="text-[15px] font-bold leading-none text-purple-600 dark:text-purple-400">{{ store.gamification.streak }}</div>
        <div class="text-[10px] text-slate-400 mt-0.5">连续学习天数</div>
      </div>
    </aside>

    <div v-if="!hideNav && !isNotesEditing" class="fixed top-3 right-4 z-40 flex items-center gap-2">
      <span class="hidden sm:inline-flex items-center rounded-full bg-slate-100 dark:bg-slate-700 px-3 py-1.5 text-[11px] text-slate-500 dark:text-slate-300">私有本地模式</span>
      <RouterLink to="/settings" class="w-9 h-9 rounded-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-500 flex items-center justify-center shadow-sm" aria-label="打开设置" title="设置">⚙</RouterLink>
    </div>

    <main :class="hideNav ? '' : (navCollapsed ? 'md:pl-16' : 'md:pl-56') + ' pb-20 md:pb-6' + (isNotesEditing ? '' : ' pt-14')">
      <RouterView v-slot="{ Component }"><Transition name="fade"><component :is="Component" /></Transition></RouterView>
    </main>

    <nav v-if="!hideNav" class="md:hidden fixed bottom-0 inset-x-0 bg-white dark:bg-slate-800 border-t border-slate-100 dark:border-slate-700 z-30 flex justify-around py-1.5" style="padding-bottom: env(safe-area-inset-bottom)">
      <RouterLink v-for="item in mobileNav" :key="item.path" :to="item.path" class="flex flex-col items-center px-2 py-1 text-[10px] rounded-lg max-w-[64px]" :class="isNavActive(item.path) ? 'text-primary-600 dark:text-primary-400 font-semibold' : 'text-slate-500 dark:text-slate-400'">
        <span class="text-sm font-semibold leading-none">{{ item.icon }}</span><span class="truncate w-full text-center mt-0.5">{{ item.label }}</span>
      </RouterLink>
    </nav>

    <Toast ref="toastRef" />
    <Onboarding v-if="showOnboarding" />
    <UpdateDialog />
    <AgentDock />
  </div>
</template>
