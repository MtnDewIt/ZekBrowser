import { onMounted, ref } from 'vue';

type Appearance = 'light' | 'dark';

export function updateTheme(value: Appearance) {
    if (typeof window === 'undefined') {
        return;
    }

    const isDark = value === 'dark';
    
    document.documentElement.classList.toggle('dark', isDark);
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
}

const setCookie = (name: string, value: string, days = 365) => {
    if (typeof document === 'undefined') {
        return;
    }

    const maxAge = days * 24 * 60 * 60;
    
    document.cookie = `${name}=${value};path=/;max-age=${maxAge};SameSite=Lax`;
};

const appearance = ref<Appearance>('light');

export function useAppearance() {
    onMounted(() => {
        // Read initial appearance from server
        if (typeof window !== 'undefined' && (window as any).__INITIAL_APPEARANCE__) {
            appearance.value = (window as any).__INITIAL_APPEARANCE__ as Appearance;
        }
    });

    function updateAppearance(value: Appearance) {
        appearance.value = value;
        setCookie('appearance', value);
        updateTheme(value);
    }

    return {
        appearance,
        updateAppearance,
    };
}
