<script setup lang="ts">
import { cn } from '@/lib/utils';
import { useVModel } from '@vueuse/core';

const props = defineProps<{
    defaultValue?: string | number;
    modelValue?: string | number;
    class?: string;
    placeholder?: string;
    type?: string;
}>();

const emits = defineEmits<{
    (e: 'update:modelValue', payload: string | number): void;
}>();

const modelValue = useVModel(props, 'modelValue', emits, {
    passive: true,
    defaultValue: props.defaultValue,
});
</script>

<template>
    <input
        v-model="modelValue"
        :type="type || 'text'"
        :class="
            cn(
                'flex h-10 w-full rounded-lg border border-border/60 bg-background px-3 py-2 text-sm ring-offset-background transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus:border-border focus:ring-1 focus:ring-ring/20 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50',
                props.class,
            )
        "
        :placeholder="placeholder"
    />
</template>
