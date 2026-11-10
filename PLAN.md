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
- ~~Models are built in code from a kit of parts~~ → superseded: landmarks are built in
  Blender by script with Poly Haven textures and baked lighting (Union Hotel first).
  The code kit (`js/kit.js`) remains for placeholders.
- Start small: the block around the courthouse and the Union Hotel first, then expand.
- Outbuildings on hold. Visitors stay on Main Street (no alleys or side streets).
- Buildings go through the agent pipeline in CLAUDE.md
  (planner → asset-scout → blender-builder → reviewer → scene-integrator), one at a time,
  with user approval of the spec and of the review.
- 2026-11-03: owner is away and asked the orchestrator to keep building and integrating
  buildings without waiting. Specs and reviews are auto-approved for now ("most realistic,
  from the photos"); open questions are settled from the photos and logged under each spec's
  "Orchestrator decisions" for the owner to check later. Order after the courthouse: county
  offices → Wurts law office → bank building → 78 Main → house at 65 Main → 68 Main.
  A building that fails 3 review rounds is parked and skipped.
- 2026-11-03: the planner may now work one building ahead (see CLAUDE.md); only one building is
  in Blender at a time.

## Pipeline status

| Building | Spec | Assets | Built | Review | In scene |
|----------|------|--------|-------|--------|----------|
| Union Hotel (70–76 Main) | done before pipeline | done | done | — | yes |
| Hunterdon County Courthouse (75 Main) | approved | done | done, round-1 fixes applied (13.7k tris, 2.6 MB) | round 2: PASS | yes (GLB, 2026-11-03) |
| County Offices / Hall of Records (69–71 Main) | written, auto-approved (owner away) | done (1 new + 3 tinted, 3 reused) | done (8.6k tris, 2.2 MB, LIGHTMAP_SCALE 1.1299) | round 1: PASS | yes (GLB, 2026-11-03) |
| Wurts Law Office (59 Main) | written, auto-approved (owner away) | reused, none new (asset-scout skipped; 1 grey copy of weathered_planks made locally) | done (7.6k tris, 5 materials, 1.2 MB, 1K lightmap, LIGHTMAP_SCALE 1.1647) | round 1: PASS | yes (GLB, 2026-11-03) |
| Bank Building / Flemington National Bank (56–66 Main) | written, auto-approved (owner away) | done (1 new: sandstone_blocks_05 greyed → stone_rockfaced; 1 generated: awning_stripes; 3 reused) | done, round-1 fixes applied (8.8k tris, 6 materials, 1.8 MB, 2K lightmap, LIGHTMAP_SCALE 1.1241) | round 2: PASS | yes (GLB at 12.24, 0.15, −66.24) |
| Nevius Store / Fulper's Dry Goods (78 Main) | written, auto-approved (owner away) | reused, none new (asset-scout skipped; 4 reused maps) | done, round-1 fixes applied (7.0k tris, 5 materials, 1.3 MB, 2K lightmap, LIGHTMAP_SCALE 1.1072) | round 2: PASS (round 1: 3rd-floor windows raised; LIGHTMAP_SCALE now 1.1072) | **yes** (10.30, 0.15, −7.33) |
| Frame Dwelling at 65 Main (old no. 510) | written, auto-approved (owner away) | reused, 1 recoloured copy (asset-scout skipped; brown_planks_05 → clapboard_cream made by the builder; roof_slates_03 + red_brick reused) | done (6.3k tris, 4 materials, 1.0 MB, 2K lightmap, LIGHTMAP_SCALE 1.274) | round 1: PASS | yes (GLB, 2026-11-03) |
| Lovell's Restaurant (68 Main) | written, auto-approved (owner away) | reused + 2 generated (asset-scout skipped; clapboard_cream reused; signs_atlas + stone_bluestone (lightened concrete_floor_worn_001) made by the builder) | done, round-1 fixes applied (4.75k tris, 4 materials, 0.77 MB, 2K lightmap, LIGHTMAP_SCALE 1.2462) | round 2: PASS (round 1: awning raised/shortened, glazed doors, lighter stone; LIGHTMAP_SCALE now 1.2462) | yes (2026-11-04) at (12.66, 0.15, −52.13); bank forecourt extended over its front strip |
| Rea Building / Clock Tower Building, old Post Office block (48–52 Main) | approved by owner 2026-11-04, **landmark** detail (≤ 15k tris) | — | done (14.6k tris, 5 materials, 1.89 MB, 2K lightmap, LIGHTMAP_SCALE 1.1735) | round 1: PASS | yes (2026-11-04) at (10.85, 0.15, −97.79); 1 draw call |
| County Hotel (47–49 Main) | approved by owner 2026-11-04: pale painted walls, **landmark** detail (≤ 15k tris) | — | done (10.2k tris, 8 materials, 1.81 MB, 2K lightmap, LIGHTMAP_SCALE 1.1087) | round 1: PASS | in scene 2026-11-04 (−10.30, 0.15, −112.07), 1 draw call |
| Block at 40–46 Main (40–42 "Auto Sales", 44–46 "Shoe Shine & Fruits") | approved by owner 2026-11-04: map-true placement, ordinary (≤ 10k tris) | — | done (4.8k tris, 8 materials, 1.43 MB, 2K lightmap, LIGHTMAP_SCALE 1.2152) | **PASS** round 1 (2026-11-04) | **in scene** 2026-11-04 (8.60, 0.15, −116.55), 1 draw call |
| Test person 1: John B. Pickell, clerk at the Nevius store (78 Main) | written, auto-approved (owner away) | done (Quaternius UAL Standard rig + clips incl. Idle_Talking_Loop; UBC Standard = Superhero bodies only, no Regular; MakeHuman system assets + MPFB 2.0.18 zip, not installed; 3 Poly Haven cloth/leather maps + 3 tinted) | done, round-1 fixes applied (12.8k tris, 65 bones, 1 mesh / 1 material / 1 2K atlas, 1.25 MB; Idle 6 s, Talk 3 s, Walk 1.33 s; MPFB head + hands) | round 2: PASS (round 1 FIXES: moustache, stance/crotch, shoulder and collar, jacket fronts, cuffs, gaze, chain) | **yes** (9.50, 0.15, −8.45), talks with a voice (js/people.js) |
| Street ambiance pass 1: sound + street props (`street-props.glb`, `assets/audio/`) | written, auto-approved (owner away) | done (3 Poly Haven maps + 3 recoloured, 3 reused; 16 audio clips, 1.96 MB / 250 s; bed = #0659 instead of #1911) | props done, round-1 fixes applied (4.75k tris, 12 nodes, 1 material / 1 2K atlas colour × AO, 0.83 MB) | props round 2: PASS (round 1 FIXES: horse-head relief, pump globe lettering seam) | sound: yes (2026-11-04, `js/ambience.js`); props: yes (2026-11-04, `street-props` in `js/components.js`: 34 placements in 3 z-band meshes + 1 wire mesh, +4 draw calls) |
| Distant landscape pass 1 (`landscape.glb`: real hills ring from USGS 3DEP + tree lines + town silhouettes) | written; owner pre-approved the approach, auto-approved within the usage cap (2026-11-04) | not needed (DEM in `assets/maps/`, 1 generated atlas) | done (8.3k tris: far terrain 5,760 + far trees 1,116 + town 1,426; 3 unlit materials, COLOR_0 + 1K RGBA tree atlas, 0.77 MB GLB, no lightmap) | no separate review (integrator sanity check, 2026-11-04) | in scene 2026-11-04: `#landscape` (far ring follows rig at 0.85), ground = 335 m following disc, fog 0.005, sky r 1200, camera near 0.05; +3 draw calls |
| Palace Theatre (31 Main, old no. 518) | approved by owner 2026-11-08: c. 1920, blank parapet panel, ordinary (≤ 10k tris) | reused, none new (asset-scout skipped; 6 reused maps + 1 generated poster atlas, no lettering) | done 2026-11-10 (2.7k tris, 8 materials, 1.58 MB, 2K lightmap, LIGHTMAP_SCALE 0.9901) | **PASS** round 1 (reviewer 2026-11-10) | **yes** (−10.30, 0.15, −145.52) |
| Odd Fellows Hall / Hopewell Building (82–84 Main, old nos. 537–538) | approved by owner 2026-11-10: blank signboards, ordinary (≤ 10k tris) | — | — | — | placeholder only |
| Block at 35–41 Main (35–37 frame "Gro.", 39–41 brick "Cobbler") | approved by owner 2026-11-10: valance lettered "PRODUCE \| JACOB R. HALL \| GROCER" (3b), stair modelled (B2) | — | — | — | placeholder only |
| Block at 32–38 Main (frame row: "Mill'y", "Bakery", "Meats") | written, awaiting owner approval | — | — | — | placeholder only |
| Dry goods and clothing store (27 Main, old nos. 519 A/B; "D.G. & Clo.", possibly the "Potter Building") | written, awaiting owner approval | — | — | — | placeholder only |

## Building specs

(Written by the planner agent, one section per building.)

### Hunterdon County Court House (75 Main St)

**Status:** in scene (scene-integrator, 2026-11-03): `#courthouse` at (−18.34, 0.15, −6.85), rotation 0 90 0, GLB + baked lightmap (intensity 1.1979); paved forecourt (x −10.3 … −18.3, z −13.55 … 0) at sidewalk height replaces the lawn path; 15 cm grade slabs under body, north wing and jail yard. No console errors; 160 draw calls / 53k triangles from the start view (149 / 39k before), 66 / 19k facing it from the east sidewalk. Screenshot `assets/models/previews/courthouse-in-scene.png`. Earlier: review round 2: PASS (reviewer, 2026-11-03): all 5 round-1 fixes + rock wall resolved; GLB 13,680 tris, 2.63 MB, 9 × 1K JPG, TEXCOORD_0+1; lightmap 2048², black area 55% → ~20%; loads in the review viewer (intensity 1.1979) with no console errors. Next: show the owner, then scene-integrator. Earlier: round-1 fixes applied (blender-builder, 2026-11-03): front chimney moved to (3.0, 4.6), top 14.2; rear stacks 0.9 × 1.2 m, top 13.9; smoother white paint on columns/trim (`paint_white.jpg`), warm cream stucco (`stucco_cream.jpg`), mid-grey yard wall (`rock_wall_grey.jpg`), made by `tools/prepare_courthouse_paints.py`; hidden faces (podium top, entablature layers, roof underside, interior) removed and lightmap repacked, window holes filled. GLB 13,680 triangles, 12 materials, 2.6 MB; lightmap 2048², LIGHTMAP_SCALE 1.1979. Previews re-rendered. Next: reviewer round 2. Earlier: review round 1: FIXES (reviewer, 2026-11-03): GLB 11,751 tris, 2.70 MB, 9 × 1K JPG, TEXCOORD_0+1, lightmap 2048² all OK; proportions, columns, pediment, cupola, steps match the c.1910 photo. 5 fixes: front chimney overlaps the cupola (1909 view), blotchy grey column texture, walls read cool blue-white not cream, rear chimneys too slender, ~55% of the lightmap wasted on hidden faces. Browser viewer could not be opened (navigation refused), so checked by GLB parse + previews. Next: blender-builder fixes, then review round 2. Earlier: built (blender-builder, 2026-11-03): `assets/models/courthouse.glb` (11,751 triangles, 12 materials, 2.7 MB), `assets/textures/courthouse-lightmap.jpg` (2048², LIGHTMAP_SCALE 1.1169), scripts `tools/blender/courthouse.py` + `courthouse_bake.py` + `courthouse_preview.py`, source `assets/models/source/courthouse.blend`, previews `assets/models/previews/courthouse-*.png`. Next: reviewer. Earlier: assets ready (asset-scout, 2026-11-03): 5 new Poly Haven CC0 1K maps in `assets/textures/courthouse/` — `stucco_offwhite.jpg` (walls, 2.0 m), `brownstone.jpg` (steps/pedestals/base/sills, 2.15 m), `clapboard_buff.jpg` (north wing + yard building, 1.0 m), `rock_wall_08.jpg` (jail-yard wall, 1.8 m), `dome_paint_green.jpg` (cupola dome, 1.0 m); reuse from `polyhaven/`: trim_paint_cream, roof_slates_03, red_brick, door_paint_green, weathered_planks/wood_table_worn (metal_plate_02 not needed). Logged in SOURCES.md. Next: blender-builder. (Spec approved by owner 2026-11-03; planner 2026-11-02, cross-checked 2026-11-03.)

**Owner decisions (2026-11-03, settled from the photos)** — these override anything below:
1. Main roof: dark grey slate (barely visible from the street; no photo shows it as tin).
   Cupola dome: painted sheet metal, muted green (the 1909 tinted postcard shows a green dome;
   HABS shows it ribbed metal).
2. Walls: warm off-white painted stucco, slightly cream (c.1910 and 1909 views), with grime.
3. Eaves and rake: paired scroll brackets as in the c.1910 dead-on photo (not the later plain
   modillion blocks seen in HABS).
4. Jail yard: include the stone wall and small yard building behind, low detail.
5. No window bars — no photo shows any.
6. Fire-alarm post: include as a simple low-poly prop at the map's F.A. spot.
7. Rear chimneys: three on each roof slope (HABS shows the south slope, the 1909 postcard
   the north slope). Back wall and wing roof stay simple guesses.

**Sources**
- Map: 1921 Sanborn sheet 2. Stone body ("COUNTY COURT HOUSE & JAIL", blue, "2" storeys, "30'"):
  px x 2967–3360, y 6640–6897. Frame portico ("1-2", yellow, dashed outline), full width:
  x 3360–3445. North wing (1-storey frame, "1", with a 1 m blue/stone strip against the body):
  x 3197–3347, y 6567–6640 (yellow 6567–6620, blue 6620–6640). Jail yard with "STONE WALL 20'":
  x 2750–2967, y 6600–6897; 2-storey frame building in the yard x 2855–2950, y 6775–6895.
  Main St property line x 3599; "F.A." circle at (3463, 6845); "T.H." (hydrant) at (3700, 6855).
- Photos (all `assets/photos/reference/`):
  - **Primary: `flemington_-_hunterdon_county_court_house_viewed_dead_on_-_c_1910.jpg`** — straight-on
    east front, c. 1910. Used for every front proportion below (scale: frieze width = 13.4 m
    → 0.031 m/px at the front plane).
  - `flmngtncountycrthousvu09.jpg` (1909, colour, from the NE): north side — 4 brick chimneys,
    frame north wing with shed hood, brownstone base course, granite drinking fountain with globe
    lamp in front of the wing.
  - `flmngtncntycourthsview06.jpg` (1906), `flmngtnhtdncntycrtandbldg05.jpg` (1905),
    `flmngtncrthouspublcbldg08.jpg` (1908, colour), `flmngtncntybldngsvuof08.jpg` (1908),
    `flmngtncourthsandsurrogateoffice.jpg` (c. 1908): all from the NE, showing the pediment
    brackets, cupola, a red chimney just in front of the cupola on the north slope, and the
    low frame wing at the portico's north side; paved forecourt, young curb trees, no railings.
  - `flemington_-_hunterdon_county_courthouse_view.jpg` (1930s, cars) and
    `flmgtnhtrdncntycrths2.jpg` (1930s–40s): south side, 3 rear chimneys; by then the brackets
    are replaced by plain modillions and the pediment has 4 windows — **later state, do not copy**.
  - HABS NJ-771 (1960s, `habs/courthouse-east-front.jpg`, `…-from-northeast.jpg`,
    `…-east-front-and-south-side.jpg`): best for column shape, side-window layout, cupola form
    and the front wall's attic lights. 1960s differences from 1920 are listed below.
  - `flmngtndrinkingfountainbycrthous.jpg`: the horse fountain (separate prop, not in this model).
- Web: NRHP Flemington Historic District nomination (https://npgallery.nps.gov/AssetDetail/NRIS/80002493,
  p. 103: "temple plan with a 3-bay facade set on a high stone foundation… octagonal, frame cupola
  over the front portion of the roof… arched transom, sidelights, 6-panel double doors");
  Preservation NJ (https://preservationnj.org/pnj-on-tour-the-historic-hunterdon-county-courthouse-and-jail/:
  built 1828, Doric columns raised above the street, **brownstone steps**, stucco; present jail
  built **1925**, i.e. after our date); Goodspeed Histories
  (https://goodspeedhistories.com/hunterdons-courthouse-1828/: cornerstone May 1828, portico by
  1830, ground floor = county jail, courtroom on the high second floor, a **frame building on the
  side served as the jail kitchen** = the north wing); NJ Historic Trust
  (https://www.nj.gov/dca/njht/funded/sitedetails/hunterdon_county_courthouse.shtml: stuccoed
  masonry). HABS record https://www.loc.gov/pictures/item/nj0068/ (page refused the fetch; photos
  already local).

**Placement** (west side, front faces east onto Main St)
- Entity position = centre of the portico front line: **(−18.34, y, −6.85)**, `rotation="0 90 0"`
  (placeholder was (−17.8, 0, −7.05); move it). Front line 8.0 m behind the Main St property
  line (x −10.3). Steps project 1.65 m further, to x ≈ −16.7.
- Body front wall x −22.77, rear wall x −43.24; south wall z −0.16 (on the Court St line);
  north wall z −13.55.
- Blender local frame (front −Y, origin at portico front, **+X = north**): portico y 0 … 4.43;
  body x −6.70 … +6.70, y 4.43 … 24.91; north wing x +6.70 … +10.50, y 5.11 … 12.93;
  jail yard x −6.69 … +8.75, y 24.91 … 36.2.
- z = 0 in Blender = foot of the steps (forecourt level). See integrator notes for y.

**Massing**
- Body: 13.40 m wide × 20.48 m deep (map), 2 storeys, eaves/cornice top **9.0 m** above the
  forecourt (map "30'" = 9.1 m; photo 9.0 m). Ground floor (jail) 1.10 → 4.3 m, courtroom floor
  4.3 → 7.45 m (photo/HABS estimate).
- Roof: front-to-back gable, ridge 13.1 m (pediment rise 4.1 m over 6.7 m half-span ≈ 31°,
  photo 1910 + HABS), eaves overhang 0.6 m on the sides. Same closed pediment at the rear (guess).
- Portico: full width (13.4 m) × 4.43 m deep (map), floor (podium top) at **1.10 m**
  (photo, 6 risers); the portico shares the main roof — pediment and roof run forward over it.
- Base course: brownstone water table 1.10 m high round the body (1909 colour photo), flush with
  the podium.
- North wing ("jail kitchen"): 1 storey frame, 3.8 m (N–S) × 7.8 m (E–W), eave 3.4 m, low shed
  roof falling to the north from 4.2 m at the body wall (photo 1909, estimate). The inner 1.04 m
  strip against the body is stone (map) — stucco it like the body, same roof.
- Jail yard (low detail): stone wall 6.1 m high ("20'"), 0.6 m thick, on the yard's north,
  west and south (Court St) sides; 2-storey frame building in the yard's SE corner, 5.0 × 6.3 m,
  eave 6.0 m, low gable (map; form is a guess).

**Elevation details (1920 state)**
- **Columns**: 4, evenly spaced, centres at x = ±2.04 and ±6.13 (spacing 4.09 m), centre
  y = 0.58. Shafts **unfluted**, Doric/Tuscan, base diameter 0.90 m tapering to 0.78 m, from
  1.55 to 7.30 m; simple capital (echinus 0.15 + square abacus 1.05 × 0.15) to 7.45 m. Each
  stands on a **dark brownstone pedestal** 1.15 m square × 0.45 m high (1.10 → 1.55).
- **Entablature** (front and round all sides) 7.45 → 9.0 m: architrave 0.55, frieze 0.65,
  cornice 0.35 with 0.6 m overhang. In the frieze: **pairs of large scroll brackets** above each
  column (4 pairs, the corner pairs wrapping the corners) and small block modillions at ~0.6 m
  between them; same brackets in pairs every ~4 m along the side frieze. Small rectangular
  datestone (1.0 × 0.35 m) centred in the frieze.
- **Pediment**: stuccoed tympanum with **two** 6-light windows (0.9 × 1.1 m, sill 10.0 m,
  centres x ±2.3). Raking cornice with 3 pairs of pendant scroll brackets per side plus small
  modillions between. No oculus.
- **Front wall** (under the portico, y = 4.43), 3 bays: centre **round-arched doorway** 1.85 m
  wide, crown 3.85 m (spring 2.92), fanlight with radiating bars, double 6-panel doors (sidelights
  per NRHP, may be omitted — in deep shadow in 1910); side bays at x ±3.7: ground windows
  1.1 × 1.8 (sill 2.0), second-floor windows 1.1 × 1.9 (sill 4.45) over the door too, and small
  attic lights 0.9 × 0.6 (sill 6.55) above the side second-floor windows (HABS; dark in 1910).
  6/6 double-hung sash, **dark-painted sash and frames** (1910 photo), plain stucco surrounds,
  thin stone sills. Flat plastered portico ceiling at 7.45 m. Flat stucco antae 0.6 m wide at
  the front-wall corners.
- **Steps**: brownstone, full width between the outer pedestals and running past them
  (13.0 m), 6 risers × 0.183 m, treads 0.30 m, projecting to y = −1.65. No handrails in 1920.
- **Side walls** (both): front 3.5 m blank, then 5 bays at 3.2 m, window centres
  y ≈ 9.0, 12.2, 15.4, 18.6, 21.8 (HABS + 1930s photo). Ground floor 1.0 × 1.8 (sill 2.0) with
  vertical iron bars (jail — guess); second floor taller 1.0 × 2.6 (sill 4.4). On the north side
  the wing hides the first two ground-floor bays. Corner pilasters as on the front.
- **Rear wall** (guess, not visible from Main St): 3 bays of the same windows, plain pediment
  without brackets, one attic window.
- **Chimneys**, red brick, 0.8 × 0.6 m, corbelled cap: **south slope 3** at y ≈ 15, 18.5, 22
  rising ~1 m inside the eave line to 14.6 m (HABS/1930s); **north slope 3** matching at the
  rear plus **1 front chimney** just north of the cupola at (x +1.5, y 8), top 15.0 m (1906–09
  photos; gone by the 1960s).
- **Cupola** (centre x 0, y 6.5, over the front of the roof): square stuccoed base 3.0 m
  from the roof to 13.9 m; **octagonal** frame drum 2.8 m across flats, 13.9 → 16.3 m, with a
  round-arched louvred opening (1.0 × 1.6 m) in each of the 8 faces and corner pilasters;
  moulded cornice 0.35 m; **dome** (slightly bell-shaped, ribbed at the 8 corners) 16.65 → 18.1 m;
  ball finial 0.35 m and iron spike/weathervane to ~19.4 m. (Height checked against 1910 photo
  with perspective.)
- **North wing**: east face (y 5.11) with a 4-pane-high window 1.4 × 1.2 and a plain door
  0.9 × 2.1 under a shed hood (0.6 m deep, at 2.7 m); clapboard 0.1 m exposure, corner boards.
- No signage beyond the datestone. No flagpole, lamps or railings on the building in 1920.

**Materials & colours (1920)**
- Walls, antae, tympanum: lime stucco on stone, painted **warm off-white / pale grey**
  (≈ #E6E1D4); columns, entablature, brackets, cupola: painted wood/stucco, brighter white
  (≈ #F2EFE6).
- Steps, pedestals, base course, sills: **brownstone**, red-brown (≈ #6E4A3C).
- Roof: dark grey **slate** (guess, see questions). Cupola dome: painted sheet metal,
  dark grey-green. Chimneys: red brick, unpainted.
- Sash/frames: dark green-black paint; doors dark varnished brown or the hotel's green.
- North wing: clapboard painted dull buff-brown (1909 colour, guess), dark trim.
- Jail-yard wall: grey rubble fieldstone.
- Textures — reuse: `trim_paint_cream.jpg` (columns/trim, 2 m), `roof_slates_03.jpg` (3 m),
  `red_brick.jpg` (chimneys, 1.4 m), `metal_plate_02.jpg` (dome, tinted, 2 m),
  `door_paint_green.jpg` (doors, 0.8 m), `weathered_planks.jpg`/`wood_table_worn.jpg` as needed.
  **New for asset-scout** (Poly Haven CC0, 1K colour): (1) smooth painted stucco/plaster,
  off-white, tile ~3 m; (2) brownstone / red sandstone (smooth or ashlar), tile ~1.5 m;
  (3) painted wooden clapboard/siding, tile ~2 m; (4) rough grey fieldstone/rubble wall, tile ~3 m.

**Weathering**: stucco slightly streaked below sills, under the cornice and at chimney stacks;
greenish-grey damp staining just above the brownstone base; brownstone treads worn and darker in
the middle; chalky paint on the column bases; soot at chimney tops; light rust streaks on the dome.
Keep it a cared-for public building — subtler than the hotel.

**Budget**: target ~22k triangles, hard cap 30k (landmark). Columns 32 sides; brackets as
low-poly profile extrusions; jail-yard wall and yard building < 1k together. 5 reused + 4 new
1K colour textures, one 2K lightmap `assets/textures/courthouse-lightmap.jpg`. GLB ≤ 5 MB:
`assets/models/courthouse.glb`; scripts `tools/blender/courthouse.py` + `courthouse_bake.py`.

**Acceptance checks for the reviewer**
1. Four unfluted columns, evenly spaced across the full 13.4 m front, on dark brownstone
   pedestals; no railings.
2. Pediment has exactly **two** windows and paired scroll brackets on the raking cornice;
   paired brackets over each column in the frieze.
3. Front wall: 3 bays, round-arched centre door, windows on two floors each side.
4. Eaves top 9.0 m ± 0.3 above the step foot; ridge ≈ 13.1 m; pediment pitch ≈ 31°.
5. Octagonal cupola with arched openings and a dome + finial, sitting over the front part of
   the roof (centre ~6.5 m behind the portico front), dome top ≈ 18 m.
6. Body footprint 13.4 × 20.5 m behind a 4.4 m portico; brownstone steps (6 risers) in front.
7. Red brick chimneys: 3 at the rear on each slope + 1 beside the cupola on the north slope.
8. One-storey frame wing on the north side (+X), starting ~0.7 m behind the front wall.
9. Walls off-white stucco, trim white, base/steps red-brown; ≤ 30k triangles. With the WSW
   sun the east front is in shade: the portico and front wall must still read (bounce light,
   not black), and the sunlit south side shows window reveals and chimney shadows.
10. Model origin at the centre of the portico front at step-foot level; front faces −Y.

**Integrator notes (scene, not the model)**
- Move `#courthouse` to (−18.34, y, −6.85). Photos show a **paved forecourt** (no lawn) in
  front of the courthouse: replace the lawn path at (−13.05, −7.05) with paving from the steps
  (x −16.7) to the property line (x −10.3), z ≈ −13.6 … −0.2; set entity y to that paving level
  (0.15 if flush with the sidewalk, as the hotel).
- Curb trees at (−7, −2.6) and (−7, −11.5) match the 1906–1912 views (young trees at the curb);
  keep them. A telegraph pole stood at the curb by the north corner (1910).
- Drinking fountain (rough granite block ~1.6 m with a horse-head medallion, round basin, globe
  lamp on top): 1909 photo puts it at the sidewalk by the north wing, in front of the county
  offices; separate prop later.
- `lawn-west` must not show through the jail-yard / courthouse footprint.

**Differences 1905–1912 vs. HABS 1960s** (build the earlier state): 1960s has plain modillion
cornice (no scroll brackets), 3 + 2 pediment windows, white sash, handrails and cheek walls on the
steps, a hanging lantern, no front chimney, the 1925 stone jail behind, flagpole; trees gone.

**Open questions / guesses**
1. Roof: dark slate (recommended) or painted tin (the 1908 colour card shows it green)?
2. Wall colour: warm off-white painted stucco (recommended) vs. natural grey stucco?
3. Brackets vs. plain modillions: the brackets are documented 1905–1912 but gone by the 1930s;
   the change date is unknown. Recommend brackets (closest photos to 1920).
4. Include the jail-yard 20' stone wall and the yard building (recommended, low detail) or stop at
   the courthouse body?
5. Iron bars on the ground-floor side windows (jail) — guess; keep or drop?
6. "F.A." circle on the map at the portico's SE corner (scene (−17.4, −2.9)) — probably a fire-alarm
   post; the 1905–08 cards show a stone post with a lamp near there. Model it as a prop or ignore?
7. Rear (west) wall and the north wing's exact roof form are not visible in any photo — guesses.
8. Rear chimneys: 3 on each slope (spec) or 3 in total on the north side? (cross-check above)

**Cross-check (second planner pass, 2026-11-02; independent re-measurement, no web access)**
Confirms the spec above within ~0.1 m: map body px x 2968–3361, y 6640–6895 (13.3 × 20.5 m),
portico front px 3443 → entity (−18.44, −6.90) vs (−18.34, −6.85) above — keep the spec's
value. Front proportions from the 1910 dead-on card (0.031 m/px) agree: eaves 9.1 m, columns
evenly spaced at ~4.1 m with the outer ones at the corners, column base Ø ≈ 0.9 m, door 1.85 m
wide with crown ≈ 3.2 m above the portico floor, front bays at x ±3.6. Points the builder should
take from this pass:
- **Pediment windows are taller than above**: 1910 card gives ≈ 0.95 × 1.5 m with sills just
  above the horizontal cornice (≈ 9.3–9.4 m), centres x ±2.1. Use 0.95 × 1.45, sill 9.4.
- **Front chimney**: in the 1906/1908 NE views it stands directly in front of the cupola base,
  i.e. north-*east* of the cupola. Put it at about (x +1.5, y 5.0), not y 8.
- **Rear chimneys**: the NE views (1909) show 3 along the north side, the SE views (1930s, HABS)
  show 3 above the south eave. These may be the same three tall stacks seen across the roof, or
  two rows. The spec's 3 + 3 is a guess; 3 in total on the north slope is equally plausible
  (see open question 8).
- Podium: the 1910 card reads ≈ 0.93 m (5 risers); the spec's 1.10 m / 6 risers is within the
  photo's error — keep 1.10 (HABS shows more steps), but check the column pedestals don't
  look stubby.
- Side ground-floor windows: the 1930s SE card suggests sills nearer 1.4 m than 2.0 m;
  keep 2.0 under the jail-bars guess.
- The south wall sits on the Court St line, so the whole south side is seen from Main St
  (looking down Court St): give it the same window detail as the front, not "simpler".

### Hunterdon County Offices / Hall of Records (69–71 Main St)

**Status:** **in scene** (scene-integrator, 2026-11-03): GLB at (−17.71, 0.02, −27.87), rotation 0 90 0, lightmap intensity 1.1299; three 1.6 m walks to the stoops (z −24.07, −27.87, −31.67) replace the old single path; all front paths merged into one mesh (`ground-patches`, 1 draw call). Props from the integrator notes **not added yet** (draw-call budget): low iron post-and-rail fence, ~2 m board fence to the courthouse wing, shade tree before the south half (curb tree `tree-west-3` at z −24 stands there already), telegraph pole. Earlier: reviewed, round 1: **PASS** (reviewer, 2026-11-03). Loads clean in the browser viewer
(8,624 tris, 10 meshes, no errors; brick baseColorFactor survives `baked-lighting`); bay rhythm, 3 stoops, roof
arch, string course, sign panel and brackets match the 1908/1912 cards; no lightmap blotches or seams. Minor notes:
the roof arch is a little rounder than the 1908 card's segmental arch; ~1/3 of the lightmap is an unused black block
(not sampled by any face). Next: scene-integrator. Earlier: built (blender-builder, 2026-11-03): `assets/models/county-offices.glb` (8,624 triangles,
10 materials, 2.2 MB, TEXCOORD_0 + 1, brick tint as glTF baseColorFactor), `assets/textures/county-offices-lightmap.jpg`
(2048², **LIGHTMAP_SCALE 1.1299**), scripts `tools/blender/county_offices.py` + `county_offices_bake.py` +
`county_offices_preview.py`, source `assets/models/source/county_offices.blend`, previews
`assets/models/previews/county-offices-{front,three-quarter-ne,three-quarter-se,detail,match-1908,match-1912}.png`.
Simplified: brick voussoir rings not modelled (flush brick; keystones and frames only); north-inner upper window
stands on the sign panel (sill 5.40 instead of 5.20); side/rear arches 6 segments; no rust streaks in the grime.
Next: reviewer. Earlier: assets ready (asset-scout, 2026-11-03): new `county-offices/stone_buff.jpg` (Poly Haven
`scuffed_cement`, shifted to #CDBFA2, tile 1.6 m) + tinted `trim_paint_drab.jpg`, `roof_tin_redbrown.jpg`,
`door_varnish_dark.jpg`; reuse `polyhaven/red_brick.jpg`, `polyhaven/trim_paint_cream.jpg`,
`courthouse/rock_wall_08.jpg`. Next: blender-builder.

**What it is**: the county Hall of Records (county clerk and surrogate), built 1870–71, Italianate,
red brick, 2 storeys, "originally built with three separate doorways each with its own steps,
remodeled in 1928" (Hunterdon County Historical Society). So the 1920 state is the **original
1870 front with three stoops**; anything later (1928 enlargement, today's look) is not ours.
The map shows **one building** (one pink block, numbers 69 and 71, an interior "WALL 1ST ONLY"
partition), not two, so this spec covers the whole block. Next building north is the frame
house at 65 Main (separate spec later).

**Orchestrator decisions** (settled from the photos/map; owner to check later)
1. **One building, 13.9 × 15.2 m**, front wall 7.4 m behind the property line (map). The
   placeholder (z −36.2 … −20.8 at x −17.6) is ~0.6 m too far north; move it (see Placement).
2. **Front: 7 openings on the ground floor, W-D-W-D-W-D-W**, three round-arched doors each
   with its own stoop (walking-tour text "three separate doorways each with its own steps";
   1908 NE card shows 7 ground openings, 1906/1912 cards show the north and centre doors and a
   door near the south end). Upper floor: 4 single windows over the ground windows plus a
   **paired arched window in the centre** (1906, 1908, 1912 cards).
3. **Curved (segmental) central roof arch** with a round oculus, rising above the bracketed
   cornice over the centre bay (all eight views; Goodspeed lists it among Main St "roof arches").
4. **Paired scroll brackets** on a deep wooden cornice, front and both sides (1906/1908 cards).
5. **Shutters on the ground-floor windows only** (front and sides), open, cream; none upstairs
   (1908 sepia, 1909, 1912).
6. **No awnings.** Striped awnings appear in 1906/1908 only; 1909 and 1912 have none.
7. **One plain pale stone panel** on the string course under the north inner upper window,
   **no lettering** (it carried "DENTIST" 1909–12; the 1920 tenant is unknown).
8. **Raised basement**: rough stone foundation 1.2 m high with small segmental basement windows;
   first floor at 1.2 m, reached by 7-riser stoops with black iron railings (1906, 1912 close-ups).
9. **Stoops, string course, sills, keystones: pale buff stone** (they read light in the sepia
   cards and white in the 1908 colour card — not brownstone like the courthouse steps).
10. **Roof: low hipped roof (~18°), painted tin, dark red-brown**; it only shows as a dark edge
    behind the cornice (1908 sepia NE view). **No chimneys** — none show on the full north
    roofline in the 1908 NE card. Sanborn wall symbols (see Sources) are not modelled.
11. **Triangle class: ordinary building (≤ 10k)** — it is ornate (brackets, roof arch,
    stoops, railings), but it isn't one of the two project landmarks and it's seen mostly from
    the street. The ornament fits in 10k with low-poly brackets and simple railings.
12. Front yard: lawn, three paved walks to the stoops, low iron post-and-rail fence along the
    sidewalk (1909 and 1912, the views closest to 1920). The 1906/08 views show it paved;
    these are integrator items, not part of the model.

**Sources**
- Map: 1921 Sanborn **sheet 2**, pink (brick) block labelled "COUNTY OFF'S", "2" storeys and
  "28'" on both halves; street numbers **69, 71** (73 = courthouse below). Pixel box
  **x 3164–3456, y 6232–6498** (front wall x 3456; rear 3164; north 6232; south 6498).
  Internal E–W line at y 6326 marked "WALL 1ST ONLY" (ground-floor partition only: ignore).
  An uncoloured **dashed line** runs the full front at x ≈ 3463–3468 (0.4 m outside the wall):
  probably the stone stoops/area edge; stoops are modelled from photos instead. Wall marks:
  "12 12" (12-inch brick walls, both storeys) and asterisk-like symbols on the N and S walls
  at x ≈ 3250 and 3395 (meaning unclear; perhaps flues, not visible in photos). No rear wing.
  Main St property line x ≈ 3600. Courthouse north wing (yellow, "1") at y 6567–6620.
- Photos (all `assets/photos/reference/`, local only, never commit):
  - **Primary: `flmngtncntybldngsvuof08.jpg`** (1908, sepia, from the NE across Main St):
    whole front in perspective + north side; clearest bay rhythm, cornice brackets, roof arch,
    string course and the sign panel. Use for bay layout and proportions.
  - `flmngtnhtdncntycrtandbldg05.jpg` (1905) and `flmngtncntycourthsview06.jpg` (same view,
    postmarked July 10, 1906; from the NE, nearer frontal): north half of the front close up —
    arched door with a window either side, shutters, basement window, string course, panel;
    used for heights (≈ 59 px/m at the north corner of the 1906 copy).
  - `flmngtncrthouspublcbldg08.jpg` (1908, tinted colour, NE): red brick, pale string course
    and panel, light grey cornice, cream shutters, grey stone stoops; awnings (omit).
  - `flmngtncourthsandsurrogateoffice.jpg` (c. 1908, NE, sepia; "Court house and Surrogate
    office"): confirms this is the Surrogate's/county office; north side brick wall; telegraph pole.
  - `flemington_-_county_building_-_1912.jpg` (1912, sepia, from the SE) and
    `flmngtnhtncountybldg08.jpg` / `flmngtncountybldnganddentistoffice09.jpg` (1908/1909 tinted
    versions of the same SE view): **south side** (shuttered arched windows, rough stone
    foundation with a segmental basement window), centre and north stoops with railings,
    "DENTIST" panel, board fence between this building and the courthouse wing, lawn with a
    low post fence. Closest dated view to 1920 → use it for the stoops and the south side.
  - `flmngtncountycrthousvu09.jpg` (1909, colour): only the SE corner at the far right edge.
  - HABS (`habs/`): no photo of this building (the courthouse sheets don't show it).
- Web: Hunterdon County Historical Society walking tour
  (https://hunterdonhistory.org/wp-content/uploads/2018/08/Flemington-TRAIL-online8-1.pdf,
  p. 4: "71 Main Street, Hall Of Records (1870)… fine Italianate structure, originally built with
  three separate doorways each with its own steps, was remodeled in 1928… 'common' bricks used
  on the sides"); Clarke Caton Hintz (https://clarkecatonhintz.com/?p=1051: "erected in 1870…
  in 1928 expanded to its current configuration"; later repairs to "roof and cornice");
  Goodspeed Histories (https://goodspeedhistories.com/roof-arches-part-one/: "Hall of Records at
  71 Main St. (1871)" keeps its roof arch). NRHP nomination PDF is a scan without text (not used).

**Placement** (west side, front faces east onto Main St)
- Entity position = centre of the front (brick) wall face at grade: **(−17.71, 0.02, −27.87)**,
  `rotation="0 90 0"` (replaces the placeholder at (−17.6, 0, −28.5)). y 0.02 = lawn level
  (`lawn-west` is at 0.015; sidewalk top 0.15).
- Front wall x −17.71 (7.41 m behind the property line x −10.3); rear wall x −32.98;
  north wall z −34.80; south wall z −20.94 (3.27 m clear of the courthouse wing at z −17.67).
  Stoops reach x ≈ −15.3; cornice overhangs to x ≈ −17.0.
- Blender local frame: front −Y, origin at the front wall face, **+X = north**, z = 0 = grade.
  Body x −6.95 … +6.95, y 0 … 15.21. Stoops y −2.4 … 0. Sun "to sun" vector (−0.40, 0.90, 0.36).
- Stoop centres in the scene: z −24.07 (south door), −27.87 (centre), −31.67 (north door).

**Massing**
- Body: 13.9 m wide (front, map 266 px) × 15.21 m deep (map 292 px = 50 ft), 2 storeys
  + raised basement. Flat front, no projections except stoops, cornice and roof arch.
- Levels (photo estimates, 1906 card at the north corner + map "28'"): grade 0; stone
  foundation 0 → 1.20; first floor 1.20; second floor ≈ 5.0; frieze 7.75 → 8.25;
  **cornice top 8.6 m** (map 28' = 8.53 m); cornice overhang 0.7 m on front and sides,
  0.4 m at the rear.
- Roof: **low hip, 18°**, from the cornice line (8.6) to a short E–W ridge ≈ 10.8 m
  (13.9 m span → rise 2.25 m); ridge length ≈ 1.3 m. Barely visible from the street (guess).
- **Roof arch** over the centre bay: a brick parapet 0.4 m thick standing on the front wall,
  segmental arch from ±2.6 m at 8.6 m to a crown of **10.8 m** at x 0 (1905/1912 cards: rise
  1.8–2.7 m; average). The hip roof meets its back.
- Ground floor walls 0.30 m thick (12-inch brick, map): window/door reveals 0.20 m deep.

**Elevation details (1920 state)**
- **Front (east) ground floor**, openings centred at x = −5.5, −3.8, −2.1, 0, +2.1, +3.8, +5.5
  (W D W D W D W, symmetric; 1908 NE card + walking-tour text):
  - 4 windows at ±2.1, ±5.5: 1.0 × 2.35 m, sill 1.75, **round-arched head**, crown 4.10;
    2/2 double-hung sash, light-painted frames; brick voussoir arch (0.25 m ring) with a pale
    stone keystone; pale stone sill 1.2 × 0.12, projecting 0.06. **Shutters**: 2 open panelled
    leaves per window, each 0.5 × 2.35 (with arched top cut square for simplicity), cream,
    0.04 thick, standing 0.03 off the wall.
  - 3 doors at 0, ±3.8: opening 1.15 m wide, threshold 1.20, round-arched crown 4.10;
    semicircular fanlight (radiating bars) above a transom bar at 3.55; double-leaf panelled
    doors (upper glazed panels) 1.15 × 2.35, dark varnished brown; brick arch + keystone as
    windows; set 0.20 m into the wall.
  - Basement windows: under each front window, segmental-headed 0.9 × 0.5 m, sill 0.35,
    dark glass behind a 3-bar iron grille (1906, 1912 cards), in the stone foundation.
- **String course**: pale stone band 0.22 m high, projecting 0.08 m, top at 5.05 m, full front
  and both sides (1906/1908 cards; it doubles as the upper sill line).
- **Front upper floor**: single windows at ±2.1 and ±5.5: 0.9 × 2.05 m, sill 5.20, round-
  arched, crown 7.25; 2/2 sash; brick arch + keystone; no shutters. **Centre: paired window**
  — two round-arched lights 0.75 × 2.05 separated by a 0.25 m brick mullion (overall 1.75 m),
  same sill/crown, one stone sill across both. **Sign panel**: plain pale stone panel
  1.5 × 0.35 m standing on the string course under the window at +2.1 (north inner), 0.05 proud.
- **Cornice**: frieze band 7.75 → 8.25 (brick, flush); moulded wooden cornice 8.25 → 8.6
  with 0.7 m soffit overhang; **paired scroll brackets** (each 0.9 high × 0.6 deep × 0.18 wide,
  pair spacing 0.35 m) at: both front corners (wrapping), x ±4.6, and the two ends of the roof
  arch (±2.6); small square dentils/blocks between optional. Main cornice is **interrupted**
  between x −2.6 … +2.6 where the roof arch rises.
- **Roof arch**: tympanum in brick; arched moulded cornice following the arch (0.35 m deep
  profile, 0.45 m projection), terminating on the bracket pairs at ±2.6; **round oculus**
  Ø 0.8 m, centre (0, 9.3), pale stone ring 0.12 m, dark glass. Back of the arch: plain brick.
- **Stoops** (3, identical): pale buff stone, solid block with closed cheek walls; 1.6 m wide,
  **7 risers × 0.171 m** (to 1.20), top landing 0.8 m deep in front of the door, 6 treads
  × 0.27 m → projects 2.4 m (y −2.4 … 0). **Iron railings** both sides: black, 0.9 m high
  above the nosing line, square newel post at the bottom (0.08 × 0.08 × 1.0), top + bottom rail,
  vertical pickets every 0.15 m (thin 4-sided bars, 0.02 m), following the slope and the
  landing; return to the wall.
- **South and north sides** (common brick, same courses), 4 bays at y = 2.0, 5.7, 9.4, 13.1:
  ground windows as the front (with shutters), upper windows as the front singles, basement
  windows under the ground windows. String course and cornice with paired brackets at both
  corners and at y ≈ 3.85, 7.55, 11.25 (between bays). Foundation as the front.
- **Rear (west) wall** (not seen in any photo; guess): 3 bays of plain round-arched windows on
  both floors (no shutters), a plain back door at ground level with a 4-riser wooden step,
  plain cornice without brackets (overhang 0.4).
- **Foundation**: rough coursed grey-brown stone, 0 → 1.20 m, flush with the brick above, a
  0.05 m chamfered stone water-table cap at 1.20 m. Extend 0.2 m below z 0 (hidden skirt) so
  the model never floats on the slightly uneven lawn.
- No chimneys, no awnings, no signage, no flagpole, no lamps on the building (see decisions).

**Materials & colours (1920)**
- Walls: red pressed brick on the front, slightly duller "common" brick on the sides and rear
  (≈ #8E3F2C front, #87452F sides; same texture, tint only). Thin light mortar.
- Cornice, brackets, arch cornice, window frames and sash: painted wood, **light warm grey /
  stone drab** (≈ #BDB4A0) (1908 colour card). Shutters: cream (≈ #D9CFB4).
- String course, sills, keystones, oculus ring, sign panel, stoops: **pale buff sandstone**
  (≈ #CDBFA2).
- Foundation: rough grey-brown rubble/coursed stone.
- Doors: dark varnished brown (≈ #3A2A1F). Glass very dark. Railings and grilles: black iron.
- Roof: tin painted dark red-brown (≈ #5A3E34).
- Textures — reuse: `polyhaven/red_brick.jpg` (walls, 1.4 m, tinted per wall), `polyhaven/
  trim_paint_cream.jpg` (cornice, brackets, frames, shutters; 2.0 m; tint drab or cream),
  `courthouse/rock_wall_08.jpg` (foundation, 1.8 m), `polyhaven/metal_plate_02.jpg` (roof, 2.0 m,
  tinted), `polyhaven/wood_table_worn.jpg` (doors, 0.8 m, tinted dark). Sash/glass/iron: plain
  colours as in the courthouse bake.
  **New for asset-scout** (Poly Haven CC0, 1K colour, 1 map): **smooth pale buff sandstone /
  dressed limestone** (fine-grained, no strong blocks or joints), tile ~1.5 m — for the
  string course, sills, keystones and stoops. Fallback if none fits: reuse
  `courthouse/stucco_offwhite.jpg` tinted buff.

**Weathering**: soot darkening under the cornice soffit and on the brick just below it; dark
streaks below each stone sill and keystone; brick darker and greenish in the 0.3 m above the
foundation (damp); stoop treads worn and darker in the middle; rust streaks from the railing
feet; paint slightly chalky on the brackets. A cared-for public building: subtler than the hotel.

**Budget**: **ordinary building, hard cap 10k triangles, target ~8.5k**: walls with openings
~1.8k, ~36 arched windows/doors with frames + sash ~3.4k (rear ones simplest), brackets
(12 pairs = 24 brackets, ≤ 40 tris each as profile extrusions) ~1.0k, roof arch + cornices ~0.8k, 3 stoops with railings
~1.2k (pickets as 4-sided bars, ≤ 40 per stoop), shutters/sills/basement windows ~0.6k, roof
~0.1k. 5 reused + 1 new 1K colour texture, one 2K lightmap `assets/textures/county-offices-lightmap.jpg`.
Files: `tools/blender/county_offices.py` + `county_offices_bake.py`,
`assets/models/source/county-offices.blend`, `assets/models/county-offices.glb` (≤ 5 MB),
previews `assets/models/previews/county-offices-*.png`. ≤ 10 materials.

**Acceptance checks for the reviewer**
1. Footprint 13.9 × 15.2 m, plain rectangle, no rear wing; origin at the centre of the front
   wall face at grade, front faces −Y, +X = north.
2. Front ground floor reads **W-D-W-D-W-D-W**: three round-arched doors (centre and ±3.8 m),
   each with its **own 7-riser stone stoop and black iron railings**; four shuttered arched windows.
3. Upper floor: four single round-arched windows aligned over the ground windows plus a
   **paired arched window in the centre**; no shutters upstairs.
4. **Curved roof arch with a round oculus** rises over the centre bay to ≈ 10.8 m; the main
   cornice stops at its ends on paired brackets.
5. Bracketed cornice top 8.6 ± 0.2 m above grade, overhang ≈ 0.7 m, **paired scroll
   brackets** at the corners and between bays on front and sides.
6. Pale stone string course at ≈ 5 m running round front and both sides; pale sills and
   keystones; one plain panel on the string course under the north inner upper window.
7. Raised rough-stone basement ≈ 1.2 m with small basement windows; first floor ≈ 1.2 m.
8. Red brick walls, light drab cornice, cream shutters, dark doors; low hip roof hardly visible
   from the sidewalk; no chimneys, awnings or lettering.
9. ≤ 10k triangles, GLB ≤ 5 MB, 1K colour maps, 2K lightmap, TEXCOORD_0 + 1. With the WSW sun
   the front is in shade: stoops, shutters and window reveals must still read (bounce light,
   not black); the south side is sunlit and shows bracket and stoop shadows.

**Integrator notes (scene, not the model)**
- Move `#county-offices` to **(−17.71, 0.02, −27.87)**, rotation 0 90 0, GLB + lightmap.
- Replace the single front path at (−13.4, −28.5) with **three walks** (≈ 1.6 m wide) from the
  sidewalk (x −10.3) to the stoop feet (x ≈ −15.3) at z −24.07, −27.87, −31.67.
- Later props (1909/1912 cards): low iron post-and-pipe-rail fence along the property line
  with gaps at the walks; a vertical-board fence ≈ 2 m high across the gap between this
  building's SE corner and the courthouse north wing; a large shade tree in front of the south
  half; telegraph pole at the curb (1906). The horse fountain stands before the courthouse wing.

**Pure guesses (owner to check)**
1. Exact door/window positions on the south half of the front (perspective in the cards;
   symmetric layout chosen).
2. Roof form, pitch and material (low hip, tin) — never seen clearly.
3. No chimneys; the Sanborn wall symbols at 4.4 m and 11.9 m from the front are unexplained.
4. Rear wall layout and back door — not in any photo.
5. Side walls have 4 bays — only 2–3 are visible in any one view.
6. Colours of cornice (light drab) and stone trim (pale buff) come from one hand-tinted
   card and the sepia tones.
7. Stoop width/depth and railing pattern simplified (photos show ornamental cast-iron rails).
8. Basement window grilles.

### Wurts Law Office (59 Main St)

**Status:** in scene (scene-integrator, 2026-11-03): `#wurts-law-office` at (−14.95, 0.02, −68.69), rotation 0 90 0, GLB + baked lightmap (intensity 1.1647), replacing the kit placeholder; front path now `-12.5 -68.69 4.5 1.2` (sidewalk to 0.1 m under the step at x −14.65). No console errors; loaded bounds x −24.23 … −14.65, z −71.36 … −66.02, y −0.18 … 6.52 (no float, no z-fight with lawn or path). Draw calls / triangles: start view 162 / 61.5k → 160 / 69.0k. Screenshot `assets/models/previews/wurts-law-office-in-scene.png`. Shaded east front reads slightly cooler than the warm cream 65 Main, but acceptable next to its neighbours. Earlier: reviewer round 1: **PASS** (2026-11-03): GLB loads in the browser viewer with no errors (7,627 tris, 5 materials, 1.24 MB, TEXCOORD_0+1, 4 × 1K JPEG, 1K lightmap clean); matches both HABS views. Minor notes only: the shaded east front reads slightly cool/grey, the wreaths look octagonal up close, the chimney may sit ~0.3 m too far forward. Next: scene-integrator. Earlier: built and baked (blender-builder, 2026-11-03). Asset-scout skipped (nothing new needed; the four reused textures confirmed; grey copy `wurts-law-office/planks_grey.jpg` made by `tools/prepare_wurts_textures.py`). `assets/models/wurts-law-office.glb`: 7,627 triangles, 5 materials, 1.2 MB; lightmap `wurts-law-office-lightmap.jpg` 1024² (no seams seen, 2048 not needed), LIGHTMAP_SCALE 1.1647; previews `assets/models/previews/wurts-law-office-*.png`.

**What it is**: the Alexander Wurts (a.k.a. Samuel Southard) law office, a tiny 1-storey frame
office built c. 1811 as a plain clapboard building and remodelled c. 1840 by builder Mahlon
Fisher into a Greek Revival "temple" with a 4-pillar portico, a deep entablature with carved
wooden wreaths in the frieze and a flat roof. Wurts used it 1820–1881. In the **late 1920s**
the Women's Club turned it into a public restroom; the **west (rear) T-wing seen in HABS is a
later addition** (HABS data form: "T-shaped… western wing is an addition"). The 1921 map
shows only a small rear lean-to, so the 1920 state is the plain rectangle + portico.

**Orchestrator decisions** (settled from the photos/map; owner to check later)
1. **Footprint: 4.70 m wide × 8.0 m deep** (portico 1.6 + body 6.4). The map gives 8.0 m total
   depth (body 7.06 + front strip 0.89) but only **4.12 m width**; at 4.12 m the HABS front would
   have a 1.6–1.9 m tall, 0.6 m wide door — impossible. The two HABS photos together (front
   width ÷ height 1.11; side length ÷ height 1.86, perspective-corrected) give W ≈ 4.75 m and
   H ≈ 4.4 m when the side length is the map's 8.0 m; the door then comes out 0.78 × 2.2 m and
   the side clapboard exposure ≈ 0.2 m. Width kept centred on the map's centre line.
2. **Portico 1.6 m deep, not the map's 0.89 m strip**: in the HABS south photo the portico is
   0.25 × the body length (anta to pillar front), and a front-photo capital-height parallax check
   gives 1.6–2.2 m. The map's front line (porch edge) is kept as the model's front.
3. **No rear T-wing** (HABS data: later addition; not on the 1921 map). Instead a small
   1-storey **frame lean-to at the rear**, 2.9 × 1.1 m (map), low detail.
4. **Flat roof** (HABS data form) behind the entablature, tin (map "o" roof symbol); not visible
   from the street.
5. **One interior brick chimney** rising ~2.1 m above the cornice, south of centre (both HABS
   photos). Kept for 1920: a stove-heated office needed one; nothing suggests it is later.
6. **Colours: white paint all over, dark green louvred shutters, open** (HABS shows white with
   dark shutters; standard for a Greek Revival office of the period). **Door: same dark green**
   (one material shared with the shutters, saves a draw call; the HABS white door may be a
   later replacement).
7. **No signage** (the HABS "COUNTY SUPERINTENDENT OF SCHOOLS" board is mid-20th-century; the
   1920 occupant is unknown). No house number, lamps or awnings.
8. **Square pillars, plain shafts, moulded capitals** ("square, with egg and dart molding on
   capitals": HABS data); egg-and-dart is not modelled, only a stepped capital profile.
9. **Material count 5** (see Budget): one white paint for all painted wood (walls, clapboard as
   geometry, pillars, entablature, wreaths, dentils, sash, casings), one dark green (shutters,
   doors), plain dark glass (no texture), red brick (chimney), one grey (porch deck, step,
   foundation, roofs). **No new textures.**
10. **Ordinary building**, target ~6k triangles (hard cap 10k); lightmap **1024²** is enough
    for a building this small (2048² only if seams show).

**Sources**
- Map: 1921 Sanborn **sheet 2**, yellow (frame) "OFF." labelled "1" storey, street number
  **59** (between the 3-storey brick block 57 to the north and the frame house 65 to the south).
  Pixel box (line centres): body **x 3356–3491.5, y 5542–5621.5**; front strip ("1", "o")
  x 3491.5–3508.5 across the full width; rear lean-to (yellow, "1") **x 3334.5–3356,
  y 5552.5–5607.5**. "o" = slate/tin roof on body and front strip. Main St property line
  x 3600. Lot lines y 5460 (north) and 5787 (south). No height note.
- Photos:
  - **Primary: `habs/wurts-law-office-east-front.jpg`** (HABS NJ-772-1, mid-20th c., probably
    1960s–70s; public domain): straight-on east front. Use for the front proportions, pillar
    spacing, entablature layers, wreath count (7), window/door layout, chimney.
  - `habs/wurts-law-office-south-side.jpg` (HABS NJ-772-2, same date, from the SE): south side —
    2 shuttered windows, a mid-side pilaster, dentil course, 9 wreaths along the side frieze,
    portico depth, chimney; at the far left the later T-wing (do not build).
  - West Jersey History photos (`assets/photos/reference/`, all 32 checked on contact sheets):
    **none shows the law office** (the closest, `flmngtnmainstrycolrvu10.jpg` and the 1907
    "business blocks" card, show other buildings).
- Web: HABS NJ-772 data form (https://tile.loc.gov/storage-services/master/pnp/habshaer/nj/nj0000/nj0072/data/nj0072data.pdf:
  "ca. 1830, Mahlon Fisher, builder… Frame, with flush siding on east facade and clapboards on
  other facades… T-shaped; 1-story; 1-story, columned portico on east front; flat roof… Large
  entablature with dentilled architrave and simple projecting cornice, frieze decorated by
  carved wood wreaths; portico columns are square, with egg and dart molding on capitals…
  Western wing is an addition"); HCHS walking tour
  (https://hunterdonhistory.org/wp-content/uploads/2018/08/Flemington-TRAIL-online8-1.pdf:
  "59 Main Street, Samuel Southard Law Office (1811)… Mahlon Fisher updated the simple
  clapboard structure to its current Greek Revival style in 1840… opened it for a time in the
  late 1920's as a women's public restroom"); The History Girl
  (https://thehistorygirl.com/2013/01/23/leaving-his-mark-in-flemington/: four square columns,
  egg-and-dart capitals, carved wooden wreaths = Fisher trademark); Clarke Caton Hintz
  (https://clarkecatonhintz.com/project/samuel-lewis-southard-law-office/: "originally built as a
  simple, clapboarded office", later Greek Revival); Wikipedia, Flemington Historic District
  (https://en.wikipedia.org/wiki/Flemington_Historic_District: Wurts office 1820–1881).

**Placement** (west side, front faces east onto Main St)
- Entity position = centre of the portico front line (pillar front faces / porch edge) at
  grade: **(−14.95, 0.02, −68.69)**, `rotation="0 90 0"` (replaces the placeholder at
  (−15.2, 0, −68.8)). y 0.02 = lawn level.
- Portico front x −14.95 (map px 3508.5; **4.69 m** behind the property line x −10.26);
  front wall x −16.55; rear wall x −22.95 (map 3356 → −22.98); lean-to to x −24.05.
  North wall z −71.04, south wall z −66.34. The step and cornice reach x ≈ −14.65.
- Neighbours: brick block 57 Main to the north (front x ≈ −12.35, i.e. 2.6 m further east;
  south wall z ≈ −77.2, 6 m clear); frame house 65 Main to the south (north wall z ≈ −55.7,
  10 m clear). Lot lines z −75.0 (north) and −58.0 (south). Nothing within 5 m of the office.
- Blender local frame: front −Y, origin at the portico front at grade, **+X = north**, z = 0 =
  grade. Portico y 0 … 1.6; body x −2.35 … +2.35, y 1.6 … 8.0; lean-to x −1.35 … +1.55,
  y 8.0 … 9.1. Step y −0.30 … 0. Sun "to sun" vector (−0.40, 0.90, 0.36).

**Massing**
- Body + portico: one rectangle 4.70 × 8.0 m under one flat roof and one continuous
  entablature (decision 1–2). Body walls 6.4 m deep; the portico is the front 1.6 m, open on
  the front and recessed between the side walls' front ends (the side walls stop at the
  front wall; the portico sides are open between the corner anta and the outer pillar).
- Levels above grade (front photo at 102.7 px/m on the pillar plane; checked against the
  side photo): porch floor **0.30**; pillar base 0.30–0.42; shaft 0.42–3.08; capital
  3.08–3.30; architrave 3.30–3.52; dentil course 3.52–3.62; frieze 3.62–4.06; cornice
  4.06–4.42 → **cornice top 4.42 m**, overhang 0.30 m on front and sides, 0.20 at the rear.
- Roof: flat tin deck at 4.32 with a slight fall to the rear (2 %), hidden by the cornice
  (a 0.10 m parapet lip). Not visible from the street.
- Foundation: grey stone underpinning 0 → 0.25 under the walls, skirt to −0.2 (hidden) so it
  never floats; porch platform 0 → 0.30 with grey painted board facing.
- Rear lean-to: 2.9 (N–S) × 1.1 m (map), 1 storey frame, shed roof falling west from 3.0 to
  2.4 m, tucked under the main cornice (guess for heights).
- Chimney: brick, 0.60 (x) × 0.70 (y), centre **(x −1.0, y 4.4)**, from the roof to **6.5 m**,
  corbelled cap course 0.15 m projecting 0.05 (HABS front + side).

**Elevation details (1920 state)**
- **Portico pillars**: 4, **square**, 0.38 × 0.38 m, plain (no flutes, no panels), evenly
  spaced, centres x = **±0.72, ±2.16** (spacing 1.44; outer faces flush with the side walls),
  front faces at y 0 (centres y 0.19). Base: plinth 0.46 square × 0.12. Capital 3.08–3.30:
  necking band 0.04, flared echinus to 0.46, abacus 0.50 × 0.50 × 0.08.
- **Antae**: flat corner pilasters on the front-wall corners, 0.24 m on both faces, 0.04 proud,
  same base and capital profile as the pillars (seen in both photos).
- **Entablature** (front and both sides, continuous over the portico; rear plain): architrave
  plain fascia 0.22; **dentil course** 0.10 high (blocks 0.07 wide × 0.06 deep at 0.12 m
  centres) front and sides; frieze 0.44 flat; cornice 0.36: corona 0.26 with 0.30 overhang
  and a small top moulding 0.10. Porch ceiling flat at 3.30 (underside of the architrave).
- **Wreaths** (carved wood): ring Ø 0.34 m, tube Ø 0.07, projecting 0.05, centred in the
  frieze at 3.84 m. **Front: 7** at 0.72 m centres (x = −2.16 … +2.16). **Each side: 9** at
  0.8875 m centres, y = 0.35 … 7.45. Rear: none.
- **Front wall** (y 1.6, flush boarding, painted white), **W-D-W**:
  - Door centred: opening **0.78 × 2.20** (0.30 → 2.50), panelled (4 panels: two tall upper,
    two short lower), set 0.10 in; flat casing 0.08 m; head casing with a small cornice cap
    0.15 tall, 0.05 proud, top at 2.75. No fanlight or sidelights (HABS).
  - Windows at x **±1.32**: opening **0.78 × 1.70**, sill 1.05, head 2.75; **6/6 double-hung**
    (3 × 2 panes per sash), muntins 0.025; casing 0.07, head cap as the door; sill board 0.05.
  - **Shutters**: 2 louvred leaves per window, 0.36 × 1.70, open flat, 0.03 off the wall,
    dark green (louvres as texture/shallow grooves, not modelled slats). The outer leaf may
    touch the anta and the inner leaf the door casing — as in the photo.
- **Side walls** (south and north alike; north mirrored, no photo): clapboard, **0.20 m
  exposure** (16 courses 0.25 → 3.30), modelled as a stepped profile; corner boards 0.20 at
  the rear corners; a flat **pilaster 0.20 wide** at **y 4.4** from sill board to architrave
  (HABS south). Two windows as the front (with shutters) at **y 3.32 and 6.79**.
- **Rear wall** (guess, not seen): clapboard, blank; the lean-to covers the middle.
- **Lean-to**: clapboard as the sides, plain door 0.75 × 1.95 on its south face, one small
  2/2 window 0.6 × 0.8 (sill 1.2) on its west face; shed roof grey; no ornament.
- **Porch and step**: board deck at 0.30 from y 0 to 1.6 with 0.03 nosing; one step 0.15 high ×
  0.30 deep, **2.6 m wide**, centred (y −0.30 … 0) (HABS front).
- No railings, gutters/downpipes not modelled, no lamps, no sign.

**Materials & colours (1920)** — 5 materials
1. `white_paint` — all painted wood: walls, clapboard, pillars, antae, entablature, dentils,
   wreaths, casings, sash, porch ceiling, lean-to walls. Warm white ≈ #EEEBE2.
   Texture reuse **`courthouse/paint_white.jpg`**, tile 2.0 m.
2. `green_paint` — shutters and both doors, dark green ≈ #2F3B2C.
   Reuse **`polyhaven/door_paint_green.jpg`**, tile 0.8 m (tint darker if needed).
3. `glass` — plain colour, no texture: very dark blue-grey ≈ #1E2226, roughness 0.15.
4. `brick` — chimney. Reuse **`polyhaven/red_brick.jpg`**, tile 1.4 m.
5. `grey` — porch deck, step, porch facing, stone underpinning, flat roof, lean-to roof.
   Reuse **`polyhaven/weathered_planks.jpg`** tinted mid grey ≈ #8A877F, tile 2.0 m.
- **New for asset-scout: none.** All maps exist; asset-scout only needs to confirm the four
  files above and log nothing new.

**Weathering**: light — a small, cared-for white building. Dirt splash on the bottom 0.3 m of
walls and pillar bases; faint grey streaks under window sills and below the cornice corona;
soot on the chimney top; porch deck worn darker in front of the door; slight chalkiness on
the south (sunlit) side.

**Budget**: **ordinary building, target ~6k triangles, hard cap 10k**: walls with openings +
clapboard profile ~0.9k; 4 pillars + 2 antae with base/capital ~0.5k; entablature ~0.4k;
dentils (≈ 40 front + 2 × 66 sides, 10 tris each) ~1.7k; wreaths (25 × low-poly torus 8 × 4)
~1.6k; 6 windows + door with sash/casings ~0.6k; 12 shutters ~0.3k; porch, step, chimney,
roof, lean-to ~0.3k. **5 materials = 5 draw calls**, no new textures, one lightmap
`assets/textures/wurts-law-office-lightmap.jpg` (1024², 2048² only if needed). Files:
`tools/blender/wurts_law_office.py` + `wurts_law_office_bake.py`,
`assets/models/source/wurts_law_office.blend`, `assets/models/wurts-law-office.glb` (≤ 5 MB,
expect < 1 MB), previews `assets/models/previews/wurts-law-office-*.png`.

**Acceptance checks for the reviewer**
1. Footprint 4.70 × 8.0 m plain rectangle (no T-wing) plus a small rear lean-to 2.9 × 1.1 m;
   origin at the portico front at grade, front faces −Y, +X = north.
2. **Four square, plain pillars**, evenly spaced across the full front, outer faces flush with
   the side walls; portico 1.6 m deep with matching antae at the front-wall corners.
3. Front wall reads **W-D-W**: centred panelled door, two 6/6 windows with open dark-green
   louvred shutters.
4. Deep entablature (≈ 1.1 m) with a dentil course and **7 round wreaths** on the front frieze
   and **9 on each side**; cornice top 4.42 ± 0.15 m.
5. **Flat roof** — no gable or hip shows above the cornice; one brick chimney south of centre
   rising ≈ 2 m above the cornice.
6. Side walls clapboard with two shuttered windows and a mid pilaster; front wall smooth.
7. Porch floor ≈ 0.3 m with one wide step; all white except shutters/doors (dark green),
   brick chimney, grey porch and roof.
8. ≤ 10k triangles (target ~6k), **≤ 5 materials**, GLB ≤ 5 MB, TEXCOORD_0 + 1. With the WSW
   sun the front is in shade: pillars, shutters and wreaths must still read (bounce light, not
   flat grey); the south side is sunlit with clear shutter and cornice shadows.

**Integrator notes (scene, not the model)**
- Move `#wurts-law-office` to **(−14.95, 0.02, −68.69)**, rotation 0 90 0, GLB + lightmap;
  remove the kit placeholder.
- Front path (`#paths` ground-patches): replace `-12.6 -68.8 4.55 1.4` with
  **`-12.5 -68.69 4.5 1.2`** (sidewalk x −10.25 to x −14.75, 0.1 m under the step).
- Optional later (draw-call budget): one large shade tree just north of the portico at about
  (−14.3, −71.9) (HABS shows a big old trunk there; likely a mid-size tree in 1920 — guess).
  No fence known.

**Differences HABS (mid-20th c.) vs. 1920** (build 1920): HABS has the rear T-wing (wider than
the body on the south, with its own wreath frieze), the "County Superintendent of Schools"
board, a white door, shrubs and a concrete walk; possibly a raised grade around the porch.

**Pure guesses (owner to check)**
1. Exact width (4.70 m) — map 4.12 m vs photo; see decision 1.
2. North side layout (mirror of the south) and blank rear wall.
3. Lean-to heights, door and window; whether it was enclosed (map yellow = frame).
4. Door and shutter colour (dark green) and door panelling in 1920.
5. Porch floor height (0.30) and step size — the HABS ground may be higher than in 1920.
6. Chimney present in 1920 and its cap detail.
7. Front-yard tree and path width.

### Bank Building / Flemington National Bank (56–66 Main St)

**Status:** in scene (scene-integrator, 2026-11-03): GLB placed at (12.24, 0.15, −66.24), rotation 0 −90 0, lightmap intensity 1.1241; code-built placeholder replaced; front strip x 10.30–12.28 paved with one concrete box (`#bank-forecourt`, flush with the sidewalk top). Tested: no console errors, faces Main St, lightmap reads, stoops sit on the strip, north wall meets the Bloomfield Ave grade with no gap. Earlier: review round 2: PASS (reviewer, 2026-11-03): GLB 8,808 tris, 6 materials, 1.79 MB, 5 × 1K JPG, TEXCOORD_0+1; lightmap 2048², LIGHTMAP_SCALE 1.1241; loads in the review viewer with no console errors. Stone now reads mid grey, clearly darker than the pale trim (1908 colour card); chimney now shows above the SW cornice return; no regressions. Next: show the owner, then scene-integrator. Earlier: round-1 fixes applied (blender-builder, 2026-11-03): stone tinted to a mid cool grey (baseColorFactor 0.66/0.68/0.72), chimney raised to 13.20; re-baked and re-exported: 8,808 triangles, 6 materials, 1.79 MB, **LIGHTMAP_SCALE 1.1241**; all previews re-rendered. Next: reviewer round 2. Earlier: review round 1: FIXES (reviewer, 2026-11-03): GLB 8,802 tris, 6 materials, 1.79 MB, 5 × 1K JPG, TEXCOORD_0+1; lightmap 2048²; loads in the review viewer at intensity 1.1249 with no console errors, brick/trim colour factors survive. Proportions, 12 bays, 12.2 m cornice, roundels, bank entrance, shop fronts, awnings and lightmap all good; builder simplifications 1–7 accepted. Fixes: (1) stone ground storey too pale/cream, reads as bright as the trim; darken ~30% and cool it to mid grey (1908 colour card, 1907 card); (2) optional: chimney barely shows above the cornice, raise to ~13.2 m (1908 SW card). Next: blender-builder fixes, then review round 2. Earlier: built (blender-builder, 2026-11-03): `assets/models/bank-building.glb` 8,802 triangles, 6 materials (brick, stone, trim, glass, dark, awning), 1.79 MB, TEXCOORD_0 + TEXCOORD_1, one 2K lightmap `assets/textures/bank-building-lightmap.jpg`, **LIGHTMAP_SCALE 1.1249**; scripts `tools/blender/bank_building.py`, `bank_building_bake.py`, `bank_building_preview.py`; source `assets/models/source/bank_building.blend`; previews `assets/models/previews/bank-building-{front,three-quarter-nw,three-quarter-sw,detail,match-1907,match-1908}.png`. Next: reviewer. Earlier: assets ready (asset-scout, 2026-11-03): new `bank-building/stone_rockfaced.jpg` (Poly Haven `sandstone_blocks_05`, 1K, rock-faced coursed ashlar greyed to #A8A294, tile 3.0 m, ~7 courses of 0.34–0.47 m per tile; untinted source kept as `sandstone_blocks_05.jpg`); generated `bank-building/awning_stripes.jpg` (1K, red #9A4A3E / cream #DDD3BC 0.15 m stripes running along V, canvas weave + fading, seamless, tile 0.6 m across); reused unchanged and confirmed present: `polyhaven/red_brick.jpg` (1.4 m), `county-offices/trim_paint_drab.jpg` (2.0 m), `county-offices/door_varnish_dark.jpg` (0.8 m). Script `tools/prepare_bank_textures.py`; logged in SOURCES.md. Next: blender-builder. Earlier: spec written — auto-approved (owner away) (planner, 2026-11-03).

**What it is**: the 3-storey brick-and-stone "Bank Building" (also "Richards Building") on the
**SE corner of Main St and Bloomfield Ave**, built **1897** by William Richards on the site of
"Blackwell's Row"; the Flemington National Bank (chartered 1876) had its banking room in the
north end. A **first-floor fire on 9 Feb 1901** was repaired; the 1906–1908 cards show the
repaired building. HCHS: "classic brick and stone building… Multiple entryways have been changed
over the years" — so the 1920 state is the 1906–08 postcard state. In 1921 the map tenants are
(north → south) Bank (56), Men's Furnishings (58), Drugs (62), Boots & Shoes (64), Confectionery (66).
**The Post Office is not in this building**: the 1906/1907 cards ("Post Office – Richards Bldg /
Bank Building – Union Hotel") show the "P.O." awning on the 3-storey Italianate block **across
Bloomfield Ave to the north** (scene placeholder `bldg-48-52-main`, spec later).

**Orchestrator decisions** (settled from the photos/map; owner to check later)
1. **One model for the whole 56–66 block, 22.14 m frontage.** The map draws two brick parts
   with a party wall at 11.46 m from the north (56–58 is 20.32 m deep, 62–66 only 11.05 m), but
   every photo (1906, 1907, both 1908 cards) shows **one continuous 1897 facade** with the same
   bays, belt course and cornice from the Bloomfield corner to the frame building at 68. The
   L-shaped plan follows the map; the facade is one.
2. **Front wall 1.95 m behind the property line** (map: thin wall line at px 4032, street line
   3990–3995; the gap holds the stoops). Entity **(12.24, 0.15, −66.24)**, not the placeholder's
   (10.6, 0, −66.2). The strip between the sidewalk and the front is paved by the integrator.
3. **Bays: 12 equal upper bays on the front, 11 on the north (Bloomfield) side**, brick
   pilaster between every bay (1908 SW card: 12 third-floor windows counted; side bays look the
   same width as front bays in the 1906/07 cards). Ground floor = **6 bays of 2 upper bays each**
   between rock-faced stone piers (the piers line up with the map's partitions at 11.5, 14.7,
   17.7 m within 0.4 m).
4. **Ground storey of rock-faced grey stone on the front and the whole north side**, stone belt
   course at 4.3–4.6 m; red brick above (all cards). Upper windows: **2nd floor rectangular with
   pale stone lintels, 3rd floor round-arched**; **pale roundels** in the band above the arches,
   one over every second pilaster (1908 colour card shows one roundel per pair of windows).
5. **Bank front (north end)**: ground bay 1 = big bank window, ground bay 2 = **round-arched
   stone entrance with its own stoop and iron railings** (1906/1907 close views). The other four
   ground bays are **shop fronts with raised floors and small stone stoops** (1908 cards).
6. **Raised ground floor at 0.90 m** (5 risers) for bank and shops; small basement windows
   under the bank window and the north-side windows (1907 card: low openings under the sill line).
7. **Stoops perpendicular to the front**, inside the 1.95 m strip (bank stoop 1.8 m, shop stoops
   1.2 m) — the 1908 colour card shows sloping stone cheek walls coming out toward the street.
8. **Awnings: striped canvas awnings on the four shop bays only**, extended; none on the bank
   bays and **none on the upper windows** (1906–08 all show shop awnings; upper-window awnings are
   seasonal and costly). Faded red-and-cream stripes (1908 colour card). No lettering.
9. **Roof: shed roofs falling to the rear, hidden** behind the front and north cornices (1908 SW
   card: the south wall top steps down toward the back). **One chimney**, on the south wall near
   the front (1908 SW card); no others seen.
10. **South wall plain common brick, no openings** (it abuts 68 Main; 1908 SW card shows it blank
    above 68's roof). Cornice returns 0.8 m round the SW corner, then stops.
11. **North side cornice and frieze run the full 20.3 m** (it is a street front on Bloomfield
    Ave; only the front 4 bays are visible in the cards, the rest is hidden by the P.O. block).
12. **Colours**: front and north brick red-brown; stone light warm grey; cornice, frieze,
    lintels, sills, roundels, shop fronts and sash share one **pale drab stone/paint colour**;
    doors dark varnish. (Cards disagree — 1908 NW card: dark grey cornice, red brick; 1908 SW
    card: pinkish front — the pale-drab trim is the middle reading and saves a material.)
13. **Ordinary building, hard cap 10k triangles, target ~8.5k**, **6 materials** (see Budget).
    It is large but repetitive (identical bays); it is not one of the two project landmarks.
14. **Rear parts on Bloomfield Ave and in the back yard are not modelled** (outbuildings on hold;
    see Sources for what the map shows). The two rear walls are plain brick with simple windows.

**Sources**
- Map: 1921 Sanborn **sheet 2**, pink (brick) block, street numbers **56, 58, 62, 64, 66**,
  "3" storeys and **"40'"** on all units; wall marks "12 12 16" (north part) and "12 12 12" (south).
  Pixel lines (centres): **front wall x 4032**; street line x 3990–3995; **north wall y 5416**
  (on the Bloomfield Ave street line, y 5414); **south wall y 5841** (68 Main's north wall at
  5850); **party wall y 5636** (with a "‖" fire-wall mark, carried across the front strip to the
  street line, as is the lot line at 5841). **Rear of 56–58: x 4422; rear of 62–66: x 4244.**
  Partitions: dashed (non-structural) line between 56/58 at y 5530; "WALL 1ST ONLY" at y 5700 and
  5757. Not modelled (rear, low): 1-storey brick at x 4300–4422, y 5638–5690; 3-storey frame strip
  x 4245–4422, y 5690–5720; 1-storey brick/frame + stairs behind 66 (x 4245–4300, y 5740–5840);
  on Bloomfield Ave a 1-storey frame strip x 4422–4455, y 5418–5530, a 2-storey frame strip
  x 4422–4455, y 5530–5640 and a 1-storey brick wing x 4455–4570, y 5530–5640 with a porch.
- Photos (all `assets/photos/reference/`, local only, never commit):
  - **Primary: `flmngtnpobankunionhtl07.jpg`** (1907, sepia, "Post Office – Bank Building –
    Union Hotel", from the NW across Bloomfield Ave): NW corner, front 4 bays and north side 4
    bays sharp — rock-faced ground storey, belt course, pilasters, lintels, arched 3rd-floor
    windows, roundel, panelled frieze, modillion cornice, bank window, arched bank entrance with
    stoop and railings, shop awnings. Use for the vertical layout (≈ 31 px/m at the corner).
  - `flmingtnporichardsbldgunionhtl.jpg` / `flmngtnmainstrichardsbldgpo06.jpg` (1906, same
    viewpoint, "Richards Bldg"): same detail; confirms 4 bays per visible north-side stretch.
  - `flmngtnbankandpovu08.jpg` (1908, tinted, from the SW, west side of Main St): **whole front**
    — 12 upper bays, shop fronts with stoops, the plain red south wall with the chimney and the
    stepped-down coping; 68 Main (frame, 2 storeys) to the right; the P.O. block beyond Bloomfield.
  - `flmngtnpoandnatbank08.jpg` (1908, tinted, from the SW, closer): red brick, grey rock-faced
    ground storey and piers, pale lintels, **roundels between window pairs**, dark grey cornice,
    striped red/cream shop awnings and upper-window awnings, stone stoops with cheek walls.
  - Checked, **not this building**: `flmngtnmainstrycolrvu10.jpg` (1910; a 3-storey brick
    building with a hedge and brick, not stone, ground storey — probably the block north of
    Bloomfield Ave), `flemington_-_some_business_blocks_on_main_street_-_1907.jpg` and
    `flmgtnmainststores.jpg` (west-side blocks), all Union Hotel views (bank out of frame).
    No HABS sheet covers it.
- Web: HCHS walking tour (https://hunterdonhistory.org/wp-content/uploads/2018/08/Flemington-TRAIL-online8-1.pdf:
  "56 Main Street Bank Building (1897) This classic brick and stone building survived a first
  floor fire in 1901. Multiple entryways have been changed over the years."); Goodspeed Histories
  (https://goodspeedhistories.com/?p=23290: at "the south corner of the Main & Bloomfield
  intersection… a large building that once was headquarters for the Flemington National Bank";
  "The building that replaced Blackwell's Row was built by William Richards in 1897"); Bank Note
  History wiki (https://banknotehistory.spmc.org/wiki/Flemington_National_Bank,_Flemington,_NJ_(Charter_2331):
  9 Feb 1901 fire started in the Henry Richards building and spread to the bank building;
  chartered 1876); bank centennial booklet 1976 (https://www.butkus.org/information/flemington_nat_bank/flemington_national_bank-1976.pdf,
  via search snippet: "Main Street Office – Corner of Main & Bloomfield Avenue").

**Placement** (east side, front faces west onto Main St)
- Entity position = centre of the front (ground-storey stone) wall face at sidewalk level:
  **(12.24, 0.15, −66.24)**, `rotation="0 -90 0"` (replaces `#bank-building` at (10.6, 0, −66.2)).
  y 0.15 = sidewalk top (the front strip gets paved to that level).
- Front wall x 12.24 (1.94 m behind the property line x 10.30); north wall z −77.31 (0.3 m
  inside Bloomfield Ave's road edge z −77.6); south wall z −55.17 (68 Main's north wall
  ≈ −54.7); rear of the north part x 32.56, of the south part x 23.29; party wall z −65.85.
  Stoops reach x ≈ 10.45, awnings x ≈ 10.5, cornice x ≈ 11.5 — all inside the property line.
- Blender local frame: front −Y, origin at the centre of the front wall face at sidewalk level,
  **+X = south**, −X = north (Bloomfield Ave), z = 0 = sidewalk top. North part x −11.07 … +0.39,
  y 0 … 20.32; south part x +0.39 … +11.07, y 0 … 11.05. Walls skirt down to z −0.20 (the
  Bloomfield side ground is 0.15 lower). Sun "to sun" vector **(0.40, −0.90, 0.36)** (front is
  sunlit, north side in shade).

**Massing**
- L-shaped plan (map): north part 11.46 × 20.32 m, south part 10.68 × 11.05 m, both 3 storeys,
  **cornice top 12.20 m** (map 40' = 12.19 m) on the front and the whole north side.
- Levels (1907 card at the NW corner, ≈ 31 px/m, upper floors corrected for the low viewpoint):
  ground/shop floor 0.90; stone ground storey 0 → 4.30; **belt course 4.30–4.60**; 2nd floor
  ≈ 4.75; 3rd floor ≈ 7.60; pilaster caps 10.45–10.60; **frieze 10.60–11.45**; **cornice
  11.45–12.20**, projecting 0.75 m (front and north), 0.8 m return on the south and rear corners.
- Roof (hidden): north part shed from 11.40 at the front to 10.40 at the rear; south part 11.40
  → 10.60. Flat-ish, dark. Rear walls end in a 0.3 m coping above the roof's low edge.
- South wall coping follows the roof slope behind the cornice return. **Chimney** on the south
  wall: 0.90 (y) × 0.55 (x, set into the wall, flush outside), centre y 1.6, top **12.60**,
  plain with a 0.10 projecting cap course.

**Elevation details (1920 state)**
- **Front grid** (x from north −11.07 to south +11.07): corner piers 0.80 m; 12 bays at
  **1.712 m**; window centres x = ±0.856, ±2.568, ±4.280, ±5.992, ±7.704, ±9.416; pilasters
  (brick, 0.65 wide, 0.08 proud, 4.60 → 10.45, corbelled cap 10.45–10.60 proj 0.12) at
  x = 0, ±1.712, ±3.424, ±5.136, ±6.848, ±8.560; the corner piers run full height as pilasters.
- **Ground storey** (stone, rock-faced, face at y 0; 0 → 4.30): stone piers 0.80 wide at the
  corners and at x = ±3.424, ±6.848 and 0 (0.04 proud of the infill); clear bays 2.62 m:
  - **G1 bank window** (x −10.27 … −7.25): stone infill with one opening **2.0 × 2.5 m** (sill
    1.20, head 3.70), central mullion 0.12 and transom bar at 3.10 (4 lights), trim frame, stone
    lintel flush; basement window 1.2 × 0.45 below (sill 0.25), dark glass.
  - **G2 bank entrance** (x −6.45 … −3.82, centre −5.136): stone infill, **round-arched doorway
    1.5 m wide**, threshold 0.90, spring 3.05, crown 3.80, rock-faced voussoir ring 0.30 with a
    keystone; recessed 0.45; panelled double doors 1.5 × 1.9 (dark varnish, upper glazed panels),
    transom bar at 2.80, semicircular fanlight. **Stoop**: stone, 2.1 m wide, 5 risers × 0.18,
    4 treads × 0.30 (y −1.80 … −0.60) + landing y −0.60 … 0; stone cheek walls 0.25 thick with
    sloping tops; **black iron handrail** on each cheek (end posts 0.05 sq., one top rail).
  - **G3–G6 shop fronts** (centres x −1.712, +1.712, +5.136, +8.560): painted wood (trim) in
    the 2.62 m opening: stone plinth 0 → 0.90; **recessed entrance 1.0 m wide × 0.9 m deep**
    centred, half-glazed door 0.95 × 2.30 (0.90 → 3.20), transom to 3.60; display windows each
    side (0.81 wide, bulkhead panel 0.90–1.30, glass 1.30–3.20); 3-light transom band 3.20–3.60;
    plain fascia 3.60–4.30 (no lettering). **Stoop**: 5 risers, 1.0 m wide in the recess line,
    4 treads y −1.20 … 0, landing in the recess; stone cheek walls 0.20 each side, no railings.
    **G6** variant: entrance recess at the south side of the bay (display window 1.62 m on the
    north), with the store door at the back and a second door (upper floors) in the recess's
    south side wall.
- **Belt course**: stone, 4.30–4.60, projects 0.12, front and full north side.
- **2nd floor** (front 12, north 11): opening **0.95 × 1.95**, sill 5.00 (trim sill 0.08 thick,
  proj 0.06), head 6.95; **flat stone lintel** 1.25 × 0.30 (6.95–7.25), 0.04 proud, trim
  material; 1/1 double-hung sash, trim-colour frames, set 0.12 in.
- **3rd floor**: **round-arched** opening 0.95 wide, sill 7.75, spring 9.30, crown 9.775;
  1/1 sash with arched head; brick hood ring 0.15 wide, 0.05 proud; small trim keystone
  0.20 × 0.30; trim sill as below.
- **Roundels**: trim discs Ø 0.55, 0.06 proud (8-sided is fine), centre z 10.25, over
  pilasters x = ±1.712, ±5.136, ±8.560 (6 on the front, one centred over each ground bay) and
  on the north side over pilasters 1, 3, 5, 7, 9 (5).
- **Frieze** 10.60–11.45: trim (painted galvanised iron), flat, with shallow raised panels
  0.35 × 0.45, 0.02 proud, two per bay (≈ 0.86 m centres) on front and north side.
- **Cornice** 11.45–12.20: bed moulding 0.10; **modillions** 0.12 w × 0.20 h × 0.40 deep at
  0.57 m centres (3 per bay) under a corona projecting 0.75; top cap moulding 0.08. Front, full
  north side, 0.8 m returns at the SW and NE corners.
- **North (Bloomfield) side** (x −11.07; from front y 0 to rear y 20.32): NW corner pier
  0.80, 11 bays at **1.72 m** (bay centres y = 1.66 + 1.72·k), rear corner pier 0.60; upper
  floors as the front; ground storey rock-faced stone with one window per bay **0.95 × 2.60**
  (sill 1.00, head 3.60, trim frame, 2/2 sash) and a basement window 0.80 × 0.40 (0.15–0.55)
  under each. No door.
- **Rear walls** (east; never photographed): common brick, no ornament; north part 4 windows
  per floor, south part 3; segmental-headed 0.9 × 1.8 upstairs, 0.9 × 2.2 + one back door
  0.9 × 2.1 on the ground floor of each part; stone sills. **Courtyard face** of the north part
  (x +0.39, y 11.05 … 20.32): 2 plain windows on each upper floor.
- **South wall**: plain common brick, no openings, sloping coping, chimney (see Massing).
- Not modelled: gutters, downpipes, signs, lettering, upper-floor awnings, lamps, flagpole.

**Materials & colours (1920)** — **6 materials = 6 draw calls**
1. `brick` — walls, pilasters, hood rings, chimney, rear/south walls. Red-brown pressed brick
   ≈ #8A4030 (front and north), common brick ≈ #87452F (south, rear, courtyard; tint only).
   Reuse **`polyhaven/red_brick.jpg`**, tile 1.4 m.
2. `stone` — rock-faced ground storey, piers, infill, belt course, voussoirs, plinths, stoops,
   cheek walls. Light warm grey ≈ #A8A294. **New texture** (below), tile 3.0 m.
3. `trim` — everything painted or smooth-pale: cornice, modillions, frieze and panels, lintels,
   sills, keystones, roundels, shop fronts, bulkheads, fascias, window frames and sash.
   Pale drab ≈ #B5AC98. Reuse **`county-offices/trim_paint_drab.jpg`**, tile 2.0 m.
4. `glass` — plain colour, no texture, very dark blue-grey ≈ #1E2226, roughness 0.15.
5. `dark` — doors (dark varnish ≈ #3A2A1F), iron handrails, roof surfaces, chimney cap.
   Reuse **`county-offices/door_varnish_dark.jpg`**, tile 0.8 m.
6. `awning` — 4 shop awnings. Faded red ≈ #9A4A3E and cream ≈ #DDD3BC stripes, 0.15 m each,
   running down the slope. Texture `bank-building/awning_stripes.jpg` (1K) **generated locally**
   by a small Pillow script (`tools/prepare_bank_textures.py`: stripes + light canvas noise), tile
   0.6 m across the stripes. Not a download.
- **New for asset-scout** (Poly Haven CC0, 1K colour, **1 map**): **coursed rock-faced (quarry-
  faced) stone ashlar, light grey**, regular courses ≈ 0.45–0.55 m high, blocks 0.9–1.5 m long,
  bumpy faces and thin joints (not random rubble, not smooth sawn blocks); real-world tile ≈ 3 m.
  Save as `assets/textures/bank-building/stone_rockfaced.jpg`. Fallback if nothing fits: reuse
  `courthouse/rock_wall_grey.jpg` (tile 1.8 m). Asset-scout also makes `awning_stripes.jpg`.

**Weathering**: moderate (busy commercial block, 23 years old): soot under the cornice
corona and on the frieze; dark streaks under every lintel, sill and roundel; brick darker on
the shaded north side; grime and splash on the bottom 0.5 m of the stone and on stoop treads
(worn darker in the middle); soot round the chimney top; awnings sun-bleached on top and
slightly darker at the valance; a little rust under the handrail feet.

**Budget**: **ordinary building, hard cap 10k triangles, target ~8.5k**: walls with openings
~1.6k; 46 upper windows (frames + sash + glass, arched ones ≤ 70 tris) ~2.6k; 11 north ground
windows + 13 basement/rear/courtyard openings ~0.8k; pilasters + caps ~0.5k; 75 modillions as
simple blocks ~0.75k; cornice/frieze + 46 panels ~0.8k; 11 roundels ~0.2k; bank window,
entrance arch, 5 shop fronts ~0.8k; 5 stoops + rails ~0.4k; awnings, roof, chimney ~0.1k. If
over budget: flatten rear/courtyard windows to inset panels first, then drop frieze panels.
**6 materials**, 1 new + 1 generated + 3 reused 1K colour maps, one **2K lightmap**
`assets/textures/bank-building-lightmap.jpg` (the walls are large: 2K needed). Files:
`tools/blender/bank_building.py` + `bank_building_bake.py`, `assets/models/source/bank_building.blend`,
`assets/models/bank-building.glb` (≤ 5 MB, expect ~2 MB), previews
`assets/models/previews/bank-building-*.png` (incl. matches to the 1907 NW and 1908 SW views).

**Acceptance checks for the reviewer**
1. L-shaped plan: front 22.14 m; north part 20.3 m deep, south part 11.05 m deep; origin at
   the centre of the front stone face at sidewalk level, front −Y, **+X = south**.
2. Front reads as **one continuous facade with 12 equal upper bays** divided by brick
   pilasters; 2nd-floor windows rectangular with pale lintels, **3rd-floor windows round-arched**;
   6 pale roundels, one centred over each ground bay.
3. **Rock-faced grey stone ground storey** with a projecting belt course at ≈ 4.3–4.6 m on the
   front and the whole north side; red brick above.
4. Ground floor N→S: **bank window, arched bank entrance with stoop and black railings, then
   four shop fronts** with recessed doors, small stone stoops and **striped awnings** (none on
   the bank bays or upper windows).
5. Cornice top 12.2 ± 0.2 m with modillions and a panelled frieze, running along the front and
   the **entire Bloomfield (north) side**; short return on the south corner.
6. North side: 11 bays, same window pattern as the front, stone ground storey with tall windows
   and basement windows, no door.
7. South wall plain brick with **one chimney near the front**; no roof form visible above the
   cornice from the sidewalk.
8. Nothing crosses the property line: stoops end ≈ 1.8 m (bank) / 1.2 m (shops) in front of the
   wall; awnings ≈ 1.75 m.
9. ≤ 10k triangles, **≤ 6 materials**, GLB ≤ 5 MB, 1K colour maps, 2K lightmap, TEXCOORD_0 + 1.
   With the WSW sun the front is sunlit (pilaster, lintel, awning and stoop shadows visible); the
   north side is in shade but its windows and roundels still read.

**Integrator notes (scene, not the model)**
- Replace `#bank-building` with the GLB at **(12.24, 0.15, −66.24)**, rotation 0 −90 0,
  lightmap + LIGHTMAP_SCALE from the bake.
- **Pave the front strip**: one box x 10.30 … 12.24, z −77.31 … −55.17, top y 0.15, texture
  `polyhaven/sidewalk_concrete.jpg` (photos: paving runs up to the stoops). +1 draw call; the
  same box can later be lengthened south for 68 Main (front at map px 4040 → x ≈ 12.66).
- Expected draw-call change: kit placeholder (~6–7 calls) → GLB 6 + strip 1, i.e. about ±0.
- Optional later (budget): telegraph pole at the curb before the bank (1906), fire hydrant on the
  sidewalk near the Bloomfield corner (1907).

**Differences 1906–08 vs 1920** (build 1920): the upper-window awnings of 1907–08 are left
out; shop awning lettering is unreadable and omitted; the entrances may have changed by 1920
(HCHS) — the 1906–08 layout is kept as the best evidence.

**Pure guesses (owner to check)**
1. Exact storey heights above the belt course (low-viewpoint postcards; only the 40' total is
   measured).
2. North side beyond the first 4 bays (11 bays, all windows, no side door) and the cornice
   running its full length.
3. Rear and courtyard walls, rear windows and doors; roof slopes and heights.
4. Shop-front details (door recess, bulkheads, transoms) and the G6 upper-floor door.
5. Colours: brick tone, stone grey, one pale drab for cornice and trim, awning stripe colours.
6. Roundel placement on the north side and the frieze panel pattern.
7. Stoop sizes; railings only on the bank stoop.
8. Only one chimney.

### Nevius Store / Fulper's Dry Goods Building (78 Main St)

**Status:** **in scene** — scene-integrator placed the GLB at (10.30, 0.15, −7.33), rotation 0 −90 0, intensity 1.1072, replacing the code-built `#bldg-78-main` placeholder (id kept); side gaps show the ground, no floating or overlaps; committed and pushed (scene-integrator, 2026-11-03). Earlier: round-1 fixes applied — asset-scout skipped (no new downloads; reused red_brick, trim_paint_cream, door_varnish_dark, awning_stripes); blender-builder raised the 3rd-floor front windows (spring 8.95, crown ~9.40, hoods and end blocks raised; central section and quoins now to 9.50), tightened the cornice (bed moulding 9.50–9.58, frieze from 9.58; dentils 10.15, top 10.70 unchanged) and put the shop-front cornice on the dark material; re-baked and re-exported `assets/models/nevius-store.glb` (6,954 triangles, 5 materials, 1.3 MB, 2K lightmap, LIGHTMAP_SCALE 1.1072), previews re-rendered (blender-builder, 2026-11-03). Reviewer round 1: FIXES (3rd-floor front windows too short vs the 1909 card). Reviewer round 2: **PASS** — loads cleanly at intensity 1.1072, no console errors, colour factors and lightmap intact; upper floors now match the 1909 card; bracket pendants resting on the pair's hood moulds accepted; next: scene-integrator (reviewer, 2026-11-03).

**What it is**: a tall, narrow (25 ft) **3-storey red-brick Italianate store** on the east side,
just south of the Union Hotel, opposite the Court House. A store has stood on the lot since
before 1856; **William H. Fulper's "extensive alterations" of 1880** most likely gave it this front
(architect C. Pickell: "probably in the 1880's"). Occupants: Fulper (to 1880), Hall, Trewin &
Rittenhouse (1887–92), W. E. Trewin (1892), **Andrew T. Connet** (1897, d. 1913); the 1909 card
calls it the **"Nevius Store"** (P. TenBroek Nevius clerked there in the 1890s; the Nevius family
owned it later as **Nevius Brothers Dry Goods**). The 1921 Sanborn labels it **"Dry Goods"**. The
front survives today almost unchanged except a 1950s shop front.

**Orchestrator decisions** (settled from the photos/map; owner to check later)
1. **The placeholder `#bldg-78-main` covers just this one building.** Footprint **8.00 m wide ×
   32.25 m deep** (Sanborn sheet 3: 153 × 619 px). Sheet 2 repeats the building as an overlap strip
   159 px (8.31 m) wide; sheet 3 is the detailed, labelled drawing and agrees better with
   Pickell's "25 feet wide", so its 8.00 m is used.
2. **Front wall on the property line** (both sheets: the wall is drawn on the Main St line) →
   entity **(10.30, 0.15, −7.33)**, not the placeholder's (10.3, 0, −9.1). North wall z −11.33
   (sheet 2 line y 6682.5; 4.4–4.6 m clear of the hotel's south wall on both sheets), south wall
   z −3.33.
3. **Upper front = 1 + 2 + 1 windows per floor**: a single window in each outer bay and a **pair in
   a slightly projecting central section** (1909 card shows the north single and the central
   pair; Pickell: "a central projecting section"; HABS 1963 shows the same rhythm from the NW).
   The south single is out of frame in 1909 and assumed symmetric.
4. **2nd floor: segmental-arched windows with pale cut-stone arches and keystones; 3rd floor:
   semicircular-arched windows with slim brick hood moulds ending in square blocks, standing on a
   boldly projecting stone sill band** (Pickell's description; matches the 1909 card, where the
   2nd-floor heads are flatter with pale arches and the 3rd-floor heads are full round). The
   diamond/swirl carving on the arches is texture-level, not modelled.
5. **Brick quoins** on both front corners, full height (Pickell; 1909 and HABS-1 show
   alternating blocks on the corner piers). Modelled as relief blocks in brick.
6. **Bracketed cornice with a segmental-arched pediment over the central section** (1909 card:
   grouped brackets at the corners and at the central section's edges, arched crest above the
   cornice; HABS-2 shows the same arched crest in 1963). Cornice and pediment painted pale cream
   like the stone trim (1909 colours) — one `trim` material.
7. **Cornice height 35 ft = 10.70 m** (Sanborn "35'"); the 1909 card scaled to it gives the floor
   levels below.
8. **1920 shop front = the 1909 one**: painted wood front between the corner piers, wide display
   window on the north, **recessed central double door**, smaller display window south, a plain
   **street door to the upper floors at the south end** (common on 25-ft fronts; not visible in the
   1909 card), transom band, shop-front cornice at the 2nd-floor floor line. **One stone step** along
   the front. The 1950s front (HABS) is not used.
9. **One extended striped canvas awning with a scalloped valance** across the whole shop front
   (1909 card) — a model part, reusing the bank's red/cream `awning_stripes.jpg`. **No lettering or
   signboard** (tenant name not readable in any photo; 1921 just "Dry Goods").
10. **Side walls plain red common brick** with a plain trim frieze + cornice along their full
    length (HABS-2 shows the north-side cornice running the visible length), 4 segmental windows
    per upper floor, ground floor blank on the north, two small high windows on the south (alley).
    Rubblestone base not modelled (would cost a 6th material; below the sidewalk grade line).
11. **Only the 3-storey main block is modelled.** The 2-storey brick "FEED HO." (24', 13.6 m) and
    the further 2-storey block behind it toward Spring St are rear parts (outbuildings on hold).
12. **5 materials** (brick, trim, glass, dark, awning) = 5 draw calls; **no new textures**.
    Ordinary building, target ~5.5k triangles (cap 10k). **2K lightmap** (two 32 m side walls).

**Sources**
- Map: 1921 Sanborn **sheet 3** (primary): pink (brick), **"3"** storeys, **"35'"**, label
  **"Dry Goods"**, street numbers **78** (new) / **539** (old). Pixel lines (centres): front wall /
  street line x **4019.5**; rear wall x **4638.5**; north wall y **1063.5**; south wall y **1217**;
  Union Hotel south wall y 976; 82 Main north wall y 1306.5. Side-wall marks "12 12 16" and "///"
  on both long walls. Behind: brick "2" storey **"FEED HO."** "24'" x 4638–4900, then another
  2-storey brick 24' unit beyond x 4900 (not modelled). **Sheet 2** (overlap strip, unlabelled):
  north wall y 6682.5, south y 6842, front x 3991.5, hotel south wall y 6598. Scene z uses the
  sheet-2 frame (sheet 3 + 5593 is ~26 px off here; distances to the hotel are measured on sheet 3
  and agree on both sheets).
- Photos (local only, never commit):
  - **Primary: `flmngtnneviusstoreandununionhtl09.jpg`** (1909 tinted card "Union Hotel",
    West Jersey History title "Nevius Store and Union Hotel"; from the SW on the west sidewalk,
    looking NNE): right third = 78 Main's front, north single bay + central pair visible:
    quoined corner, segmental 2nd-floor and round 3rd-floor windows, grouped brackets, arched
    crest, shop-front cornice, scalloped striped awning, display window and recessed door,
    stone step. Vertical scale ≈ 85 px/m at 2× zoom (35 ft cornice).
  - `habs/union-hotel-west-elevation-2.jpg` (HABS NJ-732, 1963, from the NW): right edge = 78's
    north wall and front, painted light, 1950s shop front with "NEVIUS"-style lettering; shows the
    1+2+1 rhythm, the arched crest, the cornice running along the north wall. Differs from 1920:
    painted brick, 1950s front, a ground-floor display window cut into the north wall.
  - `habs/union-hotel-west-elevation-1.jpg` (1963, from the SW): right edge = 78's NW corner pier
    with banded quoins and the paired console brackets of the cornice.
  - Checked, not showing it: all other Union Hotel cards (78 is just out of frame on the right;
    `flmngtnunionhtlview.jpg` shows only a dark shaded edge), `flmngtnmainstrtunionhtlvu08.jpg`
    (looks north from the hotel's south end), bank/P.O./courthouse/county views.
- Web: Goodspeed Histories, "Fulper's Store, or the Gilded Age on Main Street" (2022,
  https://goodspeedhistories.com/fulpers-store/: occupant list; Fulper's 1880 alterations;
  Pickell / Friends of Historic Flemington: "local red brick on a rubblestone base… only 25 feet
  wide… brick quoins on the corners… semicircular and segmental arched wooden one-over-one double
  hung windows… third floor window heads… slim brick hood mouldings which terminate in square
  blocks… second floor… stone arches with keystones… third floor sills are boldly projecting
  stone bands… classic 1950's storefront"); West Jersey History image index
  (https://westjerseyhistory.org/images/hunterdon/flemington/: "Nevius Store and Union Hotel",
  1909).

**Placement** (east side, front faces west onto Main St)
- Entity position = centre of the front wall face at sidewalk level: **(10.30, 0.15, −7.33)**,
  `rotation="0 -90 0"` (replaces `#bldg-78-main` at (10.3, 0, −9.1), 7.3 × 17 m).
- Front x 10.30 (on the property line); rear x 42.55; north wall z −11.33; south wall z −3.33.
- Neighbours: Union Hotel GLB south end z ≈ −15.9 (veranda front x 11.6, i.e. 78 stands 1.3 m
  further forward) — 4.6 m gap; alley ("80") to the south, 82 Main's north wall z ≈ +1.48 —
  4.8 m gap. Court House opposite. No street tree in front (east trees end at z −18.8).
- Projections onto the sidewalk: step to x 10.05, shop-front cornice x 10.0, awning to **x 8.40**,
  main cornice x 9.75 — all clear of the curb (x 6.52).
- Blender local frame: front −Y, origin at the centre of the front wall face at sidewalk level,
  **+X = south**, −X = north (hotel side), z = 0 = sidewalk top. Body x −4.00 … +4.00,
  y 0 … 32.25. Sun "to sun" vector **(0.40, −0.90, 0.36)** (front sunlit, north side in shade).

**Massing**
- One brick box 8.00 × 32.25 m, 3 storeys; walls 0.40 (front), 0.35 (sides/rear); skirt to
  z −0.20.
- Levels (1909 card scaled to the 35' cornice): shop floor 0.12 (one step); 2nd floor ≈ 4.30;
  3rd floor ≈ 7.30; **main cornice top 10.70**; **pediment crown 11.95**.
- Side and rear walls: top 10.20 level, with a plain trim frieze 9.40–10.00 and corona
  10.00–10.20 (0.20 projection) along both side walls full length; rear wall plain coping 10.20.
- Roof: flat tin, 9.90 at the front falling to 9.40 at the rear, hidden behind the cornices
  (dark). Front cornice returns 0.6 m round each front corner into the side cornice.
- **Chimney**: brick, in the south wall (flush outside), 0.60 (x) × 0.90 (y), centre y 16.0,
  top 11.40, 0.08 cap course (guess).

**Elevation details (1920 state)** — front, x from north (−) to south (+)
- **Grid**: corner piers 0.55 wide (x ±3.45 … ±4.00); outer bays x ±1.35 … ±3.45 (2.10);
  **central section x −1.35 … +1.35**, 0.10 proud of the wall from 4.20 to 9.30, edged by brick
  pilaster strips 0.35 wide (x ±1.00 … ±1.35).
- **Quoins**: on both corner piers, z 0.12 → 9.30, 0.30-high courses alternating 0.55 / 0.38 m
  on the front face (and 0.38 / 0.55 on the side face), 0.03 proud, 0.015 joint gaps; brick
  material.
- **Shop front** (z 0 → 4.20, between the corner piers, x −3.45 … +3.45; painted wood, `trim`):
  - Stone step 0 → 0.12, 0.25 deep (y −0.25 … 0), x −3.45 … +3.45 (`trim`).
  - North display window x −3.35 … −0.85: panelled bulkhead 0.12–0.70, glass 0.70–2.95 with one
    central mullion (0.08).
  - **Recessed entry** x −0.85 … +0.75, 1.2 m deep, floor 0.12; splayed glass side returns;
    **glazed double door** 1.40 × 2.60 (0.12–2.72, dark varnish, glass upper two-thirds) at the back.
  - South display window x +0.75 … +2.45, as the north one.
  - **Upper-floor street door** x +2.50 … +3.35: single panelled door 0.85 × 2.50 (dark), flush
    in the front plane +0.10 recess.
  - Transom bar 2.95–3.05 and a band of 6 transom lights 3.05–3.55 across all four parts;
    fascia 3.55–3.95 (plain, no lettering); shop-front cornice 3.95–4.20, projecting 0.30, with a
    small bed moulding.
- **Awning**: striped canvas, x −3.40 … +3.40, hung at z 3.50 on the front, sloping to z 2.70 at
  **1.90 m out** (y −1.90), scalloped valance 0.25 deep (scallops as alpha-free zigzag geometry,
  ~0.30 m pitch) down to 2.45; thin side cheeks optional; no iron frame modelled.
- **2nd floor** (1/1 double-hung, frames `trim`, set 0.15 in): singles 0.90 wide at x ±2.40;
  pair 0.85 wide at x ±0.575 (brick mullion 0.30). Sill 4.55 (stone sill 0.10 tall, 0.05 proud,
  0.15 wider each side); jambs to spring 6.45; **segmental head**, rise 0.25 (crown 6.70).
  **Stone arch** 0.22 deep around the head, 0.03 proud, **keystone** 0.24 wide × 0.40 high,
  0.05 proud, top 6.95.
- **Sill band** (3rd floor): stone, z 7.25–7.45, projecting 0.08, continuous from quoin to quoin
  (breaking forward over the central section).
- **3rd floor**: same x positions and widths; sill 7.45, spring 8.50, **semicircular head**
  (crown 8.95 / 8.925). **Brick hood mould** 0.10 wide, 0.05 proud, following the arch, ending in
  0.20 × 0.20 square blocks at the springing.
- **Main cornice** (front, `trim`): bed moulding 9.30–9.40; frieze 9.40–10.15 with one flat
  sunk panel per bay; dentil row 10.15–10.25 (0.06 blocks at 0.12 m); corona 10.25–10.60
  projecting **0.55**; cap 10.60–10.70. Breaks forward 0.10 over the central section.
- **Brackets**: 4 groups — over each corner pier (x ±3.725) and each pilaster strip (x ±1.175);
  each group **2 scroll brackets** 0.12 wide, 0.08 apart, z 9.30–10.25, 0.50 deep at the top
  tapering to 0.15, small pendant drop 0.15 below. Simple 6–8-point side profile.
- **Pediment** over the central section: **segmental arch**, chord 3.40 m (x −1.70 … +1.70) on
  the cornice top 10.70, crown **11.95**; raking moulding 0.25 high, 0.30 proud, following the
  arc (10–12 segments); flat tympanum set 0.10 back; all `trim`.
- **North and south walls** (common brick): 2nd and 3rd floors, 4 windows each at
  **y 7, 14, 21, 28**, 0.85 × 1.90, segmental heads (rise 0.20) with a plain brick arch (relief
  only), stone sills; 2nd sill 4.70, 3rd sill 7.60. Ground floor: north blank; south two small
  windows 0.80 × 1.40, sill 1.60, at y 18 and 26.
- **Rear wall** (x 42.55, not seen): 2 windows per upper floor (as the sides), ground-floor door
  1.0 × 2.2 and one window.
- Not modelled: gutters, downpipes, signs, lamps, cellar hatches in the sidewalk.

**Materials & colours (1920)** — **5 materials = 5 draw calls**
1. `brick` — all walls, quoins, pilaster strips, mullions, hood moulds, chimney. Local red brick
   ≈ #8E4632 (front), common brick a touch duller on sides/rear (tint only).
   Reuse **`polyhaven/red_brick.jpg`**, tile 1.4 m.
2. `trim` — stone arches, keystones, sills, sill band, step, cornice, brackets, dentils, pediment,
   side cornices, shop front (frames, bulkheads, fascia, transom bars), window frames and sash.
   Pale cream ≈ #D8CDB4 (1909 card: cornice and arches cream). Reuse
   **`polyhaven/trim_paint_cream.jpg`**, tile 2.0 m.
3. `glass` — plain colour, no texture, very dark blue-grey ≈ #1E2226, roughness 0.15.
4. `dark` — doors, roof surfaces, chimney cap. Dark varnish ≈ #3A2A1F. Reuse
   **`county-offices/door_varnish_dark.jpg`**, tile 0.8 m.
5. `awning` — reuse **`bank-building/awning_stripes.jpg`** (red/cream 0.15 m stripes running
   down the slope), tile 0.6 m across the stripes.
- **New for asset-scout: none.** Asset-scout can be skipped; the builder confirms the four files.

**Weathering**: moderate (40-year-old commercial front): soot under the cornice corona and
pediment moulding; dark drip streaks under every keystone, sill and the sill band; grime and
splash on the bottom 0.5 m of the corner piers and shop-front bulkheads; step worn darker at the
door; awning faded on top, darker valance; side walls slightly patchy/darker toward the rear,
north wall cooler and greener at the base (shade); soot round the chimney top.

**Budget**: **ordinary building, target ~5.5k triangles, hard cap 10k**: walls with ~26 openings
~0.9k; quoins (2 × 30 blocks × 2 faces) ~0.8k; 8 front windows with frames, sash, arches,
keystones, hoods ~0.9k; 16 side + 4 rear windows ~0.6k; shop front, recess, doors ~0.5k; cornice,
dentils (~60) and 8 brackets ~0.9k; pediment ~0.3k; awning with scallops ~0.2k; roof, chimney,
side cornices ~0.2k. **5 materials**, 0 new textures (4 reused 1K maps), one **2K lightmap**
`assets/textures/nevius-store-lightmap.jpg`. Files: `tools/blender/nevius_store.py` +
`nevius_store_bake.py` (+ optional `_preview.py`), `assets/models/source/nevius_store.blend`,
`assets/models/nevius-store.glb` (≤ 5 MB, expect ~1.5 MB), previews
`assets/models/previews/nevius-store-*.png` (incl. a match to the 1909 card from the SW at eye
height, ~25 m away on the west sidewalk).

**Acceptance checks for the reviewer**
1. Box 8.00 × 32.25 m, cornice top 10.70 ± 0.15 m, pediment crown ≈ 11.95; origin at the centre
   of the front wall face at sidewalk level, front −Y, **+X = south**.
2. Upper front reads **1 + 2 + 1** on both floors, with the pair in a **slightly projecting
   central section** edged by pilaster strips; nothing off-centre.
3. **2nd-floor windows segmental with pale stone arches and keystones; 3rd-floor windows
   semicircular with thin brick hood moulds**, standing on a continuous pale sill band.
4. **Brick quoins** visible on both front corners from the sidewalk to the frieze.
5. Pale bracketed cornice with **4 groups of paired brackets**, a dentil row, and a
   **segmental-arched pediment** centred over the central section.
6. Shop front: north display window, **recessed central double door**, smaller south display
   window, narrow upper-floor door at the south end, transom band, shop-front cornice, one step;
   **one striped awning with a scalloped valance**, ~1.9 m deep; no lettering.
7. Side walls plain red brick with 4 segmental windows per upper floor and a plain cornice
   along their whole length; no roof visible from the sidewalk.
8. ≤ 10k triangles, **5 materials**, GLB ≤ 5 MB, 1K colour maps, 2K lightmap, TEXCOORD_0 + 1.
   Front sunlit with clear bracket, keystone, sill-band and awning shadows; the shaded north
   wall still reads as brick, not black.

**Integrator notes (scene, not the model)**
- Replace `#bldg-78-main` with the GLB at **(10.30, 0.15, −7.33)**, rotation 0 −90 0,
  `baked-lighting` with the bake's LIGHTMAP_SCALE. Remove the code-built placeholder.
- Check the ground in the two side gaps (hotel gap z −15.9 … −11.33, alley z −3.33 … +1.48,
  from x 10.3 back to ~x 20): it must not show a void; the sidewalk already runs in front.
- Expected draw calls: placeholder (~6–7) → GLB 5, i.e. −1 to −2.
- Optional later (budget): the 2-storey "FEED HO." behind (x 42.55 … 56.2), the alley at 80.

**Differences 1909 / 1963 vs 1920** (build 1920): 1963 has the brick painted white, a 1950s shop
front with lettering, a display window cut into the north wall; the 1909 awning is kept for 1920.

**Pure guesses (owner to check)**
1. South outer bay (out of frame in 1909): symmetric single windows.
2. Shop-front layout south of the door and the upper-floor door at the south end.
3. Which floor has segmental vs semicircular heads (Pickell says they "alternate"; the floors
   split is read from the blurry 1909 card).
4. Side-wall window count/spacing, south ground-floor windows, rear wall, roof, chimney.
5. Pediment height (1.25 m) and chord; frieze panels and dentils.
6. Colours: cream trim, awning stripes (1909 tint shows a mostly pale awning).
7. Exact width 8.00 m (sheet 3) vs 7.62 m (Pickell, 25 ft) vs 8.31 m (sheet 2 overlap strip).

### Frame Dwelling "D" at 65 Main St (65 Main St, old no. 510)

**Status:** **in scene** (scene-integrator, 2026-11-03): GLB placed at (−14.07, 0.02, −51.19), rotation 0 90 0, lightmap intensity 1.274; the kit placeholder at (−16.3, 0, −51.2) is gone; front path now `-12.63 -51.19 4.75 1.3` (sidewalk to under the steps). Footprint z −55.89…−45.73, clear of the Hall of Records and the Wurts office. No console errors; draw calls/triangles from the start view 164/84.7k → 159/90.9k, from opposite the house 64/34.0k → 59/40.2k. Fence, tree and side path skipped (draw calls). Screenshot `assets/models/previews/house-65-main-in-scene.png`. Before that: **reviewed, round 1: PASS** (reviewer, 2026-11-03). GLB parse: 6,343 tris, 4 materials, three 1024² JPEGs, TEXCOORD_0 + 1, 1.04 MB; lightmap 2048². Browser viewer: loads, no console errors, colour factors and lightmap (1.274) applied. All 8 acceptance checks met; the 13 builder simplifications are all acceptable. Minor notes, no fix needed: the bay's own hip roof is mostly hidden under the main soffit from street level; the sunlit south wall is only moderately brighter than the shaded front, and the flush shutters cast no shadows. Before that: **built** (blender-builder, 2026-11-03). Asset-scout skipped (nothing to download; the builder made `house-65-main/clapboard_cream.jpg` from `courthouse/brown_planks_05.jpg` with `tools/prepare_house_65_textures.py`, logged in SOURCES.md). `assets/models/house-65-main.glb`: 6,343 triangles, 4 materials (paint, dark, roof, brick), 1.04 MB, TEXCOORD_0 + 1; 2K lightmap `house-65-main-lightmap.jpg`, **LIGHTMAP_SCALE 1.274**. Previews `assets/models/previews/house-65-main-{front,three-quarter-ne,three-quarter-se,detail,match-1909}.png`. Builder deviations: eaves/frieze/soffit 6.48–6.80–6.98 with a 0.35 overhang put the ridge at 10.48 (ell 8.85) instead of 10.25 (8.60); front outer windows at x ±2.95 (not 2.85) so the inner shutters clear the porch pilasters; bay 2nd-floor windows 4.60–6.25 and ell-rear 1st-floor window 1.30–2.90 (under the rear-porch roof); deck/skirt tints made bluer than the spec values so they read grey on the cream paint; roof tile 3.0 m (orchestrator) instead of 2.6. Earlier: spec written, auto-approved (planner, 2026-11-03).

**What it is**: a **2½-storey frame dwelling** (Sanborn "D", yellow = frame, "2½") on the west
side between the Hall of Records (69–71) and the Wurts Law Office (59). The 1921 map gives an
**L-shaped plan**: a front block the full 8.6 m width, a narrower rear ell along the north side, a
small open entrance porch centred on the front, a **2-storey canted bay on the south side**, and an
open rear porch. Owner, builder and date are not documented on the web (searched the HCHS walking
tour, the Goodspeed "County House" series, NRHP/HABS); the plan and the "2½" point to a mid-19th-
century front-gabled house of the kind common on Flemington's Main St. It is **gone today**: the
HABS law-office photo (1960s–70s) shows a modern flat-roofed multi-storey building on its site.

**Orchestrator decisions** (settled from the map and photos; owner to check later)
1. **Footprint from Sanborn sheet 2** (the only sheet that shows it): front block **8.60 m wide ×
   9.72 m deep**; rear ell **4.27 m wide** (flush with the north wall) × **7.24 m** deep; total
   depth 16.96 m; open rear porch 4.07 × 1.41 m; open front porch **4.00 wide × 2.00 deep**,
   centred; south bay 3.0 m at the wall, 1.0 m projection. All from pixel lines (see Sources).
2. **Position: porch front 3.80 m and front wall 5.81 m behind the property line**, centred on
   z −51.19 → entity **(−14.07, 0.02, −51.19)**, rotation 0 90 0. (The placeholder at x −16.3
   has its front wall about where the real wall is, but its origin is not the porch front.)
3. **Front-facing gable (ridge east–west)**. Evidence: in the county-building cards (1908, 1909,
   1912) the house's south wall shows clapboard right up to a **horizontal eave line that recedes
   downward to the west** — an eaves wall, not a gable end. A front gable over an 8.6 m front with
   a "2½" (attic) storey is also the usual Flemington type. The ell has its own lower gable roof,
   same pitch, ridge also east–west.
4. **The whole L is one height class ("2½")**: the map draws the ell inside the same outline with
   no dividing line or own storey number, so the north eave runs continuously at the same height;
   the narrower ell's ridge comes out lower automatically.
5. **Walls: painted clapboard, warm cream** (#E6DFCC): the 1909 coloured card shows the south wall
   pale cream/buff with clearly visible lap lines; the 1912 b/w card shows it pale. Trim painted
   the same colour (one material; see decision 9).
6. **Roof: slate, dark grey.** Sanborn "o" (slate or tin) on the house and on the bay; slate from
   the nearby Pennsylvania quarries was normal on Hunterdon houses of this size. The red-brown
   wedge in the coloured 1908/1909 cards sits *below* the pale eave band — read as the
   colourist's tint of the shaded soffit, not a red roof.
7. **Front: 3 bays, centred door** (the porch is centred on the façade): 1st floor W-D-W, 2nd floor
   3 windows, **2 attic windows** in the gable. **2/2 sash** (as in the 1870 county building next
   door in the same cards; also the cheapest in triangles). Dark-green **louvred shutters** on
   the front and side windows (period norm; the Wurts office next door has them).
8. **Front porch**: 4 square chamfered posts, low-pitched hipped roof, plain frieze, simple
   railing with square balusters, **3 steps** centred between the inner posts (map: dashed open
   porch "1", roof "o"). Porch deck 0.68 m, house floor 0.75 m.
9. **4 materials = 4 draw calls** (see Materials): `paint` (clapboard texture; trim UVs squeezed
   onto one board so trim reads as flat paint), `dark` (plain colour: glass, shutters, doors),
   `roof` (slate: main, ell, bay and porch roofs), `brick` (foundation and chimneys). The porch
   deck and steps are made grey by an RGB tint in the bake's grime mask (no extra material; the
   bake already multiplies an RGB grime mask into the lightmap).
10. **Two brick chimneys** (none visible in any photo): one on the main ridge toward the rear, one
    on the ell ridge (kitchen).
11. **Ordinary building, target ~5.5k triangles (cap 10k)**; **2K lightmap** (≈ 550 m² of wall
    and roof; 1K would blur the shutters and porch).

**Sources**
- Map: 1921 Sanborn **sheet 2**, yellow (frame), **"2½"**, **"D"**, street numbers **65** (new) /
  **510** (old). Pixel lines (centres): **front wall x 3488.5**; **north wall y 5835** (straight,
  front to rear); **south wall y 6000** (front block); front block rear wall **x 3302**; ell south
  wall **y 5917** (x 3163–3302); **rear wall x 3163**. Front porch (dashed, "1", "o"):
  **x 3488.5–3527, y 5881–5958**. South bay ("2", "o"): wall span **y 6000, x 3420–3480**, outer
  face **y 6020, x 3432–3477**. Rear porch (dashed, "1", "o"): **x 3136–3163, y 5832–5913**.
  Property line x 3600; lot lines y 5787 (north) and 6143 (south). No height note. Sheet 3 does
  not cover it (blank at sheet-3 y 242–407).
- Photos (local only, never commit). **No photo shows the front.** The house appears only at the
  right (north) edge of the county-building cards, seen from the SE across the Hall of Records
  lawn:
  - **Primary: `flmngtncountybldnganddentistoffice09.jpg`** (1909 coloured card "County Building";
    the "dentist" of the title is the DENTIST sign on the Hall of Records, not this house):
    x ≈ 860–1024: pale cream **clapboard south wall** with wide lap lines, a pale eave band near
    the top receding to the west, shade trees, a **low post-and-rail fence** along the sidewalk
    continuing in front of the house.
  - `flemington_-_county_building_-_1912.jpg` (1912 b/w, same viewpoint): same wall, eave line
    sloping down to the right (= west), shrubs, fence.
  - `flmngtnhtncountybldg08.jpg` (1908 coloured, same view as the 1909 card).
  - `habs/wurts-law-office-east-front.jpg` (HABS NJ-772-1, 1960s–70s): left edge shows the modern
    building that replaced the house — not used for the model.
  - Checked, not showing it: all other West Jersey History cards (courthouse views from the SE are
    blocked by the Hall of Records; `flmgtnhtrdncntycrths2.jpg` is post-1928 and shows only an
    unclear brick wall beyond; Main St / bank / hotel views look elsewhere); the other HABS photos.
- Web (no data on this house found): HCHS Flemington walking trail
  (https://hunterdonhistory.org/wp-content/uploads/2018/08/Flemington-TRAIL-online8-1.pdf: entries
  for 71 and 59 Main only); Goodspeed Histories "County House" series on the west side of Main St
  between Court and Capner Sts (https://goodspeedhistories.com/category/countyhouseseries/: no
  mention of 65); Wikipedia, Flemington Historic District
  (https://en.wikipedia.org/wiki/Flemington_Historic_District).

**Placement** (west side, front faces east onto Main St)
- Entity position = centre of the porch front edge at grade: **(−14.07, 0.02, −51.19)**,
  `rotation="0 90 0"`; y 0.02 = lawn. Replaces `#house-65-main` at (−16.3, 0, −51.2).
- Scene lines: porch front x −14.07; steps to x −14.91; **front wall x −16.07**; front block rear
  x −25.79; ell/rear wall x −33.03; rear porch to x −34.44. **North wall z −55.49**; **south wall
  z −46.89**; bay outer face z −45.85; ell south wall z −51.22.
- Neighbours: Wurts office south wall z −66.34 (10.9 m clear); Hall of Records north wall
  z −34.80 (11.0 m clear of the bay). Lot lines z −57.99 / −39.44.
- **Blender local frame**: front −Y, origin at the porch front edge at grade, **+X = north**,
  z = 0 = grade. Porch x −2.00 … +2.00, y 0 … 2.00; steps y −0.84 … 0; front block
  x −4.30 … +4.30, y 2.00 … 11.72; ell x +0.03 … +4.30, y 11.72 … 18.96; rear porch
  x +0.23 … +4.30, y 18.96 … 20.37; bay on the south wall (x −4.30), centre y 4.00. Sun "to sun"
  vector **(−0.40, 0.90, 0.36)** (front in shade, south side and bay sunlit).

**Massing** (heights are photo estimate / guess: no height note on the map)
- Foundation: brick, grade → 0.70 visible, skirt to −0.20; 1st floor 0.75.
- Floor levels: 1st 0.75; 2nd ≈ 3.95; attic ≈ 6.95. **Wall plate / eave (top of frieze) 7.00**
  (1912 card: the house eave stands ≈ 0.7 × the Hall of Records' 8.5 m cornice height, and the
  house is further from the camera → roughly 6.5–7.5 m).
- **Main roof**: front gable, ridge east–west on x 0, pitch **37° (9/12)** → ridge **10.25**;
  eave overhang 0.40 (boxed, with soffit), rake overhang 0.25; the roof ends at the rear wall
  y 11.72 in a gable (the ell abuts its north half).
- **Ell**: 4.27 wide, same eave 7.00 on the north (continuous with the main block) and on its south
  wall, same pitch → ridge **8.60** on x +2.17; gable end at the rear (y 18.96).
- **South bay**: 2 storeys, canted: wall span y 2.50 … 5.50, outer face y 2.90 … 5.10 at
  x −5.30 (1.0 projection); on the brick foundation; own cornice 6.20–6.45, hipped slate roof
  rising to 6.85 against the wall (below the main frieze).
- **Front porch**: deck 0.68, posts to 3.05, frieze 3.05–3.30, low hipped roof (≈ 15°) from the
  3.35 eave at the front up to 3.85 at the wall (below the 2nd-floor sills at 4.70).
- **Rear porch**: deck 0.50, 3 posts, shed roof 2.90 → 3.30 at the wall; no railing; low detail.
- **Chimneys** (brick, guess): A on the main ridge, centre (x 0, y 9.0), 0.55 × 0.80, top
  **11.20**; B on the ell ridge, centre (x +2.17, y 17.8), 0.50 × 0.65, top **9.50**; each with a
  0.10 corbel course near the top.

**Elevation details (1920 state)**
- **Corner boards** 0.15 wide on all corners; **frieze board** 0.35 under the eaves on both sides;
  boxed cornice 0.25 deep with the 0.40 soffit; **front gable**: raking cornice (0.20 fascia +
  small crown) and **short cornice returns** 0.60 long at both front corners (Greek-Revival
  type); the rear gables get the plain rake only.
- **Windows (all)**: 2/2 double-hung, sash set 0.08 in, meeting rail 0.04, one vertical muntin
  0.03 per sash; flat casing 0.10 with a small head cap (0.12 tall, 0.04 proud); sill 0.05 proud.
  Sizes: **1st floor 0.90 × 1.80** (sill 1.45, head 3.25); **2nd floor 0.90 × 1.65** (sill 4.70,
  head 6.35); **attic 0.70 × 1.15** (sill 7.55, head 8.70).
- **Shutters**: louvred (louvres as 3–4 shallow grooves, not slats), 2 leaves per window, each
  half the window width, open flat 0.03 off the wall, on all 1st/2nd-floor windows of the front,
  north and south walls and the ell; **none** on the bay or attic windows.
- **Front (east) wall** (y 2.00), x from south (−) to north (+):
  - 1st floor: windows at **x −2.85 and +2.85**; **door centred**: 0.95 × 2.25 (0.75 → 3.00),
    4-panel, set 0.10 in, casing 0.12 with head cap; **4-light transom** 0.95 × 0.40 above it
    (3.08 → 3.48) in the same casing.
  - 2nd floor: 3 windows at **x −2.85, 0, +2.85**.
  - Gable: **2 attic windows at x ±0.90**.
  - Foundation: two small cellar vents 0.6 × 0.3 under the outer windows (dark).
- **South wall, front block** (x −4.30): the **bay** at y 2.50 … 5.50: per floor one 0.90 window
  in the 2.2 m outer face and one **0.50 window** in each canted face (same heads/sills as the
  floor); a flat panel under each 1st-floor bay window; then one window per floor at **y 9.00**.
- **North wall** (x +4.30, continuous to the rear): windows per floor at **y 4.00, 8.60, 13.80,
  17.20**.
- **Ell south wall** (x +0.03): 1st floor **side door** 0.90 × 2.15 at y 14.20 (plain stoop
  1.0 × 0.8 at 0.50 with one step) and a window at y 17.20; 2nd floor windows at y 14.20 and 17.20.
- **Rear walls**: main block (y 11.72, x −4.30 … 0): one window per floor at x −2.15, one attic
  window at x −1.00 (low in the gable, clear of the ell roof); ell rear (y 18.96): door
  0.90 × 2.15 at x +2.80 onto the rear porch, window at x +1.10; 2nd floor one window at x +2.17.
- **Front porch**: deck boards (paint + grey tint) with a 0.04 nosing; skirt boards 0 → 0.68
  (paint, slightly darker tint); **4 square posts 0.15**, chamfered (8-sided mid shaft), small
  base and cap blocks, centres **x ±1.90, ±0.70** at y 0.15; 2 half-pilasters on the wall at
  x ±1.90; frieze 0.25 on all three open sides; **railing** between the outer and inner post on
  each front segment and along both sides: top rail 0.06 × 0.10 at 0.68 + 0.80, bottom rail at
  0.68 + 0.08, square balusters 0.04 at 0.12 m centres (~9 per front segment, ~15 per side).
  **Steps**: 3 treads 0.28 deep, risers 0.17 (top at deck 0.68), **1.25 wide** centred
  (y −0.84 … 0), with plain closed stringers; no handrail.
- Not modelled: gutters, downpipes, lamps, house number, signs, lightning rods, storm doors.

**Materials & colours (1920)** — **4 materials = 4 draw calls**
1. `paint` — clapboard walls (real-world box UVs, boards horizontal) **and all painted trim**
   (corner boards, frieze, cornices, soffits, casings, sash frames, porch posts, rails, balusters,
   porch frieze, skirt, deck, steps, bay panels). Trim UVs are scaled down (×0.02) and moved onto
   the middle of one board in the texture so trim reads as flat paint without lap lines; porch-deck
   UVs rotated so the boards run east–west (along Y). Colour warm cream ≈ **#E6DFCC**.
   Texture: **new local copy `assets/textures/house-65-main/clapboard_cream.jpg`**, made by the
   builder from the existing **`courthouse/brown_planks_05.jpg`** (Poly Haven `brown_planks_05`,
   CC0): desaturate, recolour to #E6DFCC, contrast ≈ 35 % so the lap shadows stay and the grain
   and knots mostly disappear; 1024². **Tile 1.6 m** (9 boards per tile → **0.18 m exposure**).
   Made by a small `tools/prepare_house65_textures.py` (pattern: `tools/prepare_wurts_textures.py`)
   and logged in SOURCES.md.
   **Bake tints** (RGB multipliers in the grime mask, multiplied into the lightmap): porch deck
   and steps (0.60, 0.60, 0.58) → worn grey paint; porch skirt (0.80, 0.80, 0.78).
2. `dark` — plain colour, **no texture**: all glass, shutters, doors, transom bars, cellar vents.
   Very dark green ≈ **#27322A**, roughness 0.3 (glass reads as dark panes; shutters and doors as
   dark-green paint).
3. `roof` — main, ell, bay, porch and rear-porch roofs (and ridge caps). Reuse
   **`polyhaven/roof_slates_03.jpg`**, **tile 2.6 m** (≈ 22 courses per tile → ~0.12 m exposure),
   tinted toward cool dark grey ≈ #4C5155; slate rows run horizontally on each slope.
4. `brick` — foundation (all round, incl. under the bay) and both chimneys. Reuse
   **`polyhaven/red_brick.jpg`**, **tile 1.4 m**, tint ≈ #87452F; chimney caps in the same brick.
- **New for asset-scout: none** (no downloads). Asset-scout can be skipped; the builder makes
  `clapboard_cream.jpg` locally from an existing CC0 map and confirms the other two.

**Weathering**: light to moderate — a lived-in house repainted within the last decade: dirt
splash on the bottom 0.4 m of the foundation and porch skirt; faint grey streaks under the window
sills and below the eave soffit; slightly chalky, warmer paint on the sunlit south side and bay;
porch deck and top step worn darker at the door and down the middle; soot on both chimney tops
and a faint dark stain on the slate below them; north wall a touch cooler/greener near the ground.

**Budget**: **ordinary building, target ~5.5k triangles, hard cap 10k**: walls with ~40 openings
(clapboard is texture, not geometry) ~1.0k; ~34 windows with casing, sash, rail, muntin ~1.4k;
~44 shutter leaves ~0.5k; roofs, cornices, returns, frieze, soffits ~0.7k; bay ~0.3k; porch
(posts, rails, ~48 balusters, roof, deck, steps) ~0.9k; rear porch, side stoop ~0.2k; chimneys,
foundation ~0.2k. **4 materials** (draw calls); the placeholder costs ~6–7, so the scene saves
2–3 calls. Textures: 1 locally recoloured 1K map + 2 reused 1K maps; one **2048² lightmap**
`assets/textures/house-65-main-lightmap.jpg`. Files: `tools/blender/house_65_main.py` +
`house_65_main_bake.py` (+ optional `_preview.py`), `assets/models/source/house_65_main.blend`,
`assets/models/house-65-main.glb` (≤ 5 MB, expect ~1.2 MB), previews
`assets/models/previews/house-65-main-*.png` (incl. one from the SE at eye height on the Hall of
Records lawn, ~30 m away, to compare with the 1909/1912 cards, and one straight-on from the east
sidewalk).

**Acceptance checks for the reviewer**
1. L-shaped plan: front block 8.60 × 9.72 m, rear ell 4.27 × 7.24 m flush with the **north** wall,
   open rear porch; origin at the porch front edge at grade, front −Y, **+X = north**.
2. **Front-facing gable** (ridge east–west), slate roof, ridge ≈ 10.25 m, eaves ≈ 7.0 m, short
   cornice returns at the front corners; the ell roof is lower (ridge ≈ 8.6 m).
3. Front reads **3 bays**: W-D-W on the 1st floor (door centred, with a transom), 3 windows on the
   2nd, **2 attic windows** in the gable; all sash 2/2.
4. **Centred open porch 4.0 × 2.0 m** with 4 square posts, railing, low hipped roof and **3 steps**
   centred between the inner posts; the porch roof stays below the 2nd-floor sills.
5. **2-storey canted bay on the south side** near the front (centre 2.0 m behind the front wall),
   1.0 m deep, with its own small roof below the main eaves.
6. Walls cream clapboard with visible ~0.18 m laps; trim the same cream with no lap lines;
   dark-green louvred shutters on front/side windows (not on bay or attic windows); red-brick
   foundation and two brick chimneys.
7. **≤ 4 materials**, ≤ 10k triangles (target ~5.5k), GLB ≤ 5 MB, TEXCOORD_0 + 1, 1K colour maps,
   2K lightmap. Porch deck and steps read grey (bake tint), not cream.
8. With the WSW sun the east front is in shade but the shutters, porch posts and door still read
   (bounce light, not flat grey); the south wall and bay are sunlit with clear shutter, cornice and
   bay shadows.

**Integrator notes (scene, not the model)**
- Replace `#house-65-main` (kit placeholder at (−16.3, 0, −51.2)) with the GLB at
  **(−14.07, 0.02, −51.19)**, rotation 0 90 0, `baked-lighting` with the bake's LIGHTMAP_SCALE;
  keep the id.
- Front path (`#paths` ground-patches, "x z width depth"): replace `-11.75 -51.2 2.9 1.4` with
  **`-12.63 -51.19 4.75 1.3`** (sidewalk x −10.25 to x −15.0, 0.1 m under the bottom step at
  x −14.91).
- Optional later (draw-call budget, skip for now): the **low post-and-rail fence** along the
  property line in front of the Hall of Records and 65 Main (1908/1909/1912 cards), a shade tree
  in the front yard south of the path, and a side path to the ell door. No outbuildings (on hold).

**Photos vs 1920**: the 1908–1912 cards are the closest dates and are used directly; the HABS
photos (1960s–70s) show the house already replaced — not used.

**Pure guesses (owner to check)**
1. Front gable vs side gable (only the receding south eave in two blurry cards supports it).
2. All heights (eave 7.0, ridge 10.25, floor 0.75, porch 0.68) and the 37° pitch.
3. The whole front elevation: centred door with transom, 3 bays, 2 attic windows, 2/2 sash,
   shutters and their colour; no photo shows the front.
4. Porch details (4 chamfered posts, railing, hipped roof, 3 steps); only its size and position
   are from the map.
5. Window positions on the sides, rear and ell; the ell side door and rear-porch details.
6. Chimney count and positions.
7. Slate (vs tin) roof and its colour; red-brick (vs stone) foundation.
8. Cream wall colour (from a hand-coloured card) and same-colour trim.

### Lovell's Restaurant (68 Main St)

**Status:** **in scene** (scene-integrator, 2026-11-04): GLB placed at (12.66, 0.15, −52.13),
rotation 0 −90 0, replacing the code-built placeholder (id `bldg-68-main` kept); `#bank-forecourt`
extended to x 10.30–12.66, z −77.31 … −49.13 so it also paves 68's front strip (no extra draw
call). No console errors; faces Main St; signs readable; gap to the hotel shows ground; seam with
the bank clean. Draw calls unchanged (161 at the start view), +4.7k triangles.
Previous: reviewer round 2: **PASS** (2026-11-03). 4,752 tris, 4 materials, 0.77 MB, 2K
lightmap, **LIGHTMAP_SCALE 1.2462**; loads clean, no console errors. Awning now short and high
(valance 3.30–3.00) with transoms and lantern visible; doors read as dark-green glazed doors
(builder's darker tint accepted); steps pale bluestone. Next: show the user, then scene-integrator.
Previous: round-1 fixes applied, re-baked and re-exported — next: reviewer round 2
(blender-builder, 2026-11-03). (1) Shallow awning: still hung at 3.52, front bar at y −0.95 /
z 3.30, valance bottom 3.00, cheeks and arms shortened; lantern back at the spec position (body
2.65–3.10 at y −0.35, arm at 3.40, pale glass body kept). (2) Door stiles, rails, panels and
transom bars moved to `paint` with a dark-green bake tint (0.115, 0.145, 0.125) ≈ #4F564A; glass
stays `dark`. (3) `stone` uses the new lightened `lovells-restaurant/stone_bluestone.jpg` (mean
#8E8C86, made by `tools/prepare_lovells_textures.py`); roof tint lowered to (0.21, 0.215, 0.23).
GLB: 4,752 triangles, 4 materials, 0.77 MB, TEXCOORD_0 + 1; 2K lightmap, **LIGHTMAP_SCALE 1.2462**.
Previews re-rendered under the same names.
Previous: reviewer round 1: **FIXES** (2026-11-03): (1) awning too deep and low, hides the
transoms and lantern; (2) door glass and leaves read as solid black slabs; (3) stone steps and
foundation too dark. Loads clean (4,730 tris, 4 materials, 0 errors); deviations 1, 2, 4, 6, 7, 8 accepted.
Next: blender-builder round-1 fixes.
Previous: built, baked and exported — next: reviewer (blender-builder, 2026-11-03).
Asset-scout skipped (no downloads): clapboard_cream + concrete_floor_worn_001 reused, sign atlas
generated by `tools/prepare_lovells_textures.py`. `assets/models/lovells-restaurant.glb`: 4,730
triangles, 4 materials (paint, dark, signs, stone), 0.76 MB, TEXCOORD_0 + 1; 2K lightmap
`lovells-restaurant-lightmap.jpg`, **LIGHTMAP_SCALE 1.2451**. Previews
`assets/models/previews/lovells-restaurant-{front,three-quarter-sw,three-quarter-nw,detail,match-lovells,match-oysters}.png`.
Builder's deviations: upper windows at x ±1.65 (spec ±1.50) and LOVELL'S board 1.34 m wide (spec
1.65) so the board fits between the inner shutters as in the photos; lantern body 2.40–2.96
(spec 2.65–3.10) and its glass pale (paint) so it shows below the valance against the dark
doors; awning hung at 3.52 at 0.13 m out (clears the pilaster caps); chimney in `paint` with a
brick-red bake tint (the stone map is too dark to tint to brick); stone left at the map's own
dark bluestone grey (~#565654; a factor can't brighten it to #8E8C86); arch crown 7.68.

**What it is**: a **2-storey frame restaurant with a pool (billiard) room upstairs** (Sanborn 1921:
yellow = frame, "2", "Restr't & Pool Room 2nd"), wedged between the Bank Building (56–66) and the
gap north of the Union Hotel. Goodspeed Histories ("The surprising history behind a modest
building") traces it as Flemington's oyster restaurant from 1848; the **1870 remodel gave it the
present front with an arch in the roofline**; Theodore B. Bellis ran a "restaurant and billiard
room" 1886–c. 1910, then **Fred Lovell ran "Lovell's Restaurant" from c. 1910 to after 1935**
(Lindbergh-trial photo). So in 1920 it is **Lovell's Restaurant**. The building still stands as
the **Higgins News Agency, 68 Main St**, refaced in buff brick with a flat top (no arch); the
modern front is not used.
**The placeholder `#bldg-68-main` covers only this building.** Behind it (not in this spec) the
1921 map shows a separate 2-storey frame **Harness Shop** (px x 4400–4505) and a larger frame
building further back; outbuildings are on hold.

**Orchestrator decisions** (settled from the map and photos; owner to check later)
1. **Footprint 6.00 m wide × 18.39 m deep, one block, 2 storeys, no porch on the map.** Depth from
   sheet 2 (front wall outer face px x 4040, rear wall x 4393 = 18.39 m). Width: the map draws
   68's north wall line at y 5851 and the bank's south wall at y 5841 (0.5 m apart), but **every
   photo (c. 1900, 1901, 1908, Lovell's c. 1910–20) shows the two fronts touching**. The north wall
   is therefore put against the bank (z −55.13, 4 cm clear of the bank GLB's south wall at
   −55.17) and the south wall kept on the map (y 5957 → z −49.13). Lovell's photo, scaled by the
   three men (~1.7 m), gives a front of ≈ 5.5–6.0 m, consistent.
2. **Front wall 2.36 m behind the property line**, 0.42 m behind the bank's front (map px 4040 vs
   the bank's 4032; the c. 1900 photo shows the bank's stone pier slightly proud of 68). Entity
   **(12.66, 0.15, −52.13)**, rotation 0 −90 0 — not the placeholder's (10.6, 0, −51.7).
3. **Front = c. 1910–20 Lovell's photo** (primary): shop front of **left door ("Ladies'
   Entrance") – pier – recessed glazed double door – pier – display window** with an "ICE CREAM"
   bulkhead and a cellar window under it; full-width sign board "RESTAURANT" with end consoles;
   small "LOVELL'S" board above it between the upper windows; **plain pale canvas awning with a
   scalloped valance lettered "LOVELL'S RESTAURANT."**; hanging gas lantern over the centre door;
   **3 stone steps** across the two doors only. Upper floor and roof line from the **c. 1900
   "Oysters" photo** (same front, frontal) and the 1901 fire photo: **2 shuttered windows with
   segmental heads, two short bracketed cornice blocks at the ends, and a segmental arch rising
   between them in the middle of the roofline**.
4. **Front surface smooth** (flush boards, no visible laps in either close photo); **side and rear
   walls clapboard** (c. 1900 Bank/Oyster House photo, 1908 colour card, 1910s hotel cards all
   show the south wall clapboarded).
5. **One paint colour, warm off-white/cream, for front, sides and trim** (1908 colour card: cream
   front; 1910s coloured hotel cards: pale south wall; Lovell's photo: pale front). The 1908 card
   tints the south wall tan-brown; the later, closer-to-1920 cards are followed.
6. **Shutters dark green, louvred**, on the two front windows (Lovell's photo, dark louvred
   shutters) and on the south-wall windows (1900/1908 views show shutters there too).
7. **Low shed roof hidden behind the front parapet/arch and the side cornices** (c. 1900 view from
   the SW: side eave line level, no gable; 1910s hotel cards: level cornice line on the south wall).
   Tin, grey (Sanborn shows no shingle "×").
8. **South wall openings**: 4 windows upstairs, 3 windows + a kitchen door downstairs (c. 1900 view
   shows windows starting ~2.5 m from the front at regular spacing). **North wall**: blank where it
   abuts the bank (first 11.05 m: bank 62–66 is 11.05 m deep), 2 windows per floor on the exposed
   rear part. **Rear wall**: blank (the harness shop abuts it).
9. **4 materials = 4 draw calls**: `paint` (clapboard texture; front and trim UVs squeezed onto one
   board so they read smooth), `dark` (plain colour), `signs` (one generated atlas: awning, valance
   lettering, RESTAURANT board, LOVELL'S board, ICE CREAM panel), `stone` (steps, foundation,
   cellar-window surrounds, roof, chimney; roof and chimney coloured by bake tints).
10. **Bake with occluder proxies** (not exported): a box for the Union Hotel's north end and one
    for the bank, so the hotel's late-afternoon shadow falls on the rear part of the south wall
    (shadow line reaches the south wall ≈ 7 m behind the front) and the bank's tall south wall
    adds bounce/shade. Values under Placement.
11. **One brick chimney** for the restaurant kitchen on the exposed rear part of the north wall
    (none visible in any photo; a restaurant needs a range flue).

**Sources**
- Map: 1921 Sanborn **sheet 2**, yellow, **"2"**, "Restr't & Pool Room 2nd", street number
  **68**. Pixel lines: **front wall x 4040** (outer face; street line x 3990), **rear wall
  x 4393**, **north wall y 5851** (bank south wall y 5841), **south wall y 5957**; a small "o"
  (roof mark) near the front SW corner; no porch, no height note. Harness Shop behind at
  x 4400–4505, y 5850–5970 ("2"); open gap south of 68 to the hotel (hotel's 2nd-floor-only bay
  at y ≈ 6020–6045). Sheet 3 does not reach 68 (it starts at the hotel).
- Photos, West Jersey History (local only, never commit):
  - `flmngtnbankandpovu08.jpg` (1908 colour card, from the SW): 68 at x ≈ 700–860 next to the
    bank: cream front, arched hood at the top, shop front with two doors and a window, bracketed
    shop cornice; its **tan clapboard south wall with shuttered windows** at x 860–1024 (this is
    68's side, seen across the gap, not a separate building).
  - `flemington_-_union_hotel_-_union_hotel_-_1910s.jpg`, `flmngtndcmuirheadsunionhtl10.jpg`,
    `flemington_-_the_union_hotel_in_winter.jpg` (1910s, from the W/SW): left edge, behind the
    hotel's north veranda: **pale clapboard south wall of 68 with a window and a level cornice**,
    the bank's brick south wall rising above it.
  - `flmngtnpobankunionhtl07.jpg`, `flmingtnporichardsbldgunionhtl.jpg`,
    `flmngtnmainstrichardsbldgpo06.jpg` (1906–07, from the NW): 68 hidden behind the bank awnings
    (only a low awning edge shows) — not useful. Other hotel/courthouse cards: 68 out of frame.
  - HABS NJ-732 hotel views (1963): 68 only as a sliver at the frame edge — not used.
- Web photos (Goodspeed Histories article, viewed for reference only, not saved to the project):
  - **Primary: "Lovell's Restaurant", after 1910** (frontal, ground floor + bottom of the upper
    floor): https://goodspeedhistories.com/wp-content/uploads/2021/09/9-Lovells-Rest-copy.jpg
  - **"Oysters" photo, c. 1900** (near-frontal from the SW, whole front incl. arch and cornice):
    https://goodspeedhistories.com/wp-content/uploads/2021/09/2-Oysters-alone.jpg
  - Bank + Oyster House, c. 1900 (from the SW; shows the clapboard south wall):
    https://goodspeedhistories.com/wp-content/uploads/2021/08/68-OysterHouse-Bank-copy.jpeg
  - Richards Building fire, Feb 1901 (from the NW; arch and cornice from the side):
    https://goodspeedhistories.com/wp-content/uploads/2021/09/6-Richards-fire.jpg
  - Higgins News Agency today (modern refacing, not used).
- Web text: Goodspeed Histories, "The surprising history behind a modest building"
  (https://goodspeedhistories.com/?p=23290): owners and tenants 1848–1935, 1870 alterations and
  the arch, "Ladies Entrance" left door, restaurant originally in the basement, ice delivered
  through a sidewalk manhole, Lovell's c. 1910–1935+.

**Placement** (east side, front faces west onto Main St)
- Entity position = centre of the front wall face at sidewalk level: **(12.66, 0.15, −52.13)**,
  `rotation="0 -90 0"`; replaces `#bldg-68-main` (keep the id).
- Scene lines: front wall x 12.66; rear wall x 31.05; **north wall z −55.13** (bank south wall
  −55.17); **south wall z −49.13**. Union Hotel GLB north end z ≈ −45.6 (veranda front x 11.6),
  so a 3.5 m open gap. The bank's south cornice return (z −54.37, ~11.5 m up) passes high over
  68's north edge (68 tops out at 7.65).
- Projections: shop-front pilasters/cornice to x 12.51, main cornice blocks to x 12.21, steps to
  **x 11.71**, awning to **x 11.11** — all on the private strip, clear of the sidewalk line 10.30.
- **Blender local frame**: front −Y, origin at the centre of the front wall face at sidewalk
  level, **+X = south** (hotel side), −X = north (bank side), z = 0 = sidewalk top. Body
  x −3.00 … +3.00, y 0 … 18.39. Sun "to sun" vector **(0.40, −0.90, 0.36)** (front sunlit,
  south wall grazing sun).
- **Bake occluders** (hidden from export, visible to the bake): Union Hotel box
  x +6.53 … +36.0, y +1.94 … +10.54, z 0 … 12.25, plus an inset mansard box to 15.6; its veranda
  as a box x +6.53 … +36.0, y −1.06 … +1.94, z 0 … 7.6 (open sides not needed). Bank box
  x −25.18 … −3.04, y −0.42 … +10.63, z 0 … 12.35.

**Massing** (heights are photo estimates: the c. 1900 frontal photo scaled by the bank's belt
course at 4.45 m and its 0.17 m stoop risers, cross-checked on Lovell's photo by door and people
heights)
- Foundation: grey stone course 0 → 0.45 on all walls (skirt to −0.10); **1st floor 0.45**
  (3 risers; Lovell's photo). 2nd floor ≈ 4.30.
- **Side walls** (clapboard) to the eave at **6.30**; boxed side cornice 6.30–6.55, 0.30
  overhang, frieze board 6.05–6.30 below it.
- **Front**: wall face to 6.15; two **cornice blocks** at the ends (x −3.05 … −1.45 and
  +1.45 … +3.05), crown at **6.45–6.70**, 0.45 projection, each on 3 scroll brackets; **segmental
  arch** between them springing at 6.70 (x ±1.45), **apex 7.55**, moulded archivolt 0.20 wide ×
  0.30 projecting (crown 7.65); the tympanum under it is flat boarding, flush with the wall. The
  cornice blocks return 0.45 along each side and die into the side cornice.
- **Roof**: tin shed roof, 6.55 at the front (behind the parapet) falling to 6.25 at the rear
  wall, inside the side cornices; not visible from the street. Thin flat coping on the parapet
  behind the arch.
- **Chimney** (brick, guess): on the north wall at y 15.0, 0.60 × 0.50, top **7.90**, with a
  0.08 corbel course.

**Elevation details (1920 state)** — x from north (−) to south (+)
- **Shop front** (from Lovell's photo, proportions scaled to 6.0 m), all panelled painted wood:
  - **Corner pilasters** x −3.00 … −2.65 and +2.65 … +3.00, 0.08 proud, 0 → 3.55, with recessed
    panels and small caps.
  - **Left door (Ladies' Entrance)**: opening x −2.65 … −1.70; single 4-panel door with glazed
    upper half, 0.95 × 2.30 (0.45 → 2.75); **transom** 2.85 → 3.45.
  - **Pier** x −1.70 … −1.05.
  - **Centre double door**: opening x −1.05 … +0.65 (1.70), **recessed 0.45** with panelled
    reveals; two glazed leaves 0.75 × 2.40 (0.45 → 2.85), panelled bottoms; transom 2.95 → 3.45.
    **Hanging gas lantern** centred in front of it: iron arm from the wall at 3.40, lantern body
    0.25 Ø × 0.45 hanging 2.65 → 3.10 at y −0.35.
  - **Pier** x +0.65 … +1.10.
  - **Display window** x +1.10 … +2.65: panelled **bulkhead 0.45 → 1.05** with the "ICE CREAM"
    panel (signs atlas); glass 1.05 → 2.95 in one big pane with a 2-light top row 2.95 → 3.45;
    sill 0.06 proud. Below it, in the stone course, a **cellar window** 0.70 × 0.30.
  - **Shop entablature**: sign board 3.55 → 3.98 across x −2.85 … +2.85 ("RESTAURANT", signs
    atlas), crown moulding 3.98 → 4.10 projecting 0.15; **end consoles** at x ±2.85, 0.25 wide ×
    0.70 tall (3.45 → 4.15), 0.18 deep.
  - **Steps** (stone): 3 risers 0.15, treads 0.30, across **x −3.00 … +0.80** (both doors):
    bottom y −0.95 … −0.65 (top 0.15), middle −0.65 … −0.35 (0.30), top landing −0.35 … 0
    (0.45). The display window bay has no steps.
- **Upper front**: 2 windows at **x ±1.50**, 2/2 sash, **0.85 × 1.45** (sill 4.20, spring 5.53,
  segmental head rise 0.12 → 5.65), flat casing 0.10 with a **segmental moulded hood** to 5.80;
  sill 0.05 proud; **louvred shutters**, 2 leaves each (0.43 wide), open flat 0.03 off the wall.
  **"LOVELL'S" board** centred: 1.65 × 0.32, bottom 4.12, 0.04 proud.
- **Brackets**: 3 per cornice block at x ±2.95, ±2.35, ±1.65: scroll profile 0.55 tall
  (5.90 → 6.45) × 0.40 deep × 0.12 wide, extruded from one 8–10-point profile, with a small drop
  pendant; one more bracket on each side face at the front corner (y 0.30) under the return.
- **Awning**: plain pale canvas, full width x −2.90 … +2.90, hung at **3.50** on the wall, sloping
  out to **2.75 at y −1.55**; **scalloped valance** 0.30 deep (bottom 2.45) with
  "LOVELL'S RESTAURANT." (signs atlas), 18 scallops as geometry (≈ 4 segments each); canvas side
  cheeks (triangles); 2 iron arms (dark) from the wall at 2.50 to the front bar. 2.45 m headroom
  at the valance.
- **South wall** (x +3.00, clapboard): 2nd floor windows at **y 2.5, 6.5, 10.5, 14.5** (sill 4.30,
  0.85 × 1.45, straight heads, casing with head cap); 1st floor windows at **y 2.5, 6.5, 10.5**
  (sill 1.25, 0.85 × 1.70); **kitchen door** 0.90 × 2.10 at y 15.5 with one stone step
  (1.1 × 0.4, 0.15 → 0.45 platform at 0.30); all windows 2/2, louvred dark shutters. Two cellar
  windows 0.60 × 0.30 in the stone course at y 4.5 and 12.5. **Corner boards** 0.15 at both ends.
- **North wall** (x −3.00): blank from y 0 to 11.05 (against the bank); windows at **y 13.0 and
  16.5** on both floors (same sizes as the south side, shutters omitted to save triangles);
  chimney at y 15.0 rises from the eave (stack only above the roof, 6.30 → 7.90).
- **Rear wall** (y 18.39): blank clapboard (abuts the harness shop).
- Not modelled: gutters/downpipes, the "FREE…" poster, flags and the hanging "ICE CREAM" banner,
  the sandwich board, the sidewalk ice manhole, the upper-window awnings, interior.

**Materials & colours (1920)** — **4 materials = 4 draw calls**
1. `paint` — side and rear clapboard (box UVs, boards horizontal) **and the whole front plus all
   trim** (front wall, tympanum, pilasters, piers, panels, casings, sash frames, cornices,
   brackets, consoles, hoods, corner boards, frieze, door/window frames, bulkhead frame). Front
   and trim UVs scaled ×0.02 onto the middle of one board so they read as smooth paint (same
   trick as 65 Main). Colour **warm off-white cream ≈ #E4DDCB** (colour factor ~1.0 on the cream
   map). Texture: reuse **`house-65-main/clapboard_cream.jpg`** (from Poly Haven
   `brown_planks_05`, CC0), **tile 1.6 m** (0.18 m exposure).
2. `dark` — plain colour, no texture: glass, door leaves, shutters, lantern, awning arms, cellar
   windows, recess floor. **#2B302C** (very dark green), roughness 0.3.
3. `signs` — **new locally generated atlas `assets/textures/lovells-restaurant/signs_atlas.jpg`,
   1024²** (made by the builder with Pillow, `tools/prepare_lovells_textures.py`, logged in
   SOURCES.md as own work). Layout (top → bottom): awning canvas 1024 × 384, plain off-white
   #E8E2D2 with a faint canvas weave and soft soiling, no stripes; valance strip 1024 × 128,
   same canvas with **"LOVELL'S RESTAURANT."** in dark brown #3A2E26 serif capitals; board
   1024 × 160, mid grey-green **#5B5F55** with **"RESTAURANT"** in widely spaced cream #E6DFCC
   Roman capitals (Lovell's photo: pale letters on a darker board); bottom row: 512 × 128
   **"LOVELL'S"** board, white #EEEAE0 with black block capitals and a thin dark border, and
   512 × 128 **"ICE CREAM"** panel, dark #2E2A26 with white capitals; spare area filled with
   canvas. Use a bold serif font installed on the PC (e.g. Georgia Bold / Times New Roman Bold);
   the rendered image is our own work. Awning canvas UVs tile 1.5 m.
4. `stone` — steps, foundation course, cellar-window surrounds, step at the kitchen door, roof,
   parapet coping, chimney. Reuse **`polyhaven/concrete_floor_worn_001.jpg`**, **tile 2.0 m**,
   tinted bluestone grey **≈ #8E8C86**. **Bake tints** (RGB multipliers in the grime mask, as on
   65 Main): roof and coping (0.62, 0.63, 0.66) → dark tin grey; chimney (1.00, 0.62, 0.50) →
   dull brick red.
- **New for asset-scout: none.** Lightmap: one **2048²** `assets/textures/lovells-restaurant-lightmap.jpg`
  (front and south wall weighted up in the lightmap UVs; north wall, rear and roof weighted down).

**Weathering**: a busy commercial front, painted every few years: dirt splash on the stone
course and pilaster bases (0.4 m); the steps worn darker on the treads in front of both doors;
faint grey streaks below the cornice blocks, brackets and window sills; slightly soiled awning
valance edge; the south wall a little more chalky and stained than the front, darker near the
ground in the narrow gap; soot on the chimney top.

**Budget**: **ordinary building, target ~5k triangles, hard cap 10k**: walls, foundation and
openings ~0.7k; 15 windows with casings, sash, rails, muntins ~0.8k; 22 shutter leaves ~0.3k;
shop front (pilasters, panels, doors, transoms, recess, display window, consoles, board)
~0.9k; 8 brackets and two cornice blocks ~0.6k; arch archivolt (16 segments, 2 bands) and
tympanum ~0.4k; awning with scallops, cheeks and arms ~0.4k; steps, lantern, signs, chimney,
roof ~0.4k. **4 materials** (the kit placeholder costs ~6–7 calls → saves 2–3). Textures: 2 reused
1K maps + 1 generated 1K atlas; one 2K lightmap. Files: `tools/blender/lovells_restaurant.py` +
`lovells_restaurant_bake.py` (+ optional `_preview.py`), `assets/models/source/lovells_restaurant.blend`,
`assets/models/lovells-restaurant.glb` (≤ 5 MB, expect ~1 MB), previews
`assets/models/previews/lovells-restaurant-*.png` (incl. one frontal at eye height from the
sidewalk to compare with Lovell's photo, one from the SW at ~25 m to compare with the 1908 card
and the c. 1900 Bank/Oyster House photo).

**Acceptance checks for the reviewer**
1. Footprint 6.00 × 18.39 m, 2 storeys, frame; origin at the centre of the front wall face at
   sidewalk level, front −Y, **+X = south**; nothing in front of y −1.55.
2. **Roofline**: two short bracketed cornice blocks at the ends (3 scroll brackets each) and a
   **segmental arch rising between them to ≈ 7.6 m**; cornice ≈ 6.7 m; no gable or pitched roof
   visible from the street.
3. **Shop front reads, north to south: single door – pier – recessed double glazed door – pier –
   display window**, each door with a transom, panelled corner pilasters, "RESTAURANT" sign board
   with end consoles above.
4. **3 stone steps across the two doors only**; a cellar window in the stone course under the
   display window; shop floor 0.45 m above the sidewalk.
5. Upper front: **2 shuttered 2/2 windows with segmental hoods** at x ±1.5, "LOVELL'S" board
   between them, sills just above the shop cornice.
6. **Pale scalloped awning lettered "LOVELL'S RESTAURANT."** full width, valance bottom ≥ 2.4 m;
   hanging lantern over the centre door.
7. Front smooth cream paint, **sides clapboard** in the same cream; dark-green louvred shutters on
   the front and south windows; south wall with 4 + 3 windows and a rear door; north wall blank
   along the first 11 m.
8. **≤ 4 materials**, ≤ 10k triangles (target ~5k), GLB ≤ 5 MB, TEXCOORD_0 + 1, 1K colour maps,
   2K lightmap; roof grey and chimney brick-red via bake tints.
9. With the WSW sun the front is sunlit with clear bracket, cornice, awning and step shadows; the
   rear part of the south wall is in the Union Hotel's shadow (occluder proxy), the front part
   grazed by sun.

**Integrator notes (scene, not the model)**
- Replace `#bldg-68-main` (kit placeholder at (10.6, 0, −51.7)) with the GLB at
  **(12.66, 0.15, −52.13)**, rotation 0 −90 0, `baked-lighting` with the bake's LIGHTMAP_SCALE;
  keep the id.
- **Pave the front strip with no extra draw call**: enlarge `#bank-forecourt` to x 10.30 … 12.66,
  z −77.31 … −49.13 (width 2.36, depth 28.18, centre (11.48, 0.075, −63.22); adjust `repeat`).
  The extra 0.42 m under the bank's front wall is hidden inside its stone skirt.
- Check the 3.5 m gap to the hotel (z −49.13 … −45.6, x 10.3 → ~31): ground must show, no void;
  the 1921 map shows it open (a passage).
- Expected draw calls: placeholder (~6–7) → GLB 4 (start view 159 → ~156).
- Optional later (budget, skip now): the hanging "ICE CREAM" banner and flag, the sandwich board,
  the Harness Shop behind.

**Photos vs 1920**: Lovell's photo (after 1910) is the closest and sets the ground floor, awning
and signs; the c. 1900 photos set the upper floor, cornice and arch (unchanged in 1908 and in
Lovell's lower edge of the upper floor). The modern Higgins News front (refaced, flat top) and
the 1935 photo (Coca-Cola signs) are later and not used.

**Pure guesses (owner to check)**
1. Exact heights (cornice 6.7, arch apex 7.55, floor 0.45, eave 6.30); photo-scaled, ±0.3 m.
2. Width 6.00 m (map 5.6 m + closing the 0.5 m slot to the bank).
3. Colours: cream paint all round (1908 card shows a tan side wall), grey-green sign board, dark
   green shutters and doors, pale awning.
4. Side and north window positions and counts, kitchen door, no shutters on the north wall.
5. Roof form (low tin shed) and the chimney.
6. Awning projection (1.55 m) and side cheeks; lantern size.
7. Bracket count (3 per block) and the moulding profile of the arch.

### Rea Building / "Clock Tower Building", the old Post Office block (48–52 Main St)

**Status:** Spec approved by the owner (2026-11-04) at **landmark** detail (cap 15k tris). Asset-scout skipped (no downloads). **Built by blender-builder 2026-11-04**: 14,593 tris, 5 materials (brick, trim, stone, dark, signs), GLB 1.89 MB, 2K lightmap, LIGHTMAP_SCALE 1.1735; generated atlas `rea-building/signs_atlas.jpg` (`tools/prepare_rea_textures.py`); previews `assets/models/previews/rea-building-*.png`. **Review round 1 (2026-11-04): PASS** (14,593 tris, 5 materials, 1.89 MB, UV2, 2K lightmap; loads cleanly; minor optional notes: cupola could be a touch more cream-yellow, Flats door step sticks 0.40 m past the south wall onto Bloomfield Ave). Owner approved placement ("Place it", cupola colour left as is). **In scene 2026-11-04 (scene-integrator)** at (10.85, 0.15, −97.79), `rotation="0 -90 0"`, replacing the `#bldg-48-52-main` placeholder (id kept); merged 5 materials → 1 draw call; steps cover the strip behind the sidewalk (no paving box); no props moved; Flats door step left as is (minor). Screenshots `assets/models/previews/rea-building-scene-*.png`.

**What it is**: the 3-storey red-brick **Italianate block on the NE corner of Main St and
Bloomfield Ave**, built **1874 for George A. Rea** (shoe dealer; "the new building under the Town
Clock", 1878 ad). It has a **segmental arched pediment with an oval window in the middle of the
front roofline**, a second arch on the Bloomfield side, a bracketed cornice and a **square wooden
cupola with a clock on all four faces**. Flemington National Bank 1876–1891 in the south shop; the
**U.S. Post Office from 1 Feb 1899** (south shop, "P.O." awning in the 1906/07 cards). It still
stands (50 Main St), little changed above the shop fronts. It is **not** the "Richards Building":
in the 1905–07 card captions "Post Office – Richards Bldg – Union Hotel" the Richards Bldg is the
Bank Building across Bloomfield Ave. **c. 1920 tenants (Sanborn 1921), north → south: 48 Drugs
(Green's drug store; "Green's Apothecary" awning 1906–07; Frank E. Green bought the building in
1915), 50 Cobbler, 52 Jeweler (1st) / Club Rooms (2nd).** The Post Office had left by 1921 (no
"P.O." on the map; where it went is unknown).

**Planner decisions** (from the map and photos; owner to confirm)
1. **One model: the main block (15.94 × 15.20 m) plus the 3-storey brick "Flats" wing behind it on
   Bloomfield Ave** (7.87 × 8.91 m, same 36' height; the modern photo shows one continuous cornice
   along the whole Bloomfield side). The frame rear porches (yellow on the map) are not modelled.
2. **Height: cornice top 11.0 m = Sanborn "36'"**. The modern frontal photo, if not stretched,
   would give ~12.5 m, but it is perspective-corrected (vertically stretched); a vanishing-point
   check on the 1907 card puts the PO cornice ~1.4 m below the bank's 12.2 m, i.e. ≈ 10.8 m.
   All levels below are the modern photo's proportions scaled to 11.0 m.
3. **Facade = 2016 frontal photo for the upper floors** (7 bays grouped 2–3–2, pediment over the
   middle 3), **1906–07 cards + 1880s photo for the ground floor** (raised shop floors with stone
   steps along the whole front; 3 round arches in the middle section; shop fronts with arched-head
   display windows).
4. **Middle section arches (1920 guess)**: north arch = cobbler's door (50), middle arch = window,
   south arch = door to the stair hall (club rooms upstairs; the old P.O. lobby door with its sign in
   1907). The 1907 card shows window, window, door; today it is window, door, window.
5. **Front wall 0.55 m behind the scene's property line** (map); **steps run along the whole front
   and stand on the public sidewalk** to x 9.65, as in the 1906–08 cards. No forecourt box needed.
6. **Awnings 1920**: 48 plain cream canvas, valance lettered "GREEN'S APOTHECARY"; 52 red/cream
   striped, no lettering; none on 50 or the upper windows (the 1906–07 upper-window awnings are left
   out, as on the bank).
7. **Ordinary building: hard cap 10k triangles, target ~9k; 5 materials; no downloads.**

**Sources**
- Map: 1921 Sanborn **sheet 2**, pink (brick), **"3"** storeys, **"36'"** on all three units,
  "o" (non-combustible roof) marks; street numbers 48, 50, 52; "Drugs", "Cobbler",
  "Jeweler 1st / Club Rooms 2nd". Pixel lines: **front wall x 4004–4008** (east street line slants
  from x 3963 at y 4880 to 3975 at y 5150; a dashed line at x 3993–3997 = scene property line
  10.30); **north wall y 4870**; **south wall y 5176** (on the Bloomfield Ave line); **rear wall
  x 4297**; partitions: solid with a central opening at y 4960 (48|50), dashed at y 5040 (50|52).
  **Flats** (street no. 4/6 Bloomfield): x 4297–4448, y 5005–5176, "3", "36'", NE corner chamfered
  (4420,5005)→(4447,5030). Not modelled: 3-storey frame porch strip x 4297–4318, y 4890–5000 and a
  1-storey frame strip x 4318–4420, y 4970–5005. North neighbour (44–46, frame "Shoe Shine &
  Fruits") south wall y ≈ 4826: a 2.3 m open passage. Hydrant "T.H." off the SW corner.
- Photos, West Jersey History (`assets/photos/reference/`, local only, never commit):
  - **Primary (ground floor, 1906–07): `flmngtnpobankunionhtl07.jpg`** (1907, from the NW on the
    sidewalk, "Post Office – Bank Building – Union Hotel"): front from the middle to the SW corner:
    3 round arches in a pale rusticated middle section, "GREEN'S APOTHECARY" awning (48), striped
    awning (52), 4-riser stone steps along the front, segmental-headed upper windows with hoods,
    paired corner brackets, the arched pediment with the oval window (top left).
  - `flmingtnporichardsbldgunionhtl.jpg` and `flmngtnmainstrichardsbldgpo06.jpg` (1906, same
    viewpoint): same; **"P.O." on the striped south awning**, a sign over the south arch door.
  - `flmngtnpoandnatbank08.jpg` (1908, tinted, from the SW): the **Bloomfield side**: red brick,
    pale open shutters on the 1st/2nd-floor windows, segmental 3rd-floor window, cream cupola with
    pilasters and tall windows, a brick chimney beside it, a tall spike on top.
  - `flmngtnbankandpovu08.jpg` (1908, tinted, from the SW, farther): whole block behind the bank:
    front with the arched pediment, cupola with a tall pole, pale shop fronts and awnings.
  - Checked, not this building: `flmngtnmainstrycolrvu10.jpg` (brick ground storey, no arches),
    the "business blocks" cards (78 Main southward), all Union Hotel/courthouse cards and all
    HABS photos (none show it).
- Web photos (Goodspeed Histories, viewed for reference only, not saved to the project):
  - **Primary (upper floors and roofline): modern frontal view, Dave Norton**:
    https://i0.wp.com/goodspeedhistories.com/wp-content/uploads/2021/08/54-Rea-Bldg-copy.jpg
    (all window positions and the pediment were measured on it: facade 1130 px = 15.94 m).
  - 2016 view from the SW (front + Bloomfield side, cupola):
    https://i0.wp.com/goodspeedhistories.com/wp-content/uploads/2021/08/50Main-Feb2016_088-copy.jpeg
  - Roof-top close-up of the cupola (clapboard body, pilasters with consoles, tall windows, a
    segmental arched gable with a clock dial on each face, metal roof):
    https://i0.wp.com/goodspeedhistories.com/wp-content/uploads/2021/08/Rea-Clock-Tower-copy.jpg
  - Flemington National Bank in the south shop, 1876–91, from the SW (shop fronts with arched-head
    windows, corner pilaster with console, steps, Bloomfield side windows with shutters):
    https://i0.wp.com/goodspeedhistories.com/wp-content/uploads/2021/08/54-Rea-FNB-copy.jpg
- Web text: Goodspeed Histories, "The Clock Tower Building"
  (https://goodspeedhistories.com/the-clock-tower-building/): 1874, Rea; bank 1876–91; Shields
  bought it and "the rear building on Bloomfield Avenue" 1895; repainted 1895; granolithic walk
  1898; **P.O. leased the first-floor room (16 × 46 ft) from 1 Feb 1899**; Berkaw 1911, Frank E.
  Green 1915; 1979 county survey: "3-story, brick, Italianate", "stone keystones and sills",
  "segmentally arched pediments on the central bay of each side", oval front window, "segmentally
  arched brick hoods", "wood cupola" with "a clock on each of its 4 sides", ground floor "stucco
  panels". "A Distinctive Feature of Downtown Flemington" (https://goodspeedhistories.com/roof-arches-part-one/):
  Bertland: "square cupola, low pitched roof, wide bracket eaves cornice and segmental arched
  windows"; the pediment is "broken… along the bottom". HCHS (https://hunterdonhistory.org/?p=6574):
  built 1874, "one of the best preserved". HCHS container list
  (https://hunterdonhistory.org/wp-content/uploads/2022/06/Collection-238-Container-List.pdf): photo
  of the corner with "Green Apothecary, Shoemaker, and Post Office".

**Placement** (east side, front faces west onto Main St)
- Entity position = centre of the front wall face at sidewalk level: **(10.85, 0.15, −97.79)**,
  `rotation="0 -90 0"`; replaces the kit placeholder `#bldg-48-52-main` at (10.3, 0, −98.3)
  (keep the id).
- Scene lines: front wall x 10.85; **north wall z −105.76**; **south wall z −89.82** (Bloomfield
  Ave road plane starts at −89.8); main-block rear wall x 26.05; Flats x 26.05 … 33.92,
  z −98.73 … −89.82. Steps reach **x 9.65**, awnings x 8.65, cornice x 10.0 — street props
  nearby (pole-E5 at 6.9/−92.5, hydrant-Y2 at 6.85/−90.9) are clear.
- **Neighbours**: the Bank Building (front x 12.24, north wall z −77.31) is across Bloomfield Ave,
  12.5 m south; its `#bank-forecourt` (z −77.31 … −49.13) does **not** reach this block and needs
  no change. This front is 1.39 m further west than the bank's (1907 card: the PO steps come further
  into the sidewalk than the bank stoops). North: 2.0 m open passage, then the 40–46 placeholder
  (z ≤ −107.8).
- **Sidewalk**: the strip x 10.30 … 10.85 lies under the steps; the steps' blocks and cheek walls
  skirt down to local z −0.20 (world −0.05), so no paving box is needed. All walls also skirt to
  −0.20 (Bloomfield side and passage are at ground y 0).
- **Blender local frame**: front −Y, origin at the centre of the front wall face at sidewalk
  level, **+X = south** (Bloomfield), −X = north, z = 0 = sidewalk top. Main block
  x −7.97 … +7.97, y 0 … 15.20; Flats x −0.96 … +7.97, y 15.20 … 23.07 (chamfer from
  (−0.96, 21.60) to (+0.34, 23.07)). Sun "to sun" **(0.40, −0.90, 0.36)** (front sunlit, Bloomfield
  side grazed, north side in shade). Optional bake occluder (not exported): box for 44–46 at
  x −26.0 … −10.28, y −0.55 … 16.0, z 0 … 8.0.

**Massing** (heights = modern frontal photo proportions scaled to cornice top 11.0 m;
widths measured on the same photo at 15.94 m across)
- Main block 15.94 × 15.20 m, Flats 8.91 × 7.87 m; both 3 storeys, **cornice top 11.00** all round.
- Levels: shop floors **0.60** (4 risers); ground storey to the shop entablature top **4.70**;
  2nd floor ≈ 4.75; 3rd floor ≈ 7.75; frieze 9.75–10.55; cornice 10.55–11.00.
- **Roof**: low hipped tin roof (≈ 12°) from 10.75 behind the cornice up to a flat deck at
  **11.95** under the cupola (main block); Flats: flat tin roof at 10.70 behind its cornice.
  Hardly visible from the street; dark grey.
- **Front pediment** (centred, X 0): **segmental arch, outer moulding chord 6.00 m (X ±3.00),
  springing at 11.00 on the cornice ends, crown 12.10** (R ≈ 4.64 m); moulding 0.30 deep (crown
  roll 0.12 + fascia), projecting 0.25, with a dentil course under it (see Elevation). The main
  cornice stops at X ±2.20 with short returns; **between them the brick wall rises as the tympanum**
  to the arch's underside (the pediment is "broken along the bottom"). Behind the arch a
  **segmental barrel roof**, same profile, runs 1.50 m back (tin) and dies into the hip roof.
- **Side pediment** (Bloomfield face, centred at y 7.60): same design, **chord 5.00, crown 11.95**,
  no oval window; barrel 1.20 m deep.
- **Cupola** (centred at x 0, y 7.60, on the deck): wood, clapboard. Plinth 3.70 sq, 11.95–12.30,
  sloped top; **body 3.30 × 3.30, 12.30–14.70**, corner pilasters 0.30 wide with scroll consoles at
  the top; one tall window per face **0.80 × 1.80** (sill 12.60), narrow sunk panel 0.35 wide each
  side; frieze 14.40–14.70; **cornice 14.70–14.95, 0.30 overhang, small brackets (2 per face)**.
  On each face a **segmental arched clock gable**: chord 1.70, from 14.95 up to **15.95**, front
  face flush with the body, its own 0.08 moulding; **clock dial Ø 1.00, centre 15.40**, 0.04 proud.
  Behind the four gables: low pyramid roof, 14.95 → 15.70, plus the four little barrel roofs of the
  gables (tin). **Iron pole** Ø 0.05 from the apex to **18.70** with a ball Ø 0.12 (1908 cards).
- **Chimney**: one, brick, on the south wall at y 11.5 (behind the side pediment), 0.90 × 0.50,
  top **12.60**, 0.08 corbel cap (1908 SW card: a brick stack beside the cupola).

**Elevation details (1920 state)** — X from north (−) to south (+)
- **Upper front (7 bays, 2–3–2)**: window centres **X = −6.13, −3.84, −1.56, 0, +1.56, +3.84,
  +6.13**. 2nd floor: opening **0.90 × 1.75**, sill 4.82, segmental head (rise 0.15) crown 6.57;
  3rd floor: **0.90 × 1.55**, sill 7.85, crown 9.40. Both: **raised brick segmental hood** 0.14 wide,
  0.05 proud, 0.15 above the opening, with a pale stone **keystone** 0.18 × 0.28; stone sill
  1.15 × 0.10, 0.06 proud; 2/2 sash in a trim frame set 0.12 in; **open louvred shutters**
  (2 leaves 0.45 × opening height, 0.03 off the wall, louvres from the atlas).
- **Main entablature (front)**: brick frieze 9.75–10.40 with a pale moulded band and **dentil
  course 10.40–10.55** (atlas strip on a 0.04-proud band); cornice (trim) 10.55–11.00 projecting
  **0.85** (bed moulding, flat soffit, corona, cap). **4 pairs of large scroll brackets** under
  it at **X ±7.60 and ±2.35** (pair = 2 brackets 0.20 wide, 0.25 apart; 0.80 tall 9.75–10.55,
  0.75 deep; one 10-point side profile extruded, with a drop pendant).
- **Oval window** in the tympanum: centre (0, 10.45), **0.82 wide × 0.90 tall**, 16-sided, dark
  glass set 0.10 in; pale stone surround 0.12 wide with 4 small keystones (N/E/S/W). The 1874
  "initials" round it are not modelled.
- **Arch moulding**: pale trim; dentils on the inner edge (atlas strip, 0.15 tall).
- **Ground storey, side shops** (48: X −7.62 … −2.60; 52: X +2.60 … +7.62, clear 5.02 m):
  painted wood/cast-iron (trim) shop fronts between **pilasters 0.35 wide, 0.06 proud** at
  X ±7.795 and ±2.425 (panelled shafts, small console caps 3.80–3.95). Each shop, symmetric:
  **display window 1.75 wide** each side on a panelled bulkhead 0.60–1.10, glass 1.10 → 3.15 with
  a **segmental/round-cornered head to 3.35**; centre **recessed entrance 1.50 wide × 0.90 deep**,
  glazed double doors 2 × 0.70 × 2.40 (0.60 → 3.00), transom 3.05–3.30; **sign band 3.40–3.95**
  (52: "JEWELER" board; 48: plain); recess floor at 0.60.
- **Ground storey, middle section** (X −2.25 … +2.25, 50 and the stair hall): **pale rusticated
  stucco** (trim material, horizontal 0.02-deep channels every 0.40 m, modelled as 0.02-proud
  bands) on a stone plinth 0 → 0.60. **Three round arches 1.00 wide at X −1.45, 0, +1.45**,
  springing 2.90, crown 3.40, plain stucco archivolt 0.15, 0.03 proud, stone keystone:
  north arch = **glazed door** 0.90 × 2.30 (0.60 → 2.90) + fanlight (cobbler); middle arch =
  **window**, sill 1.20, 2/2 sash, arched top sash; south arch = **panelled door** with glazed upper
  panels + fanlight (stair hall). Small dark board **"SHOES REPAIRED"** 1.10 × 0.30 at 3.45 over the
  north arch (guess).
- **Shop entablature**, full front width (+0.35 m return on the Bloomfield side):
  architrave 3.95–4.10, frieze 4.10–4.45, cornice 4.45–4.70 projecting 0.30; small console over
  each pilaster.
- **Steps** (stone): along the whole front, **4 risers × 0.15, treads 0.30, y −1.20 … 0** (top
  step = landing at 0.60, running into the shop recesses); **stone cheek blocks** 0.30 wide,
  sloped top 0.75 → 0.30, at X −7.80, −2.42, +2.42, +7.80. All step blocks skirt to −0.20.
- **Awnings**: 48 and 52 only, full shop width (X −7.55 … −2.65, +2.65 … +7.55): roller bar at
  **3.35** on the wall, sloping to **2.65 at y −2.20**, **valance 0.25 (bottom 2.40)**, cloth side
  cheeks, 2 iron arms each. 48 plain cream with **scalloped valance "GREEN'S APOTHECARY"**; 52
  red/cream stripes, plain scalloped valance.
- **Bloomfield (south) side**, main block (x +7.97, y 0 … 15.20): window bays at **y 2.30, 6.60,
  8.56, 12.86** (pediment over the middle pair); upper windows as the front (same sizes, hoods,
  keystones, sills, shutters); **ground floor windows 0.95 × 2.40** (sill 1.20) with shutters at the
  same y; stone water table 0 → 0.60 (skirt to −0.20). Entablature, dentil band and cornice as the
  front, **bracket pair at the SW corner and at y 5.10 / 10.10** (flanking the side pediment),
  single brackets at y 13.6. The front shop entablature returns 0.35 m.
- **Flats (Bloomfield face y 15.20 … 23.07)**: same cornice and frieze (single brackets at 2.4 m),
  windows (no shutters, no keystones) at **y 16.60 and 19.70** on all floors, a **door** 0.95 × 2.30
  with one stone step at y 21.80; east face: 2 windows per floor; north (yard) face: 2 windows per
  floor, plain; chamfered NE corner plain.
- **North wall** (x −7.97, passage side): common brick, cornice and frieze continue (brackets only
  at the NW corner pair); upper windows at y 3.0, 7.6, 12.2 (no shutters); ground floor: 2 small
  high windows (sill 2.0) at y 5.0 and 10.0.
- **Main-block rear wall** (y 15.20, X −7.97 … −0.96, above the yard): plain, 2 windows per floor.
- Not modelled: gutters, downpipes, telephone/electric drops, the 1906–07 upper-window awnings,
  the frame rear porches, interiors.

**Materials & colours (1920)** — **5 materials** (merged into one draw call by `baked-lighting`)
1. `brick` — walls, hoods, frieze, tympanum, chimney. Red-brown pressed brick ≈ #8A4030 (1908
   cards). Reuse **`polyhaven/red_brick.jpg`**, tile 1.4 m.
2. `trim` — cornices, brackets, arch mouldings, pilasters, shop fronts, bulkheads, sign band,
   window frames, sash, shutter frames, keystones and sills (pale stone and paint read alike in
   every card), rusticated middle section, cupola. **Pale drab ≈ #B5AC98**; reuse
   **`county-offices/trim_paint_drab.jpg`**, tile 2.0 m. **Bake tint** on the cupola
   (1.00, 0.96, 0.80) → cream-yellow (1908 cards).
3. `stone` — steps, cheek blocks, plinths, water table, Flats door step. Reuse
   **`lovells-restaurant/stone_bluestone.jpg`** (#8E8C86), tile 2.0 m.
4. `dark` — plain colour, no texture: glass (≈ #1E2226), door leaves (dark varnish ≈ #3A2A1F via
   vertex/bake tint), roofs and barrel roofs (tin grey ≈ #4A4C50 via bake tint), iron arms, pole.
5. `signs` — **new locally generated atlas `assets/textures/rea-building/signs_atlas.jpg`, 1024²**
   (Pillow script `tools/prepare_rea_textures.py`, own work, logged in SOURCES.md), cells:
   plain cream canvas (#E2DACA, faint weave); scalloped valance strip "GREEN'S APOTHECARY" (dark
   brown serif capitals on cream); red/cream stripe canvas + plain striped valance (resampled from
   `bank-building/awning_stripes.jpg`); **clock dial** (white face, black Roman numerals and
   minute ring, black hands at about 4:50); **louvre pattern** for shutters (pale drab slats with
   shadow lines); **dentil strip**; "JEWELER" board (gold-cream letters on black); "SHOES
   REPAIRED" board (cream on dark green).
- **New for asset-scout: none.** One **2K lightmap** `assets/textures/rea-building-lightmap.jpg`
  (front, Bloomfield side and cupola weighted up; north, rear and roofs down).

**Weathering**: 46 years old, well kept (repainted 1895): soot under the main cornice and
pediment moulding; dark streaks under sills, keystones and bracket feet; brick darker on the
shaded north wall and in the passage; grime and splash on the bottom 0.4 m and on the step treads
(worn darker in front of the doors); cupola paint slightly chalky, darker under its cornice; tin
roofs dull; soot on the chimney top; awnings sun-bleached on top.

**Budget**: **ordinary building, hard cap 10k triangles, target ~9k**: walls with openings ~1.5k;
~50 windows (frames, sash, glass, segmental heads ≤ 60 tris) ~2.6k; hoods + keystones + sills
~0.7k; 64 shutter leaves as boxes ~0.8k; ~30 brackets ~1.0k; cornices, frieze, returns ~0.5k;
2 pediment arches + barrel roofs + oval ~0.5k; cupola with 4 clock gables and dials ~0.8k; shop
fronts, arches, doors ~0.7k; steps and cheeks ~0.2k; awnings ~0.3k; roofs, chimney, pole ~0.2k.
If over: drop the north/rear/Flats window sash detail to flat inset panels, then the north-side
shutters (none planned), then single brackets on the Flats. Textures: 3 reused 1K maps + 1
generated 1K atlas, one 2K lightmap. Files: `tools/blender/rea_building.py` +
`rea_building_bake.py` (+ `_preview.py`), `assets/models/source/rea_building.blend`,
`assets/models/rea-building.glb` (≤ 5 MB, expect ~1.8 MB), previews
`assets/models/previews/rea-building-*.png` (incl. a frontal one to compare with the modern
frontal photo, one from the NW sidewalk at eye height to compare with the 1907 card, one from the
SW across Bloomfield to compare with `flmngtnpoandnatbank08.jpg`).

**Acceptance checks for the reviewer**
1. Main block 15.94 × 15.20 m + Flats 8.91 × 7.87 m behind it on the Bloomfield side; origin at
   the centre of the front wall face at sidewalk level, front −Y, **+X = south**; cornice top
   11.0 ± 0.2 m all round.
2. Front upper floors: **7 bays grouped 2–3–2** on both floors, segmental heads with raised brick
   hoods and pale keystones, open louvred shutters.
3. **Segmental arched pediment over the middle three bays, broken at the bottom**, crown ≈ 12.1 m,
   with an **oval window** in the brick tympanum; a smaller arch on the Bloomfield side.
4. Bracketed cornice with a dentil band; **four pairs of large brackets** on the front (corners and
   flanking the pediment).
5. **Square cream cupola** centred on the roof, one tall window per face, and a **clock dial in a
   segmental gable on each of the four faces**; thin pole on top (≈ 18.7 m).
6. Ground floor, N→S: **shop (48) with "GREEN'S APOTHECARY" awning – pale rusticated section with
   three round arches (door, window, door) – shop (52) with striped awning**; shop floors 0.60 m up,
   **stone steps along the whole front** with cheek blocks, reaching ≤ 1.2 m out.
7. Bloomfield side: 4 window bays on the main block (pair under the side arch), shutters, chimney
   behind the side arch; Flats with 2 bays and a door; nothing crosses z −89.82 except the cornice
   overhang (≤ 0.85 m).
8. ≤ 10k triangles, **≤ 5 materials**, GLB ≤ 5 MB, TEXCOORD_0 + 1, 1K colour maps, 2K lightmap;
   cupola reads cream against red brick; roofs grey.
9. With the WSW sun the front is sunlit (bracket, hood, awning and step shadows), the Bloomfield
   side grazed, the north wall in shade; no floating at the Bloomfield and passage edges.

**Integrator notes (scene, not the model)**
- Replace `#bldg-48-52-main` with the GLB at **(10.85, 0.15, −97.79)**, rotation 0 −90 0,
  `baked-lighting` with the bake's LIGHTMAP_SCALE; keep the id.
- No paving box (the steps cover the 0.55 m strip); `#bank-forecourt` unchanged.
- Check the steps against the sidewalk-east box edge at x 10.30 (no gap or z-fighting) and the
  south wall against the Bloomfield Ave plane.

**Photos vs 1920**: the 1906–08 cards are the closest views and set the ground floor, steps,
awnings, shutters and cupola colour; the modern photos set the exact upper-floor layout, pediment,
cornice and cupola form, which match the old cards. Left out as later: today's green shop fronts,
level entrances (no steps) and teal clock dials. Left out as earlier: "P.O." lettering and the
sign over the stair-hall door (P.O. gone by 1921), upper-window awnings.

**Pure guesses (owner to check)**
1. Height 11.0 m (Sanborn 36') rather than the ~12.5 m the stretched modern photo suggests.
2. Arch uses in the middle section (cobbler door / window / stair door) and the "SHOES REPAIRED"
   and "JEWELER" boards (1921 tenants, wording invented); Green's awning lettering still in 1920.
3. Shop-front details (arched-head display windows, recessed doors) from the 1880s and 1906 views.
4. Colours: shutters and cupola pale (tinted cards), white clock dials, red-brown brick, pale trim.
5. Cupola size (3.3 m) and heights; the pole; low hipped roof form.
6. Bloomfield-side bay positions (perspective-measured on the 2016 photo), side pediment size,
   chimney position; north, rear and Flats walls entirely guessed.
7. Steps continuous along the whole front (1906–07 cards) and 4 risers.

### County Hotel (47–49 Main St)

**Status:** **In scene** (scene-integrator, 2026-11-04): `#county-hotel` at (−10.30, 0.15, −112.07), rotation 0 90 0, faces Main St, veranda floor flush with the sidewalk; merged to 1 draw call; `#bldg-35-41-main` placeholder shortened to z −135.6 … −124.2; no props moved (pole-W5 clear, no trees nearby); no console errors; screenshots `assets/models/previews/county-hotel-scene-{across,veranda}.png`. Earlier: **Reviewed, round 1: PASS** (reviewer, 2026-11-04): loads in the viewer with no errors (10,234 tris, 8 materials, TEXCOORD_0 + 1, all colour maps 1K, 2K lightmap); matches the c. 1905 photo (8-bay two-storey veranda, X-panel posts, lattice railing, bracketed porch and main cornices, 12 shuttered 3rd-floor windows, lamp, south bay, rear wing); clean soft-shade lightmap, pale paint not overbright. Next: show the owner, then scene-integrator. Earlier: **Built** (blender-builder, 2026-11-04): `assets/models/county-hotel.glb` (1.81 MB, 10,234 tris, 8 materials, TEXCOORD_0 + 1), 2K lightmap `assets/textures/county-hotel-lightmap.jpg`, **LIGHTMAP_SCALE 1.1087**; scripts `tools/blender/county_hotel.py` + `_bake.py` + `_preview.py`, `tools/prepare_county_hotel_textures.py` (painted-brick recolour + signs atlas); source `assets/models/source/county-hotel.blend`; previews `assets/models/previews/county-hotel-{front,three-quarter,detail,north}.png`. Earlier: spec approved by the owner (2026-11-04): pale painted walls, landmark detail (≤ 15k tris); asset-scout skipped (no downloads). Next: reviewer.

**What it is**: the town's second hotel, on the **west side of Main St, opposite the Rea Building
and a little north of the Union Hotel**. The lot was a tavern from the 18th century (County
Tavern, "County House" from 1855); **William H. Force** bought it after the Civil War and called it
**"The County Hotel"**; **Samuel H. Mount** bought it on **1 June 1891** ($25,000), and c. 1905 it
was "Mount's Hotel" (lettered lantern in the photo); it was **sold again in 1907, still as the
County Hotel** (buyer not named). The 1921 Sanborn labels it **"COUNTY HOTEL", "Heat: Steam",
"Light: Elec."**, with a 1-storey **"Bar & Pool Room"** wing behind. Architect Chris Pickell calls
the style **Italianate (c. 1850–70)** and found **solid brick exterior walls**. Replaced in the
1970s by the "New Market" shops (Don Shuman); a sandstone slab lettered "County Hotel" was long
in the sidewalk. **The 1920 proprietor is not known.**

What it looked like (1905–08 photos): a long **3-storey flat-topped block, 24 m front, 8 bays,
with a deep bracketed cornice and shuttered 2/2 windows**, and a **full-width 2-storey veranda over
the sidewalk**: square posts with long sunk "X" panels, a **diamond-lattice railing** on the upper
deck and a **bracketed porch cornice** just under the 3rd-floor windows. A cast-iron lamp standard
with a lettered lantern stood at the south end of the veranda.

**Planner decisions** (from the map and photos; owner to confirm)
1. **Footprint and height from the 1921 Sanborn** (frontage 23.86 m, main block 9.07 m deep,
   veranda 2.52 m, "3" storeys, "30'"), **form and details from the c. 1905 "Mount's Hotel"
   photograph** (sharp, near-frontal from the SE), checked against the 1906 and 1908 cards.
2. **Walls painted pale cream-buff (painted brick)** for 1920. Evidence conflicts: c. 1905 photo
   and 1906 tinted card = unpainted red brick; **1908 card = pale walls** (painted by then);
   1921 Sanborn = frame (yellow) with the **front and south walls marked grey "(Ir. Cl.)"
   (iron-clad)**; Pickell = solid brick. Pale painted is the latest evidence. **Owner option:
   red brick (reuse `polyhaven/red_brick.jpg` unchanged).**
3. **North end bay of the veranda enclosed on both floors** (glazed upper room, boarded ground
   floor with a window), as in the 1906 "Main Street – County Hotel" card and the 1906 tinted card.
4. **Lamp standard kept, lantern lettered "COUNTY HOTEL"** (it read "MOUNT'S HOTEL" c. 1905;
   name per 1907/1921). Whether it still stood in 1920 is a guess. No other signs (the
   "Jacob Veit Livery" board on the corner post c. 1905 is left out).
5. **Bar & Pool Room wing modelled as a simple 1-storey clapboard box** (visible through the open
   lot to the south); the rear porches are not modelled.
6. **Budget: recommend "landmark detail" cap 15k tris (target ~13k), 8 materials merged to one
   draw call.** Why: the façade is 24 m of repeated detail (≈ 70 scroll brackets, 8 bays of
   lattice railing, 18 posts, ~50 shuttered windows); at 10k the railing and brackets must be
   flattened and the building's character (it is the visitor's main west-side view north of
   Bloomfield Ave, opposite the Rea Building) would suffer. It is not a top landmark like the
   courthouse or Union Hotel, so not 30k. **Ordinary (10k) fallback**: see Budget.

**Sources**
- Map: 1921 Sanborn **sheet 2** [M1]: "COUNTY HOTEL / HEAT: STEAM / LIGHT: ELEC.", yellow
  (frame), **"3"** storeys, **"30'"**, a grey L-shaped strip along the inside of the front and south
  walls lettered **"(IR. CL.)"**, "o" marks (non-combustible roofs); street numbers **47, 49** (old
  514/515); a yellow **"2"**-storey strip across the whole front (the veranda). Pixel lines:
  **front wall x 3551; veranda front x 3600 (= the dashed property line); rear wall x 3377;
  north wall y 4520 (party line with the brick "Cobbler" building, 39–41); south wall y 4978**.
  South-wall canted 1-storey bay: base x 3380–3465, outer face x 3400–3440 at y 5001.
  Bar & Pool Room (1-storey frame): from the rear wall to x 3100, south edge (3372, 4985) →
  (3100, 4940), north edge (3340, 4855) → (3165, 4825), plus a small 1-storey bump at its NW
  end and a stoop on its south side. Rear porches: 2-storey x 3340–3377, y 4530–4650; 1-storey
  x 3340–3377, y 4785–4850. South of the hotel an open lot (y 4978 … ~5095, 6.1 m) to 51–57 Main.
- Photos (**none of the local `assets/photos/reference/` files or HABS photos show this hotel**;
  all checked). Viewed online for this spec, not saved to the project:
  - **Primary: "Mount's Hotel", c. 1905 (before Aug 1906)**, HCHS PX333, in Goodspeed "The
    County House, Part One":
    https://i0.wp.com/goodspeedhistories.com/wp-content/uploads/2025/11/Hotel-Tunison.jpg
    (3081 × 2516; from the street to the SE, front + south side; brick, cornice, 12 upper
    windows, 9 veranda posts with X panels, lattice railing, porch brackets, lamp, south bay,
    clapboard wing behind, two chimneys). All proportions below were scaled on it
    (≈ 63 px/m at the SE corner on the 1400-px copy, from cornice top = 9.15 m).
  - **"The County Hotel – 1908"** (WJH `flmngtncountyhotel08.jpg`): same viewpoint, **pale walls**,
    dark shutters, same veranda and lamp. Closest to 1920 for colour.
  - **"The County Hotel – 1906"** (WJH `flmngtncountyhtl06.jpg`, tinted): salmon/red walls, green
    shutters, brown trim; the north-end upper bay glazed; chimneys at both ends.
  - **"Main Street – County Hotel – 1906"** (WJH `flmngtnmainstrtcountyhtlvu06.jpg`, looking
    south from the north): **north-end veranda bay enclosed on both floors** (two windows in its
    north face upstairs, a window below), chimney mid-roof, flat roofline.
  - "Main Street and County Hotel – 1908" (WJH `flmngntnmainstcountyhtl08.jpg`, looking north,
    dark): confirms the long veranda and cornice; no detail.
  - Originals at `https://westjerseyhistory.org/images/hunterdon/flemington/data/images/<file>`.
    The orchestrator may ask asset-scout to save the four WJH cards **local-only** (gitignored)
    for the reviewer.
- Web text: Goodspeed Histories, "The County House, Part One"
  (https://goodspeedhistories.com/the-county-house-part-one/): names, Force, Mount 1891, 1907
  sale, Tunison, Pickell (Italianate, solid brick walls), New Market 1970s, "County Hotel" slab;
  "County House" series [W11] (18th–early 19th c. tavern; not used for the 1920 form).

**Placement** (west side, front faces east onto Main St)
- Entity position = centre of the veranda front line at sidewalk level:
  **(−10.30, 0.15, −112.07)**, `rotation="0 90 0"`; replaces the kit placeholder `#county-hotel`
  at (−10.3, 0, −111.8) (keep the id).
- Scene lines: veranda front x −10.30 (property line; map −10.26); **front wall x −12.82**;
  **rear wall x −21.88**; **north wall z −124.00**; **south wall z −100.14**; Bar & Pool Room
  wing to x −36.31. Cornices overhang the veranda front by 0.30 (to x −10.00), above 5.7 m.
- **Neighbours**: north, the brick "Cobbler" (39–41; front ≈ x −13.1, z −129.2 … −124.0) abuts
  the north wall. Its kit placeholder `#bldg-35-41-main` (front x −10.3, z −135.6 … −123.6)
  **overlaps the hotel by 0.4 m** — scene-integrator: shorten/shift it to end at z ≤ −124.05
  (not part of this model). South: an open lot 6.1 m wide, then the `#bldg-57-main` placeholder
  (z ≥ −93.4). Opposite: the Rea Building.
- **Street props**: pole-W5 (−6.9, −118) is 3.4 m in front of the veranda — clear; no street
  trees between z −95 and −130. The lamp standard (part of this model) stands at world
  ≈ (−9.70, 0.15, −102.2), 3.2 m from the curb.
- **Ground**: the veranda floor is the paved strip between the property line and the front wall
  (flush with the sidewalk top, local z 0), so no paving box is needed. All walls and the paving
  skirt to local z −0.20 (world −0.05; the side lot and rear yard are at world y 0).
- **Blender local frame**: front −Y, origin at the centre of the veranda front line at sidewalk
  level, **+X = north**, −X = south, z = 0 = sidewalk top. Main block X −11.93 … +11.93,
  Y 2.52 … 11.58; veranda Y 0 … 2.52. Sun "to sun" **(−0.40, 0.90, 0.36)** (front in shade,
  south side grazed, rear sunlit). Optional bake occluder (not exported): box for 39–41 at
  X +11.93 … +17.1, Y 2.8 … 11.6, z 0 … 8.5.

**Massing** (heights: cornice top = Sanborn 30' = 9.15 m; levels scaled on the c. 1905 photo)
- Main block **23.86 × 9.07 m**, 3 storeys. Ground floor 0.15 above the paving (one sill
  step at doors); **2nd floor ≈ 3.05; 3rd floor ≈ 6.15**.
- Main entablature: frieze band 8.10–8.75 (brackets 8.15–8.75), **cornice 8.75–9.15 projecting
  0.65**, all four sides (rear: plain fascia, no brackets).
- **Roof**: flat/very low tin deck (≈ 3°) behind the cornice, top ≤ 9.45; never seen in photos;
  dark grey.
- **Chimneys** (brick, 0.90 × 0.50, top **10.30**, 0.08 corbel cap): one on the south wall at
  Y 4.5 (≈ 2 m behind the front), one on the north wall at Y 4.5 (photo shows a north-end
  stack; position a guess).
- **Veranda**: full width (X −11.93 … +11.93), Y 0 … 2.52, 2 storeys: ground-floor posts on the
  paving; **upper deck top 3.10** (fascia beam 2.80–3.10); railing top 4.00; upper posts to 5.75;
  **porch entablature 5.75–6.40** (frieze with brackets 5.80–6.25, cornice 6.25–6.40 projecting
  0.30 at front and ends); porch roof (tin) slopes from 6.40 at the front to 6.55 at the wall
  (under the 3rd-floor sills).
- **South-wall bay** (1 storey, canted, map): on the south face X −11.93, base Y 7.00 … 11.43,
  outer face Y 8.30 … 10.38 at X −13.13; walls to 3.30, small cornice to 3.50, flat tin roof.
- **Bar & Pool Room wing** (1-storey frame, map): trapezoid in plan, corners (X, Y) =
  (−11.93, 11.58), (−5.55, 11.58), (−3.95, 26.00), (−9.95, 26.00); clapboard walls to **3.60**,
  low shed roof falling to the south (top 4.20 at the north wall), 0.25 eave. 2 windows on its
  south side, a door with one step at Y 19.0 (map stoop), plain elsewhere. The small NW bump is
  left out.

**Elevation details (1920 state)** — X from south (−) to north (+)
- **Veranda posts: 9 per floor, evenly spaced at X = −11.80 + 2.95 k (k = 0 … 8), front face at
  Y 0.** Ground posts 0.26 square, 0 → 2.80, with a 0.10 plinth block and a moulded cap
  (0.34 square, 0.12); upper posts 0.24 square, 3.10 → 5.75, same cap. Each post face shows a
  **long sunk panel with an "X"** (two X's stacked on the ground posts, one on the upper) — atlas
  texture, not geometry.
- **Upper deck**: fascia beam 0.30 deep across the front and both ends; deck edge at Y 0.
  **Railing**: 8 bays between the posts (and the two ends, Y 0 … 2.52), top rail 0.10 × 0.06 at
  3.94–4.00, bottom rail at 3.20–3.26, filled with **crossed diagonal slats** (0.04 × 0.03,
  at ±45°, 0.25 m apart = a diamond lattice, as the c. 1905 photo). The north bay has no railing
  (enclosed).
- **Porch entablature**: plain frieze board, **scroll brackets every ≈ 0.98 m (one over each post
  + two between: 25 on the front, 3 on each end)**, 0.45 tall, 0.30 deep, 0.10 wide; cornice
  with a 0.30 soffit. A sloping tin leader (downpipe) from the south end of the porch roof to the
  wall (as photo): optional.
- **Enclosed north bay** (X +8.85 … +11.93, Y 0.10 … 2.52, both floors): ground floor boarded
  (trim material, panelled), one 0.90 × 1.70 window in the front and one in the north face;
  upper floor glazed: front face **two 0.90 × 1.80 sash windows**, north face two, on a panelled
  dado 3.10–3.90.
- **Main front, ground floor** (behind the veranda, Y 2.52), per bay centre: bay 1 (X −10.33):
  **large display window 1.60 × 1.90** (sill 0.60) left + panelled door 0.90 × 2.30 right;
  bay 2: window; **bay 3: main entrance, double doors 1.30 × 2.60 with tall etched-glass upper
  panels, transom to 3.00**; bays 4–7: windows **0.90 × 1.70, sill 1.10**, 2/2, open louvred
  shutters; bay 8 behind the enclosure (one door 0.90 × 2.30).
- **Main front, 2nd floor** (behind the veranda): one opening per bay centre, bays 1–7:
  windows 0.85 × 1.70 (sill 3.60) with shutters in bays 1, 3, 5, 7; **glazed doors 0.85 × 2.30
  onto the deck in bays 2, 4, 6** (guess pattern; the photo shows a mix). Bay 8 behind the
  enclosure: one window.
- **3rd floor front: 12 windows, centres X = −10.94 + 1.99 k (k = 0 … 11)**, **0.80 × 1.20,
  sill 6.70**, 2/2 sash, plain frame 0.10, stone/painted sill, **open louvred shutters**
  (2 × 0.40 × 1.20). (Count 12 ± 1 on the photo.)
- **Main cornice brackets**: large scroll brackets 0.60 tall × 0.45 deep × 0.12 wide, **every
  ≈ 1.0 m (24 on the front, 9 on each side), a pair at each front corner**, with sunk panels in
  the frieze between them; cornice crown moulding.
- **South side** (X −11.93, Y 2.52 … 11.58; exposed to the open lot): 3rd floor **3 windows at
  Y 3.6, 6.9, 10.1**; 2nd floor **2 windows at Y 3.6 and 10.1**; ground floor 1 window at Y 3.6,
  then the canted bay (one 1.10 × 1.70 window in the outer face, a 0.60 × 1.70 one in each
  canted face). All with shutters, sizes as the front floors (2nd: 0.85 × 1.70, sill 3.60).
- **North side**: as the south upper floors (guess); the ground floor is hidden by 39–41.
- **Rear (west)**: 2nd and 3rd floors 5 windows each (no shutters), ground floor hidden by the
  wing and rear porches (2 windows north of the wing); plain fascia cornice. Guess.
- **Lamp standard** (cast iron, documented 1905–08): at **(X −9.90, Y −0.60)**; fluted base
  Ø 0.30 × 0.50, shaft Ø 0.10 to 3.00, **square lantern 0.40 × 0.40 × 0.70 (3.00–3.70)** with a
  pyramid cap and a small ball/spike finial to 4.10 (the eagle is simplified). Glass panes
  **lettered "COUNTY HOTEL"** (atlas, two words stacked, dark letters on pale glass).
- Not modelled: gutters, telephone/electric drops, the rear porches, the wing's NW bump,
  interiors, the c. 1905 livery sign.

**Materials & colours (1920)** — 8 materials (merged into one draw call by `baked-lighting`)
1. `walls` — **painted brick, pale cream-buff ≈ #D8CDB4**: new local recolour
   **`assets/textures/county-hotel/brick_painted_cream.jpg`** from `polyhaven/red_brick.jpg`
   (desaturate, lighten, ~30 % contrast so the coursing just shows), tile 1.4 m. (Owner option:
   unpainted red brick → reuse `polyhaven/red_brick.jpg`.)
2. `trim` — cornices, brackets, frieze, veranda posts/beams/railing/brackets, window frames, sash,
   enclosure boards, door frames: **off-white** — reuse **`courthouse/paint_white.jpg`**, tile 2.0
   m, bake tint (0.96, 0.94, 0.88) so it reads just lighter than the walls (1908 card).
3. `shutters` — shutters and doors: **dark green** — reuse **`polyhaven/door_paint_green.jpg`**,
   darkened (1906 tinted card: green; dark in all sepia views); louvre lines from the atlas.
4. `dark` — plain colour: glass ≈ #1E2226, roofs/tin ≈ #4A4C50, lamp iron ≈ #24262A.
5. `brick` — chimneys: reuse **`polyhaven/red_brick.jpg`**, tile 1.4 m.
6. `paving` — veranda floor strip: reuse **`lovells-restaurant/stone_bluestone.jpg`** (flags),
   tile 2.0 m (c. 1905 photo: flagged/brick walk under the veranda).
7. `clapboard` — Bar & Pool Room wing: reuse **`house-65-main/clapboard_cream.jpg`**, tile 1.6 m
   (c. 1905 photo: pale clapboard wing).
8. `signs` — **new locally generated atlas `assets/textures/county-hotel/signs_atlas.jpg`, 1024²**
   (Pillow script `tools/prepare_county_hotel_textures.py`, own work, logged in SOURCES.md):
   louvre pattern (dark green slats with shadow lines), **post face with a long sunk "X" panel**
   (off-white, shadowed edges; one cell for the double-X ground post, one single-X), lantern pane
   "COUNTY HOTEL" (dark serif capitals on pale amber glass).
- **New for asset-scout: none** (2 locally generated files). One **2K lightmap**
  `assets/textures/county-hotel-lightmap.jpg` (front, veranda and south side weighted up; rear,
  north wall and roofs down).

**Weathering**: a 1850s–60s building in a working hotel, kept up but not new: soot under the
main and porch cornices; grey streaks under the 3rd-floor sills and bracket feet; paint chalkier
and slightly dirtier on the south wall; dark scuffing on the lower 0.6 m of the ground-floor
wall and the post plinths; the paving darker and worn along the door line and at the bay-3
entrance; railing paint a little grey; rust stain under the lamp lantern; tin roofs dull; soot
on the chimney tops; the clapboard wing greyer than the hotel.

**Budget**: **recommended cap 15k triangles, target ~13k**: walls with openings ~1.2k; ~55
windows (frames, sash, glass, sills) ~2.8k; ~45 shutter pairs as boxes ~1.1k; ~70 main + porch
scroll brackets (10-point profile) ~2.6k; railing lattice (8 bays + ends, slats as thin boxes)
~2.0k; 18 posts with caps and plinths ~0.6k; cornices, friezes, beams, porch roof ~0.8k; doors
and enclosure ~0.6k; south bay ~0.3k; wing ~0.3k; chimneys, lamp ~0.4k; paving, roof ~0.1k.
**If the owner chooses ordinary (≤ 10k)**: railing as a top/bottom rail with one diagonal per
0.5 m, porch brackets only over the posts (9), main brackets every 2 m, rear/north windows as
flat inset panels. Textures: 6 reused 1K maps + 2 generated (1 recolour, 1 atlas), one 2K
lightmap. Files: `tools/blender/county_hotel.py` + `county_hotel_bake.py` (+ `_preview.py`),
`assets/models/source/county_hotel.blend`, `assets/models/county-hotel.glb` (≤ 5 MB, expect
~2 MB), previews `assets/models/previews/county-hotel-*.png` (incl. one from the SE at street
level matching the c. 1905 photo's viewpoint, one from the north on the west sidewalk
matching the 1906 "Main Street – County Hotel" card, one frontal).

**Acceptance checks for the reviewer**
1. Main block 23.86 × 9.07 m, cornice top 9.15 ± 0.2 m; veranda 2.52 m deep across the full
   front; origin at the centre of the veranda front line at sidewalk level, front −Y, **+X = north**.
2. **Two-storey veranda with 9 evenly spaced posts per floor (8 bays)**, posts showing sunk "X"
   panels, a **diamond-lattice railing** on the upper deck, and a **bracketed porch cornice just
   below the 3rd-floor windows**.
3. **12 shuttered 3rd-floor windows** across the front above the porch roof; deep main cornice
   with closely spaced scroll brackets (≈ 1 m) on the front and both sides; flat roofline (no
   visible roof).
4. **North-end veranda bay enclosed on both floors**, glazed upstairs.
5. South side: 3 / 2 / 1 windows (3rd / 2nd / ground) plus a **1-storey canted bay** at the rear
   corner; a brick chimney near the front on the south wall.
6. Ground floor: display window + door in the south bay, **double main entrance in bay 3**,
   shuttered windows elsewhere.
7. Cast-iron **lamp standard with a lantern lettered "COUNTY HOTEL"** at the south end, in front
   of the veranda.
8. 1-storey clapboard **Bar & Pool Room** wing behind, reaching 14.4 m beyond the rear wall.
9. Walls read **pale cream-buff with faint brick coursing**; trim off-white; shutters dark green;
   chimneys red brick.
10. ≤ 15k triangles (or ≤ 10k if the owner chose ordinary), ≤ 8 materials, GLB ≤ 5 MB,
    TEXCOORD_0 + 1, 1K colour maps, 2K lightmap; with the WSW sun the front and veranda are in
    soft shade, the south wall grazed; nothing floats at the side lot or the rear yard.

**Integrator notes (scene, not the model)**
- Replace `#county-hotel` with the GLB at **(−10.30, 0.15, −112.07)**, rotation 0 90 0,
  `baked-lighting` with the bake's LIGHTMAP_SCALE; keep the id.
- Shorten/shift `#bldg-35-41-main` so it ends at z ≤ −124.05 (0.4 m overlap today).
- No paving box (the model's veranda floor covers x −10.30 … −12.82).

**Photos vs 1920**: the latest views of the hotel are the 1908 cards, 12 years early. Taken from
them: pale walls, the veranda, lamp and the enclosed north bay. From the sharper c. 1905 photo:
all proportions and details. Left out as earlier: "MOUNT'S HOTEL" lantern lettering, the livery
sign. The 1921 Sanborn confirms the 1920 footprint, height, veranda and rear wing; its "(Ir. Cl.)"
note on the front and south walls may mean these walls were sheathed in sheet metal by 1921,
which the model does not show (no evidence of its pattern).

**Pure guesses (owner to check)**
1. Wall finish in 1920: pale painted brick (1908 card) vs red brick (c. 1905, 1906) vs iron
   cladding (Sanborn "Ir. Cl."); colours of trim and shutters (one tinted card).
2. The lamp standard and its "COUNTY HOTEL" lettering still there in 1920.
3. 2nd-floor door/window pattern behind the veranda; ground-floor openings in bays 2 and 4–8.
4. North-wall windows, rear wall, chimney positions, roof form, the wing's roof and openings.
5. South bay shape: canted per the 1921 map (the c. 1905 photo shows a squarer 1-storey
   projection; the map is followed).
6. Window count 12 on the 3rd floor (±1) and the bracket spacing (≈ 1 m) from one photo.
7. The 1920 proprietor (unknown; nothing in the model depends on it).

### Block at 40–46 Main St: "Auto Sales" (40–42) and "Shoe Shine & Fruits" (44–46)

**Status:** Spec approved by the owner (2026-11-04): **map-true** placement (44–46 on the 1921 street line, sidewalk narrows to 2.1 m), ordinary building (≤ 10k tris). Asset-scout skipped (no downloads needed). blender-builder 2026-11-04: **built** `assets/models/block-40-46.glb` (4,821 tris, 8 materials, 1.43 MB, 2K lightmap, LIGHTMAP_SCALE 1.2152), previews `assets/models/previews/block-40-46-{front,three-quarter,detail}.png`.. reviewer 2026-11-04: **PASS (round 1)** — loads with no errors (4,821 tris, 8 materials, UV2), cornices 9.15 / 6.10, 1.98 m step, 2.6 m arch, signs legible, clean lightmap. **In scene (scene-integrator, 2026-11-04)** at (8.60, 0.15, −116.55), rotation 0 −90 0, replacing `#bldg-40-46-main` (id kept); faces Main St, 44–46 1.98 m in front of 40–42; merged 8 materials → 1 draw call; `#bldg-32-38-main` trimmed to z −137.6 … −124.05 (width 13.55, height 7.5 and depth 12 kept, hides 40–42's open north wall, no gap from the street); passage to the Rea open; no props moved (pole-E6 at z −124 and wires clear of the awning); fruit stand `goods-G4` (shop_goods) at (8.05, 0.15, −112.6) leaves ~1.2 m of walk; screenshots `assets/models/previews/block-40-46-scene-{street,sidewalk}.png`.

**What it is**: the row of **frame (wooden) buildings just north of the Rea Building**, across a
3.3 m passage. The 1921 Sanborn shows **two buildings**: **40–42, a 3-storey frame building
(30 ft) used for "Auto Sales"**, with an arched drive-through at no. 40 and a 1-storey porch with a
canted show window at no. 42; and **44–46, a 2-storey frame building (20 ft) used for "Shoe Shine
& Fruits"**, standing right on the street line, with two 2nd-floor bay windows over the passage.
**No history of either building was found** (Goodspeed Histories, HCHS and West Jersey History
searched 2026-11-04); the names of the 1920 dealer and the shoe-shine/fruit man are not known.
The "Flemington Garage Co." sign with an arrow on the Rea Building's Bloomfield side (1909 card)
and the 1909 "Flemington Garage" card (a 1-storey concrete-block garage on a corner) are a
**different business and building**, not this one.

**Planner decisions** (owner to confirm)
1. **One model, "block-40-46", in 3 clearly separate parts**: (A) 40–42, 3-storey frame;
   (B) 42's 2-storey rear wing; (C) 44–46, 2-storey frame with a 1-storey rear part. Different
   clapboard colours and cornices so they read as separate buildings.
2. **Placement true to the map**: 44–46 stands **on the map's street line, 2.25 m in front of the
   Rea Building's front wall** (scene x 8.60), so here the sidewalk narrows to 2.1 m. The scene's
   property line (x 10.30) is a simplification; on the 1921 map the east street line runs at
   scene x ≈ 8.5 here. Alternative (b) in the guesses below.
3. **Ordinary building: cap 10k triangles, target ~7k; 8 materials; no downloads** (1 generated
   sign/awning atlas).
4. No period photo shows the fronts. **Form and all façade details are period-typical guesses**
   for small-town frame commercial buildings (cf. the frame block beside the Nevius store in
   `flmgtnmainststores.jpg`): flat roofs behind bracketed cornices, 2/2 sash windows, shutters.

**Sources**
- Map: 1921 Sanborn **sheet 2** [M1], pixel box **x 3955–4460, y 4515–4830**; all yellow (frame),
  "o" (slate/metal roof) marks. Lines: **east street line x ≈ 3960** (thick); **40–42 front wall
  x 4000**, rear wall x 4177; **north wall y 4520** (shared with 36–38 "Meats", 2-storey frame);
  **40|42 partition y 4577** (door at x 4085–4105); **42|44 wall y 4697**; **44–46 south wall
  y 4806**; lot line y 4827; Rea north wall y 4868. Labels: 40 "3" with a **half-circle at the
  front (x 4000) and rear (x 4177) walls, y 4522–4572** (read as arched openings; no label);
  42 "3", **"30'"**, "AUTO SALES"; 42 porch "1", x 3966–4000, y 4580–4697, with a canted bay
  x 3978–4000, y 4600–4665 (flat front y 4612–4650); 42 rear wing "2", x 4177–4320,
  y 4587–4683; 44–46 "2", **"20'"**, "Shoe Shine & Fruits", x 3961–4297, y 4697–4806, front on
  the street line; **two boxes on the south wall marked "2d only"** (2nd-storey projections)
  x 4058–4115 and x 4232–4297, y 4806–4818; 44–46 rear: 1-storey x 4297–4372 with a slanting
  south wall (4297, 4806) → (4372, 4785), frame porch "1" x 4372–4397 and a 1-storey shed
  x 4397–4460, y 4688–4712 (not modelled). Yard behind 40 (white) to a dashed fence at x 4560.
- Photos: **no reference photo shows the fronts.** Seen:
  - `flemington_-_main_street_north_from_bloomfield_avenue_-_flemington_garage_-_c_1910.jpg`
    [P37] and `flmngntnmainstandbloomfieldaveview09.jpg` [P38] (West Jersey History, viewed
    online, not saved): Rea Building from the SW; beyond its north wall a lower building with a
    roof/wall-top line running parallel to the street, half hidden by a large tree at the east
    curb. Only proves something lower stood there; no details.
  - `flmingtngarage09.jpg` [P39] (viewed online, not saved): the Flemington Garage, a 1-storey
    rock-faced concrete-block building with a stepped parapet; not on this lot (see above).
  - Checked, not showing it: all local `assets/photos/reference/*.jpg` incl. the 1906–08 PO cards
    (taken from in front of this block looking south) and `flmngtnbankandpovu08.jpg`; no HABS.
  - Note (planner, 2026-11-10): the HCHS Stryker plate c. 1906–10 (`hchs-stryker-main-st-south-from-hall-grocery.jpg`, local only) shows the Rea's raised stoops at its left edge (full-res x ≈ 700–900) and, at about the 40–42 position (fit ±5 m), a frame front with stacked front bay windows under a pyramid roof, a balustraded deck on a 1-storey porch and striped awnings — not the built plain flat-cornice 40–42; too uncertain in position (could be 32–38) to serve as a check, so no change.
- Web: Goodspeed Histories roof-arch series [W7] and Clock Tower article [W17] (no mention of
  40–46); West Jersey History index [W16]. Searches for 40/42/44/46 Main and a 1920 Flemington
  auto dealer found nothing.

**Placement** (east side, front faces west onto Main St)
- Entity position = centre of the block's front line at sidewalk level: **(8.60, 0.15, −116.55)**,
  `rotation="0 -90 0"`; replaces the placeholder `#bldg-40-46-main` at (10.3, 0, −115.8) (keep
  the id).
- **Blender local frame** (as the Rea Building): front −Y, origin at world (8.60, 0.15, −116.55),
  **+X = south**, Y = depth (world x − 8.60), z 0 = sidewalk top. Map → local:
  X = (py − 4806) × 0.0521 + 7.45, Y = (px − 3961) × 0.0521.
- Scene lines: block **z −124.00 … −109.10** (14.90 m); 44–46 front x 8.60; 40–42 front wall
  x 10.58 (0.27 m in front of the Rea front at 10.85); 42 porch front x 8.81.
- **Neighbours**: Rea Building north wall z −105.76 → **3.34 m open passage** (the Rea spec's
  "2.0–2.3 m" took the lot line at y 4827 as this wall); the 2nd-floor bays reach z −108.47.
  North: 36–38 "Meats" (2-storey frame), placeholder `#bldg-32-38-main` (z −137.6 … −123.8)
  overlaps by 0.2 m: the integrator trims it to end at z ≤ −124.05.
- Props/trees: pole-E6 (6.9, −124) is clear (1.7 m from the front); no trees or other props
  here. The awning stops at x 7.00 (curb x 6.52).
- Sun "to sun" **(0.40, −0.90, 0.36)**. **Bake occluders (not exported)**: Rea Building box
  X +10.79 … +26.70, Y 2.25 … 17.45, Z 0 … 11.0 (shades the passage wall); 36–38 box
  X −20 … −7.45, Y 0.4 … 18, Z 0 … 6.1.

**Massing** (footprints = Sanborn; heights = Sanborn eave heights taken as cornice tops, as for
the County Hotel; storey splits are guesses)

| Part | Local X (N → S) | Local Y | Storeys / height | Roof |
|------|-----------------|---------|------------------|------|
| A. 40–42 main | −7.45 … +1.67 (9.12 m) | 1.98 … 11.20 (9.22 m) | 3, cornice top **9.15** (30') | flat tin, 2° back slope, deck 8.95 |
| A1. 40 archway (inside A) | −7.45 … −4.51 | 1.98 … 11.20 | tunnel through the ground storey | — |
| A2. 42 porch | −4.51 … +1.67 | 0.21 … 1.98 | 1, roof 3.55 → 3.30 | shed, tin |
| B. 42 rear wing | −3.95 … +1.05 | 11.20 … 18.65 | 2, cornice top 6.10 (guess) | flat tin |
| C. 44–46 main | +1.67 … +7.45 (5.78 m) | 0 … 17.45 (17.45 m) | 2, cornice top **6.10** (20') | low shed roof falling to the rear, tin (guess) |
| C1. 2nd-floor bays (south) | +7.45 … +8.08 | 5.00 … 7.97 and 14.06 … 17.45 | 2nd storey only, 3.55 … 5.85 | hipped tin cap |
| C2. 44–46 rear | +1.67 … +7.45 → +6.36 (slanting S wall) | 17.45 … 21.36 | 1, 3.30 | shed |

- A levels: ground storey 0 … 3.60 (2nd floor 3.75), 3rd floor 6.45, frieze 8.40–8.85, cornice
  8.85–9.15 projecting 0.55. C levels: ground 0 … 3.40 (2nd floor 3.55), frieze 5.40–5.80,
  cornice 5.80–6.10 projecting 0.45. All walls skirt to −0.20; the passage and yard are at
  world y 0.
- **Apron slab** (stone, top 0.0, skirt −0.20) under A1/A2: X −7.45 … +1.67, Y 0 … 1.98
  (fills the strip in front of 40 and under the porch; the sidewalk box ends at x 10.30).
- Exposed side walls: A's north wall above 6.10 (36–38 is 2-storey) and A's south wall above
  6.10 (over C); C's south wall full length on the passage.

**Elevation details (1920 state; guesses unless marked "map")**
- **A, 40 (archway)**: front **round-arched opening 2.60 wide** (map), centred X −5.98, springing
  2.25, crown 3.55; plain board archivolt 0.20 with a keyblock. Tunnel: board walls, plank
  ceiling at 3.60, floor stone material darkened with **oil stains**; **rear arch** the same with
  **closed plank double doors** (so the yard need not be modelled). Over the arch: one window per
  upper floor at X −5.98.
- **A, 42 ground (behind the porch)**: **canted show window** (map): flat front 1.98 wide at
  Y 0.85, X −2.65 … −0.67, sides back to the wall at X −3.28 and +0.11; bulkhead 0.15–0.75,
  plate glass 0.75–2.90, small cornice to 3.10. **Shop door** X +0.90, 1.00 × 2.30 glazed +
  transom (sale-room entrance); **stair door** X −3.90, 0.90 × 2.30 panelled (upper floors).
- **A2 porch**: deck 0.15 (one step up from the apron; stone step 0.30 deep along the front),
  4 square chamfered posts 0.14 at X −4.40, −2.80, +0.05, +1.56 on Y 0.30; plain fascia 0.30
  carrying an **"AUTO SALES" board** (atlas; wording from the Sanborn label, the sign itself a
  guess); shed roof tin.
- **A upper floors**: **4 bays**: X −5.98 (over 40) and −3.40, −1.42, +0.56 (over 42). 2nd floor
  windows 0.85 × 1.65, sill 4.35; 3rd floor 0.85 × 1.50, sill 7.00; 2/2 sash, cased trim 0.12
  with a small cap cornice; **open louvred shutters, dark green**. Corner boards 0.15 at both
  ends.
- **A cornice**: frieze 8.40–8.85, cornice 8.85–9.15 projecting 0.55, **scroll brackets in pairs
  at both corners + singles at ~1.5 m** (8 on the front), returns 0.55 on both sides. North wall
  above 6.10: 2 windows on the 3rd floor at Y 4.5, 8.5; south wall above 6.10: 2 windows at the
  same Y; rear wall: 2 windows per floor, plain.
- **B rear wing**: plain clapboard, 2 windows per floor on its north and rear faces, a plank door
  on the north (yard) face; simple cornice board. Low detail (seen only from the passage/yard).
- **C, 44–46 front** (5.78 m): ground: **shop front** between corner pilasters 0.25: two doors
  (44 north at X +2.30, 46 south at X +6.80), each 0.90 × 2.30 glazed + transom, recessed 0.40;
  between them a **display window** X +2.90 … +6.20 on a bulkhead 0.15–0.70, glass to 2.85; sign
  band 2.95–3.40 with two boards **"SHOES SHINED"** (north half) and **"FRUITS"** (south half)
  (wording guess); shop cornice 3.40–3.55. **Striped awning** X +1.85 … +7.30: roller at 2.95,
  out to **Y −1.60 at 2.35**, valance 0.20, 2 iron arms. 2nd floor: **2 windows** at X +3.25,
  +5.85, 0.80 × 1.45, sill 3.90, shutters as A.
- **C cornice**: frieze 5.40–5.80, cornice 5.80–6.10 projecting 0.45, 4 brackets (corners and
  thirds); returns 0.45.
- **C south (passage) wall**: ground floor 3 windows (0.80 × 1.50, sill 1.00) at Y 3.0, 9.5,
  12.5 and a side door 0.90 × 2.20 at Y 11.0; **two box bays on the 2nd floor only** (map C1):
  0.63 out, floor apron at 3.55 on 3 small brackets each, **2 windows on each south face**
  (0.75 × 1.40, sill 3.90), plain ends, hipped tin cap 5.85 → 6.05; one plain window at Y 11.0
  between them. North wall (above A2/B, mostly hidden): plain. C2 rear: 1 window, plain.
- Not modelled: gutters/downpipes, wires, the 44–46 rear porch and shed, interiors (except the
  dark tunnel and a dark back panel behind the show window), goods: the integrator can place a
  street-props **`shop_goods`** group before the 44–46 display window (crates and a barrel read
  as the fruit stand).

**Materials & colours (1920, all guesses: no colour evidence)** — 8 materials, merged to one
draw call by `baked-lighting`
1. `clap_a` (A, B): clapboard, **pale buff-grey ≈ #B9AE96**; reuse
   **`courthouse/clapboard_buff.jpg`**, tiled as on 65 Main (≈ 0.11 m board exposure).
2. `clap_b` (C): clapboard, **cream-white ≈ #DCD6C4**; reuse **`house-65-main/clapboard_cream.jpg`**
   (bake tint lighter if needed), same tiling.
3. `trim`: cornices, brackets, corner boards, window frames, sash, porch posts, archivolt:
   **off-white ≈ #E4DFD2**; reuse **`polyhaven/trim_paint_cream.jpg`**, tile 2.0 m.
4. `green`: shutters, doors, 44–46 shop-front pilasters and bulkhead, the arch's rear doors:
   **dark green ≈ #2F4A36**; reuse **`polyhaven/door_paint_green.jpg`**, tile 0.8 m.
5. `roof`: porch, bay caps, all roofs: reuse **`county-offices/roof_tin_redbrown.jpg`**, tile
   2.0 m (main roofs bake-tinted greyer; barely visible).
6. `stone`: apron, porch step, door sills, tunnel floor: reuse
   **`lovells-restaurant/stone_bluestone.jpg`**, tile 2.0 m.
7. `dark`: glass ≈ #1E2226, tunnel interior, awning arms; plain colour.
8. `signs`: **new generated atlas `assets/textures/block-40-46/signs_atlas.jpg`, 1024²** (Pillow,
   `tools/prepare_block_40_46_textures.py`, own work, log in SOURCES.md): "AUTO SALES" board
   (cream on dark green), "SHOES SHINED" and "FRUITS" boards (dark on cream), **red/cream
   striped canvas + valance** (resampled from `bank-building/awning_stripes.jpg`), louvre strip
   (as in the Rea atlas).
- **New for asset-scout: none.** One 2K lightmap `assets/textures/block-40-46-lightmap.jpg`
  (fronts weighted up; passage wall, tunnel and rear down).

**Weathering**: frame buildings repainted every few years: light chalking, darker paint under
cornices and sills, soot on cornice tops; grime and splash on the bottom 0.4 m; **dark oil and
tyre stains on the tunnel floor and apron** (auto sales); the passage (south) wall of 44–46
greyer and darker (in the Rea's shadow); awning sun-bleached; tin roofs dull, rust at the edges.

**Budget**: **ordinary, cap 10k, target ~7k**: walls/openings ~1.2k; ~30 windows ~1.6k;
22 shutter leaves ~0.3k; ~20 brackets ~0.7k; cornices/returns ~0.4k; archway + tunnel ~0.4k;
porch + show bay ~0.6k; 44–46 shop front + awning ~0.6k; 2 bays ~0.4k; rear parts ~0.3k. If over:
flat inset panels for the rear/north windows, fewer brackets. Textures: 6 reused 1K maps + 1
generated 1K atlas, one 2K lightmap. Files: `tools/blender/block_40_46.py` + `_bake.py`
(+ `_preview.py`), `assets/models/source/block-40-46.blend`, `assets/models/block-40-46.glb`
(≤ 5 MB, expect ~1.2 MB), previews `assets/models/previews/block-40-46-*.png` (frontal; from the
SW at the Bloomfield corner as in [P38]; from the north sidewalk at eye height; into the passage).

**Acceptance checks for the reviewer**
1. Origin = centre of the front line at sidewalk level, world (8.60, 0.15, −116.55); front −Y,
   **+X = south**; block 14.90 m along the street (X −7.45 … +7.45).
2. **Two clearly separate buildings**: 40–42 **3 storeys, cornice top 9.15 ± 0.2 m**, buff
   clapboard, front wall at Y 1.98; 44–46 **2 storeys, cornice top 6.10 ± 0.2 m**, cream
   clapboard, front at Y 0 (1.98 m in front of 40–42, 2.25 m in front of the Rea).
3. 40: **round-arched drive-through 2.60 m wide**, a dark tunnel with closed doors at the rear.
4. 42: 1-storey porch on 4 posts with an "AUTO SALES" board, a **canted show window** under it,
   shop door south of it, stair door north of it.
5. 40–42 upper floors: **4 shuttered windows per floor** (1 over the arch, 3 over 42); bracketed
   cornice with returns.
6. 44–46: shop front with **two doors and a display window**, "SHOES SHINED" / "FRUITS" boards,
   **striped awning** reaching Y −1.60 at 2.35 m; 2 shuttered windows upstairs.
7. 44–46 south (passage) wall: **two box bays on the 2nd floor only**, 0.63 m out, at
   Y 5.00–7.97 and 14.06–17.45; nothing crosses world z −108.4.
8. Rear parts present: 42's 2-storey wing to Y 18.65; 44–46's 1-storey rear to Y 21.36 with the
   slanting south wall.
9. ≤ 10k triangles, ≤ 8 materials, GLB ≤ 5 MB, TEXCOORD_0 + 1, 1K colour maps, 2K lightmap.
   With the WSW sun the fronts are lit and the passage wall is in the Rea's shade; nothing floats
   at the apron, passage or yard edges.

**Integrator notes (scene, not the model)**
- Replace `#bldg-40-46-main` with the GLB at **(8.60, 0.15, −116.55)**, rotation 0 −90 0,
  `baked-lighting` with the bake's LIGHTMAP_SCALE; keep the id.
- Trim `#bldg-32-38-main` to end at z ≤ −124.05.
- No paving box (apron slab in the model). Optional: a `shop_goods` group at about
  (8.05, 0.15, −112.6), rotation −90, under the awning, clear of the doors.

**Photos vs 1920**: no photo shows the building. The c. 1909–10 cards only show that something
lower than the Rea stood here behind a big curb tree.

**Pure guesses (owner to check)**
1. **Placement**: (a, chosen) map-true, 44–46 on the 1921 street line at scene x 8.60, which
   narrows the sidewalk to 2.1 m; or (b) shift the whole block +1.70 m so 44–46's front is on
   the scene property line x 10.30 (then 40–42 sits 1.4 m behind the Rea front and the Rea's
   steps stick out past 44–46).
2. The half-circles at no. 40 read as an **arched drive-through**; they could be another Sanborn
   mark. The rear doors are shown closed.
3. All façade details: window counts and sizes, shutters, brackets, shop-front layouts, porch
   posts, show-window glazing, roof forms (flat/shed), rear-wing openings.
4. All colours (buff and cream clapboard, off-white trim, green shutters, striped awning).
5. Sign wording ("AUTO SALES", "SHOES SHINED", "FRUITS") follows the Sanborn labels; the real
   signs and the dealer's car make are unknown.
6. Storey heights within the Sanborn 30'/20'; the rear wing's height (no map note).

### Palace Theatre (31 Main St, old no. 518)

**Status:** **in scene** (scene-integrator, 2026-11-10): `#palace-theatre` at (−10.30, 0.15, −145.52), rotation 0 90 0, intensity 0.9901; `bldg-27-main` placeholder resized to z −164.7 … −152.2 to hide the dark north wall (0.38 m slit); poster frames still show the first build's generic graphics until the planned re-export.
Built, baked and exported (blender-builder, 2026-11-10): `assets/models/palace-theatre.glb`,
2,688 tris, 8 materials, 1.58 MB, 2K lightmap, **LIGHTMAP_SCALE 0.9901**; previews
`assets/models/previews/palace-theatre-{front,three-quarter,detail,match-potter-card,alley}.png`.
Change from the spec: brick tiled at 1.4 m (as every other brick building; 2.0 m would give 0.10 m
courses). **Review round 1: PASS** (reviewer, 2026-11-10; from previews + GLB inspection, no browser).
(Spec approved by owner 2026-11-08.)

**What it is**: a **movie theatre, really on this spot by September 1921**. The Sanborn prints
"PALACE THEATRE" across a long 1-storey hollow-tile auditorium with a "STAGE", reached through a
narrow "ENTRANCE" hall in a 2-storey brick front block, beside a vacant store. The street number
31 is printed at this lot. A card captioned **"Palace Theatre & Potter Building, Flemington, N.J."**
shows the front. Evidence on the date, plainly:
- **Documented**: on the map, surveyed **Sept 1921**. Trade press names it from **Nov–Dec 1922**
  (Moving Picture World; David Chait, "Palace Theatre, Flemington", 1923, admission 15–25 cents).
  It was still running in 1931 (program) and 1951 (Film Daily Yearbook, via Cinema Treasures).
- **Not found**: an opening date, a builder, or any mention before Sept 1921. **So "c. 1920" is
  not proven**: it may have opened only in 1920–21. It is in the scene on the same basis as the
  other 1921 Sanborn tenants. The name is right for 1921.
- In Jan 1916 the town's picture house was the **Flemington Opera House on Bloomfield Ave**, a
  different building. Cinema Treasures' "silent picture days of the early 1900s" quotes a book
  caption (not seen); no dated evidence ties that to this building. Inferred: built between Jan
  1916 and Sept 1921 (hollow tile and the "Vac." store suit a recent building; neither proves it).
- A 2015 Cinema Treasures comment doubts the listed address (the card "looks nothing like" the
  Shaker Cafe building at 31 Main). The **1921 map's "31" settles the 1921 position**, whatever
  stands at 31 Main today.

**Planner decisions** (owner to confirm)
1. **Ordinary building: cap 10k tris, target ~5k.** It is a town landmark by use, but all the
   visible detail is one plain 12.6 m brick front; the 40 m auditorium and stage are blank boxes
   seen only from an alley. A landmark budget would buy nothing.
2. **One model, 3 parts**: A front block (detailed), B auditorium, C stage house (both low detail).
3. **Front on the scene property line x −10.30** (map −10.39, within reading error), so no forecourt.
4. **Parapet panel is left blank**: see Pure guess 1. Owner (2026-11-08) also confirmed keeping the
   theatre in the "c. 1920" scene on the 1921 map evidence.

**Sources**
- Map: 1921 Sanborn **sheet 2** [M1], pixel box **x 2390–3610, y 3960–4235**, all pink (brick
  colour). Labels: front block "2", **"26'"**, "ENTRANCE", "WALL 1ST ONLY" (partition y 4058),
  "VAC. S."; auditorium "1", "1B" (handwriting reads like "18"; the same mark at the stage is
  clearly "1B" = 1 storey + basement), "PALACE THEATRE / HEAT: STEAM / LIGHT: ELEC. / (HOLLOW
  TILE)"; stage "1B", **"26'"**, "STAGE", dashed line x ≈ 2620 (proscenium, read from position).
  Lines: front wall x 3598; front block rear x 3160 with a gap at y 4000–4020 (the entrance hall's
  way in); north wall y 3986, south wall y 4228 (front block); auditorium and stage north y 3965;
  rear wall x 2393. Roof marks: open circles on the front block, solid dots on the auditorium and
  stage (standard Sanborn key; meaning not confirmed on this sheet). A second height note beside
  the entrance strip (y 3990–4035) is unreadable, taken as 26' too. Thin solid line x 3608
  (0.5 m before the wall), unlabelled: see Pure guess 7.
- **Primary photo (the only view of the front)**: "Palace Theatre & Potter Building, Flemington,
  N.J.", printed card, from the street looking NW along the west side. Called "old postcard 1920s"
  by a Cinema Treasures commenter (date not otherwise established). View online, **do not save in
  the project** (rights unknown):
  https://photos.cinematreasures.org/production/photos/323405/1604912133/large.jpg
  It shows: the 2-storey brick front in the middle; **the sunlit south side wall with a downpipe**
  and the alley; frame no. 35 with a 2-tier porch at left; next building right (no. 27, map "D.G. &
  Clo.", inferred to be the "Potter Building") with a long awning. All dimensions marked "card"
  below come from a perspective fit: fitted to the wall ends and centre panel, the four window
  groups came out equal in width (1.9–2.1 m), so the fit is sound; heights assume the map's 26' is
  the shoulder of the parapet. ±0.3 m.
- Also viewed: 1931 program and 1941 manager photo (Cinema Treasures, theatre 15430, a lobby with
  ticket chopper, later than the period; do not use). **No local photo shows it**: all
  `assets/photos/reference/*.jpg` (contact sheet of all 32) show the south end only (HABS: court
  house, Wurts office, Union Hotel only); the 1913 "looking north" and c. 1905 commercial West
  Jersey cards do not show it; `flmngtnmainstrtnorthfromhtl08.jpg` could not be fetched.
- Web: [W-a] https://cinematreasures.org/theaters/15430 (Palace, 31 Main, 525 seats, 1944/51
  yearbooks, comments); [W-b] Lantern: https://lantern.mediahist.org/catalog/movingpicturewor59novd_1123
  (Nov–Dec 1922), https://lantern.mediahist.org/catalog/movpicwor61movi_0705 (1923, 15–25 cents,
  "retired farmers and residents"), https://lantern.mediahist.org/catalog/motionpicturenew131unse_1079
  (Opera House opens with pictures, Jan 15 1916); [W-c] https://cinematreasures.org/theaters/10586
  (Opera House, Bloomfield Ave). Only first pages of Lantern results were read, so an earlier
  mention may exist.

**Placement** (west side, front faces east)
- Entity = centre of the front at sidewalk level: **(−10.30, 0.15, −145.52)**, `rotation="0 90 0"`,
  id `palace-theatre` (replaces the placeholder at z −145.7).
- **Blender frame**: front −Y, origin as above, **+X = north**, Y = depth (world x = −10.30 − Y),
  world z = −145.52 − X. Map → local: X = (4107 − py) × 0.0521, Y = (3598 − px) × 0.0521.
- Scene lines: front block z −151.82 … −139.22; rear wall at world x −73.08.
- **Neighbours**: south, **3.5 m open alley** to no. 35 (north wall z −135.7, `bldg-35-41-main`);
  north, no. 27 nearly touches at the front (map 0.3 m, Y 0 … 4.4), with a 2.6 m light court behind.
- **Sun** "to sun" **(−0.40, 0.90, 0.36)**. **Bake occluders (not exported)**: no. 35 box X −21.3 …
  −9.9, Y 0 … 12, Z 0 … 7; no. 27 box X +6.4 … +19.2, Y 0 … 20, Z 0 … 7.6.

**Massing** (footprints = map ±0.1 m; heights as marked)

| Part | Local X (S → N) | Local Y | Storeys / height | Roof |
|------|-----------------|---------|------------------|------|
| A. Front block | −6.30 … +6.30 (12.60) | 0 … 22.82 | 2; parapet shoulder **7.92** (map 26') | flat, tin/tar, behind the parapet; side walls top 7.40 (card) |
| B. Auditorium | −6.30 … +7.40 (13.70) | 22.82 … 50.95 | 1 + basement; eaves **6.40 (guess, no map height)** | low gable, ridge along Y, ridge 7.70 (guess), tin |
| C. Stage house | −6.30 … +7.40 | 50.95 … 62.78 | 1 + basement, top **7.92** (map 26') | flat, tin (guess) |

Ground floor 0 … 4.25 (card), upper floor above. All walls skirt to −0.20 (alley and yard at
world y 0). B's roof must stay below A's parapet from the street. Upper-floor use: unknown.

**Elevation details: front** (from the card unless marked). X from south to north; openings
recessed 0.25.
- **Brick wall** full width, flat, no upper pilasters. **Corner piers and ground piers** run up to
  the belt, flush.
- **Ground openings, head 4.05** (S → N): corner pier −6.30 … −5.74 | **shop window** −5.74 … −0.60
  | pier −0.60 … 0.00 | **shop door opening** 0.00 … +1.70 | pier +1.70 … +2.55 | **theatre
  entrance** +2.55 … +5.45 | corner pier +5.45 … +6.30. (Partition at X +2.55 = map's y 4058.)
- Over every opening a **pale panelled band Z 2.85 … 4.00** (card: light flat panels; glazed or
  boarded is not visible). Shop window: glass 0.60 … 2.85 on a low pale bulkhead 0.15 … 0.60,
  one mullion at X −4.14. Shop door: pair of glazed doors. Bright triangles on the glass in the
  card are reflections: do not model.
- **Theatre entrance**: dark recessed lobby 1.00 deep, floor at sidewalk level, with a pair of
  doors (guess) and one small ticket opening (guess); two poster frames on the piers (artistic).
- **Belt course Z 4.25 … 4.80**, plain brick band projecting 0.15 across the full front (the
  strongest line of the front).
- **Upper floor: 4 window groups at X −4.50, −1.50, +1.50, +4.50**: each **two 1/1 sash windows
  side by side**, total 2.00 wide, Z 4.95 … 7.05, cream frames and a 0.08 mullion, no shutters.
  **Soldier-course hood** with a shallow segmental crown, Z 7.05 … 7.35, 2.20 wide, projecting
  0.06. **Pale stone keystone** over each centre, 0.22 wide, Z 7.10 … 7.55.
- **Stepped gable parapet**: shoulders at Z 7.92 from the corners to X ±3.95; step up 0.25, then
  sloping straight to **apex Z 8.65 at X 0**, with a thin coping. **Pale centred panel** X −0.73
  … +0.73, Z 7.37 … 8.06.
- **South corner pier** rises to Z 8.05 with a corbelled cap (card; may be a chimney). Small vent
  pipe behind the parapet near X −4.5 (optional).
- **Three white glass globe lamps**, Ø 0.36, centre Z 3.80, hung on short iron rods from under the
  belt, Y −0.35, at **X −5.54, +0.45, +2.88**.
- **South wall of A (lit, seen from the alley)**: brick, top 7.40, **no upper windows**; **iron
  downpipe** Ø 0.10 at Y 0.35, Z 0.15 … 7.40, curved foot, small bracket at the top. Two plain
  ground-floor doors at Y 7.7 and 14.0 (map "X" ticks; **form inferred**).
- **North wall and rear of A**: blank.
- **B / C**: plain walls, low detail. Two dark plank fire-exit doors on the south wall at Y 28.6
  and 39.6 (map ticks; inferred) with a concrete pad; plain rear door on C at Y 62.78, X −2.5
  (map "B" mark, inferred). No gutters, no signs.
- Not modelled: interiors, stage, projection booth, the sheds behind ("Auto", map x 2340–2665).

**Materials & colours** (no colour evidence: all guesses; the card is black and white). 8 materials,
merged by `baked-lighting`. No downloads, so asset-scout can be skipped.
1. `brick`: **dark red-brown** ≈ #7A4436; reuse `polyhaven/red_brick.jpg`, tile 2.0 m: front, belt,
   hoods, piers and side walls of A (A's south wall ~15% lighter by tint, as in the card's lit wall).
2. `tile_stucco`: B and C walls, **buff-grey roughcast** ≈ #A79F8B (**hollow tile documented,
   finish guessed**); reuse `courthouse/stucco_cream.jpg` tinted down, tile 2.0 m.
3. `trim`: sashes, frames, panel band, **cream** ≈ #DDD5C2; reuse `polyhaven/trim_paint_cream.jpg`, tile 2.0 m.
4. `stone`: keystones, panel, coping, bulkhead, pads, **pale buff**; reuse `county-offices/stone_buff.jpg`, tile 1.5 m.
5. `roof`: reuse `county-offices/roof_tin_redbrown.jpg`, tile 2.0 m (dulled).
6. `doors`: dark green-black; reuse `polyhaven/door_paint_green.jpg`, tile 0.8 m; fire doors bake-darker.
7. `dark`: glass ≈ #1E2226, lobby, iron; plain colour. Lamp globes: plain opal white ≈ #EDE8DA, unlit.
8. `signs`: new generated atlas `assets/textures/palace-theatre/signs_atlas.jpg`, 1024² (Pillow, own
   work, log in SOURCES.md): 2 poster frames, **PLAIN and EMPTY (owner, 2026-11-10: realism; the first build had generic figure graphics, to be replaced)**. No panel lettering.

**Weathering**: a fairly new building, so only lightly dirty: soot along the belt top and under
the coping, faint streaks below keystones, dark splash on the bottom 0.4 m and on the alley wall;
rust stain at the downpipe joints; B and C duller and more streaked. No moss, no heavy grime.

**Budget**: **ordinary, cap 10k, target ~5k**: walls/parapet ~0.5k; 8 sashes with hoods ~1.2k;
ground openings ~1.2k; 3 globes + rods ~0.6k (16 sides); downpipe ~0.1k; B/C + doors ~0.3k.
Textures: 6 reused 1K maps + 1 generated 1K atlas, one 2K lightmap weighted to the front and south
wall. Files: `tools/blender/palace_theatre.py` + `_bake.py`, `assets/models/source/palace-theatre.blend`,
`assets/models/palace-theatre.glb` (≤ 5 MB), previews `assets/models/previews/palace-theatre-*.png`
(frontal; from the SE matching the card; into the alley).

**Acceptance checks for the reviewer**
1. Origin at world (−10.30, 0.15, −145.52); front −Y, **+X = north**; front 12.60 m wide, total
   depth 62.8 m; auditorium and stage 1.10 m wider than the front, on the north side only.
2. Front: 2-storey brick, 7.92 m at the shoulders, **stepped low gable to 8.65 m at centre**,
   pale panel at centre.
3. Exactly **4 paired windows upstairs**, evenly spaced, cream, unshuttered, with arched dark
   hoods and pale keystones.
4. A plain **belt course across the whole front** at 4.25–4.80 m; no projecting cornice.
5. Ground floor reads, south to north: **wide shop window, door, then the theatre entrance at the
   north end**, separated by brick piers; a pale band above each.
6. **Three opal globe lamps** at the given X; **no marquee, canopy or awning** on this building.
7. South wall: brick, **no upper windows, one iron downpipe** near the front corner.
8. Auditorium lower than the front parapet; stage house back to 7.92 m.
9. ≤ 10k tris, ≤ 8 materials, GLB ≤ 5 MB, TEXCOORD_0 + 1, 1K maps, 2K lightmap. A preview from
   the SE matches the card's window rhythm, belt and parapet.

**Integrator notes**: replace the placeholder, keep the id. Extend `bldg-27-main` south to z −152.2
(map) so no 2.4 m hole shows beside the theatre. The alley needs no paving.

**1920 vs later**: no marquee on the card (the 1941 lobby photo is much later). Keep it marquee-free.

**Pure guesses (owner to check)**
1. **Parapet panel stays BLANK (owner, 2026-11-08)**: the card's central panel looks blank, and the
   owner does not want artistic liberties unless another photo shows lettering. No "PALACE" text.
2. **All colours** (card is black and white): brick shade, cream trim, buff stucco, dark doors.
3. Auditorium wall height (6.40) and roof form (no map height, not visible on the card); the finish
   over the hollow tile.
4. Opening date (not found); the "Potter Building" being no. 27 (from the caption order only).
5. Lobby contents, ticket window, poster frames; what the pale panels over the openings really are.
6. Fire doors and side doors, read from unlabelled map ticks; use of the upper floor.
7. Unlabelled thin map line 0.5 m before the front (not modelled; the card shows no canopy, only a
   low ledge at the shop window).

### Odd Fellows Hall / Hopewell Building (82–84 Main St, old nos. 537–538)

**Status:** spec written — awaiting user approval (planner, 2026-11-08). Not built.

**What it is**: **one building with two shops**, not two buildings: a 3-storey hall on the east side,
just south of the Nevius store, built by John C. Hopewell about 1881–82 (standing by Oct 1882 / the
1883 Bailey map). Its mark is a **big arch along the front of the roof**. Hopewell called it "Odd
Fellows Hall"; Sanborn called it "Hopewell Building" (1885). The front 10.7 m is **frame**, the
rear 10.6 m **brick** (yellow + pink on both the 1885 and 1921 maps). Goodspeed (March 2022) says it
was "about to come down"; whether it did is not confirmed, and it does not matter for 1920.

**What is documented, inferred, guessed**
- **Documented (map, Sept 1921)**: footprint, 3 storeys, 35', frame front + brick rear, "Jeweler"
  (no. 82, north) and "Gro." (no. 84, south), the partition between them.
- **Documented (photos, 1907 and 1910s)**: 7 windows on each upper floor, belt course, hoods, scroll
  brackets, arched crest with fan vent, clapboard north wall, one window per floor at the visible
  front of that wall (ground one shuttered), two shop fronts, two signboards, two scalloped awnings.
- **Inferred**: that the 1907–1910s front still stood unchanged in 1920 (no photo between the 1910s
  card and the 1921 map); door positions in the north shop; the stair door; rear-wing windows.
- **Pure guess**: all colours, roof form behind the arch, the south wall, front wall finish.
- **Tenants c. 1920**: only the map's trades. **Names not found.** John Ott, the jeweler here in the
  1880s–90s, went bankrupt in the early 1900s and left town, so do not use his name. Upper-floor
  use in 1920 is unknown (the Democrat-Advertiser had left "by" 1926; no date for its move).

**Planner decisions** (owner to confirm)
1. **Show the 1907–1910s state**, the closest to 1920. Not the earlier state (undated, before 1907):
   full-width porch roof, "ODD FELLOWS HALL", "THE DEMOCRAT-ADVERTISER", "JOHN OTT JEWELER".
2. **No lettering at all.** The two signboards exist on both cards but cannot be read (zoomed
   crops tried). They are modelled as **blank pale panels**. See Pure guess 1.
3. **Ordinary building: cap 10k, target ~7k.** One model: A frame front (detailed), B brick rear (low).
4. **z moves south**: the placeholder used the "+5593" sheet join, ~26 px off here (Nevius spec).
5. **Front on the scene sidewalk edge x 10.30**, in line with Nevius (map 0.18 m further back, within
   reading error), so no strip of bare ground shows.

**Sources**
- Map: 1921 Sanborn **sheet 3** [M2], pixel box **x 4020–4435, y 1300–1610**. Numbers 82 / 538 and
  84 / 537 at the street; "80" beside the alley. Lines (centres): front x **4023**; frame rear x
  **4227.5** (solid y 1306–1428, dashed y 1428–1575); rear wall x **4431**; north wall y **1306**;
  south wall y **1604**; shop partition (dashed) y **1427.5**. Labels: "3 / 35'" on both shops, "3"
  and "o" on the brick. The yellow wash runs on to x ≈ 4250 inside the brick walls (1.2 m, probably
  a colouring slip; ignored). Brick walls marked "12 12 16"; "///" ticks at north wall x ≈ 4345,
  south wall x ≈ 4250 and 4345. Sheet 2 stops north of this building, but shows the same street-line
  jog (y 6966 vs sheet-3 y 1342: join ≈ +5624, agreeing with the Nevius figure of +5619).
- **1885 Sanborn** (detail in the Goodspeed article): same yellow front, pink rear, "Jeweller" left,
  "D.G." right, "Print'g" and "Lodge" above.
- **Primary photo: `flmgtnmainststores.jpg`** ("Some Business Blocks", 1910s, local only), from the
  street NW of the building, looking SE: the north wall and whole front. Clearest copy. All Z and
  shop-front X values below come from a perspective fit of this card (front's vanishing point at
  card x 1271; 7 windows and 2 shops come out regular). ±0.3 m.
- `flemington_-_some_business_blocks_on_main_street_-_1907.jpg` (same view, 1907, also online as
  `flmngtnbizblocks12.jpg`, 1912): **the front is unchanged 1907–1912**.
- Web photos, **view only, do not save in the project**, both on
  https://goodspeedhistories.com/hopewells-buildings/ : `2-Odd-Fellows-Hall-copy.jpg` (straight-on,
  undated, with the old porch; used for window spacing and arch width) and `Snow-Bldg-copy.jpg`
  (undated, Hunterdon County Historical Society watermark; shows the roof box).
- `flmngtnmainstrycolrvu10.jpg`, `flmngtnneviusstoreandununionhtl09.jpg`, HABS: do not show it.
- Web: [a] Goodspeed, "Hopewell's Buildings", 18 Mar 2022 (above); [b] Goodspeed, "Fulper's Store",
  https://goodspeedhistories.com/fulpers-store/ (alley enlarged 1882; Hopewell owned next door).
  No data sheet or NRHP text was found for this address.

**Placement** (east side, front faces west)
- Entity = centre of the front at sidewalk level: **(10.30, 0.15, 9.09)**, `rotation="0 -90 0"`, keep
  id `bldg-82-84-main` (replaces the placeholder at z 7.7).
- **Blender frame**: front −Y, origin as above, **+X = south**, Y = depth (world x = 10.30 + Y), world
  z = 9.09 + X. Map → local: X = (py − 1455) × 0.0521, Y = (px − 4023) × 0.0521.
- Scene lines: north wall z **1.33** (Nevius south wall −3.33 + 4.66 m alley, measured on sheet 3),
  south wall z **16.86**, rear x 31.56. The visitor starts at (0, 0.15, 18), level with its south end.
- Neighbours: north, **4.66 m open alley** to Nevius; south, 4.7 m alley to brick 90–94 (map north
  wall about z 21.6; its placeholder starts at z 18.7, not this spec's job).
- **Sun** "to sun" **(0.40, −0.90, 0.36)**. **Bake occluders (not exported)**: Nevius box X −20.42 …
  −12.42, Y 0 … 32.25, Z 0 … 10.7; 90–94 box X +12.5 … +32, Y 0 … 26, Z 0 … 11.6.
- Known simplification: the map's heavy street line jogs 1.9 m further out (toward the road) south
  of y 1342. The scene's sidewalk keeps one straight edge, so this is not shown.

**Massing** (X, Y = map ±0.1 m)

| Part | Local X | Local Y | Storeys / height | Roof |
|------|---------|---------|------------------|------|
| A. Frame front | −7.765 … +7.765 (15.53, 51 ft) | 0 … 10.65 | 3; cornice top **10.67** (map 35') | low hip, tin (**guess**; map "o") |
| B. Brick rear | same | 10.65 … 21.26 | 3 (map); top 10.67 (**inferred**: no height note on it) | same low roof continues |

Floors (card): shop cornice top **3.60**; belt **6.68**; soffit **9.77**. Eaves line Z 10.00, ridge
along Y at Z 11.30 from Y 4 to 18 (**guess**, barely seen). Walls skirt to −0.20 on the sides and rear
(alleys at world y 0). Interiors not modelled.

**Elevation details: front** (centre X = 0; wall plane Y = 0 unless marked)
- **Wall**: pale and smooth, no visible boards on either card, though the map says frame (see
  Materials). Corner boards 0.18 wide, full height above the shop cornice.
- **7 windows on each upper floor, identical columns, at X = 0, ±1.85, ±3.75, ±5.85** (card and the
  straight-on photo agree within 0.3 m; the outer gap really is wider). Surround overall 1.10 wide;
  sash opening 0.86; two-over-two sash (**inferred**: card shows a centre bar and meeting rail),
  dark glass, set back 0.08.
  - 3rd floor: opening Z **7.60–9.25**, flat hood 9.25–9.45.
  - 2nd floor: opening Z **4.05–5.45**, flat hood 5.45–5.65. (Shorter than the 3rd floor, on both cards.)
  - Each: flat hood 1.30 wide projecting 0.10; sill 1.20 wide, 0.08 tall, projecting 0.05.
  - Blank wall stays between 2nd-floor hoods and the belt: **leave it blank.**
- **Belt course** Z 6.58–6.78, projecting 0.08, across the full front.
- **Upper cornice**: frieze Z 9.50–9.77; soffit 9.77; projection 0.65, top 10.67; **8 scroll brackets**
  at X = ±0.95, ±2.80, ±4.80, ±6.85 (between the windows), each 0.15 wide, 0.35 tall, 0.35 deep,
  simple low-poly profile, dark as in shadow.
- **Arched crest** (centre X 0): a false front in the plane Y +0.35, behind the cornice. Half-ellipse,
  **half-width 4.40**, sprung at the cornice top, **apex Z 12.90** (±0.3). Outer moulded band 0.30
  broad; curved top with **0.45 thickness** going back (lit edge on the card); inner moulding 0.35
  inside the outer. Tympanum smooth pale; **one half-round louvred vent** width 1.30, Z 10.90–11.60,
  centred. Four or five small scrolls on the arch band on the card: **not modelled** (too small).
- **Roof box** on the ridge at X 0, Y ≈ 8 (**position guess**): 2.2 wide × 2.0 deep, flared cap, top
  Z ≈ 12.90 (±0.5). Seen in the snow photo and the corner of both cards.
- **Shop front (dark painted wood)**, X from north, card fit:

| X from | X to | Part |
|--------|------|------|
| −7.77 | −7.32 | north corner pier |
| −7.32 | −5.21 | north shop, window (**hidden by the pole on the cards**; inferred) |
| −5.21 | −3.49 | north shop door, pair, recessed 0.60 (**position inferred**) |
| −3.49 | −1.41 | north shop, window |
| −1.41 | −1.25 | post (= map partition, X −1.44) |
| −1.25 | +0.17 | single plain door to the upper floors (**inferred**: dark opening on the card) |
| +0.17 | +0.88 | wide post |
| +0.88 | +3.14 | south shop, window |
| +3.14 | +5.09 | south shop door, pair, recessed 0.60 (**inferred**) |
| +5.09 | +7.37 | south shop, window |
| +7.37 | +7.77 | south corner pier |

  Bulkhead Z 0–0.45; glass Z 0.45–2.60; head 2.75. Fascia Z 2.75–3.55, dark; cornice Z 3.55–3.60
  (a shallow cap) projecting 0.25. Low pale stone sill along the front, Z 0–0.12, 0.25 deep, stopping at
  the door recesses.
- **Signboards** (documented but unreadable): two **blank** pale panels on the fascia, Z 3.03–3.50,
  flat and thin, X **−5.60 … −1.90** and **+2.30 … +6.90**, pale border 0.04.
- **Two awnings** (card, 1907–1910s; canvas is seasonal): sloping straight, from Z 3.00 at the wall to
  Z 2.45 at Y −1.60; scalloped valance to Z 2.25; X **−6.80 … +0.15** (north end hidden, guess) and
  **+0.65 … +7.40**. Two thin iron arms each. **No lettering.**
- **North wall (A)**: clapboard, Y 0 … 10.65; pale corner boards; **one column of windows at Y ≈ 1.80**
  (±0.5), surround 1.05 wide: 3rd floor Z 7.80–9.45; 2nd floor Z 4.25–5.50; ground Z 0.85–2.40 with
  **two open plain shutters** 0.45 wide. Further back the card is cut off by the Nevius store:
  **leave blank**. Cornice and soffit carry on along the full frame wall, with 5 brackets at 2 m centres
  from Y 0.5 (card shows 2–3 near the corner; rest inferred).
- **North wall (B)**, **south wall**: B = brick. **South wall of A (no source): clapboard, blank**, with
  no windows. Map "///" ticks = one column of 3 plain dark windows (**form inferred**), Z as the upper floors
  and ground 0.85–2.40, at Y **16.8** (north), Y **11.8 and 16.8** (south).
- **Rear wall**: plain brick, no detail (the map shows no attached shed).
- Not modelled: the wires and pole in front (already in the street props), the striped post on the card
  at X ≈ +0.5 (unclear object), awning ropes.

**Materials & colours** (no colour evidence; cards are black and white). **All guesses except the tone
relationships**: front much paler than the north clapboard (but that wall is in shade); pale window trim
stands out on it, so the clapboard is really mid-toned; shop front dark. 8 materials, all reused, so
asset-scout can be skipped.
1. `front`: smooth, pale buff ≈ #CFC2A4; reuse `polyhaven/trim_paint_cream.jpg` tinted, tile 2.0 m.
2. `trim`: hoods, surrounds, arch bands, corner boards, signs, cream ≈ #DDD5C2; reuse the same map, tile 2.0 m.
3. `clapboard`: warm mid drab ≈ #8A8072, boards ≈ 0.14 m; reuse a clapboard map below, tinted down.
   Use `house-65-main/clapboard_cream.jpg` (tile to suit the 0.14 m board).
4. `brick`: rear, red-brown; reuse `polyhaven/red_brick.jpg`, tile 2.0 m.
5. `roof`: reuse `county-offices/roof_tin_redbrown.jpg`, tile 2.0 m, dulled.
6. `shopfront`: dark green-black ≈ #2A2E28; reuse `county-offices/door_varnish_dark.jpg` darkened, tile 0.8 m.
7. `dark`: glass ≈ #1E2226, plain colour.
8. `awning`: reuse the bank's `awning_stripes.jpg` (colours a guess; the cards show pale canvas with faint stripes).
Low stone sill: use `trim`.

**Weathering**: about 40 years old in 1920, so moderate: soot under the cornice and hoods; faint streaks
below the sills; dark band on the bottom 0.4 m of the clapboard and brick; brick rear duller. No moss.

**Budget**: **ordinary, cap 10k, target ~7k**: 14 upper windows with hoods ~2k; arch, crest and vent ~1k;
cornice and brackets ~0.8k; shop front ~1.5k; awnings ~0.5k; north windows and shutters ~0.4k; shell, B and
roof ~0.5k. Textures: 6 reused 1K maps, one 2K lightmap weighted to the front and north wall. Files:
`tools/blender/odd_fellows_hall.py` + `_bake.py`, `assets/models/source/odd-fellows-hall.blend`,
`assets/models/odd-fellows-hall.glb` (≤ 5 MB), previews `assets/models/previews/odd-fellows-hall-*.png`
(frontal; from the NW matching the 1910s card; from the visitor's start).

**Acceptance checks for the reviewer**
1. Origin at world (10.30, 0.15, 9.09); front −Y, **+X = south**; 15.53 m wide, 21.26 m deep overall.
2. Front wall and front 10.65 m of the sides are frame; **brick only from Y 10.65 back**.
3. Cornice top at 10.67 m; **a large arched crest, centred, apex about 12.9 m**, about 8.8 m wide, with a
   half-round louvred vent.
4. **Exactly 7 windows on the 2nd floor and 7 on the 3rd**, stacked in columns, each with a flat hood; 3rd
   floor taller than the 2nd; outer spacing wider (X 0, ±1.85, ±3.75, ±5.85).
5. Belt course across the whole front at about 6.68 m; 8 scroll brackets under the cornice.
6. **Two shops plus a narrow door between them**, the partition at X about −1.4; dark wood fronts.
7. Two blank pale signboards and two scalloped awnings. **No lettering anywhere, no porch.**
8. North wall clapboard, darker than the front, with **one column of 3 windows near the front** and the
   ground one shuttered.
9. ≤ 10k tris, ≤ 8 materials, GLB ≤ 5 MB, TEXCOORD_0 + 1, 1K maps, 2K lightmap. A preview from the NW
   matches the card's window rhythm, arch and shop front.

**Integrator notes**: replace the placeholder, keep the id, move it to z 9.09. Keep the 4.66 m alley open.

**1920 vs earlier and later**: the porch and big lettering (before 1907) are gone. Odd Fellows or a newspaper
may still have used the upper floors in 1920; nothing on the outside shows it, so nothing is modelled.

**Pure guesses (owner to check)**
1. **Signboards**: blank pale panels (they exist but are unreadable). **Owner chose blank panels, 2026-11-10.**
2. **All colours**, including the awnings and whether the north wall's darkness is paint or shade.
3. **Front wall finish**: the map says frame and the wall reads smooth; flush boards or a stucco skin are both
   possible. Modelled as plain smooth paint.
4. Roof behind the arch; roof-box position; rear-wing height.
5. South wall of the frame part (never photographed): plain and windowless. A visitor sees it at a slant from
   the start. Windows could be added if the owner prefers, but no source shows any.
6. Awnings in 1920 (seen 1907–1910s), and that the shop fronts did not change by 1920.
7. North-shop door position, the stair door, double doors.

### Block at 35–41 Main St: frame "Gro." (35–37, old no. 517) and brick "Cobbler" (39–41, old no. 516)

**Status:** spec written — awaiting user approval (planner, 2026-11-08; re-checked 2026-11-10; **revised 2026-11-10 from two new local photos**: Stryker glass plate c. 1906–10 and the c. 1905 County Hotel photo). Not built.

**What it is**: **two separate buildings**, 0.44 m apart on the map, between the Palace Theatre alley
and the County Hotel. North: a **3-storey frame grocery with a two-tier front porch**. South: a
**small 2-storey-and-basement brick building set back 2.8 m** ("Cobbler" in 1921), tucked between the
porch and the hotel. Modelled as one GLB (as at 40–46) for one draw call.

**What is documented, inferred, guessed**
- **Documented (map, Sept 1921)**: both footprints, frame vs brick, 35–37 "3" storeys and "28'", the
  2-storey porch strip, "Gro.", the 2-storey frame wing behind, "Cobbler", numbers 35/37/39/41, old
  numbers 517/516.
- **Documented, 35–37, c. 1906–10 (Stryker plate, close up; primary for form)**: two-tier porch, **4 round
  Tuscan columns per tier** on one line; **upper deck rail of turned balusters**; **a frieze of short turned
  spindles under the porch roof** in every bay, with a **cut-out drop fringe** under it (seen in the two
  south bays); porch floor raised about 0.45 m with **two steps** along the front; a **straight stair with
  boarded sides and handrails both sides inside the south bay**; ground floor behind the porch: a shuttered
  window (south), a single door, a large shop window; **louvred shutters** on the 3rd-floor windows, which
  have **plain projecting heads**; **bracketed main eave** (scroll brackets); pale clapboard walls, trim
  darker than the walls. Awning rolled up; its scalloped valance lettered in three panels
  **"PRODUCE | JACOB R. HALL | GROCER"** (readable).
- **Documented, 35–37, c. 1905 (Goodspeed/HCHS PX333, right edge, past the hotel)**: clapboard front with
  **shuttered 2nd- and 3rd-floor windows (shutters open)**; the same stair (see Decision 6). The porch
  columns there are behind a tree.
- **Documented, 35–37, 1906 card**: 4 evenly spaced columns (projective check), the stair, unreadable
  fascia lettering. **1920s card** (closest to 1920): north end of the upper tier with **low balusters below
  and tall close vertical bars above**, an extended **striped scalloped awning** whose valance carries
  unreadable letters, a brick chimney near the north wall.
- **Documented, 39–41, c. 1905 only (Goodspeed, seen through the hotel's then-open north veranda bay;
  camera fit below)**: dark (unpainted) brick front; **a shallow balcony across the front at about 1.5 m with
  a rail of flat sawn balusters**, matching the map's dashed line 0.44 m before the wall; **tall windows with
  louvred shutters** opening onto it (upper part hidden by the hotel's upper deck); **under the balcony a
  shop door whose head is only about 1.1 m above the court, read as a basement entrance down steps** (fits
  the map's "2B" = 2 storeys + basement); a **lettered board over that door (unreadable)**; two small
  striped cone-shaped objects either side of the door (not identified, not modelled). Its 2nd floor and
  top are hidden. Stryker: hidden behind the grocery porch's south end (fit), nothing readable.
- **Inferred**: 3rd window on the 3rd floor (2 seen in 1906 and c. 1906–10, third behind a tree); awning
  full width; balcony full width; that the c. 1906–10 forms still stood in 1920 where the 1920s card cannot
  see (it agrees wherever it does see).
- **Pure guess**: all colours (every photo is black-and-white or sepia), 39–41's 2nd floor, top and parapet,
  how the 39–41 balcony is reached, the stair's upper flight, side walls, roof forms.
- **Tenants c. 1920**: only the map's trades ("Gro.", "Cobbler"). **Jacob R. Hall c. 1920: not confirmed.**
  Searched 2026-11-10: the HCHS item (https://hunterdonhistory.omeka.net/items/show/1740) is **undated** and
  says only "Jacob Hall Grocery store"; web searches for Jacob R. Hall as a Flemington grocer (directories,
  Find a Grave, Goodspeed, HCHS) found **nothing**; HCHS Collection 238 lists an undated photo of
  **"Wm. H. Hall & Son Groceries and Provisions" at 9–11 Main St** (a Hall grocery at another address, link
  unknown) and an undated "Childs' Cash Grocer" (no address). The **1920s card's valance lettering has a
  different layout** at the north end (a short group of 2–3 characters, a gap, then a group of about 10)
  where the c. 1906–10 valance reads just "GROCER": the text was probably changed, but it cannot be read.
  1920 census / Hunterdon County Democrat not searchable free online here.
- **Potter Building: not this block, as far as can be told** (unchanged: no "Potter" on this model).

**Planner decisions** (owner to confirm)
1. **Map-true setback, not the placeholder's x −10.3**: porch front x −11.12, brick wall x −13.02.
   A paved strip in the model fills the gap back to the sidewalk.
2. **Ordinary building: cap 10k, target ~7k** (raised from ~5k for the turned balusters, spindle frieze,
   brackets, shutters, stair and balcony now documented). One model, parts A–F below.
3. **Lettering: OWNER CHOSE (b), 2026-11-10: letter the valance "PRODUCE | JACOB R. HALL | GROCER" until contrary evidence turns up.** Fascia, hung board (1906) and 39–41's door board stay plain (unreadable).
   For the **awning valance**: (a, **recommended**) **plain valance**: the only readable text is c. 1906–10,
   Hall's tenancy in 1920 is not confirmed, the 1921 map says only "Gro." and the 1920s card's valance text is
   laid out differently; or (b) letter it **"PRODUCE | JACOB R. HALL | GROCER"** (dark serif capitals on the
   pale valance, three panels as in the Stryker plate), accepting it shows the c. 1906–10 tenant.
4. **Upper tier = 1920s card**: turned balusters (c. 1906–10, and the 1920s card's low balusters) **plus the
   tall close bars** above them (1920s only). Spindle frieze and drop fringe from c. 1906–10 on top.
5. **39–41 front follows the c. 1905 photo** where it is seen (balcony, shuttered tall windows, basement door);
   its 2nd floor and parapet stay a plain guess. **No awning, no sign text.**
6. **Stair: OWNER CHOSE: model it (B2), 2026-11-10.** Documented c. 1905, 1906 and c. 1906–10 (three photos,
   two viewpoints); the 1920s card cannot see the south bay. Both camera views agree that the visible flight
   runs **from the porch front back towards the building wall** (bottom by the south column, top near the
   wall); its upper part is hidden in every photo, so the landing and upper flight are a guess. Geometry
   below (part B2). Option (b): leave it out, as before.
7. **Shutters on 35–37** (documented c. 1905 and c. 1906–10), **open (pinned back)** for 1920 on the 2nd and
   3rd floors; the ground-floor window's shutters closed as in the plate.

**Sources**
- Map: 1921 Sanborn **sheet 2** [M1], pixel box **x 2965–3605, y 4290–4530** (pink and yellow).
  Line centres from a brightness profile:
  - **35–37 (yellow)**: street line x 3600.5; **porch front x 3583.5** (dashed, y 4292–4408); **front
    wall x 3545.5**; main rear x 3278.5 (gap y 4374–4395); wing partition x 3107.5; wing rear x
    2967.5; **north wall y 4293; south wall y 4416**; wing north y 4329. Labels (read rotated): main
    "3", **"28'"**, "o", "Gro."; porch "2", "o"; both wing parts "2", "o"; north shed "1", "o", x
    3191–3279, y 4298.5–4328.5, dashed north side. No partition between 35 and 37.
  - **39–41 (pink)**: **front x 3547; north wall y 4424.5; south wall y 4526.5**; main rear x 3345
    (dashed); 1-storey rear with a notch: x 3231–3345 at the north, x 3287.5–3345 at the south, arm
    bottom y 4466.5. Labels: **"28" twice near the front (y 4430–4490), most likely "2B" and "28'"**
    (now supported by the basement door in the c. 1905 photo), "o", "Cobbler"; rear "1" and a solid dot
    x 3304, y 4513 (meaning not confirmed). North wall "12 12".
  - Forecourt: blank strip x 3547–3600, bounded by lines y 4415.5 and y 4526.5, with an unlabelled
    **dashed line x 3555.5, y 4431–4518** (0.44 m before the wall) = **the balcony's outline** (c. 1905 photo).
  - Numbers on the street: 35, 37, 517 on the north lot; 39, 41, 516 on the south lot. All on sheet 2.
- **Primary photo for form: `assets/photos/reference/hchs-stryker-main-st-south-from-hall-grocery.jpg`**
  (local only, HCHS terms: personal study/research only; never commit or publish). Asher Stryker glass
  plate, c. 1906–10, looking south from the north end of no. 35–37; the porch fills full-res x ≈ 3300–4100,
  y ≈ 700–2150 (columns at x ≈ 3440, 3590, 3770, 3990). Camera fit on the County Hotel's posts and the east
  curb: camera ≈ (2.5, ~1.3, −160) ± 3 m, looking south, f ≈ 4500 px.
- **Primary for 1920: `palace-theatre-potter-building-card.jpg`** (local only; "1920s" per a Cinema Treasures
  commenter; card x 0–100): see Documented.
- **`goodspeed-mounts-hotel-c1905-hchs-px333.jpg`** (local only; c. 1905, from the SE): right edge, full-res
  x ≈ 2600–2960. A ground homography fitted on the hotel's 9 post bases and two wall corners puts 39–41's
  front at x ≈ 2576–2759 (seen between the last two posts at 2622 and 2750: it is 39–41, not the hotel) and
  35–37's front wall from x ≈ 2769, porch front ≈ 2886 (behind the tree trunk).
- `flmngtnmainstrtcountyhtlvu06.jpg` (1906, local only): 4 equal bays, stair, unreadable fascia lettering.
- Not showing this block: `flmngtnmainstnorth13.jpg`, `flmingtnmainstrtview.jpg`, all other local files, HABS.
- Web: HCHS item https://hunterdonhistory.omeka.net/items/show/1740 ; HCHS Collection 238 list
  https://hunterdonhistory.org/wp-content/uploads/2022/06/Collection-238-Container-List.pdf (Wm. H. Hall & Son
  at 9–11 Main; Childs' Cash Grocer); Goodspeed County House series
  https://goodspeedhistories.com/category/countyhouseseries/ ; Cinema Treasures https://cinematreasures.org/theaters/15430 .
  No data sheet or NRHP text found for these numbers.

**Placement** (west side, front faces east)
- Entity = centre of the front line (porch front) at sidewalk level: **(−11.12, 0.15, −129.89)**,
  `rotation="0 90 0"`, keep id `bldg-35-41-main` (replaces the placeholder at x −10.3, z −129.9).
- **Blender frame**: front −Y, origin as above, **+X = north**, Y = depth (world x = −11.12 − Y),
  world z = −129.89 − X. Map → local: X = (4406.9 − py) × 0.0521, Y = (3583.5 − px) × 0.0521.
- Scene lines: 35–37 north wall **z −135.82**, south wall **z −129.42**, porch front x −11.12, front wall
  **x −13.10**. 39–41 north wall **z −128.97**, front wall **x −13.02**, south wall **z −123.95** (map
  −123.66; trimmed to run 0.05 inside the hotel's north wall z −124.00). Frontage therefore 5.02 m.
- **Neighbours**: north, **3.4 m open alley** to the Palace (south wall z −139.22); south, the County
  Hotel abuts no. 39–41 and its veranda (x −10.30 … −12.82) closes the south side of the court.
- **Sun** "to sun" **(−0.40, 0.90, 0.36)** (front in shade). **Bake occluders (not exported)**: hotel box
  X −29.75 … −5.89, Y −0.82 … 10.76, Z 0 … 9.15; Palace box X +9.33 … +21.93, Y −0.82 … 22.0, Z 0 … 8.65.

**Massing** (X, Y = map ±0.1 m; heights as marked)

| Part | Local X | Local Y | Storeys / height | Roof |
|------|---------|---------|------------------|------|
| A. 35–37 main | −0.47 … +5.93 (6.40, 21 ft) | 1.98 … 15.89 | 3; eave **8.53** (map 28') | low hip, ridge along Y at X 2.73, Y 5.0 … 12.9, **top 9.45 (guess)**, tin (map "o") |
| B. 35–37 porch | −0.47 … +5.93 | 0 … 1.98 | 2 tiers (map "2") | shed roof, wall side 6.85, eave 6.45, tin |
| C. Frame rear wing | −0.47 … +4.06 (4.53) | 15.89 … 32.10 | 2 (map); top **6.10 (guess)** | low shed/flat, tin (guess) |
| D. North shed | +4.06 … +5.65 | 15.89 … 20.50 | 1 (map); top **3.10 (guess)** | shed, tin |
| E. 39–41 brick | −5.94 … −0.92 (5.02) | 1.90 … 12.43 | 2 + basement (map "2B", photo); top **8.53** (map 28') | flat behind a plain parapet (**guess**), tin |
| F. Brick rear | −5.94 … −0.92 for Y 12.43 … 15.43; −3.11 … −0.92 for Y 15.43 … 18.37 | as left | 1 (map); top **3.60 (guess)** | flat, tin (guess) |

Walls skirt to −0.20 (alley and yards at world y 0). Interiors not modelled (but see the dark basement well).

**Paving**: flat concrete slab at Z 0 (flush with the sidewalk top), X −5.94 … +5.93, Y −0.82 … 0 and in
the brick court X −5.94 … −0.47, Y 0 … 1.90, skirted to −0.20, **with the basement areaway opening** (39–41).

**Elevation details: 35–37 front** (X centre 2.73; heights scaled on the 1906 card and the Stryker plate, ±0.3)
- **Porch floor** raised: deck top **Z 0.45**, X −0.47 … +5.93, Y 0 … 1.98, plain board fascia; **two steps**
  along the whole front: treads at Z 0.15 and 0.30, each 0.30 deep (Y −0.60 … −0.30 and −0.30 … 0) (photo:
  raised ≈ 0.45 m with two risers).
- **Columns, both tiers: 4 round Tuscan columns on the front line at X −0.35, +1.70, +3.76, +5.81**
  (evenly spaced), Ø 0.22 tapering to 0.19, square plinth 0.28 × 0.08, torus base, plain capital with an
  abacus 0.28 square. Ground tier Z 0.45 … 3.20; upper tier Z 3.70 … 6.30 (on the deck, rising through the rail).
- **Beam and fascia between the tiers** Z 3.20 … 3.70, projecting 0.08, plain (no lettering). Upper deck Z 3.70.
- **Upper-deck rail** (c. 1906–10 and 1920s): turned balusters, Z 3.70 … 4.55, Ø 0.06 (6-sided lathe
  profile, belly at mid-height), at 0.12 centres between the columns, flat top rail 0.10 × 0.06 and bottom
  rail; front only, plus the two short return ends (Y 0 … 1.98). South end open where the stair comes up (B2).
- **Bars** (1920s card only): tall close vertical bars Z 4.60 … 5.80, 0.05 wide, 0.12 centres, between the
  columns on the front (read as hung blinds or screens, not certain).
- **Spindle frieze** (c. 1906–10): between the column caps in every front bay, Z 5.90 … 6.30: top and bottom
  rails 0.05, short turned spindles Ø 0.035 at 0.09 centres. Under it a **cut-out drop fringe** (flat board,
  Z 5.75 … 5.90, scalloped/pendant lower edge, 0.15 period) in every bay. Top beam Z 6.30 … 6.45. Porch roof
  from Z 6.85 at the wall to Z 6.45 at Y 0, 0.15 overhang.
- **Awning** (1920s card, north end; rest inferred): extended, from under the deck, Z 3.20 at Y 0 sloping
  straight to Z 2.50 at Y −1.30, scalloped valance to Z 2.25, X −0.47 … +5.93, striped, two thin iron arms.
  **Valance: plain (Decision 3a) or "PRODUCE | JACOB R. HALL | GROCER" (3b).**
- **Ground floor behind the porch** (c. 1906–10, read past the columns at a steep angle; X ±0.5): **south:
  one 2/2 window X 0.15 … 1.15, Z 1.05 … 2.75, with closed louvred shutters**; **single door X 2.30 … 3.20,
  head 2.85**, four-panel, dark, glazed upper half; **one large shop window X 3.95 … 5.60, glass Z 1.05 …
  2.85** on a panelled bulkhead; dark wood frames. (Replaces the earlier guessed double door and two windows.)
- **2nd floor behind the upper tier**: three 2/2 windows at X 0.73, 2.73, 4.73, 0.90 × 1.65, Z 4.25 … 5.90,
  pale frames, **louvred shutters open** (each 0.45 × 1.65, flat against the wall either side) (c. 1905).
- **3rd floor, above the porch roof** (2 seen, third inferred): three windows at X 0.73, 2.73, 4.73,
  **0.75 × 1.05, Z 6.95 … 8.00**, plain projecting head 0.06 thick, **louvred shutters open** (closed in the
  plate; open for 1920 as a guess). Clapboard around; corner boards 0.15.
- **Main eave** (c. 1906–10): plain frieze board Z 8.05 … 8.33; boxed eave Z 8.33 … 8.53, projecting 0.45;
  **5 scroll brackets** 0.18 wide, 0.30 tall, 0.40 deep under the soffit at X −0.30, 1.25, 2.73, 4.21, 5.76.
  Return 0.5 m along each side wall.
- **Chimney** (1920s card, brick, near the north wall): 0.55 × 0.55, X +5.20, Y 7.00 (depth a guess), top
  **Z 10.40** (±0.6).
- **Side walls, wing and shed**: clapboard, **blank** (no source), one plain rear door on C at Y 32.10, X +1.8 (guess).
- **Not modelled**: the US flag, produce crates and bench, the cigar sign leaning on the step, the rolled
  awning of c. 1906–10, pole and wires.

**B2. Porch stair (Decision 6; owner said yes, 2026-11-10: build it)**
- **Visible flight** (photos): straight, X −0.45 … +0.45 (0.90 wide, along the porch's south edge, just behind
  the south column), **rising from the porch front to the wall**: bottom tread at Y 0.10, Z 0.45 → top at
  Y 1.70, Z 2.05 (8 risers of 0.20, treads 0.20, ≈ 45°; steep, as the c. 1905 photo shows); **closed stringers
  boarded solid** on both sides; handrail Ø 0.05 on both sides 0.85 above the nosings; square newel posts
  0.10 at the bottom (Z to 1.45) and top.
- **Landing (guess)**: X −0.45 … +1.35, Y 1.40 … 1.98, Z 2.05, on two posts.
- **Upper flight (guess, hidden in every photo)**: along the wall, X +0.45 … +2.45, Y 1.10 … 1.98, rising
  north from Z 2.05 to the upper deck Z 3.70 (8 risers), through an opening in the deck X +0.45 … +2.45,
  Y 1.10 … 1.98, open rail on its outer side. Keep it plain; it is mostly hidden by the bars and columns.

**Elevation details: 39–41 front** (c. 1905 where marked; rest guess)
- Brick wall X −5.94 … −0.92, flat, **unpainted red-brown** (dark in the c. 1905 photo).
- **Balcony (c. 1905; map dashed line)**: floor Z **1.50**, 0.08 thick, Y 1.46 … 1.90 (0.44 deep), X −5.80 …
  −1.06; rail of **flat sawn balusters** (boards 0.10 wide, 0.02 thick, shaped edge, 0.14 centres) Z 1.58 …
  2.40 with a flat top rail; carried on 4 plain wooden brackets. **Access: none modelled** (not seen).
- **First floor (raised, c. 1905)**: **two tall windows / French doors** opening onto the balcony at X −4.68
  and −2.18, 0.95 × 2.10, **Z 1.58 … 3.68**, dark glass, pale frames, **louvred shutters open** (dark, as on the
  hotel); stone sills/thresholds.
- **Basement shop door (c. 1905)** under the balcony: door X −3.00 … −2.10, sill Z −0.95, head **Z 1.10**,
  glazed upper half, dark wood; plain **blank** board over it, Z 1.15 … 1.40, X −3.20 … −1.90 (the lettering
  was unreadable). **Areaway**: open well in the court X −3.30 … −1.80, Y 0.80 … 1.90, brick-lined; **5 steps
  down towards the door** from Y 0.80 (Z 0) to the sill at Y 1.90 (Z −0.95), risers 0.19, treads 0.22; plain
  iron pipe rail 0.90 high along both sides. (Door-head height read from one photo, ±0.2.)
- **2nd floor (guess, hidden in every photo)**: two 2/2 windows at X −4.68 and −2.18, 0.95 × 1.70,
  Z 5.00 … 6.70, pale frames, stone sills, shutters open as below.
- **Parapet (guess)** to **Z 8.53**, plain, with a simple flat coping. **No cornice, no sign, no awning.**
- North wall (0.44 m gap): brick, blank. South wall: against the hotel. Rear F: plain, one door (guess).

**Materials & colours** (no colour evidence: every photo is monochrome; tones from the photos). 9 materials,
all reused, so asset-scout can be skipped.
1. `clapboard`: warm pale cream ≈ #D8CFB8 (pale in all photos); reuse `house-65-main/clapboard_cream.jpg` (board ≈ 0.14 m).
2. `trim`: columns, rails, spindles, fascia, eave, brackets, frames: **a mid stone-grey, darker than the walls**
   (both photos show the trim darker) ≈ #A39A88 (hue a guess); reuse `polyhaven/trim_paint_cream.jpg` tinted, tile 2.0 m.
3. `brick`: red-brown; reuse `polyhaven/red_brick.jpg`, tile 2.0 m (39–41, areaway, chimney).
4. `roof`: reuse `county-offices/roof_tin_redbrown.jpg`, tile 2.0 m, dulled.
5. `shopfront`: doors, shop window, stair boards: dark brown ≈ #2E2E26; reuse `county-offices/door_varnish_dark.jpg`, tile 0.8 m.
6. `dark`: glass ≈ #1E2226, iron arms and rail; plain colour.
7. `awning`: reuse `bank-building/awning_stripes.jpg` (stripes in the 1920s card; colours a guess). If Decision 3b:
   a generated valance strip (pale band, dark serif capitals, three panels) added to an atlas.
8. `shutter`: dark green ≈ #2F3A2E louvres (dark in both photos; hue a guess); **reuse the County Hotel's
   louvred-shutter atlas cell** (same period, same street).
9. `paving`: reuse `polyhaven/sidewalk_concrete.jpg`, tile as the scene sidewalk.

**Weathering**: a plain, older frame: soot under the eave and porch roof; dirt band on the bottom 0.4 m of
clapboard and on the brick; brick streaked below sills and the balcony; the areaway darker and damp; porch steps
worn pale at the middle; slab darker along the walls. No moss.

**Budget**: **ordinary, cap 10k, target ~7k**: 8 columns ~0.6k; turned balusters ~1.3k; bars ~0.5k; spindle
frieze and fringe ~0.9k; brackets ~0.2k; stair ~0.4k; awning ~0.4k; windows, shutters and doors of both fronts
~1.6k; 39–41 balcony and areaway ~0.5k; shells, wings, roofs, slab, steps ~0.6k. Textures: 8 reused 1K maps
(+ an optional valance strip), one 2K lightmap weighted to the two fronts and the alley side.
Files: `tools/blender/block_35_41.py` + `_bake.py`, `assets/models/source/block-35-41.blend`,
`assets/models/block-35-41.glb` (≤ 5 MB), previews `assets/models/previews/block-35-41-*.png` (frontal; from the
north along the porch, matching the Stryker plate; from the SE matching the 1920s card; into the court).

**Acceptance checks for the reviewer**
1. Origin at world (−11.12, 0.15, −129.89); front −Y, **+X = north**; porch front line at Y 0; **front wall
   of 35–37 at Y 1.98, front wall of 39–41 at Y 1.90**; two separate buildings, 0.44 m gap at X −0.92 … −0.47.
2. 35–37: 6.40 m wide, 3 storeys, eave 8.53 m with **5 scroll brackets**; **two-tier porch with exactly 4
   round Tuscan columns per tier, evenly spaced**, floor raised 0.45 m with two steps.
3. Upper tier: **turned balusters**, tall bars above them, **spindle frieze with a drop fringe** under the porch
   roof; plain fascia between the tiers.
4. Ground floor: shuttered window (south), one door, one large shop window; **open louvred shutters** on the
   2nd- and 3rd-floor windows; 3 small windows on the 3rd floor.
5. **Striped scalloped awning** reaching Y −1.30; valance **as the owner decided** (plain or the three Hall panels).
6. Stair: present only if the owner chose it; if present, its visible flight runs **front-to-back** in the south
   bay with boarded sides and two handrails.
7. 39–41: 5.02 m wide, red-brown brick, top 8.53 m, **balcony 0.44 m deep at Z 1.50 with sawn balusters**, two
   tall shuttered windows onto it, **basement door down an areaway**, blank board, **no sign text, no awning**.
8. One brick chimney near the north wall, top above the eave; frame rear wing 4.53 m wide, 2 storeys; brick rear lower, with its notch.
9. Paving reaches Y −0.82 and fills the court; ≤ 10k tris, ≤ 9 materials, GLB ≤ 5 MB, TEXCOORD_0 + 1, 1K maps, 2K lightmap.

**Integrator notes**: replace the placeholder, keep the id; the position's x moves to −11.12. No extra
paving box. Check no street prop stands at x −9.8 … −11.1 in z −136 … −129 (awning edge x −9.82). The Palace
spec's bake occluder for this block (height 7, front x −10.3) is a rough stand-in (true: 8.53 m, porch front −11.12).

**1920 vs earlier**: c. 1905 (Goodspeed): open shutters, the stair; c. 1906–10 (Stryker, 1906 card): the porch as
specified, open upper tier, rolled awning lettered for Jacob R. Hall; 1920s card: bars in the upper tier, an
extended striped awning with differently laid-out (unreadable) lettering. The 1920 model takes the 1920s card
where it sees, the c. 1906–10 plate elsewhere. Nothing later is known.

**Pure guesses (owner to check)**
1. 39–41's 2nd floor and parapet (hidden in every photo); how its balcony was reached; the cone-shaped objects left out.
2. **All colours**, incl. the awning stripes, the darker trim tone and dark green shutters.
3. The stair's landing and upper flight (if built), and whether it stood in 1920.
4. Roof forms (hips, wing, parapet), wing and rear heights; chimney depth.
5. Side walls blank (no source shows them).
6. The upper-tier bars being blinds or screens; the awning across the full width.
7. Ground-floor opening positions of 35–37 (±0.5 m, read at a steep angle); 3rd-floor shutters shown open.
8. The basement door's depth (one photo).

### Block at 32–38 Main St: frame row "Mill'y", "Bakery" and "Meats" (old nos. 557–554)

**Status:** spec written — awaiting user approval (planner, 2026-11-08; re-checked against the owner's newly saved local photos 2026-11-10: nothing changes; Stryker plate c. 1906–10 checked 2026-11-10, see Sources: model unchanged). Not built.

**What it is**: a **row of three small 2-storey frame shops behind one continuous 1-storey open porch**,
directly north of 40–46. From north to south on the Sept 1921 Sanborn: **millinery ("Mill'y")**,
**"Bakery"**, **"Meats"**. The south part of "Meats" drops to 1 storey at the front, and a long 1-storey
back building runs behind it. Modelled as one GLB, as at 40–46.

**What is documented, inferred, guessed**
- **Documented (map, Sept 1921)**: footprints; all frame; storey figures "2" (each front block) and "1"
  (porch, Meats south strip and rear, two back additions); roof marks "o" (slate or metal) and "x" (shingle)
  on the Mill'y rear porch; the trades; numbers 32, 34, 36, 38 and old 557, 556, 555, 554; the open (dashed)
  porch across all three. **No height figure is written on any part.**
- **Inferred**: that the three read as one row (shared porch, straight front); 2-storey block heights by
  analogy with 44–46 next door (2-storey frame, marked 20'); which number goes with which shop: 32 =
  Mill'y and 38 = Meats fit, **34 and 36 sit on the partition lines and cannot be assigned** (four
  evenly spaced numbers over three shops). No number goes on the model.
- **Pure guess**: **the entire front**: no photo shows it. Openings, porch post count and form, porch
  floor, roof shape, every colour, all side walls. Kept deliberately plain.
- **Tenants c. 1920**: only the map's trades. **No names found.** A "Nathaniel G. Smith bakery & harness
  shop" stood directly north of the Rea lot in 1873 and 1889 (Goodspeed, below); the 40–46 lots are in
  between, so it cannot be tied to this Bakery: not used. "Alex Zanetti store at 30 Main" (HCHS photo list,
  undated) is the next lot north: not this block.

**Planner decisions** (owner to confirm)
1. **Map-true placement, as approved for 40–46**: porch front at x 8.54, on the sidewalk, leaving a
   2.1 m walk, the same as in front of 44–46. Alternative in Pure guesses no. 1.
2. **Straight front.** The map's front line slants 0.39 m over the 13.5 m (px 3988.5 → 3996); the model
   uses the mean, so each end is within ±0.2 m. Rotation stays the standard `0 -90 0`.
3. **No signs, lettering, awnings, shutters, brackets or chimneys**: no source shows any. The shops will
   read as anonymous plain fronts; that is intended (owner's preference, 2026-11-08).
4. **Part G, a patch for the 40–42 wall** (see Massing): the map makes the south end of this row only
   1 storey, so it **cannot** hide 40–42's north wall up to 6.10 m the way the placeholder did. Those
   faces were deleted from `block-40-46.glb` (`block_40_46_bake.py` line 365), so without the patch you
   would see through 40–42. This is a repair, and matches the map (that wall really stood exposed).
5. **Ordinary building: cap 10k, target ~3.5k.** 7 materials, all reused; asset-scout can be skipped.

**Sources**
- Map: 1921 Sanborn **sheet 2** [M1], pixel box **x 3945–4445, y 4258–4525**, all yellow (frame). Line
  centres from a brightness profile:
  - **Street line** (thick): x 3944.5 (y 4310) → 3951.5 (y 4510). **Porch front** (dashed): x 3957 (y 4270) →
    3966.5 (y 4510), mean **3961**. **Front wall**: x 3989.5 (y 4310), 3991.5 (y 4375), 3994.5 (y 4470), 3996
    (y 4510), mean **3992.3**. Porch north end y 4262; south end dashed, y 4516. Porch labels "1", "o".
  - **North wall y 4261.5; Mill'y | Bakery y 4341; Bakery | Meats y 4427.5; south line y 4521.5** (shared
    with no. 40; the 40–46 spec reads the same line as y 4520).
  - **Mill'y** (79.5 px = 4.14 m): "2", "o", "Mill'y". Partition with a gap at x 4281 (y 4290–4311). Rear part
    to x 4385.5, "2", "o". Rear porch to x 4410.5 (dashed), "1", "x" (shingle).
  - **Bakery** (86.5 px = 4.51 m): "2", "o", "Bakery". Rear wall x 4282.
  - **Meats** (94 px = 4.90 m): **2-storey block x 3994–4112.5, y 4427.5–4489** ("2", "o"; its rear and south
    lines have gaps at y 4451–4461 and x 4037–4055, read as interior doorways). **Strip south of it y 4489–4521.5
    and everything behind x 4112.5 back to x 4441**: "1", "o", "Meats". Its north wall has a gap at x 4310–4335.
  - **Back addition behind the Bakery**: x 4282–4357, y 4391–4427.5, "1" and a solid dot (meaning not confirmed).
  - **Numbers** (street strip, read rotated): 32 / 557 at about y 4274; 34 / 556 at 4346; 36 / 555 at 4417;
    38 / 554 at 4487.
  - North neighbour: 24–30 ends at y 4195; **white gap y 4195–4261 (3.4 m)**. All on sheet 2.
  - **Placeholder z is right (north end −137.6, map −137.46); its x 10.3 is close to the front wall
    (10.17) but it has no porch, which reaches 1.63 m further out.** It also has only one height.
- **Photos: none shows these fronts.** Checked:
  - All 32 `assets/photos/reference/*.jpg` (contact sheet) and `habs/`: nothing this far north on the east side.
  - West Jersey History, viewed from the site, not saved in the project: `flmngntnmainstcountyhtl08.jpg` (1908,
    looking north past the County Hotel): the east side here is **behind a large tree**; enlarged, only a
    light vertical at the right edge, unreadable. `flmngtnmainstrtcountyhtlvu06.jpg` (1906, looking south; **now
    saved locally by the owner**, re-checked 2026-11-10): a camera fit from the 35–37 porch columns and the County
    Hotel veranda (west side) puts the camera at about z −152 and the card's left edge at the east-side line at
    roughly z −120 … −140 (the focal length is poorly fixed, so ±10 m). What stands there in the card is **a
    3-storey building with stacked front bay windows over striped canvas awnings**, then a tree. That matches
    nothing in this row as mapped in 1921 (2 storeys, one continuous 1-storey porch); it is either 40–42 (if the
    fit runs long) or a 1906 state that was gone by 1921. **Not used for this row**; the earlier note "left edge
    starts at about the Rea Building" is withdrawn as unsure.
  - **HCHS Stryker plate c. 1906–10** (`hchs-stryker-main-st-south-from-hall-grocery.jpg`, local only, looking south from
    35–37), camera fit 2026-11-10 (County Hotel posts, grocery columns, east curb; camera ≈ (2.5, −160) ± 3 m): the left edge
    meets the east building line at about **z −135 … −143 (±5 m)**, so 32–38 is **probably in frame** (full-res x ≈ 0–550, the
    Rea's stoops at x ≈ 700–900). What stands there: **a continuous 1-storey porch with posts and striped awnings** (fits the
    map's porch), behind it a frame front with **stacked 2-level front bays under a pyramid roof with a finial** and a balustraded
    deck on the porch roof, and at the very left a **taller frame front with a mansard tower**. These are the same bay-windowed
    fronts as in the 1906 card and do **not** match the 1921 map's plain 2-storey row (no height figure, though); the fit cannot
    rule out that they are 40–42 instead. **Model unchanged** (owner may ask for the porch awnings or bays as a c. 1906–10 guess).
  - Owner's other new local photos (2026-11-10): `palace-theatre-potter-building-card.jpg` (west side only);
    `flmngtnmainstnorth13.jpg` (1913, residential north end by the Soldiers' Monument); `flmingtnmainstrtview.jpg`
    ("Commercial Buildings", inked "Sept. 16, 1905": south end). None shows this row.
  - The owner got 404 for `flmngtnmainstrtnorthfromhtl08.jpg`, `flmngtnmainstreetsouthfrmonument08.jpg` and
    `flmngtnmainststores14.jpg`; the names listed above with "flmngntn…" (extra n) are probably the real ones.
    `flmngntnmainstrtnorthfromhtl08.jpg` (Union Hotel porch, row too far), `flmngtncountyhtl06.jpg`,
    `flmngtncountyhotel08.jpg` (west side only), `flmngtnmainstnorth13.jpg`, `flmngtnmainstrtviewof06.jpg`,
    `flmngntnmainststores14.jpg`, `flmingtnmainstrtview.jpg`, `flmngtnmainstrtvu.jpg`, `flmngtnminestrtview08.jpg`,
    `flmngntnmainstreetsouthfrmonument08.jpg`, `flemngtnmainstatbranchst10.jpg`, `flmngtnmainstmaybe.jpg`:
    other parts of the street.
- `HISTORY-SOURCES.md`: nothing on these numbers.
- Web: Goodspeed, "The Clock Tower Building", https://goodspeedhistories.com/the-clock-tower-building/ (the Smith
  bakery, 1873 and 1889); "Roof Arches, part 1", https://goodspeedhistories.com/roof-arches-part-one/ (nothing on
  32–38); HCHS Collection 238 list,
  https://hunterdonhistory.org/wp-content/uploads/2022/06/Collection-238-Container-List.pdf (Zanetti, no. 30);
  West Jersey History index, https://westjerseyhistory.org/images/hunterdon/flemington/ (no caption names these
  shops). No NRHP or HABS text found for these numbers.

**Placement** (east side, front faces west onto Main St)
- Entity = centre of the front line (porch front) at sidewalk level: **(8.54, 0.15, −130.755)**,
  `rotation="0 -90 0"`; keep id `bldg-32-38-main` (replaces the placeholder at (10.3, 0, −130.825)).
- **Blender frame** (as 40–46): front −Y, origin as above, **+X = south**, Y = depth, Z 0 = sidewalk top. World
  x = 8.54 + Y, world z = −130.755 + X. Map → local: X = (py − 4390.3) × 0.0521, Y = (px − 3961) × 0.0521.
- Scene lines: north wall **z −137.46**; Mill'y | Bakery z −133.32; Bakery | Meats z −128.82; Meats block south
  z −125.61; south end **z −124.05** (map −123.92; trimmed to stay 0.05 clear of 40–42's built north wall at
  z −124.00). Porch front x 8.54; front wall **x 10.17**.
- **Neighbours**: south, 40–42 touches (its porchless no. 40 front is 0.41 m behind this front wall, x 10.58); north,
  **3.4 m open gap** to the 24–30 placeholder (z −140.9).
- Props: pole-E6 (6.9, −124) is clear; no tree here. Walk left in front of the porch: x 6.40 … 8.54.
- **Sun** "to sun" **(0.40, −0.90, 0.36)** (front lit). **Bake occluders (not exported)**: 40–46 box X +6.76 … +21.66,
  Y 2.04 … 18.0, Z 0 … 9.15; 24–30 box X −26.55 … −10.15, Y 1.76 … 13.76, Z 0 … 7.5.

**Massing** (X, Y = map ±0.1 m; every height is a guess, the map writes none)

| Part | Local X | Local Y | Storeys / height | Roof |
|------|---------|---------|------------------|------|
| A. Mill'y (main + rear part) | −6.705 … −2.57 (4.14) | 1.63 … 22.12 | 2 (map); front top **6.10 (guess)** | low shed falling to rear, 6.10 → 5.50, tin (map "o") |
| B. Bakery | −2.57 … +1.94 (4.51) | 1.63 … 16.70 | 2 (map); front top 6.10 (guess) | shed, 6.10 → 5.60, tin |
| C. Meats 2-storey block | +1.94 … +5.14 (3.20) | 1.63 … 7.89 | 2 (map); front top 6.10 (guess) | shed, 6.10 → 5.90, tin |
| D. Meats 1-storey (south strip + rear, an L) | +5.14 … +6.705 for Y 1.63 … 7.89; +1.94 … +6.705 for Y 7.89 … 25.06 | as left | 1 (map); top **3.80 (guess)** | nearly flat, 3.80 → 3.60, tin (map "o") |
| E. Porch | −6.705 … +6.55 | 0 … 1.63 | 1, open (map) | shed, tin (map "o") |
| F1. Mill'y rear porch | −6.705 … −2.57 | 22.12 … 23.42 | 1, open (map); top 2.90 → 2.60 (guess) | shed, wood shingle (map "x") |
| F2. Bakery back addition | +0.04 … +1.94 | 16.70 … 20.63 | 1 (map); top 3.00 (guess) | shed, tin (guess) |
| G. **Patch on 40–42's north wall** | plane X +6.705, facing north | **2.04 … 11.26** | Z **3.60 … 6.12** (repair) | none |

Part G is a thin plain panel of **buff clapboard, the material of 40–42** (`clap_a`), lying over the opening; it
starts inside D's roof and overlaps the existing 6.10 line by 0.02. Blank (40–42's built windows are all above 6.10).

Walls skirt to −0.20 (yards at world y 0). Interiors not modelled. D's south face for Y 1.63 … 11.26 is against no. 40
(only Y 1.63 … 2.04 shows, a sliver); beyond Y 11.26 it faces 40–42's yard and is plain clapboard.

**Elevation details: all guess, plain by choice** (Z values follow the built 44–46 next door)
- **Porch**: deck Z 0 … 0.15 over the sidewalk (no step), X −6.705 … +6.55. **6 plain square posts 0.14 wide**, front
  line Y 0.10, evenly spaced at X **−6.60, −3.99, −1.38, +1.23, +3.84, +6.45**, Z 0.15 … 3.00. **Post count and form
  are guesses.** Plain fascia Z 3.00 … 3.30, no lettering. Shed roof Z 3.45 at the wall to 3.20 at Y 0, overhang 0.10.
  **No rail** (the map's dashes show only that it is open).
- **Shop fronts** in the wall plane Y 1.63, dark wood frames, bulkhead Z 0.15 … 0.75, glass Z 0.75 … 2.75; door glazed
  in its upper half, head Z 2.60, 0.90 wide:
  - Mill'y: window X −6.30 … −4.00; door X −3.70 … −2.80.
  - Bakery: window X −2.20 … +0.45; door X +0.75 … +1.65.
  - Meats: window X +2.30 … +4.00; door X +4.20 … +5.10. South strip X +5.14 … +6.705: **blank clapboard**.
- **Upper floor**: six 1/1 windows, 0.80 × 1.45, Z 3.90 … 5.35, plain pale frames, at X **−5.67, −3.61** (Mill'y), **−1.44,
  +0.81** (Bakery), **+2.79, +4.29** (Meats). No shutters.
- **Eave**: plain boxed eave Z 5.90 … 6.10, projecting 0.30, X −6.705 … +5.14, across the front only. **No brackets, no cornice
  mouldings.** Plain vertical corner boards 0.15 at both ends and thin plain boards at the two partition lines.
- **Side and rear walls**: clapboard, **blank** (no source), incl. **A's north wall, 20.5 m long, in plain view across the 3.4 m
  gap** (real one surely had windows; see Pure guesses). C's south wall above D and rear wall above D, blank. One plain door on
  D's rear at Y 25.06, X +4.3 (guess).
- **Not modelled**: chimneys, gutters, the interior doorways, wires.

**Materials & colours** (no colour evidence: all guesses)
1. `clap_row`: warm pale cream ≈ #D8CFB8; reuse `house-65-main/clapboard_cream.jpg` (board ≈ 0.11–0.14 m, as its other uses).
2. `clap_a` (part G only): buff; reuse `courthouse/clapboard_buff.jpg`, tiled as on 40–42 so it matches.
3. `trim`: posts, fascia, eave, frames, boards, cream ≈ #DDD5C2; reuse `polyhaven/trim_paint_cream.jpg`, tile 2.0 m.
4. `roof`: reuse `county-offices/roof_tin_redbrown.jpg`, tile 2.0 m, dulled (F1 darker, as weathered shingle).
5. `shopfront`: dark brown ≈ #2E2E26; reuse `county-offices/door_varnish_dark.jpg`, tile 0.8 m.
6. `dark`: glass ≈ #1E2226; plain colour.
7. `deck`: reuse `lovells-restaurant/stone_bluestone.jpg`, tile 2.0 m (as 42's porch).

**Weathering**: plain older frame: soot under the eave and the porch roof; dirt band on the bottom 0.4 m; chalky paint on the
north wall; deck darker at the wall and at the shop doors. No moss.

**Budget**: **ordinary, cap 10k, target ~3.5k**: 6 posts + fascia + porch roof ~0.4k; 3 shop fronts ~0.9k; 6 windows ~0.5k; eave and
boards ~0.2k; shells and roofs ~0.7k; patch ~0.02k. Textures: 6 reused 1K maps, one 2K lightmap weighted to the front and the north wall.
Files: `tools/blender/block_32_38.py` + `_bake.py`, `assets/models/source/block-32-38.blend`, `assets/models/block-32-38.glb` (≤ 5 MB),
previews `assets/models/previews/block-32-38-*.png` (frontal; from the NW showing the north wall and the patch; from the SW along the porch).

**Acceptance checks for the reviewer**
1. Origin at world (8.54, 0.15, −130.755); front −Y, **+X = south**; porch front at Y 0; front wall at Y 1.63.
2. 13.41 m along the street (X ±6.705); partition lines at X −2.57 and +1.94; one continuous open porch to X +6.55.
3. **Three 2-storey fronts, top 6.10 m**, and at the south end a **1-storey strip** X +5.14 … +6.705 (top 3.80), so the roofline steps down
   beside 40–42.
4. **Exactly 6 plain square posts, evenly spaced**; 3 doors and 3 shop windows; 6 upper windows.
5. **No sign, no lettering, no awning, no shutters, no brackets, no chimney** anywhere.
6. Meats 1-storey back building reaches Y 25.06; Mill'y reaches Y 22.12 with its open rear porch to Y 23.42.
7. **See-through check**: in the scene, from the north and north-west, there is **no hole in 40–42's north wall**: buff panel from the 1-storey
   roof to 6.12 m, Y 2.04 … 11.26, meeting the built wall at the 6.10 line.
8. Nothing crosses z −124.05 or x < 8.54 except eave and roof overhang (≤ 0.10 at the porch).
9. ≤ 10k tris, ≤ 7 materials, GLB ≤ 5 MB, TEXCOORD_0 + 1, 1K maps, 2K lightmap.

**Integrator notes**: replace the placeholder, keep the id, position x moves to 8.54 and y to 0.15. No paving box. Confirm the view of 40–42's north wall once the
placeholder is gone. If the 24–30 placeholder's south end (z −140.9) looks wrong beside this row, leave it for that building's spec.

**1920 vs earlier**: no photo at any date shows this row; everything is the Sept 1921 map plus a plain stand-in. (The 1906
County Hotel card may show this stretch of the east side, but not in its 1921 form; see Sources.)

**Pure guesses (owner to check)**
1. Placement: (a, chosen) porch on the map's line at x 8.54, walk 2.1 m; or (b) drop the porch front back to x 9.3 for a wider walk, which is not what the map shows.
2. **All openings on the front**, the post count, deck and roof shape: only "shop front below, windows above, open porch" is safe.
3. **All heights** (no figure on the map). If the owner wants them lower, 5.5 m is equally defensible.
4. **All colours.**
5. **Blank side walls**, above all the long north wall in view from the street. Windows could be added only as an admitted guess.
6. No chimney even though a bakery surely had one; the map marks none. It can be added as an admitted guess.
7. Reading of the Meats rear as "1" (only one figure is on that part) and the solid-dot mark.

### Dry goods and clothing store (27 Main St, old nos. 519 A/B)

**Status:** spec written — awaiting user approval (planner, 2026-11-08; re-checked against the owner's newly saved local photos 2026-11-10: confirmed, nothing new). Not built.

**What it is**: **one 2-storey brick store**, 12.35 m (40.5 ft) wide and 24.2 m deep, labelled "D.G. & Clo."
(dry goods and clothing) on the Sept 1921 Sanborn, directly north of the Palace Theatre. The map shows one
building, no partition, with one new number (27) and two old numbers (519 A and B). It has a long awning and
four tall upper windows. Behind it are a 2-storey frame gallery and a 1-storey frame wing.

**What is documented, inferred, guessed**
- **Documented (map, Sept 1921)**: footprint, brick, "2" storeys, "25'", "D.G. & Clo.", number 27, old 519
  A/B, 2-storey frame strip with a dashed outer side, 1-storey frame wing, light court on the south side.
- **Documented (photo)**: the front on the "Palace Theatre & Potter Building" card (from the SE): deep plain
  cornice; blank brick frieze with **no visible sign**; pale bands at window heads and sills across the
  front; **four evenly spaced tall windows** with pale side strips; dark shop cornice; **one long plain
  (unstriped) awning** with a diagonal arm at its south end; **one globe lamp** at the south corner; a pale
  south pier; a low chimney or block at the north end of the roof.
- **Inferred**: that this card building is no. 27 (strong: it stands right beside the theatre, and a
  perspective fit from the Palace front predicts its north end at card x 487 against about 491–494 seen);
  1/1 sashes (only a meeting rail shows); the pale bands being stone or painted; a matching north pier; a
  second awning arm; the roof being low-pitched (a slight rise shows above the cornice).
- **Pure guess**: **everything under the awning** (too dark to read; only a bright patch at the south end
  and a dark vertical band north of centre), all colours, side walls, rear heights, roof shape.
- **Tenant c. 1920**: only the map's trade. **No name found.** Nothing is lettered on this model.
- **Potter Building: not confirmed.** It is likely, but it rests on the caption alone: the card names two
  things and shows the theatre with no. 27 beside it. Searches (Goodspeed Histories, HCHS container lists and
  trail brochure, Cinema Treasures, general web) found **no mention of any Potter building, store or merchant
  in Flemington**. The NRHP nomination PDF is a scan with no readable text, so it could not be searched. No
  "Potter" name goes on this model.

**Planner decisions** (owner to confirm)
1. **Ordinary building: cap 10k, target ~4k.** One GLB, parts A–D below.
2. **Front at x −10.30**, flush with the Palace and the property line (map reads −10.50, within reading
   error; the card shows the two fronts in line).
3. **No lettering, no sign, no sign board** anywhere, including the frieze and awning.
4. **Ground floor deliberately plain** behind the awning: two windows and one door (see Pure guess 1).
5. **Side walls blank** (no source shows them), although the map has unlabelled wall ticks. See Pure guess 3.

**Sources**
- Map: 1921 Sanborn **sheet 2** [M1], pixel box **x 2797–3600, y 3735–3990**. Line centres from a brightness
  profile: **front wall x 3595.5**; **north wall y 3739.5** (drifts to 3744.5 at x 3200, read as paper skew,
  built straight); **south wall of the front part y 3976.5**, to x 3514.5; **south wall of the rest y 3936**;
  brick rear x 3131.7; frame strip outer (dashed) x 3104, y 3741–3935, marked "2" and "o"; 1-storey frame
  wing x 2797–3104, north side y 3843 (3830 at far end), south side y 3935 with a small step at x ≈ 2922,
  marked "1" and a solid dot. Labels (brick): "2", **"25'"**, "D.G. & Clo.", "o" at x 3572, y 3957. Wall figures
  "12 12" (read as inches of wall). Street: "27" and "A 519 B" (rotated). No "29" printed. Unlabelled crossed
  ticks on the north wall (x ≈ 3490, 3280) and the south wall (x ≈ 3440, 3285). Dashed line x ≈ 3606
  (0.5 m before the wall), y 3738–3975, unlabelled; the awning is the likely reason but that is not stated.
  Palace north wall y 3985.5, so the map's gap between the fronts is **0.47 m** (a dark slit also shows on the
  card). North of it the map shows open ground, a thin line y 3693.5, then no. 17 (brick, "D", old 520) from y 3678.
- **Primary photo (the only view of the front found)**: "Palace Theatre & Potter Building, Flemington, N.J."
  card, looking NW, right-hand part (card x 380–510); dated "1920s" only by a Cinema Treasures commenter. **Now
  saved by the owner, local only (never commit): `assets/photos/reference/palace-theatre-potter-building-card.jpg`**,
  the same image as https://photos.cinematreasures.org/production/photos/323405/1604912133/large.jpg . Re-checked
  on the local copy 2026-11-10 (enlarged, brightened): every reading below holds; under the awning still only a
  bright display window at the south end and dark beyond; frieze blank; awning plain. The next building north
  (two tiers of dark openings with posts) appears right beyond the north end; the map's 3.2 m gap cannot be read
  at this angle (no. 17 is not in the scene, so the model is unchanged). Only 640 px wide with a
  coarse halftone: heights and positions below marked "card" are ±0.3 m. Vertical scale taken from map 25' =
  card y 122 (cornice top) to y 303 (ground) at the south corner. Positions along the front from a
  projective fit: windows measure 1.61, 4.86, 7.88, 11.02 m from the south corner, spacings 3.0–3.25, so
  equal bays centred on the front are used.
- **Local photos**: all 32 earlier `assets/photos/reference/*.jpg` (contact sheet) and HABS show the south end
  only; none shows no. 27. `HISTORY-SOURCES.md` has nothing on this number.
- **Viewed 2026-11-10 (owner's new local saves), none shows no. 27**: `flmngtnmainstrtcountyhtlvu06.jpg` (1906,
  looking south; a camera fit puts the camera at about z −152, i.e. in front of no. 27 / the Palace, so this
  building is behind it); `flmngtnmainstnorth13.jpg` (1913, "Main St – Soldiers' Monument – Pres. Church":
  the residential north end, houses with porches); `flmingtnmainstrtview.jpg` ("Commercial Buildings", inked
  "Sept. 16, 1905": the south end, a brick building with stoops and a 3-storey brick corner block).
- **Still not viewed** (404 for the owner): "Main Street South From the Monument" 1908
  (`flmngtnmainstreetsouthfrmonument08.jpg`), "North From the Hotel" 1908 (`flmngtnmainstrtnorthfromhtl08.jpg`),
  "Main Street Stores" 1914 (`flmngtnmainststores14.jpg`). The 32–38 spec lists these three spelt
  "flmngntn…" (extra n), probably the real file names. The 1908 view south from the monument is the one most
  likely to show this front. The site refuses automated downloads; open by hand at
  https://westjerseyhistory.org/images/hunterdon/flemington/ .
- Web (nothing on no. 27): https://cinematreasures.org/theaters/15430 ; https://goodspeedhistories.com/category/countyhouseseries/ ;
  https://hunterdonhistory.org/wp-content/uploads/2018/08/Flemington-TRAIL-online8-1.pdf ;
  https://hunterdonhistory.org/wp-content/uploads/2022/06/Collection-238-Container-List.pdf ;
  https://npgallery.nps.gov/AssetDetail/NRIS/80002493 (scan, unread). A search snippet placed an 1823
  congregation's former church at "21–27 Main"; no page confirmed it, not used.

**Placement** (west side, front faces east)
- Entity = centre of the front at sidewalk level: **(−10.30, 0.15, −158.49)**, `rotation="0 90 0"`, keep id
  `bldg-27-main`.
- **Placeholder is off**: its centre z −159.5 is 1.0 m too far north; its north end (z −164.7) is right, its
  south end (−154.3) is 2.0 m short; it is also too tall (9 against 7.62) and too shallow (20 against 24.2).
- **Blender frame**: front −Y, origin as above, **+X = north**, Y = depth (world x = −10.30 − Y), world z =
  −158.49 − X. Map → local: X = (3858 − py) × 0.0521, Y = (3595.5 − px) × 0.0521.
- Scene lines: north wall **z −164.66**, south wall of the front part **z −152.31**, rear brick wall world x −34.46.
- **The Palace gap**: this model's south wall at z −152.31 closes the 2.4 m gap, leaving the map's **0.49 m
  slit** to the Palace's north wall (z −151.82). The Palace integrator note (extend the placeholder south
  to z −152.2) only applies if the Palace goes in first; it lapses once this model replaces the placeholder.
- **Neighbours**: south, the Palace (0.49 m slit, then a 2.6 m light court X −6.67 … −4.06 behind Y 4.22);
  north, 3.2 m of open ground to no. 17, **which is not in the scene, so the north wall is in full view**.
- **Sun** "to sun" **(−0.40, 0.90, 0.36)**. **Bake occluders (not exported)**: Palace front block X −19.27
  … −6.67, Y 0 … 22.82, Z 0 … 8.65; auditorium and stage X −19.27 … −5.58, Y 22.82 … 62.78, Z 0 … 7.9.

**Massing** (X, Y = map ±0.1 m; heights as marked)

| Part | Local X (S → N) | Local Y | Storeys / height | Roof |
|------|-----------------|---------|------------------|------|
| A. Front part | −6.175 … +6.175 (12.35) | 0 … 4.22 | 2; cornice top **7.62** (map 25') | as B |
| B. Main block | −4.06 … +6.175 (10.24) | 4.22 … 24.16 | 2; rear eave **7.00 (guess)** | low gable, ridge parallel to Main at Y 7.0, **top 8.10 (card shows a slight rise; height a guess)**, front eave 7.55 behind the cornice, tin (map "o", key unconfirmed) |
| C. Rear frame gallery | −4.06 … +6.175 | 24.16 … 25.61 | 2 (map); top **6.40 (guess)** | shed, tin (guess); map's dashed side suggests open, built as a plain closed lean-to |
| D. Frame wing | −4.10 … +1.10 (simplified) | 25.61 … 41.60 | 1 (map); top **3.60 (guess)** | low shed, tin (guess) |

Walls skirt to −0.20 (alley and yards at world y 0). Interiors not modelled. "Coop." and "Auto" sheds not modelled.

**Elevation details: front** (from the card unless marked; X from south to north; sidewalk Z 0)
- **Cornice**: plain wooden box, Z 7.28 … 7.62, projecting **0.55 (guess)**, full width, dark soffit, pale upper
  edge. **No brackets** (none readable).
- **Frieze**: plain brick wall Z 6.02 … 7.28. **Blank: no sign, no letters.**
- **Head band** Z 5.82 … 6.02 and **sill band** Z 3.60 … 3.90: pale, continuous between the corner strips,
  projecting 0.03.
- **Corner strips**: pale, 0.20 wide, projecting 0.03, at both ends, Z 3.60 … 7.28.
- **Upper floor: 4 windows at X −4.71, −1.57, +1.57, +4.71** (equal 3.14 m bays), opening **0.95 × 1.87**, Z 3.95
  … 5.82, recessed 0.20, 1/1 sash (inferred), dark frames and glass. **Pale side strips** 0.18 wide each side,
  projecting 0.03, Z 3.90 … 5.82. No shutters, no hoods.
- **Wall below sill band**: brick, Z 3.35 … 3.60.
- **Shop cornice**: dark wooden beam, Z 2.95 … 3.35, projecting 0.12, full width.
- **South pier**: pale, X −6.175 … −5.55, Z 0 … 2.95, flush. **North pier** X +5.60 … +6.175 to match (inferred).
- **Globe lamp**: one, opal white, Ø 0.28, at X −5.85, Y −0.35, centre Z 3.35, short iron bracket into the
  wall (card shows it at the south corner; none is visible elsewhere above the awning).
- **Awning** (card): plain, **no stripes, no scallops, no letters**. X −5.55 … +6.175; top edge Z 2.95 at Y 0,
  straight down to **Z 2.30 at Y −1.90 (projection and drop are guesses)**. Thin iron side arm at the south end
  (card) and north end (inferred).
- **Shop front (GUESS: hidden under the awning; plain by choice)**, in the wall plane, recess 0.10: glass south
  X −5.55 … +0.25 (one mullion at X −2.65) and north X +1.95 … +5.60, glass Z 0.55 … 2.75 on a dark wooden
  bulkhead Z 0 … 0.55, dark panel Z 2.75 … 2.95. **One door opening X +0.25 … +1.95**, recessed 0.90, dark, pair
  of plain glazed doors, head 2.75. Door position follows the dark band north of centre on the card (weak).
- **South wall, part A (in the slit) and part B (light court)**, **north wall**, **rear of B**: plain brick, **blank**.
  C and D: clapboard, blank; one plain rear door on D at Y 41.60, X −1.5 (guess).
- **Chimney** (card: low flat-topped block at the north end of the roof; form uncertain): brick, 1.00 × 0.60, X
  +5.40, Y 6.0 (depth a guess), top **Z 9.00 (±0.6)**.
- **Not modelled**: the map's dashed line before the wall, poles and wires (street props).

**Materials & colours** (no colour evidence: all guesses; the card is black and white). 7 materials, all reused,
so asset-scout can be skipped.
1. `brick`: red-brown ≈ #7A4436, like the Palace; reuse `polyhaven/red_brick.jpg`, tile 2.0 m.
2. `bands`: head and sill bands, corner and side strips, piers, pale buff; reuse `county-offices/stone_buff.jpg`, tile 1.5 m.
3. `shopfront`: cornice, beam, bulkhead, doors, sashes, dark brown-green ≈ #2E2E26; reuse `county-offices/door_varnish_dark.jpg`, tile 0.8 m.
4. `roof`: reuse `county-offices/roof_tin_redbrown.jpg`, tile 2.0 m, dulled.
5. `clapboard`: parts C and D, reuse `house-65-main/clapboard_cream.jpg` (board ≈ 0.14 m), darkened about 15%.
6. `awning`: **plain faded canvas ≈ #8C8573**, plain colour, no stripes.
7. `dark`: glass ≈ #1E2226, iron arms and bracket; globe: plain opal white ≈ #EDE8DA, unlit (may share this material via vertex colour).

**Weathering**: soot under the cornice and along the shop cornice; streaks below the head and sill bands; dirt on
the bottom 0.4 m of the piers and side walls; north wall a little rain-streaked; awning slightly darker along its
outer edge. No moss.

**Budget**: **ordinary, cap 10k, target ~4k**: shell, roof, cornice ~0.5k; 4 windows with strips ~0.8k; bands and piers
~0.3k; shop front ~1.2k; awning and arms ~0.3k; globe and bracket ~0.4k; chimney, C, D ~0.3k. Textures: 5 reused 1K
maps, one 2K lightmap weighted to the front and north wall. Files: `tools/blender/bldg_27_main.py` + `_bake.py`,
`assets/models/source/bldg-27-main.blend`, `assets/models/bldg-27-main.glb` (≤ 5 MB), previews
`assets/models/previews/bldg-27-main-*.png` (frontal; from the SE matching the card; north wall).

**Acceptance checks for the reviewer**
1. Origin at world (−10.30, 0.15, −158.49); front −Y, **+X = north**; front 12.35 m wide, brick depth 24.16 m.
2. South side: front part full width to Y 4.22, then the wall steps in 2.11 m (the light court).
3. 2 storeys, **cornice top at 7.62 m**, deep plain cornice, **no brackets**; slight roof rise behind it.
4. Exactly **4 evenly spaced tall windows** upstairs with pale side strips; no shutters or hoods.
5. **Two continuous pale bands**, at window heads and sills, between pale corner strips.
6. **Frieze blank; no lettering or sign anywhere on the model**, awning included.
7. **One long plain awning, unstriped, no scallops**, from just north of the south pier to the north corner, reaching Y −1.90.
8. **Exactly one globe lamp**, at the south corner; dark shop cornice across the full front.
9. Ground floor: two plain windows and one recessed door, nothing more; side walls blank.
10. Frame gallery and 1-storey wing behind, lower than the brick; ≤ 10k tris, ≤ 7 materials, GLB ≤ 5 MB,
    TEXCOORD_0 + 1, 1K maps, 2K lightmap. A preview from the SE matches the card's window rhythm, bands and awning.

**Integrator notes**: replace the placeholder, keep the id; position moves to z −158.49. Nothing extends south past z
−152.31, so check the 0.49 m slit reads dark rather than showing sky-lit ground. Check no street prop stands at x −8.4
… −10.3 in z −164.7 … −152.3 (awning outer edge x −8.40). The Palace bake occluder for no. 27 (X +6.4 … +19.2 in its
frame, height 7.6) is close enough; it is the Palace builder's to update if wanted (true: its X +6.79 … +19.14).

**1920 vs later**: nothing later is known. The card (called 1920s) is the closest source to 1920 and still the only one
showing this front (re-checked 2026-11-10 with the owner's new photos).

**Pure guesses (owner to check)**
1. **The whole ground floor behind the awning**: too dark on the card; kept to two windows and one door.
2. **All colours**, incl. the awning and the pale bands (stone or paint unknown).
3. **Blank north and south walls.** The north wall, 24 m long, is in full view because no. 17 is not modelled. The map's
   two ticks per wall suggest openings, but their form is unknown; windows could be added only as an admitted guess.
4. Roof form and heights behind the cornice, the rear parts' heights, the depth of the cornice and awning.
5. The chimney's form and depth (may be another roof feature).
6. "Potter Building" = no. 27 (caption only); no merchant's name known.
7. The meaning of "A 519 B": two old numbers on one store, so possibly once two units; only one tenant on the 1921 map.

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
       2026-11-04 draw-call pass ("texture-sheet pass", done in the browser, GLBs unchanged):
       `baked-lighting` now merges each baked building into **one draw call** (all its 1024²
       colour maps go into one sRGB texture array, one layer each, still tiling; per-vertex
       layer + colour tint; same lightmap; plain colours skip the texture). Anything unusual
       (alpha, non-1024 map, no uv1, skinned, multi-material) keeps the old path;
       `merge: false` turns it off. Street trees: `instanced-trees` loads the tree GLB once
       and draws all 12 with instancing (4 calls instead of 48). Look is pixel-identical
       (differences only on a few edge pixels and Mr. Pickell's animation frame).
       Draw calls / triangles before → after: start (0, 0.15, 18) 161 / 108.4k → 69 / 108.4k;
       (0, −30) north 94 / 59.4k → 56 / 66.3k; (0, −60) south 156 / 92.4k → 74 / 92.4k;
       west sidewalk (−8.5, −52) east 56 / 53.2k → 20 / 59.1k. Texture memory (estimate,
       RGBA + mips) ~561 MB → ~458 MB (one tree model instead of 12 copies).
       Placeholders (`building`, `kit-building`) unchanged. Still to check on the Quest: fps.
12. [ ] Optional: host on HTTPS (e.g. GitHub Pages) to open directly in the Quest browser without Link.

## Later phases (owner's ideas, 2026-11-03)

Order agreed with the owner: finish 65 Main → **one test person** → 68 Main → texture-sheet
(atlas) pass on all GLB buildings → more people/vehicles/props → streets and background.
"As realistic as possible" is the target throughout, within the Quest 2 budgets.

**A. People, vehicles and props that talk to you**
- A mix: standing people (porch, doorways, sidewalk), walkers on fixed routes, a horse and buggy
  and a Model T on Main St, plus talking props (e.g. a newspaper stand or a notice board).
- Conversations: walk up to someone → a dialogue box with what they say and 2–4 replies to pick
  with the controller. Lines are written per character from the sources (who lived/worked here
  c. 1920), in period voice, and kept historically honest.
- Stretch goal: an **AI character you can talk to freely** (Claude). Needs a small server
  (e.g. a Cloudflare Worker) so the API key is never in the public site, a per-chat cost, and a
  character brief built from PLAN.md/SOURCES.md so it doesn't invent history. Input by voice
  (speech-to-text) or picked prompts, since typing in VR is awkward. Owner to decide on cost.
- Realism vs. Quest 2: about 10–20 animated people in view, one material each, mid-detail bodies
  close up and simpler (or hidden) far away. Period clothing from the reference photos.
- Pipeline: same agents. The planner writes a character spec (who, where, clothes, lines), the
  asset-scout finds a CC0 base character + animations, the builder restyles it in Blender, the
  reviewer checks it, and the integrator adds the animation (aframe-extras), routes and dialogue.

- **Voice quality (owner, 2026-11-04):** Pickell's Piper voice is "ok, kinda roboty". Later:
  try a more natural voice (e.g. a newer open TTS model, or a paid service such as ElevenLabs
  if the owner accepts the cost), or record a real person. Clips + timings.json are swappable
  via `tools/make_voice_pickell.py` without touching the scene code.
  **2026-11-10: Kokoro-82M voice `am_michael` (owner's pick) is now live**, made by `tools/make_voice_pickell_kokoro.py`.

**C. Mini map (owner idea, 2026-11-04; design later)**
- A small map in a top corner of the view (desktop) / on the wrist or a toggle (VR): shows north,
  where you are and which way you face, building names/addresses, maybe people to talk to.
  Could be drawn from the 1921 Sanborn sheets or a clean simplified plan. Craft the details with
  the owner before building.

**D. Sky and distant landscape (owner idea, 2026-11-04)**
- Better sky (period-appropriate clouds, late-afternoon colour matching the baked sun from the WSW)
  and a soft, hazy far landscape — distant hills, tree lines, rooftops — so the street's ends and
  gaps don't look empty. Cheap: a painted/blurred panorama or low-poly silhouettes + fog. Ties in
  with B's "background" item.
- Options explored (orchestrator, 2026-11-04). Current scene: `gradient-sky` sphere
  (#a9bfd2 → #ecdfc4), exponential fog #ecdfc4 density 0.011, a 500 m flat ground plane.
  - Sky: (1) a CC0 Poly Haven late-afternoon HDRI turned into a 2K equirect JPG on the sky
    sphere (real clouds; pick one with no modern objects; ~11 MB GPU, 1 call) — recommended;
    (2) a few cloud cards over the gradient (cheapest); (3) procedural cloud shader (risky
    fill-rate cost on Quest 2).
  - Landscape: (1) a ring of distant hills built from USGS 3DEP elevation data (public domain)
    so the real horizon shows (to research: e.g. Sourland Mtn to the SE, Cushetunk Mtn to the
    NE — verify); (2) tree-line ring + low-detail rooftop/steeple silhouettes at the street ends
    and side streets, fading into fog; (3) a painted panorama cylinder. Recommended: 1 + 2,
    ~3–5 draw calls, < 10k tris, retune fog so the ends dissolve into haze.
- **Sky built (scene-integrator, 2026-11-04):** option 1. `#sky` sphere (r 400, 48x24 segs) shows
  `assets/textures/sky/sky-late-afternoon.jpg` (flat, fog off, sRGB), `scale="-1 1 1"`, `rotation="0 60 0"` so the
  photo's sun sits to the WSW (direction -0.92, 0, +0.38), matching the baked sun. Fog #ebe4cb, density 0.011.
  `gradient-sky` kept in js/components.js to switch back. Landscape (hills, tree lines) still to do.

**Mini map: options explored (orchestrator, 2026-11-04)**
- Desktop: an HTML canvas overlay in a top corner (no 3D cost): street plan, "you are here"
  arrow turning with the view, north arrow, building names/addresses, people markers.
- VR (HTML overlays don't show in WebXR): (a) a wrist map on the left controller that appears
  when you look at your wrist, or (b) a button (e.g. Y) toggles a floating map panel; one
  canvas-texture plane, 1 draw call while shown.
- Style: (1) clean modern plan; (2) the 1921 Sanborn sheet itself (public domain, on theme)
  with our own labels and the player dot; (3) hybrid tinted Sanborn + clean labels.
- Data: building positions/names from index.html + a small JSON; later, tap a building to see
  its history from HISTORY-SOURCES.md.
- **Owner choices (2026-11-04):** VR map = **pop-up button**; style = **polished 1921 Sanborn**
  (cleaned up, cream paper tint, our own clean labels + addresses, red "you" arrow, north badge),
  **final: style B, the "mix"** (faded Sanborn + clean Main St band; labels stand apart from the old map text). Mockup was a scratch
  image only. Sky = **real photographed sky** (option 1); landscape = **real hills from elevation
  data + tree lines/rooftop silhouettes** (options 1 + 2). Build after the weekly reset (2026-11-08).
- **Mini map BUILT (scene-integrator, 2026-11-04):** style B. `tools/prepare_minimap.py` → `assets/maps/minimap-1921.jpg` (sheets 2 + 3, x ±45 m, z −165…+50, 6 px/m) + `data/minimap.json` (bounds, streets, 11 building tags, Mr. Pickell); `js/minimap.js` draws a north-up 60 m window at ≤ 10 Hz. Desktop: top-right overlay, **N** toggles. VR: **Y** (left controller) pops a 0.6 m panel up 0.7 m ahead, 0.22 m below eye; 1 draw call shown, 0 hidden.

**B. Roads, sidewalks and background**
- Rework the road, sidewalks, curbs, lawns and side streets (Court St, Bloomfield Ave) to the
  same standard as the buildings: period surfaces from the photos, gutters, crossings, wear.
- Background: the rest of the town beyond the walkable street (distant buildings, trees, hills,
  sky) as cheap low-detail scenery.

## Street ambiance

(Non-building items that make the street feel lived in. Same pipeline: planner → asset-scout →
blender-builder → reviewer → scene-integrator.)

### Pass 1: sound and street props

**Status:** **in scene** (scene-integrator, 2026-11-04): all 34 props placed under `#street-props` in `index.html`; new `street-props` component (js/components.js) bakes them into 3 static meshes by z band (z > −20, −20 … −60, < −60) with the GLB's own lit material, plus one `LineSegments` for the wires (6 per span along both pole lines, 12-segment parabolas, 1.2 % sag; span wires from the W1/E1 and W4/E4 eye bolts to the arc-lamp hooks). Moved from the table: fountain F1 x −7.45 → −7.70 (the bowl reaches 1.32 m in front of the origin, so at −7.45 it overhung the road by 0.27 m; now its front is at x −6.38, on the curb); goods G2 z −56 → −59 (−56 cut through the 66 Main stoop at z −57.57 … −56.17); bicycle B1 → (−7.12, −14.6) rot 180 and B2 → (7.25, −76.5) rot 0 so each leans toward its post/pole with the post mid-frame. Draw calls / triangles: start view 69 → 73 / 108k → 126k; (0, 0.15, −30) 56 → 59 / 66k → 77k; (0, 0.15, −60) 52 → 55 / 21k → 32k; 17.2k triangles placed in total. No console errors. Screenshots `assets/models/previews/street-props-scene-{start,fountain,pole,arc-lamp}.png`. Earlier: props built, round-1 fixes applied (blender-builder, 2026-11-04): `assets/models/street-props.glb`
(0.83 MB, 12 nodes at the origin, 4,754 tris, one material `M_StreetProps`, one 2048² atlas
`assets/textures/street-props-atlas.jpg` = colour × baked AO, no sun bake, no alpha; lit
MeshStandard, roughness 0.9, metalness 0, no intensity factor). Scripts `tools/blender/street_props.py`,
`street_props_bake.py`, `street_props_preview.py`; previews `assets/models/previews/street-props-*.png`.
Sound already in the scene (scene-integrator). Earlier: assets ready (asset-scout, 2026-11-04;
3 new Poly Haven maps + 3 re-coloured copies, reused `metal_plate_02`, `wood_table_worn`;
audio 16 OGG, 1.96 MB). **Review round 1 (reviewer, 2026-11-04): FIXES (2):** (1) fountain horse-head
relief reads as a pointed "A"/arrowhead, not a horse head; (2) "GASOLINE" band on the pump globe garbled at its
UV seam. Everything else OK (loads, 4,594 tris, 12 nodes, 1 material, 2K atlas, no alpha).
**Fixes applied (blender-builder, 2026-11-04):** horse head remodelled as a side-view silhouette with ears, muzzle,
jaw, neck, mane locks and eye; "GASOLINE" now sits mid-front and mid-back on the band, joins in blank band
(fountain 1,587 tris, pump 616). **Review round 2 (reviewer, 2026-11-04): PASS.** Next: scene-integrator
(placement, merged bands, wires).

**Orchestrator decisions**
- Auto-approved, owner away (2026-11-04). The owner approved the direction ("sound plus a batch
  of street props: fast win, makes the street feel lived in"). Open questions below were settled
  from the photos and the 1921 Sanborn map; the owner can check them later.

#### Sources

Photos (local only, `assets/photos/reference/`), what each shows at street level:

| Photo | Date | Viewpoint | Street furniture shown |
|-------|------|-----------|------------------------|
| `flmngtndrinkingfountainbycrthous.jpg` | c. 1910 | close-up, looking W at the county building | **Primary for the fountain.** Rough-faced granite monolith with a rounded top, horse-head relief in a smoothed oval, round dressed bowl in front, dark recess above the bowl, small arched niche at the bottom left, iron 4-arm holder with a white globe on top. Behind: brick wall, "SHERIFF'S OFFICE" in a window, "DE…" sign, stoops with iron rails = County Offices (69–71). |
| `flemington_-_union_hotel_-_union_hotel_-_1910s.jpg`, `flmngtndcmuirheadsunionhtl10.jpg` | 1910s (Model T) | from the W side looking E at the hotel | The same fountain (back face, globe on top) in the foreground at the **west curb**, roughly opposite the hotel centre. |
| `flmngtnunionhtlwthsnow.jpg`, `flemington_-_the_union_hotel_in_winter.jpg` | c. 1910 | same | Fountain with globe again, sleighs in the road. |
| `flmngtncountycrthousvu09.jpg` | 1909 | NE of the courthouse | Fountain (globe) at the west curb N of the portico; tall smooth pole at the curb S of the portico; bicycle. |
| `flemington_-_some_business_blocks_on_main_street_-_1907.jpg`, `flmgtnmainststores.jpg` | 1907 / 1910s | E sidewalk at 78 Main, looking S | **Primary for poles.** Wooden pole at the east curb in front of 80–82 Main: two crossarms with glass insulators, a lamp on a short bracket at ~⅓ height; wires along the street and crossing it; low granite carriage-step blocks at the curb in front of 78 Main and by the pole; a sandwich board at the curb further S; crates under the awnings. |
| `flmngtncntycourthsview06.jpg`, `flmngtnhtdncntycrtandbldg05.jpg` | 1906 / 1905 | SE of the courthouse | Wooden pole with crossarm and bracket at the **west curb** in front of the County Offices. |
| `flmngtncntybldngsvuof08.jpg`, `flmngtncrthouspublcbldg08.jpg` | 1908 | SE | Square stone posts (~1 m) at the west curb in front of the courthouse / County Offices (hitching posts). |
| `flmngtnpobankunionhtl07.jpg` | 1907 | N of Bloomfield Ave, looking S | Fire hydrant at the east curb by the Bloomfield corner; bicycle at the curb; sandwich board near the hotel. |
| `flmingtnporichardsbldgunionhtl.jpg`, `flmngtnmainstrichardsbldgpo06.jpg` | 1906 | same | Wooden pole, one long crossarm, at the east curb at the bank's Bloomfield corner; crates and a bicycle at the curb. |
| `flmngtnmainstrycolrvu10.jpg` | 1910 | street view, trees | **Enclosed arc lamp hung over the street** on a span wire (reflector cap + globe). |
| `flmngtnbankandpovu08.jpg`, `flmngtnpoandnatbank08.jpg` | 1908 | Bloomfield corner | Horse and wagon at the curb (vehicles: later pass), poles. |
| `flmngtnunionhtlvu20s.jpg`, `flemington_-_the_union_hotel_with_parked_cars.jpg`, `flmngtnunionhtl.jpg` | late 1920s–early 1930s (car styles) | W side | Ornamental lamp standards with lantern heads and wires across the hotel front. **Later than 1920: not used.** Whitewashed lower tree trunks (note for the tree pass). |

HABS photos (1963) show no period street furniture; not used.

1921 Sanborn (sheet 2 unless noted; `x = (px − 3797) × 0.0521`, `z = (py − 6900) × 0.0521`):
- "T.H." hydrant at px (3675, 6815) → x −6.36, z −4.43 (west curb, in front of the courthouse;
  repeated on sheet 3 at (3670, 1222)).
- "T.H." hydrant at px (3910, 5155) → x +5.9, z −90.9 (east curb, N corner of Bloomfield Ave;
  matches the 1907 card).
- "F.A." (fire-alarm box) at px (3480, 6805) → x −16.5, z −4.9 (at the foot of the courthouse
  steps). Not modelled (see open questions).
- Sheet 3: "500 gal gasol. tank buried" at px (3915, 2212) → x +6.15, z +47.15: a curb gasoline
  pump in front of 100–102 Main ("Auto Supplies").
- Main St water pipes 8" and 4"; "Light: Elec." on the Union Hotel and County Hotel.

Web: Wisconsin Historical Society, Albertype card "The Fountain, Flemington, N.J." (stone fountain
with light fixture and carved horse head on a curb in front of a "Clerk's Office" and a "Dentist",
undated): https://www.wisconsinhistory.org/Records/Image/IM77896 — confirms the fountain stood
at the curb in front of the county office building. Flemington Baptist Church (1867, 170 Main St,
spire seen at the S end in the 1907 card): https://ldsgenealogy.com/NJ/books/History-of-Hunterdon-and-Somerset-counties-New-Jersey-with-illustrations-and-biographical-sketches-of-its-prominent-men-and-pioneers-part-81.htm.
National Humane Alliance fountains (1903–13, granite, a similar type; Flemington's is a rougher
local design): https://en.wikipedia.org/wiki/National_Humane_Alliance_fountains. No source on
Flemington's street lighting was found; arc lamps and pole lamps are from the 1907/1910 cards.

#### A. Street props kit: `assets/models/street-props.glb`

One GLB, built by `tools/blender/street_props.py` + `street_props_bake.py`, collection
`street_props`. **Each prop is a separate named object/node** at the file origin (not placed),
so the scene can stamp it many times. Conventions per prop: Z up, metres, **front faces −Y**
(becomes +Z in glTF), origin at the centre of its footprint at ground level (exceptions noted).
West-side placements use `rotation="0 90 0"` (front faces the street, +X), east-side
`rotation="0 -90 0"`.

**One material, one 2048² atlas** (`assets/textures/street-props-atlas.jpg`, also embedded): colour
maps tiled at real-world size, packed per prop, multiplied by a Cycles AO bake (no sun bake: the
props are placed at both orientations). No alpha anywhere (spokes, insulators are geometry), so
the whole kit can be merged into a few static meshes. Material: lit by the scene lights
(MeshStandard, roughness ~0.9, metalness 0), like Mr. Pickell. GLB ≤ 2 MB. 2K atlas justified:
11 props share it instead of 11 textures.

Texture types for asset-scout (Poly Haven CC0, 1K colour only):
| Want | Suggested Poly Haven id | Real tile | Used on |
|------|------------------------|-----------|---------|
| weathered grey-brown wood, vertical grain | `old_planks_02` (new) | 1.5 m | poles, crossarms, crates, sandwich boards |
| rough pitched light-grey granite | `granite_wall` (new) | 1.5 m | fountain monolith |
| dressed light granite | reuse `street-tree/granite_tile_03.jpg` | 1.0 m | fountain bowl, hitching posts, carriage steps |
| rusty/painted cast iron | `rust_coarse_01` (new) + reuse `polyhaven/metal_plate_02.jpg` | 0.8 m | hydrant, lamp brackets, fountain lamp holder, pump, barrel hoops |
| barrel staves | reuse `polyhaven/wood_table_worn.jpg` | 0.6 m | barrel |
Small painted lettering (two sandwich boards, pump "GASOLINE") is drawn by the builder into the
atlas (plain serif capitals, no invented business names).

Props (triangle targets are per prop; total unique ≤ 8,000):

| Node | What (1920 state) | Dimensions | Tris | Evidence |
|------|-------------------|------------|------|----------|
| `pole` | Wooden utility pole, dark weathered grey-brown, 10-sided taper 0.30 m Ø base → 0.20 m top, **10.8 m** above grade + 0.2 m below. **Two crossarms** 2.4 m × 0.09 × 0.11 at y 10.2 (upper) and 9.5 (lower), each with 2 diagonal iron braces; **crossarms run along the glTF Z axis (Blender Y)** so they end up across the wire line in the scene. 6 pin insulators per arm (pale green glass, 8-sided, 0.08 Ø × 0.10) at Blender Y = ±0.40, ±0.75, ±1.05. A small eye bolt on the front (−Y) face at y 8.6 for cross-street span wires. A few iron step pegs from 2.5 m up (optional). | 0.30 Ø × 10.8 m, arms 2.4 m | ≤ 600 | 1906, 1907 cards |
| `pole_lamp` | Bracket street lamp to bolt on a pole: iron arm 1.1 m pointing −Y (to the street) with a scroll brace, enamelled radial-wave reflector 0.42 m Ø (dark green outside, white inside), clear bulb. **Origin at the pole axis**, mounting height built in: arm at y 4.6. | reach 1.1 m | ≤ 200 | 1907 card (lamp on pole), 1906 card |
| `arc_lamp` | Enclosed carbon-arc street lamp hung from a span wire: hook + short rod, dark iron mechanism case (cylinder 0.16 Ø × 0.45), flat reflector cap 0.48 Ø, opal globe (oval, 0.30 Ø × 0.38). **Origin at the top hook.** Total 1.10 m. | 0.48 Ø × 1.10 | ≤ 320 | 1910 colour card |
| `fountain` | Horse/drinking fountain: rough-pitched light-grey granite monolith **1.05 w × 0.65 d × 1.95 h** with a rounded, irregular top; on the front (−Y) face a smooth oval medallion 0.55 × 0.45 centred 1.35 m up with a low-relief horse head (simple extruded profile, ~3 cm relief); below it a dark iron spout plate 0.45 × 0.30 at 0.75–1.05 m; a **round dressed-granite bowl** 1.00 Ø outer, 0.85 inner, 0.32 deep, rim at 0.62 m above the base, centre 0.50 m in front of the monolith face (bowl front reaches 1.0 m in front of it); water in the bowl as a dark flat disc 5 cm below the rim; at the bottom left of the front face a small arched niche 0.30 w × 0.28 h (dog trough) with a shallow basin. On top, a cast-iron 4-arm scroll holder 0.30 h with a **white opal globe 0.38 Ø** (top of globe 2.55 m). Origin: centre of the monolith base. | 1.05 × 1.65 (incl. bowl) × 2.55 | ≤ 1,500 | fountain photo + 4 hotel/courthouse cards |
| `hitching_post` | Square granite post 0.22 × 0.22 × 0.95, pyramidal chamfered top, iron tie ring (8-sided torus, 0.10 Ø) on the front face at 0.80 m. | 0.22 × 0.22 × 0.95 | ≤ 120 | 1908 cards |
| `carriage_step` | Granite mounting block 0.90 (along glTF X = along the curb) × 0.45 × 0.35 h, chamfered top edges, slightly rough. | 0.90 × 0.45 × 0.35 | ≤ 40 | 1907 card |
| `hydrant` | Post hydrant c. 1910: barrel 0.24 Ø, body height 0.80 m, flange ring at 0.08 m, domed bonnet with pentagon operating nut, two 0.08 Ø hose nozzles at the sides with caps on chains (chains as thin boxes), a larger 0.12 Ø steamer nozzle to the front (−Y). Dark red-brown paint #5A2A22, worn to iron at edges (colour is a guess). | 0.24 Ø × 0.88 | ≤ 300 | Sanborn T.H. ×2, 1907 card |
| `shop_goods` | Group at a shop front: 3 slatted wooden crates (0.60 × 0.40 × 0.35, stacked 2 + 1, the top one tilted 5°), one 12-staved barrel (0.55 Ø × 0.80, 3 iron hoops, lid). | 1.3 × 0.6 × 0.8 | ≤ 400 | 1906/1907 cards |
| `sandwich_board_groceries` / `sandwich_board_icecream` | A-frame board 0.60 w × 1.00 h, legs splayed 0.45 m at the base, dark green paint, cream lettering "GROCERIES" / "ICE CREAM · SODA" on both faces (only what the Sanborn uses say: 84 Main "Gro.", 66 Main "Conf'y"). Faces ±Y. | 0.6 × 0.45 × 1.0 | ≤ 60 each | 1907 cards |
| `bicycle` | Upright roadster bicycle c. 1910: 28" wheels (0.71 Ø, 16-gon rims + tyres), 12 spokes each as thin boxes, diamond frame (tube 0.03), upright bars, leather saddle, no gears; **modelled leaning 12° to its left** about its long axis (glTF Z), long axis along glTF Z (Blender Y), front wheel toward glTF −Z (Blender +Y). Origin: midpoint between the tyre contact points. Black enamel, nickel bars. | 1.75 × 0.55 × 1.05 | ≤ 600 | 1907 and 1909 cards |
| `gas_pump` | Curb gasoline pump c. 1920 (cabinet type): square cast-iron cabinet 0.45 × 0.45 × 1.55 on a 0.55 base, domed cap, crank handle on the right side, hose (8-sided tube) coiled on a hook, round glass globe 0.36 Ø on top (white, red band, "GASOLINE"). Red paint (guess). Total 2.20 m. | 0.55 × 0.55 × 2.2 | ≤ 500 | Sanborn sheet 3 buried tank |

Total unique ≈ 4,700 tris (well under 8k; builder may spend the margin on the fountain and pole).

**Overhead wires (not in the GLB):** the integrator builds them in the scene from the placed
poles' insulator positions, as one `THREE.LineSegments` (1 draw call, colour #1E1A17, no fog
change). Each span: a parabola with 12 segments, sag = 1.2 % of span length (≈ 0.35 m over 30 m),
`y(t) = lerp(y0, y1, t) − 4·sag·t(1−t)`. Wires per span along each side: **6** (upper arm
±0.40, ±1.05; lower arm ±1.05; glTF-local Z offsets → scene ±X around the pole). Two cross-street
**span wires** at 8.6 m (pole eye bolt) carry the arc lamps (sag 0.25 m at the lamp). Optional
2–3 service drops from E1/E2 lower arms to building fronts at ~7 m (1907 card shows several).

**Scene placements** (y = 0.15 sidewalk top unless noted; west poles `0 90 0`, east `0 -90 0`).
Curb inner edge is x ±6.64; tree pits at x ±7.5 reach ±0.83 m; every prop below was checked
against the tree pits, the front paths (z −24.07, −27.87, −31.67, −51.19, −68.69), the Nevius
door (z −7.33) and Mr. Pickell (9.50, −8.45). The walking strip x ±7.4 … ±10.3 stays ≥ 2.4 m clear.

| Prop | id | x | y | z | rot Y | Note |
|------|----|---|---|---|-------|------|
| pole | W0 | −6.90 | 0.15 | 28.0 | 90 | S of Court St (guess, keeps wires running past the start) |
| pole + `pole_lamp` | W1 | −6.90 | 0.15 | −0.6 | 90 | Court St corner; anchors arc lamp A1 (1909 card pole S of portico) |
| pole + `pole_lamp` | W2 | −6.90 | 0.15 | −21.5 | 90 | in front of County Offices N end (1906 card) |
| pole + `pole_lamp` | W3 | −6.90 | 0.15 | −55.0 | 90 | between 65 Main path and tree-west-5 |
| pole | W4 | −6.90 | 0.15 | −86.0 | 90 | opposite Bloomfield Ave; anchors arc lamp A2 |
| pole + `pole_lamp` | W5 | −6.90 | 0.15 | −118.0 | 90 | |
| pole | W6 | −6.90 | 0.15 | −150.0 | 90 | end of line |
| pole | E0 | 6.90 | 0.15 | 34.0 | −90 | S of Court St (guess) |
| pole + `pole_lamp` | E1 | 6.90 | 0.15 | 3.0 | −90 | in front of 80–82 Main (**1907 card**); anchors A1 |
| pole | E2 | 6.90 | 0.15 | −15.5 | −90 | between Nevius (N wall −11.33) and tree-hotel-7 |
| pole + `pole_lamp` | E3 | 6.90 | 0.15 | −46.5 | −90 | in the gap between the hotel and Lovell's |
| pole | E4 | 6.90 | 0.15 | −76.5 | −90 | bank's Bloomfield corner (**1906 PO card**); anchors A2 |
| pole | E5 | 6.90 | 0.15 | −92.5 | −90 | N corner of Bloomfield |
| pole + `pole_lamp` | E6 | 6.90 | 0.15 | −124.0 | −90 | |
| pole | E7 | 6.90 | 0.15 | −156.0 | −90 | end of line |
| arc_lamp | A1 | 0.00 | 8.35 | 1.2 | 0 | hook on the W1–E1 span (Court St crossing) |
| arc_lamp | A2 | 0.00 | 8.35 | −81.25 | 0 | hook on the W4–E4 span (Bloomfield crossing) |
| fountain | F1 | −7.45 | 0.15 | −29.8 | 90 | monolith centre; bowl front at x −6.45 (over the curb, horses drink from the road); in front of the County Offices between the middle and N walks |
| hitching_post | H1 | −6.80 | 0.15 | −9.4 | 90 | courthouse front |
| hitching_post | H2 | −6.80 | 0.15 | −14.6 | 90 | |
| hitching_post | H3 | −6.80 | 0.15 | −26.2 | 90 | County Offices |
| hitching_post | H4 | −6.80 | 0.15 | −35.0 | 90 | |
| carriage_step | C1 | 6.89 | 0.15 | −7.3 | −90 | in front of Nevius (1907 card) |
| carriage_step | C2 | 6.89 | 0.15 | 1.6 | −90 | next to pole E1 (1907 card) |
| hydrant | Y1 | −6.85 | 0.15 | −4.4 | 90 | Sanborn T.H. |
| hydrant | Y2 | 6.85 | 0.15 | −90.9 | −90 | Sanborn T.H. (1907 card) |
| shop_goods | G1 | 9.95 | 0.15 | −4.0 | −90 | Nevius S window, under the awning, clear of the door |
| shop_goods | G2 | 11.95 | 0.15 | −56.0 | −90 | on the bank forecourt at 66 Main (confectionery); integrator shifts ±1 m in z to clear a stoop |
| shop_goods | G3 | 9.95 | 0.15 | 11.0 | −90 | 84 Main (grocer) |
| sandwich_board_groceries | S1 | 7.25 | 0.15 | 12.5 | 0 | curb at 84 Main; faces ±Z (along the walk) |
| sandwich_board_icecream | S2 | 7.25 | 0.15 | −58.0 | 0 | curb at 66 Main (1907 card shows a board here) |
| bicycle | B1 | −7.05 | 0.15 | −15.5 | 0 | leaning on H2 (1909 card); integrator nudges so the bars touch the post |
| bicycle | B2 | 7.15 | 0.15 | −75.3 | 180 | leaning on E4 (1907 card) |
| gas_pump | P1 | 6.95 | 0.15 | 47.2 | −90 | Sanborn sheet 3 buried tank, 100–102 Main |

Counts: 15 poles (7 with lamps), 2 arc lamps, 1 fountain, 4 hitching posts, 2 carriage steps,
2 hydrants, 3 shop-goods groups, 2 sandwich boards, 2 bicycles, 1 gas pump = 34 placements,
~14k triangles in total (≤ 60k in view).

**Draw calls (≤ 10 extra; target 4):** new component `street-props` (js/components.js): loads
the GLB once, bakes each placement's transform into a copy of the node geometry and **merges
all placements into 3 static meshes by z band** (z > −20, −20 … −60, < −60) sharing the one
material → 3 draw calls (with per-band frustum culling) + 1 for the wires. Fallback if merging is
awkward: one `InstancedMesh` per node (≤ 12 calls; then drop the bicycles first).

#### B. Ambient sound

All files mono OGG Vorbis (~64 kbps, 44.1 kHz), saved to `assets/audio/`, logged in SOURCES.md.
**Total ≤ 4 MB** (estimate ≈ 2.3 MB) and **≤ ~5 min total duration** (Web Audio decodes every
clip to PCM: ~190 KB per second at 48 kHz, so 5 min ≈ 55 MB of memory). Loops trimmed at
zero-crossings with a 0.5–1 s crossfade so they loop without a click. **No modern sounds:**
asset-scout listens to every clip and rejects/cuts any aircraft, motorway hum, sirens, modern
engines, phones, reversing beeps or clear modern speech.

Licences checked 2026-11-04:
- **BigSoundBank** (Joseph Sardin): every sound "CC0 / WTFPL / public domain", attribution
  optional; direct downloads without an account at `https://bigsoundbank.com/UPLOAD/ogg/<NNNN>.ogg`
  (verified: HTTP 200, no login). Licence page: https://bigsoundbank.com/droit.html.
- **Wikimedia Commons**, G. McGrane bird recordings (NC, 1999–2008): "I, the copyright holder of
  this work, release this work into the public domain."
- **Freesound, user craigsmith**: each file below is marked **Creative Commons 0**; the
  full-quality download needs a login, but the **HQ preview MP3** (`cdn.freesound.org/previews/…-hq.mp3`,
  verified HTTP 200, no login) is good enough for 64 kbps mono. Risk: these are his digitised
  copies of 1930s–60s Hollywood studio effects; he released them CC0, but the underlying studio
  rights are not documented. Use them only where no BigSoundBank/Commons alternative exists
  (wagon, Model T, walla, shop bell) and note this in SOURCES.md. Sonniss is not used.

| File (assets/audio/) | Source + URL | Licence | Trim | Use |
|---|---|---|---|---|
| `amb-town-bed.ogg` | BigSoundBank #1911 "Countryside #3" (afternoon, May 2020, recorded in lockdown so no traffic): https://bigsoundbank.com/countryside-3-s1911.html → `UPLOAD/ogg/1911.ogg` | CC0 | 60–75 s clean section, loop | global bed |
| (alt. bed) | #0659 "Wind in a Tree" https://bigsoundbank.com/wind-in-a-tree-s0659.html; #0097 "Countryside" https://bigsoundbank.com/countryside-s0097.html | CC0 | | if #1911 has modern noise or too many European-only birds (blackbird, chaffinch, cuckoo) |
| `amb-walla.ogg` | craigsmith 817131 "Crowd Walla" (outdoor, repeating loop): https://freesound.org/s/817131/ → `https://cdn.freesound.org/previews/817/817131_2524442-hq.mp3`; alt. 675026 "Crowd walla at outdoor farmers' market" https://freesound.org/s/675026/ | CC0 | 40 s, loop | 2 positional sources |
| `bird-robin.ogg` | https://commons.wikimedia.org/wiki/File:American_Robin.ogg → https://upload.wikimedia.org/wikipedia/commons/4/4e/American_Robin.ogg | PD | 2–3 phrases, ~10 s | one-shots |
| `bird-cardinal.ogg` | https://commons.wikimedia.org/wiki/File:Northern_Cardinal.ogg → https://upload.wikimedia.org/wikipedia/commons/f/f6/Northern_Cardinal.ogg | PD | ~10 s | one-shots |
| `bird-titmouse.ogg` | https://commons.wikimedia.org/wiki/File:Tufted_Titmouse.ogg → https://upload.wikimedia.org/wikipedia/commons/4/45/Tufted_Titmouse.ogg | PD | ~8 s | one-shots |
| `bird-catbird.ogg` | https://commons.wikimedia.org/wiki/File:Gray_Catbird.ogg → https://upload.wikimedia.org/wikipedia/commons/5/5a/Gray_Catbird.ogg | PD | ~8 s | one-shots |
| `horse-carriage.ogg` | craigsmith 437076 "Horse Drawn Carriage" (wheels + hooves, hard surface): https://freesound.org/s/437076/ → `…/previews/437/437076_2524442-hq.mp3` | CC0 | 30 s | wagon pass |
| `horse-buckboard.ogg` | craigsmith 437077 "Buckboard Wagon": https://freesound.org/s/437077/ → `…/previews/437/437077_2524442-hq.mp3` | CC0 | 25 s | wagon pass (variant) |
| `horse-neigh.ogg` | BigSoundBank #0863 "Horse Neighing #3": https://bigsoundbank.com/horse-neighing-3-s0863.html | CC0 | 4 s | during a pass |
| `horse-snort.ogg` | BigSoundBank #0286 "Breath of a horse #2": https://bigsoundbank.com/breath-of-a-horse-2-s0286.html | CC0 | 1 s | during a pass |
| `modelt-run.ogg` | craigsmith 675236 "Model T steady; clatters": https://freesound.org/s/675236/ → `…/previews/675/675236_2524442-hq.mp3` | CC0 | 15 s, loop | car pass |
| `modelt-stop.ogg` | craigsmith 675234 "Model T Ford in & stop": https://freesound.org/s/675234/ → `…/previews/675/675234_2524442-hq.mp3` | CC0 | 15 s | occasional |
| `horn-oogah.ogg` | BigSoundBank #2541 "Oogah horn #2": https://bigsoundbank.com/oogah-horn-2-s2541.html (alt. #0679) | CC0 | 2 s | rare, during a car pass |
| `bell-five.ogg` | BigSoundBank #3445 "Bell 5 O'clock" (church bell strikes five): https://bigsoundbank.com/bell-5-o-clock-s3445.html | CC0 | 13 s | five o'clock fits the late-afternoon light |
| `shop-bell.ogg` | craigsmith 479988 "Shop Bell" (small bell on a shop door): https://freesound.org/s/479988/ → `…/previews/479/479988_2524442-hq.mp3` | CC0 | one 2 s jingle | Nevius door |
| `train-whistle.ogg` (optional) | BigSoundBank #3013 "Hiss of steam train #4" (steam whistle): https://bigsoundbank.com/hiss-of-steam-train-4-s3013.html | CC0 | 4 s | very distant; played at 0.8× speed (lower, closer to an American chime whistle) |

Sound sources in the scene (A-Frame `sound`: `positional: true`, `distanceModel: inverse`
unless noted; volumes are starting values for the integrator to balance by ear):

| Source | File | Position (x, y, z) | Loop / schedule | volume | refDistance | maxDistance | rolloff |
|--------|------|--------------------|-----------------|--------|-------------|-------------|---------|
| Town bed | amb-town-bed | non-positional | loop, 3 s fade-in | 0.35 | — | — | — |
| Walla, hotel veranda | amb-walla | (10.5, 1.6, −30.75) | loop | 0.30 | 5 | 45 | 1.2 |
| Walla, courthouse steps | amb-walla (start offset 20 s) | (−15.5, 1.6, −6.85) | loop | 0.20 | 4 | 35 | 1.2 |
| Birds | 4 bird clips, random | a random street-tree crown: tree position + (0, 6.5, 0) | one every 8–25 s, never the same clip twice running | 0.35–0.5 random | 6 | 60 | 1 |
| Horse + wagon pass | horse-carriage / horse-buckboard | moving along a random unseen route (below) at 2.0 m/s | every 70–150 s; 2 s fades; 30 % chance of a neigh/snort mid-pass | 0.8 | 8 | 120 | 1 |
| Model T pass | modelt-run (loop while moving) | route at 6 m/s | every 3–6 min; 40 % chance of one horn blast; 1 in 4 passes ends with modelt-stop instead | 0.6 (horn 0.5) | 8 | 150 | 1 |
| Bell strikes five | bell-five | (30, 30, 260) (Baptist church, S end of Main) | first at 75 s, then every 6 min | 0.6 | 80 | 600 | 1 |
| Shop door bell | shop-bell | (10.5, 2.2, −7.33) (Nevius door) | random every 40–120 s, only while the player is within 20 m | 0.5 | 2 | 20 | 2 |
| Train whistle (optional) | train-whistle, playbackRate 0.8 | (−500, 20, 150) | every 8–14 min | 0.35 | 150 | 800 | 1 |

Unseen routes for passing traffic (sounds only, so they must never seem to be on Main St in view):
R1 west back lane x −55, z +40 → −120 (behind the courthouse/county buildings); R2 east back lane
x +60, z −130 → +40 (behind the hotel/bank); R3 Bloomfield Ave far east (220, 1, −84) → (120, 1, −84)
(≥ 110 m, in the haze); R4 Main St far north x +3, z −270 → −200 (in the haze). Random direction.

Implementation (scene-integrator): new `js/ambience.js` with a `street-ambience` component on the
scene. Nothing plays until the first user gesture (`click`, `keydown`, `touchstart` or `enter-vr`):
then resume the Web Audio context (`this.el.sceneEl.audioListener.context.resume()`), start the
loops with a 3 s fade-in and begin the random schedulers. Pause everything on
`visibilitychange` (hidden) and resume after. **M** toggles mute (add a line to `#help`).
Load clips after the scene has loaded (not in `<a-assets>`, so they don't delay the first frame).
One-shots use `poolSize: 2`. No console errors or autoplay warnings.

#### Weathering

Poles dark grey-brown with paler sun-bleached upper parts and darker creosote base; insulators
pale green glass; iron parts rust at edges and joints; granite with grime in the pitched faces and
a darker water stain below the spout and around the bowl; hydrant paint chipped at the nozzles;
crates and boards dull and greyed; sandwich-board paint scuffed at the feet.

#### Budget

Kit ≤ 8,000 unique triangles (target ~4.7k); ~14k placed; ≤ 60k in view. One material, one 2K
atlas, GLB ≤ 2 MB. Draw calls +4 (≤ 10). Audio ≤ 4 MB, ≤ 5 min decoded.

#### Acceptance checks for the reviewer

1. `street-props.glb` has these 12 separate nodes at the origin: pole, pole_lamp, arc_lamp,
   fountain, hitching_post, carriage_step, hydrant, shop_goods, sandwich_board_groceries,
   sandwich_board_icecream, bicycle, gas_pump; one material, one 2K atlas, no alpha;
   ≤ 8,000 triangles; ≤ 2 MB.
2. Pole: wooden, 10.8 m, **two crossarms with glass insulators**, crossarms along the glTF Z axis
   (in the scene they run across the street, not along it).
3. Fountain matches `flmngtndrinkingfountainbycrthous.jpg`: rough grey granite block with a
   rounded top, horse-head medallion on the street face, round bowl projecting toward the road,
   small arched niche bottom left, iron holder with a white globe on top, ~2.5 m tall.
4. Arc lamps hang from span wires over the centre of Main St at the Court St and Bloomfield
   crossings, globe bottom ~7.2 m above the road.
5. In the scene: 15 poles along both curbs with sagging wires (6 per span, one draw call);
   hydrants at (−6.85, −4.4) and (6.85, −90.9); fountain at the west curb in front of the County
   Offices with its bowl over the curb.
6. No prop blocks a doorway, stoop, front path or Mr. Pickell; the sidewalk keeps ≥ 2.4 m clear;
   nothing floats or sinks (bases at y 0.15).
7. Draw calls at the start view (0, 0.15, 18) rise by ≤ 10 (target 4) and triangles by ≤ 60k.
8. Sound: silent until the first click/key/Enter VR, then a quiet bed with walla near the hotel,
   birds from the trees, an occasional unseen wagon or Model T, the bell striking five; M mutes;
   no autoplay warning in the console.
9. Every audio file is CC0/PD from the table above, logged in SOURCES.md; total ≤ 4 MB; no
   modern sounds audible (aircraft, motorway, sirens, modern engines).

#### Open questions / guesses

- **Fountain position (guess within ±3 m):** the Albertype caption and the fountain photo put it
  in front of the County Offices; the hotel cards put it roughly opposite the hotel centre;
  chosen z −29.8. Its exact donor/date unknown.
- **Pole line:** the 1905–07 cards show poles on both curbs; spacing (~30 m) and positions other
  than E1, W2 and E4 are guesses; heights scaled from the 3-storey fronts.
- **Street lighting in 1920:** arc lamps (1910 card) may already have been replaced by
  incandescent lamps; we keep both. The ornamental lantern posts in the hotel cards are from the
  late 1920s/30s and are left out.
- **Hydrant colour** unknown (dark in the cards); dark red-brown chosen. **Gas pump** type and
  colour are guesses (Sanborn only shows the tank).
- **Fire-alarm box** (Sanborn "F.A." at the courthouse steps) not modelled: no photo shows it.
- No flagpole/flag, benches, mailboxes or street-name signs: none appear in the period photos.
- **craigsmith (Freesound) files:** CC0 by the uploader, but they are digitised studio effects
  (see licence note); replace if better CC0/PD wagon, Model T or walla recordings turn up.
- The bed recording is French countryside; if its birds are clearly European, use the
  alternates and let the American bird one-shots carry the birdsong.
- Bell origin (Baptist church spire at 170 Main, seen in the 1907 card) is plausible, not documented.

#### Out of scope for pass 1

- Moving vehicles or animals you can see (horse and wagon, Model T, parked cars), and people:
  later passes (Later phases A).
- Road, gutter, crossing and sidewalk surface rework; side streets; background scenery (Later
  phases B).
- Night lighting / lit lamps, weather, seasons; footstep sounds for the player; interactive
  props (talking notice board, newspaper stand).
- Awnings and shop signs (already on the buildings).

## Background

(Scenery beyond the walkable street: far hills, tree lines, town silhouettes. Same pipeline.
Item D, options 1 + 2, chosen by the owner 2026-11-04.)

### Distant landscape (pass 1)

**Status:** Built (blender-builder, 2026-11-04): `assets/models/landscape.glb` 0.77 MB, 8,302 tris, 3 unlit materials (KHR_materials_unlit, vertex colours COLOR_0; trees + 1K RGBA atlas `assets/textures/landscape/tree_silhouettes.png`, alphaMode MASK 0.5, double-sided). Root nodes `landscape_far` (terrain + trees, ring 330–800 m, follows the rig, fog off) and `landscape_town` (fixed, true scale, fog on), both pivots at the origin. EXAG 1.0. Script `tools/blender/landscape.py`, texture `tools/prepare_landscape_textures.py`; previews `assets/models/previews/landscape-{north,west-ridge}.png` (only 2 under the usage cap). Known: thin pale slivers can show along a few crests (coarse 3° azimuth grid); town tree crowns are simple 6-sided lumps. Next: reviewer. **In scene (scene-integrator, 2026-11-04):** `#landscape` entity + `far-landscape` / `follow-rig` components (js/components.js); MeshBasicMaterial vertex colours (far: fog off; town: fog on); `#ground` is now a 335 m `a-circle` following the rig at 0.85; fog density 0.005, sky radius 1200, camera near 0.05 / far 10000. Start view 73 → 76 draw calls, +8.3k tris. Town silhouettes intersect no modelled entity (vertex check). Screenshots `assets/models/previews/landscape-scene-{court-st,north-end,bloomfield}.png`. Noted: at the north end of the walk (z −160) the town blocks/tree lumps are close and read as crude low-poly shapes.

**Sources**
- Elevation: **USGS 3DEP** (The National Map), `3DEPElevation` ImageServer `exportImage`, no login,
  public domain (USGS: "U.S. Geological Survey, 3D Elevation Program"). Bare earth (no trees, no
  buildings). Fetched 2026-11-04: bbox W −75.04, S 40.377, E −74.68, N 40.647 (≈ 30 × 30 km),
  640 × 480 px float32 (≈ 48 m E–W × 62 m N–S per px). Request URL in the docstring of
  `tools/prepare_landscape_dem.py`.
- Project files: `assets/maps/landscape-dem.png` (16-bit grey, value = elevation m × 10, row 0 =
  north, 640 × 480, 0.3 MB) + `assets/maps/landscape-dem.json` (bounds, encoding, transform,
  origin elevation 55.3 m, 360° horizon profile). Re-make with
  `python -I tools/prepare_landscape_dem.py <dem.tif>`.
- Street axis: OpenStreetMap way 28039047 (Main St, Court St → Bloomfield Ave): bearing **354.5°**
  (runs 5.5° west of true north going north). Origin = Main St centreline at the Court St line,
  **40.51030 N, 74.85890 W** (OSM; ±15 m).
- Hill names: Cushetunk Mountain summit 836 ft / 255 m (https://en.wikipedia.com/wiki/Cushetunk_Mountain,
  https://topoquest.com/place-detail.php?id=875786); Sourland / Rocky Hill diabase ridges to the
  SE (https://en.wikipedia.org/wiki/Rocky_Hill_Ridge); Copper Hill is a village in the Amwell
  Valley, not a hill (https://en.wikipedia.com/wiki/Copper_Hill,_New_Jersey).
- Scene: `index.html` (fog, `#ground`, `#sky` r 400, camera), Court St z 0…12.2 (west), Bloomfield
  Ave z −89.8…−77.6 (east), walk range z ≈ +50…−165 (`data/minimap.json`).

**What is really on the horizon (from the DEM, eye 1.75 m above the street at 55.3 m, Earth
curvature + refraction included; azimuth = true bearing)**

| True bearing | Scene direction (0° = street north, + = clockwise) | Feature | Distance | Top elevation | Elevation angle |
|---|---|---|---|---|---|
| 290–345° (WNW–NNW) | −65…−10° (left of north, behind the west side) | **The hills just west of town**: ridge 120–155 m high | 1.8–2.5 km | 155 m | **2.0–2.6°** (highest skyline) |
| 250–285° (W) | −105…−70° (**down Court St**) | same ridge, western part | 2.1–3.4 km | 135–175 m | 1.4–2.1° |
| 235–245° (WSW–SW) | −120…−110° | higher ground SW (Amwell Valley edge) | 4.7–5.2 km | 158 m | 1.1–1.2° |
| 5–25° (NNE) | +10…+30° (right of street north) | **Cushetunk Mountain** (Round Valley ridge) | 6.4–12.5 km | 233–251 m | **0.8–1.0°** |
| 30–95° (NE–E) | +35…+100° (**down Bloomfield Ave**) | Raritan lowland: flat, no hills | 3–8 km | 57–83 m | ≈ 0° |
| 100–190° (ESE–S) | +105…+195° (**street south** ≈ +180°) | **Sourland Mountain** ridge (SE), its western end toward Ringoes (S) | 10.6–13.7 km | 127–168 m | 0.3–0.5° |
| 195–230° (SSW) | +200…+235° | low ground, gentle rises | 6–10 km | 84–127 m | 0.1–0.6° |

So: looking **north up Main St** the skyline is the west ridge (≈1.4° at the left, falling off) with
Cushetunk Mountain faint beyond to the right; **down Court St** the west ridge fills the view at
~2°; **down Bloomfield Ave** the land is flat (tree lines only); **looking south** the long, low
Sourland line sits ~0.3–0.5° up, very hazy. All angles are small (a 2° ridge is ~40 px tall on a
Quest 2): that is the real Hunterdon skyline. **No vertical exaggeration** (owner asked for real
hills). The builder keeps an `EXAG` knob (default 1.0); the reviewer may accept ≤ 1.5 for terrain
**beyond 6 km only** if Cushetunk/Sourland do not read at all, and must note it.

**Geographic → scene transform (true scale)**
- `E = (lon + 74.85890) × 84 656` m, `N = (lat − 40.51030) × 111 132` m.
- Street bearing b = −5.5°: `x = 0.9954·E + 0.0958·N`, `z = 0.0958·E − 0.9954·N`,
  `y = elev − 55.3 − d²/(2·6 371 000)·0.87` (curvature + refraction; d = horizontal distance).
- Check: Cushetunk summit area (bearing 15°, 10.3 km) → scene ≈ (+3.6 km, −9.7 km); west ridge
  top (305°, 1.9 km) → (−1.4 km, −1.2 km); Sourland (135°, 11.2 km) → (+7.1 km, +8.6 km).

**Rendering approach: a distance-compressed "3D skybox"** (why: true 12 km geometry would need a
camera far plane of 13+ km and a 12 km sky sphere, and with a 24-bit depth buffer the ridges,
tree cards and terrain would z-fight at that range; at true scale the inner ring would also hide
the town). Build the terrain from true coordinates, then for every vertex at true horizontal
distance r (from the origin) and relative height y:
- `r' = 330 + 470 · ln(r / 700) / ln(13000 / 700)` m (r 0.7 km → 330 m, 2 km → 499 m,
  5 km → 646 m, 11 km → 773 m, 13 km → 800 m), same bearing;
- `y' = 1.75 + (y − 1.75) · r'/r` (keeps the **elevation angle seen from eye height** exact).
- Order of ridges along every bearing is kept (r' grows with r), so occlusion is correct.
- In the scene the landscape group **follows the player rig** in x/z with factor **f = 0.85**
  (`position = 0.85 × rig position`, y fixed) so walking 200 m does not make hills slide past
  the way a 500 m object would. Error left: the 2 km west ridge shifts ~1° too little over the
  walk — acceptable.

**Massing / content (one GLB `assets/models/landscape.glb`, two root nodes)**

Node `Far` (follows the rig; entity at origin, rotation 0 0 0):
1. **Terrain ring** (1 mesh, 1 material): polar grid around the origin, **120 azimuth segments ×
   24 radial rings**, rings log-spaced r = 0.70 … 13.0 km (true), sampled bilinearly from
   `landscape-dem.png` (decimetres → m) and then compressed as above. ≈ 5.8k tris.
   - **Inner apron:** the first ring (r' 330 m) at y' = −0.30, rising to the sampled terrain by
     r' ≈ 360 m (hidden under/behind the ground disc edge; see Ground). Clamp any terrain with
     y' < −0.3 inside r' 400 to −0.3.
   - **Outer skirt:** one extra ring at r' 800 dropping to y' = −40 so no sky shows under the far
     edge; its colour = horizon colour.
   - **Colour = vertex colours (COLOR_0), unlit** (base × simple sun term × haze), no texture,
     no lightmap:
     - base: woods `#47512f` where true elevation > 120 m or slope > 8 % (the diabase ridges were
       wooded c. 1920), else farmland: low-frequency noise mix of `#8a8752` (hay/stubble),
       `#6f7a3e` (pasture/corn), `#5a6236` (woodlot) — ~25 % woodlot;
     - sun term `0.78 + 0.22·max(0, n·s)`, s = to-sun in Blender axes `(−0.86, −0.36, 0.36)`
       normalised (WSW, 21° up; scene sun direction (−0.92, 0, +0.38));
     - haze by **true** r: `h = 1 − exp(−r / 4500)` (0.7 km 14 %, 2 km 36 %, 5 km 67 %,
       11 km 91 %); haze colour `#bfc6c2` (cool blue-grey) blended to `#ebe4cb` (sky horizon /
       fog) for r 8–13 km; final = mix(base·sun, hazeColour, h);
     - inner seam: from r' 330 to 400 blend toward the **fogged ground colour**
       mix(`#6f6a45`, `#ebe4cb`, 0.93) so the ground disc edge and ring meet without a line.
2. **Tree lines** (1 mesh, 1 material, alpha-tested): vertical double-sided quads (not
   billboards) standing on the terrain, base sunk 1.5 m (true) into it, compressed with the same
   r'/y' rule (their height scales by r'/r too). ~600 quads ≈ 1.2k tris.
   - c. 1920 Hunterdon: open farmland with **hedgerows** along field edges, **woodlots** and
     wooded stream lines, orchards near town, solid woods on the ridge crests.
   - Band A, true 0.8–1.6 km all round: town-edge trees, orchards, farm groves, 12–22 m tall,
     dense (this band also hides the inner seam). Band B, 1.6–5 km: hedgerow strips 8–14 m tall
     and woodlot clumps 15–22 m, ~40 % coverage. Ridge crests (west ridge, Cushetunk, Sourland):
     a continuous 18–22 m crown fringe along the skyline so the ridge tops look wooded, not bald.
     Also 4–6 small farmhouse + barn silhouettes in Band B (row 3 of the atlas).
   - Texture: **one generated 1K RGBA atlas** `assets/textures/landscape/treeline_atlas.png`
     (no download): 3 rows of soft-edged crown silhouettes (round deciduous crowns, mixed
     heights, a few pointed cedars), row 3 = farm buildings + windbreaks. Greyscale × vertex
     colour; vertex colour = foliage `#3f4a2c` (barns `#7d4a36` red, houses `#d8d2c0`) hazed with
     the same h(r) as the terrain, plus +5 % haze so trees never read darker than the ridge behind.
     alphaTest 0.5, mipmaps on.

Node `Town` (fixed, true scale, scene fog ON; entity at origin, rotation 0 0 0): low-detail
**rooftop / steeple / tree silhouettes** where the street opens, beyond the modelled blocks:
- **North end**: z −175 … −250 both sides of Main St (x ±12 … ±40): 6–8 house/store blocks (2–3
  storeys, 8–12 m eaves, gable roofs ridge parallel or across), street-tree crowns, and **one
  church steeple** (~30 m, guess, west side ~z −230).
- **South end**: z +70 … +140, x ±12 … ±40: 5–6 houses (2–2½ storey, gables), trees.
- **Court St (west)**: x −60 … −200, z −5 … +20: 4–5 houses along both sides, big shade trees
  (guess; the jail/courthouse grounds occupy the near part).
- **Bloomfield Ave (east)**: x +65 … +200, z −95 … −70: 4–5 houses, trees; land falls toward the
  lowland (flat skyline behind).
- Simple extruded boxes + gable prisms, tree crowns as 20–40-tri lumps on a trunk-less base;
  ≈ 1.5k tris; flat vertex colours (walls pale cream / white / red-brown brick `#8a4b3a`, roofs
  dark slate `#4a4a4e`, trees `#46532f`) with the same simple sun term, no texture. Keep all of it
  within x ±200, z −250 … +140 (so it is always nearer than the ring's inner edge).
- Must not intersect any existing entity (check `index.html` placeholders: nothing beyond the
  street blocks).

**Ground, fog, sky, camera changes (scene-integrator)**
- **Fog:** keep exponential `#ebe4cb`; density **0.011 → 0.005** (100 m 22 %, 200 m 63 %, 330 m
  93 %). Street ends still dissolve, town silhouettes read faintly; the `Far` node uses
  **`fog: false`** (its haze is baked into the vertex colours).
- **Ground:** replace the fixed 500 m `#ground` plane with a **disc radius 335 m** (64 segments,
  same colour #6f6a45) inside the following group (f = 0.85), so its edge always meets the ring's
  inner apron and never shows as a line. The paved streets/lawns stay as they are on top.
- **Sky sphere:** radius 400 → **1200** (the ring reaches 800 m from the moving origin; worst case
  ~ 800 + 0.15·170 + 170 < 1200). Keep `fog: false`, same yaw.
- **Camera:** set `near: 0.05` (default 0.005) — depth precision at 800 m goes from ~8 m to
  ~0.8 m; far stays 10000. Hands/controllers are never closer than 5 cm.
- Materials: replace `Far` materials at load with `MeshBasicMaterial({vertexColors: true, fog:
  false})` (trees: `+ map, alphaTest 0.5, side: DoubleSide`); `Town` with
  `MeshLambertMaterial({vertexColors: true})` or basic + baked sun (fog on). One small component
  (e.g. `far-landscape` in `js/components.js`) does both and the rig-follow.
- Render order: normal opaque; no transparency sorting needed (alpha test only).

**Blender conventions for this asset**
- Blender X = scene x, Blender Y = **−scene z** (north = +Y), Z up; glTF export turns it into the
  scene frame directly; entity rotation `0 0 0` (not the building rule).
- Script `tools/blender/landscape.py` (reads `assets/maps/landscape-dem.png` + `.json` with Pillow
  or Blender's image API; builds `Far` and `Town`); export with COLOR_0, no lightmap bake (skip
  the `_bake.py` pattern; this asset is unlit). Source `assets/models/source/landscape.blend`,
  previews `assets/models/previews/landscape-*.png` from eye height (1.75 m) at the origin
  looking N, S, W (Court St), E (Bloomfield), and one top view.

**Budget**
- ≤ **10k tris** (target 8.5k: terrain 5.8k, trees 1.2k, town 1.5k). **3 draw calls**
  (terrain, trees, town) + the existing ground (now a disc). GLB ≤ 1 MB; 1 texture (1K RGBA atlas).
  No 2K lightmap.

**Acceptance checks for the reviewer**
1. From (0, 1.75, 0) looking along true bearing 305° (scene ≈ 50° left of north) the skyline
   is a wooded ridge at **~2.5° ± 0.5°** elevation; looking down Court St (scene west) it is
   ~1.5–2°.
2. Cushetunk Mountain shows as a faint, low, broad hump right of street north (scene +10…+30°)
   at ~1°, lighter/hazier than the west ridge.
3. Looking scene south (street south) a long low ridge (Sourland) at ~0.3–0.5°, very pale.
4. Looking down Bloomfield Ave (scene east) the horizon is flat: only tree lines, no hill.
5. Colours get steadily lighter and bluer-grey with distance and reach the sky horizon colour
   at the far edge: **no visible line** where terrain meets sky, and no gap under the far edge.
6. No visible seam / line / z-fighting where the ground disc meets the ring (test at the start
   view and at z −165 and z +50 looking out).
7. Tree lines read as hedgerows/woodlots with soft crowns, never darker than the nearer town
   silhouettes; no flicker between trees and terrain at 0.05 near plane.
8. Town silhouettes visible at the north and south street ends and down both side streets,
   fogged, nothing floating, nothing intersecting modelled buildings.
9. Walking from z +50 to z −165 the hills do not visibly slide with the player or swim; the
   ring never cuts through any building or the street.
10. ≤ 10k tris, 3 draw calls, GLB ≤ 1 MB; start view total stays ≤ ~70 calls / ≤ 170k tris.

**Risks**
- VR scale: the compressed ring is at 330–800 m; stereo disparity there is already ≈ 0, so it
  reads as "very far" (true 12 km looks the same). Don't move it nearer than 300 m.
- z-fighting: apron below the disc edge (−0.3 m) + near 0.05 handle the inner edge; tree bases
  are sunk, not touching.
- Draw distance: everything within 1200 m; far plane 10000 is fine.
- Quest fill-rate: terrain/trees cover only a thin band near the horizon; alpha-tested cards
  are small on screen.
- The DEM is modern (lidar): later road cuts, the Round Valley dams (1960s) and quarries are
  either hidden behind ridges or below 50 m resolution; no effect at this scale.

**Open questions / guesses**
- Name of the ridge 1.8–3.4 km west/north-west of town: not found (not Copper Hill, which is a
  village). Labelled "the hills west of town". (Guess.)
- Season: summer foliage assumed (matches the street trees).
- Land cover mix c. 1920 (≈ 75 % farmland, woods on ridge crests) is typical for Hunterdon,
  not mapped. (Inferred.)
- Town silhouettes: number, heights and the north-end steeple position are guesses (Sanborn
  sheets 1, 4–8 not checked under the usage cap). A later pass can place real churches.
- Exact origin ±15 m and bearing ±1° (OSM); the Sanborn north arrow was not measured.

## People

(Character specs, written by the planner. Same pipeline as the buildings: planner → asset-scout →
blender-builder → reviewer → scene-integrator. Dialogue lines live in `data/dialogue/<id>.json`.)

### Test person 1: John B. Pickell, clerk at the Nevius store (78 Main St)

**Status:** in scene and **voiced** (scene-integrator, 2026-11-04: clip per line, word-by-word text, Talk for the clip length; see "Voice in scene" below). Earlier: built (blender-builder, 2026-11-03): `assets/models/npc-pickell.glb`, 1.25 MB, one
skinned mesh, one material, one 2048² JPEG atlas (colour × baked AO, embedded; copy at
`assets/textures/npc-pickell-atlas.jpg`), 12,756 triangles, 65 bones (UAL rig unchanged apart from a
uniform 0.9403 scale to 1.72 m), clips `Idle` 6.0 s, `Talk` 3.0 s, `Walk` 1.33 s (24 fps), soles at
y 0, height 1.719 m, faces +Z. MPFB 2.0.18 installed and the CC0 system-asset pack loaded: head,
neck and hands are MakeHuman (age 0.62 ≈ 41 y, `middleage_caucasian_male` skin, low-poly eyes,
eyebrow001 painted in, short02 as the hair-shell guide). Suit, shirt, collar, tie, oxfords, tape,
chain and pencil modelled by script. Scripts: `tools/blender/npc_pickell.py`, `npc_pickell_bake.py`,
`npc_pickell_preview.py`; previews `assets/models/previews/npc-pickell-{front,three-quarter,closeup,talk,scale}.png`.
Known flaws for review: trousers look a little baggy at the crotch in the wide UAL idle stance; small
dark specks can show at the coat's left shoulder by the collar in some frames; coat shoulders a bit
square. Next: reviewer.
**Review round 1 (reviewer, 2026-11-03): FIXES.** Budgets, scale, clips, Idle/Talk feet locked and
seamless loops, and no console errors all pass. To fix: the moustache reads as a "toothbrush";
trousers hang in a drop-crotch in the 0.59 m wide stance; the jacket's left shoulder/collar is torn
with dark facets and has no collar round the back of the neck; the lower jacket fronts are jagged;
the grey shirt cuffs look like a wristwatch; the head looks down in Idle. Next: blender-builder (fixes).
**Round-1 fixes applied (blender-builder, 2026-11-03):** GLB re-exported (1.25 MB, 12,806 triangles,
65 bones, 1 mesh / 1 material / 1 2K atlas; Idle 6.0 s, Talk 3.0 s, Walk 1.33 s; soles y 0, height
1.719 m) and all 5 previews re-rendered. (1) Moustache now spans the whole upper lip to just short of
the mouth corners, fuller, tapered ends. (2) Idle/Talk re-keyed: legs turned in and closed up, ankles
0.28 m / balls of the feet 0.295 m apart (was 0.59 m), toe-out 12°, feet still locked (drift ≤ 0.3 mm);
trouser hip tube tucked inside the legs, no drop crotch. (3) Coat collar is its own part, continuous
from notch to notch round the back of the neck (≈1 cm of shirt collar shows); coat AO baked without
collar/tape over it — 0 near-black texels visible on shoulders/collar in Idle t = 1, 2, 3, 5 s and
Talk. (4) Lower fronts weighted to pelvis/spine_01 (thighs only a small share), front skirt eased over
the thighs, waistcoat points re-cut (centre notch, two points). (5) Plain ivory starched cuffs, ~1 cm,
no dark inner ring; ragged sleeve-hem band removed; cuff buttons smaller. (6) Idle gaze raised from
−12° to −3° (Talk −13° → −7°), glance kept. (7) Watch chain: shallow curve pocket to pocket (±8 cm)
with a T-bar at the centre buttonhole. Next: reviewer (round 2).
**Review round 2 (reviewer, 2026-11-03): PASS.** All 7 fixes verified in the browser (12,806 tris,
1 mesh/material, no console errors; Idle/Talk loops seamless, ankles 0.28 m apart, feet drift
≤ 4 mm): full clipped moustache, clean continuous coat collar and shoulders, ivory cuffs, level gaze,
chain across the waistcoat. Minor notes, no fix needed: a soft fabric fold still hangs between the
thighs in Talk; the lower right coat front corner is slightly angular.
**In scene (scene-integrator, 2026-11-04):** `#npc-pickell` at (9.50, 0.15, −8.45), rotation 0 −60 0, clear of the step (his max x 9.74 < 10.05) and awning; `animation-mixer` (aframe-extras 7.7.0 loaders, pinned) plays Idle, crossfades (0.4 s) to Talk while he speaks a line; blob shadow kept. New `js/people.js` (`npc`, `blob-shadow`, `dialogue` system: one 0.80 × 0.50 m canvas panel, scripted provider + commented AI hook), `data/dialogue/pickell.json` (11 nodes verbatim, sources, brief), `#right-laser` in the rig. Tested on desktop: opens at 2.45 m, closes at 4.09 m, turns to face the visitor and back to −60°, every node reached by keys 1–3 and mouse clicks, `again` on the return visit, `[Walk on]` closes; VR laser/trigger simulated with events (not tested in a headset). Draw calls / triangles: start view 159 / 90.9k → 161 / 103.7k; panel +1 call (+1 laser line in VR). Next: owner check in the headset.
**Voice (2026-11-04, owner approved TTS):** 11 clips `assets/audio/voices/pickell/<node-id>.ogg`
(one per node `text`; replies are not voiced), 5.4–18.4 s, 1.29 MB total, mono Vorbis 64 kbps
22.05 kHz, −18 LUFS, plus `timings.json` (node → `duration_s`, `words[{w,start,end}]`, one entry per
on-screen token, times from Piper's phoneme alignment) for word-by-word reveal. Offline Piper TTS,
model `en_US-libritts-high` speaker 595 (calm, low ~90 Hz), length_scale 1.15, noise defaults;
CC BY 4.0 attribution text in SOURCES.md (needs a credits line). Regenerate with
`tools/make_voice_pickell.py` (pronunciation map inside). Next: scene-integrator (play the clip
when a line opens, drive Talk/Idle by the clip length, reveal words by `timings.json`).
**Voice in scene (scene-integrator, 2026-11-04):** `npc="…; voice: assets/audio/voices/pickell/"`.
When a line opens its clip plays as a `THREE.PositionalAudio` at his head (1.65 m above his feet;
inverse distance, ref 1.5 m, rolloff 1.6: about −6 dB at 2.5 m, −18 dB at 8 m; gain 1.3) on the
shared AudioContext/listener of `js/ambience.js` (new small API: `audioReady`, `prefetch`,
`getBuffer` (decode once, cached by URL), `makeVoice`, `duck`), so M mutes him too; clips download
when you come within 25 m and decode once sound is on. Town bed and walla duck −4 dB while he
speaks. Text appears word by word on the audio clock (panel redrawn only when a word appears);
replies show at the end of the line; Space / Enter / 1–3 / a click / the right trigger during a line
shows it all at once (voice keeps going); a reply fades the clip out (0.08 s) and starts the next;
walking away fades it out (0.25 s). Talk runs for the clip's `duration_s`, then Idle. Missing clip
or sound not started yet → old text-only behaviour. No jaw movement: the GLB has no jaw bone (only
`Head`, `neck_01`) and no morph targets. CC BY 4.0 credit added as `#credits` (bottom-left of the
page). Tested on desktop: word reveal within 0–20 ms of `words[].start`, Talk 10.36 s for `start`
(10.358 s clip), clips switch on reply, fade-out on walking away, 404 → text only, no new meshes.

**Who**: **John B. Pickell** (b. c. 1879), the senior clerk of the Nevius dry-goods store at
78 Main, standing on the sidewalk at his shop door, as a clerk does in the 1907 and 1910s cards.
He is a **real, documented person**: the *Whitehouse Review* (17 Apr 1945, p. 1, quoted on
78main.wordpress.com) says he "went to the Nevius store as a clerk in 1895 at the age of 16" and
had been its manager "for the past 21 years" (i.e. from c. 1924). So in **September 1920** he is
about 41, a clerk of 25 years' standing, not yet manager. His face, voice and opinions are not
documented: the likeness is generic and his lines stick to sourced facts about the store and town.
Setting of the scene's day: **a warm afternoon in early September 1920** (trees in full leaf;
suffrage just ratified; presidential election coming in November).

**Orchestrator decisions** (settled from the sources; owner to check later)
1. **Person = the Nevius store clerk, John B. Pickell.** Evidence: the two "Some business blocks"
   cards (`flemington_-_some_business_blocks_on_main_street_-_1907.jpg`, `flmgtnmainststores.jpg`)
   show **a man in a dark suit standing at the door of this very store**, under an awning lettered
   **"DRY GOODS · NEVIUS BROS · NOTIONS"**; the 1909 card is titled "Nevius Store"; Sanborn 1921
   sheet 3 labels 78 Main **"Dry Goods"**; Pickell's 50 years (1895–1945) "with the Nevius store in
   Flemington" make him the one documented employee there in 1920. The store is 25 m from the start
   view (ahead-right), so the owner meets him at once. (The Union Hotel proprietor in 1920 and the
   bank's 1920 staff were not found in any source; the 1910 card names D. C. Muirhead, too early.)
2. **Those two "business blocks" cards show 78 Main, looking south** (not west-side blocks as an
   earlier note says): quoined corners, 1 + 2 + 1 window rhythm, round 3rd-floor heads and the
   arched crest match the 78 Main model; the frame building beyond the alley is 82 Main. (Side
   note for the orchestrator: the 1907 awning lettering could be added to the 78 Main model later;
   its spec chose "no lettering".)
3. **Name used for real**, with title "Mr. Pickell" in the panel header. Middle name unknown
   ("B." only). Wife/family not mentioned in any line (unknown).
4. **Spot: on the sidewalk in front of the north display window, just north of the recessed
   door**, where the man stands in the cards. Scene position **(9.50, 0.15, −8.45)** (store front
   x 10.30; step edge x 10.05; entry opening z −8.18 … −6.58; north window z −10.68 … −8.18),
   under the awning (bottom 2.45 m above the sidewalk; he is 1.72 m).
5. **Default facing `rotation="0 -60 0"`** (front +Z turned to (−0.87, 0, +0.50): across the street
   and 30° toward the south, i.e. toward the visitor coming up from the start point (0, 18)).
   While a conversation is open he **turns (whole entity, eased 0.6 s, yaw only) to face the
   visitor**, and turns back to −60° when it closes.
6. **Clothes = a conservative dark three-piece business suit, bareheaded** (the clerk in the
   cards wears a dark suit with waistcoat and white collar, no hat; a 41-year-old small-town
   clerk would not follow the young men's 1920 fashions). Tape measure round the neck = the one
   trade marker (dry-goods clerks measured cloth by the yard).
7. **Base: Quaternius Universal Animation Library rig + clips (CC0), with a realistic MPFB2
   (MakeHuman, CC0) head and hands and a modelled 1920 suit, skinned to that rig** (comparison
   below). Mixamo is not used: it needs the owner's Adobe login and its terms forbid
   redistributing raw characters/animations, which a public GitHub Pages repo comes close to.
8. **Lighting: real-time scene lights, not the baked-lightmap method.** A lightmap is fixed to the
   mesh and would be wrong once he moves. He gets a standard (lit) material whose colour atlas
   already has **baked ambient occlusion** multiplied in, lit by the scene's existing hemisphere +
   directional lights. Check: the low WSW sun reaches under the 1.9 m awning below ~2.0 m at his
   spot, so he is in sun like the shop front behind him; no shade factor needed. No real-time
   shadows; a **soft blob shadow** under the feet (+1 draw call, see Budget).
9. **Dialogue panel = one canvas-texture plane** (text and reply buttons drawn on a 2D canvas),
   1 draw call, instead of A-Frame `text` entities (one call each, ~8 for a panel).
10. **aframe-extras 7.7.0, loaders bundle only** (contains `animation-mixer`; published
    2026-04-01, 7 months old; README: v7.x supports A-Frame 1.2–1.7, so 1.6.0 is fine).

**Pure guesses** (no source; change freely)
- Height 1.72 m, medium build with a slight middle-aged thickening; light skin, ruddy; dark brown
  hair greying at the temples; clipped moustache (the card's clerk has one; Pickell's face unknown).
- Suit colour (charcoal grey), tie colour (maroon), pencil behind the ear, watch chain.
- The personal touches in his lines: rolling bolts as a boy, "boys will be boys" about the 1896
  signature, the hotel full on court days, motor cars on Saturday evenings, the closing joke.
- Early-September date (chosen to fit the leafy trees and the 1920 suffrage news).

**Sources**
- Map: 1921 Sanborn **sheet 3**, 78 Main "Dry Goods", 3 storeys, 35', brick (see the 78 Main spec
  above for pixel lines); his spot is measured from that spec's shop-front layout.
- Photos (local only, never commit):
  - **Primary: `flmgtnmainststores.jpg`** ("Main Street Stores – 1910s") and the same view
    **`flemington_-_some_business_blocks_on_main_street_-_1907.jpg`** (1907): looking south along
    the east side from in front of the Union Hotel. At px ≈ (225–245, 445–520) a man stands at
    the Nevius door: bareheaded, short light/greying hair, moustache, **dark sack suit with
    waistcoat, white collar and dark tie**, hands at his sides/in pockets, dark shoes, relaxed
    weight-on-one-leg stance. Only ~75 px tall: proportions and garment set, not a face.
  - `flmngtnneviusstoreandununionhtl09.jpg` (1909): the store front and awning behind him.
  - `flmngtnunionhtlvu20s.jpg`, `flemington_-_the_union_hotel_with_parked_cars.jpg` (1920s): motor
    cars parked along the curb; figures on the hotel porch too small/blurred for clothing.
  - `flmngtnmainstrycolrvu10.jpg` (1910): a few tiny pedestrians only. HABS 1963 photos: no people.
- Web:
  - 78 Main history blog (Dan Lynn): https://78main.wordpress.com/ ; Pickell's 50 years and the
    1896 signature: https://78main.wordpress.com/2009/05/07/41/ ; Jacob Nevius ("began his first
    store in Flemington in 1878", Somerville store 1883, died in Somerville 5 May 1926):
    https://78main.wordpress.com/2010/01/18/jacob-nevius-the-founder/ ; 1917 ad "Dress Materials":
    https://78main.wordpress.com/2009/06/11/the-nevius-store-1917/ ; 1901 ad (ladies' jackets):
    https://78main.wordpress.com/2009/06/11/ladies-jackets-for-4-75-well-in-1901/
  - Goodspeed Histories, "Fulper's Store": https://goodspeedhistories.com/fulpers-store/ (store on
    the lot before 1856; W. H. Fulper's 1880 alterations). Note: it says the Nevius family "took
    possession… in the 1930s" — contradicted by the 1907 awning, the 1909 title and Pickell's
    1895–1945 service, so not followed.
  - Court House 1828, county jail on the ground floor (new jail only in 1925):
    https://goodspeedhistories.com/hunterdons-courthouse-1828/ ,
    https://preservationnj.org/pnj-on-tour-the-historic-hunterdon-county-courthouse-and-jail/
  - Union Hotel: front of 1878 on an older tavern: https://en.wikipedia.org/wiki/Union_Hotel_(Flemington,_New_Jersey)
  - Fair: fairgrounds bought 1856 by the Hunterdon County Agricultural Society; auto racing from
    1915: https://en.wikipedia.org/wiki/Flemington_Speedway
  - Fulper Pottery: pottery in Flemington since 1814, Fulper from 1860, Vasekraft art ware 1909:
    https://ellarslie.org/?p=3784 , https://emuseum.its.iastate.edu/people/3661/fulper-pottery-co/objects
  - Population 2,590 (1920 census): https://en.wikipedia.org/wiki/Flemington,_New_Jersey
  - 18th Amendment in force 17 Jan 1920: https://en.wikipedia.org/wiki/Eighteenth_Amendment_to_the_United_States_Constitution ;
    19th Amendment, New Jersey ratified 9 Feb 1920, adopted Aug 1920, first presidential vote
    2 Nov 1920 (Harding v. Cox): https://en.wikipedia.org/wiki/Nineteenth_Amendment_to_the_United_States_Constitution
  - Prices about double 1914 by mid-1920 (CPI 10.0 → ~20), falling from late 1920:
    https://fred.stlouisfed.org/series/CPIAUCNS
  - Dress c. 1920: FIT Fashion History Timeline 1920–1929 (soft collars spreading, oxfords and
    brogues replacing boots, short hair; women: rising hems, dropped waist, cloche, early bob):
    https://fashionhistory.fitnyc.edu/1920-1929/

**Placement**
- Entity `#npc-pickell` at **(9.50, 0.15, −8.45)**, `rotation="0 -60 0"`, east sidewalk (top
  y 0.15), 0.55 m in front of the step, 0.27 m north of the entry opening, clear of the awning
  arms; nothing else stands there (east street trees end at z −18.8).
- Start view (0, 0.15, 18) facing north: he is ~28 m away, ~20° right of centre, framed by the
  striped awning. Trigger radius 2.5 m (horizontal distance camera → entity).
- Blender frame: Z up, metres, **front faces −Y**, origin **on the ground between the feet**
  (soles at z = 0), so glTF +Z = his front in the scene.

**Appearance (1920 state, builder detail)**
- **Body**: man, ~41, **1.72 m**, medium build, slight paunch under the waistcoat; head:body ≈
  1:7.5 (realistic, no stylised big head/eyes). Light skin with a ruddy, slightly weathered
  face; faint lines at the eyes; clean-shaven except a **clipped moustache** (not past the
  mouth corners).
- **Hair**: short back and sides, longer on top, **side parting on his left**, combed flat with
  pomade (slight sheen), dark brown **#3A2A1E**, **grey at the temples**. Bareheaded.
- **Jacket**: single-breasted **sack coat**, 3 buttons (top two fastened, bottom open), soft
  natural shoulders, **notch lapels ~7.5 cm wide**, hip length (to the top of the thigh), straight
  hang, flap side pockets + a welt breast pocket with a white handkerchief edge showing; 4 cuff
  buttons. Charcoal-grey worsted **#3B3A3C** with a barely visible herringbone.
- **Waistcoat**: same cloth, 5–6 buttons, V-neck showing above the jacket's fastening, a **gold
  watch chain** (#B8964A) across between the pockets.
- **Shirt**: white/ivory **#F0ECE2**; **detachable starched collar**, round-cornered turn-down
  ("club"/high fold, ~5 cm high); starched cuffs ~1 cm showing below the jacket sleeves.
- **Tie**: narrow four-in-hand knot, dark maroon **#5A1F24** with a faint small figure, tucked
  into the waistcoat.
- **Trousers**: same cloth, straight and moderately slim, **pressed crease**, **turn-ups (cuffs)
  ~4 cm**, slight break on the shoe; no belt visible (braces under the waistcoat).
- **Shoes**: black calf **lace-up oxfords** (#1C1714), polished toe, low heel.
- **Trade details**: a **cloth tape measure** draped round the neck under the collar points,
  ends hanging to the waistcoat (cream #E6D79A with black marks, ~1.6 cm wide); a yellow pencil
  behind his right ear.
- **Not present (modern)**: wristwatch, glasses, belt loops, logos, visible zips.
- **Pose**: relaxed standing idle, weight on one leg, arms at the sides (one hand may rest in a
  trouser pocket in the idle clip if the rig allows without clipping; otherwise both at sides).
- For later women NPCs (research note): c. 1920 small-town NJ — skirts mid-calf, loose bodice,
  waist dropping toward the hips with a sash, shirtwaist blouses, long hair pinned up (the bob
  only just appearing), wide-brimmed or cloche hats, stockings, strap or laced shoes with low
  Louis heels.

**Base character and animations** (for asset-scout and blender-builder)
- Compared:
  - *Quaternius Ultimate/Modular low-poly characters, KayKit*: CC0, 1–3k tris, cartoon faces —
    too stylised for "as realistic as possible".
  - *Quaternius Universal Base Characters* (Aug 2025, CC0, ~13k tris, "Regular" proportions,
    20 hair styles in Source; free Standard tier = 2 base models + 5 hair styles):
    https://quaternius.com/packs/universalbasecharacters.html — natively on the UAL rig, but
    tagged stylised and in underwear (suit to be modelled anyway).
  - *MPFB2 / MakeHuman* (Blender extension 2.0.16, GPL code; **core assets and exported models
    CC0**: https://static.makehumancommunity.org/about/license.html ,
    https://extensions.blender.org/add-ons/mpfb/): the most realistic CC0 humans (real
    proportions, skin textures, age/weight sliders), but its own rigs carry no animations.
  - *Mixamo*: best motion, but needs an Adobe login and forbids standalone redistribution — not now.
- **Recommended (decision 7)**: the **Quaternius Universal Animation Library** (CC0, March 2025;
  Standard tier free, ~45 clips; the Pro tier may also be free — to confirm):
  https://quaternius.com/packs/universalanimationlibrary.html /
  https://quaternius.itch.io/universal-animation-library — supplies the **rig and the Idle and
  Walk clips** (and any talk/gesture/emote clip it has). The **visible body comes from MPFB2**:
  a 41-year-old male (age ~0.55, slightly above-average weight, height 1.72 m), MakeHuman system
  skin (light, middle-aged), eyes, eyebrows, eyelashes, short hair (system asset, restyled),
  **only the head, neck and hands kept** (everything under the clothes deleted). The builder fits
  this to the UAL armature (UBC "Regular" male, if in the free Standard tier, as the weight
  donor: Data Transfer of vertex weights), models the suit over it and skins it to the same
  armature, so the UAL clips play **without retargeting**.
- **Fallback A**: Universal Base Characters "Regular" male used as the body itself (stylised face
  softened in texture), plus the modelled suit — same rig, least work.
- **Fallback B**: MPFB2 full character with its "game engine" rig and UAL clips retargeted onto it
  in Blender (bone map + baked actions).
- **Clips in the GLB** (in-place, 30 fps, names exact): **`Idle`** (loop 4–8 s, breathing + weight
  shift, no foot sliding), **`Talk`** (loop 3–6 s: small hand gesture, head nods; if UAL has
  none, the builder keys one on the same rig), **`Walk`** (optional, for future route NPCs).
  Asset-scout: confirm which clips the free Standard/Pro zips contain and record exact names.

**Budget**
- **≤ 15k triangles** (target ~12k: head+neck 3.0k, hair+moustache 0.8k, hands 2.0k, jacket 3.5k,
  waistcoat/shirt/collar/tie 1.2k, trousers 1.8k, shoes 1.0k, tape/chain/pencil 0.3k).
- **One skinned mesh, one material** (MeshStandard: metallic 0, roughness 0.8 overall; hair/shoe
  sheen via the texture, not extra materials), **one 2048² colour atlas with baked AO multiplied
  in** (face/head ≈ 30% of the atlas so the face holds up at 1 m in VR; hands 10%; suit 35%;
  shirt, tie, shoes, hair, tape 25%). JPEG q85. No normal map, no alpha (moustache and eyebrows
  are painted/solid geometry, hair is solid card-free geometry). Skeleton ≤ 65 bones (drop
  finger-tip/face bones the clips don't use).
- **GLB ≤ 3 MB** (atlas ~0.8 MB + mesh/skin ~0.7 MB + clips ~0.5 MB); no Draco (skinned).
- **Draw calls**: +1 (body) +1 (blob shadow, a 0.9 × 0.6 m plane with a shared 128² radial alpha
  gradient, multiply-dark, `depthWrite: false`) while idle; +1 panel and +1 controller ray only
  while a conversation is open. Start view 164 → **166**; if that is judged too many, drop the
  blob shadow first.
- Textures for asset-scout (types; Poly Haven CC0 or MakeHuman CC0, 1K each, baked into the one
  atlas by the builder, then not shipped separately): **fine dark grey worsted wool / herringbone
  suiting** (tile ~0.10 m), **white cotton shirting** (tile ~0.05 m), **smooth black leather**
  (tile ~0.15 m), **MakeHuman middle-aged light male skin** (system asset). Source files stay in
  `assets/textures/source/` (or the builder's scratch), not loaded by the scene.
- Files: `tools/blender/npc_pickell.py` (build), `tools/blender/npc_pickell_bake.py` (AO bake,
  atlas, export), `assets/models/source/npc_pickell.blend`, **`assets/models/npc-pickell.glb`**,
  previews `assets/models/previews/npc-pickell-{front,three-quarter,face,talk}.png`.

**Weathering**: slight dust on the shoe tops and trouser turn-ups; faint sheen/wear on the jacket
elbows and cuff edges; shirt cuffs a touch ivory; tape measure soft and slightly frayed at the
ends; skin with natural variation (no plastic look); no grime on the face or hands.

**Dialogue** (write to `data/dialogue/pickell.json`; he speaks first; replies numbered 1–3;
every node is ≤ ~300 characters so the panel never scrolls)

| Node | He says | Replies → next |
|------|---------|----------------|
| `start` | "Good afternoon! John Pickell, of the Nevius store. Step in out of the sun, if you like — the door's open. Is there something I can show you?" | 1 "What do you sell here?" → `goods` · 2 "Have you worked here long?" → `owner` · 3 "What's that big building across the street?" → `town` |
| `again` (used when he has already been talked to this visit) | "Back again? Always glad to see a customer. What can I do for you?" | same as `start` |
| `goods` | "Dry goods and notions, as the awning says. Dress goods by the yard — gingham, percale, serge, silk — thread, buttons, ribbon, hosiery, and ladies' coats. Mind you, everything costs near twice what it did before the war." | 1 "Twice as much? Why?" → `prices` · 2 "Who owns the store?" → `owner` · 3 "Thank you. Good day." → `bye` |
| `prices` | "The war, mostly. Wool and cotton went sky-high, and they haven't come down yet. The papers say prices may break before winter. I'll believe it when the mills' bills say so." | 1 "What other news is there in town?" → `news` · 2 "What's across the street?" → `town` · 3 "Good day." → `bye` |
| `owner` | "Mr. Jacob Nevius. He opened his first store here in Flemington in 1878, and he has the store over in Somerville too. I came to work for him in 1895, a boy of sixteen, rolling bolts of cloth. Twenty-five years this year." | 1 "Tell me about the building." → `building` · 2 "What do you sell?" → `goods` · 3 "Good day." → `bye` |
| `building` | "There's been a store on this lot since before the Civil War. Mr. Fulper had it before us; they say he gave it this brick front about 1880. Go up to the third floor and you'll find my name pencilled on the wall — January 1896. Boys will be boys." | 1 "And the big building across the street?" → `town` · 2 "What's the news in town?" → `news` · 3 "Good day." → `bye` |
| `town` | "That's the Court House, built in 1828. The county jail is on the ground floor, under the courtroom. The county offices stand just beyond it. And next door to us is the Union Hotel — on court days it's full of lawyers and jurymen." | 1 "Is the hotel bar busy?" → `dry` · 2 "What else is worth seeing?" → `sights` · 3 "Good day." → `bye` |
| `dry` | "Not as it was. The whole country went dry in January — it's in the Constitution now. But more folks come through by motor car than ever; of a Saturday evening the cars are lined up along the curb out front." | 1 "Any other news?" → `news` · 2 "What else is worth seeing?" → `sights` · 3 "Good day." → `bye` |
| `sights` | "Come back for the Fair at the end of summer — it's been held out at the fairgrounds since 1856: trotting races, and automobile races these last few years. And there's Fulper's pottery; they've made pottery in Flemington for over a hundred years." | 1 "What's the news in town?" → `news` · 2 "Thank you. Good day." → `bye` |
| `news` | "Why, the ladies have the vote! New Jersey ratified the amendment back in February, and now it's the law of the land. Come November every woman in Hunterdon County can vote for President — Harding or Cox." | 1 "Thank you, Mr. Pickell. Good day." → `bye` · 2 "What's across the street?" → `town` |
| `bye` | "Good day to you. And mind the motor cars at the Court Street corner — some of these fellows drive faster than any horse." | 1 "[Walk on]" → close |

Fact sources per node: `goods` — 1907 awning "Dry Goods · Nevius Bros · Notions", 1917 ad "dress
materials", 1901 ad ladies' jackets (78main), CPI ~double 1914→1920 (FRED); `prices` — CPI peak
mid-1920 then fall (FRED); `owner` — 78main (Jacob Nevius, 1878, Somerville; Pickell 1895 at 16);
`building` — Goodspeed (store before 1856, Fulper's 1880 alterations), 78main (signature Jan 1896);
`town` — Goodspeed/Preservation NJ (1828, jail on the ground floor until 1925), the scene's own
county offices; `dry` — 18th Amendment (17 Jan 1920), 1920s cards (cars at the hotel curb);
`sights` — Flemington Speedway article (fairgrounds 1856, auto racing from 1915), Ellarslie
(pottery since 1814); `news` — 19th Amendment article (NJ 9 Feb 1920; election 2 Nov 1920);
`bye` — Court St corner is at z 0, 8 m south of him. Guessed colour: see "Pure guesses".

**Integrator design notes**
- **Scripts**: add after A-Frame 1.6.0:
  `<script src="https://cdn.jsdelivr.net/npm/aframe-extras@7.7.0/dist/aframe-extras.loaders.min.js"></script>`
  (pinned; 2026-04-01; contains `animation-mixer`). New `js/people.js` with the components below.
- **Data**: `data/dialogue/pickell.json`:
  `{ "id": "pickell", "name": "Mr. John B. Pickell", "role": "Clerk, Nevius store (Dry Goods), 78 Main St",
  "start": "start", "returnStart": "again", "nodes": { "<id>": { "text": "…", "replies": [ { "text": "…",
  "next": "<id>|null" } ] } }, "sources": { "<node id>": ["url", …] }, "brief": "…" }`.
  `next: null` closes the panel. More people = more JSON files + one entity each.
- **Entity**: `<a-entity id="npc-pickell" position="9.5 0.15 -8.45" rotation="0 -60 0"
  gltf-model="url(assets/models/npc-pickell.glb)" animation-mixer="clip: Idle; crossFadeDuration: 0.4"
  npc="dialogue: data/dialogue/pickell.json; radius: 2.5; closeRadius: 4"></a-entity>` + its
  blob-shadow plane at y 0.152.
- **`npc` component**: each tick (throttled to ~10 Hz) measures the horizontal camera distance.
  ≤ 2.5 m → open the panel at node `start` (`again` if already talked to this session), switch the
  mixer to `Talk` while he is "speaking" (first ~3 s after each new line), then back to `Idle`;
  yaw toward the visitor (decision 5). > 4 m (hysteresis) or `next: null` → close, return to
  −60°, `Idle`. Pickell's material: if he reads brighter or darker than the baked shop front,
  scale the material colour (one number in the component), don't add lights.
- **Dialogue panel**: one plane **0.80 × 0.50 m**, canvas 1024 × 640, warm paper colour
  (#F3EAD6, 92% opaque, dark brown text #2B2118, serif `Georgia, "Times New Roman", serif`),
  header "Mr. Pickell — Nevius Store", body text ~38 px, replies as numbered boxes ~34 px
  (highlight on hover). Placed **1.1 m from the visitor's head along the line to Pickell, shifted
  0.35 m to the side** so his face stays visible, at **head height − 0.45 m** (chest height),
  yawed to face the visitor, tilted back ~10°; re-placed only when the visitor moves > 1 m.
  `transparent: true`, `depthTest` on, `fog: false`, `shader: flat`.
- **Picking**: reply hit-testing from the ray's **UV on the canvas plane** (one mesh, class
  `dialogue-hit`).
  - **VR**: a new `#right-laser` entity with `laser-controls="hand: right"` and
    `raycaster="objects: .dialogue-hit; far: 4; enabled: false; lineColor: #f3e3c0"`, enabled and
    visible only while a panel is open; **right trigger** chooses (the left trigger is the sprint
    button — don't use it). Check it doesn't double-fire the existing `#right-hand` snap-turn.
    Optional: right thumbstick up/down + A button as an alternative.
  - **Desktop**: on open call `document.exitPointerLock()` and enable `cursor="rayOrigin: mouse"`
    so the mouse can click a reply; **keys 1–3** also choose. On close the visitor clicks the
    scene to look around again (pointer lock).
- **AI hook (future, not now)**: the panel asks a *provider* for the next line:
  `scriptedProvider(nodeId, replyIndex)` reads the JSON. A later `aiProvider(history, brief)` would
  POST to a small server (e.g. a Cloudflare Worker holding the Claude API key) with the JSON's
  `"brief"` (who he is, the sourced facts above, "say you don't know rather than invent") and
  return text + 2–3 suggested replies. Enable per person with `npc="… ; ai: true"` and a 4th
  reply "Ask something else…" (speech-to-text or picked prompts). Owner to decide on cost.
- Test: no console errors; panel readable on Quest 2 at arm's length; replies pick with the ray
  and the mouse; draw calls at the start view (expect 166) and with the panel open.

**Acceptance checks for the reviewer**
1. `assets/models/npc-pickell.glb` ≤ 3 MB, **one skinned mesh, one material, one texture
   (≤ 2048²)**, ≤ 15k triangles (report the count), clips **`Idle` and `Talk`** present and
   looping without pops; Idle has no foot sliding.
2. Standing in the GLB, **soles at y 0 (± 1 cm), height 1.70–1.75 m**, faces +Z.
3. Reads as a **man of about 40 with realistic proportions and face** (not a cartoon: normal-sized
   eyes, head ≈ 1/7.5 of height), **bareheaded**, side-parted short dark hair **grey at the
   temples**, clipped moustache.
4. **Dark charcoal three-piece suit**: 3-button sack jacket with notch lapels, waistcoat with a
   gold watch chain visible, **white turn-down collar and maroon tie**, trousers with crease and
   **turn-ups**, **black lace-up oxfords**; **tape measure round the neck**; no modern items.
5. Skinning: no candy-wrapper wrists or collapsing shoulders/elbows in Idle and Talk; suit does
   not intersect the body or hands.
6. In the scene at **(9.50, 0.15, −8.45)**, default yaw −60° (faces WSW toward the street and the
   start point), standing on the sidewalk in front of the north display window just north of the
   recessed door, not inside the step, window or awning; visible from the start view.
7. Walking up to him opens the panel at ≤ 2.5 m with his `start` line; walking away > 4 m closes
   it; he turns to face the visitor and back.
8. Panel text matches the Dialogue table **verbatim**, fits without clipping, sits at chest height
   facing the visitor; replies pick with the right-controller ray + trigger (VR) and the mouse /
   keys 1–3 (desktop); `[Walk on]` closes it.
9. Lighting: not noticeably brighter or darker than the Nevius shop front behind him, no black or
   flat-unlit look, no plastic shine; blob shadow grounds the feet.
10. Draw calls at the start view ≤ 166 (+2); +≤ 2 more with the panel open; no console errors.

**Open questions**
- Whether the free UAL tiers include a talking/gesture clip and which body models the free UBC
  Standard tier contains (asset-scout to confirm; fallbacks above).
- MPFB2 asset packs other than the system assets may be CC-BY: use only CC0 items, or log the
  attribution in SOURCES.md.
- Pickell's appearance is unknown; a portrait (e.g. in the 1945 *Whitehouse Review* or the
  Hunterdon County Democrat) could replace the generic face later.
- The Goodspeed article's "Nevius family took possession in the 1930s" conflicts with the other
  sources; if the owner finds the 1920 tenant was someone else, only the JSON and the name change.

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
| 2026-11-02 | Union Hotel made realistic: Poly Haven CC0 textures (brick, painted trim, weathered planks, slate, tin, concrete, wood), warm late-afternoon sun + sky baked with Cycles into a 2K lightmap (shadows, bounce, AO) with a grime mask, rendered unlit in A-Frame by the new `baked-lighting` component. `tools/blender/union_hotel_bake.py` → `assets/models/union-hotel.glb` (26.4k triangles, 8 × 1K textures). Fixed Quest thumbstick walking (oculus-touch-controls). |
| 2026-11-02 | From the 1920s photos: hotel doors rebuilt (white frame, fanlight with radiating bars, panelled grey-green double doors); street trees (`tools/blender/street_tree.py`, 464 triangles) in a row before the hotel and along the west side; pale paved macadam road and scored concrete sidewalks with stone curbs replace the dirt road and plank walks. Not yet committed. Photo-to-map reference page started (all 39 photos viewed), paused. |
| 2026-11-02 | Agent pipeline set up: `.claude/agents/` (planner, asset-scout, blender-builder, reviewer, scene-integrator), rules in CLAUDE.md, review viewer `tools/review/viewer.html`. |
| 2026-11-03 | planner (second pass): independent cross-check of the courthouse spec appended to its section (map and 1910 card re-measured; corrections to pediment windows, front chimney position; rear-chimney count questioned). Spec still awaiting approval. |
| 2026-11-02 | Planner: courthouse build spec written (Sanborn sheet 2 re-measured, 12 photos compared, NRHP/Preservation NJ/Goodspeed sources). New position (−18.34, y, −6.85). Awaiting user approval. |
| 2026-11-03 | scene-integrator: rebuilt street tree integrated (`assets/models/street-tree.glb`, 896 triangles: bark, root flare, soil pit with granite edging). 12 trees moved to x = ±7.5 (builder suggested ±7.3, but at the varied scales the 1.44 m pit then crossed the curb's inner edge at ±6.64), y = 0.175 so the soil isn't hidden by the 0.15 sidewalk, rotations 0/90/180/270 so the pits line up with the street. Tested: no console errors, all trees and the baked-lit hotel load; 87 draw calls / 37.6k triangles from the street. Committed with the hotel door rebuild, roads, sidewalks, curbs, tree assets and agent pipeline files. |
| 2026-11-03 | scene-integrator: Hunterdon County Court House GLB integrated (`assets/models/courthouse.glb`, 13,680 triangles, 12 materials, baked lightmap intensity 1.1979) at (−18.34, 0.15, −6.85): portico front 8.0 m behind the property line, steps reach x −16.69. The code-built placeholder and the lawn path at (−13.05, −7.05) were replaced by a paved concrete forecourt flush with the sidewalk (out to the Court St line), plus 15 cm grade slabs under the body, north wing and jail yard so no wall floats above the lawn. Curb trees at x −7.5 and the county offices placeholder (z ≤ −20.45) clear the model. Tested: no console errors, lightmap reads (no black faces; wing door and entablature fine). Start view (0, 0, 18) facing north: 160 draw calls / 53k triangles (was 149 / 39k); the ~150 call guideline is exceeded mainly by the code-built placeholders, which will drop as they are replaced by GLBs. |
| 2026-11-03 | planner: County Offices / Hall of Records (69–71 Main, 1870 Italianate) spec written and auto-approved (owner away). Sanborn sheet 2 re-measured: one brick building 13.9 × 15.2 m, 2 storeys, 28', front 7.4 m behind the property line → entity (−17.71, 0.02, −27.87). Eight period cards compared (1905–1912); HCHS walking tour confirms three doorways with own steps until the 1928 remodel. Ordinary building (≤ 10k tris); 1 new texture (pale buff sandstone). Next: asset-scout. |
| 2026-11-03 | scene-integrator: County Offices / Hall of Records GLB integrated (`assets/models/county-offices.glb`, 8,624 triangles, 10 materials, lightmap intensity 1.1299) at (−17.71, 0.02, −27.87), rotation 0 90 0; the kit placeholder at (−17.6, 0, −28.5) is gone. The single lawn path was replaced by three 1.6 m walks (sidewalk x −10.3 to just under the stoop feet at x −15.3); all five front paths are now one mesh via a new `ground-patches` component (js/components.js) to save draw calls. Fences, extra shade tree and telegraph pole skipped for the draw-call budget. Tested: no console errors (only the pane's pointer-lock errors), faces Main St, lightmap reads, stoops meet the walks, no floating. Draw calls / triangles before → after: start view (0, 0, 18) 160 / 53.0k → 162 / 61.5k; opposite sidewalk (8.5, −27.87) 79 / 47.9k → 82 / 56.3k; in front on the road (−2, −27.87) 46 / 16.5k → 50 / 25.0k. (The placeholder cost ~6 calls; the GLB costs 10, one per material.) Screenshot `assets/models/previews/county-offices-in-scene.png`. |
| 2026-11-03 | planner: Wurts Law Office (59 Main, c. 1811, Greek Revival remodel c. 1840) spec written and auto-approved (owner away). Sanborn sheet 2: 1-storey frame office, 8.0 m deep, portico front 4.7 m behind the property line → entity (−14.95, 0.02, −68.69). Width set to 4.70 m from the two HABS photos (map's 4.12 m would give a 1.7 m door). 1920 state: no rear T-wing (later addition per the HABS data form), flat roof, 4 square pillars, wreath frieze. No West Jersey History photo shows it. Target ~6k tris, 5 materials, no new textures. Next: asset-scout. |
| 2026-11-03 | blender-builder + reviewer: Wurts Law Office built and baked (`assets/models/wurts-law-office.glb`, 7,627 triangles, 5 materials, 1.2 MB, 1K lightmap, LIGHTMAP_SCALE 1.1647; asset-scout skipped, grey planks copy made by `tools/prepare_wurts_textures.py`). Review round 1: PASS. |
| 2026-11-03 | scene-integrator: Wurts Law Office GLB integrated at (−14.95, 0.02, −68.69), rotation 0 90 0; the kit placeholder at (−15.2, 0, −68.8) is gone; its front path narrowed to 1.2 m and re-centred on the portico (x −14.75 … −10.25). Optional shade tree skipped (draw-call budget). Tested: no console errors (only the pane's pointer-lock errors), faces Main St, lightmap reads on all 5 materials, step meets the path, nothing floats. Draw calls / triangles before → after: start view (0, 0, 18) 162 / 61.5k → 160 / 69.0k; opposite sidewalk (8.5, −68.69) 60 / 23.8k → 58 / 31.3k; in front on the road (−2, −68.69) 49 / 13.3k → 47 / 20.8k. (The placeholder cost ~7 calls; the GLB costs 5.) Screenshot `assets/models/previews/wurts-law-office-in-scene.png`. |
| 2026-11-03 | planner: Bank Building / Flemington National Bank (56–66 Main, 1897, SE corner of Bloomfield Ave) spec written and auto-approved (owner away). Sanborn sheet 2: one L-shaped 3-storey brick block, 40', front 22.14 m, 20.3 m deep (56–58) / 11.05 m (62–66), front wall 1.95 m behind the property line → entity (12.24, 0.15, −66.24). 1906–08 cards: one continuous facade, 12 bays, rock-faced stone ground storey, arched 3rd-floor windows, roundels, modillion cornice on front and Bloomfield side, bank entrance + 4 shop fronts with stoops and striped awnings. The Post Office was across Bloomfield Ave (not this building). Ordinary (≤ 10k tris), 6 materials; 1 new Poly Haven texture (rock-faced ashlar) + 1 locally generated awning stripe. Next: asset-scout. |
| 2026-11-03 | asset-scout + blender-builder + reviewer: Bank Building built and baked (`assets/models/bank-building.glb`, 8,808 triangles, 6 materials, 1.79 MB, 2K lightmap, LIGHTMAP_SCALE 1.1241). Review round 1: FIXES (stone too pale, chimney too low); round 2: PASS. |
| 2026-11-03 | scene-integrator: Bank Building GLB integrated at (12.24, 0.15, −66.24), rotation 0 −90 0; the code-built placeholder at (10.6, 0, −66.2) is gone. The 1.98 m strip between the sidewalk and the front wall (x 10.30–12.28, z −77.31 … −55.17) is paved with one concrete box flush with the sidewalk top (`#bank-forecourt`, +1 draw call: the patch list is a flat plane in a different colour, so it couldn't be merged). Clear of 68 Main (z ≥ −54.45; the bank's south cornice return at z −54.37 is above 68's 7.5 m roof), Bloomfield Ave and 48–52 Main; walls skirt to y −0.05 so the north side meets the Bloomfield grade without a gap. Tested: no console errors (only the pane's pointer-lock errors), faces Main St, lightmap reads. Draw calls / triangles before → after: start view (0, 0, 18) 162 / 69.0k → 163 / 77.8k; in front on the road (0, −66) facing east 23 / 26.3k → 30 / 35.2k; west sidewalk (−8, −66) facing east 34 / 27.5k → 39 / 37.3k. Screenshot `assets/models/previews/bank-building-in-scene.png`. |
| 2026-11-03 | planner: Nevius Store / Fulper's Dry Goods (78 Main, 3-storey brick Italianate store, front c. 1880) spec written and auto-approved (owner away). Sanborn sheet 3: "Dry Goods", 3 storeys, 35', 8.00 × 32.25 m, front on the property line → entity (10.30, 0.15, −7.33) (placeholder was at z −9.1 and only 17 m deep); 4.6 m gap to the Union Hotel, 4.8 m alley to 82 Main. Primary photo: 1909 "Nevius Store and Union Hotel" card; HABS 1963 hotel views show its corner and north wall. Goodspeed Histories / Pickell description used for windows (segmental 2nd floor with stone keystone arches, round 3rd floor with brick hoods), quoins and sill band. Ordinary (target ~5.5k tris), 5 materials, no new textures, 2K lightmap. Next: asset-scout (nothing to fetch). |
| 2026-11-03 | scene-integrator: Nevius Store / Fulper's Dry Goods GLB integrated (`assets/models/nevius-store.glb`, 6,954 triangles, 5 materials, lightmap intensity 1.1072) at (10.30, 0.15, −7.33), rotation 0 −90 0, front on the property line; the code-built placeholder at (10.3, 0, −9.1) is gone (id `bldg-78-main` kept). Walls skirt to y −0.05, so they meet the ground in the 4.6 m gap to the Union Hotel and the alley to 82 Main without floating; the awning (to x 8.39) clears tree-hotel-7 and the 82–84 placeholder (north edge z −0.1). Draw calls / triangles: start view (0, 0, 18) 163 / 77.8k → 164 / 84.7k; facing it from the road 30 / 27.6k → 31 / 34.5k; from the west sidewalk 58 / 42.1k → 59 / 49.0k. Screenshot `assets/models/previews/nevius-store-in-scene.png`. Note: the start view was already over the ~150 draw-call guideline before this building. |
| 2026-11-03 | planner: Frame Dwelling at 65 Main (old no. 510) spec written and auto-approved (owner away). Sanborn sheet 2: 2½-storey frame dwelling, L-plan (front block 8.60 × 9.72 m, rear ell 4.27 × 7.24 m on the north side), centred open front porch 4.0 × 2.0 m, 2-storey canted bay on the south side, open rear porch; front wall 5.81 m behind the property line → entity (−14.07, 0.02, −51.19) at the porch front. No photo shows the front; the 1908/1909/1912 county-building cards show its cream clapboard south wall and receding eave (front gable). No history found on the web; demolished before the HABS photos. Ordinary (target ~5.5k tris), **4 materials** (paint, dark, roof, brick; porch deck greyed by a bake tint), no downloads (one local recolour of brown_planks_05), 2K lightmap. Next: blender-builder. |
| 2026-11-03 | scene-integrator: Frame Dwelling at 65 Main GLB integrated (`assets/models/house-65-main.glb`, 6,343 triangles, 4 materials, lightmap intensity 1.274) at (−14.07, 0.02, −51.19), rotation 0 90 0; the kit placeholder is gone and the front path is now 1.3 m wide from the sidewalk to under the porch steps. No console errors; draw calls/triangles start view 164/84.7k → 159/90.9k, opposite the house 64/34.0k → 59/40.2k. |
| 2026-11-03 | planner: Test person 1 spec written and auto-approved (owner away), new section "## People": **John B. Pickell** (b. c. 1879), clerk of the Nevius dry-goods store at 78 Main since 1895 (Whitehouse Review 1945 via 78main.wordpress.com), standing at the shop door as the clerk in the 1907/1910s "business blocks" cards does (those cards show 78 Main looking south, awning "Dry Goods · Nevius Bros · Notions"). Entity (9.50, 0.15, −8.45), yaw −60°, 2.5 m trigger. Dark three-piece suit, bareheaded, tape measure. Base: Quaternius Universal Animation Library rig/clips (CC0) + MPFB2 (CC0) head/hands + modelled suit; ≤ 15k tris, 1 material, one 2K atlas with baked AO, scene-lit; 11-node branching dialogue with sources; aframe-extras 7.7.0 loaders. Next: asset-scout. |
| 2026-11-03 | planner: Lovell's Restaurant (68 Main, 2-storey frame restaurant with pool room upstairs; 1870 front with an arch in the roofline; Fred Lovell's restaurant c. 1910–1935+, today Higgins News Agency, refaced) spec written and auto-approved (owner away). Sanborn sheet 2: 18.39 m deep, front 2.36 m behind the property line; width 6.00 m (north wall put against the bank, photos show the fronts touching) → entity (12.66, 0.15, −52.13). Primary photos: Lovell's Restaurant (after 1910) and the c. 1900 "Oysters" front (Goodspeed Histories), 1908 colour card. Ordinary (target ~5k tris), **4 materials** (paint, dark, signs, stone), no downloads (1 generated sign atlas), 2K lightmap, hotel/bank occluder proxies for the bake. Next: blender-builder. |
| 2026-11-04 | scene-integrator: John B. Pickell placed at (9.50, 0.15, −8.45), rotation 0 −60 0, with Idle/Talk via aframe-extras 7.7.0 `animation-mixer`, blob shadow and a talking dialogue panel (`js/people.js`, `data/dialogue/pickell.json`, right-hand laser in VR, mouse/keys 1–3 on desktop). No console errors; panel opens at 2.5 m, closes past 4 m; all 11 nodes walked through. Draw calls / triangles: start view 159 / 90.9k → 161 / 103.7k; near him 102 → 103 with the panel open (+1 laser line in VR). Screenshots `assets/models/previews/npc-pickell-in-scene.png`, `npc-pickell-dialogue.png`. |
| 2026-11-04 | scene-integrator: Lovell's Restaurant (68 Main) GLB integrated (`assets/models/lovells-restaurant.glb`, 4,752 triangles, 4 materials, lightmap intensity 1.2462) at (12.66, 0.15, −52.13), rotation 0 −90 0, front wall 2.36 m behind the property line; the code-built placeholder at (10.6, 0, −51.7) is gone (id `bldg-68-main` kept). `#bank-forecourt` enlarged to x 10.30–12.66, z −77.31 … −49.13 (centre 11.48, −63.22; 2.36 × 28.18 m) so one box paves the strip in front of both the bank and 68 (runs 0.42 m under the bank's front wall, no gap; no extra draw call). The 3.5 m gap to the Union Hotel shows ground; the bank seam and cornice return show no z-fighting (68's side cornice dies into the bank's south wall). Tested: no console errors, faces Main St, lightmap and signs read, Mr. Pickell's panel still opens beside him. Draw calls / triangles before → after: start view (0, 0.15, 18) 161 / 103.7k → 161 / 108.4k; in front on the road (2, −52.13) facing east 40 / 43.8k → 40 / 48.5k; west sidewalk (−8, −52.13) 55 / 48.4k → 55 / 53.1k (the placeholder's calls are replaced by the GLB's 4 materials). Screenshot `assets/models/previews/lovells-restaurant-in-scene.png`. |
| 2026-11-04 | scene-integrator: draw-call pass. `baked-lighting` merges each of the 8 baked buildings into one draw call (texture array + per-vertex layer/tint; all 8 merged, none skipped: courthouse 12 materials, Union Hotel 11, county offices 10, bank 6, Wurts 5, Nevius 5, 65 Main 4, Lovell's 4); street trees drawn with `instanced-trees` (one GLB load, 4 instanced calls). Start view 161 → 69 draw calls, same triangles (108.4k); (0, −60) south 156 → 74. Before/after screenshots `assets/models/previews/perf-before-*.png` / `perf-after-*.png` match pixel for pixel apart from edge pixels and Mr. Pickell's animation; his dialogue still opens. No console errors. |
| 2026-11-04 | planner: Street ambiance pass 1 (sound + street props) spec written and auto-approved (owner away), new section "## Street ambiance". From 14 period cards + the 1921 Sanborn: one kit GLB `street-props.glb` (12 named nodes, one material, one 2K atlas, ~4.7k unique tris): wooden utility poles with two crossarms (1906/1907 cards), pole bracket lamps, 2 span-wire arc lamps (1910 card), the granite horse/drinking fountain with globe lamp at the west curb in front of the County Offices (fountain photo, hotel cards, Albertype "Clerk's Office / Dentist" caption), granite hitching posts and carriage steps, 2 hydrants at the Sanborn "T.H." spots, shop goods, 2 sandwich boards, 2 leaning bicycles, a curb gasoline pump (Sanborn sheet 3 buried tank at 100–102 Main). 34 placements, wires as one LineSegments, target +4 draw calls. Sound: CC0/PD only (BigSoundBank, Commons G. McGrane birds, Freesound craigsmith CC0 previews; ~2.3 MB): bed, walla, American birds, unseen wagon and Model T passes, bell striking five, Nevius shop bell, optional distant train whistle; starts on first gesture, M mutes. Next: asset-scout. |
| 2026-11-04 | asset-scout: Street ambiance pass 1 assets ready. Textures (`assets/textures/street-props/`, Poly Haven CC0, 1K): `old_planks_02` (poles, crossarms, crates, boards), `rust_coarse_01` (iron), `rock_boulder_dry` greyed → `granite_rough_grey` (fountain monolith; `granite_wall` rejected for its block joints), seamless joint-free `granite_dressed_light` from `granite_tile_03` (bowl, posts, steps), `iron_paint_redbrown` from `metal_plate_02` (hydrant); reused `metal_plate_02`, `wood_table_worn`. Audio (`assets/audio/`): 16 mono OGG clips, 1.96 MB, 250 s total, ~−20 LUFS, loops crossfaded (BigSoundBank CC0, Commons G. McGrane PD birds, Freesound craigsmith CC0 previews with a rights note in SOURCES.md). Bed = BigSoundBank #0659 "Wind in a Tree" instead of #1911 (loud crickets, dense European birdsong). Converted with ffmpeg from the `imageio-ffmpeg` pip package (no ffmpeg on the PC). Next: blender-builder. |
| 2026-11-04 | scene-integrator: Street ambiance pass 1, **sound part** integrated (props and wires come later). New `js/ambience.js`, `street-ambience` on `<a-scene>`: clips fetched after the scene loads, AudioContext + one `THREE.AudioListener` created at the first click/key/touch/Enter VR (no autoplay warning), listener on the active THREE camera (follows the headset in VR; XR select/squeeze also resume the context), buffers decoded once and reused, max 6 voices. Bed 0.35 (3 s fade-in, non-positional); walla hotel (10.5, 1.6, −30.75) 0.30 ref 5/max 45/rolloff 1.2 and courthouse (−15.5, 1.6, −6.85) 0.20 ref 4/max 35, 20 s offset; birds from the 12 street-tree crowns (+6.5 m), 8–25 s, never the same clip twice; horse/wagon passes every 70–150 s at 2 m/s on routes R1–R4 (the clip's 50–60 m centred on the point nearest the visitor; 2 s fades; 30 % neigh/snort); Model T every 3–6 min at 6 m/s along a whole route (40 % oogah horn, 1 in 4 ends with modelt-stop); bell at 75 s then every 6 min from (30, 30, 260); shop bell every 40–120 s only within 20 m of the Nevius door; train whistle at 0.8× every 8–14 min from (−500, 20, 150). Timers run on the scene clock and the context is suspended while the tab is hidden; M mutes (help text updated). Tested in the preview: silent and no AudioContext before the click, context `running` after, 16/16 decoded, loops at the spec gains, every source at its spec position/ref/max/rolloff, horse source moving at 2.0 m/s with the panner following, car horn + stop ending, shop bell skipped at 26 m and played at 5 m, M ramps the master gain 1 → 0 → 1; no console errors. Draw calls/triangles unchanged (start view 69 / 108.4k); tick ≈ 0.4 µs. Not yet heard in the headset. |
| 2026-11-04 | blender-builder: street props kit built. `assets/models/street-props.glb` (823,692 bytes): 12 nodes at the origin (pole 650 tris, pole_lamp 222, arc_lamp 314, fountain 1,471, hitching_post 78, carriage_step 20, hydrant 289, shop_goods 294, sandwich_board_groceries 36, sandwich_board_icecream 36, bicycle 612, gas_pump 572 = 4,594), one material (roughness 0.9, metalness 0, no alpha), one 2048² atlas `assets/textures/street-props-atlas.jpg` (605 KB; colour maps box-projected in metres × Cycles AO 0.5 m, no sun bake; serif-capital lettering). Crossarms along glTF Z, insulators at glTF Z ±0.40/±0.75/±1.05, x +0.148 (upper arm, top y 10.355) and +0.151 (lower, top y 9.655); eye bolt at (0, 8.6, +0.18). Scripts `tools/blender/street_props.py`, `street_props_bake.py`, `street_props_preview.py`; .blend `assets/models/source/street-props.blend`; previews `street-props-lineup/three-quarter/match-fountain/fountain/pole-top/pole-lamp/hydrant/gas-pump/gas-pump-right/goods-boards-bicycle.png`. Next: reviewer. |
| 2026-11-04 | blender-builder: street props round-1 fixes. (1) Fountain horse head remodelled as a side-view silhouette facing the viewer's left (two upright ears, long face to a rounded muzzle at the lower left, chin, jaw and round cheek, throat, neck curving down into the oval, mane crest), 3.5 cm proud of the oval, plus raised mane locks, cheek line, nostril and eye (~7 mm); oval, spout plate, bowl, niche and holder unchanged. (2) Pump globe: the word is mapped on the front half and again on the back half of the band and now fills only the middle of each half, so the joins at the sides fall in blank red band; globe 12 → 16 sides. Tris: fountain 1,471 → 1,587, gas_pump 572 → 616, total 4,594 → 4,754; GLB 833,384 bytes; atlas 608 KB. New previews `street-props-horse-head.png`, `street-props-gas-globe.png`; all others re-rendered. Next: reviewer round 2. |
| 2026-11-04 | reviewer: street props kit round 1: **FIXES (2)**. GLB 0.82 MB loads in the viewer without errors (4,594 tris, 12 named nodes at the origin, one material `M_StreetProps`, one 2048² JPEG, opaque, POSITION/NORMAL/TEXCOORD_0); scale, pole/crossarm/eye-bolt orientation, bicycle lean, lettering on the boards all correct. Fix: (1) fountain horse-head relief doesn't read as a horse head (compare `flmngtndrinkingfountainbycrthous.jpg`); (2) pump globe "GASOLINE" band garbled at the UV seam. |
| 2026-11-04 | reviewer: street props kit round 2: **PASS**. Horse head now reads clearly (ears, muzzle, jaw, neck, eye, mane; matches `flmngtndrinkingfountainbycrthous.jpg`); "GASOLINE" clean front and back on a 16-sided globe. GLB 833,384 bytes reloads fresh in the viewer without errors: 4,754 tris, 12 nodes, 1 material, 1 2048² JPEG, opaque; other props unchanged (same bounds). Ready for scene-integrator. |
| 2026-11-04 | scene-integrator: Street ambiance pass 1, **street props** integrated: 15 wooden poles (7 with bracket lamps) along both curbs with sagging overhead wires, 2 arc lamps on span wires over the Court St and Bloomfield crossings, the horse fountain before the County Offices, 4 hitching posts, 2 carriage steps, 2 hydrants, 3 shop-goods groups, 2 sandwich boards, 2 bicycles, the curb gas pump (34 placements, 17.2k triangles). New `street-props` component in `js/components.js` (reuses `mergeGeometries` from `js/kit.js`): 3 merged z-band meshes + 1 wire mesh = +4 draw calls at the start view (69 → 73), +3 further north (one band culled). Fountain moved 0.25 m back from the road, shop goods at 66 Main moved 3 m north off the stoop, bicycles turned to lean on their posts. |
| 2026-11-04 | voice: Mr. Pickell's 11 dialogue lines voiced offline with Piper TTS 1.8.0 (scratch venv), model `en_US-libritts-high` speaker 595 (LibriTTS CC BY 4.0, trained from scratch; `libritts_r` skipped as a fine-tune of the restrictively licensed lessac voice), length_scale 1.15. `assets/audio/voices/pickell/<node-id>.ogg` (5.4–18.4 s, 1.29 MB total, −18 LUFS) + `timings.json` (per-word times from Piper's phoneme alignment); script `tools/make_voice_pickell.py`; SOURCES.md has the attribution. Next: scene-integrator (play clips, word reveal, credits line). |
| 2026-11-04 | scene-integrator: Mr. Pickell **voiced in scene**: each line's clip plays from his head (shared Web Audio of `js/ambience.js`, M mutes it, walla/town bed −4 dB while he speaks), text revealed word by word from `timings.json` (0–20 ms off), replies after the line or on Space/click/trigger, Talk for the clip length, fade-out on reply/walking away, text-only fallback if a clip fails; CC BY 4.0 voice credit on the page. No jaw (model has no jaw bone or morphs). No extra draw calls. |
| 2026-11-04 | planner: Rea Building / "Clock Tower Building" (48–52 Main, 1874 Italianate brick block on the NE corner of Bloomfield Ave; Post Office from 1899 to before 1921; 1921 tenants Green's drugs, cobbler, jeweler/club rooms) spec written, **awaiting owner approval**. Sanborn sheet 2: 3 storeys, 36', main block 15.94 × 15.20 m + 3-storey "Flats" wing 7.87 × 8.91 m on Bloomfield Ave, front 0.55 m behind the property line → entity (10.85, 0.15, −97.79). Upper floors and roofline measured on a modern frontal photo (Goodspeed Histories): 7 bays 2–3–2, segmental arched pediment with oval window, bracketed cornice, square cupola with 4 clock dials; ground floor from the 1906–07 cards (raised shops, steps along the front, 3 round arches). Ordinary (target ~9k tris), 5 materials, no downloads (1 generated sign/clock atlas), 2K lightmap. |
| 2026-11-04 | blender-builder: Rea Building / Clock Tower Building (48–52 Main) **built** at landmark detail: `tools/blender/rea_building.py` + `_bake.py` + `_preview.py`, `tools/prepare_rea_textures.py` (sign/clock/louvre/dentil atlas). 14,593 tris after hidden-face removal, 5 materials, GLB 1.89 MB, 2K lightmap, LIGHTMAP_SCALE 1.1735. 7 bays 2–3–2 with hoods, keystones, louvred shutters; segmental pediments (front with oval window, Bloomfield side), 20 scroll brackets, dentil course; cupola with 4 clock gables and dials, pole to 18.7 m; shop fronts 48/52, rusticated arches, steps along the front, Green's and striped awnings; Flats wing. Previews: front, three-quarter, cupola, detail, match-flmngtnpoandnatbank08, match-flmngtnpobankunionhtl07. Next: reviewer. |
| 2026-11-04 | reviewer: Rea Building / Clock Tower Building (48–52 Main) round 1: **PASS**. GLB 1.89 MB, 14,593 tris (≤ 15k landmark cap), 5 materials, 4 × 1K JPEG + 2K lightmap, TEXCOORD_0/1; viewer loads with no errors. Matches the 1907/1908 cards and spec: 7 bays 2–3–2 with hoods, keystones and shutters, broken segmental pediment with oval window, paired brackets and dentils, cupola with 4 clock gables and pole to 18.7 m, rusticated arches (door, window, door), steps, Green's and striped awnings, Bloomfield side with side arch, chimney and Flats. Optional: warmer cream cupola; Flats door step projects 0.40 m onto Bloomfield Ave. |
| 2026-11-04 | scene-integrator: Rea Building / Clock Tower Building (48–52 Main) **in scene** at (10.85, 0.15, −97.79), rotation 0 −90 0, replacing the placeholder `#bldg-48-52-main` (id kept); `baked-lighting` intensity 1.1735, merged 5 materials → 1 call. Draw calls / triangles (looking north): start 73 → 70 / 125.7k → 140.3k; z −60: 56 → 53 / 39.1k → 53.7k; z −90: 41 → 38 / 7.2k → 21.8k (placeholder used 4 calls). Steps stand on the sidewalk to x 9.65, clear of pole E5 and hydrant Y2; no props or trees moved; `#bank-forecourt` unchanged; 2.0 m passage to the 40–46 placeholder; Flats door step (0.40 m onto Bloomfield Ave) looks fine. No console errors. Also added HISTORY-SOURCES.md (register of historical claims and sources). |
| 2026-11-04 | planner: County Hotel (47–49 Main, west side opposite the Rea Building; Italianate hotel, "County Hotel" under W. H. Force after the Civil War, Mount's Hotel from 1891, sold 1907, demolished 1970s for New Market) spec written, **awaiting owner approval**. Sanborn sheet 2: 3 storeys, 30', 23.86 × 9.07 m, full-width 2-storey veranda 2.52 m deep to the property line, front/south walls "(Ir. Cl.)", 1-storey Bar & Pool Room wing → entity (−10.30, 0.15, −112.07). No local photo shows it; four West Jersey History cards (1906–08) and the c. 1905 "Mount's Hotel" photo (Goodspeed/HCHS) viewed online: 8-bay veranda with X-panel posts and diamond-lattice railing, 12 shuttered 3rd-floor windows, bracketed cornice, lamp standard. Walls pale painted brick (1908) vs red brick (1905–06): owner to choose. Recommended 15k tris (landmark detail), 8 materials, no downloads (1 recolour + 1 sign atlas generated), 2K lightmap. |
| 2026-11-04 | blender-builder: County Hotel (47–49 Main) **built**: `tools/blender/county_hotel.py` + `_bake.py` + `_preview.py`, `tools/prepare_county_hotel_textures.py` (brick_painted_cream.jpg, signs_atlas.jpg). GLB 1.81 MB, 10,234 tris (≤ 15k cap), 8 materials, 2K lightmap, LIGHTMAP_SCALE 1.1087, west-side sun (−0.40, 0.90, 0.36), 39–41 bake occluder 7 m. Changes from spec: north-wall windows only on the 3rd floor (plain, unshuttered; the 2nd floor is hidden by the 7 m neighbour), rear 2nd floor 4 windows (moved clear of the wing roof), main-door transom to 2.92 (under the 3.00 deck ceiling), enclosure windows recessed 0.10. Next: reviewer. |
| 2026-11-04 | reviewer: County Hotel (47–49 Main) round 1 **PASS**: GLB loads cleanly (10,234 tris, 8 materials, UV2), proportions and veranda/cornice/shutter/lamp detail match the c. 1905 photo, lightmap clean (no blotches, seams or black spots). Builder deviations accepted. Next: owner, then scene-integrator. |
| 2026-11-04 | scene-integrator: County Hotel (47–49 Main) **in scene** at (−10.30, 0.15, −112.07), 1 draw call; 35–41 placeholder shortened to end at z −124.2; no props moved. Draw calls/tris (looking north): start 70/140k → 67/150k, z −90 38/22k → 35/32k, z −110 37/7k → 34/17k. |
| 2026-11-04 | planner: Block at 40–46 Main (two frame buildings north of the Rea Building: 40–42 3-storey "Auto Sales" with an arched drive-through, porch and canted show window; 44–46 2-storey "Shoe Shine & Fruits" on the street line with two 2nd-floor bays over a 3.3 m passage) spec written, **awaiting owner approval**. Sanborn sheet 2 (30' / 20', frame); no photo of the fronts and no written history found, so all façade details and colours are labelled guesses; entity (8.60, 0.15, −116.55), rotation 0 −90 0; ordinary (target ~7k tris), 6 reused maps + 1 generated atlas, no downloads. Owner to choose placement (a) map-true street line or (b) on the scene property line. |
| 2026-11-04 | blender-builder: Block at 40–46 Main **built**: `tools/blender/block_40_46.py` + `_bake.py` + `_preview.py`, `tools/prepare_block_40_46_textures.py` (signs_atlas.jpg). GLB 1.43 MB, 4,821 tris (≤ 10k), 8 materials, 2K lightmap, LIGHTMAP_SCALE 1.2152, east-side sun, bake occluders Rea + 36–38. Changes from spec: clap_a uses clapboard_cream × factor (the buff map cannot be lightened to #B9AE96 by a factor); 40–42 3rd-floor windows sill 6.85 / 1.40 tall and 44–46 2nd-floor sill 3.80 (to clear the friezes); 44–46 doors at X 2.40 / 6.70 (clear of the pilasters); apron top 0.01 (no z-fight with the sidewalk); flat roof decks on A and C2. Next: reviewer. |
| 2026-11-04 | reviewer: Block at 40–46 Main **PASS (round 1)**. GLB 1.43 MB, 4,821 tris, 8 materials, 1K maps + 1K atlas, 2K lightmap, TEXCOORD_0/1; loads in the viewer with no errors. Two buildings read clearly (3-storey buff / 2-storey cream, cornice tops 9.15 / 6.10, 44–46 1.98 m forward), arch, porch, show window, awning, passage bays all as spec; signs legible; lightmap clean. Note for integrator: A's open north wall below 6.10 is hidden by `#bldg-32-38-main` (7.5 m tall), so keep that placeholder's height when trimming it. |
| 2026-11-04 | scene-integrator: Block at 40–46 Main **in scene** at (8.60, 0.15, −116.55), 1 draw call; 32–38 placeholder trimmed to z −124.05; fruit stand goods-G4 added; draw calls / triangles start view 63 / 150.7k → 64 / 155.5k, at (0, 0.15, −110) 30 / 17.6k → 31 / 22.5k. |
| 2026-11-04 | asset-scout: Sky (D, option 1) **asset ready**: `assets/textures/sky/sky-late-afternoon.jpg` (2048 x 1024 equirect, 53 KB) from Poly Haven `hilly_terrain_01_puresky` (CC0, sky-only edit, nothing modern), made by `tools/prepare_sky.py` (exposure 1.9, wb 1.10,0.95,0.90, warm 2.5); horizon ~#ebe4cb, zenith ~#97b3c4; sun at u = 0.600, 12 deg up (lower than the 21 deg baked sun). |
| 2026-11-04 | scene-integrator: **Mini map built** (1921 Sanborn, style B): js/minimap.js + data/minimap.json + assets/maps/minimap-1921.jpg (tools/prepare_minimap.py). Desktop overlay (N), VR pop-up panel (Y, left controller). Checked at the start view and near the Bank Building: arrow position/turn and tags line up with the Sanborn buildings. VR panel 64 → 65 draw calls (+2 tris) at the start view; desktop overlay is HTML (0 calls). No console errors. |
| 2026-11-04 | scene-integrator: **Photographed sky in scene** (D, option 1): equirect sky on the `#sky` sphere, yaw 60 deg puts the sun WSW over the west side of the street (east fronts sunlit, as baked); fog #ecdfc4 -> #ebe4cb; still 1 draw call; start view 64 calls / 157.0k tris. No console errors. Previews sky-north-main-st.png, sky-wsw-sun-side.png. |
| 2026-11-04 | planner: **Distant landscape pass 1** spec written (new `## Background`). USGS 3DEP DEM (public domain) → `assets/maps/landscape-dem.png/.json` via `tools/prepare_landscape_dem.py`; horizon from Main St: west ridge 1.8–3.4 km at 2–2.6° (down Court St, NW of the street end), Cushetunk Mtn NNE ~1°, Sourland SE–S 0.3–0.5°, flat to the east. Plan: distance-compressed ring (330–800 m, angles exact) following the rig at 0.85, tree lines, town silhouettes; ≤ 10k tris, 3 calls; fog 0.011 → 0.005, ground → 335 m following disc, sky r 1200, camera near 0.05. |
| 2026-11-04 | blender-builder: **Distant landscape pass 1 built**: `landscape.glb` 0.77 MB, 8.3k tris, 3 unlit materials, nodes `landscape_far` (follows rig, fog off) + `landscape_town` (fixed, fog on); generated `tree_silhouettes.png` atlas. |
| 2026-11-04 | scene-integrator: **Distant landscape in scene**: `#landscape` (far ring follows the rig at 0.85, unlit, fog off; town fixed, fogged), ground → 335 m following disc, fog 0.011 → 0.005, sky r 400 → 1200, camera near 0.05; start view 73 → 76 calls. |
| 2026-11-08 | planner: **Palace Theatre (31 Main, old no. 518)** spec written, **awaiting owner approval**. Confirmed on the Sept 1921 Sanborn (2-storey 26' brick front block 12.60 × 22.82 m with entrance hall + vacant store; 1-storey + basement hollow-tile auditorium and stage, 62.78 m deep overall); trade press names it from Nov–Dec 1922; opening date not found, so "c. 1920" is unproven (the Flemington Opera House on Bloomfield Ave was the picture house in 1916). Façade from the undated "Palace Theatre & Potter Building" card (Cinema Treasures, view only): 4 paired windows, stepped gable parapet, belt course, 3 globe lamps, no marquee. Entity (−10.30, 0.15, −145.52), rotation 0 90 0; ordinary (target ~5k tris), no downloads, 1 generated sign atlas. Colours and auditorium height are guesses. |
| 2026-11-08 | orchestrator: **Palace Theatre spec approved by owner** (c. 1920, blank parapet panel). blender-builder **stopped before building**: PC memory commit 59 of 61 GB (about 42 GB unexplained, running since Nov 2), only 2.18 GB headroom after clearing Blender (3 GB required). Build, landscape polish and voice sample wait for a Windows restart. |
| 2026-11-08 | planner: **Odd Fellows Hall / Hopewell Building (82–84 Main)** spec written, **awaiting owner approval**. One 3-storey building with two shops ("Jeweler", "Gro."): frame front 10.65 m + brick rear 10.6 m, 15.53 m wide, 35' (Sept 1921 Sanborn), built c. 1881–82 by John C. Hopewell (Goodspeed). Front from the 1907 and 1910s "Some Business Blocks" cards: 7 windows per upper floor, arched crest, two shop fronts. Tenant names not found; signboards unreadable, so blank; colours are guesses. Placement z 9.09, not the placeholder's 7.7. |
| 2026-11-08 | planner: **Block at 35–41 Main** spec written, **awaiting owner approval**. Two buildings on the Sept 1921 Sanborn: 35–37 (old 517) 3-storey frame "Gro.", 28', 6.40 m wide, two-tier porch (4 columns, 1906 and 1920s cards); 39–41 (old 516) 2-storey brick "Cobbler", 28', set back 2.8 m, **no photo of its front**, kept plain. Tenant names not found; "Potter Building" not tied to this block. Placement (−11.12, 0.15, −129.89), not the placeholder's x −10.3. |
| 2026-11-08 | planner: **Block at 32–38 Main** spec written, **awaiting owner approval**. Sept 1921 Sanborn: a row of three 2-storey frame shops, "Mill'y", "Bakery", "Meats" (old nos. 557–554), 13.41 m frontage behind one open 1-storey porch; south end of Meats only 1 storey, so the spec adds a patch for the deleted 40–42 north wall. **No photo shows the fronts**; front kept plain, no signs; tenant names not found. Placement (8.54, 0.15, −130.755): z as the placeholder, porch 1.63 m in front of its wall. |
| 2026-11-08 | planner: **Dry goods and clothing store (27 Main, old 519 A/B)** spec written, **awaiting owner approval**. Sept 1921 Sanborn: one 2-storey brick store, "D.G. & Clo.", 25', 12.35 m wide, 24.16 m deep, with a south light court and frame rear parts. Front from the "Palace Theatre & Potter Building" card (no other view found): 4 tall windows, pale bands, deep plain cornice, one long plain awning, one globe lamp; **ground floor hidden, kept plain**; no signs. Tenant name not found; "Potter Building" = no. 27 still unproven. Placement (−10.30, 0.15, −158.49), 1.0 m south of the placeholder; closes the Palace gap to the map's 0.49 m slit. |
| 2026-11-10 | planner: **Specs for 27 Main, 32–38 Main and 35–41 Main re-checked** against the owner's newly saved local photos (`flmngtnmainstrtcountyhtlvu06.jpg`, `flmngtnmainstnorth13.jpg`, `flmingtnmainstrtview.jpg`, `palace-theatre-potter-building-card.jpg`); all three stay **awaiting owner approval**. 35–41: 1906 card (camera fit) confirms 35–37 and its 4 evenly spaced columns; adds an open stair in the porch's south bay (1906 only, **not modelled by default, owner to choose**) and unreadable lettering on the 1906 fascia and 1920s valance (kept plain); 39–41 front still hidden. 27: card re-checked, no change; no other photo shows it. 32–38: still no usable photo; the 1906 card's east-side edge shows a 3-storey bay-windowed building that does not match the 1921 row (not used). The three 404 files are probably spelt "flmngntn…" (extra n). |
| 2026-11-10 | blender-builder: **Palace Theatre (31 Main) built, baked and exported** (`assets/models/palace-theatre.glb`, 2,688 tris, 8 materials, 1.58 MB, 2K lightmap, LIGHTMAP_SCALE 0.9901). Brick front with 4 paired windows, dark hoods, keystones, belt, stepped gable with a **blank** panel, shop window, shop door, dark lobby with 2 generic posters (no lettering), 3 globe lamps; auditorium and stage plain. Brick tiled at 1.4 m instead of the spec's 2.0 m (true course size). Previews front, three-quarter, detail, match-potter-card, alley. Awaiting review. |
| 2026-11-10 | orchestrator: **Odd Fellows Hall / Hopewell Building (82–84 Main) approved by owner** with two blank pale signboards. Build after the Palace Theatre leaves Blender. |
| 2026-11-10 | planner: **35–41 Main spec revised** from two new local-only photos (HCHS Stryker plate c. 1906–10; c. 1905 County Hotel photo), still **awaiting owner approval**. 35–37: 4 round Tuscan columns per tier, turned-baluster deck rail, spindle frieze with drop fringe, raised floor with two steps, bracketed eave, open louvred shutters, ground floor = shuttered window + door + shop window; stair runs front-to-back in the south bay (3 photos). 39–41 (c. 1905, seen through the hotel's open north bay): balcony 0.44 m deep (= the map's dashed line), tall shuttered windows, basement door down an areaway. **Owner decisions**: awning lettering "PRODUCE \| JACOB R. HALL \| GROCER" (recommend plain: Hall not confirmed for 1920, 1920s valance laid out differently) and the stair (recommend model it). 32–38: Stryker camera fit puts its lots probably in frame, but the bay-windowed/towered fronts there do not match the 1921 map; model unchanged; one note added to 40–46. |
| 2026-11-10 | orchestrator: **Block at 35–41 Main approved by owner**: valance lettered "PRODUCE \| JACOB R. HALL \| GROCER" until contrary evidence (Decision 3b), porch stair modelled (B2). |
| 2026-11-10 | reviewer: **Palace Theatre round 1 PASS**. GLB 1.58 MB, 2,688 tris, 1 mesh, 8 materials, 7 JPEG maps all 1024², TEXCOORD_0 + 1, lightmap 2048². Bounds fit the spec (front 12.6 m, auditorium/stage to +7.4 north, depth 62.8 m + rear fascia). Previews match the card: 4 paired windows, hoods + keystones, belt, stepped gable with blank panel, shop window / door / entrance, 3 globes, no marquee, plain south wall with one downpipe. Note: north wall of the front bakes black; it must be hidden by no. 27 (extend `bldg-27-main` or place the 27 Main model). |
| 2026-11-10 | orchestrator: owner wants the Palace Theatre poster frames **plain and empty** (realism). Blender follow-up after 82–84: blank the 2 posters in signs_atlas, re-export palace-theatre.glb (no rebake needed if UVs unchanged). Owner also wants all windows to stop reading as flat black (see Later phases). |
| 2026-11-10 | scene-integrator: **Palace Theatre (31 Main) in the scene**: `#palace-theatre` = gltf-model `assets/models/palace-theatre.glb` + baked-lighting intensity 0.9901 at (−10.30, 0.15, −145.52), rotation 0 90 0 (sidewalk level, like the Nevius Store and County Hotel; walls skirt to −0.20). The old box placeholder (z −145.7) is gone. `bldg-27-main` placeholder moved/resized to (−10.3, 0, −158.45), width 12.5 (z −164.7 … −152.2): 0.38 m clear of the Palace front block (z −151.82), covers its black-baked north wall; the auditorium (to z −153.07) starts behind the placeholder's 20 m depth (x −33.1 vs −30.3), so no overlap. 3.6 m alley to the 35–41 placeholder (z −135.6). Pole W6 (x −6.9, z −150) is on the curb, clear. Minimap entry added. GLB 1.58 MB, 2,688 tris, 8 materials = +8 draw calls (replaces 1 box). Checked by GLB parse and code reading only (no browser, per orchestrator). Posters still to be blanked. |
