<script setup>
defineProps({
  name: { type: String, required: true },
  color: { type: String, default: '#10B981' },
  mark: { type: String, required: true },
})
</script>

<template>
  <div
    class="flex shrink-0 items-center gap-3 rounded-2xl border border-hairline bg-surface px-4 py-3 transition-shadow duration-300"
  >
    <span
      class="flex h-9 w-9 items-center justify-center rounded-xl text-[13px] font-bold leading-none text-white"
      :style="{ backgroundColor: color }"
      aria-hidden="true"
    >
      {{ mark }}
    </span>
    <span class="whitespace-nowrap text-sm font-semibold text-ink">{{ name }}</span>
  </div>
</template>
