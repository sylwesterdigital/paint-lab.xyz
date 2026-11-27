# Rantlist integration v2 — Discuss the exact Paint Lab artwork

Paint Lab sender: v0.1.75. Existing Rantlist archive inspected: `websocket-room-chat-v9.6.721-rantlist-deploy-r749` (the live site may be newer; reconcile against your current Rantlist branch before changing it). This is **in addition to**, not a replacement for, `RANTLIST_INTEGRATION.md` (the owner-only bot post bridge).

## User experience and intended semantics

For example, clicking **Discuss art** while viewing
`https://paint-lab.xyz/p/zIourFLU--LiGydL2qFN8hx_DFY?browse=explore&sort=recent&period=all&page=1`
should open a **new tab** in Rantlist, target **#lobby**, and prepare a **draft image message** linked to publication `zIourFLU--LiGydL2qFN8hx_DFY`. The image must be displayed with the same **medium-sized native image bubble** component as an ordinary Rantlist image upload. Show the published artwork title and a clickable canonical Paint Lab link. The visitor can type their own comments, then press **Send**. Nothing is posted on opening the link.

Paint Lab now uses this URL contract (token *only*, no untrusted title or image URL in query):

`https://rantlist.me/?room=lobby&paintLabPublication=zIourFLU--LiGydL2qFN8hx_DFY`

After swiping or using arrows in Paint Lab, the same `paintLabPublication` value updates to the currently displayed item. Paint Lab preserves its own tab and tries to copy the title and canonical public link as a manual fallback. **Until Rantlist adds the consumer, query parameters alone cannot open #lobby or show an image draft.**

## Rantlist work required

1. In the Rantlist browser client, allowlist only this explicit share-intent pair: `room=lobby` and `paintLabPublication=<20-80 URL-safe chars>`. Reject/truncate other values. Do not use the query as an arbitrary URL or HTML input. Keep it pending until normal authentication/registration and room permissions are complete; do not override a user who cancels the intent. Do not select the last-used channel when a valid intent was requested. Prefer the existing room-selection helper (`rantlistNativeOpenRoom`) or its internal underlying `joinRoom`, once the room list is ready.
2. After the person can access #lobby, present an obvious **Discuss this artwork** composer draft with image preview (medium size, consistent with existing native image posts), a safe public title and canonical link. The text editor must remain editable. Display an error if the publication is removed or made private.
3. The Rantlist server must resolve the *token*, not arbitrary browser-supplied addresses: require `https://paint-lab.xyz/p/<token>` for page/publication checks, and fetch the actual image only from `https://paint-lab.xyz/p/<token>/image.png` through a strict HTTPS allowlisted resolver. Verify status 200, `image/png`, valid actual PNG bytes and dimensions, bounded body (e.g. <=7 MiB), response timeouts, redirects disabled and DNS/IP pinning or equivalent SSRF protections. A hidden/deleted publication must be rejected. Never request cloud editable projects, authentication cookies, brush history or any other artist data.
4. Use the **existing normal Rantlist image attachment creation/persistence path** when the user confirms Send, including quota checks, media storage and WebSocket broadcast, so the result is a normal native media message with the standard medium image bubble, title/caption and clickable Paint Lab link. Avoid a text-only link or a web screenshot card. Reuse current media layout/resize controls; full image can open via the native image viewer. The image preview displayed in the draft may be transient, but the sent image must be a durable attachment using Rantlist's media retention and security rules.
5. The message must be attributed to the **authenticated Rantlist user who actually pressed Send**, not the Paint Lab bot. Do not automatically send just because the URL was visited; protect the composer from duplicate clicks, unexpected reloads, and XSS through artwork names. Permit a reply/discussion thread in the usual chat.
6. Once a share intent is consumed or dismissed, remove only `room` and `paintLabPublication` from the URL with `history.replaceState`; ensure Back/Forward or reload cannot create duplicate images/posts. Consider preserving a per-tab pending state through a login redirect, but expire/clear it on logout, cancellation and invalid publication.
7. On smartphones, keep the medium thumbnail within the normal chat width and reuse the chat image preview settings. The actual message image must not be pixelated by copying a 720px Paint Lab gallery thumbnail; fetch/use the original public PNG and let Rantlist create its own media derivatives.
8. Test: direct published link; arrow/swipe changes target; signed-out login; permissions to #lobby; removed/hidden publication; extremely long/malicious title; spoofed DNS/redirects/invalid PNG; click/double-click/cancel; regular Rantlist uploaded media regression; mobile; and no messages posted before Send.

## Distinct integration: Paint Lab owner share button

Paint Lab **Save & share → Share to Rantlist #lobby** uses a separate, already-prepared owner-authenticated, HMAC-signed service-to-service bridge (`POST /api/integrations/paint-lab/publications`). That endpoint has **not** been proven deployed. When implemented, it should post a Paint Lab **bot** image message in #lobby using the *same* native medium-image pipeline and an idempotent publication token. It is not the appropriate route for anonymous visitors viewing public gallery artworks, who must explicitly author their own discussion.

## Cross-service deployment

Rantlist changes should ship through **Rantlist's** release process, independently of Paint Lab. Test the share-intent receiver on the current Rantlist code before turning it live. Do not embed any HMAC secrets in client code, URLs, or releases. The user-visible Paint Lab v0.1.75 fallback remains manual until the receiver is installed and verified.
