export const TEAM_COLORS = ['#9b3332', '#325992', '#1F3602', '#BC4D00', '#1D1052', '#A77708', '#1C0D02', '#FF4D8A'];

export const TEAM_NAMES = ['Red', 'Blue', 'Green', 'Orange', 'Purple', 'Gold', 'Brown', 'Pink'];

export function teamColor(team: number | null | undefined, fallback = 'transparent'): string {
    if (team !== null && team !== undefined && team >= 0 && team < TEAM_COLORS.length) {
        return TEAM_COLORS[team];
    }

    return fallback;
}

export function toTeamIndex(value: unknown): number | null {
    if (value === null || value === undefined) {
        return null;
    }

    const n = Number(value);

    return Number.isFinite(n) ? n : null;
}
