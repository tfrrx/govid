<script setup>
import sponsorSticker from '../assets/sponsor-sticker.jpg'
import AppIcon from './icons/AppIcon.vue'

const PERKS = [
  '不限解析与下载次数',
  '最高 4K 画质 · 无水印原画',
  '进度实时可见，随时可取消',
  '中文文件名不乱码，直出可播放',
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
        <h2 class="section-title mt-4">当前版本完全免费</h2>
        <p class="section-sub mt-3">所有功能直接开放，不限次数、不加水印、不需要注册账号。</p>
      </div>

      <div class="mx-auto mt-12 grid max-w-4xl gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <!-- 免费说明 -->
        <article class="card flex flex-col p-7">
          <span class="flex h-11 w-11 items-center justify-center rounded-xl bg-primary-soft text-primary-deep">
            <AppIcon name="checkCircle" :size="21" />
          </span>

          <h3 class="mt-5 text-lg font-semibold text-ink">免费使用</h3>
          <p class="mt-1 text-sm text-ink-soft">无试用期、无功能锁，打开就能用。</p>

          <ul class="mt-6 flex flex-1 flex-col gap-3 border-t border-hairline pt-6">
            <li
              v-for="perk in PERKS"
              :key="perk"
              class="flex items-start gap-2.5 text-sm text-ink-soft"
            >
              <span class="mt-0.5 text-primary">
                <AppIcon name="check" :size="15" :stroke-width="2.4" />
              </span>
              {{ perk }}
            </li>
          </ul>
        </article>

        <!-- 赞助位：先放贴纸，收款码稍后替换 -->
        <article class="card flex flex-col items-center justify-center p-7 text-center">
          <h3 class="max-w-[16rem] text-balance text-lg font-semibold text-ink">
            如果你对此工作感到满意，请给小人一点打赏！
          </h3>
          <p class="mt-2 text-sm text-ink-soft">你的支持是继续维护下去的动力。</p>

          <img
            :src="sponsorSticker"
            alt="赞助支持"
            width="959"
            height="959"
            loading="lazy"
            decoding="async"
            class="mt-6 w-full max-w-[212px] rounded-2xl"
          />
        </article>
      </div>
    </div>
  </section>
</template>
