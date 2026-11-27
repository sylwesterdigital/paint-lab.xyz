# Rantlist — Paint Lab image-discussion draft receiver (v3, 2026-11-27)

## Source and deployment boundary

Paint Lab source reviewed: release v0.1.75 (v0.1.76 updates its publishing UI). The Rantlist ZIP supplied previously is v9.6.721/r749. It does not include a verified `paintLabPublication` query handler. The latest deployed Rantlist release was not supplied, so no claim is made about its current code. Paint Lab and Rantlist run on **separate servers**. The public PNG was verified by the user as HTTP 200 from the Rantlist host (1600×1600 PNG, 4,126,006 bytes).

## Contract shared by Paint Lab and Rantlist

After Paint Lab publishes a public image, both Save & share and Share artwork now link to:

`https://rantlist.me/?room=lobby&paintLabPublication=<public-token>`

The public viewer Discuss art link uses exactly the same query names. The token identifies a public image, not an editable private project. Example:

`https://rantlist.me/?room=lobby&paintLabPublication=ylXJE8AVgDG25bf6ubJKZxL78hI`

The browser opens Rantlist in a new tab. It must **not auto-send a message**. If Rantlist ignores the query, the link will just display the previously visited channel. The old Rantlist r749 client searched the URL for some invite/media parameters, but no `paintLabPublication` support was confirmed in that source.

## Required changes in the current Rantlist development thread

1. At startup/after authentication, parse `room=lobby` and `paintLabPublication`. Validate the ID strictly against `[A-Za-z0-9_-]{20,80}`. Preserve pending intent across login without exposing it in a public message or silently sending. Never honor an arbitrary room or URL from the query.
2. Navigate explicitly to the existing **#lobby** channel after authentication, overriding the last-visited channel for this one navigation; respect normal room join and posting permissions. Never create a new channel from the query.
3. On the Rantlist server, resolve the publication using only the fixed Paint Lab origin and public route: `https://paint-lab.xyz/p/<token>/image.png` (or a smaller preview `https://paint-lab.xyz/p/<token>/preview.webp`). Do not call owner-only `/api/publications/.../image.png`. Disallow redirects or cross-host follow-ups, impose a byte/time/dimension cap, verify content signature and actual image MIME, and prevent SSRF.
4. The supplied image is **4,126,006 bytes** (3.94 MiB), so a 4,000,000-byte cap on original PNGs would reject it. If that exceeds Rantlist's native upload cap, use Paint Lab's bounded WebP preview route or safely generate an accepted preview server-side. Keep a canonical link to the unmodified original for full-resolution opening/download. Do not silently broaden all media upload limits.
5. Populate the existing **medium-sized native image bubble composer** as a draft with the safe thumbnail/image and a public artwork link/title. Do not simply create a plain text URL, and do not bypass Rantlist's validated attachment/chat pipeline. Leave the visitor free to add text, edit and confirm Send or Cancel.
6. Neither opening the link nor creating the draft must automatically post to #lobby. The logged-in user explicitly sends the message through the existing authenticated channel pipeline. Preserve ownership and rate limits.
7. Show distinct errors for 404/410 unpublished images, upstream connectivity/timeout, byte limit, failed thumbnail decode, storage full, and missing permissions. A 200/valid image must not be reported as “This artwork is no longer public or is unavailable” without a more specific validation check.
8. Confirm with browser tests: active publication from gallery arrows/back, publication from both Paint Lab save dialogs, login redirect preserving intent, #lobby not last-visited channel, correct medium image draft, cancel without posting, user-confirmed send, 4,126,006-byte PNG, restricted/revoked publication, disk pressure, and no cross-site request forgery.

## Do not conflate the two integrations

The optional signed server-to-server Paint Lab bot endpoint `POST /api/publications/<token>/share/rantlist` is **not** the user-confirmed Discuss art link. It remains in Paint Lab, but the Share to Rantlist button in the v0.1.76 UI now always uses the contextual **draft** link, not an automated bot post. The source-sensitive Rantlist receiver must be implemented and tested in the current Rantlist repository before declaring this flow functional.
