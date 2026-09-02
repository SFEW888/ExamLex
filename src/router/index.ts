import { createRouter, createWebHashHistory } from 'vue-router'

// Private ExamLex routes. Authentication, community, messaging and team
// routes are intentionally not registered in the personal edition.
const routes = [
  { path: '/', name: 'dashboard', component: () => import('../pages/Dashboard.vue'), meta: { title: '首页' } },
  { path: '/math', name: 'math', component: () => import('../pages/Math.vue'), meta: { title: '高等数学' } },
  { path: '/english', name: 'english', component: () => import('../pages/English.vue'), meta: { title: '英语专项' } },
  { path: '/english/:module', name: 'english-module', component: () => import('../pages/ExamModule.vue'), meta: { title: '英语专项' } },
  { path: '/practice/past-papers', name: 'past-papers', component: () => import('../pages/PracticeLibrary.vue'), props: { kind: 'past' }, meta: { title: '历年真题' } },
  { path: '/practice/mock', name: 'mock-practice', component: () => import('../pages/PracticeLibrary.vue'), props: { kind: 'mock' }, meta: { title: '模拟特训' } },
  { path: '/practice/session/:id?', name: 'practice-session', component: () => import('../pages/PracticeSession.vue'), meta: { title: '专项练习' } },
  { path: '/subject/:id', name: 'subject', component: () => import('../pages/Subject.vue'), meta: { title: '科目' } },
  { path: '/error-book', name: 'error-book', component: () => import('../pages/ErrorBook.vue'), meta: { title: '错题本' } },
  { path: '/pomodoro', name: 'pomodoro', component: () => import('../pages/Pomodoro.vue'), meta: { title: '番茄钟' } },
  { path: '/habits', name: 'habits', component: () => import('../pages/Habits.vue'), meta: { title: '习惯追踪' } },
  { path: '/daily-summary', name: 'daily-summary', component: () => import('../pages/DailySummary.vue'), meta: { title: '每日总结' } },
  { path: '/daily-summary/:date', redirect: '/daily-summary' },
  { path: '/notes', name: 'notes', component: () => import('../pages/Notes.vue'), meta: { title: '笔记' } },
  { path: '/statistics', name: 'statistics', component: () => import('../pages/Statistics.vue'), meta: { title: '数据统计' } },
  { path: '/materials', name: 'materials', component: () => import('../pages/Materials.vue'), meta: { title: '资料库' } },
  { path: '/settings', name: 'settings', component: () => import('../pages/Settings.vue'), meta: { title: '设置' } }
]

export const router = createRouter({ history: createWebHashHistory(), routes })

router.afterEach((to) => {
  document.title = `${to.meta.title || ''} · ExamLex 英语备考系统`
})

const ROUTE_RELOAD_KEY = 'route-error-reloaded'
router.onError((err, to) => {
  console.error(`页面加载失败: ${to.fullPath}`, err)
  if (sessionStorage.getItem(ROUTE_RELOAD_KEY)) return
  sessionStorage.setItem(ROUTE_RELOAD_KEY, '1')
  window.location.reload()
})

router.afterEach(() => sessionStorage.removeItem(ROUTE_RELOAD_KEY))
