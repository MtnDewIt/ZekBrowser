import { onMounted, ref } from 'vue';

type Appearance = 'light' | 'dark';

const appearance = ref<Appearance>('light');

export function updateTheme(value: Appearance) 
{
    if (typeof globalThis.window === 'undefined') 
    {
        return;
    }

    const isDark = value === 'dark';
    
    document.documentElement.classList.toggle('dark', isDark);
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
}

const setCookie = (name: string, value: string, days = 365) => 
{
    if (typeof document === 'undefined')
    {
        return;
    }

    const maxAge = days * 24 * 60 * 60;
    
    document.cookie = `${name}=${value};path=/;max-age=${maxAge};SameSite=Lax`;
};

export function updateAppearance(value: Appearance) 
{
    appearance.value = value;
    setCookie('appearance', value);
    updateTheme(value);
}

export function useAppearance() 
{
    onMounted(() => 
    {
        if (typeof globalThis.window !== 'undefined' && (globalThis.window as any).__INITIAL_APPEARANCE__) 
        {
            appearance.value = (globalThis.window as any).__INITIAL_APPEARANCE__ as Appearance;
        }
    });

    return {
        appearance,
        updateAppearance,
    };
}
