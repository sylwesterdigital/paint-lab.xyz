# Paint Lab → Rantlist #lobby: integration contract (v1)

**Rantlist base reviewed:** `websocket-room-chat-v9.6.721-rantlist-deploy-r749`.
**Paint Lab sender introduced:** v0.1.70. The bundled Rantlist revision does **not** implement this external service endpoint. Do not enable the Paint Lab bridge until the Rantlist work is deployed and tested.

## Existing Rantlist implementation (source confirmed)

- Its primary HTTP/WebSocket service is `server.js`, not Express. Authenticated room chat uses the WebSocket `message.room` action and `sendRoomText`, which enforces room membership/writability, rate limits, message validation and durable persistence.
- It supports a native/PWA inbound share queue that is user/session specific, but no verified browser cross-origin deep-link endpoint for submitting a post to a named channel. The `window.rantlistNativeOpenRoom` helper is internal to an authenticated loaded client, not an external API.
- Rantlist has `integrations/paint-lab/` for an *older embedded client (Paint Lab v0.1.32)* and near-real-time collaborative previews. Do not overwrite that embedded app or mistake it for the independent `paint-lab.xyz` public publication API.

## Implement on Rantlist

1. Add an **HTTPS, server-to-server only** endpoint: `POST /api/integrations/paint-lab/publications` in the Rantlist HTTP router. It must **not** accept browser cookies or cross-origin posting as authentication, and must not become a generic proxy for arbitrary URLs or arbitrary channels.
2. Use a dedicated secret from the protected Rantlist environment, e.g. `RANTLIST_PAINT_LAB_BRIDGE_SECRET` (minimum 32 randomly generated characters), also configured on Paint Lab as `PAINT_LAB_RANTLIST_BRIDGE_SECRET`. Never put the secret in HTML, client JS, the repository, or the ZIP archive. Rotate it independently of chat sessions and other integrations.
3. Read the **raw request body** with an upper bound of 2 KB. Verify `X-Paint-Lab-Timestamp` as integer Unix seconds within ±300 s of Rantlist server time. Verify `X-Paint-Lab-Signature` as `sha256=` plus the **hex HMAC-SHA256** of `ASCII(timestamp) + "\n" + raw_UTF8_body` using the shared secret, with `crypto.timingSafeEqual` on same-length buffers. Reject invalid/missing headers, invalid JSON, replayed/malformed timestamps and oversized bodies before posting.
4. The accepted payload is `{ "version":1, "destination":"lobby", "publication_id":"<token>", "title":"<public artwork title>", "url":"https://paint-lab.xyz/p/<same token>" }`. Validate the token against `[A-Za-z0-9_-]{20,80}`, the exact URL origin `https://paint-lab.xyz`, pathname `/p/<same token>` without query/fragment, and string title length ≤90. Reject every destination except `lobby`; reject unknown keys if convenient. **Never** accept a remote HTTP URL from arbitrary input for preview-fetching.
5. Optionally verify that the published artwork link is publicly accessible and visible on Paint Lab before posting; use fixed HTTPS host/allowed path, no redirects to internal networks, a short timeout and a strict byte cap. Do not require or fetch private Paint Lab user data. Paint Lab already verifies the calling artist's own session, CSRF, publication ownership, and `is_visible=1` before making the bridge request.
6. Represent the post as **Paint Lab bot/service identity**, not the human's Rantlist identity. Grant that identity permission to **post only in #lobby**. Route the message through the usual Rantlist persisted/broadcast message pipeline (with `sendRoomText`-equivalent validation, history, timestamps, message IDs, clients), not direct file/SQL insertion bypassing normal chat semantics. Use something like `New Paint Lab artwork: <title>\nhttps://paint-lab.xyz/p/<token>`; sanitize the title before display. Render with the existing secure link-preview pipeline if available.
7. Make `publication_id` **idempotent** in durable storage with a unique key, returning the previously posted ID for retries, including when concurrent calls arrive. Use `X-Paint-Lab-Idempotency-Key` (which Paint Lab sets to the token) and cross-check it equals payload `publication_id`. Add per-service IP, request-rate and per-hour post limits; no automatic sharing from Rantlist.
8. On a **confirmed durable message** return HTTP 200 or 201: `{"ok":true,"channel":"lobby","message_id":"<stable message ID>"}`. Return a non-2xx JSON error otherwise. If Rantlist fails or cannot confirm persistence, Paint Lab must not announce success. Test restart/retry safety and bot permissions, including hidden/revoked publications, malformed HMAC, stale timestamp, wrong channel, forged URL and duplication.

## Paint Lab v0.1.70 sender behaviour

- A painter first publishes a PNG explicitly. The public link area then offers **Share to Rantlist #lobby**. This never runs automatically during ordinary Save or Publish.
- If the bridge is not configured, it instead opens `https://rantlist.me/` and tries to copy the *public URL* to clipboard. The painter must manually join `#lobby` and paste/send. The UI explicitly says no post occurred.
- If the bridge is configured, the signed call is made **from Paint Lab Flask**, after Paint Lab session, CSRF, ownership, visibility and rate-limit checks. No browser key or private canvas content is transmitted.
- Paint Lab stores the confirmed Rantlist message ID in SQLite, linked to the publication. Repeated shares of the same publication return the stored result rather than making another post. Rantlist must also independently deduplicate to cover concurrent calls, retries and crashes between remote persistence and local commit.
- `GET /api/integrations/rantlist` indicates `{enabled:true|false,destination:"lobby"}` (capability only). `POST /api/publications/<token>/share/rantlist` is Paint Lab's owner-authenticated endpoint, not a public inbound Rantlist posting endpoint.
- Paint Lab's outbound destination is hard-pinned to `https://rantlist.me/api/integrations/paint-lab/publications` and refuses redirects. Optional `PAINT_LAB_RANTLIST_BRIDGE_URL` may only specify that exact secure host/path. Set the secret using Ubuntu service environment configuration (not inside code, ZIP or GitHub) and restart the Paint Lab service after Rantlist has deployed.

## Deployment sequence and acceptance

1. Implement the receiver and Rantlist bot permissions with tests in the Rantlist development thread, using the existing Rantlist guarded deployment pipeline. No changes to its embedded Paint Lab v0.1.32 are needed for public gallery sharing.
2. Deploy and verify Rantlist's endpoint with test credentials and a real public Paint Lab publication. Confirm exactly one persisted #lobby message, correct bot attribution, and proper link preview.
3. Configure identical bridge secret in both services, verify the Paint Lab capability endpoint responds `enabled:true`, then click Share to #lobby for one published test artwork. Confirm end-to-end receipt and idempotent repeat.
4. Verify rejected invisible/other-owner artwork, unauthenticated/CSRF attempts, 503 when unconfigured, Rantlist offline/timeout paths, and no data from private projects or brush-stroke histories. Do not mark the integration live without these checks.
5. Future improvement (separate decision): offer an author-authenticated Rantlist share-intent/deep-link that opens `#lobby` with a draft for the author to confirm; this should not be confused with the server-bot workflow described here.
