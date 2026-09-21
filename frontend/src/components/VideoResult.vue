<script setup>
import { computed } from 'vue'

import AppIcon from './icons/AppIcon.vue'
import { formatCount, formatDuration } from '../utils/format'

const props = defineProps({
  video: { type: Object, required: true },
  selectedId: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  thumbnailUrl: { type: Function, default: null },
})

const emit = defineEmits(['update:selectedId', 'download'])

const posterSrc = computed(() => {
  const raw = props.video?.thumbnail
  if (!raw) return ''
  // 走服务端代理绕开平台防盗链；没传代理函数时退化为直连
  return props.thumbnailUrl ? props.thumbnailUrl(raw) : raw
})

const meta = computed(() => {
  const items = []
  if (props.video.author) items.push({ icon: 'users', text: props.video.author })
  const duration = formatDuration(props.video.duration)
  if (duration) items.push({ icon: 'clock', text: duration })
  const views = formatCount(props.video.view_count)
  if (views) items.push({ icon: 'gauge', text: `${views} 次播放` })
  return items
})

const selected = computed(
  () => props.video.formats?.find((f) => f.id === props.selectedId) ?? null,
)

const topTierLabel = computed(
  () =>
    props.video.formats?.find((f) => f.kind === 'video' && !f.recommended)?.label ?? '—',
)

const videoCount = computed(
  () => props.video.formats?.filter((f) => f.kind === 'video').length ?? 0,
)

const audioCount = computed(
  () => props.video.formats?.filter((f) => f.kind === 'audio').length ?? 0,
)

function select(id) {
  if (props.disabled) return
  emit('update:selectedId', id)
}
</script>

<template>
  <div class="animate-rise grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)] lg:gap-8">
    <!-- 左栏：封面 + 信息 -->
    <div class="flex flex-col gap-5">
      <div class="card overflow-hidden">
        <div class="relative aspect-video w-full bg-surface-sub">
          <img
            v-if="posterSrc"
            :src="posterSrc"
            :alt="`${video.title} 的视频封面`"
            class="h-full w-full object-cover"
            loading="eager"
            decoding="async"
            referrerpolicy="no-referrer"
            @error="(event) => (event.target.style.display = 'none')"
          />
          <div
            v-else
            class="flex h-full w-full items-center justify-center text-ink-soft"
            aria-hidden="true"
          >
            <AppIcon name="image" :size="36" />
          </div>

          <span
            v-if="video.duration"
            class="absolute bottom-3 right-3 rounded-md bg-ink/80 px-2 py-0.5 text-xs font-medium tabular-nums text-white"
          >
            {{ formatDuration(video.duration) }}
          </span>
        </div>

        <div class="flex flex-col gap-4 p-5">
          <h3 class="text-lg font-semibold leading-snug text-ink">{{ video.title }}</h3>

          <div class="flex flex-wrap items-center gap-2">
            <span class="chip border-primary/25 bg-primary-soft text-primary-deep">
              <AppIcon name="globe" :size="13" />
              {{ video.platform }}
            </span>
            <span v-for="item in meta" :key="item.text" class="chip">
              <AppIcon :name="item.icon" :size="13" />
              {{ item.text }}
            </span>
          </div>

          <dl class="grid grid-cols-2 gap-3 border-t border-hairline pt-4 text-sm">
            <div>
              <dt class="text-xs text-ink-soft">可用画质</dt>
              <dd class="mt-0.5 font-semibold tabular-nums text-ink">
                {{ videoCount }} 档
                <span v-if="audioCount" class="ml-1 text-xs font-normal text-ink-soft">
                  + 音频 {{ audioCount }}
                </span>
              </dd>
            </div>
            <div>
              <dt class="text-xs text-ink-soft">最高分辨率</dt>
              <dd class="mt-0.5 font-semibold tabular-nums text-ink">
                {{ topTierLabel }}
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </div>

    <!-- 右栏：清晰度选择 -->
    <div class="card flex flex-col overflow-hidden">
      <div class="flex items-center justify-between border-b border-hairline px-5 py-4">
        <div class="flex items-center gap-2">
          <AppIcon name="layers" :size="18" class="text-primary" />
          <h3 class="text-base font-semibold text-ink">选择清晰度</h3>
        </div>
        <span class="text-xs text-ink-soft">{{ video.formats.length }} 项可选</span>
      </div>

      <div
        class="no-scrollbar flex max-h-[400px] flex-col gap-2 overflow-y-auto p-4"
        role="radiogroup"
        aria-label="清晰度选择"
      >
        <label
          v-for="format in video.formats"
          :key="format.id"
          class="group relative flex cursor-pointer items-center gap-3 rounded-xl border p-3.5 transition-colors duration-200"
          :class="[
            format.id === selectedId
              ? 'border-primary bg-primary-soft/70'
              : 'border-hairline bg-surface hover:border-primary/35 hover:bg-surface-sub',
            disabled ? 'cursor-not-allowed opacity-60' : '',
          ]"
        >
          <input
            type="radio"
            name="govid-format"
            class="sr-only"
            :value="format.id"
            :checked="format.id === selectedId"
            :disabled="disabled"
            @change="select(format.id)"
          />

          <span
            class="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border-2 transition-colors duration-200"
            :class="format.id === selectedId ? 'border-primary bg-primary' : 'border-hairline bg-surface'"
            aria-hidden="true"
          >
            <span v-if="format.id === selectedId" class="h-1.5 w-1.5 rounded-full bg-white" />
          </span>

          <span class="min-w-0 flex-1">
            <span class="flex flex-wrap items-center gap-x-2 gap-y-1">
              <span class="text-sm font-semibold text-ink">{{ format.label }}</span>
              <span v-if="format.recommended" class="rounded-full bg-primary px-1.5 py-0.5 text-[10px] font-semibold text-white">
                推荐
              </span>
              <span
                v-if="format.needs_merge"
                class="rounded-full bg-accent-soft px-1.5 py-0.5 text-[10px] font-semibold text-accent"
              >
                需合并
              </span>
              <span
                v-if="format.kind === 'audio'"
                class="rounded-full bg-surface-sub px-1.5 py-0.5 text-[10px] font-semibold text-ink-soft"
              >
                仅音频
              </span>
            </span>
            <span class="mt-1 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-ink-soft">
              <span>{{ format.resolution }}</span>
              <span aria-hidden="true">·</span>
              <span class="uppercase">{{ format.ext }}</span>
              <template v-if="format.size_text">
                <span aria-hidden="true">·</span>
                <span>约 {{ format.size_text }}</span>
              </template>
              <template v-if="format.fps">
                <span aria-hidden="true">·</span>
                <span>{{ Math.round(format.fps) }}fps</span>
              </template>
            </span>
            <span v-if="format.note" class="mt-0.5 block text-xs text-ink-soft/85">
              {{ format.note }}
            </span>
          </span>

          <AppIcon
            name="music"
            v-if="format.kind === 'audio'"
            :size="15"
            class="text-ink-soft/60"
          />
        </label>
      </div>

      <div class="border-t border-hairline bg-surface-sub/70 px-5 py-4">
        <div class="mb-3 flex items-center justify-between gap-3 text-sm">
          <span class="text-ink-soft">已选</span>
          <span class="truncate font-semibold text-ink">
            {{ selected ? `${selected.label} · ${selected.resolution}` : '未选择' }}
          </span>
        </div>

        <button
          type="button"
          class="btn-primary w-full"
          :disabled="disabled || !selected"
          @click="emit('download')"
        >
          <AppIcon v-if="!disabled" name="download" :size="18" />
          <span
            v-else
            class="h-4 w-4 animate-spin rounded-full border-2 border-white/35 border-t-white"
            aria-hidden="true"
          />
          {{ disabled ? '下载中…' : '开始下载' }}
        </button>

        <p class="mt-2.5 text-center text-xs leading-relaxed text-ink-soft">
          文件仅保存在本机 tmp 目录，下载完可以随时删除
        </p>
      </div>
    </div>
  </div>
</template>
