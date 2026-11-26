# UI/UX design rationale

## Page structure

The desktop layout uses three stable areas:

1. A left sidebar for **Main**, **Planets**, **Tech Tree**, and **Ship Builds**.
2. A central workspace for the selected page.
3. A right chat rail that stays available while the player changes pages.

Energy, alloys, fleet power, and colony count remain directly below the page header on every tab. This answers the earlier “where are the existing indicators?” problem and prevents the player from losing overall campaign context while reviewing a colony or ship design.

On narrower windows, the sidebar becomes a compact top navigation and the chat moves below the selected page.

## Information priority

- **Main** begins with the next 5–10 year plan and warnings, followed by trends and empire comparisons.
- **Planets** ranks urgent colonies first. Selecting one reveals measured values and one build or recovery recommendation.
- **Tech Tree** uses one card per research branch, showing the current project before a suggested visible alternative.
- **Ship Builds** starts with the recommendation, then shows owned designs and their saved components.

The recommendation and its measured reason appear together. Detailed values support the decision instead of competing with it.

## Chat interaction

Quick questions change with the active tab and fill the input so the player can edit them before sending. Typing `/` opens a command hint; **Tab** completes `/ask `. Enter sends and Shift+Enter adds a line. A thinking message identifies slow local models without making the interface appear frozen.

## Visual language

The dark navy palette echoes Stellaris without copying game assets. Teal marks the player and positive values, violet marks other empires, coral marks urgent warnings, and gold marks time targets. Borders and spacing separate information without filling the page with decorative panels.

## Accessibility

- Navigation and chat work with keyboard controls.
- Text labels accompany color states.
- Buttons retain visible focus behavior supplied by the browser.
- Responsive layouts avoid horizontal page scrolling at common desktop and tablet widths.
- Recommendations use plain language and expose the reason behind each priority.
