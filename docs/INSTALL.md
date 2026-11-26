# Install Stellaris Guide 1.6.4 on Windows

1. Find `StellarisGuide-Windows-1.6.4.zip`. Right-click it and choose **Extract All**.
2. Open the extracted folder and double-click **StellarisGuide.exe**. Check the badge below **STELLARIS GUIDE** says **v1.6.4**.
3. Open your Stellaris **4.5.2 Cygnus** campaign. The Guide checks your newest save every **15 seconds**. Click **↻** to check immediately.

You do not need a mod, Node, a terminal, or an AI account. The Guide only reads saves. It never changes them.

## Choose the right campaign

If another campaign appears, open **Settings → Stellaris save folder** and select the folder containing your campaign folders. Usually this is:

```text
Documents\Paradox Interactive\Stellaris\save games
```

Make a new save in the campaign you want, then click **↻**. The first large save may take a little longer to read.

## Read the dashboard

- **Main:** your most useful next move, a goal you pinned, serious resource warnings, trends, Watchlist, and the known-galaxy comparison. Expand a move for steps you can take in game.
- **Planets:** select a colony for jobs, housing, amenities, stability, and cautious build advice.
- **Empires:** review known contacts. Exact rival figures may be hidden; **Unknown** means the Guide cannot verify them in normal mode.
- **Tech Tree:** see current research and select a target for **Explore route**. This opens a separate Microsoft Edge window with prerequisite steps. Close that window with its own **Close** button.
- **Fleet:** review your owned fleets, saved designs, recorded components and policies. Enter the naval limit shown in Stellaris to see whether a planned build exceeds it. The Guide remembers that number on this PC for the campaign.

If Microsoft Edge is not installed, the main Guide still works in your default browser, but **Explore route** cannot open its separate window. A route labelled **Limited** needs an in-game check because the game version, DLC, mod rules, or prerequisite data could not be fully verified. This release was checked against **4.5.2 Cygnus**; after a game update, treat route and strategy rules as unverified until compatibility is checked again.

## Ask a question

The **built-in guide works offline**. Choose a quick question or type your own. You can type `/ask`; **Tab** completes the command and **Enter** sends. **History** stores question text locally without images or AI answers.

Optional **Ollama** and **LM Studio** use a model on your PC. For LM Studio, start its local server on port 1234. **OpenRouter** uses an online service and needs its model ID and API key in Settings. Text questions fall back to the built-in guide when an AI provider fails.

For a screenshot question, select an **image-capable model**, then click the camera beside Send. The Windows app first tries to capture Stellaris. Select the region you want to ask about and press **Send**. If Stellaris is minimized or cannot be captured, restore the window or choose another window or the full screen. OpenRouter receives your question, a relevant summary from the selected save, and any attached image online when you press Send. If the image cannot be analyzed, the Guide says so. Check image-derived suggestions in Stellaris.

## Hidden information

**Settings → Show hidden save information (spoilers)** starts off. Enabling it requires reading a warning and confirming twice. It can reveal rival data not yet visible in game. Consent applies to the **exact selected save** and turns off when a different save is selected, including the next autosave. This prevents a replacement campaign from inheriting permission. You may turn it off at any time.

## Reopen or close

Closing the browser tab leaves the Guide running. Find its icon near the Windows clock; click **^** if hidden. Right-click it to **Open dashboard**, **Refresh latest save**, or **Quit Stellaris Guide**. You can also quit from Settings. v1.6.4 can run beside an older release during testing; quit the older tray icon when you no longer need it.

## Common fixes

| Problem | Try this |
| --- | --- |
| Wrong campaign | Save the desired campaign and click ↻; check the folder in Settings. |
| Old date | Wait for Stellaris to finish the autosave, then click ↻. |
| No game artwork | Select your Stellaris installation folder in Settings. |
| LM Studio timeout | Confirm its local server and model are running, or use the built-in guide. |
| Route says Limited | Confirm release, DLC, mod and research prerequisites in Stellaris. |
| Camera cannot find Stellaris | Restore its window, then retry or choose another capture source. |
