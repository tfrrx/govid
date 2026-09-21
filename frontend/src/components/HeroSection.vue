<script setup>
import AppIcon from './icons/AppIcon.vue'

defineProps({
  id: { type: String, default: undefined },
})
</script>

<template>
  <section id="govid-hero" class="relative overflow-hidden">
    <!-- 背景：品牌色柔光 + 细网格，纯 CSS 不引图片 -->
    <div class="pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
      <div class="absolute inset-0 bg-surface" />
      <div
        class="absolute left-1/2 top-[-18rem] h-[36rem] w-[64rem] -translate-x-1/2 rounded-full opacity-70 blur-3xl"
        style="background: radial-gradient(closest-side, rgba(16, 185, 129, 0.22), transparent 70%)"
      />
      <div
        class="absolute inset-0 opacity-[0.035]"
        style="
          background-image: linear-gradient(#0f172a 1px, transparent 1px),
            linear-gradient(90deg, #0f172a 1px, transparent 1px);
          background-size: 44px 44px;
          mask-image: radial-gradient(ellipse 60% 50% at 50% 0%, #000, transparent 75%);
        "
      />
    </div>

    <div class="container-page pb-12 pt-14 sm:pt-20 lg:pb-16">
      <div class="mx-auto flex max-w-3xl flex-col items-center text-center">
        <p class="eyebrow">
          <AppIcon name="zap" :size="14" />
          覆盖 1200+ 站点 · 无水印直出 · 完全免费
        </p>

        <h1
          class="mt-5 text-4xl font-bold leading-[1.12] tracking-tight text-ink sm:text-5xl lg:text-6xl"
        >
          全网视频
          <span class="bg-gradient-to-r from-primary to-primary-deep bg-clip-text text-transparent">
            秒速下载
          </span>
          到本地
        </h1>

        <p class="mt-5 max-w-2xl text-base leading-relaxed text-ink-soft sm:text-lg">
          粘贴链接或 App 分享文案，即可解析标题、封面与全部可用清晰度。选好画质一键下载，
          进度实时可见，成品无水印、原画质直出。
        </p>
      </div>

      <!-- 输入区由父组件注入，方便与状态机联动 -->
      <div class="mx-auto mt-9 max-w-2xl">
        <slot name="form" />
      </div>

      <ul class="mx-auto mt-9 flex max-w-3xl flex-wrap items-center justify-center gap-x-7 gap-y-3">
        <li
          v-for="item in [
            { icon: 'zap', text: '解析通常 5 秒内出结果' },
            { icon: 'film', text: '最高 4K · 音视频自动合并' },
            { icon: 'image', text: '无水印原画 · 直取源文件' },
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
</template>
