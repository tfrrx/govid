import { computed, onBeforeUnmount, reactive, ref } from 'vue'

import { ApiError, api, taskFileUrl, thumbnailUrl } from '../api/video'

const POLL_INTERVAL = 1000
const TERMINAL = new Set(['completed', 'failed', 'cancelled'])

const URL_PATTERN = /^https?:\/\/[^\s]+$/i
// 分享文案里的链接：抖音 / 快手 App 复制的整段文本里，链接两侧常跟中文标点或空格
const URL_IN_TEXT = /https?:\/\/[^\s，,。；;、"'“”()（）【】\[\]]+/i

/**
 * 从用户输入中取出真正的链接。
 * 纯链接原样返回；整段分享文案则抓出其中的 URL。
 * 抖音的分享文案不是 URL，必须走提取，否则会被判成「格式不对」而卡在解析前。
 */
export function extractUrl(text) {
  const value = String(text ?? '').trim()
  if (!value) return ''
  if (URL_PATTERN.test(value)) return value
  const match = value.match(URL_IN_TEXT)
  return match ? match[0] : ''
}

/**
 * GoVid 前端状态机。
 * phase: idle → parsing → ready → downloading → done
 * 任何一步失败都会回退到可重试的状态，并抛一条 Toast。
 */
export function useDownloader() {
  const phase = ref('idle')
  const url = ref('')
  const urlError = ref('')
  const video = ref(null)
  const selectedId = ref('')
  const task = ref(null)
  const toasts = ref([])
  const cancelled = ref(false)

  const busy = computed(() => phase.value === 'parsing')
  const downloading = computed(
    () => phase.value === 'downloading' && !!task.value && !TERMINAL.has(task.value.status),
  )
  const selectedFormat = computed(
    () => video.value?.formats?.find((f) => f.id === selectedId.value) ?? null,
  )
  const hasResult = computed(() => phase.value !== 'idle' && phase.value !== 'parsing')

  let pollTimer = null
  let toastSeq = 0
  const abort = reactive({ current: null })

  // ------------------------------------------------------------ Toast

  function pushToast(message, type = 'error', timeout = 5000) {
    const id = ++toastSeq
    toasts.value = [...toasts.value, { id, message, type }]
    if (timeout > 0) {
      window.setTimeout(() => dismissToast(id), timeout)
    }
    return id
  }

  function dismissToast(id) {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  function handleError(error) {
    if (error instanceof ApiError) {
      pushToast(error.message, 'error')
      return error.message
    }
    if (error?.name === 'AbortError') return ''
    pushToast('出了点意外，请重试', 'error')
    return '出了点意外，请重试'
  }

  // ------------------------------------------------------------ 解析

  function validate(rawUrl) {
    const value = rawUrl.trim()
    if (!value) return '请先粘贴视频链接'
    if (!extractUrl(value)) return '没找到视频链接，粘贴链接或 App 的分享文案都行'
    return ''
  }

  async function parse() {
    const target = extractUrl(url.value)
    urlError.value = validate(url.value)
    if (urlError.value) {
      pushToast(urlError.value, 'error', 4000)
      return
    }
    // 把提取到的链接回填输入框，让用户看清实际解析的是什么
    if (target !== url.value) url.value = target

    stopPolling()
    task.value = null
    phase.value = 'parsing'
    cancelled.value = false

    abort.current?.abort()
    const controller = new AbortController()
    abort.current = controller

    try {
      const data = await api.parse(target, { signal: controller.signal })
      video.value = data
      selectedId.value = data.formats?.find((f) => f.recommended)?.id ?? data.formats?.[0]?.id ?? ''
      phase.value = 'ready'
      urlError.value = ''
      scrollToWorkspace()
    } catch (error) {
      const message = handleError(error)
      phase.value = 'idle'
      if (message && error?.code !== 'offline') video.value = null
    } finally {
      if (abort.current === controller) abort.current = null
    }
  }

  function scrollToWorkspace() {
    window.requestAnimationFrame(() => {
      const el = document.getElementById('govid-workspace')
      if (!el) return
      const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
      el.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' })
    })
  }

  // ------------------------------------------------------------ 下载

  function stopPolling() {
    if (pollTimer !== null) {
      window.clearInterval(pollTimer)
      pollTimer = null
    }
  }

  async function startDownload() {
    if (!selectedFormat.value) {
      pushToast('请先选择清晰度', 'error', 4000)
      return
    }
    if (downloading.value) return

    cancelled.value = false
    phase.value = 'downloading'
    task.value = { status: 'pending', progress: 0 }

    try {
      const created = await api.createTask({
        url: video.value.webpage_url || url.value.trim(),
        format_id: selectedFormat.value.id,
        title: video.value.title,
        thumbnail: video.value.thumbnail,
        quality_label: selectedFormat.value.label,
      })
      task.value = { ...task.value, ...created }
      beginPolling(created.task_id)
    } catch (error) {
      handleError(error)
      phase.value = 'ready'
      task.value = null
    }
  }

  function beginPolling(taskId) {
    stopPolling()
    const tick = async () => {
      try {
        const data = await api.getTask(taskId)
        task.value = data
        if (TERMINAL.has(data.status)) {
          stopPolling()
          if (data.status === 'completed') {
            phase.value = 'done'
            pushToast('下载完成，可以保存到本地了', 'success', 6000)
          } else if (data.status === 'cancelled') {
            phase.value = 'ready'
            pushToast('已取消下载', 'info', 4000)
          } else {
            phase.value = 'ready'
            pushToast(data.error || '下载失败，请重试', 'error')
          }
        }
      } catch (error) {
        stopPolling()
        phase.value = 'ready'
        handleError(error)
      }
    }
    tick()
    pollTimer = window.setInterval(tick, POLL_INTERVAL)
  }

  async function cancel() {
    if (!task.value?.task_id) return
    cancelled.value = true
    try {
      const data = await api.cancelTask(task.value.task_id)
      task.value = data
    } catch (error) {
      handleError(error)
    } finally {
      stopPolling()
      phase.value = 'ready'
    }
  }

  function reset() {
    stopPolling()
    abort.current?.abort()
    abort.current = null
    phase.value = 'idle'
    video.value = null
    task.value = null
    selectedId.value = ''
    urlError.value = ''
    cancelled.value = false
  }

  function setUrl(value) {
    url.value = value
    if (urlError.value) urlError.value = validate(value)
  }

  onBeforeUnmount(() => {
    stopPolling()
    abort.current?.abort()
  })

  return {
    // 状态
    phase,
    busy,
    downloading,
    hasResult,
    url,
    urlError,
    video,
    selectedId,
    selectedFormat,
    task,
    toasts,
    // 行为
    parse,
    startDownload,
    cancel,
    reset,
    setUrl,
    pushToast,
    dismissToast,
    // 工具
    fileUrl: taskFileUrl,
    thumbnailUrl,
  }
}
