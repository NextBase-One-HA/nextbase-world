# GLB Finish Phase TODO

Status: frontend room UI exists; Cursor fixed onboarding and room entrypoints in commit 39a98ff.

Next safe implementation batch:

1. glb-room.html
- In chat mode, add visible expiry line: This room will disappear in 30 days.
- Add local-only message input in chat mode.
- Add Share Room button in chat mode using Web Share API or clipboard fallback.
- Do not add network calls yet.

2. index.2.99.html
- Add a non-blocking first-run hint near the result tools: Tap Flip and show them.
- Do not touch core app logic.

3. index.14.99.html
- Ensure Create Room link remains visible near the top.
- Do not add a sales block inside the Travel app body.

4. Later
- Room API waits until UI PASS.

PASS checks:
- index.html has only Try free and Core CTA.
- Core page has Join Room link.
- Travel page has Create Room link.
- glb-room.html supports create, join, and chat mock.
- No new network calls in glb-room.html.
