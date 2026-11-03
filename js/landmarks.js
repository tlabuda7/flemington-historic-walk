/*
 * landmarks.js — buildings modelled from the 1921 Sanborn map and period photos.
 *
 * Usage:
 *   <a-entity id="union-hotel" position="11.6 0 -30.75" rotation="0 -90 0"
 *             kit-building="type: union-hotel"></a-entity>
 *
 * Like the placeholder `building` component, the entity's position is the centre of
 * the building's FRONT LINE at ground level, and the front faces local +Z.
 * Dimensions come from the map (sheet 2, 1921) unless a comment says "guess".
 *
 * Types:
 *   union-hotel     Union Hotel, 70–76 Main St (east side)
 *   courthouse      Hunterdon County Court House, 75 Main St (west side)
 *   county-offices  County office building, 69–71 Main St (west side)
 *   law-office      Alexander Wurts law office, 59 Main St (west side)
 *   house           A generic 2–2½ storey frame house with a front porch.
 *                   Takes width, depth, stories, color, trim, roof, porch, porchWidth.
 */

const DARK = '#2a2622'; // door and window openings

const KIT_TYPES = {

  /* ---------------------------------------------------------------- */
  /* Union Hotel                                                       */
  /* Map: 97 ft frontage, 4 storeys, brick, two-storey frame veranda.   */
  /* Photos: mansard roof with dormers, taller end towers, curved      */
  /* central pavilion lettered "UNION HOTEL", arched upper gallery.    */
  /* ---------------------------------------------------------------- */
  'union-hotel'(b) {
    const W = 29.7;          // frontage along Main Street (m)
    const D = 8.6;           // depth of the main block
    const front = -3.0;      // brick front wall, set back behind the veranda
    const plinth = 0.8;      // raised ground floor
    const floorH = 3.6;
    const wallTop = plinth + 3 * floorH;   // top of the brick walls
    const roofBase = wallTop + 0.5;        // top of the cornice
    const bays = 11;
    const bay = W / bays;
    const midZ = front - D / 2;

    const brick = kitMaterial('#8a3d2c');
    const trim = kitMaterial('#efe7d6');
    const slate = kitMaterial('#57605f');
    const stone = kitMaterial('#a59c8c');
    const boards = kitMaterial('#8d867a');

    // Main block and the rear wing (wing is offset north, per the map).
    b.block(brick, W, wallTop, D, 0, midZ);
    b.block(brick, 6.8, 10.8, 10.3, -2.35, front - D - 5.15);

    // Front wall: 11 bays x 3 floors of arched windows.
    const windows = new THREE.MeshStandardMaterial({
      map: makeWindowBayTexture('#8a3d2c', '#efe7d6', 'brick', bays, 3, 'arched'), roughness: 0.9
    });
    b.panel(windows, W, wallTop - plinth, 0, plinth + (wallTop - plinth) / 2, front + 0.02);

    // Cornice and mansard roof.
    b.box(trim, W + 0.4, 0.5, D + 0.4, 0, wallTop + 0.25, midZ);
    b.mansard(slate, W, D, 3.6, 1.0, 0, midZ, roofBase);
    b.block(trim, W - 1.8, 0.15, D - 1.8, 0, midZ, roofBase + 3.6);

    // Dormers share one texture: white face with a window.
    const dormerFace = new THREE.MeshStandardMaterial({
      map: makeWindowBayTexture('#efe7d6', '#efe7d6', 'plain', 1, 1, 'arched'), roughness: 0.9
    });
    const dormer = (x, yBottom, h) => {
      b.block(slate, 1.3, h, 1.0, x, front - 0.6, yBottom);
      b.panel(dormerFace, 1.2, h, x, yBottom + h / 2, front - 0.09);
      b.arch(trim, 0.68, 1.1, x, yBottom + h, front - 0.6); // round hood
    };
    for (const i of [1, 2, 3, 7, 8, 9]) dormer(-W / 2 + bay * (i + 0.5), roofBase + 0.5, 1.7);

    // End towers: taller, steeper mansards over the end bays.
    for (const s of [-1, 1]) {
      const tx = s * (W / 2 - 1.6);
      b.mansard(slate, 3.2, D, 5.0, 0.45, tx, midZ, roofBase);
      b.block(trim, 2.6, 0.3, D - 0.6, tx, midZ, roofBase + 5.0);
      dormer(tx, roofBase + 1.6, 1.9);
    }

    // Central pavilion with a curved top and the hotel's name.
    b.block(slate, 5.2, 3.4, 3.0, 0, front - 1.55, roofBase);
    b.arch(slate, 2.6, 3.0, 0, roofBase + 3.4, front - 1.55);
    b.arch(trim, 2.75, 0.2, 0, roofBase + 3.4, front - 0.3); // trim edge, just behind the face
    const sign = new THREE.MeshStandardMaterial({ map: makeSignTexture('UNION HOTEL'), roughness: 0.8 });
    b.panel(sign, 4.2, 0.8, 0, roofBase + 2.85, front - 0.02);
    b.panel(dormerFace, 2.6, 2.0, 0, roofBase + 1.3, front - 0.02);

    // Chimneys.
    for (const x of [-8.5, 8.5]) b.block(brick, 0.8, 2.4, 0.8, x, midZ - 1, roofBase + 3.0);

    // Veranda: foundation, floor, steps down to the sidewalk.
    b.block(brick, W, plinth - 0.2, 3.0, 0, -1.5);
    b.block(boards, W, 0.2, 3.0, 0, -1.5, plinth - 0.2);
    b.steps(stone, W - 2, plinth, 3, 0.43, 0, 0);

    // Twelve posts on each level, 11 spans between them.
    const posts = [];
    for (let i = 0; i < 12; i++) posts.push(-W / 2 + 0.25 + i * (W - 0.5) / 11);
    const galleryFloor = plinth + 3.6 + 0.45;          // top of the gallery floor
    posts.forEach((x) => b.column(trim, 0.13, 3.6, x, -0.3, plinth, 8));
    b.box(trim, W, 0.45, 3.0, 0, plinth + 3.6 + 0.225, -1.5);
    posts.forEach((x) => b.column(trim, 0.11, 3.0, x, -0.3, galleryFloor, 8));

    // Gallery railing and the row of arches under the porch roof.
    const rail = kitCutoutMaterial(makeBalustradeTexture('#efe7d6', Math.round(W / 0.9)));
    b.panel(rail, W, 0.95, 0, galleryFloor + 0.475, -0.3);
    const arcade = kitCutoutMaterial(makeArcadeTexture('#efe7d6', 11));
    b.panel(arcade, W - 0.5, 1.1, 0, galleryFloor + 3.0 - 0.55, -0.29);
    b.box(trim, W + 0.3, 0.35, 3.3, 0, galleryFloor + 3.0 + 0.175, -1.5);
  },

  /* ---------------------------------------------------------------- */
  /* Hunterdon County Court House (built 1828)                         */
  /* Map: stone, 2 storeys, 30 ft high, 44 ft wide, frame portico.     */
  /* Photos: four giant columns, pediment, octagonal domed cupola.     */
  /* ---------------------------------------------------------------- */
  courthouse(b) {
    const W = 13.5;          // width of the front
    const depth = 20.8;      // depth of the stone body
    const portico = 4.7;     // depth of the portico in front of the body
    const H = 9.1;           // wall height (30 ft)
    const podium = 1.0;      // portico floor height
    const total = depth + portico;

    const stucco = kitMaterial('#d6cebb');   // walls, a shade darker than the trim
    const trim = kitMaterial('#fbf8f1');     // columns, entablature, pediment
    const stone = kitMaterial('#bdb5a5');
    const roof = kitMaterial('#6a6865');
    const metal = kitMaterial('#8a918c', 0.6);
    const dark = kitMaterial(DARK);
    const roofH = 3.3;       // pediment height (photos show a low pitch)

    // Podium, steps and the main body.
    b.block(stone, W, podium, portico, 0, -portico / 2);
    b.steps(stone, W - 0.6, podium, 4, 0.5, 0, 0);
    b.block(stucco, W, H, depth, 0, -portico - depth / 2);

    // Front wall behind the columns: 3 bays x 2 floors, arched centre door.
    const windows = new THREE.MeshStandardMaterial({
      map: makeWindowBayTexture('#d6cebb', '#fbf8f1', 'plain', 3, 2, 'sash'), roughness: 0.9
    });
    const wallH = H - podium - 1.0;
    b.panel(windows, W - 1.0, wallH, 0, podium + wallH / 2, -portico + 0.02);
    b.panel(dark, 1.6, 2.4, 0, podium + 1.2, -portico + 0.04);
    b.arch(dark, 0.8, 0.02, 0, podium + 2.4, -portico + 0.04);

    // Four columns with simple bases and capitals.
    for (let i = 0; i < 4; i++) {
      const x = -(W / 2 - 0.7) + i * (W - 1.4) / 3;
      b.block(trim, 1.15, 0.35, 1.15, x, -0.7, podium);
      b.column(trim, 0.5, 7.2, x, -0.7, podium + 0.35, 12);
      b.block(trim, 1.2, 0.35, 1.2, x, -0.7, podium + 7.55);
    }

    // Entablature round the whole building, gable roof, and the pediment.
    const eaves = podium + 7.9;
    b.box(trim, W + 0.4, 0.9, total + 0.4, 0, eaves + 0.45, -total / 2);
    const roofBase = eaves + 0.9;
    b.gable(roof, W + 0.8, roofH, total + 0.8, 0, -total / 2, roofBase);
    b.gable(trim, W + 0.2, roofH * (W + 0.2) / (W + 0.8), 0.1, 0, 0.42, roofBase);
    for (const x of [-2.0, 2.0]) b.panel(dark, 0.8, 1.0, x, roofBase + 1.0, 0.48);

    // Cupola: square base, octagonal drum, dome and finial.
    const cz = -6;
    b.block(trim, 3.4, 1.6, 3.4, 0, cz, roofBase + roofH - 0.9);
    b.cylinder(trim, 1.6, 2.2, 0, roofBase + roofH + 1.8, cz, 8);
    b.cylinder(trim, 1.8, 0.25, 0, roofBase + roofH + 3.0, cz, 8);
    b.dome(metal, 1.65, 0, cz, roofBase + roofH + 3.1);
    b.cylinder(metal, 0.06, 1.4, 0, roofBase + roofH + 5.3, cz, 6);
  },

  /* ---------------------------------------------------------------- */
  /* County office building, 69–71 Main St                             */
  /* Map: brick, 2 storeys, 28 ft high. Photos: bracketed cornice,     */
  /* arched windows, curved central gable, stoops to the street.       */
  /* ---------------------------------------------------------------- */
  'county-offices'(b) {
    const W = 15.4, D = 15.1, H = 8.5, base = 1.0;

    const brick = kitMaterial('#9a4a35');
    const stone = kitMaterial('#b3a995');
    const cornice = kitMaterial('#5d4b3d');
    const roof = kitMaterial('#5e605d');
    const dark = kitMaterial(DARK);

    b.block(brick, W, H, D, 0, -D / 2);
    b.block(stone, W + 0.1, base, D + 0.1, 0, -D / 2);

    const windows = new THREE.MeshStandardMaterial({
      map: makeWindowBayTexture('#9a4a35', '#e9dfca', 'brick', 5, 2, 'arched'), roughness: 0.9
    });
    b.panel(windows, W, H - base - 0.3, 0, base + (H - base - 0.3) / 2, 0.03);

    // Bracketed cornice and low hipped roof.
    b.box(cornice, W + 0.7, 0.6, D + 0.7, 0, H + 0.3, -D / 2);
    b.mansard(roof, W + 0.4, D + 0.4, 1.6, 4.0, 0, -D / 2, H + 0.6);

    // Curved central gable with a round window.
    b.arch(cornice, 2.85, 0.5, 0, H + 0.6, -0.05);
    b.arch(brick, 2.6, 0.6, 0, H + 0.6, 0.0);
    b.add(dark, new THREE.CircleGeometry(0.45, 12).translate(0, H + 1.7, 0.31));

    // Centre door and stoop.
    b.panel(dark, 1.3, 2.5, 0, base + 1.25, 0.05);
    b.steps(stone, 2.2, base, 3, 0.35, 0, 0);
  },

  /* ---------------------------------------------------------------- */
  /* Alexander Wurts law office, 59 Main St                            */
  /* Map: 1-storey frame office set back from the street.              */
  /* HABS photo: Greek Revival temple front, four square pillars,      */
  /* deep entablature, window-door-window behind the porch.            */
  /* ---------------------------------------------------------------- */
  'law-office'(b) {
    const W = 4.6, porch = 1.8, D = 6.8, wallH = 3.8, floor = 0.35;

    const white = kitMaterial('#f1ede4');
    const trim = kitMaterial('#fbf8f1');
    const roof = kitMaterial('#5c5a57');
    const boards = kitMaterial('#9b968c');
    const brick = kitMaterial('#8a4a38');
    const dark = kitMaterial(DARK);

    b.block(white, W, wallH, D, 0, -porch - D / 2);
    const windows = new THREE.MeshStandardMaterial({
      map: makeWindowBayTexture('#f1ede4', '#fbf8f1', 'wood', 2, 1, 'sash'), roughness: 0.9
    });
    b.panel(windows, W, wallH - floor - 0.2, 0, floor + (wallH - floor - 0.2) / 2, -porch + 0.02);
    b.panel(dark, 1.0, 2.3, 0, floor + 1.15, -porch + 0.04);

    // Porch floor, step and four square pillars.
    b.block(boards, W + 0.2, floor, porch, 0, -porch / 2);
    b.block(boards, W * 0.6, floor / 2, 0.35, 0, 0.175);
    for (const x of [-1.95, -0.65, 0.65, 1.95]) b.block(trim, 0.32, wallH - floor, 0.32, x, -0.25, floor);

    // Deep entablature over porch and body, low roof, chimney.
    const zMid = -(porch + D) / 2 + 0.15;
    b.box(trim, W + 0.3, 1.1, porch + D + 0.3, 0, wallH + 0.55, zMid);
    b.mansard(roof, W + 0.3, porch + D + 0.3, 0.8, 1.6, 0, zMid, wallH + 1.1);
    b.block(brick, 0.55, 1.6, 0.55, 0, -5.5, wallH + 0.9);
  },

  /* ---------------------------------------------------------------- */
  /* Generic frame house with a front-facing gable and a porch.        */
  /* ---------------------------------------------------------------- */
  house(b, d) {
    const W = d.width, D = d.depth, base = 0.6, storyH = 3.0;
    const H = base + d.stories * storyH;
    const roofH = W * 0.42;

    const wall = kitMaterial(d.color);
    const trim = kitMaterial(d.trim);
    const roof = kitMaterial(d.roof);
    const stone = kitMaterial('#a59c8c');
    const boards = kitMaterial('#8d867a');
    const brick = kitMaterial('#8a4a38');
    const dark = kitMaterial(DARK);

    b.block(wall, W, H, D, 0, -D / 2);
    b.block(stone, W + 0.05, base, D + 0.05, 0, -D / 2);
    const windows = new THREE.MeshStandardMaterial({
      map: makeWindowBayTexture(d.color, d.trim, 'wood', Math.max(2, Math.round(W / 2.6)), d.stories, 'sash'),
      roughness: 0.9
    });
    b.panel(windows, W, H - base, 0, base + (H - base) / 2, 0.02);
    b.panel(dark, 1.0, 2.2, d.porchX, base + 1.1, 0.04);

    // Front-gable roof with eaves, siding in the gable, attic window, chimney.
    b.box(trim, W + 0.6, 0.12, D + 0.4, 0, H + 0.06, -D / 2 + 0.2);
    b.gable(roof, W + 0.6, roofH, D + 0.4, 0, -D / 2 + 0.2, H);
    b.gable(wall, W, roofH * W / (W + 0.6), 0.1, 0, 0.45, H);
    b.panel(dark, 0.9, 1.1, 0, H + roofH * 0.35, 0.51);
    b.block(brick, 0.6, roofH + 1.0, 0.6, W * 0.25, -D * 0.6, H + roofH * 0.3);

    if (!d.porch) return;
    const pw = d.porchWidth || W, px = d.porchX, pd = 2.4, postH = 2.7;
    b.block(boards, pw, base, pd, px, pd / 2);
    const n = Math.max(2, Math.round(pw / 2.2) + 1);
    for (let i = 0; i < n; i++) {
      b.block(trim, 0.16, postH, 0.16, px - pw / 2 + 0.15 + i * (pw - 0.3) / (n - 1), pd - 0.15, base);
    }
    b.box(roof, pw + 0.3, 0.14, pd + 0.3, px, base + postH + 0.07, pd / 2);
    b.box(trim, pw + 0.3, 0.3, 0.06, px, base + postH - 0.05, pd + 0.15);

    // Railings either side of the steps.
    const seg = (pw - 0.3 - 1.4) / 2;
    if (seg > 0.4) {
      const rail = kitCutoutMaterial(makeBalustradeTexture(d.trim, Math.max(1, Math.round(seg / 0.9))));
      for (const s of [-1, 1]) b.panel(rail, seg, 0.8, px + s * (0.7 + seg / 2), base + 0.4, pd - 0.15);
    }
    b.steps(stone, 1.4, base, 2, 0.35, px, pd);
  }
};

AFRAME.registerComponent('kit-building', {
  schema: {
    type:       { default: 'house', oneOf: Object.keys(KIT_TYPES) },
    // The options below are used by the 'house' type.
    width:      { default: 8 },
    depth:      { default: 10 },
    stories:    { default: 2 },
    color:      { type: 'color', default: '#e3dccb' },
    trim:       { type: 'color', default: '#f6f2ea' },
    roof:       { type: 'color', default: '#55575a' },
    porch:      { default: true },
    porchWidth: { default: 0 },   // 0 = full width of the house
    porchX:     { default: 0 }    // porch centre, relative to the house centre
  },

  update() {
    this.remove();
    const builder = new KitBuilder();
    KIT_TYPES[this.data.type](builder, this.data);
    this.el.setObject3D('mesh', builder.build());
  },

  remove() {
    const group = this.el.getObject3D('mesh');
    if (!group) return;
    disposeKitGroup(group);
    this.el.removeObject3D('mesh');
  }
});
