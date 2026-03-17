<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, nextTick } from 'vue'

const props = defineProps<{
  modelValue: string
  options: { label: string; value: string; icon?: string; iconRounded?: boolean }[]
  class?: string
  iconOnly?: boolean
  fullWidthTrigger?: boolean
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

  let anchor: HTMLElement | null = null
  try {
    anchor = root.value.parentElement?.closest('.relative') as HTMLElement | null
  } catch (e) {
    anchor = null
  }
  if (!anchor) anchor = root.value.parentElement || root.value

  const rect = anchor.getBoundingClientRect()
  const OFFSET_PX = 4

  if (props.iconOnly) {
    dropdownStyle.value = {
      position: 'fixed',
      top: `${Math.round(rect.bottom + OFFSET_PX)}px`,
      left: `${Math.max(0, Math.round(rect.left))}px`,
      width: `${rect.width}px`,
    }
  } else {
    dropdownStyle.value = {
      position: 'fixed',
      top: `${Math.round(rect.bottom + OFFSET_PX)}px`,
      left: `${Math.max(0, Math.round(rect.left))}px`,
      minWidth: `${rect.width}px`,
    }
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

const selectedOpt = computed(() => props.options.find(o => o.value === props.modelValue) ?? props.options[0])
const selectedLabel = computed(() => selectedOpt.value?.label ?? '')
</script>

<template>
  <div ref="root" class="relative inline-block" :class="class">

    <!-- Compact trigger — rendered inside the search bar, bare chevron icon -->
    <button
      v-if="props.iconOnly"
      type="button"
      class="h-8 w-8 p-0 rounded-md bg-transparent border-0 flex items-center justify-center focus:outline-none focus:ring-0 hover:bg-muted/60 transition-colors"
      :aria-label="`Filter by: ${selectedLabel}`"
      :aria-expanded="open"
      aria-haspopup="listbox"
      @click="toggle"
    >
      <svg
        viewBox="0 0 20 20" fill="none" stroke="currentColor"
        class="w-5 h-5 transition-transform duration-150"
        :class="open ? 'rotate-180' : ''"
      >
        <path d="M6 8l4 4 4-4" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>

    <!-- Regular trigger -->
    <button
      v-else
      type="button"
      :class="[
        'h-10 px-3 rounded-lg border border-border/60 bg-muted/40 text-foreground text-sm flex items-center gap-2 hover:bg-muted/60 transition-colors focus:outline-none',
        props.fullWidthTrigger ? 'w-full' : 'min-w-[8rem]',
      ]"
      :aria-label="selectedLabel"
      :aria-expanded="open"
      aria-haspopup="listbox"
      @click="toggle"
    >
      <span class="flex items-center flex-1 truncate min-w-0 leading-none">
        <slot name="trigger-content" />
        {{ selectedLabel }}
      </span>
      <svg
        viewBox="0 0 20 20" fill="none" stroke="currentColor"
        class="w-5 h-5 flex-shrink-0 transition-transform duration-150"
        :class="open ? 'rotate-180' : ''"
      >
        <path d="M6 8l4 4 4-4" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>

    <teleport to="body">
      <Transition
        enter-active-class="transition ease-out duration-100"
        enter-from-class="opacity-0 scale-95 -translate-y-1"
        enter-to-class="opacity-100 scale-100 translate-y-0"
        leave-active-class="transition ease-in duration-75"
        leave-from-class="opacity-100 scale-100 translate-y-0"
        leave-to-class="opacity-0 scale-95 -translate-y-1"
      >
        <ul
          v-if="open"
          role="listbox"
          :aria-label="props.iconOnly ? 'Search filter' : 'Options'"
          :style="dropdownStyle"
          class="z-[99999] py-1 max-h-80 overflow-auto rounded-lg border border-border/60 bg-card text-foreground shadow-xl ring-1 ring-black/5 dark:ring-white/10 origin-top"
        >
          <li
            v-for="opt in options"
            :key="opt.value"
            role="option"
            :aria-selected="opt.value === modelValue"
            @click.stop="select(opt.value)"
            class="flex items-center gap-2.5 px-3 py-2 cursor-pointer text-sm transition-colors hover:bg-muted/60"
            :class="opt.value === modelValue ? 'text-foreground font-medium' : 'text-foreground/80'"
          >
            <img
              v-if="opt.icon"
              :src="opt.icon"
              :alt="opt.label"
              class="w-5 h-5 object-contain flex-shrink-0"
              :class="opt.iconRounded ? 'rounded-full' : ''"
            />
            <span class="flex-1 truncate">{{ opt.label }}</span>
            <svg
              v-if="opt.value === modelValue"
              viewBox="0 0 16 16" fill="none" stroke="currentColor"
              class="w-3.5 h-3.5 flex-shrink-0 text-primary"
              stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"
            >
              <path d="M2.5 8l4 4 7-7" />
            </svg>
          </li>
        </ul>
      </Transition>
    </teleport>
  </div>
</template>
