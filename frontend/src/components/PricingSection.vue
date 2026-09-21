<script setup>
import AppIcon from './icons/AppIcon.vue'

const emit = defineEmits(['notify'])

const PLANS = [
  {
    name: '免费版',
    tagline: '个人日常够用',
    price: '¥0',
    unit: '/ 永久',
    highlight: false,
    features: ['每天 3 次解析下载', '最高 1080P 画质', '进度实时可见', '本机运行，不上传数据'],
    cta: '当前版本',
    disabled: true,
  },
  {
    name: 'Pro 版',
    tagline: '重度使用者与创作者',
    price: '即将公布',
    unit: '',
    highlight: true,
    features: ['不限解析与下载次数', '4K 超高清与仅音频导出', 'AI 视频总结与思维导图', '字幕下载（SRT / VTT / TXT）'],
    cta: '敬请期待',
    disabled: false,
  },
]
</script>

<template>
  <section id="pricing" class="border-y border-hairline bg-surface-sub/60 py-16 sm:py-20">
    <div class="container-page">
      <div class="mx-auto max-w-2xl text-center">
        <p class="eyebrow">
          <AppIcon name="gauge" :size="14" />
          价格
        </p>
        <h2 class="section-title mt-4">先把免费版做扎实</h2>
        <p class="section-sub mt-3">Pro 版在规划中，落地前不会向你收一分钱。</p>
      </div>

      <div class="mx-auto mt-12 grid max-w-3xl gap-6 sm:grid-cols-2">
        <article
          v-for="plan in PLANS"
          :key="plan.name"
          class="relative flex flex-col rounded-2xl border bg-surface p-6"
          :class="plan.highlight ? 'border-primary shadow-primary' : 'border-hairline shadow-card'"
        >
          <span
            v-if="plan.highlight"
            class="absolute -top-3 left-6 rounded-pill bg-primary px-3 py-1 text-xs font-semibold text-white"
          >
            规划中
          </span>

          <h3 class="text-lg font-semibold text-ink">{{ plan.name }}</h3>
          <p class="mt-1 text-sm text-ink-soft">{{ plan.tagline }}</p>

          <p class="mt-5 flex items-baseline gap-1.5">
            <span
              class="font-bold tracking-tight"
              :class="plan.price === '即将公布' ? 'text-2xl text-ink' : 'text-4xl text-ink'"
            >
              {{ plan.price }}
            </span>
            <span v-if="plan.unit" class="text-sm text-ink-soft">{{ plan.unit }}</span>
          </p>

          <ul class="mt-6 flex flex-1 flex-col gap-3 border-t border-hairline pt-6">
            <li
              v-for="feature in plan.features"
              :key="feature"
              class="flex items-start gap-2.5 text-sm text-ink-soft"
            >
              <span class="mt-0.5" :class="plan.highlight ? 'text-primary' : 'text-ink-soft/60'">
                <AppIcon name="check" :size="15" :stroke-width="2.4" />
              </span>
              {{ feature }}
            </li>
          </ul>

          <button
            type="button"
            class="mt-7 w-full"
            :class="plan.disabled ? 'btn-secondary' : 'btn-primary'"
            @click="!plan.disabled && emit('notify')"
          >
            {{ plan.cta }}
          </button>
        </article>
      </div>

      <p class="mx-auto mt-8 max-w-2xl text-center text-xs leading-relaxed text-ink-soft">
        当前为内测版本，免费版暂未施加次数限制，所有功能都可直接使用。Pro 版能力上线后会在这里同步说明。
      </p>
    </div>
  </section>
</template>
