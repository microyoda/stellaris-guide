# v1.6 chat evidence and safety decision

The optional model receives a question-specific packet from the selected save. It includes the save date, game release, player empire, DLC and mod labels, installed-rule verification state, relevant planet/contact/ship records, current research and requested technology route. Save labels alone do not prove active mod rules. Normal mode removes exact rival strength and hidden stockpiles before packet construction.

Answers cite packet records. Each sentence with a save-derived number may cite one record, and the number must match a nearby field label and value in that record. The app rejects unsupported claims and uses the built-in guide as fallback. This is a guard against common mistakes, not a proof that every natural-language claim is strategically correct. Questions requiring unsupported or unverified data should be checked in game.

Spoiler consent uses the SHA-256 fingerprint of the **exact selected save file**. It turns off whenever a different autosave is selected, even within the same campaign. This is intentional: the available folder and player IDs can be reused by a different campaign, so they cannot safely preserve consent. The interface discloses this behavior before enabling spoilers. Old folder-based consent is ignored.

Screenshots are local until the player sends one. A screenshot goes to the selected local vision model or OpenRouter. Provider metadata must confirm image support; invalid or blank images fail before upload. The app labels an image observation and warns when the image date differs from the selected save. Image text is untrusted and several instruction patterns are rejected, but prompt injection phrased differently can still contaminate advice. The model has no application tools or API key in its prompt, and the UI renders its reply as text. Players should verify image-derived actions in Stellaris.

Ollama, LM Studio and OpenRouter request and error paths have mocked tests on the same fixture. Live local model quality was not compared in this environment because Ollama and LM Studio were unavailable; no claim of model quality parity is made.
