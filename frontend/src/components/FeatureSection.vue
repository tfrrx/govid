<script setup>
import AppIcon from './icons/AppIcon.vue'

const FEATURES = [
  {
    icon: 'zap',
    title: '极速解析',
    desc: '一条链接换回完整的视频档案，不用等、不用装插件。',
    points: ['标题 / 封面 / 时长 / 作者一次拿全', '最高 4K 全部清晰度列齐', '自动识别平台并排序推荐'],
  },
  {
    icon: 'gauge',
    title: '全流程可见',
    desc: '解析、下载、合并三段进度分开呈现，卡在哪一步一眼看得出。',
    points: ['分段式进度条，不再猜还剩多久', '实时速度 / 已下载体积 / 剩余时间', '中途可取消，不留半个残文件'],
  },
  {
    icon: 'image',
    title: '无水印原画',
    desc: '直取平台原始文件，不加水印、不二次转码，画质就是源站的画质。',
    points: ['抖音拿到的是无水印原图与原视频', '原码率直出，不是录屏或压缩版', '中文文件名不乱码，落地即可播放'],
  },
]
</script>

<template>
  <section id="features" class="container-page py-16 sm:py-20">
    <div class="mx-auto max-w-2xl text-center">
      <p class="eyebrow">
        <AppIcon name="sparkles" :size="14" />
        核心能力
      </p>
      <h2 class="section-title mt-4">把下载这件小事做扎实</h2>
      <p class="section-sub mt-3">没有花哨的概念，只解决三件事：快、干净、看得见。</p>
    </div>

    <div class="mt-12 grid gap-6 md:grid-cols-3">
      <article
        v-for="feature in FEATURES"
        :key="feature.title"
        class="card card-hover group flex flex-col p-6"
      >
        <span
          class="flex h-11 w-11 items-center justify-center rounded-xl bg-primary-soft text-primary-deep transition-colors duration-[250ms] group-hover:bg-primary group-hover:text-white"
        >
          <AppIcon :name="feature.icon" :size="21" />
        </span>

        <h3 class="mt-5 text-lg font-semibold text-ink">{{ feature.title }}</h3>
        <p class="mt-2 text-sm leading-relaxed text-ink-soft">{{ feature.desc }}</p>

        <ul class="mt-5 flex flex-col gap-2.5 border-t border-hairline pt-5">
          <li
            v-for="point in feature.points"
            :key="point"
            class="flex items-start gap-2.5 text-sm text-ink-soft"
          >
            <span class="mt-0.5 text-primary">
              <AppIcon name="check" :size="15" :stroke-width="2.4" />
            </span>
            <span>{{ point }}</span>
          </li>
        </ul>
      </article>
    </div>
  </section>
</template>
