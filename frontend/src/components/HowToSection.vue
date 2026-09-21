<script setup>
import AppIcon from './icons/AppIcon.vue'

const STEPS = [
  {
    icon: 'link',
    title: '粘贴视频链接',
    desc: '从浏览器地址栏复制视频页地址，粘进首页输入框按回车即可。',
  },
  {
    icon: 'layers',
    title: '挑一个清晰度',
    desc: '列表标出分辨率、格式与预估体积，标「需合并」的会自动处理音轨。',
  },
  {
    icon: 'download',
    title: '保存到本地',
    desc: '下完点一下保存，文件直接落到你的下载目录，随时可以再删。',
  },
]
</script>

<template>
  <section id="howto" class="border-y border-hairline bg-surface-sub/60 py-16 sm:py-20">
    <div class="container-page">
      <div class="mx-auto max-w-2xl text-center">
        <p class="eyebrow">
          <AppIcon name="wand" :size="14" />
          三步上手
        </p>
        <h2 class="section-title mt-4">从链接到本地文件，只需三步</h2>
        <p class="section-sub mt-3">不需要注册，不需要安装浏览器扩展，打开页面就能用。</p>
      </div>

      <ol class="relative mt-12 grid gap-6 md:grid-cols-3" role="list">
        <li
          v-for="(step, index) in STEPS"
          :key="step.title"
          class="relative flex flex-col items-start gap-4 rounded-2xl border border-hairline bg-surface p-6"
        >
          <div class="flex w-full items-center justify-between">
            <span
              class="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary-dark text-white shadow-primary"
            >
              <AppIcon :name="step.icon" :size="20" />
            </span>
            <span class="text-4xl font-bold leading-none text-primary/15">
              {{ String(index + 1).padStart(2, '0') }}
            </span>
          </div>

          <div>
            <h3 class="text-base font-semibold text-ink">{{ step.title }}</h3>
            <p class="mt-2 text-sm leading-relaxed text-ink-soft">{{ step.desc }}</p>
          </div>
        </li>
      </ol>
    </div>
  </section>
</template>
