# v1.5 planning record and remaining candidates

This document records the requests and review that led to v1.5.0. For what was actually shipped, read [v1.5 release notes](RELEASE-1.5.md). The wording below is historical planning language, not a statement that every item was delivered.

## Remaining candidates after v1.5

- Validate naval capacity, subject and overlord ties, claims, diplomatic weight, victory standings, ascension paths, and detailed espionage operations against multiple 4.5.2 saves and in-game screens.
- Validate exact building and ship eligibility, costs, enemy-specific counters, and policy/diplomacy recommendations before presenting them as actionable.
- Apply enabled mod and DLC conditions to technology and artwork mapping; test more empire types and save variants.
- Test the Windows camera across fullscreen, borderless, minimized windows and multiple monitors. Preserve the browser picker in source mode.
- Improve non-spoiler rival comparisons where reliable player-visible contact ratings can be extracted. Do not derive ordinary advice from hidden exact scores.

## Next-release review: empire overview, planet jobs, and rival intelligence

**Scope:** planning and fix notes only. Target the current 4.5.2 Cygnus save format; validate every new field against a same-date in-game screen before presenting it as an available action. Keep the existing Main, Planets, Tech Tree, Ship Builds, and chat navigation. The previous player-inclusive Military/Economy/Technology/Opinion comparison fix remains in scope.

### What the current dashboard actually knows

- The save parser reads the player's Energy, Minerals, Food, Consumer Goods, Alloys, Unity, and Influence stockpiles and monthly balances; research income keys may be present. Main prominently displays only Energy, Alloys, fleet power, colony count, naval *use*, and empire size. It does not yet display naval capacity, starbase use/capacity, or a full resource overview.
- Planets currently show stability, crime, population, free housing, free amenities, aggregate output/upkeep, and counts of districts/buildings. They do **not** show individual job settings, filled/vacant jobs, unemployment, construction eligibility, or pop-group details. The existing planet advice is consequently a prompt to check the game, not a verified build order.
- Contacts currently expose names, exact saved military/economy/technology power, and an opinion value when found. They do **not** yet expose intel level, relative in-game ratings, war exhaustion, claims, diplomatic weight, overlord/subject ties, victory score, or espionage details. Exact foreign power from a save may exceed what the player knows in game. Label or withhold it accordingly.

### Recommended one-screen layout

```text
Left navigation     Main command screen                                  Chat
Main                Campaign/date + stale-save/refresh state            Ask or screenshot
Planets             Your empire health: Economy | Progress | Capacity   History/quick asks
Empires             Next 5–10 years: goal → 1–2 verified steps         Context follows tab
Tech Tree           Urgent watchlist                                     
Ship Builds         Known empires: top risk/opportunity + View all      
                    Compact trend (expand for history)                  
```

Use a small number of color-coded exceptions, with labels and units: **healthy, watch, urgent, unknown**. Group the player's indicators into **Economy** (Energy, Minerals, Food where relevant, Consumer Goods where relevant, Alloys), **Progress** (Physics/Society/Engineering research and Unity), and **Capacity** (empire size trend, naval used/limit, starbases used/limit). Show stockpile plus monthly change where meaningful. A click opens the relevant detail; keep long explanations in collapsible sections so goals and the next graph remain visible without excessive scrolling. Do not turn a positive monthly balance into an automatic “all clear” when the stockpile or forecast is poor.

### P1 — Planet jobs and actionable advice

Add a **Jobs & controls** block to the selected Planet card: filled/open/disabled jobs by type, relevant job priority or enablement settings, unemployed population, housing, amenities, stability, and crime/deviance if available in this empire's save. Show designation, districts, buildings, queue, and verified build capacity alongside those values. Account for Cygnus Pop Group representation and empire types; do not invent one-pop-to-one-job assignments when the save does not support them.

Each recommendation should use **Observation → Suggested in-game action → Expected effect/trade-off → Confidence/check**. Examples: enable existing amenity jobs before proposing a building; prioritize a mining job only if capacity, workers, and mineral need justify it; add housing only if an eligible district/building is available. Consider the resulting upkeep and displaced production. If exact job controls or construction eligibility cannot be parsed, say what the player should inspect in game instead of naming a build as guaranteed.

### P1 — Empires view and player position

Give **Empires** a left-side destination and keep a brief comparison on Main. Show the player's nation as a fixed, highlighted reference with its rank/ratio wherever a comparable saved number exists. Use top category tabs **Military | Economy | Technology | Diplomacy | Intel**; Opinion belongs in Diplomacy and is explained as a relationship value, not a measure of power. Selecting a contacted empire opens its detail card rather than adding a tall list to Main.

- **Military:** player-relative fleet rating or clearly labeled saved-power comparison, war participation and side-specific exhaustion when at war, and verified claims. Claims are a risk signal, never a prediction that war is certain.
- **Economy / Technology:** player-relative ratings when supported by current intel. Do not show an exact foreign stockpile, monthly balance, tech queue, or research completion as ordinary player knowledge.
- **Diplomacy:** opinion **and** attitude, diplomatic weight, agreements, federation, subject/overlord relationships, truces, and war ties when verified. A weak subject's overlord is a useful attack-planning warning.
- **Intel:** what the player knows about that empire; espionage network/infiltration, assets, operations, and known intelligence where the 4.5.2 save and game UI can be reconciled. Mark each field **Known**, **Unknown: improve intel**, or **Unavailable in this save**. The page must never turn a missing value into zero.
- **Progression:** victory standings and known ascension path are secondary, collapsible details only if validated against the player's in-game information.

The save may contain hidden AI economy, technology, personality, unexplored galaxy, and pop data. **Recommendation: omit hidden information from normal advice.** If a later release adds a spoiler mode, make it explicit, off by default, and visually distinct; never let hidden values silently drive military or diplomatic recommendations. First verify that the proposed fields really exist and are stable in representative 4.5.2 saves. This also avoids giving recommendations that the player cannot independently confirm in game.

### Optional spoiler mode: Settings consent flow

Add one Settings control labelled **Show hidden save information (spoilers)**, off by default. Selecting it opens a warning dialog without changing the setting. The warning should say: **“Save files may reveal other empires' resources, technology, plans, and unexplored galaxy details before you discover them in game. Seeing these can reduce the fun of exploration and strategy.”** Provide **Cancel** as the safe exit.

Require two deliberate confirmations inside the dialog: (1) the player checks **“I understand this may spoil my game”**; (2) the player clicks **“Enable spoilers”**, which stays disabled until the acknowledgement is checked. Closing or cancelling the dialog leaves the setting off. The control may be turned off immediately without another confirmation.

When enabled, display a persistent **Spoiler mode ON** marker wherever hidden values appear, and label each such value **From save · hidden in game**. Apply the setting consistently to Main, Empires, graphs, chat context and replies, and screenshots or exports the dashboard creates, so hidden details never leak while it is off. Keep spoiler-derived recommendations separately labelled; normal recommendations continue to use player-visible intelligence. Save consent for the current campaign only and reset it for a different campaign. Verify the default, cancel, enable, disable, restart, campaign switch, and chat paths before release.

### Camera: prefer the Stellaris window

On camera click in the packaged Windows app, find a visible Stellaris game window and make it the default capture target. With one unambiguous match, capture that window directly and open the existing region-selection preview; the player still chooses a crop or the full captured window before attaching it to chat. If several Stellaris windows match, ask which one. If none is found, or direct capture fails, show **Choose a window** and **Entire screen** options. Never silently capture the desktop as a fallback. Keep the existing manual choice available so the player can photograph a launcher, map, or other window deliberately.

This needs a Windows-side capture path in the desktop package: the current camera uses browser `getDisplayMedia()`, whose picker cannot be forced to select Stellaris or restricted to a particular window. In browser-only mode, show the browser's normal window/screen picker and explain that the player should select Stellaris. Capture only when the camera button is pressed, stop the capture session after taking the frame, and do not send it until the player submits the chat question. Verify windowed, borderless, and fullscreen modes; multiple monitors; minimized/inaccessible windows; permission denial; and the no-Stellaris fallback.

### Priority and acceptance checks

1. **Trust and correctness first:** distinguish saved values from player-visible intel; include player position in comparisons; show unknown and save age explicitly. Compare with the same 4.5.2 in-game date and an empire with low intel.
2. **Main-page empire health:** surface all relevant resource trends and capacity limits without crowding the goal cards. Check organic and machine empires, deficits, and missing fields. Resource needs and penalties vary by empire, policies, difficulty, and version; avoid blanket rules such as “a food deficit always halts growth” or “a claim guarantees war.”
3. **Planet jobs:** verify settings, available/fill rates, queue, and build eligibility with several different colony types before emitting a concrete action. Verify advice changes when jobs are disabled or an eligible district is exhausted.
4. **Empire detail:** validate intel, power ratings, relationship data, wars, and subject ties against Contacts/Diplomacy/War screens; test both well-known and poorly known rivals. War exhaustion is side/context dependent. Keep unsupported categories collapsed or unavailable.
5. **Optional later research:** victory scores, ascension clues, hidden save information, anomaly/galaxy data, and exact AI stockpiles. These should not delay the player-facing P1 improvements.


The v1.4 goal-to-action cards, progress tracking, selected military policies, local game artwork, focused base-game technology paths, and shorter LM Studio requests are delivered. See [v1.4 release notes](RELEASE-1.4.md).

These items still need research and validation before a later release:

1. **Verify build eligibility directly.** Parse district capacity, building slots, construction queues, jobs, and eligible system deposits so a recommendation can say a named build is available rather than ask the player to check. Include mineral, food, and consumer-goods upkeep in the decision.
2. **Expand diplomacy and policy eligibility.** Read treaties, federation laws and benefits, policy cooldown, wars, truces, and player-visible intel before naming an available action. Do not infer an ally will join a war.
3. **Apply enabled mod overrides** to technology prerequisites, icon paths, localization, and policy options.
4. **Improve historical planning.** Record completed goals and refresh a plan after a major event without resetting active targets. Track additional planet and faction trends when Cygnus Pop Group fields are validated.
5. **Refine artwork.** Compare best-effort flag composition against the in-game shader and map more local icons.
6. **Follow 4.6 Ideologies separately.** Developer diary #436 is a preview, not a 4.5.2 rule. See [the 4.6 watchlist](WILLPOWER-4.6-IDEOLOGIES.md).

## Fix notes from v1.4 screenshots

1. **Chat response error — delivered in v1.4.3.** Missing or null provider text now produces a useful error rather than `'NoneType' object has no attribute 'strip'`. Text questions retain the built-in fallback. Screenshot questions explicitly say when the image was not analyzed.
2. **Compare empires with the player.** Add Military, Economy, Technology, and Opinion tabs at the top of the Other empires card. Show the player's nation highlighted at its actual rank in the first three tabs, with saved values and ratios to the player. Keep Opinion separate as their relationship with the player. Label foreign power values as save data and validate what the game exposes through intel.
3. **Make Ship Builds recommend designs, not just reinforcement.** The current parser retains only distinct component names, and its recommendation chooses a saved design largely by role or hull size. In the shared example it recommends reinforcing Tachi, while the in-game Ship Designer shows the auto-generated Fox-class Frigate's actual slots, components, role, cost, upkeep, and combat stats. Those screens are from different game dates (dashboard save 2277.07.01; game 2277.09.16), so compare them again at the same save date before treating any difference as a parsing error.

   Build a native, save-grounded design check first: read sections and slot-by-slot components (including repeated components), unlocked alternatives, ship role, relevant policies, build cost, upkeep, naval-capacity usage, and any usable enemy intel. Rank owned designs for a stated purpose, then suggest concrete, legal changes in the in-game Ship Designer only when eligibility can be verified. Distinguish auto-generated from player-edited designs when the save exposes that information. If data is missing, say what must be checked in game.

   Let the optional AI explain the trade-offs and answer questions such as “Should I keep Fox's siege loadout or change it?” using the validated design data. The native recommendation must remain available when no AI provider is configured or its response fails. Present **Current design → Suggested change → Why → Expected trade-off → Check in game** on the existing Ship Builds page. Validate displayed slots, component counts, role, cost, and stats against the 4.5.2 in-game Ship Designer before claiming a recommendation is buildable.
