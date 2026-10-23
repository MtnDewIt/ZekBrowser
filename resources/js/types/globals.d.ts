import type { AppPageProps } from '@/types/index';
import type { createHeadManager, PageProps as InertiaPageProps, Page, Router } from '@inertiajs/core';

declare module 'vite/client' {
    interface ImportMetaEnv {
        readonly VITE_APP_NAME: string;
        [key: string]: string | boolean | undefined;
    }

    interface ImportMeta {
        readonly env: ImportMetaEnv;
        readonly glob: <T>(pattern: string) => Record<string, () => Promise<T>>;
    }
}

declare module '@inertiajs/core' {
    interface PageProps extends InertiaPageProps, AppPageProps {}
}

declare module '@vue/runtime-core' {
    interface ComponentCustomProperties {
        $inertia: Router;
        $page: Page;
        $headManager: ReturnType<typeof createHeadManager>;
    }
}

declare global {
    interface Window {
        __INITIAL_APPEARANCE__?: 'light' | 'dark';
    }
}
