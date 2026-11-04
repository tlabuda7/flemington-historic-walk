# History sources — research register

This register lists the **historical claims** the Flemington Historic Walk (Main Street, c. 1920)
makes or depends on, and where each one comes from. It lets anyone, for example the Hunterdon
County Historical Society, trace a detail in the scene back to its evidence, or see that it is a
guess.

- Compiled 2026-11-04 from the per-building **Sources** blocks and notes in `PLAN.md`, the brief
  and per-line sources in `data/dialogue/pickell.json`, and `SOURCES.md`. No new research was done,
  except one quick web search to check the HABS survey numbers (marked "verified 2026-11-04").
- **Asset licences** (textures, 3D bases, sounds, voice, code) are not repeated here: see
  [SOURCES.md](SOURCES.md).
- PLAN.md is the working document. Where it and this register disagree, PLAN.md is newer.

## How claims are graded

| Grade | Meaning |
|-------|---------|
| **Documented** | A source says it in words, or it shows plainly in a dated photo, or it is written on the 1921 Sanborn map (a label, storey count or height note). |
| **Measured** | A number we worked out from the Sanborn map (pixels × 0.0521 m; scale bar 50 ft = 292 px; about ±0.1 m) or by scaling a photo against a known size. The method is given. |
| **Inferred** | Reasoned from evidence, but no source states it. The reasoning is given. |
| **Guess / artistic** | No evidence. Chosen because it is typical of the period, or to make the scene work. Change freely if better evidence turns up. |

"Source not recorded" means PLAN.md states the claim but names no source. It does **not** mean
the claim is wrong.

Notes on the evidence:
- **Hand-tinted postcards** (marked "tinted" or "colour" below) were coloured by hand at the
  printer. Their colours are weak evidence, so colours taken from them are graded *Inferred*.
- **Photo dates** are the dates in the West Jersey History captions. Where a caption has no
  date, the date in brackets is our estimate (for example from car styles).
- **Sanborn map**: a fire-insurance map surveyed September 1921. It records footprint, storeys,
  construction (pink = brick, yellow = frame, blue = stone), heights at the eaves, roof type and
  use. It does not show façade details.

---

## 1. Bibliography

### 1.1 Maps

| ID | Source |
|----|--------|
| **[M1]** | *Sanborn Fire Insurance Map from Flemington, Hunterdon County, New Jersey*, Sanborn Map Company, September 1921, **sheet 2** (Main St from Pennsylvania Ave south to Court St). Library of Congress, Geography and Map Division, item `sanborn05479_006`, https://www.loc.gov/item/sanborn05479_006/ . Public domain. Local copy `assets/maps/flemington-1921-sanborn-sheet-02.jpg` (6450 × 7650 px), saved 2026-11-02. |
| **[M2]** | Same map, **sheet 3** (Main St from Court St south to William St). Local copy `assets/maps/flemington-1921-sanborn-sheet-03.jpg`, saved 2026-11-02. |

### 1.2 Historic American Buildings Survey (HABS), Library of Congress

All public domain (U.S. Government work); local copies in `assets/photos/reference/habs/`, saved 2026-11-02.

| ID | Source |
|----|--------|
| **[H1]** | HABS **NJ-771**, *Hunterdon County Courthouse, Main & Court Streets, Flemington* (LoC record `nj0068`, https://www.loc.gov/pictures/item/nj0068/). Photos (1960s): 1 East front `courthouse-east-front.jpg` (https://www.loc.gov/pictures/item/nj0068.photos.107297p/); 2 East front from the northeast `courthouse-east-front-from-northeast.jpg` (…107298p/); 3 East front and south side `courthouse-east-front-and-south-side.jpg` (…107299p/). Survey number from a Wikipedia list, verified 2026-11-04 by web search only (loc.gov refused the fetch). |
| **[H2]** | HABS **NJ-772**, *Alexander Wurts Law Office, 59 Main Street* (LoC `nj0072`). Photos (mid-20th c., probably 1960s–70s): 1 East front `wurts-law-office-east-front.jpg` (https://www.loc.gov/pictures/item/nj0072.photos.107271p/); 2 South side `wurts-law-office-south-side.jpg` (…107272p/). **Data form**: https://tile.loc.gov/storage-services/master/pnp/habshaer/nj/nj0000/nj0072/data/nj0072data.pdf . Survey number checked the same way as H1. |
| **[H3]** | HABS, *Union Hotel, 76 Main Street* (LoC `nj0071`). Photos dated **February 1963**: 1 West elevation `union-hotel-west-elevation-1.jpg` (https://www.loc.gov/pictures/item/nj0071.photos.107282p/); 2 West elevation `union-hotel-west-elevation-2.jpg` (…107283p/). PLAN.md calls this survey "HABS NJ-732"; that number is **not verified**. |

### 1.3 Period photographs and postcards — West Jersey History Project

Source: West Jersey History Project, *Historic Images of Hunterdon County: Flemington*,
https://westjerseyhistory.org/images/hunterdon/flemington/ . Each original is at
`https://westjerseyhistory.org/images/hunterdon/flemington/data/images/<file>`. Credit: "Courtesy
West Jersey History". **Local only**: the files are kept in `assets/photos/reference/` on the
developer's PC, are gitignored, and must not be published (reposting rights are not confirmed).
Cite them by filename. Saved 2026-11-01 (7) and 2026-11-02 (25). Captions are copied from the gallery.

| ID | File | Caption (date) |
|----|------|----------------|
| [P01] | `flemington_-_county_building_-_1912.jpg` | County Building – 1912 |
| [P02] | `flemington_-_hunterdon_county_court_house_viewed_dead_on_-_c_1910.jpg` | Hunterdon County Court House viewed dead on – c 1910 |
| [P03] | `flemington_-_hunterdon_county_courthouse_view.jpg` | Hunterdon County Courthouse view (undated; [1930s], cars) |
| [P04] | `flemington_-_some_business_blocks_on_main_street_-_1907.jpg` | Some business blocks on Main Street – 1907 |
| [P05] | `flemington_-_the_union_hotel_-_1900s.jpg` | The Union Hotel – 1900s |
| [P06] | `flemington_-_the_union_hotel_in_winter.jpg` | The Union Hotel in Winter (undated; [c. 1910s]) |
| [P07] | `flemington_-_the_union_hotel_with_parked_cars.jpg` | The Union Hotel with parked Cars (undated; [late 1920s–early 1930s]) |
| [P08] | `flemington_-_union_hotel_-_union_hotel_-_1910s.jpg` | Union Hotel – 1910s |
| [P09] | `flmgtnhtrdncntycrths2.jpg` | Hunterton [sic] County Courthouse (undated; [1930s–40s, after 1928]) |
| [P10] | `flmgtnmainststores.jpg` | Main Street Stores – 1910s |
| [P11] | `flmingtnporichardsbldgunionhtl.jpg` | Post Office – The Richards Building – The Union Htl (undated; [1906]) |
| [P12] | `flmngtnbankandpovu08.jpg` | Bank Building and Post Office – 1908 (tinted) |
| [P13] | `flmngtncntybldngsvuof08.jpg` | Court House and County Buildings – 1908 |
| [P14] | `flmngtncntycourthsview06.jpg` | Court House and County Buildings – 1906 (postmarked 10 July 1906) |
| [P15] | `flmngtncountybldnganddentistoffice09.jpg` | County Building and Dentist Office – 1909 (tinted) |
| [P16] | `flmngtncountycrthousvu09.jpg` | Hunterdon County Court House – 1909 (tinted) |
| [P17] | `flmngtncourthsandsurrogateoffice.jpg` | Hunterdon Court House and the Surrogate's Office – c 1910 (PLAN.md says c. 1908) |
| [P18] | `flmngtncrthouspublcbldg08.jpg` | Hunterdon Court House and the Surrogate's Office – c 1908 (tinted) |
| [P19] | `flmngtndcmuirheadsunionhtl10.jpg` | The Union Hotel – D. C. Muirhead, Proprieter [sic] – 1910 |
| [P20] | `flmngtndrinkingfountainbycrthous.jpg` | The Drinking Fountain by the Court House (undated; [c. 1910]) |
| [P21] | `flmngtnhtdncntycrtandbldg05.jpg` | Hunterdon County Court House – 1905 |
| [P22] | `flmngtnhtncountybldg08.jpg` | County office Building – 1908 (tinted) |
| [P23] | `flmngtnmainstrichardsbldgpo06.jpg` | Main Street – Richards Building – Post Office – 1906 |
| [P24] | `flmngtnmainstrtunionhtlvu08.jpg` | Main Street – Union Hotel – 1908 |
| [P25] | `flmngtnmainstrycolrvu10.jpg` | Main Street view – 1910 (tinted) |
| [P26] | `flmngtnneviusstoreandununionhtl09.jpg` | Nevius Store and Ununion [sic] Hotel – 1909 (tinted; the card itself is printed "Union Hotel") |
| [P27] | `flmngtnpoandnatbank08.jpg` | Post Office and National Bank – 1908 (tinted) |
| [P28] | `flmngtnpobankunionhtl07.jpg` | The Post Office, the National Bank and the Union Hotel – 1907 |
| [P29] | `flmngtnunionhtl.jpg` | A view of the Union Hotel (undated; [late 1920s–early 1930s]) |
| [P30] | `flmngtnunionhtlview.jpg` | Union Hotel (undated) |
| [P31] | `flmngtnunionhtlvu20s.jpg` | Union Hotel – 1920s |
| [P32] | `flmngtnunionhtlwthsnow.jpg` | Union Hotel With Snow – c 1910 |
| [P33] | `flmngtncountyhtl06.jpg` | The County Hotel – 1906 (tinted) — **viewed online 2026-11-04, not saved locally** |
| [P34] | `flmngtncountyhotel08.jpg` | The County Hotel – 1908 — viewed online, not saved locally |
| [P35] | `flmngtnmainstrtcountyhtlvu06.jpg` | Main Street – County Hotel – 1906 (looking south) — viewed online, not saved locally |
| [P36] | `flmngntnmainstcountyhtl08.jpg` | Main Street and County Hotel – 1908 (looking north) — viewed online, not saved locally |

### 1.4 Web photographs (looked at only, not saved to the project)

All are in Goodspeed Histories articles ([W12], [W18]). Photographers are named only where the article names them.

| ID | Image | URL |
|----|-------|-----|
| [G1] | "Lovell's Restaurant", after 1910, frontal (ground floor) | https://goodspeedhistories.com/wp-content/uploads/2021/09/9-Lovells-Rest-copy.jpg |
| [G2] | "Oysters", c. 1900, near-frontal, whole front of 68 Main | https://goodspeedhistories.com/wp-content/uploads/2021/09/2-Oysters-alone.jpg |
| [G3] | Bank and Oyster House, c. 1900, from the SW | https://goodspeedhistories.com/wp-content/uploads/2021/08/68-OysterHouse-Bank-copy.jpeg |
| [G4] | Richards Building fire, Feb 1901, from the NW | https://goodspeedhistories.com/wp-content/uploads/2021/09/6-Richards-fire.jpg |
| [G5] | Rea Building, modern frontal view (Dave Norton) | https://i0.wp.com/goodspeedhistories.com/wp-content/uploads/2021/08/54-Rea-Bldg-copy.jpg |
| [G6] | 50 Main St from the SW, Feb 2016 | https://i0.wp.com/goodspeedhistories.com/wp-content/uploads/2021/08/50Main-Feb2016_088-copy.jpeg |
| [G7] | Rea clock-tower cupola close-up (modern) | https://i0.wp.com/goodspeedhistories.com/wp-content/uploads/2021/08/Rea-Clock-Tower-copy.jpg |
| [G8] | Flemington National Bank in the Rea Building, 1876–91 | https://i0.wp.com/goodspeedhistories.com/wp-content/uploads/2021/08/54-Rea-FNB-copy.jpg |
| [G9] | "Mount's Hotel" (the County Hotel), c. 1905 (before Aug 1906), from the SE; Hunterdon County Historical Society PX333 (2.01.00333), in [W38] | https://i0.wp.com/goodspeedhistories.com/wp-content/uploads/2025/11/Hotel-Tunison.jpg |

Not given an ID: a modern photo of the Higgins News Agency (68 Main) in [W12], looked at and not used (no URL recorded).

### 1.5 Web texts

Access dates were not logged for each page. The date given is the day the citing spec was
written, so the page was read on or just before that day.

| ID | Source | Read by |
|----|--------|---------|
| **[W1]** | National Register of Historic Places, *Flemington Historic District* nomination (NRIS 80002493), National Park Service NPGallery, https://npgallery.nps.gov/AssetDetail/NRIS/80002493 (p. 103 quoted for the courthouse). PLAN.md notes that one copy of the PDF is a scan with no text. | 2026-11-02 |
| **[W2]** | Preservation New Jersey, "PNJ on Tour: The Historic Hunterdon County Courthouse and Jail", https://preservationnj.org/pnj-on-tour-the-historic-hunterdon-county-courthouse-and-jail/ | 2026-11-02 |
| **[W3]** | Goodspeed Histories (Marfy Goodspeed), "Hunterdon's Courthouse, 1828", https://goodspeedhistories.com/hunterdons-courthouse-1828/ | 2026-11-02 |
| **[W4]** | New Jersey Historic Trust, Hunterdon County Courthouse site details, https://www.nj.gov/dca/njht/funded/sitedetails/hunterdon_county_courthouse.shtml | 2026-11-02 |
| **[W5]** | Hunterdon County Historical Society, *Flemington walking trail* brochure (PDF), https://hunterdonhistory.org/wp-content/uploads/2018/08/Flemington-TRAIL-online8-1.pdf (entries for 56, 59 and 71 Main St) | 2026-11-03 |
| **[W6]** | Clarke Caton Hintz, Hall of Records project page, https://clarkecatonhintz.com/?p=1051 | 2026-11-03 |
| **[W7]** | Goodspeed Histories, "A Distinctive Feature of Downtown Flemington" (roof arches, part one), https://goodspeedhistories.com/roof-arches-part-one/ (quotes architectural historian Dennis Bertland) | 2026-11-03 |
| **[W8]** | The History Girl blog (author not recorded), "Leaving his mark in Flemington", 23 Jan 2013, https://thehistorygirl.com/2013/01/23/leaving-his-mark-in-flemington/ | 2026-11-03 |
| **[W9]** | Clarke Caton Hintz, Samuel Lewis Southard Law Office project page, https://clarkecatonhintz.com/project/samuel-lewis-southard-law-office/ | 2026-11-03 |
| **[W10]** | Wikipedia, "Flemington Historic District", https://en.wikipedia.org/wiki/Flemington_Historic_District | 2026-11-03 |
| **[W11]** | Goodspeed Histories, "County House" series (west side of Main St, Court to Capner Sts), https://goodspeedhistories.com/category/countyhouseseries/ | 2026-11-03 |
| **[W12]** | Goodspeed Histories, "The surprising history behind a modest building" (68 Main St; also Blackwell's Row and the 1897 bank building), https://goodspeedhistories.com/?p=23290 | 2026-11-03 |
| **[W13]** | Society of Paper Money Collectors, Bank Note History wiki, "Flemington National Bank, Flemington, NJ (Charter 2331)", https://banknotehistory.spmc.org/wiki/Flemington_National_Bank,_Flemington,_NJ_(Charter_2331) | 2026-11-03 |
| **[W14]** | Flemington National Bank centennial booklet, 1976, https://www.butkus.org/information/flemington_nat_bank/flemington_national_bank-1976.pdf — **seen only as a search-result snippet** | 2026-11-03 |
| **[W15]** | Goodspeed Histories, "Fulper's Store, or the Gilded Age on Main Street" (2022), https://goodspeedhistories.com/fulpers-store/ — quotes an architectural description of 78 Main by architect C. Pickell for the Friends of Historic Flemington | 2026-11-03 |
| **[W16]** | West Jersey History Project, Flemington image index (titles and dates of [P01]–[P32]), https://westjerseyhistory.org/images/hunterdon/flemington/ | 2026-11-01 |
| **[W17]** | Goodspeed Histories, "The Clock Tower Building", https://goodspeedhistories.com/the-clock-tower-building/ — includes an 1878 Rea advertisement and quotes a 1979 Hunterdon County historic sites survey | 2026-11-04 |
| **[W18]** | Hunterdon County Historical Society, article on the Rea Building, https://hunterdonhistory.org/?p=6574 | 2026-11-04 |
| **[W19]** | Hunterdon County Historical Society, Collection 238 container list (PDF), https://hunterdonhistory.org/wp-content/uploads/2022/06/Collection-238-Container-List.pdf — catalogue entry only; the photo itself was not seen | 2026-11-04 |
| **[W20]** | Wisconsin Historical Society, Albertype postcard "The Fountain, Flemington, N.J." (undated), image IM77896, https://www.wisconsinhistory.org/Records/Image/IM77896 | 2026-11-04 |
| **[W21]** | J. P. Snell (comp.), *History of Hunterdon and Somerset Counties, New Jersey* (1881), part 81 (Flemington Baptist Church), transcribed at https://ldsgenealogy.com/NJ/books/History-of-Hunterdon-and-Somerset-counties-New-Jersey-with-illustrations-and-biographical-sketches-of-its-prominent-men-and-pioneers-part-81.htm (compiler's name added from general knowledge, not from PLAN.md) | 2026-11-04 |
| **[W22]** | Wikipedia, "National Humane Alliance fountains", https://en.wikipedia.org/wiki/National_Humane_Alliance_fountains (comparison only) | 2026-11-04 |
| **[W23]** | Dan Lynn, *78 Main* history blog, https://78main.wordpress.com/ | 2026-11-03 |
| **[W24]** | 78 Main blog, post of 7 May 2009 (John B. Pickell's 50 years; the 1896 pencilled signature), https://78main.wordpress.com/2009/05/07/41/ — quotes [W37] | 2026-11-03 |
| **[W25]** | 78 Main blog, "Jacob Nevius, the founder", 18 Jan 2010, https://78main.wordpress.com/2010/01/18/jacob-nevius-the-founder/ | 2026-11-03 |
| **[W26]** | 78 Main blog, "The Nevius Store, 1917" (advertisement, "Dress Materials"), https://78main.wordpress.com/2009/06/11/the-nevius-store-1917/ | 2026-11-03 |
| **[W27]** | 78 Main blog, "Ladies' jackets for $4.75 (well, in 1901)", https://78main.wordpress.com/2009/06/11/ladies-jackets-for-4-75-well-in-1901/ | 2026-11-03 |
| **[W28]** | Wikipedia, "Union Hotel (Flemington, New Jersey)", https://en.wikipedia.org/wiki/Union_Hotel_(Flemington,_New_Jersey) | 2026-11-03 |
| **[W29]** | Wikipedia, "Flemington Speedway", https://en.wikipedia.org/wiki/Flemington_Speedway | 2026-11-03 |
| **[W30]** | Ellarslie (Trenton City Museum), article on Fulper Pottery, https://ellarslie.org/?p=3784 | 2026-11-03 |
| **[W31]** | Iowa State University eMuseum, "Fulper Pottery Co.", https://emuseum.its.iastate.edu/people/3661/fulper-pottery-co/objects | 2026-11-03 |
| **[W32]** | Wikipedia, "Flemington, New Jersey" (1920 census population 2,590), https://en.wikipedia.org/wiki/Flemington,_New_Jersey | 2026-11-03 |
| **[W33]** | Wikipedia, "Eighteenth Amendment to the United States Constitution", https://en.wikipedia.org/wiki/Eighteenth_Amendment_to_the_United_States_Constitution | 2026-11-03 |
| **[W34]** | Wikipedia, "Nineteenth Amendment to the United States Constitution", https://en.wikipedia.org/wiki/Nineteenth_Amendment_to_the_United_States_Constitution | 2026-11-03 |
| **[W35]** | U.S. Bureau of Labor Statistics via FRED (Federal Reserve Bank of St. Louis), Consumer Price Index for All Urban Consumers, not seasonally adjusted (CPIAUCNS), https://fred.stlouisfed.org/series/CPIAUCNS | 2026-11-03 |
| **[W36]** | Fashion Institute of Technology, *Fashion History Timeline*, "1920–1929", https://fashionhistory.fitnyc.edu/1920-1929/ | 2026-11-03 |
| **[W37]** | *Whitehouse Review*, 17 April 1945, p. 1 (article on John B. Pickell's 50 years with the Nevius store). **Not seen.** Known only as quoted in [W24]. | — |
| **[W38]** | Goodspeed Histories, "The County House, Part One", https://goodspeedhistories.com/the-county-house-part-one/ — names (County House / County Hotel / Mount's Hotel), W. H. Force, S. H. Mount 1891, 1907 sale, C. Tunison, architect Chris Pickell's notes, New Market (1970s), the "County Hotel" sidewalk slab; reader comments | 2026-11-04 |

---

## 2. Claims by building, person and item

Claim IDs (CH-1 and so on) can be quoted in correspondence. "Scene" means the 3D model or
placement; "dialogue" means something a character says.

### 2.1 Hunterdon County Court House (75 Main St) — in the scene

| ID | Claim | Grade | Sources | Method / note |
|----|-------|-------|---------|---------------|
| CH-1 | Built 1828 (cornerstone May 1828); portico in place by 1830. | Documented | W3, W2 | Also said in dialogue (PI-D7). |
| CH-2 | The ground floor held the county jail; the courtroom was on the high second floor. | Documented | W3 | Also in dialogue. |
| CH-3 | The present stone jail behind dates from **1925**, so it is not in a 1920 scene. In 1920 there was a jail yard with a 20-ft stone wall. | Documented | W2; M1 ("STONE WALL 20'") | |
| CH-4 | The 1-storey frame wing on the north side was the jail kitchen. | Inferred | W3, M1 | W3 says a frame building at the side served as the jail kitchen; matching it to the map's north wing is our reading. |
| CH-5 | Temple plan, 3-bay front, high stone foundation, octagonal frame cupola over the front of the roof, arched transom, sidelights, 6-panel double doors. | Documented | W1 (p. 103) | Sidelights are not modelled (deep shadow in P02). |
| CH-6 | Walls are stucco over stone masonry; front steps are brownstone. | Documented | W2, W4 | |
| CH-7 | Stone body 13.40 × 20.48 m, 2 storeys; full-width portico 4.43 m deep; north wing 3.8 × 7.8 m; jail yard and 2-storey frame yard building 5.0 × 6.3 m. | Measured | M1 (px x 2967–3445, y 6567–6897) | Pixels × 0.0521 m; second independent measurement agreed within ~0.1 m. |
| CH-8 | Portico front 8.0 m behind the Main St property line; south wall on the Court St line. | Measured | M1 | |
| CH-9 | Eaves/cornice top 9.0 m; ridge 13.1 m; pediment pitch ≈ 31°. | Measured | M1 ("30'"), P02, H1 | P02 scaled by frieze width 13.4 m (0.031 m/px). Ridge from P02 + H1. |
| CH-10 | Four unfluted Doric/Tuscan columns, evenly spaced (4.09 m), base Ø ≈ 0.9 m, on dark brownstone pedestals. | Documented / Measured | P02, H1 | Form seen in photos; sizes scaled from P02. |
| CH-11 | Podium (portico floor) 1.10 m, 6 risers. | Measured | P02, H1 | P02 alone reads 0.93 m / 5 risers; within photo error. |
| CH-12 | 1905–1912: **paired scroll brackets** in the frieze and on the raking cornice; by the 1930s these were replaced by plain modillions. The model uses the brackets. | Documented (both states) / Inferred (1920) | P02, P13, P14, P21; P03, P09, H1 | **The date of the change is unknown**; brackets chosen as the nearer evidence to 1920. |
| CH-13 | Pediment has **two** windows in c. 1910 (later views show 3 + 2). | Documented | P02; P03, H1 | |
| CH-14 | Front wall: round-arched centre door with fanlight, windows on two floors each side, small attic lights; dark-painted sash in 1910. | Documented | P02, H1 | Attic lights from H1 (dark in P02). |
| CH-15 | Side walls: 5 window bays behind a 3.5 m blank front strip. | Documented / Measured | H1, P03 | Seen on the south side only; north side assumed the same. |
| CH-16 | Octagonal cupola on a square base with arched louvred openings, a bell-shaped ribbed dome, ball finial and spike, top ≈ 19.4 m. | Documented / Measured | P02, H1, P16 | Height checked against P02 with perspective. |
| CH-17 | A red brick chimney just north-east of the cupola (1906–09); gone by the 1960s. | Documented | P14, P16, P18 | Position estimated from the NE views. |
| CH-18 | Three rear chimneys on **each** roof slope (6 in total). | Guess / artistic | P16 (north), H1/P03 (south) | They may be the same three stacks seen from both sides. Open question. |
| CH-19 | Roof: dark grey slate. | Guess / artistic | — | No photo shows the roof clearly. The 1908 tinted card [P18] shows it green, which could mean painted tin. |
| CH-20 | Walls painted warm off-white/cream; columns and trim brighter white; brownstone red-brown. | Inferred | P16, P02 | Colour from a hand-tinted card plus sepia tones. |
| CH-21 | Cupola dome: painted sheet metal, muted green. | Inferred | P16 (green), H1 (ribbed metal) | |
| CH-22 | No iron bars on the jail windows. | Inferred | — | No photo shows bars. (The spec text still mentions "bars (guess)"; the owner's decision of 2026-11-03 removed them.) |
| CH-23 | No handrails, railings, flagpole or lamps on the building in 1920 (the 1960s has handrails, a lantern and a flagpole). | Documented (absence in 1905–12 photos) | P02, P13, P14, H1 | |
| CH-24 | Paved forecourt in front (no lawn); young trees at the curb. | Documented | P13, P14, P16, P21 | |
| CH-25 | Small datestone in the frieze. | Source not recorded | — | Presumably seen in P02. |
| CH-26 | North wing: clapboard painted dull buff-brown; door under a shed hood; window. | Inferred (form) / Guess (colour) | P16 | |
| CH-27 | Rear (west) wall, the north wing's roof and the yard building's form. | Guess / artistic | — | Not visible in any photo. |
| CH-28 | "F.A." (fire-alarm box) at the foot of the steps. | Documented (map label) | M1 | Form unknown. The courthouse owner decision says "include as a prop"; the street-props spec left it out. |

### 2.2 Hunterdon County Offices / Hall of Records (69–71 Main St) — in the scene

| ID | Claim | Grade | Sources | Method / note |
|----|-------|-------|---------|---------------|
| CO-1 | The county Hall of Records, Italianate, red brick, 2 storeys; built **1870** (HCHS, Clarke Caton Hintz) or **1871** (Goodspeed). | Documented | W5, W6, W7 | Sources differ by one year. |
| CO-2 | It housed county offices including the Surrogate and the County Clerk. | Documented | P17, P18 (captions "Surrogate's Office"); W20 ("Clerk's Office") | |
| CO-3 | "Originally built with three separate doorways each with its own steps"; remodelled and expanded **1928**. So 1920 = the original front. | Documented | W5, W6 | |
| CO-4 | "Common" bricks on the sides. | Documented | W5 | |
| CO-5 | One building 13.9 × 15.2 m, 2 storeys, 28 ft; numbers 69 and 71; no rear wing. | Measured / Documented | M1 (px x 3164–3456, y 6232–6498; "COUNTY OFF'S", "28'") | |
| CO-6 | Front wall 7.4 m behind the property line. | Measured | M1 | |
| CO-7 | Ground floor reads window–door–window–door–window–door–window; upper floor 4 windows plus a paired arched window in the centre. | Documented / Inferred | P13, P14, P21, P01 | North half clearly seen; south half assumed symmetric. |
| CO-8 | A curved (segmental) roof arch with a round oculus over the centre bay. | Documented | P13, P14, P21, P01; W7 | |
| CO-9 | Deep cornice with paired scroll brackets on the front and sides. | Documented | P13, P14 | |
| CO-10 | Cornice top 8.6 m, raised basement 1.2 m, 7-riser stoops, string course at ≈ 5 m. | Measured | M1 ("28'"); P14 (≈ 59 px/m at the north corner) | |
| CO-11 | Stoops have black iron railings; basement windows have iron grilles. | Documented (railings) / Inferred (grilles) | P14, P01 | Railing pattern simplified (photos show ornamental cast iron). |
| CO-12 | Open cream shutters on ground-floor windows only. | Documented (shutters) / Inferred (colour) | P13, P15, P01; P18 | Colour from a tinted card. |
| CO-13 | No awnings in 1920. | Inferred | P13, P18 (awnings, 1906–08); P15, P01 (none, 1909–12) | Followed the latest photos. |
| CO-14 | The stone panel on the string course carried "DENTIST" in 1909–12; in the scene it is **blank**. | Documented (1909–12) / Guess (1920) | P15, P01 | The 1920 tenant is unknown. |
| CO-15 | A window lettered "SHERIFF'S OFFICE" (c. 1910). | Documented | P20 | Not shown in the model. |
| CO-16 | Stone trim (stoops, string course, sills, keystones) is pale buff, not brownstone. | Inferred | P13, P18 | It reads light in sepia and white in the tinted card. |
| CO-17 | Red pressed brick front; light drab cornice and woodwork. | Inferred | P18 | One tinted card. |
| CO-18 | Low hipped tin roof painted dark red-brown. | Guess / artistic | — | Never seen clearly. |
| CO-19 | No chimneys. | Inferred | P13 | None visible on the north roofline. Sanborn wall symbols at 4.4 m and 11.9 m are unexplained. |
| CO-20 | Side walls have 4 bays; rear wall layout and back door. | Guess / artistic | — | Only 2–3 side bays visible in any one view; rear never seen. |
| CO-21 | Lawn, low iron post-and-rail fence along the sidewalk; ~2 m board fence to the courthouse wing. | Documented | P15, P01 | Not yet built in the scene. |

### 2.3 Wurts Law Office (59 Main St) — in the scene

| ID | Claim | Grade | Sources | Method / note |
|----|-------|-------|---------|---------------|
| WU-1 | Built **1811** as a plain clapboard office. | Documented | W5, W9 | |
| WU-2 | Remodelled as a Greek Revival "temple" by builder Mahlon Fisher: **1840** (HCHS) or **ca. 1830** (HABS data form). | Documented | W5, H2 (data form) | Sources disagree on the date. |
| WU-3 | Known as both the Samuel Southard Law Office (HCHS) and the Alexander Wurts Law Office (HABS); Wurts used it 1820–1881. | Documented | W5, H2, W10 | |
| WU-4 | Opened "for a time in the late 1920's as a women's public restroom". | Documented | W5 | PLAN.md says the Women's Club did this; the quoted text does not name the club (source not recorded for "Women's Club"). |
| WU-5 | Frame, flush siding on the east front and clapboard elsewhere; 1-storey portico; flat roof; deep entablature with dentilled architrave and carved wooden wreaths; square columns with egg-and-dart capitals. | Documented | H2 (data form), W8 | Egg-and-dart not modelled. |
| WU-6 | The rear T-wing seen in HABS is a later addition, so it is not in the 1920 model. | Documented | H2 (data form "western wing is an addition"); M1 (not on the 1921 map) | |
| WU-7 | A small 1-storey frame lean-to at the rear, 2.9 × 1.1 m. | Measured | M1 | Heights, door and window are guesses. |
| WU-8 | Overall depth 8.0 m; portico front 4.69 m behind the property line. | Measured | M1 (px x 3356–3508.5) | |
| WU-9 | Width **4.70 m**, not the map's 4.12 m. | Inferred | H2 photos | At 4.12 m the HABS front would give a 0.6 m door. Width from the two HABS photos' proportions with the map's depth. |
| WU-10 | Portico 1.6 m deep (map strip shows 0.89 m). | Measured | H2 photos | From the south-side photo and a capital-height parallax check. |
| WU-11 | Cornice top 4.42 m; porch floor 0.30 m. | Measured | H2 (≈ 102.7 px/m on the pillar plane) | HABS ground may be higher than in 1920. |
| WU-12 | Four square plain pillars; 7 wreaths on the front frieze, 9 on each side; W-D-W front; two shuttered windows on the south side with a mid pilaster. | Documented | H2 photos | North side assumed a mirror of the south (Guess). |
| WU-13 | One interior brick chimney south of centre. | Documented (HABS) / Inferred (1920) | H2 photos | Assumed already there in 1920 (a stove-heated office). |
| WU-14 | Painted white all over, dark green louvred shutters; door dark green. | Inferred (white, shutters) / Guess (door colour) | H2 (black-and-white, later) | The HABS door is white; it may be a replacement. |
| WU-15 | No sign in 1920. | Guess / artistic | — | The HABS "County Superintendent of Schools" board is mid-20th century; the 1920 occupant is unknown. |
| WU-16 | No West Jersey History photo shows the office. | Documented (search result) | P01–P32 checked | |

### 2.4 Bank Building / Flemington National Bank (56–66 Main St) — in the scene

| ID | Claim | Grade | Sources | Method / note |
|----|-------|-------|---------|---------------|
| BA-1 | Built **1897** by William Richards on the site of "Blackwell's Row". | Documented | W12, W5 | |
| BA-2 | Also called the "Richards Building" / "Richards Bldg". | Documented | P11, P23 (captions) | |
| BA-3 | The Flemington National Bank (chartered 1876, charter no. 2331) had its banking room at the north (Bloomfield Ave) end. | Documented | W13; M1 ("Bank" at no. 56); W14 (snippet: "Corner of Main & Bloomfield Avenue") | |
| BA-4 | A first-floor fire on **9 Feb 1901**, which started in the Henry Richards building and spread to the bank building, was repaired. | Documented | W13, W5, G4 | |
| BA-5 | "Multiple entryways have been changed over the years." | Documented | W5 | So the 1920 entrances are uncertain; the 1906–08 layout is used. |
| BA-6 | 1921 tenants north to south: Bank (56), Men's Furnishings (58), Drugs (62), Boots & Shoes (64), Confectionery (66). | Documented | M1 | Tenant names not known. |
| BA-7 | The Post Office was **not** in this building but across Bloomfield Ave in the Rea Building. | Documented | P11, P23, P28 (captions and "P.O." awning); W17 | |
| BA-8 | 3 storeys, 40 ft; L-shaped plan, front 22.14 m, 20.32 m deep (56–58) and 11.05 m deep (62–66). | Measured / Documented | M1 ("3", "40'") | |
| BA-9 | Front wall 1.95 m behind the property line; stoops in that strip. | Measured | M1 | |
| BA-10 | One continuous 1897 façade with 12 equal upper bays; rock-faced grey stone ground storey, belt course, red brick above; rectangular 2nd-floor windows with pale lintels; round-arched 3rd-floor windows; pale roundels; panelled frieze; modillion cornice. | Documented | P12, P27, P28, P11, P23 | 12 bays counted on P12. |
| BA-11 | North (Bloomfield) side has 11 bays and the cornice runs its full length. | Inferred | P28 | Only the first 4 bays are visible. |
| BA-12 | Storey heights (belt course 4.30–4.60 m, cornice 11.45–12.20 m). | Measured / Guess | M1 ("40'"); P28 (≈ 31 px/m at the corner) | Only the 40-ft total is measured; floor heights from low-viewpoint cards. |
| BA-13 | Bank window plus a round-arched stone entrance with its own stoop and iron railings at the north end. | Documented | P28, P11, P23 | |
| BA-14 | Four shop fronts with raised floors and small stone stoops with sloping cheek walls. | Documented (presence) / Guess (details) | P12, P27 | Door recesses, bulkheads and transoms are period-typical. |
| BA-15 | Striped red-and-cream canvas awnings on the four shop bays. | Documented (awnings) / Inferred (colours) | P11, P23, P27, P28 | Colours from a tinted card. Upper-window awnings (1907–08) left out: artistic choice. |
| BA-16 | One chimney on the south wall near the front; plain south wall with no openings. | Documented / Inferred ("only one") | P12 | |
| BA-17 | Colours: red-brown brick, mid-grey stone, one pale drab for cornice and trim. | Inferred | P27, P12 | The cards disagree (dark grey cornice in one, pink front in another). |
| BA-18 | Rear and courtyard walls, roof slopes and heights. | Guess / artistic | — | Never photographed. |

### 2.5 Nevius Store / Fulper's Dry Goods Building (78 Main St) — in the scene

| ID | Claim | Grade | Sources | Method / note |
|----|-------|-------|---------|---------------|
| NE-1 | A store has stood on the lot since before 1856. | Documented | W15 | |
| NE-2 | William H. Fulper made "extensive alterations" in 1880, which most likely gave the present brick front. | Documented (alterations) / Inferred (that they made this front) | W15 | The architect C. Pickell (quoted in W15) dates the front "probably in the 1880's". |
| NE-3 | Occupants: Fulper (to 1880), Hall, Trewin & Rittenhouse (1887–92), W. E. Trewin (1892), Andrew T. Connet (1897, died 1913). | Documented | W15 | See question Q1: this does not fit Nevius being there from 1895. |
| NE-4 | Known as the "Nevius Store" by 1909. | Documented | P26 (gallery title) | The card itself is printed "Union Hotel". |
| NE-5 | 1907: awning lettered "DRY GOODS · NEVIUS BROS · NOTIONS". | Documented | P04, P10 | As read from the cards. **The scene's awning has no lettering.** |
| NE-6 | Goodspeed says the Nevius family "took possession… in the 1930s". | Documented, **not followed** | W15 | Contradicted by NE-4, NE-5 and Pickell's 1895–1945 service (PI-1). |
| NE-7 | 1921: brick, 3 storeys, 35 ft, "Dry Goods", street no. 78 (old no. 539); a 2-storey brick "FEED HO." (24 ft) behind. | Documented | M2 | Feed house not modelled. |
| NE-8 | Footprint 8.00 × 32.25 m; front on the property line. | Measured | M2 (153 × 619 px), M1 | Other values: 8.31 m (sheet 2 overlap strip), 7.62 m ("only 25 feet wide", W15). |
| NE-9 | Local red brick on a rubblestone base; brick quoins at the corners; a central projecting section; segmental and semicircular arched wooden 1/1 windows; slim brick hood moulds ending in square blocks; stone arches with keystones on the 2nd floor; boldly projecting stone sill bands on the 3rd floor. | Documented | W15 (C. Pickell's description of the surviving front), P26, H3 | |
| NE-10 | 2nd floor = segmental heads, 3rd floor = semicircular heads. | Inferred | W15, P26 | W15 says the shapes "alternate"; the floor split is read from the blurry 1909 card. |
| NE-11 | 1 + 2 + 1 windows per upper floor. | Documented / Inferred | P26, H3 | The south single window is out of frame in 1909; assumed symmetric. |
| NE-12 | Bracketed cornice with a segmental-arched pediment over the centre. | Documented | P26, H3 | |
| NE-13 | Cornice 10.70 m; floor levels; pediment crown 11.95 m. | Measured / Guess | M2 ("35'"); P26 (≈ 85 px/m at 2× zoom) | Pediment height is a guess. |
| NE-14 | The 1920 shop front = the 1909 one (display windows, recessed central double door). Upper-floor street door at the south end. | Inferred / Guess | P26 | The south end is not visible. |
| NE-15 | One striped canvas awning with a scalloped valance. | Documented (1909) / Inferred (still in 1920) / Guess (colours) | P26 | The 1909 tint shows a mostly pale awning. |
| NE-16 | Cream cornice and stone trim. | Inferred | P26 | Tinted card. |
| NE-17 | Side walls: 4 segmental windows per upper floor; south ground-floor windows; rear wall; flat roof; chimney. | Guess / artistic | H3 (north cornice only) | |
| NE-18 | By 1963 the brick was painted white and there was a 1950s shop front and a display window in the north wall; not used. | Documented | H3, W15 | |

### 2.6 Frame dwelling at 65 Main St (old no. 510) — in the scene

| ID | Claim | Grade | Sources | Method / note |
|----|-------|-------|---------|---------------|
| HM-1 | A 2½-storey frame dwelling ("D"), street no. 65, old no. 510. | Documented | M1 | |
| HM-2 | L-shaped plan: front block 8.60 × 9.72 m, rear ell 4.27 × 7.24 m on the north side, centred open front porch 4.0 × 2.0 m, 2-storey canted bay on the south side, open rear porch 4.07 × 1.41 m. | Measured | M1 (px lines in PLAN.md) | |
| HM-3 | Porch front 3.80 m and front wall 5.81 m behind the property line. | Measured | M1 | |
| HM-4 | Owner, builder and date of construction. | **Source not found** | W5, W11, W1, H1–H3 searched | |
| HM-5 | Built mid-19th century. | Inferred | M1 | From the plan type and "2½"; no source. |
| HM-6 | Gone today; a modern flat-roofed building stood on the site by the time of the HABS photos. | Documented | H2 (left edge of the east-front photo) | Demolition date unknown. |
| HM-7 | Front-facing gable (ridge east–west). | Inferred | P15, P01, P22 | The south wall shows an eaves line receding west; weak evidence. |
| HM-8 | Pale cream clapboard walls with wide laps; trim the same colour. | Inferred | P15 (tinted), P01 | Trim colour is a guess. |
| HM-9 | Slate roof, dark grey. | Guess / artistic | M1 ("o" = slate or tin) | |
| HM-10 | Eaves 7.0 m, ridge ≈ 10.25 m (built 10.48), 37° pitch, floor 0.75 m, porch 0.68 m. | Guess (rough photo estimate) | P01 | Eave ≈ 0.7 × the Hall of Records cornice in P01. |
| HM-11 | **The whole front**: 3 bays, centred door with transom, 2 attic windows, 2/2 sash, dark-green louvred shutters. | Guess / artistic | — | **No photo shows the front.** |
| HM-12 | Porch details: 4 chamfered posts, railing, low hipped roof, 3 steps. | Guess / artistic | M1 (size and position only) | |
| HM-13 | Side, rear and ell window positions; ell side door; rear-porch details. | Guess / artistic | — | |
| HM-14 | Two brick chimneys; red-brick foundation. | Guess / artistic | — | None visible in any photo. |
| HM-15 | A low post-and-rail fence along the sidewalk; shade trees. | Documented | P15, P01 | Not built in the scene. |

### 2.7 Lovell's Restaurant (68 Main St) — in the scene

| ID | Claim | Grade | Sources | Method / note |
|----|-------|-------|---------|---------------|
| LO-1 | Flemington's oyster restaurant from 1848. | Documented | W12 | |
| LO-2 | An 1870 remodel gave the front its arch in the roofline. | Documented | W12 | |
| LO-3 | Theodore B. Bellis ran a "restaurant and billiard room" 1886–c. 1910. | Documented | W12 | |
| LO-4 | Fred Lovell ran "Lovell's Restaurant" from c. 1910 to after 1935 (seen in a Lindbergh-trial photo), so in 1920 it is Lovell's. | Documented | W12 | |
| LO-5 | 1921: frame, 2 storeys, "Restr't & Pool Room 2nd", no. 68; a separate 2-storey frame Harness Shop behind it. | Documented | M1 | |
| LO-6 | The left door was the "Ladies' Entrance"; the restaurant was originally in the basement; ice came through a sidewalk manhole. | Documented | W12 | Manhole not modelled. |
| LO-7 | The building still stands as the Higgins News Agency, refaced in buff brick with a flat top. | Documented | W12 (modern photo) | |
| LO-8 | Depth 18.39 m; front wall 2.36 m behind the property line (0.42 m behind the bank's). | Measured | M1 (px x 4040–4393) | |
| LO-9 | Width 6.00 m, touching the bank. | Inferred | M1 (5.6 m, a 0.5 m slot to the bank); G2, G3, G4, G1, P12 (fronts touch) | Lovell's photo scaled by three men (~1.7 m) gives 5.5–6.0 m. |
| LO-10 | Shop front, north to south: single door – pier – recessed glazed double door – pier – display window with an "ICE CREAM" bulkhead and a cellar window; panelled corner pilasters; hanging lantern; 3 stone steps across the two doors. | Documented | G1 | The lantern being gas is inferred. |
| LO-11 | Signs: "RESTAURANT" board with end consoles; small "LOVELL'S" board between the upper windows; pale scalloped awning lettered "LOVELL'S RESTAURANT." | Documented (wording) / Guess (sign colours, letter style) | G1 | Wording as read from the photo. |
| LO-12 | Upper floor: 2 shuttered windows with segmental heads; two short bracketed cornice blocks; a segmental arch between them. | Documented | G2, G4, P12 | |
| LO-13 | Heights: cornice ≈ 6.7 m, arch apex ≈ 7.55 m, floor 0.45 m. | Measured (±0.3 m) | G2 (scaled by the bank's belt course 4.45 m and 0.17 m risers), G1 (doors, people) | |
| LO-14 | Smooth boarded front; clapboard side walls. | Documented | G2, G3, P12, P08, P19 | |
| LO-15 | Painted cream all round. | Inferred | P12 (cream front), P08, P19 | P12 shows the side wall tan; the later cards were followed. |
| LO-16 | Dark green louvred shutters and doors. | Guess / artistic | G1 (dark louvred shutters) | Colour unknown. |
| LO-17 | Low tin shed roof hidden behind the front and side cornices. | Inferred | G3, P08 | Level eaves line, no gable. |
| LO-18 | South wall: 4 windows upstairs, 3 + kitchen door downstairs; north wall blank where it touches the bank. | Inferred / Guess | G3 | Window spacing and the kitchen door are guesses. |
| LO-19 | One brick kitchen chimney on the north wall. | Guess / artistic | — | None seen. |

### 2.8 Rea Building / "Clock Tower Building", old Post Office block (48–52 Main St) — spec approved, not built yet

| ID | Claim | Grade | Sources | Method / note |
|----|-------|-------|---------|---------------|
| RE-1 | Built **1874** for George A. Rea, shoe dealer; "the new building under the Town Clock" (1878 advertisement). | Documented | W17, W18 | |
| RE-2 | The Flemington National Bank occupied the south shop 1876–1891. | Documented | W17, G8 | |
| RE-3 | Shields bought it and "the rear building on Bloomfield Avenue" in 1895; repainted 1895; granolithic walk 1898. | Documented | W17 | |
| RE-4 | The U.S. Post Office leased the first-floor room (16 × 46 ft) from **1 Feb 1899**; "P.O." on the south awning in 1906–07. | Documented | W17, P11, P23 | |
| RE-5 | Owners: Berkaw 1911; **Frank E. Green 1915**. | Documented | W17 | |
| RE-6 | 1921 tenants: 48 Drugs, 50 Cobbler, 52 Jeweler (1st floor) / Club Rooms (2nd). | Documented | M1 | Names of the cobbler, jeweler and club not known. |
| RE-7 | No. 48 is Green's drug store ("GREEN'S APOTHECARY" awning). | Documented (1906–07 awning) / Inferred (1920) | P28, P11, W17, W19 | Green bought the building in 1915; the drug store on the map is assumed to be his. |
| RE-8 | The Post Office had left by 1921. | Inferred | M1 (no "P.O.") | Where it went is unknown. |
| RE-9 | It is not the "Richards Building" of the card captions. | Inferred | P11, P23, P28 | The captions list P.O., Richards Bldg and Union Hotel from north to south. |
| RE-10 | 3-storey brick Italianate; segmentally arched pediments on the centre of each street side; oval front window; segmentally arched brick hoods; stone keystones and sills; wood cupola with a clock on each of its 4 sides; stucco panels on the ground floor. | Documented | W17 (1979 county survey), W7 (Bertland), G5, G6, G7, P28 | |
| RE-11 | Height: cornice top 11.0 m. | Measured | M1 ("36'"); P28 vanishing-point check | The modern photo G5 (perspective-corrected) would suggest ~12.5 m. |
| RE-12 | Main block 15.94 × 15.20 m plus the 3-storey brick "Flats" wing (4/6 Bloomfield Ave) 8.91 × 7.87 m; front 0.55 m behind the property line. | Measured | M1 | |
| RE-13 | Upper front 7 bays grouped 2–3–2, pediment over the middle three; window sizes. | Measured | G5 (façade 1130 px = 15.94 m) | Modern photo; the 1906–08 cards agree. |
| RE-14 | Ground floor: shops with raised floors; pale rusticated middle section with 3 round arches; stone steps along the whole front standing on the public sidewalk. | Documented | P28, P11, P23, G8 | 4 risers is a measurement/guess. |
| RE-15 | What the three arches were in 1920: cobbler's door, window, stair-hall door. | Guess / artistic | — | 1907 shows window, window, door; today window, door, window. |
| RE-16 | Awnings: 48 plain cream lettered "GREEN'S APOTHECARY"; 52 red/cream striped; none on 50 or upstairs. | Documented (1906–07) / Guess (still so in 1920) | P28, P11 | |
| RE-17 | Boards "SHOES REPAIRED" and "JEWELER". | Guess / artistic | M1 (uses only) | **Wording invented.** |
| RE-18 | Cream cupola with pilasters and tall windows; brick chimney beside it; tall iron pole on top; open pale shutters. | Documented (form) / Inferred (colours) | P27, P12 (tinted) | |
| RE-19 | Clock dials white with black numerals; hands at about 4:50. | Guess / artistic | — | Today's dials are teal (not used). |
| RE-20 | North, rear and Flats walls; cupola size; roof form; side pediment size. | Guess / artistic | G6 (partial) | |
| RE-21 | "One of the best preserved" of Flemington's buildings. | Documented | W18 | |

### 2.9 Union Hotel (70–76 Main St) — in the scene, built before this pipeline

The hotel was modelled before per-building specs were written, so PLAN.md has **no Sources
block** for it: its historical basis is **source not recorded** beyond the photos [P05]–[P08],
[P19], [P24], [P29]–[P32], [H3] used for modelling.

| ID | Claim | Grade | Sources | Method / note |
|----|-------|-------|---------|---------------|
| UH-1 | The hotel front dates from 1878, built on an older tavern. | Documented | W28 | Used in Pickell's dialogue. (A web-search summary of W10 on 2026-11-04 also gave "began as Hart's Hotel in 1814"; not checked, not used.) |
| UH-2 | D. C. Muirhead was proprietor in 1910. | Documented | P19 (caption) | The 1920 proprietor was not found. |
| UH-3 | Doors (white frame, fanlight, grey-green panelled doors) and other 1920s details. | Documented | P31, P07, P29 | Per the 2026-11-02 progress-log entry. |

### 2.10 Street ambiance, pass 1: street props and sound — in the scene

| ID | Claim | Grade | Sources | Method / note |
|----|-------|-------|---------|---------------|
| SA-1 | A granite horse/drinking fountain: rough-faced monolith with a rounded top, horse-head relief in an oval, round bowl, small arched niche (dog trough), iron holder with a white globe lamp on top. | Documented | P20, P08, P19, P32, P06, P16 | |
| SA-2 | Fountain sizes (1.05 × 0.65 × 1.95 m block, globe top 2.55 m). | Measured (estimate) | P20 | Scaling method not recorded. |
| SA-3 | It stood at the west curb in front of the County Offices. | Documented | W20 ("Clerk's Office", "Dentist" behind it), P20, P16 | Exact position (z −29.8) is a guess within ±3 m; the hotel cards suggest opposite the hotel centre. Donor and date unknown. |
| SA-4 | Wooden utility poles on both curbs, two crossarms with glass insulators, wires along and across the street. | Documented | P04, P10, P14, P21, P11, P23 | |
| SA-5 | Pole positions other than three (in front of 80–82 Main, before the County Offices, at the bank's Bloomfield corner); spacing ~30 m; 10.8 m height. | Guess (positions) / Measured (rough height) | P04, P14, P11 | Height scaled from the 3-storey fronts. |
| SA-6 | Bracket lamps on poles. | Documented | P04, P10, P14 | |
| SA-7 | An enclosed arc lamp hung over the street on a span wire. | Documented (1910) / Guess (still in 1920) | P25 | They may have been replaced by incandescent lamps by 1920. |
| SA-8 | The ornamental lamp standards in front of the hotel are late 1920s–30s, so not used. | Inferred | P31, P07, P29 | Dated by car styles. |
| SA-9 | Square stone posts ~1 m at the west curb are hitching posts. | Documented (posts) / Inferred (use) | P13, P18 | |
| SA-10 | Granite carriage-step blocks at the east curb at 78 Main. | Documented | P04, P10 | |
| SA-11 | Fire hydrants at the two Sanborn "T.H." spots (west curb at the courthouse; east curb at the N corner of Bloomfield Ave). | Documented | M1, M2, P28 | Hydrant type and dark red-brown colour are guesses. |
| SA-12 | Sanborn notes: "F.A." (fire-alarm box) at the courthouse steps; Main St water pipes 8" and 4"; "Light: Elec." on the Union Hotel and County Hotel. | Documented | M1 | F.A. box not modelled. |
| SA-13 | A curb gasoline pump in front of 100–102 Main ("Auto Supplies"). | Inferred | M2 ("500 gal gasol. tank buried") | Pump type and colour are guesses. |
| SA-14 | Crates and barrels at shop fronts; bicycles at the curb. | Documented | P11, P23, P28, P16 | |
| SA-15 | Sandwich boards at the curb. Lettering "GROCERIES" (84 Main) and "ICE CREAM · SODA" (66 Main). | Documented (boards) / Inferred (wording) | P04, P28; M1/M2 uses ("Gro.", "Conf'y") | Wording chosen from the map uses, not read from a board. |
| SA-16 | No flagpoles, benches, mailboxes or street-name signs. | Inferred | P01–P32 | None appear in the period photos. |
| SA-17 | Flemington Baptist Church (1867) at the south end of Main St; its spire shows in the 1907 card. | Documented | W21, P04 | |
| SA-18 | A church bell strikes five, from that church. | Guess / artistic | — | Not documented. |
| SA-19 | Sounds of horse-drawn wagons and Model T Fords. | Inferred | P08, P19 (Model T), P31, P07 | Period-typical. |
| SA-20 | Bird species heard (American robin, northern cardinal, tufted titmouse, gray catbird). | Guess / artistic | — | Common eastern US species; no Flemington record. |
| SA-21 | Street lighting system in 1920. | **Source not found** | — | Arc and pole lamps are from the 1907/1910 cards only. |

### 2.11 John B. Pickell, clerk at the Nevius store (78 Main St) — person in the scene

**About the person**

| ID | Claim | Grade | Sources | Method / note |
|----|-------|-------|---------|---------------|
| PI-1 | John B. Pickell was a real person who "went to the Nevius store as a clerk in 1895 at the age of 16" and was its manager "for the past 21 years" in 1945; 50 years with the store, 1895–1945. | Documented | W24, quoting W37 | Primary article not seen. |
| PI-2 | Born c. 1879. | Inferred | W24 | Age 16 in 1895. |
| PI-3 | In September 1920 he is about 41, a clerk of 25 years, not yet manager (manager from c. 1924). | Inferred | W24 | Arithmetic from 1945 − 21. |
| PI-4 | "Senior clerk". | Guess / artistic | — | Long service suggests seniority; no source. |
| PI-5 | Middle name (only "B."), family, opinions, voice, face. | **Not known** | — | Lines avoid them; the brief tells an AI version to say "I don't know". |
| PI-6 | A man in a dark suit stands at the door of this store in the 1907 and 1910s cards. | Documented | P04, P10 | That he is Pickell is **not known**; he is used as a model for clothing and spot. |
| PI-7 | The "business blocks" cards show 78 Main looking south. | Inferred | P04, P10 vs the 78 Main model | An earlier note in PLAN.md called them west-side blocks. |
| PI-8 | Clothing: dark sack suit with waistcoat, white collar, dark tie, bareheaded, moustache. | Documented (garment set) / Guess (colours, details) | P04, P10, W36 | Only ~75 px tall in the cards. |
| PI-9 | Charcoal suit, maroon tie, tape measure round the neck, pencil behind the ear, gold watch chain, height 1.72 m, greying hair. | Guess / artistic | — | |
| PI-10 | Scene day: a warm afternoon in early September 1920. | Guess / artistic | — | Chosen to fit leafy trees and the suffrage news. |
| PI-11 | Standing spot in front of the north display window. | Inferred | P04, P10 | Where the man in the cards stands. |

**What he says** (`data/dialogue/pickell.json`; node names in brackets)

| ID | Claim in the dialogue | Grade | Sources | Note |
|----|----------------------|-------|---------|------|
| PI-D1 | [start] "John Pickell, of the Nevius store." | Documented | W24 | |
| PI-D2 | [start] "Step in out of the sun… the door's open." | Guess / artistic | — | |
| PI-D3 | [goods] "Dry goods and notions, as the awning says." | Documented (1907 awning) | P04, P10, M2 | **The scene's awning has no lettering**, so "as the awning says" does not match what the visitor sees. |
| PI-D4 | [goods] Dress goods by the yard (gingham, percale, serge, silk), thread, buttons, ribbon, hosiery, ladies' coats. | Inferred / Guess | W26 (1917 "Dress Materials"), W27 (1901 ladies' jackets) | The particular fabrics and items are period-typical, not from a 1920 Nevius ad. |
| PI-D5 | [goods] "Everything costs near twice what it did before the war." | Documented | W35 | CPI ≈ 10.0 (1914) → ≈ 20 (mid-1920). |
| PI-D6 | [prices] "Wool and cotton went sky-high… The papers say prices may break before winter." | Inferred (rise) / Guess (what papers said) | W35 | Prices did fall from late 1920; no 1920 newspaper cited. |
| PI-D7 | [owner] "Mr. Jacob Nevius. He opened his first store here in Flemington in 1878, and he has the store over in Somerville too." | Documented (facts) / Inferred (owner in 1920) | W25 | W25: first store 1878, Somerville 1883, died 5 May 1926. The 1907 awning says "Nevius Bros", so the 1920 owner may be the brothers (Q1). |
| PI-D8 | [owner] "I came to work for him in 1895, a boy of sixteen… Twenty-five years this year." | Documented / Inferred (arithmetic) | W24 | "Rolling bolts of cloth" is a guess. |
| PI-D9 | [building] "There's been a store on this lot since before the Civil War." | Documented | W15 (before 1856) | |
| PI-D10 | [building] "Mr. Fulper had it before us; they say he gave it this brick front about 1880." | Inferred / simplified | W15 | W15 lists other occupants (Hall, Trewin & Rittenhouse; Trewin; Connet) between Fulper and the Nevius store. "Had it before us" skips them. |
| PI-D11 | [building] "You'll find my name pencilled on the wall — January 1896." | Documented | W24 | "Boys will be boys" is artistic. |
| PI-D12 | [town] "The Court House, built in 1828. The county jail is on the ground floor, under the courtroom." | Documented | W3, W2 | |
| PI-D13 | [town] "The county offices stand just beyond it. And next door to us is the Union Hotel." | Documented | M1, M2 | |
| PI-D14 | [town] "On court days it's full of lawyers and jurymen." | Guess / artistic | — | Plausible; not sourced. |
| PI-D15 | [dry] "The whole country went dry in January — it's in the Constitution now." | Documented | W33 | National Prohibition in force 17 Jan 1920. |
| PI-D16 | [dry] The hotel bar "not as it was"; cars lined up along the curb "of a Saturday evening". | Inferred / Guess | P31, P07 (1920s cars parked at the hotel) | Saturday detail is invented. |
| PI-D17 | [sights] "The Fair… held out at the fairgrounds since 1856." | Inferred | W29 | W29: fairgrounds bought 1856 by the Hunterdon County Agricultural Society. That the fair was held every year since then is our reading. |
| PI-D18 | [sights] "Trotting races, and automobile races these last few years." | Documented (auto racing from 1915) / Source not recorded (trotting) | W29 | |
| PI-D19 | [sights] "Come back for the Fair at the end of summer." | Guess / artistic | — | The 1920 Fair dates are not known; if it was late August/early September, the line may be off (Q12). |
| PI-D20 | [sights] "Fulper's pottery; they've made pottery in Flemington for over a hundred years." | Documented | W30, W31 | Pottery in Flemington since 1814; Fulper from 1860; Vasekraft 1909. |
| PI-D21 | [news] "New Jersey ratified the amendment back in February, and now it's the law of the land. Come November every woman in Hunterdon County can vote for President — Harding or Cox." | Documented | W34 | NJ ratified 9 Feb 1920; adopted Aug 1920; election 2 Nov 1920. "Every woman" is simplified (citizens 21 and over, registered). |
| PI-D22 | [bye] "Mind the motor cars at the Court Street corner." | Guess / artistic | — | Court St is 8 m south of his spot in the scene. |
| PI-D23 | [brief] Flemington has about 2,600 people. | Documented | W32 | 1920 census: 2,590. |

### 2.12 County Hotel (47–49 Main St) — spec written, awaiting owner approval

| ID | Claim | Grade | Sources | Method / note |
|----|-------|-------|---------|---------------|
| CY-1 | On the site of an 18th-century tavern (County Tavern; "County House" from 1855 under Jacob B. Smith). | Documented | W38, W11 | Not modelled; background only. |
| CY-2 | William H. Force bought it "not long after the Civil War" and called it "The County Hotel". | Documented | W38 | |
| CY-3 | Samuel H. Mount bought it from William H. and Hannah Force on 1 June 1891 for $25,000; c. 1905 it was "Mount's Hotel" (lettered lantern). | Documented | W38, G9 | |
| CY-4 | Sold in 1907, still as the County Hotel; buyer not named. | Documented | W38 | |
| CY-5 | Called "County Hotel" in September 1921, with "Heat: Steam", "Light: Elec.", and a 1-storey "Bar & Pool Room" wing behind. | Documented | M1 | Labels only; whether drink was served under Prohibition is not known. |
| CY-6 | The 1920 proprietor. | **Not known** | — | Searched 2026-11-04; nothing found. |
| CY-7 | Italianate style (c. 1850–70); exterior walls solid brick. | Documented | W38 (quoting architect Chris Pickell) | Conflicts with the Sanborn colour (frame), see CY-10. |
| CY-8 | Replaced in the 1970s by the "New Market" shops (Don Shuman); a sandstone slab lettered "County Hotel" was in the sidewalk. | Documented | W38 (text and reader comments) | |
| CY-9 | Main block 23.86 × 9.07 m, 3 storeys, 30 ft; 2-storey veranda 2.52 m deep across the whole front, its front on the property line; street numbers 47 and 49. | Measured / Documented | M1 (px x 3377–3551, y 4520–4978; veranda x 3551–3600) | Cornice top taken as 9.15 m. |
| CY-10 | Front and south walls marked grey "(Ir. Cl.)" (iron-clad) on a frame (yellow) building. | Documented (map) | M1 | Meaning for the 1920 look uncertain; not shown in the model. |
| CY-11 | A 1-storey canted bay at the rear of the south wall (4.4 m along the wall, 1.2 m out); Bar & Pool Room wing 14.4 m long behind; rear porches. | Measured | M1 | The c. 1905 photo shows a squarer projection there. |
| CY-12 | Three storeys with a flat roofline, deep cornice with closely spaced scroll brackets; 12 shuttered 2/2 windows on the 3rd floor front; 3 / 2 / 1 windows on the south side; two brick chimneys (south near the front, north end). | Documented | G9, P33, P34 | Window count ±1. |
| CY-13 | Veranda: 9 square posts per floor with long sunk "X" panels, diamond-lattice railing, bracketed porch cornice under the 3rd-floor windows; floor = the paved walk. | Documented | G9, P34, P33 | |
| CY-14 | Floor levels and sizes (2nd floor ≈ 3.05 m, 3rd ≈ 6.15 m, porch deck 3.10 m, porch cornice 6.40 m, window sizes). | Measured (photo estimate) | G9 (≈ 63 px/m at the SE corner, cornice top = 9.15 m), M1 | ±0.2 m. |
| CY-15 | North-end veranda bay enclosed on both floors, glazed upstairs. | Documented (1906) / Inferred (1920) | P35, P33 | |
| CY-16 | Walls: red brick c. 1905–06; pale (painted) by 1908. The model uses pale cream-buff paint. | Documented (photos) / Inferred (1920) | G9, P33 (red, tinted), P34 (pale) | Owner may choose red brick. |
| CY-17 | Shutters dark green, trim off-white. | Inferred | P33 (tinted green shutters), P34 | Tinted card is weak colour evidence. |
| CY-18 | A cast-iron lamp standard with a lettered lantern (eagle finial) at the south end of the veranda. | Documented (c. 1905–08) / Guess (1920) | G9, P33, P34 | Lantern read "MOUNT'S HOTEL" c. 1905; **"COUNTY HOTEL" lettering in the model is a guess**. W38 names the man beside it as Cornelius "Dutchy" Tunison (billiard tables; died Aug 1906). |
| CY-19 | Ground-floor openings (display window and door in the south bay, double main door in bay 3), 2nd-floor door/window pattern, north and rear walls, roof form, chimney positions, wing details. | Guess / artistic (partly Inferred from G9) | G9 (partial) | |
| CY-20 | No local reference photo or HABS photo shows the hotel. | Documented (search result) | P01–P32, H1–H3 checked | |

---

## 3. Known uncertainties / questions for the Historical Society

Ordered roughly by how much the answer would change the walk.

1. **Nevius store, 1895–1920.** Goodspeed [W15] lists Andrew T. Connet at 78 Main from 1897
   (died 1913) and says the Nevius family "took possession… in the 1930s". But the 1907 awning
   reads "Nevius Bros" [P04], a 1909 card is titled "Nevius Store" [P26], and John B. Pickell
   joined "the Nevius store" in 1895 [W24]. Who ran 78 Main in 1920: Jacob Nevius, Nevius
   Brothers, or someone else? Was the Nevius store elsewhere in 1895?
2. **John B. Pickell.** Is there a portrait? What is his middle name? Can the *Whitehouse Review*
   article of 17 April 1945 [W37] be confirmed? Was he a clerk or already a senior man in 1920?
   Is the architect "C. Pickell" quoted in [W15] related to him?
3. **Courthouse c. 1920.** When were the paired scroll brackets replaced by plain modillions,
   and when was the pediment changed from two windows to 3 + 2? What were the roof (slate or
   painted tin) and the wall paint colour? How many chimneys were there?
4. **65 Main St (old no. 510).** Any photo of its **front**; who owned or lived in it c. 1920;
   when it was built and when it was demolished. Every front detail in the scene is a guess.
5. **Hall of Records, 1920.** What did the stone panel under the north upper window say (it read
   "DENTIST" in 1909–12)? Were there awnings, and what were the roof and trim colours? Was it
   built in 1870 or 1871?
6. **Wurts / Southard Law Office.** Who used it in 1920, and did it have a sign? Was the Greek
   Revival remodel c. 1830 (HABS) or 1840 (HCHS)? When was the rear T-wing added? Was it the
   Women's Club that opened the restroom in the late 1920s?
7. **Bank Building shops, 1920.** Names of the men's furnishings, drug, boots & shoes and
   confectionery businesses (Sanborn 1921), what their signs and awnings looked like, and how
   the entrances looked after the changes the HCHS mentions.
8. **Rea Building, 1920.** Where the Post Office moved before 1921; the names of the cobbler,
   the jeweler and the club in the club rooms; whether the "Green's Apothecary" awning was still
   there; cupola and clock-dial colours.
9. **Lovell's Restaurant.** Paint colours (one 1908 card shows a tan side wall), sign colours and
   lettering style c. 1920; anything known about Fred Lovell.
10. **Street lighting and utilities.** Were the hanging arc lamps still in use in 1920, or
    replaced? Where did the poles stand? What colour were the hydrants?
11. **Horse fountain.** Who gave it, when, and exactly where it stood (in front of the County
    Offices, or opposite the hotel?).
12. **The 1920 Hunterdon County Fair.** Its dates (Pickell says "come back for the Fair at the
    end of summer" on an early-September day), and whether trotting races were held.
13. **Union Hotel.** Who was the proprietor in 1920? (D. C. Muirhead is named in 1910.)
14. **Gas pump.** Did a curb gasoline pump stand in front of 100–102 Main ("Auto Supplies") in
    1920? Sanborn sheet 3 shows only a buried tank.
15. **Nevius awning, 1920.** Did it still carry the "Dry Goods · Nevius Bros · Notions"
    lettering? (The model has a plain awning, but Pickell refers to the lettering.)
16. **County Hotel, 1920.** Who ran it in 1920 (after the 1907 sale)? Were the walls painted, red
    brick, or sheathed in sheet iron (Sanborn 1921 "Ir. Cl.")? Did the lamp standard still stand,
    and what did the lantern say? Are there photos of it from 1910–1930?

### Internal inconsistencies noted while compiling (for the project, not the Society)

- Pickell says "as the awning says", but the Nevius model's awning has no lettering (NE-5, PI-D3).
- The courthouse owner decision says to model the "F.A." fire-alarm post; the street-props spec
  left it out (CH-28, SA-12).
- The courthouse spec text still mentions iron window bars "(guess)"; the owner decision removed
  them (CH-22).
- [P17] is captioned "c 1910" in the gallery but called "c. 1908" in PLAN.md.
- The HABS number for the Union Hotel (NJ-732 in PLAN.md) has not been checked.
