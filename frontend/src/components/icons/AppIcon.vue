<script setup>
import { computed } from 'vue'

/**
 * 内联 SVG 图标集：不引第三方图标库，零依赖、可改色、可无障碍隐藏。
 * 所有图标统一 24x24 视窗、stroke 取 currentColor。
 */
const ICONS = {
  link: [
    'M10.5 13.5a4.5 4.5 0 0 0 6.4 0l2.6-2.6a4.5 4.5 0 0 0-6.4-6.4l-1.1 1.1',
    'M13.5 10.5a4.5 4.5 0 0 0-6.4 0l-2.6 2.6a4.5 4.5 0 0 0 6.4 6.4l1.1-1.1',
  ],
  search: ['M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z', 'M21 21l-4.3-4.3'],
  download: ['M12 3v12', 'M7 11l5 5 5-5', 'M4 20h16'],
  check: ['M20 6 9 17l-5-5'],
  checkCircle: [
    'M12 22c5.5 0 10-4.5 10-10S17.5 2 12 2 2 6.5 2 12s4.5 10 10 10Z',
    'm8.4 12.4 2.4 2.4 4.8-5.2',
  ],
  spinner: ['M12 3a9 9 0 1 0 9 9'],
  close: ['M18 6 6 18', 'M6 6l12 12'],
  alert: [
    'M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z',
    'M12 9v4',
    'M12 17h.01',
  ],
  info: [
    'M12 22c5.5 0 10-4.5 10-10S17.5 2 12 2 2 6.5 2 12s4.5 10 10 10Z',
    'M12 16v-4',
    'M12 8h.01',
  ],
  zap: ['M13 2 4 14h7l-1 8 9-12h-7l1-8Z'],
  layers: ['m12 2 9 5-9 5-9-5 9-5Z', 'm3 12 9 5 9-5', 'm3 17 9 5 9-5'],
  shield: ['M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z', 'm9 12 2 2 4-4'],
  clock: ['M12 22c5.5 0 10-4.5 10-10S17.5 2 12 2 2 6.5 2 12s4.5 10 10 10Z', 'M12 7v5l3 2'],
  play: ['M8 5.1v14l11-7-11-7Z'],
  chevronDown: ['m6 9 6 6 6-6'],
  arrowRight: ['M5 12h14', 'm13 6 6 6-6 6'],
  sparkles: [
    'm12 3 1.9 4.6L18.5 9.5l-4.6 1.9L12 16l-1.9-4.6L5.5 9.5l4.6-1.9L12 3Z',
    'M19 15l.8 1.9L22 17.7l-2.2.8L19 21l-.8-2.5L16 17.7l2.2-.8L19 15Z',
  ],
  film: [
    'M4 3h16a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z',
    'M3 8h18',
    'M3 16h18',
    'M8 3v18',
    'M16 3v18',
  ],
  music: [
    'M9 18V6l10-2v12',
    'M7.5 20a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z',
    'M17.5 18a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z',
  ],
  globe: [
    'M12 22c5.5 0 10-4.5 10-10S17.5 2 12 2 2 6.5 2 12s4.5 10 10 10Z',
    'M2 12h20',
    'M12 2a15 15 0 0 1 0 20 15 15 0 0 1 0-20Z',
  ],
  copy: ['M9 9h10v10H9z', 'M15 9V5H5v10h4'],
  rotate: ['M3.5 12a8.5 8.5 0 1 0 2.8-6.3', 'M3 4v5h5'],
  image: ['M4 4h16a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Z', 'm3 16 5-5 5 5 2-2 5 5', 'M15.5 9h.01'],
  users: [
    'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2',
    'M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z',
    'M22 21v-2a4 4 0 0 0-3-3.9',
  ],
  gauge: ['M12 14 16 9', 'M3.5 19a10 10 0 1 1 17 0', 'M12 19h.01'],
  wand: ['m15 4 5 5', 'M4 20 20 4', 'm5 6 1 1', 'm18 17 1 1'],
}

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 20 },
  strokeWidth: { type: [Number, String], default: 1.8 },
  filled: { type: Boolean, default: false },
})

const paths = computed(() => ICONS[props.name] ?? ICONS.info)
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
    class="shrink-0"
  >
    <path
      v-for="(d, index) in paths"
      :key="index"
      :d="d"
      :fill="filled ? 'currentColor' : 'none'"
      :stroke="filled ? 'none' : 'currentColor'"
    />
  </svg>
</template>
