# Sanborn 1910 / 1921 / 1948 comparison and today's street: Main St 24–106

Research only (planner, 2026-11-10). Nothing here changes PLAN.md; it lists what is new and
flags conflicts. Pixel coordinates are full-resolution sheet pixels. "1921" = the Sept 1921 sheets
already in `assets/maps/`. Scene formulas from CLAUDE.md apply to the 1921 sheets only.

## Part 1: which Sanborn editions exist

The Library of Congress has **no 1913 and no 1927 edition** of Flemington. Its editions are
1885, 1890, 1896, 1902, **Nov 1910**, **Sept 1921** and **Sept 1948** (the 1948 set is the 1921 plates
with paste-over corrections up to 1948, so it shows what changed after 1921 but not when).
LoC search: https://www.loc.gov/collections/sanborn-maps/?q=flemington

| Edition | LoC item | Main St sheets used | Kept where |
|---|---|---|---|
| Nov 1910 | https://www.loc.gov/item/sanborn05479_005/ | sheet 4 (east side, Penn Ave → Union/Higgins Ave), sheet 5 (west side, Capner St → Court St) | **copied to `assets/maps/flemington-1910-sanborn-sheet-04.jpg` and `-05.jpg`**, logged in SOURCES.md (public domain) |
| Sept 1921 | https://www.loc.gov/item/sanborn05479_006/ | sheets 2, 3 (already in the repo) | `assets/maps/` |
| Sept 1948 | https://www.loc.gov/item/sanborn05479_007/ | sheets 2, 3 | scratchpad only (not committed): `C:\Users\Tarik\AppData\Local\Temp\claude\6b0f5045dbacd63f\c817071d-9017-42b3-a93d-c1a67bc890db\scratchpad\sanborn\full_1948_2.jpg`, `full_1948_3.jpg` |

Image URL pattern (IIIF): `https://tile.loc.gov/image-services/iiif/service:gmd:gmd381m:g3814m:g3814fm:g3814fm_g05479YYYY:05479_YYYY-000N/full/pct:100/0/default.jpg`
(the loc.gov item pages sit behind a Cloudflare check for scripts; the tile server does not).

Side-by-side crops (1910 | 1921 | 1948, same scale, public domain) in `research/sanborn-compare/`:
`east-24-38_…jpg`, `west-27-41_…jpg`, `west-57_…jpg`, `east-90-106_…jpg`.

**Scale and registration.** 1910 scale bar: 50 ft ≈ 295 px (1921: 292), so lengths compare directly.
Rough offsets 1910 → 1921 (±20 px): east side sheet 4 → 1921 sheet 2: **y + 780**, street line 1910 x ≈ 548
↔ 1921 x ≈ 3930–3950; west side sheet 5 → 1921 sheet 2: **y + 908, x − 2360**; east side sheet 4 → 1921
sheet 3 (Masonic Hall): **y − 4884, x + 3431**. 1948 sheet 2 is shifted by about −45 px in y and −55 px in x
against 1921 (the paste-ups vary; register locally on a shared wall).

**Old numbers.** 1910 prints only old 5xx numbers (east side 531–564, west 510–525); 1921 prints new and old.
Today's numbers differ again on the east side south of Court St (see 90–106).

---

## 24–30 Main (east side; placeholder `#bldg-24-30-main`, no spec yet)

The placeholder covers **two separate buildings**: 24–26 (old 561–560) and 28–30 (old 559–558), with a
white gap between them on every edition.

| | 24 (561) | 26 (560) | 28–30 (559–558) |
|---|---|---|---|
| **1910** | "2 D." frame dwelling, 2-storey rear part | "2 Mill'y" frame, 1-storey front addition (dashed) reaching from the south half of 561 across 560, ~0.7 m behind the street line | "2 Fruit & Candy" / "2 Barber", frame, one block, front ~2.7 m behind the street line, **no porch** |
| **1921** | "2 D", 1-storey porch strip ("1", dashed) along the front; rear wing now "1" with a porch | "2 Mill'y", the **1-storey front addition now projects past the street line** (front px x ≈ 3880 against the line at 3925–3935) | "2 Conf'y" / "2 Barber", **a narrow 2-storey porch strip ("2", dashed) added along the front**, rear 1-storey parts |
| **1948** | 24 and 26 **replaced by one building**: "2", "C.B. 1st" (concrete-block ground storey, frame above), "S"; big 1-storey concrete-block rear | (part of 24) | still 2-storey frame stores, porch strip still drawn |

1921 positions (sheet 2): 24 north wall y ≈ 3745, 24/26 line ≈ 3870, 26 south ≈ 3965; 28 north ≈ 4010, 28/30
line ≈ 4100, 30 south ≈ 4195 (z −164.4, −157.9, −152.9 / −150.6, −145.9, −140.9). Fronts: 24 wall x ≈ 3950
(scene x ≈ 8.0), its porch ≈ 3930 (6.9); 26 main wall ≈ 3955 (8.2), **26's shop addition ≈ 3880 (scene x ≈ 4.3,
i.e. on the modelled roadway)**; 28–30 wall ≈ 3955 (8.2), porch strip ≈ 3945 (7.7). Readings ±5 px; a
brightness-profile pass is needed before a spec.

**Today.**
- NRHP nomination (1980) inventory: **#24** "a 2-story, early 20th Century structure with stucco treatment
  around the first floor storefront. The 2nd floor has stucco walls with small, rectangular windows. It has
  an asphalt, shingle-covered, gable roof with modillions under the eaves." **#26** "a 1½-story, modern
  structure with brick around the first floor storefront and a steeply-pitched, shake roof with inset dormer
  windows." **No #28 or #30 entry** (the text cites "No. 28 Main Street" as an Italianate L-plan house without
  a tower, which does not fit the 1921 shop pair; probably a different numbering).
- Borough HPC property list (revised 7 Jan 2026): 24 **Contributing**; 26 **Encroaching**; **no 28 or 30**.
- Wikimedia Commons photo (5 Feb 2024, CC BY-SA 4.0, by Zeete), "24 Main Street, Flemington, NJ – looking
  north": https://commons.wikimedia.org/wiki/File:24_Main_Street,_Flemington,_NJ_-_looking_north.jpg . Left:
  the clapboard 18–22 Main with its oriel and porch (NRHP #18–22); right: a stuccoed building on a rubble-stone
  base with a green-framed shop front, probably today's 24.
- **Reading:** today's 24 is the post-1921 (by 1948) concrete-block/stucco rebuild, not the 1921 dwelling; 26's
  site is a modern building; 28–30 have probably gone (unconfirmed). **Nothing standing shows the 1920 look.**

**New vs PLAN.md (no spec):** the block is two buildings; 24 was a dwelling with a 1-storey porch, 26 a
millinery shop with a 1-storey front shop built out over the street line; 28–30 a 2-storey frame pair whose
narrow 2-storey porch was added between 1910 and 1921. **Flag for the future spec:** 26's front addition
sits ~3.3 m east of the map's own street line (x 3944 at 32–38), on what the scene models as roadway; in 1910
it stood behind the line. Either a map drafting quirk or a real encroachment; the spec must decide.

---

## 27 Main (west side; draft spec "Dry goods and clothing store", awaiting approval)

| | 27 (old 519 A/B) |
|---|---|
| **1910** | **"Gas Co's Office" (north) and "B.&S." (south)**, 2-storey brick, **25'**, two stores divided by a dashed partition. **Set back about 5.5 m** from the street line behind a **2-storey frame porch ("2", dashed) across the whole front**; 1-storey frame strip at the rear. 1910 px: brick x ≈ 5430–5850, y ≈ 2820–3030; porch to x ≈ 5905; street line ≈ 5960. |
| **1921** | "D.G. & Clo.", one store, 2-storey brick, 25'. Same north and south walls and depth as 1910 for the rear part, **but the front is now built out to the street line, over the old porch, and the new front part is ~2 m wider on the south side** (the notch the spec describes at y 3936 / 3976.5 is exactly the old 1910 south wall). |
| **1948** | same footprint, split again into 2 stores ("S", "S"), 25'. |

**So the front seen on the "Palace Theatre & Potter Building" card is a post-1910 front addition** (built
between Nov 1910 and Sept 1921), not the original building's face. That fits the card (a plain 1910s
commercial front with a long awning, deep plain cornice, four tall upper windows).

**Today.** NRHP 1980 inventory has **no #27** (it goes #26, #31). HPC list 2026: no 27. **#31** (1980): "a
3-story, mid-20th Century, commercial structure with a flat roof and storefront on the first floor" (2026:
non-contributing). The HCHS trail brochure says the Methodists' first church stood at **"21-27 Main Street (no
longer there)"** (https://hunterdonhistory.org/wp-content/uploads/2018/08/Flemington-TRAIL-online8-1.pdf);
whether the 1910 brick 519 A/B was the converted old church is **not established**. **Reading: no. 27 is gone
(site absorbed into the 31 lot or open ground); nothing survives to check.** Owner can confirm on Street View:
https://www.google.com/maps/search/?api=1&query=27+Main+St,+Flemington,+NJ+08822

**vs the draft:** **no contradiction.** Footprint, brick, 2 storeys and 25' all match. New supporting facts:
(1) the front is a 1910s addition to the street line; (2) the c. 1910 tenants were the gas company office and a
"B.&S." (boots & shoes) store; (3) the dashed line 0.5 m in front in 1921 (awning) is new after 1910. The draft's
"Potter Building" question stays open.

---

## 32–38 Main (east side; draft spec, awaiting approval)

| | 32 (557) | 34 (556) | 36 (555) | 38 (554) |
|---|---|---|---|---|
| **1910** | "2 Mill'y" | "2 Bakery" | "D.G." (dry goods, with a dashed inner partition) | "1" storey at the front |
| **1921** | "2 Mill'y" | "2 Bakery" | "Meats" (2-storey block + 1-storey strip) | (part of Meats) |
| **1948** | "2", "S" | "S" | "S" | merged with 36 |

- 1910: all frame, front wall about 2.0 m behind the street line (px x ≈ 588 vs 548), the same as 1921's 2.3 m.
  **No porch is drawn in 1910**: the 1-storey continuous porch of the 1921 map (dashed, x 3961) was **added
  between 1910 and 1921**. In 1910 the meat market was next door at old "39" (= 1921's 40, the 3-storey block).
- 1948: the porch is gone and a **brick (pink) strip runs along the whole front** at about the old porch line:
  a new brick front built out where the porch was.

**Today.** NRHP 1980: **"#32-38 Main Street – a 2-story, 3-unit, brick, commercial structure built around the
mid-20th Century."** HPC 2026: **non-contributing**. **Reading: the frame row has been replaced (or completely
re-fronted) since 1921; nothing original is visible.**
Street View: https://www.google.com/maps/search/?api=1&query=32+Main+St,+Flemington,+NJ+08822

**vs the draft:** the 1921 map remains the source, so the draft's porch, three shops and storeys stand. **One
caution for the draft's Stryker-plate note** (c. 1906–10 "continuous 1-storey porch with posts and striped
awnings" at the plate's left edge): **the Nov 1910 map draws no porch on this row**, so if the plate is pre-1910
that porch-like feature is either sidewalk awnings on posts (Sanborn does not map those) or a different frontage
(24–30 or 40–46). The draft already declines to use the plate for the row's form, so nothing needs changing;
just do not cite the plate as evidence for the 1921 porch.

---

## 35–41 Main (west side; APPROVED spec, assets ready)

| | 35–37 (517) | 39–41 (516) |
|---|---|---|
| **1910** | "3 Gro.", **28'**, frame, **2-storey porch strip ("2", dashed) across the front**, long 2-storey frame rear wing, 1-storey shed with a dashed side | **"2B" brick, "Barber Bas." + "D."** = barber shop in the basement, dwelling above; **dashed line ~0.4 m in front of the wall** (the balcony); front about 2.3 m behind the street line |
| **1921** | same: "3 Gro." 28', 2-storey porch | same footprint, "2B" 28'(?), "Cobbler" |
| **1948** | **porch gone**; "3 S 28'", frame, a thin brick (pink) strip on the front face; the rear wing is "2 Dry Cleang" | "2 S 28'", brick, a rear "Fr. 2d" part; front line about where it was |

1910 detail (sheet 5, px x 5780–5990, y 3360–3720): grocery wall x ≈ 5905, porch front ≈ 5947 (2.2 m; 1921: 2.0 m);
brick front ≈ 5917 with the dashed line at ≈ 5925; street line ≈ 5962. The 1910 brick front reads ~0.6 m in
front of the grocery wall (1921: flush within 1.5 px); minor, within drafting variation.

**Today.** NRHP 1980: **"#35 Main Street – a 2-unit, brick, mid-20th Century structure. The southern half is 3
stories high, and the northern unit is 1 story."** and **"#37 Main Street – a 2-story, brick, early 20th Century,
commercial structure."** HPC 2026: 35 **non-contributing**, 37 **contributing**. Which modern number covers which
1921 building is **not established**: the 3-storey frame grocery has either been replaced or brick-faced (35),
and "37, 2-storey brick, early 20th C" may be the 1921 "Cobbler" (2 storeys + basement, brick) re-fronted.
Street View: https://www.google.com/maps/search/?api=1&query=37+Main+St,+Flemington,+NJ+08822

**vs the approved spec: no contradiction; two confirmations.**
1. 1910 shows the same three forms (3-storey frame grocery 28' with 2-storey porch; brick 2B with front balcony line),
   so the c. 1905 and c. 1906–10 photos describe the building that stood in 1921. Good for the approved form.
2. **New:** in 1910 the basement of 39–41 was a **barber shop**. The spec's "two small striped cone-shaped objects
   either side of the door (not identified)" in the c. 1905 photo are almost certainly **barber poles**. By Sept 1921
   the basement is a "Cobbler", so leaving the poles out (as the spec does) is right; no change needed.

---

## 57 Main (west side; placeholder `#bldg-57-main`, no spec yet)

| | 57 (old 513–512) |
|---|---|
| **1910** | Brick. North front part "2" storeys with a "32'"(?) mark: **"Jewelry, Hand Printing, Photos 3rd(?)"**; behind/south a **3-storey brick dwelling "3 D."**, set back ~5 m from the street, drawn with a dashed inner outline (meaning not confirmed; possibly the upper storeys' outline); 2-storey brick rear wing. 1910 px: x ≈ 5600–5910, y ≈ 4195–4535. |
| **1921** | Same 3-storey brick body (**32'**), now stores: **"D.G."** (north, 2-storey front, 28'), **"Conf'y"** and **"Gro."** in **1-storey (14') brick shop fronts built out in front of the house**, front ≈ 2.1 m behind the street line; "Cobbler" in the 2-storey rear wing. 1921 sheet 2 px: x ≈ 3300–3550, y ≈ 5095–5435 (z ≈ −94.0 … −76.3; placeholder centre z −85.4 fits). |
| **1948** | Same outline; labels now "2", "S", "28'", "14'", "S", "S"; **no "3" or 32' left**, i.e. the 3-storey house body appears cut down or rebuilt as 2-storey stores by 1948. |

**Today.** NRHP 1980: **"#57 Main Street – a 4-unit, 2-story, brick, commercial structure built in the early 20th
Century with striated brick walls and a flat roof. The ground floor consists of aluminum storefronts."** (Also "#55
– a 2-story, brick, commercial structure built in the early 20th Century" next door.) Tax record: 57 Main, block 17
lot 9, commercial condo (https://www.njparcels.com/property/1009/17/9/C4103). HPC 2026 folds it into "39-69 Main
Street – Contributing / Encroaching". **Reading: today's 57 is a 2-storey striated-brick rebuild of the 1920s–40s; it
does not show the 1921 look** (3-storey brick house with 1-storey shops in front).
Street View: https://www.google.com/maps/search/?api=1&query=57+Main+St,+Flemington,+NJ+08822

**New vs PLAN.md (no spec):** in Sept 1921 this was a **transitional building**: a 3-storey brick dwelling (32')
with a 2-storey shop front (28') at the north and two 1-storey (14') shop fronts built out in front, all brick.
1910 shows the house without the shop fronts. No period photo identified yet.

---

## 90–94 Main, Masonic Hall / Hunterdon County National Bank (east side; APPROVED spec)

| | 90 (536) | 92 (535) | 94 (534) |
|---|---|---|---|
| **1910** | "3 Gro." | "3 D.G.", 38' | "3 **Bank**" (heating boiler in the basement) |
| **1921** | "3 **Bank**" (north 10.6 m = the old Gro. + D.G. stores) | | "Vacant" (old bank rooms); "Lodge Rms 3d" |
| **1948** | "3 BANK", "Lodge Rms 3rd" | | "S", "Br. 1st"; new 1-storey rear addition |

1910 px (sheet 4): front wall x ≈ 588, **dashed line x ≈ 577 (~0.55 m before the wall) along the whole front**, north
wall y ≈ 6580, partitions 6670 / 6785 (dashed), south 6915. 1921 spec reads the dashed line at 0.35 m.

**Today.** Standing. Goodspeed (June 2021) toured the building with March Construction and the mayor ahead of
its renovation in the Union Hotel / "Courthouse Square" redevelopment and photographed the 3rd-floor hall and
attic (https://goodspeedhistories.com/flemingtons-first-bank-part-two/); the caption of its c. 1918 facade photo
says the first floor was "renovated" in the 1920s. NRHP 1980: **"#90-104 Main Street – a 3-story, 5-bay, brick and
stone structure … It has a wide, gable roof with corbelled bricks, brackets, and arched wood trim under the eaves.
Each bay is articulated by brick pilasters and arched windows. The first floor is faced with rusticated stone and
has an entrance with Neo-Classical details."** HPC 2026: "90 Main – Significant / Non-contributing". HCHS walking
tour (via search snippet): "original brick arcades on the first floor were replaced with terracotta and granite
facade in the 1920's". The Union Hotel reopened July/Sept 2026
(https://www.wfmz.com/news/area/western-newjersey/hunterdon-county/a-relic-no-more-historic-union-hotel-reopens-in-flemington-after-11-years/article_3adac9ce-f2fc-41c1-9ee6-2a495cec1c21.html);
**no source found on what was done to the bank's front in the 2021–26 works**, so a current photo must be checked by
hand: https://www.google.com/maps/search/?api=1&query=90+Main+St,+Flemington,+NJ+08822 .
Surviving features worth matching (per 1980 text): gable front, 5 bays between brick pilasters, arched windows,
corbelled raking cornice with brackets and arched trim, rusticated stone ground floor.
Note: 82 Main (Odd Fellows / Hopewell Building) was demolished for the project (Wikipedia, Union Hotel article:
https://en.wikipedia.org/wiki/Union_Hotel_(Flemington,_New_Jersey); Goodspeed "Odd Fellows Hall is about to come down",
https://goodspeedhistories.com/hopewells-buildings/).

**vs the approved spec: no contradiction; strong confirmation.** 1910 shows the bank in the **south** store (534 =
94) and two other stores north of it; 1921 shows "Bank" across the old north and centre stores and "Vacant" in the old
bank rooms, exactly as the spec says (rebuilt 1920–21). The 1910 dashed line over the full front (the old arcade/
awning line) also matches the spec's dashed line. Small extra: "terracotta and granite" (tour) vs the spec's "pale
stone"; colour unchanged in practice.

---

## 96–98 Main, the 1875 "Democrat building" (east side; placeholder `#bldg-96-98-main`, no spec)

| | 96–98 (533) |
|---|---|
| **1910** | "2" brick **"Cigars & Tobacco"** (front), rear 2-storey brick **"Printing, Gas Eng., Metal Pot & Gas Furnace"** |
| **1921** | "2" brick **"Cigars"**, **"News"** strip at the south, rear "Printing, El. Mo." (electric motor) |
| **1948** | **"ONE S 13'"**: a 1-storey, 13 ft store (upper storey gone or rebuilt) |

**Identity (new):** this is John C. Hopewell's brick building "next to the Bank", begun Nov 1875, two storeys, built
for Joseph V. Smith's tobacco store and the *Hunterdon Democrat* (Goodspeed, https://goodspeedhistories.com/hopewells-buildings/
and https://goodspeedhistories.com/flemingtons-first-bank-part-two/). The 1876 deed **barred any building taller than
the existing one**. Goodspeed lists it (as **today's no. 104**) among the Main St buildings that once had a **mid-façade
arched roofline** (the arch is now lost): https://goodspeedhistories.com/roof-arches-part-one/ . The Democrat had left
Hopewell's buildings by 1926. **Today: "still standing but unrecognizable"** (Goodspeed). Not inventoried separately in
1980; no 104 in the HPC 2026 list (may sit under "90").
Street View: https://www.google.com/maps/search/?api=1&query=104+Main+St,+Flemington,+NJ+08822

**New vs PLAN.md (no spec):** 2-storey brick, 1875, cigar/news shop in front and the newspaper printing office behind;
probably an arched centre in the front cornice (Goodspeed's "roof arches" group; need a photo to confirm it was still
there in 1920).

---

## 100–102 Main (east side; placeholder `#bldg-100-102-main`, no spec)

| | 100–102 (532) |
|---|---|
| **1910** | "3 **Variety**", frame, **30'**, **2-storey porch strip ("2", dashed) in front**, 2-storey rear |
| **1921** | "3 **Auto Supplies**", frame, 30'; **the front strip is now marked "3"** (the porch replaced by a full-height front), with "D.R. 2.3" (read as dwelling rooms on the 2nd and 3rd floors); buried gasoline tank / curb pump (already in the street-props kit) |
| **1948** | "S", frame, 30', same outline |

**Today:** no entry in NRHP 1980 or the HPC 2026 list; no web source found. **Probably demolished or absorbed** (unverified).
Street View: https://www.google.com/maps/search/?api=1&query=106+Main+St,+Flemington,+NJ+08822

**New vs PLAN.md (no spec):** 3-storey frame, 30', and between 1910 and 1921 its 2-storey porch was built up into a
3-storey front.

---

## 106 Main (east side, corner of Higgins Ave; placeholder `#bldg-106-main`, no spec)

| | 106 (531) |
|---|---|
| **1910** | "3 **Drugs**", frame, **30'**, **1-storey porch ("1", dashed) in front**, long 1-storey/2-storey rear |
| **1921** | "3 **Drugs**", 30'; **front strip now "3"** (porch built up to a 3-storey front) |
| **1948** | "3 Drugs", 30', same |

Higgins Ave (south side of 106) is **today's Chorister Place** (inferred: the Choir School, "3 Chorister Place", is drawn
just south of Higgins Ave on the 1948 sheet; HCHS trail). **Today:** no 106/108 in NRHP 1980 or HPC 2026 (the next
listed is #110, a 3-storey early-20th-C brick block = 1921's 108–110 "Off./Stationery" across Higgins Ave). **Probably
demolished** (unverified). Street View (corner of Main St and Chorister Pl):
https://www.google.com/maps/search/?api=1&query=Main+St+and+Chorister+Pl,+Flemington,+NJ

**New vs PLAN.md (no spec):** 3-storey frame drugstore on the corner, 30', porch replaced by a 3-storey front between
1910 and 1921.

---

## Sources

Maps (public domain, Library of Congress):
- Sanborn Nov 1910: https://www.loc.gov/item/sanborn05479_005/ (sheets 4, 5)
- Sanborn Sept 1921: https://www.loc.gov/item/sanborn05479_006/ (sheets 2, 3)
- Sanborn Sept 1948: https://www.loc.gov/item/sanborn05479_007/ (sheets 2, 3)

Documents:
- NRHP nomination, Flemington Historic District (1980), inventory pp. 101–104 (OCR text layer is searchable):
  https://npgallery.nps.gov/GetAsset/1397179c-16a7-4dbf-8ec9-e635f23393f9
- Flemington Historic Preservation Commission, Historic District Property List (revised 7 Jan 2026):
  https://historicflemington.com/government/documents/department-documents/historic/1547-searchable-historic-district/file
- HCHS Flemington history trail brochure: https://hunterdonhistory.org/wp-content/uploads/2018/08/Flemington-TRAIL-online8-1.pdf
- Tax record 57 Main: https://www.njparcels.com/property/1009/17/9/C4103

Goodspeed Histories (Marfy Goodspeed):
- https://goodspeedhistories.com/hopewells-buildings/
- https://goodspeedhistories.com/flemingtons-first-bank-part-two/ (June 2021)
- https://goodspeedhistories.com/roof-arches-part-one/ (Aug 2021)

Redevelopment / today:
- https://en.wikipedia.org/wiki/Union_Hotel_(Flemington,_New_Jersey)
- https://preservationnj.org/pnj-news-20180816/seven-new-details-about-flemingtons-union-hotel-redevelopment-plan-flemington_raritan-nj-news-tapinto (Aug 2017)
- https://www.wfmz.com/news/area/western-newjersey/hunterdon-county/a-relic-no-more-historic-union-hotel-reopens-in-flemington-after-11-years/article_3adac9ce-f2fc-41c1-9ee6-2a495cec1c21.html (Sept 2026)
- https://christinecura.com/blog/after-18-years-flemingtons-main-street-has-its-anchor-back
- Wikimedia Commons, "24 Main Street, Flemington, NJ – looking north" (2024, CC BY-SA 4.0):
  https://commons.wikimedia.org/wiki/File:24_Main_Street,_Flemington,_NJ_-_looking_north.jpg

**For the owner to open by hand** (blocked to automated access or not checked):
- Real-estate listing 35 Main St (returned 403): https://www.raveis.com/prop/3897987/35-main-st-flemington-boro-nj-08822
- Google Street View for each address (links in each section above); the best way to confirm what stands today at
  27, 28–30, 35/37, 57, 90, 104 (=1921's 96–98), and the Main/Chorister corner.
- ProQuest Digital Sanborn Maps (library login): the only likely home of any 1927/1931 Flemington update, if one exists.
