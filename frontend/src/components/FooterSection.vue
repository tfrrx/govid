<script setup>
import AppIcon from './icons/AppIcon.vue'

const YEAR = new Date().getFullYear()

const LINKS = [
  { label: '核心能力', href: '#features' },
  { label: '使用流程', href: '#howto' },
  { label: '平台覆盖', href: '#platforms' },
  { label: '价格', href: '#pricing' },
]
</script>

<template>
  <footer class="border-t border-hairline bg-surface-sub/60">
    <div class="container-page py-12">
      <div class="flex flex-col gap-10 lg:flex-row lg:justify-between">
        <div class="max-w-sm">
          <div class="flex items-center gap-2.5">
            <span
              class="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary-dark text-white"
              aria-hidden="true"
            >
              <AppIcon name="download" :size="18" :stroke-width="2.2" />
            </span>
            <span class="text-lg font-bold tracking-tight text-ink">GoVid</span>
          </div>
          <p class="mt-4 text-sm leading-relaxed text-ink-soft">
            无水印、多清晰度、进度可见的视频下载工具，粘贴链接或分享文案即可开始。
          </p>
        </div>

        <nav class="flex flex-col gap-3" aria-label="页脚导航">
          <p class="text-xs font-semibold uppercase tracking-wide text-ink-soft">页面导航</p>
          <div class="grid grid-cols-2 gap-x-8 gap-y-2.5 sm:grid-cols-3 lg:grid-cols-2">
            <a
              v-for="link in LINKS"
              :key="link.href"
              :href="link.href"
              class="text-sm text-ink-soft transition-colors duration-200 hover:text-primary-deep"
            >
              {{ link.label }}
            </a>
          </div>
        </nav>
      </div>

      <div class="mt-10 border-t border-hairline pt-6">
        <p class="flex items-start gap-2.5 text-xs leading-relaxed text-ink-soft">
          <span class="mt-px shrink-0 text-ink-soft/70">
            <AppIcon name="shield" :size="14" />
          </span>
          <span>
            本工具仅供学习与个人备份使用。请遵守目标平台的服务条款与所在地区版权法律，
            不要将下载内容用于商业传播。因使用不当产生的法律责任由使用者自行承担。
          </span>
        </p>
        <p class="mt-4 text-xs text-ink-soft">© {{ YEAR }} GoVid · 由 yt-dlp 驱动</p>
      </div>
    </div>
  </footer>
</template>
