<script setup lang="ts">
defineOptions({ inheritAttrs: false });
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue';

const props = withDefaults(defineProps<{ modelValue?: boolean; placement?: 'bottom' | 'top' | 'left' | 'right' }>(), { modelValue: false, placement: 'bottom' });
const emit = defineEmits<{ (e: 'update:modelValue', value: boolean): void }>();

const open = computed({
  get: () => !!props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v),
});

const triggerRef = ref<HTMLElement | null>(null);
const contentRef = ref<HTMLElement | null>(null);
const style = ref<Record<string, string>>({ position: 'absolute', top: '0px', left: '0px', zIndex: '1000', visibility: 'hidden' });

let rafId: number | null = null;
let positionTries = 0;
const MAX_POSITION_TRIES = 10;
let resizeObserver: ResizeObserver | null = null;

function updatePosition() {
  const trigger = triggerRef.value;
  const content = contentRef.value;
  if (!trigger || !content) return;

  const rect = trigger.getBoundingClientRect();
  const cw = content.offsetWidth;
  const ch = content.offsetHeight;
  let top = 0;
  let left = 0;

  // If we don't have usable measurements yet, retry a few times.
  if ((cw === 0 || ch === 0 || rect.width === 0 || rect.height === 0)) {
    // If the document is hidden, wait for visibilitychange instead of busy-looping.
    if (document.visibilityState !== 'visible') {
      // hide until repositioned when visible
      style.value.visibility = 'hidden';
      return;
    }

    if (positionTries < MAX_POSITION_TRIES) {
      positionTries++;
      if (rafId) cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(() => updatePosition());
      return;
    }
    // fallthrough after retries
  }

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
  style.value.visibility = 'visible';
  positionTries = 0;
}

function onDocClick(e: MouseEvent) {
  const t = e.target as Node;
  if (!open.value) return;
  if (triggerRef.value && (triggerRef.value === t || triggerRef.value.contains(t))) return;
  if (contentRef.value && (contentRef.value === t || contentRef.value.contains(t))) return;
  open.value = false;
}

function onWindowChange() {
  if (rafId) cancelAnimationFrame(rafId);
  rafId = requestAnimationFrame(() => updatePosition());
}

function onVisibilityChange() {
  if (document.visibilityState === 'visible') {
    if (rafId) cancelAnimationFrame(rafId);
    rafId = requestAnimationFrame(() => updatePosition());
  }
}

watch(open, (v) => {
  if (v) {
    nextTick(() => {
      // hide until we can compute correct position
      style.value.visibility = 'hidden';
      positionTries = 0;
      updatePosition();
      document.addEventListener('mousedown', onDocClick);
      window.addEventListener('resize', onWindowChange);
      window.addEventListener('scroll', onWindowChange, true);
      window.addEventListener('focus', onWindowChange);
      document.addEventListener('visibilitychange', onVisibilityChange);

      // Observe content size changes to reposition if inner content changes
      try {
        if (contentRef.value && typeof ResizeObserver !== 'undefined') {
          resizeObserver = new ResizeObserver(() => updatePosition());
          resizeObserver.observe(contentRef.value);
        }
      } catch (e) {
        // ignore
      }
    });
  } else {
    document.removeEventListener('mousedown', onDocClick);
    window.removeEventListener('resize', onWindowChange);
    window.removeEventListener('scroll', onWindowChange, true);
    window.removeEventListener('focus', onWindowChange);
    document.removeEventListener('visibilitychange', onVisibilityChange);
    if (resizeObserver) {
      try { resizeObserver.disconnect(); } catch (e) {}
      resizeObserver = null;
    }
    // keep hidden when closed
    style.value.visibility = 'hidden';
  }
});

onMounted(() => {
  // nothing
});

onUnmounted(() => {
  document.removeEventListener('mousedown', onDocClick);
  window.removeEventListener('resize', onWindowChange);
  window.removeEventListener('scroll', onWindowChange, true);
  window.removeEventListener('focus', onWindowChange);
  document.removeEventListener('visibilitychange', onVisibilityChange);
  if (rafId) cancelAnimationFrame(rafId);
  if (resizeObserver) {
    try { resizeObserver.disconnect(); } catch (e) {}
    resizeObserver = null;
  }
});
</script>

<template>
  <div ref="triggerRef" v-bind="$attrs">
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
