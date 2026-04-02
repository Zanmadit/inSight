// src/lib/format.ts

/**
 * 1. Fixed Null/Undefined handling for dates
 */
export const formatDt = (date: string | number | Date | null | undefined) => {
    if (!date) return "-";
    try {
        return new Intl.DateTimeFormat("en-US", {
            year: "numeric",
            month: "short",
            day: "2-digit",
        }).format(new Date(date));
    } catch (e) {
        return "-";
    }
};

/**
 * 2. Fixed return types to match your Badge component's strict requirements.
 * Note: Your Badge expects "rejected" instead of "destructive".
 */
type BadgeVariant =
    | "default"
    | "outline"
    | "secondary"
    | "draft"
    | "submitted"
    | "under_review"
    | "accepted"
    | "rejected"
    | null
    | undefined;

export const statusBadgeVariant = (status: string | null | undefined): BadgeVariant => {
    if (!status) return "outline";

    const s = status.toLowerCase();

    // Mapping your logic to the specific types the Badge component allows:
    switch (s) {
        case "draft": return "draft";
        case "submitted": return "submitted";
        case "under_review":
        case "pending": return "under_review";
        case "accepted":
        case "approved":
        case "hired": return "accepted";
        case "rejected":
        case "declined":
        case "destructive": return "rejected"; // We use "rejected" because "destructive" isn't allowed
        default: return "outline";
    }
};