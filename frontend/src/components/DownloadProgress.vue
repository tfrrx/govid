<script setup>
import { computed } from 'vue'

import AppIcon from './icons/AppIcon.vue'
import { formatBytes } from '../utils/format'

const props = defineProps({
  task: { type: Object, required: true },
  qualityLabel: { type: String, default: '' },
  title: { type: String, default: '' },
  fileUrl: { type: Function, required: true },
})

const emit = defineEmits(['cancel', 'reset'])

const STATUS_TEXT = {
  pending: '排队中',
  downloading: '下载中',
  merging: '合并音视频',
  completed: '已完成',
  failed: '下载失败',
  cancelled: '已取消',
}

const status = computed(() => props.task.status || 'pending')
const percent = computed(() => Math.max(0, Math.min(100, Number(props.task.progress) || 0)))
const isActive = computed(() => ['pending', 'downloading', 'merging'].includes(status.value))
const isDone = computed(() => status.value === 'completed')
const isFailed = computed(() => status.value === 'failed')

/** 分段进度：解析在创建任务前就已完成，所以恒为 done */
const steps = computed(() => {
  const s = status.value
  const downloadState =
    s === 'failed' ? 'error' : s === 'downloading' || s === 'pending' ? 'active' : 'done'

  let mergeState = 'pending'
  if (s === 'merging') mergeState = 'active'
  else if (s === 'completed') mergeState = 'done'

  return [
    { key: 'parse', label: '解析视频', hint: '已获取全部清晰度', state: 'done' },
    {
      key: 'download',
      label: '下载数据',
      hint:
        s === 'failed'
          ? '中断'
          : s === 'pending'
            ? '排队等待中'
            : s === 'downloading'
              ? `${percent.value.toFixed(1)}%`
              : '完成',
      state: s === 'cancelled' ? 'pending' : downloadState,
    },
    {
      key: 'merge',
      label: '合并输出',
      hint:
        mergeState === 'done'
          ? '文件已就绪'
          : mergeState === 'active'
            ? '正在合并音视频…'
            : s === 'cancelled'
              ? '已取消'
              : '等待中',
      state: s === 'cancelled' ? 'pending' : mergeState,
    },
  ]
})

const stats = computed(() => {
  const t = props.task
  return [
    { label: '已下载', value: t.downloaded_text || formatBytes(t.downloaded_bytes) || '—' },
    { label: '总大小', value: t.total_text || formatBytes(t.total_bytes) || '计算中' },
    { label: '速度', value: t.speed || (status.value === 'merging' ? '合并中' : '—') },
    { label: '剩余时间', value: t.eta || (isDone.value ? '0:00' : '—') },
  ]
})

const stepIcon = (state) => {
  if (state === 'done') return 'check'
  if (state === 'error') return 'alert'
  return null
}

const statusHint = computed(() => {
  const map = {
    pending: '等待调度',
    downloading: '正在接收数据',
    merging: '正在合并音视频轨',
    completed: '文件已保存到临时目录',
    failed: '已中断',
    cancelled: '已取消',
  }
  return map[status.value] || ''
})
</script>

<template>
  <section
    class="card animate-rise overflow-hidden"
    aria-labelledby="govid-progress-title"
    aria-live="polite"
  >
    <header class="flex flex-wrap items-center justify-between gap-3 border-b border-hairline px-5 py-4">
      <div class="flex min-w-0 items-center gap-2.5">
        <span
          class="flex h-8 w-8 items-center justify-center rounded-lg"
          :class="isDone ? 'bg-primary-soft text-primary-deep' : isFailed ? 'bg-error-soft text-error' : 'bg-primary-soft text-primary'"
        >
          <AppIcon :name="isDone ? 'checkCircle' : isFailed ? 'alert' : 'download'" :size="17" />
        </span>
        <div class="min-w-0">
          <h2 id="govid-progress-title" class="truncate text-sm font-semibold text-ink">
            {{ title || '下载任务' }}
          </h2>
          <p class="truncate text-xs text-ink-soft">
            {{ qualityLabel ? `清晰度 ${qualityLabel}` : '正在处理' }}
          </p>
        </div>
      </div>

      <span
        class="rounded-pill px-3 py-1 text-xs font-semibold"
        :class="
          isDone
            ? 'bg-primary-soft text-primary-deep'
            : isFailed
              ? 'bg-error-soft text-error'
              : 'bg-surface-sub text-ink-soft'
        "
      >
        {{ STATUS_TEXT[status] || status }}
      </span>
    </header>

    <div class="flex flex-col gap-6 p-5">
      <!-- 分段进度 -->
      <ol class="flex items-start" role="list">
        <li
          v-for="(step, index) in steps"
          :key="step.key"
          class="flex min-w-0 flex-1 items-start gap-2"
        >
          <div class="flex flex-col items-center gap-2">
            <span
              class="flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold transition-colors duration-300"
              :class="{
                'bg-primary text-white': step.state === 'done',
                'bg-primary-soft text-primary-deep ring-2 ring-primary': step.state === 'active',
                'bg-error-soft text-error': step.state === 'error',
                'bg-surface-sub text-ink-soft/70': step.state === 'pending',
              }"
            >
              <AppIcon v-if="stepIcon(step.state)" :name="stepIcon(step.state)" :size="14" :stroke-width="2.4" />
              <span v-else-if="step.state === 'active' && isActive" class="relative flex h-2.5 w-2.5">
                <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-60" />
                <span class="relative inline-flex h-2.5 w-2.5 rounded-full bg-primary" />
              </span>
              <template v-else>{{ index + 1 }}</template>
            </span>
          </div>

          <div class="min-w-0 flex-1 pt-0.5">
            <p
              class="truncate text-xs font-semibold sm:text-sm"
              :class="step.state === 'pending' ? 'text-ink-soft' : 'text-ink'"
            >
              {{ step.label }}
            </p>
            <p class="truncate text-[11px] text-ink-soft">{{ step.hint }}</p>
          </div>

          <span
            v-if="index < steps.length - 1"
            class="mx-1 mt-3 h-px flex-1 min-w-4 bg-hairline sm:mx-2"
            aria-hidden="true"
          />
        </li>
      </ol>

      <!-- 进度条 -->
      <div>
        <div class="mb-2 flex items-end justify-between">
          <span class="text-3xl font-bold tabular-nums tracking-tight text-ink">
            {{ percent.toFixed(1) }}<span class="ml-0.5 text-lg font-semibold text-ink-soft">%</span>
          </span>
          <span class="pb-1 text-xs text-ink-soft">
            {{ statusHint }}
          </span>
        </div>

        <div
          class="h-2.5 w-full overflow-hidden rounded-full bg-surface-sub"
          role="progressbar"
          :aria-valuenow="Math.round(percent)"
          aria-valuemin="0"
          aria-valuemax="100"
          :aria-label="`下载进度 ${percent.toFixed(0)}%`"
        >
          <div
            class="h-full rounded-full bg-gradient-to-r from-primary to-primary-dark transition-[width] duration-500 ease-out"
            :style="{ width: `${isDone ? 100 : Math.max(percent, isActive ? 2 : 0)}%` }"
          />
        </div>
      </div>

      <!-- 统计 -->
      <dl class="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div
          v-for="item in stats"
          :key="item.label"
          class="rounded-xl border border-hairline bg-surface-sub/60 px-3.5 py-2.5"
        >
          <dt class="text-[11px] text-ink-soft">{{ item.label }}</dt>
          <dd class="mt-0.5 truncate text-sm font-semibold tabular-nums text-ink">{{ item.value }}</dd>
        </div>
      </dl>

      <!-- 失败提示 -->
      <p
        v-if="isFailed"
        class="flex items-start gap-2 rounded-xl border border-error/25 bg-error-soft px-4 py-3 text-sm text-error"
        role="alert"
      >
        <AppIcon name="alert" :size="16" class="mt-0.5" />
        <span>{{ task.error || '下载失败，请重试' }}</span>
      </p>

      <!-- 操作区 -->
      <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
        <template v-if="isDone">
          <a
            :href="fileUrl(task.task_id)"
            class="btn-primary flex-1"
            download
            referrerpolicy="no-referrer"
          >
            <AppIcon name="download" :size="18" />
            保存到本地
          </a>
          <button type="button" class="btn-secondary sm:w-auto" @click="emit('reset')">
            <AppIcon name="rotate" :size="16" />
            换个视频
          </button>
        </template>

        <template v-else-if="isActive">
          <button type="button" class="btn-secondary flex-1" @click="emit('cancel')">
            <AppIcon name="close" :size="16" />
            取消下载
          </button>
          <p class="flex-1 text-xs leading-relaxed text-ink-soft">
            进度每秒刷新一次，可以直接去干别的，服务端会继续下载。
          </p>
        </template>

        <template v-else>
          <button type="button" class="btn-primary flex-1" @click="emit('reset')">
            <AppIcon name="rotate" :size="16" />
            重新开始
          </button>
        </template>
      </div>

      <!-- 完成信息 -->
      <div
        v-if="isDone"
        class="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-primary/20 bg-primary-soft/70 px-4 py-3"
      >
        <span class="flex min-w-0 items-center gap-2 text-sm text-primary-deep">
          <AppIcon name="film" :size="16" />
          <span class="truncate font-medium">{{ task.file_name }}</span>
        </span>
        <span class="text-xs tabular-nums text-primary-deep/80">
          {{ task.file_size_text || formatBytes(task.file_size) || '' }}
        </span>
      </div>
    </div>
  </section>
</template>
