import { readFile, unlink } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

const MIME_TYPES: Record<string, string> = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".bmp": "image/bmp"
};

/** Keys of the built-in touch-strip layouts whose items are images (pixmaps). */
const PIXMAP_KEYS = new Set(["icon", "icon1", "icon2", "full-canvas", "canvas"]);

function isSvgMarkup(value: string): boolean {
    const start = value.trimStart();
    return start.startsWith("<svg") || start.startsWith("<?xml");
}

function expandHome(file: string): string {
    return file === "~" || file.startsWith("~/") ? path.join(os.homedir(), file.slice(1)) : file;
}

/**
 * Turns what the Spoon sent as an image into something Stream Deck accepts: data: URLs pass
 * through, SVG markup becomes an SVG data: URL, and anything else is read as a file path.
 */
export async function resolveImage(value: string): Promise<string> {
    if (value.startsWith("data:")) return value;
    if (isSvgMarkup(value)) return `data:image/svg+xml;charset=utf8,${value}`;

    const file = expandHome(value);
    if (!path.isAbsolute(file)) throw new Error(`Image path must be absolute: ${value}`);
    const mime = MIME_TYPES[path.extname(file).toLowerCase()];
    if (!mime) throw new Error(`Unsupported image type: ${value}`);
    const data = await readFile(file);
    return `data:${mime};base64,${data.toString("base64")}`;
}

/** Whether a feedback value is an image to resolve: unambiguous image strings anywhere, and file paths in pixmap items. */
function isFeedbackImage(key: string, value: string): boolean {
    return value.startsWith("data:") || isSvgMarkup(value) || (PIXMAP_KEYS.has(key) && value.length > 0);
}

/**
 * Resolves the images in a touch-strip feedback payload, either given directly as an item's value
 * (`icon: "/path.png"`) or as its `value` property (`icon: { value: "/path.png", opacity: 0.5 }`).
 */
export async function resolveFeedback(feedback: Record<string, unknown>): Promise<Record<string, unknown>> {
    const result: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(feedback)) {
        if (typeof value === "string" && isFeedbackImage(key, value)) {
            result[key] = await resolveImage(value);
        } else if (value && typeof value === "object" && !Array.isArray(value)) {
            const item = { ...(value as Record<string, unknown>) };
            if (typeof item.value === "string" && isFeedbackImage(key, item.value)) {
                item.value = await resolveImage(item.value);
            }
            result[key] = item;
        } else {
            result[key] = value;
        }
    }
    return result;
}

/** The prefix of the temporary files the Spoon writes; only files named like this are ever deleted. */
export const TEMP_FILE_PREFIX = "hs2-streamdeck-";

/** Deletes temporary files the Spoon wrote for us, once they've been read. */
export async function deleteFiles(files: string[] | undefined): Promise<void> {
    for (const file of files ?? []) {
        if (!path.basename(file).startsWith(TEMP_FILE_PREFIX)) continue;
        await unlink(expandHome(file)).catch(() => {});
    }
}
