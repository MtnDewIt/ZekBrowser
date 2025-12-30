export const serviceRecordCache = new Map<string, number | null>();

export async function getIdForUid(uid: string, eldewritoVersion?: string): Promise<number | null> {
    if (!uid) return null;
    if (serviceRecordCache.has(uid)) return serviceRecordCache.get(uid) ?? null;

    try {
        const res = await fetch('/api/service-record/lookup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ uid, eldewrito_version: eldewritoVersion ?? '' }),
        });

        if (!res.ok) {
            serviceRecordCache.set(uid, null);
            return null;
        }

        const data = await res.json();
        const id = (data && (data.id === null || data.id === undefined)) ? null : Number(data.id ?? null);
        serviceRecordCache.set(uid, id);
        return id;
    }
    catch (e) {
        serviceRecordCache.set(uid, null);
        return null;
    }
}

export function findUidFromPlayer(p: any): string | null {
    if (!p || typeof p !== 'object') return null;
    const candidates = ['uid', 'xuid', 'playerUid', 'player_uid', 'accountId', 'id', 'xnkid'];
    for (const k of candidates) {
        if (p[k]) return String(p[k]);
    }
    return null;
}
