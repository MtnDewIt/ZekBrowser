import { ref } from 'vue';

/**
 * Open/close state for a ClickPopover whose trigger is also the thing that closes it.
 * After closing, re-opening is ignored for a short window so the same click does not
 * close and immediately reopen the popover.
 */
export function usePopoverToggle(onOpen?: () => void) {
    const open = ref(false);
    let ignoreOpenUntil = 0;

    function toggle() {
        const now = Date.now();

        if (open.value) {
            open.value = false;
            ignoreOpenUntil = now + 300;
            return;
        }

        if (now < ignoreOpenUntil) {
            return;
        }

        open.value = true;
        onOpen?.();
    }

    return { open, toggle };
}
