<script setup>
import AppIcon from './icons/AppIcon.vue'
import PlatformLogo from './PlatformLogo.vue'
import { PLATFORM_ROWS } from '../data/platforms'

// 复制一份拼接成两段，配合 translateX(-50%) 实现无缝循环
const rows = PLATFORM_ROWS.map((row) => [...row, ...row])
</script>

<template>
  <section id="platforms" class="py-16 sm:py-20">
    <div class="container-page">
      <div class="mx-auto max-w-2xl text-center">
        <p class="eyebrow">
          <AppIcon name="globe" :size="14" />
          平台覆盖
        </p>
        <h2 class="section-title mt-4">1200+ 平台，一条链接就够了</h2>
        <p class="section-sub mt-3">
          底层是 yt-dlp 官方解析器，覆盖 1201 个顶级站点；抖音单独走自研通道，零 cookie
          直取，不依赖第三方接口。
        </p>
      </div>
    </div>

    <div class="marquee-mask marquee-track mt-11 flex flex-col gap-4 overflow-hidden">
      <div
        v-for="(row, rowIndex) in rows"
        :key="rowIndex"
        class="flex w-max gap-4"
        :class="rowIndex === 1 ? 'animate-marquee flex-row-reverse' : 'animate-marquee'"
        :style="{ animationDirection: rowIndex === 1 ? 'reverse' : 'normal' }"
        aria-hidden="true"
      >
        <PlatformLogo
          v-for="platform in row"
          :key="`${rowIndex}-${platform.name}-${platform.mark}`"
          :name="platform.name"
          :color="platform.color"
          :mark="platform.mark"
        />
      </div>
    </div>

    <p class="mt-6 text-center text-xs text-ink-soft">
      覆盖 YouTube、哔哩哔哩、Vimeo、TikTok、X、抖音、优酷等，完整列表见 yt-dlp 官方支持站点表
    </p>
  </section>
</template>
