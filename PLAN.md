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

## Pipeline status

| Building | Spec | Assets | Built | Review | In scene |
|----------|------|--------|-------|--------|----------|
| Union Hotel (70–76 Main) | done before pipeline | done | done | — | yes |
| Hunterdon County Courthouse (75 Main) | approved | done | done, round-1 fixes applied (13.7k tris, 2.6 MB) | round 2: PASS | yes (GLB, 2026-11-03) |
| County Offices / Hall of Records (69–71 Main) | written, auto-approved (owner away) | done (1 new + 3 tinted, 3 reused) | done (8.6k tris, 2.2 MB, LIGHTMAP_SCALE 1.1299) | round 1: PASS | yes (GLB, 2026-11-03) |
| Wurts Law Office (59 Main) | written, auto-approved (owner away) | reused, none new (asset-scout skipped; 1 grey copy of weathered_planks made locally) | done (7.6k tris, 5 materials, 1.2 MB, 1K lightmap, LIGHTMAP_SCALE 1.1647) | round 1: PASS | yes (GLB, 2026-11-03) |
| Bank Building / Flemington National Bank (56–66 Main) | written, auto-approved (owner away) | done (1 new: sandstone_blocks_05 greyed → stone_rockfaced; 1 generated: awning_stripes; 3 reused) | done, round-1 fixes applied (8.8k tris, 6 materials, 1.8 MB, 2K lightmap, LIGHTMAP_SCALE 1.1241) | round 2: PASS | yes (GLB at 12.24, 0.15, −66.24) |
| Nevius Store / Fulper's Dry Goods (78 Main) | written, auto-approved (owner away) | reused, none new (asset-scout skipped; 4 reused maps) | done, round-1 fixes applied (7.0k tris, 5 materials, 1.3 MB, 2K lightmap, LIGHTMAP_SCALE 1.1072) | round 2: PASS (round 1: 3rd-floor windows raised; LIGHTMAP_SCALE now 1.1072) | **yes** (10.30, 0.15, −7.33) |

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
