import type { Updater } from '@tanstack/vue-table'
import type { Ref } from 'vue'
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) 
{
    return twMerge(clsx(inputs));
}

export function valueUpdater<T extends Updater<any>>(updaterOrValue: T, ref: Ref) 
{
    ref.value = typeof updaterOrValue === 'function'
        ? updaterOrValue(ref.value)
        : updaterOrValue
}

export function capitalize(value) 
{
    return String(value).charAt(0).toUpperCase() + String(value).slice(1);
}
