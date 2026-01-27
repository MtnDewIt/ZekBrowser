<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useAppearance } from '@/composables/useAppearance'

const props = defineProps<{ text?: string; stripUnicode?: boolean }>()

// default fallback codes (kept for backward-compatibility if listing API is unavailable)
const FALLBACK_CODES = new Set([0x2611 ,0x2713, 0x2605, 0x2691, 0xE050])
// codes that should be visually inverted when dark theme is active
const INVERT_ON_DARK = new Set([
  0x2605, 0x2639, 0x263B, 0x2691, 0x2713, 0x2717,
  0xE000, 0xE001, 0xE002, 0xE004, 0xE005, 0xE006, 0xE007, 0xE008,
  0xE065, 0xE066, 0xE067, 0xE068, 0xE069, 0xE070, 0xE071, 0xE072,
  0xE073, 0xE074, 0xE075, 0xE076, 0xE077, 0xE078, 0xE079, 0xE080,
  0xE081, 0xE082, 0xE083, 0xE084, 0xE085, 0xE086, 0xE087, 0xE088,
  0xE089, 0xE090, 0xE091, 0xE092, 0xE093, 0xE094, 0xE095, 0xE096,
  0xE097, 0xE098, 0xE099, 0xE10A, 0xE10B, 0xE10C, 0xE10D, 0xE10E,
  0xE10F, 0xE110, 0xE111, 0xE112, 0xE113, 0xE114, 0xE115, 0xE116,
  0xE117, 0xE118, 0xE119, 0xE11A, 0xE11B, 0xE11C, 0xE11D, 0xE11E,
  0xE11F, 0xE120, 0xE121, 0xE122, 0xE123, 0xE124, 0xE125, 0xE126,
  0xE127, 0xE128, 0xE129, 0xE12A, 0xE12B, 0xE12C, 0xE12D, 0xE12E,
  0xE12F, 0xE130, 0xE131
])

// dynamic set of available PNG basenames (e.g., '2611','2713', ...)
const availableCodes = ref<Set<string> | null>(null)

async function loadAvailableCodes() {
  // try sessionStorage cache first
  try {
    const raw = sessionStorage.getItem('zekbrowser.unicodeFiles')
    if (raw) {
      const arr = JSON.parse(raw || '[]') as string[]
      availableCodes.value = new Set(arr.map(s => s.toUpperCase()))
      return
    }
  } catch (e) {
    // ignore and continue
  }

  try {
    const res = await fetch('/api/unicode/list');
    if (res.ok) {
      const arr = await res.json();
      if (Array.isArray(arr)) {
        const upper = arr.map((s: string) => String(s).toUpperCase())
        availableCodes.value = new Set(upper)
        try { sessionStorage.setItem('zekbrowser.unicodeFiles', JSON.stringify(upper)) } catch (e) {}
        return
      }
    }
  } catch (e) {
    // ignore
  }

  // fallback: build set from FALLBACK_CODES
  const fb: string[] = []
  for (const cp of Array.from(FALLBACK_CODES)) fb.push(cp.toString(16).toUpperCase())
  availableCodes.value = new Set(fb)
}

const { appearance } = useAppearance()
const isDark = computed(() => appearance.value === 'dark')

const parts = computed(() => {
  let s = props.text ?? ''
  // Optionally strip non-ASCII (unicode) characters entirely — useful for descriptions
  if (props.stripUnicode) {
    s = Array.from(s).filter(ch => ((ch.codePointAt(0) ?? 0) <= 127)).join('')
  }
  const arr: Array<string | { src: string; alt: string; cp?: number }> = []
  // iterate by codepoint to handle surrogate pairs
  for (const ch of Array.from(s)) {
    const cp = ch.codePointAt(0) ?? 0
    const hex = cp.toString(16).toUpperCase()
    const useImg = availableCodes.value ? availableCodes.value.has(hex) : FALLBACK_CODES.has(cp)
    if (useImg) {
      arr.push({ src: `/assets/unicode/${hex}.png`, alt: `U+${hex}`, cp })
    } else {
      arr.push(ch)
    }
  }
  return arr
})

onMounted(() => { loadAvailableCodes() })
</script>

<template>
  <span class="unicode-text inline-flex items-center">
    <template v-for="(p, idx) in parts" :key="idx">
      <img v-if="typeof p !== 'string'" :src="p.src" :alt="p.alt" :class="['inline-block w-4 h-4 align-middle mx-[2px]', (p.cp && !isDark && ((p.cp && (typeof p.cp === 'number')) ? INVERT_ON_DARK.has(p.cp) : false)) ? 'invert' : '']" />
      <span v-else>{{ p }}</span>
    </template>
  </span>
</template>

<style scoped>
.unicode-text img { display: inline-block }
.unicode-text img.invert { filter: invert(1) hue-rotate(180deg); }
</style>
