<script setup>
import { onMounted, onUnmounted, ref } from 'vue'

import AppIcon from './icons/AppIcon.vue'

const LINKS = [
  { label: '核心能力', href: '#features' },
  { label: '使用流程', href: '#howto' },
  { label: '平台覆盖', href: '#platforms' },
  { label: '价格', href: '#pricing' },
  { label: '常见问题', href: '#faq' },
]

const scrolled = ref(false)

function onScroll() {
  scrolled.value = window.scrollY > 12
}

onMounted(() => {
  onScroll()
  window.addEventListener('scroll', onScroll, { passive: true })
})

onUnmounted(() => window.removeEventListener('scroll', onScroll))

function goToInput() {
  document.getElementById('govid-hero')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  window.setTimeout(() => document.getElementById('govid-url')?.focus(), 420)
}
</script>

<template>
  <header
    class="sticky top-0 z-40 border-b backdrop-blur-md transition-colors duration-300"
    :class="scrolled ? 'border-hairline bg-surface/85' : 'border-transparent bg-surface/60'"
  >
    <div class="container-page flex h-16 items-center justify-between gap-4">
      <a href="#govid-hero" class="flex items-center gap-2.5" aria-label="GoVid 首页">
        <span
          class="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary-dark text-white"
          aria-hidden="true"
        >
          <AppIcon name="download" :size="18" :stroke-width="2.2" />
        </span>
        <span class="text-lg font-bold tracking-tight text-ink">GoVid</span>
      </a>

      <nav class="hidden items-center gap-1 md:flex" aria-label="主导航">
        <a
          v-for="link in LINKS"
          :key="link.href"
          :href="link.href"
          class="rounded-pill px-3.5 py-2 text-sm font-medium text-ink-soft transition-colors duration-200 hover:bg-primary-soft hover:text-primary-deep"
        >
          {{ link.label }}
        </a>
      </nav>

      <button type="button" class="btn-primary px-5 py-2.5 text-sm" @click="goToInput">
        <AppIcon name="zap" :size="16" />
        开始使用
      </button>
    </div>
  </header>
</template>
