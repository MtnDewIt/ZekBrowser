<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { ref, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps<{
  class?: HTMLAttributes['class']
}>()

const container = ref<HTMLElement | null>(null)

function onWheel(e: WheelEvent) {
  const el = container.value
  if (!el) return
  // If scrolling vertically, let the page handle it
  if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) return
  // Only prevent default for horizontal scrolling when the table actually overflows
  if (el.scrollWidth > el.clientWidth) {
    e.preventDefault()
    el.scrollLeft += e.deltaX
  }
}

onMounted(() => {
  container.value?.addEventListener('wheel', onWheel, { passive: false })
})
onBeforeUnmount(() => {
  container.value?.removeEventListener('wheel', onWheel)
})
</script>

<template>
  <div ref="container" data-slot="table-container" class="relative w-full overflow-x-auto">
    <table data-slot="table" :class="cn('w-full caption-bottom text-sm', props.class)">
      <slot />
    </table>
  </div>
</template>
