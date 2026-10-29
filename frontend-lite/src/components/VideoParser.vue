<script setup>
import { ref, computed } from 'vue'
import AppIcon from './AppIcon.vue'

const url = ref('')
const loading = ref(false)
const error = ref('')
const result = ref(null)

const API_BASE = '/api'

const parseVideo = async () => {
  if (!url.value.trim()) {
    error.value = '请输入视频链接'
    return
  }

  loading.value = true
  error.value = ''
  result.value = null

  try {
    const res = await fetch(`${API_BASE}/parse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: url.value.trim() }),
    })

    const data = await res.json()

    if (!res.ok) {
      error.value = data.detail || '解析失败，请检查链接是否正确'
      return
    }

    result.value = data
  } catch (err) {
    error.value = '网络请求失败，请稍后重试'
    console.error(err)
  } finally {
    loading.value = false
  }
}

const directFormats = computed(() => {
  if (!result.value?.formats) return []
  return result.value.formats.filter((f) => f.direct)
})

const downloadDirect = (format) => {
  // 浏览器直接下载
  window.location.href = format.url
}

const handleKeydown = (e) => {
  if (e.key === 'Enter') parseVideo()
}
</script>

<template>
  <div class="space-y-6">
    <!-- 输入框 -->
    <div class="space-y-3">
      <div class="flex gap-2">
        <input
          v-model="url"
          type="text"
          placeholder="粘贴视频链接或分享文案…"
          class="input flex-1"
          :disabled="loading"
          @keydown="handleKeydown"
        />
        <button
          @click="parseVideo"
          :disabled="loading || !url.trim()"
          class="btn-primary w-28"
        >
          <AppIcon v-if="!loading" name="zap" :size="16" />
          <AppIcon v-else name="loader" :size="16" class="animate-spin" />
          {{ loading ? '解析中' : '解析' }}
        </button>
      </div>

      <!-- 错误提示 -->
      <div
        v-if="error"
        class="flex items-start gap-2 rounded-lg border border-error bg-error-soft p-3 text-sm text-error"
      >
        <AppIcon name="alert-circle" :size="16" class="mt-0.5 shrink-0" />
        <span>{{ error }}</span>
      </div>
    </div>

    <!-- 解析结果 -->
    <div v-if="result" class="space-y-4">
      <!-- 视频信息卡片 -->
      <div class="rounded-xl border border-border bg-white p-5 shadow-sm">
        <div class="flex items-start gap-4">
          <!-- 封面缩略图 -->
          <div
            v-if="result.thumbnail"
            class="h-20 w-20 shrink-0 overflow-hidden rounded-lg bg-gray-100"
          >
            <img
              :src="result.thumbnail"
              :alt="result.title"
              class="h-full w-full object-cover"
            />
          </div>

          <!-- 标题和信息 -->
          <div class="min-w-0 flex-1">
            <h3 class="mb-2 font-semibold text-ink line-clamp-2">
              {{ result.title }}
            </h3>
            <div class="flex flex-wrap gap-x-4 gap-y-1 text-sm text-ink-soft">
              <span v-if="result.platform" class="flex items-center gap-1">
                <AppIcon name="globe" :size="14" />
                {{ result.platform }}
              </span>
              <span v-if="result.duration" class="flex items-center gap-1">
                <AppIcon name="film" :size="14" />
                {{ Math.floor(result.duration / 60) }}:{{
                  String(result.duration % 60).padStart(2, '0')
                }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 可用格式列表 -->
      <div v-if="directFormats.length > 0" class="space-y-3">
        <h4 class="text-sm font-medium text-ink-softer">
          可用清晰度（{{ directFormats.length }}）
        </h4>

        <div class="space-y-2">
          <div
            v-for="format in directFormats"
            :key="format.id"
            class="group flex items-center justify-between rounded-lg border border-border bg-white p-4 transition-all hover:border-primary hover:shadow-sm"
          >
            <div class="flex items-center gap-3">
              <div
                class="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-soft text-primary-deep"
              >
                <AppIcon name="film" :size="20" :stroke-width="2" />
              </div>
              <div>
                <p class="font-medium text-ink">{{ format.label }}</p>
                <p class="text-sm text-ink-soft">
                  {{ format.resolution || '原画质' }}
                  <span v-if="format.filesize" class="ml-2">
                    · {{ (format.filesize / 1024 / 1024).toFixed(1) }} MB
                  </span>
                </p>
              </div>
            </div>

            <button
              @click="downloadDirect(format)"
              class="btn-primary opacity-0 transition-opacity group-hover:opacity-100"
            >
              <AppIcon name="download" :size="16" />
              下载
            </button>
          </div>
        </div>
      </div>

      <!-- 无可用格式提示 -->
      <div
        v-else
        class="flex items-start gap-3 rounded-lg border border-border bg-surface-hover p-4 text-sm text-ink-soft"
      >
        <AppIcon name="info" :size="18" class="mt-0.5 shrink-0 text-ink-softer" />
        <div>
          <p class="font-medium text-ink">该平台暂不支持直连下载</p>
          <p class="mt-1">
            Lite 版仅支持开放 CDN 平台（抖音、快手等）。如需下载其他平台视频，请使用
            <a href="#" class="text-primary hover:underline">GoVid 完整版</a>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
