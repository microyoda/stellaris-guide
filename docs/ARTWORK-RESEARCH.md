# Game artwork research for a future release

The v1.3 release includes an original Stellaris Guide application icon. It does not yet show Stellaris empire flags or research artwork. The findings below come from the user's locally installed game and the latest autosave; game artwork should be read from that installation rather than bundled with the Guide.

## Empire flags

The player country in `autosave_2279.07.01.sav` identifies its flag with an icon category (`human`), icon file (`flag_human_9.dds`), background category (`backgrounds`), background file (`00_solid.dds`), and colors (`blue`, `black`, `null`). In the local Steam installation, the icon is at `Stellaris/flags/human/flag_human_9.dds` and the background is at `Stellaris/flags/backgrounds/00_solid.dds`. The game also has `small` and `map` variants of the icon.

**Exact file layout on this Windows installation:**

| Save descriptor or purpose | Installed game file |
| --- | --- |
| `icon={ category="human" file="flag_human_9.dds" }` | `flags/human/flag_human_9.dds` (emblem) |
| `background={ category="backgrounds" file="00_solid.dds" }` | `flags/backgrounds/00_solid.dds` (pattern) |
| `colors={ "blue" "black" "null" ... }` | `flags/colors.txt` (named color swatches) |

The folders are named after icon **categories** such as `human`, `blocky`, and `ornate`; there is no generic `flags/icon/` folder. The background folder is `backgrounds` (plural). To find these without typing the installation path, open Steam Library → Stellaris → Manage → **Browse local files**, then open `flags`.

In the installed `colors.txt`, `blue` has flag RGB `(46, 63, 152)` and `black` has flag RGB `(27, 27, 27)`. The file explains that the background texture's red, green, and blue channels weight color slots 0, 1, and 2; the `map` and `ship` RGB values in the same swatch serve different uses. The sample `00_solid.dds` is a red-channel background, so it uses the first saved flag color. The sample emblem is an RGBA texture. Exact emblem scaling, masking, and color composition still need visual comparison with the in-game flag before we render it in the Guide.

`colors.txt` also contains six-name `randomizable_combo` entries. Its comments identify slots 0–2 as the background's primary, secondary, and tertiary colors; slots 3–5 are for ship tint and map border/fill overrides. These entries are color combinations for generating flags, not image coordinates.

A future flag renderer should read the save's flag descriptor, find the corresponding files in the user's installed game (including any active mod assets), decode the DDS images, and combine the icon, background, and colors. Showing the raw icon file alone would not reproduce the in-game flag. The renderer needs a fallback badge when an asset or color cannot be resolved.

## Research artwork

The autosave's `tech_status` lists technology IDs, such as `tech_solar_panel_network`. The local game has `Stellaris/gfx/interface/icons/technologies/tech_solar_panel_network.dds`; its definition appears in `Stellaris/common/technology/00_eng_tech.txt`. A future research panel can resolve the technology ID to its definition and icon, with a placeholder when a technology or mod uses a different path.

## Recommended implementation

1. Discover the local Stellaris installation when the player first enables game artwork. Let the player choose its folder if discovery fails.
2. Resolve save asset names inside the installed game and enabled mods. Never accept an arbitrary absolute path from a save as a file to serve.
3. Convert the needed DDS assets to small cached PNGs on the player's PC, and serve those only to the local dashboard. Rebuild the cache if the game or mod files change.
4. Compose flags using the game's color and masking rules; compare the result against an in-game screenshot before presenting it as accurate.
5. Keep the original Guide icon and generic placeholders for missing or incompatible artwork. Do not package Paradox game assets in the downloadable release.

This research establishes where the sample assets are stored. It does not yet validate DDS conversion, every flag style, mod overrides, or the exact in-game color composition.

## Community visual reference: StellarisAssets

[StellarisAssets](https://tuttu.github.io/StellarisAssets/) is a visual browser for game images. Its [source repository](https://github.com/Tuttu/StellarisAssets) organizes galleries for buildings, civics, deposits, districts, edicts, icons, megastructures, ship components, and traits. The site says clicking an image copies its filename. This could help us identify the right **planet building**, **district**, **deposit**, and **ship component** artwork while designing recommendations.

For example, the local game installation contains `gfx/interface/icons/districts/district_mining.dds` and several display variants under `districts/grid_box/`. A gallery filename can point us to the right asset family, but the renderer must choose the appropriate local file and size for its UI.

The gallery does not establish a 4.5 Cygnus mapping for every asset. It is a lookup aid, not the data source for the release. Resolve IDs and image files from the player's installed 4.5 game, check examples against the in-game UI, and keep a placeholder for anything missing or changed. Continue to use the local game files for empire flags and research icons; those are not demonstrated by the gallery categories reviewed here. Do not copy the gallery's game images into the portable download.
