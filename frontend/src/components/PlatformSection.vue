<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

import AppIcon from './icons/AppIcon.vue'
import PlatformLogo from './PlatformLogo.vue'
import { PLATFORM_ROWS } from '../data/platforms'

// 复制一份拼接成两段，位移到半程时回绕，实现无缝循环
const rows = PLATFORM_ROWS.map((row) => [...row, ...row])

/** 正常速度（px/s） */
const BASE_SPEED = 32
/** 鼠标悬停时的速度系数：减速而不是停车，观感更连续 */
const SLOW_FACTOR = 0.28
/** 速度过渡的收敛速率，越大切换越干脆 */
const EASE = 6

const trackEls = ref([])
const offsets = [0, 0]
const factors = [1, 1]

let targetFactor = 1
let rafId = 0
let lastTs = 0

function setTrack(el, index) {
  trackEls.value[index] = el
}

/** 悬停减速、离开恢复；用函数而不是模板里直接赋值，setup 的 let 在模板中不可写 */
function onEnter() {
  targetFactor = SLOW_FACTOR
}

function onLeave() {
  targetFactor = 1
}

function tick(ts) {
  const dt = Math.min((ts - (lastTs || ts)) / 1000, 0.05)
  lastTs = ts

  const k = Math.min(1, dt * EASE)

  trackEls.value.forEach((el, index) => {
    if (!el) return

    // 速度平滑逼近目标值：悬停瞬间不跳变，松开也缓缓回到常速
    factors[index] += (targetFactor - factors[index]) * k

    const half = el.scrollWidth / 2
    if (!half) return

    // 第 0 行向左、第 1 行向右；位移始终循环在 (-half, 0] 区间
    const dir = index === 1 ? 1 : -1
    let next = offsets[index] + dir * BASE_SPEED * factors[index] * dt
    if (next <= -half) next += half
    if (next > 0) next -= half
    offsets[index] = next

    el.style.transform = `translate3d(${next.toFixed(2)}px, 0, 0)`
  })

  rafId = window.requestAnimationFrame(tick)
}

onMounted(() => {
  // 开了「减少动态效果」就完全不滚，静态展示即可
  if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return
  rafId = window.requestAnimationFrame(tick)
})

onBeforeUnmount(() => {
  if (rafId) window.cancelAnimationFrame(rafId)
})
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
          主流站点基本都在里面，抖音走独立通道，不需要登录、粘贴链接或分享文案都能解析。
        </p>
      </div>
    </div>

    <div
      class="marquee-mask mt-11 flex flex-col gap-4 overflow-hidden"
      @mouseenter="onEnter"
      @mouseleave="onLeave"
    >
      <div
        v-for="(row, rowIndex) in rows"
        :key="rowIndex"
        :ref="(el) => setTrack(el, rowIndex)"
        class="flex w-max gap-4 will-change-transform"
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
      覆盖 YouTube、哔哩哔哩、抖音、优酷、腾讯视频等，完整名单见 yt-dlp 官方支持站点表
    </p>
  </section>
</template>
