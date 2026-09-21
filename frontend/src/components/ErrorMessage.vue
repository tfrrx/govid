<script setup>
import AppIcon from './icons/AppIcon.vue'

defineProps({
  toasts: { type: Array, default: () => [] },
})

const emit = defineEmits(['dismiss'])

const STYLE = {
  error: {
    icon: 'alert',
    wrap: 'border-error/25 bg-surface text-ink',
    badge: 'bg-error-soft text-error',
  },
  success: {
    icon: 'checkCircle',
    wrap: 'border-primary/25 bg-surface text-ink',
    badge: 'bg-primary-soft text-primary-deep',
  },
  info: {
    icon: 'info',
    wrap: 'border-hairline bg-surface text-ink',
    badge: 'bg-surface-sub text-ink-soft',
  },
}
</script>

<template>
  <div
    class="pointer-events-none fixed inset-x-0 top-4 z-50 flex flex-col items-center gap-2 px-4"
    aria-live="polite"
    aria-atomic="false"
  >
    <TransitionGroup
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="-translate-y-3 opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-active-class="transition duration-200 ease-in absolute"
      leave-from-class="translate-y-0 opacity-100"
      leave-to-class="-translate-y-2 opacity-0"
      move-class="transition duration-200"
    >
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="pointer-events-auto flex w-full max-w-md items-start gap-3 rounded-2xl border px-4 py-3 shadow-float backdrop-blur-sm"
        :class="(STYLE[toast.type] || STYLE.info).wrap"
        :role="toast.type === 'error' ? 'alert' : 'status'"
      >
        <span
          class="mt-px flex h-7 w-7 shrink-0 items-center justify-center rounded-full"
          :class="(STYLE[toast.type] || STYLE.info).badge"
        >
          <AppIcon :name="(STYLE[toast.type] || STYLE.info).icon" :size="16" :stroke-width="2" />
        </span>

        <p class="min-w-0 flex-1 py-1 text-sm leading-relaxed">{{ toast.message }}</p>

        <button
          type="button"
          class="-mr-1 mt-px rounded-full p-1.5 text-ink-soft transition-colors duration-200 hover:bg-surface-sub hover:text-ink"
          aria-label="关闭提示"
          @click="emit('dismiss', toast.id)"
        >
          <AppIcon name="close" :size="14" :stroke-width="2.2" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>
