<script setup>
import { ref } from 'vue'

import AppIcon from './icons/AppIcon.vue'

const FAQS = [
  {
    q: '支持哪些平台？',
    a: '底层是 yt-dlp 官方解析器，YouTube、哔哩哔哩、Vimeo、TikTok、X、Instagram、抖音、优酷、腾讯视频等 1800+ 站点都在覆盖范围内。遇到平台改版导致解析失败，更新 yt-dlp 通常就能恢复。',
  },
  {
    q: '为什么某些清晰度标着「需合并」？',
    a: '高分辨率（1080P 及以上）在多数平台上音轨和视频轨是分开存放的。选中后服务端会自动下载两路并用 ffmpeg 合并成一个文件，你不需要做任何额外操作，只是多花一点合并时间。',
  },
  {
    q: '文件会保存到哪里？会不会占满硬盘？',
    a: '文件先落在项目目录下的 tmp/ 文件夹，通过页面的「保存到本地」按钮下载到你的下载目录。服务每次启动都会清空 tmp/，同时超过保留时长的任务会被自动回收，不会长期堆积。',
  },
  {
    q: '需要登录或者付费吗？',
    a: '不需要。当前版本没有账号体系、没有次数限制，也不需要付费。部分平台对会员或年龄限制内容会要求登录，这类视频暂时会解析失败并给出提示。',
  },
  {
    q: '中文文件名会不会乱码？',
    a: '不会。后端按 RFC 5987 用 UTF-8 编码文件名，Chrome、Safari、Edge 都能正确显示与保存中文标题。',
  },
  {
    q: '手机上能用吗？',
    a: '可以，只要手机和运行服务的电脑在同一个 Wi-Fi 下，用电脑的局域网 IP 加 8000 端口访问即可。页面是桌面优先设计，手机上会自动折成单列布局。',
  },
]

const openIndex = ref(0)

function toggle(index) {
  openIndex.value = openIndex.value === index ? -1 : index
}
</script>

<template>
  <section id="faq" class="container-page py-16 sm:py-20">
    <div class="mx-auto max-w-2xl text-center">
      <p class="eyebrow">
        <AppIcon name="info" :size="14" />
        常见问题
      </p>
      <h2 class="section-title mt-4">你可能想先弄清楚的事</h2>
    </div>

    <div class="mx-auto mt-11 flex max-w-3xl flex-col gap-3">
      <div
        v-for="(item, index) in FAQS"
        :key="item.q"
        class="overflow-hidden rounded-2xl border transition-colors duration-200"
        :class="openIndex === index ? 'border-primary/30 bg-surface shadow-card' : 'border-hairline bg-surface'"
      >
        <h3>
          <button
            type="button"
            class="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
            :aria-expanded="openIndex === index"
            :aria-controls="`govid-faq-${index}`"
            @click="toggle(index)"
          >
            <span class="text-sm font-semibold text-ink sm:text-base">{{ item.q }}</span>
            <span
              class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full transition-colors duration-200"
              :class="openIndex === index ? 'bg-primary text-white' : 'bg-surface-sub text-ink-soft'"
            >
              <AppIcon
                name="chevronDown"
                :size="15"
                :stroke-width="2.2"
                class="transition-transform duration-300"
                :class="openIndex === index ? 'rotate-180' : ''"
              />
            </span>
          </button>
        </h3>

        <div
          :id="`govid-faq-${index}`"
          class="grid transition-[grid-template-rows] duration-300 ease-out"
          :class="openIndex === index ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'"
        >
          <div class="overflow-hidden">
            <p class="px-5 pb-5 text-sm leading-relaxed text-ink-soft">{{ item.a }}</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
