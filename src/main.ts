import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { registerSW } from 'virtual:pwa-register'
import App from './App.vue'
import { router } from './router'
import { useAppStore } from './stores/app'
import './style.css'

// PWA：注册 Service Worker（autoUpdate 模式，新版本发布后台自动更新）
registerSW({ immediate: true })

async function bootstrap() {
  const app = createApp(App)
  const pinia = createPinia()
  app.use(pinia)

  // 私人模式从本地快照恢复，不建立账号或云端会话。
  const store = useAppStore(pinia)
  await store.hydrate()

  // 页面关闭/刷新前兜底推送防抖窗口内的未保存修改
  window.addEventListener('beforeunload', () => store.flushSave())

  app.use(router)
  app.mount('#app')
}

bootstrap().catch(e => {
  console.error('应用初始化失败', e)
  document.body.innerHTML = '<p style="padding:2rem;text-align:center;color:#888">应用初始化失败，请刷新重试</p>'
})
