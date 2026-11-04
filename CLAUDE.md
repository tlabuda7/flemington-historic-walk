# Flemington Historic Walk — project rules

A WebXR (A-Frame 1.6.0, no build tools) walkthrough of Main Street, Flemington, NJ, c. 1920,
for Meta Quest 2 (browser via GitHub Pages, or PC + Quest Link). The owner is a beginner:
explain briefly and plainly.

- Live site: https://tlabuda7.github.io/flemington-historic-walk/ (repo tlabuda7/flemington-historic-walk, branch main)
- Local preview: `python -m http.server 8000` in the project root → http://localhost:8000
- PLAN.md = goals, per-building specs, status. SOURCES.md = every external asset and its licence.

## Build pipeline (the main session is the orchestrator)

For each building, in order:

1. **planner** writes the building's spec into PLAN.md.
   → **Pause and show the spec to the user. Do not build until they approve it.**
2. **asset-scout** fetches the CC0 textures/props the spec lists.
3. **blender-builder** builds, bakes and exports `assets/models/<building>.glb`.
4. **reviewer** checks it against the spec and photos: returns PASS or a numbered fix list.
   If fixes: send them back to blender-builder, then review again. **Max 3 fix rounds**;
   after that, stop and ask the user.
   → **Show the user the reviewer's result (and preview images) before integrating.**
5. **scene-integrator** places the approved model, checks performance, commits and pushes.

Rules:
- **Only blender-builder may use the Blender MCP tools (`mcp__blender__*`), and only one
  building at a time.** No other agent and not the orchestrator may call them.
- Update the building's **Status** line in PLAN.md after every step (who did what, result).
- Only one building is in Blender (blender-builder) at a time. The **planner may work one
  building ahead**: it researches and specs the next building while the current one is being
  built, reviewed or integrated. Both edit PLAN.md, so each touches only its own building's
  section, its own Pipeline row and the Progress log.
- Subagents start without this conversation's history: give them the building name, the
  PLAN.md section, and any reviewer fixes verbatim.

## Coordinates and measurements

Scene (A-Frame): 1 unit = 1 m. Main Street runs along Z, **north = −Z**. z = 0 is the north
side of Court St. Main St is 66 ft (20.6 m) between property lines: x = −10.3 … +10.3.
Road x = ±6.4; concrete sidewalks x = ±6.4 … ±10.3, top at y = 0.15; curbs at x = ±6.52.
A building entity's position is the **centre of its front line at ground level**; west-side
buildings use `rotation="0 90 0"`, east-side `rotation="0 -90 0"`.

1921 Sanborn map (`assets/maps/flemington-1921-sanborn-sheet-02.jpg` / `-03.jpg`,
6450 × 7650 px): **1 px = 0.0521 m** (scale bar: 50 ft = 292 px). Sheet-2 pixels → scene:
`x = (px − 3797) × 0.0521`, `z = (py − 6900) × 0.0521`. Sheet 3 lines up with sheet 2 when
you add 5593 to its y. Odd street numbers are on the west side, even on the east.
`tools/` has helpers; a gridded crop script lives in the session scratchpad history, so
re-create one with Pillow if needed (crop + grid lines labelled in full-res pixels).

## Blender conventions

- Z up, metres. The building's **front faces −Y**; origin = centre of the front line at
  ground level (y = 0 is the front-most edge of porch/portico; steps may extend to −Y).
  glTF export (+Y up) turns −Y into +Z, which is "front" in the scene.
- Everything is built by a script: `tools/blender/<building>.py` (geometry) and
  `tools/blender/<building>_bake.py` (materials, lightmap bake, export). Pattern to follow:
  `tools/blender/union_hotel.py` + `union_hotel_bake.py`. Save the .blend to
  `assets/models/source/<building>.blend`, previews to `assets/models/previews/`.
- Each building gets its own collection; keep other buildings' collections hidden from
  render during a bake.
- Look: Poly Haven CC0 colour maps at 1K (tile in real-world metres with box UVs), a
  second UV map "Lightmap", Cycles bake (DIFFUSE direct+indirect) into one 2K lightmap,
  multiplied by a baked grime mask, saved sRGB-encoded as
  `assets/textures/<building>-lightmap.jpg`. The scene applies it with
  `baked-lighting="lightmap: …; intensity: <LIGHTMAP_SCALE printed by the bake>"`.
- Sun: warm late afternoon from the **WSW, ~21° up** in the world. Blender "to sun" vector:
  east-side buildings (front faces west) `(0.40, −0.90, 0.36)`; west-side buildings (front
  faces east) `(−0.40, 0.90, 0.36)`. Sky colour (0.42, 0.55, 0.78), strength 0.9.
- The GPU (RTX 3070, OptiX) is set up for Cycles. A full bake takes ~15 s.

## Budgets (Quest 2, 72 fps in the browser)

- Landmark building ≤ 30k triangles; ordinary building ≤ 10k; tree ≤ 1k.
- Colour textures 1K (2K only if the spec justifies it); one 2K lightmap per building.
- GLB ≤ 5 MB per building. Whole scene ≤ ~150 draw calls, ≤ ~300k triangles in view.

## Licences

- West Jersey History photos (`assets/photos/reference/*.jpg`) are **local only**:
  gitignored, never commit or upload them. Reference them by filename.
- HABS photos and Sanborn maps (Library of Congress): public domain, committed.
- Poly Haven assets: CC0. Log every downloaded asset in SOURCES.md (file, asset id, URL, licence).

## Environment (Windows)

- PowerShell 5.1 blocks `claude.ps1`; use `claude.cmd`. GitHub CLI:
  `"C:\Program Files\GitHub CLI\gh.exe"` (logged in as tlabuda7). Python 3.12 with Pillow.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
