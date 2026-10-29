<script setup>
import { ref } from 'vue'
import AppIcon from './components/AppIcon.vue'
import VideoParser from './components/VideoParser.vue'

const supportedPlatforms = [
  { name: '抖音', icon: 'music', color: '#000000' },
  { name: '快手', icon: 'zap', color: '#FF6600' },
]
</script>

<template>
  <div class="min-h-screen bg-gradient-to-b from-white to-gray-50">
    <!-- Hero Section -->
    <section class="relative overflow-hidden">
      <!-- 背景装饰 -->
      <div class="pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
        <div
          class="absolute left-1/2 top-[-18rem] h-[36rem] w-[64rem] -translate-x-1/2 rounded-full opacity-50 blur-3xl"
          style="background: radial-gradient(closest-side, rgba(16, 185, 129, 0.25), transparent 70%)"
        />
        <div
          class="absolute inset-0 opacity-[0.04]"
          style="
            background-image: linear-gradient(#0f172a 1px, transparent 1px),
              linear-gradient(90deg, #0f172a 1px, transparent 1px);
            background-size: 48px 48px;
            mask-image: radial-gradient(ellipse 65% 55% at 50% 0%, #000, transparent 80%);
          "
        />
      </div>

      <div class="container mx-auto max-w-4xl px-4 pb-16 pt-12 sm:pt-20">
        <!-- 标题区 -->
        <div class="mx-auto flex max-w-2xl flex-col items-center text-center">
          <div class="inline-flex items-center gap-2 rounded-full bg-primary-soft px-4 py-1.5 text-sm font-medium text-primary-deep">
            <AppIcon name="zap" :size="14" :stroke-width="2.5" />
            零流量 · 纯直链 · 完全免费
          </div>

          <h1 class="mt-6 text-4xl font-bold leading-tight tracking-tight text-ink sm:text-5xl lg:text-6xl">
            <span class="bg-gradient-to-r from-primary to-primary-deep bg-clip-text text-transparent">
              GoVid Lite
            </span>
            <br />
            <span class="text-3xl sm:text-4xl lg:text-5xl">直连版视频下载</span>
          </h1>

          <p class="mt-5 max-w-xl text-base leading-relaxed text-ink-soft sm:text-lg">
            粘贴链接即可解析，支持多清晰度选择，原画质无水印直出
          </p>
        </div>

        <!-- 解析区 -->
        <div class="mx-auto mt-10 max-w-2xl">
          <VideoParser />
        </div>

        <!-- 支持平台 -->
        <div class="mx-auto mt-12 max-w-2xl">
          <p class="mb-4 text-center text-sm font-medium text-ink-softer">
            当前支持平台
          </p>
          <div class="flex flex-wrap items-center justify-center gap-3">
            <div
              v-for="platform in supportedPlatforms"
              :key="platform.name"
              class="flex items-center gap-2 rounded-lg border border-border bg-white px-4 py-2 text-sm font-medium text-ink shadow-sm"
            >
              <AppIcon :name="platform.icon" :size="16" :stroke-width="2" />
              {{ platform.name }}
            </div>
          </div>
        </div>

        <!-- 特性说明 -->
        <ul class="mx-auto mt-10 flex max-w-3xl flex-wrap items-center justify-center gap-x-6 gap-y-3">
          <li
            v-for="item in [
              { icon: 'zap', text: '解析速度快' },
              { icon: 'film', text: '原画质无水印' },
              { icon: 'shield-check', text: '隐私安全' },
            ]"
            :key="item.text"
            class="flex items-center gap-2 text-sm text-ink-soft"
          >
            <span class="flex h-6 w-6 items-center justify-center rounded-full bg-primary-soft text-primary-deep">
              <AppIcon :name="item.icon" :size="13" :stroke-width="2" />
            </span>
            {{ item.text }}
          </li>
        </ul>
      </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-border bg-white py-8">
      <div class="container mx-auto max-w-4xl px-4 text-center text-sm text-ink-softer">
        <p>GoVid Lite · 基于开源项目构建</p>
      </div>
    </footer>
  </div>
</template>
