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
