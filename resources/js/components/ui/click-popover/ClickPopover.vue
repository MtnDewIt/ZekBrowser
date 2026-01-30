<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue';

const props = withDefaults(defineProps<{ modelValue?: boolean; placement?: 'bottom' | 'top' | 'left' | 'right' }>(), { modelValue: false, placement: 'bottom' });
const emit = defineEmits<{ (e: 'update:modelValue', value: boolean): void }>();

const open = computed({
  get: () => !!props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v),
});

const triggerRef = ref<HTMLElement | null>(null);
const contentRef = ref<HTMLElement | null>(null);
const style = ref<Record<string, string>>({ position: 'absolute', top: '0px', left: '0px', zIndex: '1000' });

function updatePosition() {
  const trigger = triggerRef.value;
  const content = contentRef.value;
  if (!trigger || !content) return;

  const rect = trigger.getBoundingClientRect();
  const cw = content.offsetWidth;
  const ch = content.offsetHeight;
  let top = 0;
  let left = 0;

  switch (props.placement) {
    case 'top':
      top = rect.top - ch - 8;
      left = rect.left + rect.width / 2 - cw / 2;
      break;
    case 'left':
      top = rect.top + rect.height / 2 - ch / 2;
      left = rect.left - cw - 8;
      break;
    case 'right':
      top = rect.top + rect.height / 2 - ch / 2;
      left = rect.right + 8;
      break;
    case 'bottom':
    default:
      top = rect.bottom + 8;
      left = rect.left + rect.width / 2 - cw / 2;
      break;
  }

  // Clamp to viewport
  const docW = document.documentElement.clientWidth;
  const docH = document.documentElement.clientHeight;

  left = Math.max(8, Math.min(left, docW - cw - 8));
  top = Math.max(8, Math.min(top, docH - ch - 8));

  style.value.top = `${top + window.scrollY}px`;
  style.value.left = `${left + window.scrollX}px`;
}

function onDocClick(e: MouseEvent) {
  const t = e.target as Node;
  if (!open.value) return;
  if (triggerRef.value && (triggerRef.value === t || triggerRef.value.contains(t))) return;
  if (contentRef.value && (contentRef.value === t || contentRef.value.contains(t))) return;
  open.value = false;
}

let rafId: number | null = null;
function onWindowChange() {
  if (rafId) cancelAnimationFrame(rafId);
  rafId = requestAnimationFrame(() => updatePosition());
}

watch(open, (v) => {
  if (v) {
    nextTick(() => {
      updatePosition();
      document.addEventListener('mousedown', onDocClick);
      window.addEventListener('resize', onWindowChange);
    });
  } else {
    document.removeEventListener('mousedown', onDocClick);
    window.removeEventListener('resize', onWindowChange);
  }
});

onMounted(() => {
  // nothing
});

onUnmounted(() => {
  document.removeEventListener('mousedown', onDocClick);
  window.removeEventListener('resize', onWindowChange);
  if (rafId) cancelAnimationFrame(rafId);
});
</script>

<template>
  <div ref="triggerRef">
    <slot name="trigger" />
  </div>

  <teleport to="body">
    <div v-if="open" ref="contentRef" :style="style" class="click-popover-content">
      <slot />
    </div>
  </teleport>
</template>

<style scoped>
.click-popover-content {
  background: var(--popover, var(--pop-over-bg, white));
  color: var(--popover-foreground);
  border-radius: 6px;
  overflow: hidden;
  -webkit-background-clip: padding-box;
  background-clip: padding-box;
  border: 1px solid var(--border);
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}
</style>
