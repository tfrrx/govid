<script setup>
import { computed, onMounted, ref } from 'vue'

import { api } from './api/video'
import AppHeader from './components/AppHeader.vue'
import DownloadProgress from './components/DownloadProgress.vue'
import ErrorMessage from './components/ErrorMessage.vue'
import FeatureSection from './components/FeatureSection.vue'
import FooterSection from './components/FooterSection.vue'
import HeroSection from './components/HeroSection.vue'
import HowToSection from './components/HowToSection.vue'
import PlatformSection from './components/PlatformSection.vue'
import PricingSection from './components/PricingSection.vue'
import VideoInput from './components/VideoInput.vue'
import VideoResult from './components/VideoResult.vue'
import AppIcon from './components/icons/AppIcon.vue'
import { useDownloader } from './composables/useDownloader'

const {
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
  parse,
  startDownload,
  cancel,
  reset,
  setUrl,
  pushToast,
  dismissToast,
  fileUrl,
  thumbnailUrl,
} = useDownloader()

const health = ref(null)
const healthError = ref('')

/**
 * 微信 / QQ / 微博等 App 的内置浏览器不支持 `download` 属性，点击下载链接
 * 常常毫无反应（或变成在页面里播视频）。这是内核限制，前端绕不过去，
 * 唯一出路是引导用户「在浏览器打开」——所以进页面就先说清楚。
 */
const IN_APP_PATTERNS = [
  [/MicroMessenger/i, '微信'],
  [/QQBrowser|QQ\/\d/i, 'QQ'],
  [/Weibo/i, '微博'],
  [/AlipayClient/i, '支付宝'],
  [/DingTalk/i, '钉钉'],
  [/BytedanceWebview|aweme/i, '抖音'],
]

const inAppName = ref('')
const noticeClosed = ref(false)

function detectInAppBrowser() {
  const ua = navigator.userAgent || ''
  for (const [pattern, name] of IN_APP_PATTERNS) {
    if (pattern.test(ua)) return name
  }
  return ''
}

const workspaceVisible = computed(() => hasResult.value || !!task.value)

onMounted(async () => {
  inAppName.value = detectInAppBrowser()
  try {
    health.value = await api.health()
    if (health.value?.ffmpeg && !health.value.ffmpeg.available) {
      pushToast('未检测到 ffmpeg，高清合并与音频转码暂不可用', 'info', 8000)
    }
  } catch (error) {
    healthError.value = error?.message || '后端服务不可用'
    pushToast(healthError.value, 'error', 8000)
  }
})

function onSelectFormat(id) {
  selectedId.value = id
}

function onReset() {
  reset()
  scrollToHero()
}

function scrollToHero() {
  const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  document
    .getElementById('govid-hero')
    ?.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' })
}
</script>

<template>
  <div class="min-h-screen bg-surface">
    <a
      href="#govid-workspace"
      class="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-pill focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:text-white"
    >
      跳到主内容
    </a>

    <AppHeader />

    <!-- 后端不可用时的显式提示，不让用户对着按钮干猜 -->
    <div
      v-if="healthError"
      class="border-b border-error/20 bg-error-soft px-4 py-2.5 text-center text-sm text-error"
      role="alert"
    >
      {{ healthError }} —— 请先启动后端服务（./run.sh），再刷新本页
    </div>

    <!-- 内置浏览器存不了文件，提前讲清楚，省得用户白点一通 -->
    <div
      v-if="inAppName && !noticeClosed"
      class="border-b border-accent/25 bg-accent-soft px-4 py-3"
      role="alert"
    >
      <div class="container-page flex items-start gap-3">
        <AppIcon name="alert" :size="17" class="mt-0.5 shrink-0 text-accent" />
        <p class="flex-1 text-sm leading-relaxed text-ink">
          你正在{{ inAppName }}里打开，
          <b class="font-semibold">{{ inAppName }}内置浏览器无法保存文件</b>。
          请点右上角「⋯」→「在浏览器打开」，再回来点下载就能存到手机了。
        </p>
        <button
          type="button"
          class="shrink-0 rounded-pill px-3 py-1 text-xs text-ink-soft transition-colors hover:bg-surface"
          @click="noticeClosed = true"
        >
          知道了
        </button>
      </div>
    </div>

    <main>
      <HeroSection>
        <template #form>
          <VideoInput
            :model-value="url"
            :busy="busy"
            :invalid="!!urlError"
            :message="urlError"
            @update:model-value="setUrl"
            @submit="parse"
          />
        </template>
      </HeroSection>

      <!-- 工作区：解析结果 + 下载进度 -->
      <section
        id="govid-workspace"
        v-show="workspaceVisible"
        class="container-page scroll-mt-20 pb-16 sm:pb-20"
        aria-label="解析与下载工作区"
      >
        <!-- 解析中骨架 -->
        <div v-if="phase === 'parsing'" class="grid gap-6 lg:grid-cols-2">
          <div class="card p-0">
            <div class="skeleton aspect-video rounded-b-none" />
            <div class="flex flex-col gap-3 p-5">
              <div class="skeleton h-5 w-3/4" />
              <div class="skeleton h-4 w-1/3" />
              <div class="skeleton h-12 w-full" />
            </div>
          </div>
          <div class="card flex flex-col gap-3 p-5">
            <div class="skeleton h-5 w-1/3" />
            <div v-for="n in 5" :key="n" class="skeleton h-16 w-full" />
          </div>
        </div>

        <template v-else>
          <VideoResult
            v-if="video"
            :video="video"
            :selected-id="selectedId"
            :disabled="downloading"
            :thumbnail-url="thumbnailUrl"
            @update:selected-id="onSelectFormat"
            @download="startDownload"
          />

          <div v-if="task" class="mt-6">
            <DownloadProgress
              :task="task"
              :quality-label="selectedFormat?.label || ''"
              :title="video?.title || ''"
              :file-url="fileUrl"
              :ttl-hours="health?.task_ttl_hours || 0"
              :in-app-name="inAppName"
              @cancel="cancel"
              @reset="onReset"
            />
          </div>

          <div v-else-if="video" class="mt-4 flex items-center justify-center gap-2 text-xs text-ink-soft">
            <AppIcon name="info" :size="14" />
            选好清晰度点「开始下载」，进度会显示在这里
          </div>
        </template>
      </section>

      <FeatureSection />
      <HowToSection />
      <PlatformSection />
      <PricingSection />

      <!-- 底部收尾 CTA -->
      <section class="container-page pb-16">
        <div
          class="relative overflow-hidden rounded-3xl border border-primary/20 bg-gradient-to-br from-primary-soft to-surface px-6 py-12 text-center sm:px-12"
        >
          <div
            class="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full opacity-60 blur-3xl animate-float"
            style="background: radial-gradient(closest-side, rgba(16, 185, 129, 0.35), transparent 70%)"
            aria-hidden="true"
          />
          <h2 class="relative text-2xl font-bold tracking-tight text-ink sm:text-3xl">
            手边正好有个想存下来的视频？
          </h2>
          <p class="relative mx-auto mt-3 max-w-xl text-sm leading-relaxed text-ink-soft sm:text-base">
            回到顶部粘上链接就能开工，全程不需要注册。
          </p>
          <button type="button" class="btn-primary relative mt-7" @click="scrollToHero">
            <AppIcon name="arrowRight" :size="18" />
            回到输入框
          </button>
        </div>
      </section>
    </main>

    <FooterSection />

    <ErrorMessage :toasts="toasts" @dismiss="dismissToast" />
  </div>
</template>
