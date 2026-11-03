# Flemington Main Street, c. 1920 — VR Walkthrough

## Goal

A walkable VR reconstruction of Main Street in Flemington, NJ as it looked around 1920,
built with A-Frame (WebXR) and viewed on a Meta Quest 2 (via Quest Link from a PC) or in
Chrome on the desktop. The street should feel like a warm, hazy small-town afternoon, with
the Hunterdon County Courthouse and the Union Hotel as the two landmarks.

Scope decisions:
- Buildings are real 3D models (not just textured boxes) so porches, verandas, steps and
  rooflines read correctly. Exteriors only: no interiors.
- Auxiliary buildings (sheds, stables, auto garages, ice houses and other outbuildings behind
  the main buildings) should eventually match the 1921 Sanborn map.

Decisions (2026-11-02):
- Models are built in code from a kit of parts (no Blender). On hold until the buildings
  are researched.
- Start small: the block around the courthouse and the Union Hotel first, then expand.
- Outbuildings on hold. Visitors stay on Main Street (no alleys or side streets).

## Constraints

- A-Frame from a CDN, plain HTML/JS. No build tools or frameworks.
- Quest 2 budget: aim for under ~100 draw calls and ~100k triangles on screen.
- Textures: JPG/WebP, 512–1024 px on the long side (2048 only for landmarks), powers of two where possible.
- Models: glTF/GLB, Draco- or meshopt-compressed, one material per model where possible.
- No real-time shadows; bake lighting into textures if needed.

## Project layout

```
index.html          The scene: sky, lights, street, buildings, player rig
js/components.js    Custom components: building, canvas-texture, gradient-sky, locomotion
js/kit.js           Kit of parts: boxes, columns, gable/mansard roofs, arches, merged per material
js/landmarks.js     kit-building component: Union Hotel, courthouse, county offices, law office, house
assets/maps/        Sanborn map sheets
assets/photos/      Facade photos (cropped straight-on to each building front)
assets/models/      GLB models (courthouse, hotel, props)
assets/textures/    Tiling textures (dirt, planks, brick, clapboard)
assets/audio/       Ambient sound (horses, birds, distant voices)
PLAN.md             This file
```

Buildings are named `bldg-w01`–`bldg-w08` (west side, north to south) and
`bldg-e01`–`bldg-e08` (east side, north to south). North is -Z.

## Build steps

1. [x] Scene skeleton: dirt road, wooden sidewalks, placeholder buildings, sky, haze, lighting.
2. [x] Movement: WASD + mouse on desktop; thumbstick walk + snap turn in VR; Enter VR button.
3. [ ] Research: gather 1915–1925 photos, Sanborn fire-insurance maps, and postcards of Main Street.
4. [~] Layout pass: adjust building widths, heights and order to match the Sanborn map.
       Done for Bloomfield Ave–Court St (starter block) and the east side to Higgins Ave.
5. [ ] Facade photos: crop/straighten a photo per building, set `photo:` on each.
6. [~] Landmarks: built in code with the kit (`js/kit.js`, `js/landmarks.js`). Done: Union Hotel,
       courthouse, county offices, Wurts law office, house at 65 Main. Still plain blocks:
       Bank Building (56–66), 68 and 78 Main, 57 Main.
7. [ ] Ground textures: replace procedural dirt and planks with real tiling textures.
8. [ ] Props: telegraph poles, hitching posts, a few period cars/wagons, street lamps (use instancing).
9. [ ] Audio: low-volume ambient loop, positional sounds near landmarks.
10. [ ] Information points: short captions about each building's history.
11. [ ] Performance pass on the Quest 2 (check draw calls, frame rate, texture sizes).
12. [ ] Optional: host on HTTPS (e.g. GitHub Pages) to open directly in the Quest browser without Link.

## Asset checklist

### Reference material
- [x] Sanborn map of Flemington, Sept 1921 (Library of Congress), sheets 2–3 in `assets/maps/`
- [ ] Historical photos / postcards of Main Street (Hunterdon County Historical Society)
- [ ] Notes on which businesses occupied which buildings c. 1920

### Photos (`assets/photos/`)
- [ ] bldg-w01 … bldg-w08
- [ ] bldg-e01 … bldg-e08
- [ ] Courthouse front
- [ ] Union Hotel front

### Models (`assets/models/`)
- [ ] courthouse.glb
- [ ] union-hotel.glb
- [ ] Props: telegraph pole, hitching post, street lamp, Model T, horse and wagon

### Textures (`assets/textures/`)
- [ ] dirt-road.jpg (tiling)
- [ ] boardwalk-planks.jpg (tiling)
- [ ] brick.jpg, clapboard.jpg (tiling, for building sides)

### Audio (`assets/audio/`)
- [ ] Ambient town loop (birds, wind, distant hooves)
- [ ] Courthouse bell (optional)

Check licensing for every asset and note the source in the progress log.

## Progress log

| Date       | Change |
|------------|--------|
| 2026-11-01 | Project set up: A-Frame 1.6.0 scene with dirt road, plank sidewalks, 16 placeholder buildings, courthouse and hotel lots, gradient sky, warm fog and lighting, desktop and VR movement. Folder structure, PLAN.md, git repo. |
| 2026-11-01 | Saved 7 reference photos from West Jersey History to `assets/photos/reference/` (see SOURCES.md). |
| 2026-11-02 | Saved 1921 Sanborn map sheets 2 and 3 (Library of Congress) to `assets/maps/`. The courthouse (75 Main, west side) and Union Hotel (76 Main, east side) face each other at Court St. |
| 2026-11-02 | Saved 25 more period photos (1905–1915) of the Union Hotel, courthouse, county buildings, bank and post office from West Jersey History, plus 7 HABS survey photos (Library of Congress) to `assets/photos/reference/habs/`. |
| 2026-11-02 | Starter block built. Added the building kit (`js/kit.js`) and modelled landmarks (`js/landmarks.js`). Street re-laid from the map: Main St 66 ft wide, real positions and setbacks for the courthouse, county offices, Wurts office, 65 Main, Union Hotel, Bank Building, 68 and 78 Main; Bloomfield Ave and Court St openings; lawns and front paths on the west side. Map-sized placeholders beyond the block. 103 draw calls, ~3.9k triangles. Guesses: style of 65 Main and the houses south of Court St; street width north of Bloomfield. |
| 2026-11-02 | Switched landmark modelling to Blender (MCP for Blender). Union Hotel built by script `tools/blender/union_hotel.py`: recessed arched windows, bracketed cornice, mansard with dormers, end towers, curved central pavilion with sign, two-storey veranda with turned posts, arcade, balustrade and spindle frieze. ~26k triangles. Saved `assets/models/source/union_hotel.blend`, preview `assets/models/previews/union_hotel.png`. Not yet exported to the scene. |
