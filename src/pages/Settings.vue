<script setup lang="ts">
import { computed, inject, onMounted, ref } from 'vue'
import { useAppStore } from '../stores/app'
import Modal from '../components/Modal.vue'
import { isDesktopNotify, notifyPermission, requestNotifyPermission } from '../services/notify'
import { subjectLabel } from '../utils/subject'

const store = useAppStore()
const toast = inject<(m: string) => void>('toast', () => {})
const s = computed(() => store.settings)

const storageUsage = ref('—')
const providerModels = ref<any[]>([])
const configuredProviders = ref<any[]>([])
const providerForm = ref({ provider_id: 'deepseek', endpoint: '', model: '', api_key_env: '' })
const providerMessage = ref('')
async function loadProviders() {
  try {
    const payload = await fetch('/api/providers').then(response => response.ok ? response.json() : null)
    configuredProviders.value = payload?.providers || []
  } catch { configuredProviders.value = [] }
}
onMounted(async () => {
  try { storageUsage.value = await store.storageUsageText() } catch { /* 忽略 */ }
  try {
    const payload = await fetch('/api/agent/manifest').then(response => response.ok ? response.json() : null)
    providerModels.value = payload?.capabilities?.models || []
  } catch { providerModels.value = [] }
  await loadProviders()
})

async function saveProvider() {
  providerMessage.value = ''
  try {
    const response = await fetch('/api/providers', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(providerForm.value) })
    const payload = await response.json()
    if (!response.ok) throw new Error(payload.error || '保存失败')
    providerMessage.value = 'Provider 配置已保存。API Key 仅从指定环境变量读取，不会写入本地状态。'
    await loadProviders()
    const manifest = await fetch('/api/agent/manifest').then(r => r.json())
    providerModels.value = manifest?.capabilities?.models || providerModels.value
  } catch (error: any) { providerMessage.value = error?.message || '保存失败' }
}

function selectProvider(item: any) {
  providerForm.value.provider_id = item.provider || item.id
  providerForm.value.model = item.model || ''
  providerForm.value.endpoint = item.provider === 'custom' ? '' : ''
  providerForm.value.api_key_env = ''
}

function update(key: string, value: any) {
  store.updateSettings({ [key]: value })
}

function applyTheme(t: string) {
  update('theme', t)
  const dark = t === 'dark' || (t === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches)
  document.documentElement.classList.toggle('dark', dark)
}

// 统一通知权限（桌面端经 preload 桥接原生通知，无需授权；浏览器端走 Web Notification）
const notifSupported = isDesktopNotify() || (typeof window !== 'undefined' && 'Notification' in window)
const notifPermission = ref(notifyPermission())

// 手动检查更新（仅桌面端打包环境可用）
const updater = (window as any).updater
function checkUpdate() {
  if (!updater) return
  updater.check()
  toast('正在检查更新…')
}

async function toggleReminder(v: boolean) {
  if (v && notifSupported) {
    const perm = await requestNotifyPermission()
    notifPermission.value = perm
    if (perm !== 'granted' && perm !== 'desktop') {
      if (perm === 'denied') {
        toast('通知权限已被拒绝，请在浏览器地址栏左侧的站点设置中手动开启通知')
      } else {
        toast('未授权通知权限，无法开启提醒')
      }
      return
    }
  }
  update('reminderEnabled', v)
  toast(v ? '已开启每日提醒（保持应用运行有效）' : '已关闭提醒')
}

// ---- 数据管理 ----
function exportData() {
  const blob = new Blob([store.exportJSON()], { type: 'application/json' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `ExamLex学习数据_${new Date().toISOString().slice(0, 10)}.json`
  a.click()
  URL.revokeObjectURL(a.href)
  toast('数据已导出')
}

const importFile = ref<HTMLInputElement>()
async function onImport(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = async () => {
    if (store.importJSON(reader.result as string)) {
      toast('导入成功！')
        // 立即写入本地快照，避免 reload 与防抖 save() 竞态导致数据丢失
      try {
        await store.saveAsync()
      } catch {
        toast('本地保存失败，请稍后重试')
      }
      setTimeout(() => location.reload(), 300)
    } else toast('导入失败：文件格式不正确')
  }
  reader.readAsText(file)
}

const showClearConfirm = ref(false)
const clearText = ref('')
async function clearAll() {
  if (clearText.value !== '确认清除') return
  store.clearAll()
  showClearConfirm.value = false
  toast('数据已清除')
  // 立即写入本地快照，避免 reload 与防抖 save() 竞态
  try {
    await store.saveAsync()
  } catch {
    toast('本地保存失败，请稍后重试')
  }
  setTimeout(() => location.reload(), 300)
}

// ---- 自定义科目 ----
const showSubject = ref(false)
const subForm = ref({ name: '', icon: '', color: '#8b5cf6', weight: 20 })
function addSubject() {
  if (!subForm.value.name.trim()) return
  store.addSubject({ ...subForm.value })
  showSubject.value = false
  subForm.value = { name: '', icon: '', color: '#8b5cf6', weight: 20 }
  toast('科目已添加，独立页面已生成')
}
/** 修改科目权重；无效/空输入恢复原值并提示 */
function onWeightChange(id: string, e: Event) {
  const input = e.target as HTMLInputElement
  const v = Number(input.value)
  if (input.value.trim() === '' || Number.isNaN(v)) {
    input.value = String(store.subjectMap[id]?.weight ?? 0)
    toast('权重输入无效，已恢复原值')
    return
  }
  store.updateSubjectWeight(id, v)
  input.value = String(store.subjectMap[id]?.weight ?? v)
  toast('权重已更新')
}

/** 删除任意科目（含内置），级联清理关联学习数据，删除后对应科目页面自动隐藏 */
function removeSubject(id: string, name: string) {
  const extra = id === 'english' ? '，英语专项数据（词汇/阅读/听力/作文模板）也将永久删除' : ''
  if (!window.confirm(`删除「${name}」？其学习记录、笔记、刷题、错题、真题将一并删除${extra}，删除后该科目页面自动隐藏。`)) return
  store.removeSubject(id)
  toast('科目已删除，关联学习数据已同步清理')
}

// ---- 恢复默认科目 ----
const showRestoreConfirm = ref(false)
function restoreDefaults() {
  const restored = store.restoreDefaultSubjects()
  showRestoreConfirm.value = false
  toast(restored > 0 ? `已恢复 ${restored} 个内置科目` : '内置科目均已存在，无需恢复')
}

// ---- 名言管理 ----
const newQuote = ref('')
function addQuote() {
  if (!newQuote.value.trim()) return
  store.settings.quotes.push(newQuote.value.trim())
  newQuote.value = ''
  store.save()
}

</script>

<template>
  <div class="p-4 md:p-6 max-w-3xl mx-auto space-y-4">
    <h1 class="page-title">设置</h1>

    <!-- 基本信息 -->
    <div class="card space-y-3">
      <div class="section-title">基本信息</div>
      <div class="grid grid-cols-2 gap-3">
        <div><label class="label">昵称</label><input :value="s.userName" class="input" @change="update('userName', ($event.target as HTMLInputElement).value)" /></div>
        <div><label class="label">下一场英语考试日期</label><input type="date" :value="s.examDate" class="input" @change="update('examDate', ($event.target as HTMLInputElement).value)" /></div>
      </div>
    </div>

    <!-- 每日目标 -->
    <div class="card space-y-3">
      <div class="section-title">每日目标</div>
      <div class="grid grid-cols-3 gap-3">
        <div><label class="label">学习时长（分钟）</label><input type="number" :value="s.dailyGoalMinutes" class="input" @change="update('dailyGoalMinutes', Number(($event.target as HTMLInputElement).value))" /></div>
        <div><label class="label">单词量</label><input type="number" :value="s.wordGoal" class="input" @change="update('wordGoal', Number(($event.target as HTMLInputElement).value))" /></div>
        <div><label class="label">做题量</label><input type="number" :value="s.problemGoal" class="input" @change="update('problemGoal', Number(($event.target as HTMLInputElement).value))" /></div>
      </div>
    </div>

    <!-- 科目管理 -->
    <div class="card space-y-3">
      <div class="flex items-center justify-between gap-2">
        <div class="section-title !mb-0">科目管理</div>
        <div class="flex items-center gap-2 shrink-0">
          <button class="btn-ghost !py-1.5 !text-xs" @click="showRestoreConfirm = true">恢复默认</button>
          <button class="btn-primary !py-1.5 !text-xs" @click="showSubject = true">+ 扩展科目</button>
        </div>
      </div>
      <div class="space-y-2">
        <div v-for="sub in store.subjects" :key="sub.id" class="flex items-center gap-2 text-sm flex-wrap">
          <span class="w-3 h-3 rounded-full shrink-0" :style="{ background: sub.color }"></span>
          <span>{{ subjectLabel(sub) }}</span>
          <span v-if="sub.builtin" class="text-[10px] text-slate-400">（内置）</span>
          <span class="ml-auto flex items-center gap-1 text-xs text-slate-400">
            权重
            <input type="number" min="0" max="100" class="input !w-16 !py-0.5 !px-1.5 !text-xs"
              :value="sub.weight" title="修改权重百分比"
              @change="onWeightChange(sub.id, $event)" />
            %
          </span>
          <button class="text-xs text-red-400 shrink-0" @click="removeSubject(sub.id, sub.name)">删除</button>
        </div>
        <p class="text-[10px] text-slate-400">可自由增删科目、调整权重；删除科目后其独立页面自动隐藏，新增科目自动生成独立页面。权重为自定义考核占比配置（各科目之和不要求等于 100%），统计图表仍按实际学习时长计算。</p>
      </div>
    </div>

    <!-- 外观 -->
    <div class="card space-y-3">
      <div class="section-title">外观与提醒</div>
      <div class="flex gap-2">
        <button v-for="t in [{ k: 'light', l: '浅色' }, { k: 'dark', l: '深色' }, { k: 'auto', l: '跟随系统' }]"
          :key="t.k" class="btn flex-1" :class="s.theme === t.k ? 'bg-primary-500 text-white' : 'bg-slate-100 dark:bg-slate-700'"
          @click="applyTheme(t.k)">{{ t.l }}</button>
      </div>
      <div class="flex items-center justify-between">
        <span class="text-sm">每日学习提醒</span>
        <div class="flex items-center gap-2">
          <input type="time" :value="s.reminderTime" class="input !w-auto !py-1" @change="update('reminderTime', ($event.target as HTMLInputElement).value)" />
          <button class="btn !text-xs" :class="s.reminderEnabled ? 'bg-emerald-500 text-white' : 'bg-slate-100 dark:bg-slate-700'"
            @click="toggleReminder(!s.reminderEnabled)">{{ s.reminderEnabled ? '已开启' : '已关闭' }}</button>
        </div>
      </div>
      <div class="pt-3 border-t border-slate-100 dark:border-slate-700 space-y-3">
        <div class="flex items-center justify-between">
          <div>
            <span class="text-sm">勿扰模式</span>
            <p class="text-[10px] text-slate-400 mt-0.5">开启后暂停学习提醒和系统通知，不影响学习数据记录</p>
          </div>
          <button class="btn !text-xs" :class="s.doNotDisturb ? 'bg-emerald-500 text-white' : 'bg-slate-100 dark:bg-slate-700'"
            @click="update('doNotDisturb', !s.doNotDisturb)">{{ s.doNotDisturb ? '已开启' : '已关闭' }}</button>
        </div>
        <div v-if="s.doNotDisturb" class="space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <div><label class="label">开始时间（留空=全天）</label><input type="time" :value="s.dndStartTime" class="input" @change="update('dndStartTime', ($event.target as HTMLInputElement).value)" /></div>
            <div><label class="label">结束时间（留空=全天）</label><input type="time" :value="s.dndEndTime" class="input" @change="update('dndEndTime', ($event.target as HTMLInputElement).value)" /></div>
          </div>
        </div>
      </div>
      <p v-if="!notifSupported" class="text-xs text-amber-500">当前浏览器不支持通知功能，无法使用每日提醒。</p>
      <p v-else-if="notifPermission === 'denied'" class="text-xs text-red-500">
        通知权限已被拒绝。请点击浏览器地址栏左侧的图标，将「通知」改为「允许」，然后重新打开此页面并开启提醒。
      </p>
      <p v-else-if="notifPermission === 'default'" class="text-xs text-slate-400">开启提醒时会请求浏览器通知权限。</p>
      <p v-else class="text-xs text-emerald-500">通知权限已授权。</p>
    </div>

    <!-- 名言 -->
    <div class="card space-y-3">
      <div class="section-title">自定义励志名言</div>
      <div class="flex gap-2">
        <input v-model="newQuote" class="input" placeholder="写一句激励自己的话…" @keyup.enter="addQuote" />
        <button class="btn-ghost shrink-0" @click="addQuote">添加</button>
      </div>
      <div class="space-y-1 max-h-40 overflow-y-auto">
        <div v-for="(q, i) in s.quotes" :key="i" class="flex items-center gap-2 text-xs group">
          <span class="flex-1 text-slate-500 dark:text-slate-400">{{ q }}</span>
          <button class="opacity-0 group-hover:opacity-100 text-red-400" @click="s.quotes.splice(i, 1); store.save()">×</button>
        </div>
      </div>
    </div>

    <!-- AI Provider：支持官方和第三方兼容 endpoint；密钥只使用环境变量 -->
    <div class="card space-y-3">
      <div class="flex items-center justify-between gap-2">
        <div><div class="section-title !mb-0">AI Provider</div><p class="text-[10px] text-slate-400 mt-1">支持 OpenAI、DeepSeek、Kimi、Qwen、GLM、Claude 和自定义中转。</p></div>
        <span class="text-[10px] rounded-full px-2 py-1 bg-slate-100 dark:bg-slate-700 text-slate-500">本地优先</span>
      </div>
      <div v-if="providerModels.length" class="grid grid-cols-2 sm:grid-cols-3 gap-2">
        <button v-for="item in providerModels.filter(x => x.id !== 'offline')" :key="item.id" class="text-left rounded-lg border px-3 py-2 transition-colors" :class="providerForm.provider_id === (item.provider || item.id) ? 'border-primary-400 bg-primary-50 dark:bg-primary-900/20' : 'border-slate-200 dark:border-slate-700'" @click="selectProvider(item)">
          <div class="text-sm font-semibold">{{ item.label }}</div><div class="text-[10px] text-slate-400 mt-1">{{ item.available ? '环境变量已就绪' : '未检测到 Key' }}</div>
        </button>
      </div>
      <div class="grid sm:grid-cols-2 gap-3">
        <div><label class="label">Provider ID</label><select v-model="providerForm.provider_id" class="input"><option v-for="item in providerModels.filter(x => x.id !== 'offline')" :key="item.id" :value="item.provider || item.id">{{ item.label }}</option><option value="custom">自定义中转</option></select></div>
        <div><label class="label">Model</label><input v-model="providerForm.model" class="input" placeholder="如 deepseek-chat" /></div>
        <div><label class="label">Endpoint（自定义时必填）</label><input v-model="providerForm.endpoint" class="input" placeholder="https://.../chat/completions" /></div>
        <div><label class="label">API Key 环境变量名</label><input v-model="providerForm.api_key_env" class="input" placeholder="DEEPSEEK_API_KEY" /></div>
      </div>
      <div class="flex items-center justify-between gap-2"><p class="text-[10px] text-slate-400">不在页面输入 API Key。未配置模型时，Agent 使用本地 RAG 和确定性规则，并在助手中提示。</p><button class="btn-primary !text-xs" @click="saveProvider">保存 Provider</button></div>
      <p v-if="providerMessage" class="text-xs text-emerald-600 dark:text-emerald-300">{{ providerMessage }}</p>
      <div v-if="configuredProviders.length" class="border-t border-slate-100 dark:border-slate-700 pt-3 space-y-2">
        <div class="text-xs font-semibold text-slate-600 dark:text-slate-300">已保存的 Provider</div>
        <div v-for="item in configuredProviders" :key="item.provider_id" class="flex items-center gap-3 rounded-lg bg-slate-50 dark:bg-slate-800/70 px-3 py-2 text-xs">
          <span class="font-semibold text-primary-600 dark:text-primary-300">{{ item.provider_id }}</span>
          <span class="flex-1 truncate text-slate-500">{{ item.model || '使用默认模型' }}</span>
          <span class="max-w-52 truncate text-slate-400">{{ item.endpoint || '官方 endpoint' }}</span>
          <span :class="item.available ? 'text-emerald-600' : 'text-amber-600'">{{ item.available ? '可用' : '待配置 Key' }}</span>
        </div>
      </div>
    </div>

    <!-- 数据管理 -->
    <div class="card space-y-3">
      <div class="section-title">数据管理</div>
      <div class="text-xs text-slate-400">本地数据大小：{{ storageUsage }}</div>
      <div class="flex gap-2 flex-wrap">
        <button class="btn-primary" @click="exportData">导出 JSON 备份</button>
        <button class="btn-ghost" @click="importFile?.click()">导入数据</button>
        <input ref="importFile" type="file" accept=".json" class="hidden" @change="onImport" />
        <button class="btn-danger" @click="showClearConfirm = true; clearText = ''">清除全部数据</button>
        <button v-if="updater" class="btn-ghost" @click="checkUpdate">检查更新</button>
      </div>
    </div>

    <!-- 恢复默认科目确认 -->
    <Modal title="恢复默认科目" :show="showRestoreConfirm" @close="showRestoreConfirm = false">
      <p class="text-sm text-slate-600 dark:text-slate-300">确定恢复默认科目列表？自定义新增的科目不会被删除，已删除的系统内置科目将会全部恢复。</p>
      <template #footer>
        <button class="btn-ghost" @click="showRestoreConfirm = false">取消</button>
        <button class="btn-primary" @click="restoreDefaults">确认恢复</button>
      </template>
    </Modal>

    <!-- 扩展科目弹窗 -->
    <Modal title="添加扩展科目" :show="showSubject" @close="showSubject = false">
      <div class="space-y-3">
        <div><label class="label">科目名称</label><input v-model="subForm.name" class="input" placeholder="如：计算机基础、政治、专业课" /></div>
        <div class="grid grid-cols-3 gap-2">
          <div><label class="label">图标 emoji</label><input v-model="subForm.icon" class="input" maxlength="4" /></div>
          <div><label class="label">颜色</label><input v-model="subForm.color" type="color" class="input !p-1 h-9" /></div>
          <div><label class="label">考核权重%</label><input v-model.number="subForm.weight" type="number" min="1" max="100" class="input" /></div>
        </div>
      </div>
      <template #footer>
        <button class="btn-ghost" @click="showSubject = false">取消</button>
        <button class="btn-primary" @click="addSubject">添加</button>
      </template>
    </Modal>

    <!-- 清除确认 -->
    <Modal title="危险操作" :show="showClearConfirm" @close="showClearConfirm = false">
      <p class="text-sm text-slate-500">此操作将永久删除所有学习记录、笔记、错题、习惯数据，<b class="text-red-500">不可恢复</b>！建议先导出备份。</p>
      <p class="text-sm mt-3">请输入「<b>确认清除</b>」以继续：</p>
      <input v-model="clearText" class="input mt-2" placeholder="确认清除" />
      <template #footer>
        <button class="btn-ghost" @click="showClearConfirm = false">取消</button>
        <button class="btn-danger" :disabled="clearText !== '确认清除'" @click="clearAll">永久清除</button>
      </template>
    </Modal>
  </div>
</template>
