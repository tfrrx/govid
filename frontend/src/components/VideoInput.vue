<script setup>
import { computed, ref } from 'vue'

import AppIcon from './icons/AppIcon.vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  busy: { type: Boolean, default: false },
  invalid: { type: Boolean, default: false },
  message: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'submit', 'clear'])

const inputRef = ref(null)

const SAMPLES = [
  { label: 'B 站示例', url: 'https://www.bilibili.com/video/BV1xx411c7mD' },
  { label: 'YouTube 示例', url: 'https://www.youtube.com/watch?v=aqz-KE-bpKQ' },
]

const hasValue = computed(() => props.modelValue.trim().length > 0)

function onInput(event) {
  emit('update:modelValue', event.target.value)
}

function onSubmit() {
  if (props.busy) return
  emit('submit')
}

function applySample(url) {
  emit('update:modelValue', url)
  inputRef.value?.focus()
}

function clearInput() {
  emit('update:modelValue', '')
  emit('clear')
  inputRef.value?.focus()
}
</script>

<template>
  <form class="w-full" novalidate @submit.prevent="onSubmit">
    <label for="govid-url" class="sr-only">视频链接</label>

    <div
      class="flex flex-col gap-2.5 border border-hairline bg-surface p-2 shadow-float transition-shadow sm:flex-row sm:items-center sm:rounded-pill sm:pl-3"
      :class="invalid ? 'rounded-3xl border-error/60' : 'rounded-3xl sm:rounded-pill'"
    >
      <div class="flex flex-1 items-center gap-2.5 px-3 sm:px-2">
        <AppIcon name="link" :size="18" class="text-ink-soft/70" />

        <input
          id="govid-url"
          ref="inputRef"
          :value="modelValue"
          type="url"
          inputmode="url"
          autocomplete="off"
          autocapitalize="off"
          spellcheck="false"
          enterkeyhint="go"
          :aria-invalid="invalid ? 'true' : 'false'"
          :aria-describedby="message ? 'govid-url-error' : undefined"
          placeholder="粘贴 YouTube / B 站 / Vimeo 等视频链接…"
          class="min-w-0 flex-1 border-0 bg-transparent py-3.5 text-base text-ink outline-none placeholder:text-ink-soft/70"
          @input="onInput"
        />

        <button
          v-if="hasValue && !busy"
          type="button"
          class="rounded-full p-1.5 text-ink-soft transition-colors duration-200 hover:bg-surface-sub hover:text-ink"
          aria-label="清空输入"
          @click="clearInput"
        >
          <AppIcon name="close" :size="16" :stroke-width="2" />
        </button>
      </div>

      <button
        type="submit"
        class="btn-primary shrink-0 sm:min-w-[136px]"
        :disabled="busy || !hasValue"
      >
        <span
          v-if="busy"
          class="h-4 w-4 animate-spin rounded-full border-2 border-white/35 border-t-white"
          aria-hidden="true"
        />
        <AppIcon v-else name="search" :size="18" />
        <span>{{ busy ? '解析中…' : '开始解析' }}</span>
      </button>
    </div>

    <p
      v-if="message"
      id="govid-url-error"
      class="mt-2.5 flex items-center gap-1.5 text-sm text-error sm:pl-6"
      role="alert"
    >
      <AppIcon name="alert" :size="15" :stroke-width="1.9" />
      {{ message }}
    </p>

    <div class="mt-3 flex flex-wrap items-center gap-2 sm:pl-6">
      <span class="text-xs text-ink-soft">没链接？试试：</span>
      <button
        v-for="sample in SAMPLES"
        :key="sample.label"
        type="button"
        class="chip transition-colors duration-200 hover:border-primary/40 hover:bg-primary-soft hover:text-primary-deep"
        @click="applySample(sample.url)"
      >
        {{ sample.label }}
      </button>
    </div>
  </form>
</template>
