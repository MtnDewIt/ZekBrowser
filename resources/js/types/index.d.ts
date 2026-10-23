export type AppPageProps<T extends Record<string, unknown> = Record<string, unknown>> = T & {
    name: string;
};
