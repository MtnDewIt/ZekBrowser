<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, computed, nextTick } from 'vue'

const props = defineProps<{
  modelValue: string
  options: { label: string; value: string }[]
  class?: string
  iconOnly?: boolean
}>()

const emits = defineEmits<{
  (e: 'update:modelValue', val: string): void
}>()

const open = ref(false)
const root = ref<HTMLElement | null>(null)
const dropdownStyle = ref<Record<string, string>>({})

async function toggle() {
  open.value = !open.value
  if (open.value) await positionDropdown()
}
function close() { open.value = false }
function select(val: string) { emits('update:modelValue', val); close() }

async function positionDropdown() {
  await nextTick()
  if (!root.value) return

  // Prefer anchoring to the nearest ancestor with the 'relative' class (layout wrapper)
  // This lets the dropdown align with the end of the search box when the select
  // is rendered as an icon inside the input container.
  let anchor: HTMLElement | null = null
  try {
    // search from parentElement to avoid selecting the Select root itself
    anchor = root.value.parentElement?.closest('.relative') as HTMLElement | null
  } catch (e) {
    anchor = null
  }
  if (!anchor) anchor = root.value.parentElement || root.value

  const rect = anchor.getBoundingClientRect()
  // position fixed relative to viewport so it escapes any overflow clipping
  // align the dropdown's right edge with the anchor element's right edge
  // subtract a small offset so the dropdown sits slightly to the right
  const OFFSET_PX = 17
  const rawRight = Math.round(window.innerWidth - rect.right - OFFSET_PX)
  const right = Math.max(0, rawRight)
  dropdownStyle.value = {
    position: 'fixed',
    top: `${rect.bottom}px`,
    right: `${right}px`,
    minWidth: `${rect.width}px`,
  }
}

function onDocClick(e: MouseEvent) {
  if (!root.value) return
  if (!(e.target instanceof Node)) return
  if (!root.value.contains(e.target)) close()
}

onMounted(() => {
  document.addEventListener('click', onDocClick)
  window.addEventListener('resize', positionDropdown, { passive: true })
  window.addEventListener('scroll', positionDropdown, { passive: true })
})
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocClick)
  window.removeEventListener('resize', positionDropdown)
  window.removeEventListener('scroll', positionDropdown)
})

const selectedLabel = computed(() => {
  const opt = props.options.find(o => o.value === props.modelValue)
  return opt ? opt.label : (props.options[0]?.label ?? '')
})

watch(() => props.modelValue, () => { /* reactive hook for consumers */ })
</script>

<template>
  <div ref="root" class="relative inline-block" :class="class">
    <button
      type="button"
      :class="[
        props.iconOnly
          ? 'h-8 w-8 p-0 rounded-md bg-transparent border-0 flex items-center justify-center focus:outline-none focus:ring-0'
          : 'h-10 min-w-[8rem] px-3 rounded-md border border-input bg-background text-foreground text-sm relative flex items-center focus:outline-none focus:ring-0'
      ]"
      @click="toggle"
    >
      <template v-if="!props.iconOnly">
        <span class="truncate pr-8">{{ selectedLabel }}</span>
      </template>
      <span class="pointer-events-none" :class="props.iconOnly ? '' : 'absolute right-3 top-1/2 -translate-y-1/2'">
        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" :style="props.iconOnly ? 'width:1.5em;height:1.5em' : 'width:1.35em;height:1.35em'"><path d="M6 8l4 4 4-4" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </span>
    </button>

    <teleport to="body">
      <ul v-if="open" :style="dropdownStyle" class="z-[99999] mt-1 max-h-56 overflow-auto rounded-md border border-input bg-background text-foreground shadow-lg">
        <li v-for="opt in options" :key="opt.value" @click.stop="select(opt.value)" class="px-3 py-2 cursor-pointer hover:bg-muted/60 hover:text-foreground active:bg-transparent focus:outline-none">
          {{ opt.label }}
        </li>
      </ul>
    </teleport>
  </div>
</template>
