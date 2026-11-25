import streamDeck from "@elgato/streamdeck";
import net from "node:net";
import os from "node:os";
import path from "node:path";

import { PROTOCOL_VERSION, SOCKET_PATH, type PluginMessage, type SpoonMessage } from "./protocol";

/** How often to try connecting while the Spoon isn't listening. */
const RETRY_INTERVAL_MS = 1000;
/** The longest line accepted from the Spoon, so a runaway sender can't exhaust memory. */
const MAX_LINE_BYTES = 32 * 1024 * 1024;

export type BridgeStatus =
    | { state: "waiting" }
    | { state: "connected"; spoon: string }
    | { state: "mismatch"; spoon: string; spoonProtocol: number; update: "plugin" | "spoon" };

type Handlers = {
    /** The Spoon said hello with a matching protocol version. */
    onConnect(): void;
    /** A message other than hello, from a Spoon with a matching protocol version. */
    onMessage(message: SpoonMessage): void;
    /** The connection was lost (or a mismatched one was given up on). */
    onDisconnect(): void;
    onStatus(status: BridgeStatus): void;
};

/**
 * Keeps a connection to the Spoon's Unix domain socket, retrying about once a second whenever
 * there isn't one, and frames messages as one JSON object per line.
 */
export class Bridge {
    readonly socketPath = path.join(os.homedir(), SOCKET_PATH);

    #socket: net.Socket | null = null;
    #ready = false;
    #retryTimer: NodeJS.Timeout | null = null;
    #status: BridgeStatus = { state: "waiting" };

    constructor(
        private readonly handlers: Handlers,
        private readonly hello: () => PluginMessage
    ) {}

    get status(): BridgeStatus {
        return this.#status;
    }

    /** True once the Spoon has said hello with a matching protocol version. */
    get isReady(): boolean {
        return this.#ready;
    }

    start(): void {
        this.#connect();
    }

    send(message: PluginMessage): void {
        if (!this.#socket || (!this.#ready && message.type !== "hello")) return;
        this.#socket.write(JSON.stringify(message) + "\n");
    }

    #setStatus(status: BridgeStatus): void {
        this.#status = status;
        this.handlers.onStatus(status);
    }

    #scheduleRetry(): void {
        if (this.#retryTimer) return;
        this.#retryTimer = setTimeout(() => {
            this.#retryTimer = null;
            this.#connect();
        }, RETRY_INTERVAL_MS);
    }

    #connect(): void {
        if (this.#socket) return;
        const socket = net.createConnection(this.socketPath);
        this.#socket = socket;
        let buffer = "";

        socket.setEncoding("utf8");
        socket.on("connect", () => {
            streamDeck.logger.info(`Connected to ${this.socketPath}`);
            this.send(this.hello());
        });
        socket.on("data", (chunk: string) => {
            buffer += chunk;
            let newline: number;
            while ((newline = buffer.indexOf("\n")) >= 0) {
                const line = buffer.slice(0, newline);
                buffer = buffer.slice(newline + 1);
                if (line.trim()) this.#receive(socket, line);
            }
            if (buffer.length > MAX_LINE_BYTES) {
                streamDeck.logger.error("Line from Hammerspoon too long, disconnecting");
                socket.destroy();
            }
        });
        socket.on("error", (err: NodeJS.ErrnoException) => {
            // ENOENT and ECONNREFUSED just mean the Spoon isn't listening (yet)
            if (err.code !== "ENOENT" && err.code !== "ECONNREFUSED") {
                streamDeck.logger.warn(`Socket error: ${err.message}`);
            }
        });
        socket.on("close", () => {
            if (this.#socket !== socket) return;
            const wasReady = this.#ready;
            this.#socket = null;
            this.#ready = false;
            if (wasReady) {
                streamDeck.logger.info("Disconnected from Hammerspoon");
                this.handlers.onDisconnect();
            }
            if (this.#status.state !== "waiting") this.#setStatus({ state: "waiting" });
            this.#scheduleRetry();
        });
    }

    #receive(socket: net.Socket, line: string): void {
        let message: SpoonMessage;
        try {
            message = JSON.parse(line);
        } catch {
            streamDeck.logger.warn(`Ignoring malformed line from Hammerspoon: ${line.slice(0, 200)}`);
            return;
        }

        if (message.type === "hello") {
            if (message.protocol !== PROTOCOL_VERSION) {
                const update = message.protocol > PROTOCOL_VERSION ? "plugin" : "spoon";
                streamDeck.logger.warn(
                    `Protocol mismatch: plugin speaks ${PROTOCOL_VERSION}, Spoon ${message.spoon} speaks ${message.protocol}; update the ${update}`
                );
                this.#setStatus({ state: "mismatch", spoon: message.spoon, spoonProtocol: message.protocol, update });
                // Both sides stay connected but idle, rather than reconnecting every second just to
                // report the same mismatch. Reloading the Spoon (after updating it) closes this
                // connection, and the next one starts afresh.
                return;
            }
            this.#ready = true;
            this.#setStatus({ state: "connected", spoon: message.spoon });
            this.handlers.onConnect();
            return;
        }

        if (!this.#ready || this.#socket !== socket) return;
        try {
            this.handlers.onMessage(message);
        } catch (err) {
            streamDeck.logger.error(`Error handling ${message.type}: ${err}`);
        }
    }
}
