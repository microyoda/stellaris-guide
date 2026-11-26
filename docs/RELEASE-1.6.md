# Stellaris Guide 1.6.0

**Supported game reference:** Stellaris 4.5.2 Cygnus. Installed checksum 9776 and base-game technology rules were checked on this Windows installation. Mods and DLC can change what is available; the Guide marks uncertain technology routes as **Limited** and asks you to verify them in Stellaris.

## What changed

- Main ranks the next moves using save facts, shows resource runway, and lets you pin a campaign goal while serious resource warnings remain visible.
- Planet recommendations inspect jobs and controls before recommending another building. The Guide avoids an urgent market warning when a negative monthly balance has a long stockpile runway.
- Research trends, policy labels and owned ship components use saved data and matching installed 4.5.2 definitions where available. They do not promise a research draw or a ship's complete build access.
- Tech Tree offers a focused route in a separate Edge window. It distinguishes completed, current and unmet steps, choices, tier gates, grants and rules it could not verify. Close affects only that route window.
- Optional AI chat receives a small packet from the selected save. It includes the game release, player empire, DLC and mod labels, relevant records and requested technology route. Numeric answers are checked against cited record fields. If a model fails, text questions fall back to the built-in guide.
- Spoiler consent applies only to the exact selected save and resets at the next autosave. The Settings warning explains this behavior. Screenshot analysis requires a verified image-capable model and labels date mismatches.

## Player safety and limits

The dashboard reads saves without changing them. Normal mode does not send hidden rival strength or stockpiles to optional AI. Screenshots are sent only when the player presses Send; OpenRouter is online, while Ollama and LM Studio are local. Image-derived advice can still be wrong or influenced by text in the image, so check actions in game. Exact costs, active mod rules, combat matchups and undiscovered information cannot always be verified.

The built-in guide works offline with no AI account. The separate technology route needs Microsoft Edge; the rest of the Guide can open in another default browser. This package does not install Stellaris or Edge.

## Verification

The source suite and optional-provider fixture tests cover successful and failing save, chat, spoiler and route paths. An interim Windows package opened the focused route in Edge against a 4.5.2 save and a synthetic campaign, and closed only its own window. Final v1.6 package and clean-path smoke verification are pending.

The package includes installed third-party license texts in `licenses/`. Research and architectural decisions are kept in the source repository documentation.
