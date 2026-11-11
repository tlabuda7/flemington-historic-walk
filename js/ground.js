/* ------------------------------------------------------------------ */
/* street-ground                                                       */
/* ------------------------------------------------------------------ */
/*
 * The street's ground: road, sidewalks, curbs, grass strips and lane mouths, built from
 * the outlines measured on the 1921 Sanborn map (PLAN.md, "Street details pass 2",
 * sections 2, 3 and 9). One merged mesh per texture, so the whole ground costs 7 draw calls:
 *
 *   road      oiled earth-and-stone with wheel tracks, crowned (middle 10 cm higher)
 *   concrete  concrete walks
 *   flags     bluestone flag walks (east side north of the Rea Building, west side at
 *             35-41 Main and the County Hotel)
 *   brick     brick crossing at the Palace alley, brick patch by 38-40 Main
 *   curb      stone curbs, dropped at the lane mouths
 *   soft      grass strips / yards and bare-earth lanes (one neutral map x vertex colour)
 *   decals    a few horse droppings and paper scraps, curved wheel tracks at the junctions
 *
 * All numbers are scene metres: x across the street (east = +x), z along it (north = -z).
 * "Road edge" = the street face of the curb; the curb is the first 0.24 m of the walk.
 * Textures come from tools/prepare_ground_textures.py (assets/textures/ground/).
 *
 * Also here: STREET_GROUND.limits(z), the walkable x range the `locomotion` component uses,
 * and `box-group`, a few plain boxes drawn as one mesh (a placeholder porch).
 */
(function () {
  const Y_ROAD = 0.01;      // road surface at the curbs
  const CROWN = 0.10;       // the middle of the road is this much higher
  const Y_WALK = 0.15;      // sidewalk top
  const Y_CURB = 0.16;      // curb top
  const CURB_W = 0.24;
  const DROP = 0.11;        // how far a dropped curb sinks (leaves a 5 cm lip)
  const RAMP = 1.0;         // depth of the sloping apron behind a dropped curb
  const Y_SKIRT = -0.05;    // side faces of the walks reach below the ground
  const ROAD_TILE = 6.4;    // road texture: 6.4 m, U = 0 on the crown

  /* Piecewise-straight line x(z) through [z, x] points (sorted by z). */
  function line(points) {
    const fn = (z) => {
      if (z <= points[0][0]) return points[0][1];
      for (let i = 1; i < points.length; i++) {
        if (z <= points[i][0]) {
          const [z0, x0] = points[i - 1];
          const [z1, x1] = points[i];
          return x0 + (x1 - x0) * (z - z0) / (z1 - z0);
        }
      }
      return points[points.length - 1][1];
    };
    fn.breaks = points.map((p) => p[0]);
    return fn;
  }
  const constant = (x) => line([[-999, x], [999, x]]);

  // Road edges and the crown line (section 9.2 / 9.4). The west edge is drawn straight across
  // the mouth of Court St (z -1.5 ... 10.2), where the curb line shifts 1.85 m east.
  const WEST_EDGE = line([[-180, -6.40], [-1.5, -6.40], [10.2, -4.55], [65, -4.24], [80, -4.19]]);
  const EAST_EDGE = line([[-180, 3.51], [-89.9, 6.40], [80, 6.40]]);
  const CROWN_X = line([[-180, -1.45], [-89.9, 0], [0, 0], [10.4, 0.93], [65, 1.08], [80, 1.08]]);
  const WEST_BACK_S = line([[10.4, -8.15], [65, -7.84], [80, -7.76]]);   // property line south of Court St

  // Lane mouths with a dropped curb, z from ... to (section 3). Three east-side mouths are cut
  // short so that pole E3 (z -46.5), pole E2 (z -15.5) and carriage step C2 (z 1.6) keep
  // standing on a full-height curb.
  const MOUTHS = {
    W: [[-139.2, -135.9],      // Palace alley (brick crossing)
        [-100.1, -94.5]],      // blacksmith's lane 49 1/2
    E: [[-140.9, -137.8],      // lane at 32
        [-124.2, -121.5],      // carriageway 40 (sloping stone apron)
        [-49.1, -47.2],        // gap 68 / Union Hotel (map: to -45.6)
        [-14.8, -11.3],        // gap hotel / Nevius (map: from -15.9)
        [-3.3, 0.6],           // alley 80 (map: to 1.3)
        [16.9, 21.7]]          // alley 86
  };
  function dropLine(mouths) {
    const pts = [[-999, 0]];
    mouths.forEach(([a, b]) => pts.push([a - 0.5, 0], [a, 1], [b, 1], [b + 0.5, 0]));
    pts.push([999, 0]);
    return line(pts);
  }
  const DROPS = { W: dropLine(MOUTHS.W), E: dropLine(MOUTHS.E) };

  /* Height of the road surface at (x, z): a shallow arch between the two curbs. */
  function roadY(x, z) {
    const c = CROWN_X(z);
    const half = x < c ? c - WEST_EDGE(z) : EAST_EDGE(z) - c;
    const t = Math.max(-1, Math.min(1, (x - c) / half));
    return Y_ROAD + CROWN * (1 - t * t);
  }

  /* How far east / west the visitor may walk at z (replaces the single boundsX). */
  function limits(z) {
    let max = 10.2;
    if (z < -141) max = 7.0;                 // 24-30 Main (front 7.29 when built)
    else if (z < -137.6) max = 7.3;          // lane at 32
    else if (z < -124.05) max = 8.25;        // 32-38 porch front 8.54
    else if (z < -105.8) max = 8.3;          // 44-46 front 8.60
    else if (z < -89.9) max = 9.35;          // Rea Building steps reach 9.65
    const min = z > 10.4 ? -7.85 : -10.2;    // 79-97 Main stand on the 53 ft line
    return { min, max };
  }

  window.STREET_GROUND = { roadY, limits, WEST_EDGE, EAST_EDGE, CROWN_X };

  /* ---------------- mesh building helpers ---------------- */

  class Group {
    constructor() { this.pos = []; this.uv = []; this.col = []; this.idx = []; }
    vert(x, y, z, u, v, c) {
      this.pos.push(x, y, z);
      this.uv.push(u, v);
      const k = c || [1, 1, 1, 1];
      this.col.push(k[0], k[1], k[2], k.length > 3 ? k[3] : 1);
      return this.pos.length / 3 - 1;
    }
    /* Triangle; `up` turns it so that it faces the sky. */
    tri(a, b, c, up) {
      if (up) {
        const p = this.pos;
        const ux = p[b * 3] - p[a * 3], uz = p[b * 3 + 2] - p[a * 3 + 2];
        const vx = p[c * 3] - p[a * 3], vz = p[c * 3 + 2] - p[a * 3 + 2];
        if (uz * vx - ux * vz < 0) { const t = b; b = c; c = t; }
      }
      this.idx.push(a, b, c);
    }
    quad(a, b, c, d, up) { this.tri(a, b, c, up); this.tri(a, c, d, up); }
    geometry() {
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.Float32BufferAttribute(this.pos, 3));
      geo.setAttribute('uv', new THREE.Float32BufferAttribute(this.uv, 2));
      geo.setAttribute('color', new THREE.Float32BufferAttribute(this.col, 4));
      geo.setIndex(this.idx);
      geo.computeVertexNormals();
      return geo;
    }
  }

  /* Sorted, de-duplicated z stations between z0 and z1 from the lines' corner points. */
  function stations(z0, z1, fns, step) {
    const zs = [z0, z1];
    fns.forEach((f) => (f.breaks || []).forEach((z) => { if (z > z0 && z < z1) zs.push(z); }));
    if (step) for (let z = Math.ceil(z0 / step) * step; z < z1; z += step) if (z > z0) zs.push(z);
    zs.sort((a, b) => a - b);
    return zs.filter((z, i) => i === 0 || z - zs[i - 1] > 0.01);
  }

  /* Flat polygon from an outline [[x, z], ...] at height y, with side faces if skirt. */
  function polygon(g, outline, y, tile, opt) {
    opt = opt || {};
    const uv = opt.uv || ((x, z) => [x / tile[0], z / tile[1]]);
    const pts = outline.map((p) => new THREE.Vector2(p[0], p[1]));
    const faces = THREE.ShapeUtils.triangulateShape(pts, []);
    const ids = outline.map((p) => { const t = uv(p[0], p[1]); return g.vert(p[0], y, p[1], t[0], t[1], opt.color); });
    faces.forEach((f) => g.tri(ids[f[0]], ids[f[1]], ids[f[2]], true));
    if (!opt.skirt) return;
    outline.forEach((p, i) => {
      const q = outline[(i + 1) % outline.length];
      const a = g.vert(p[0], y, p[1], 0, 0, opt.color), b = g.vert(q[0], y, q[1], 0.3, 0, opt.color);
      const c = g.vert(q[0], Y_SKIRT, q[1], 0.3, 0.07, opt.color), d = g.vert(p[0], Y_SKIRT, p[1], 0, 0.07, opt.color);
      g.quad(a, b, c, d);
    });
  }
  const rect = (g, x0, x1, z0, z1, y, tile, opt) =>
    polygon(g, [[x0, z0], [x1, z0], [x1, z1], [x0, z1]], y, tile, opt);

  /*
   * A stretch of sidewalk between z0 and z1: from the road edge `front(z)` back to `back(z)`.
   * side 'W' or 'E'. Behind a dropped curb the first metre slopes down to the curb (the apron).
   */
  function walk(g, side, z0, z1, front, back, tile, opt) {
    opt = opt || {};
    const s = side === 'W' ? -1 : 1;
    const drop = opt.flat ? constant(0) : DROPS[side];
    const zs = stations(z0, z1, [front, back, drop]);
    const rows = zs.map((z) => {
      const f = front(z), b = back(z);
      const cols = opt.flat ? [[f, Y_WALK], [b, Y_WALK]]
        : [[f, Y_WALK - DROP * drop(z)], [f + s * RAMP, Y_WALK], [b, Y_WALK]];
      return cols.map(([x, y]) => g.vert(x, y, z, x / tile[0], z / tile[1], opt.color));
    });
    for (let i = 1; i < rows.length; i++) {
      for (let j = 1; j < rows[i].length; j++) {
        g.quad(rows[i - 1][j - 1], rows[i - 1][j], rows[i][j], rows[i][j - 1], true);
      }
    }
    // Side faces: along the back edge and across both ends.
    const side4 = (xa, za, xb, zb) => {
      const a = g.vert(xa, Y_WALK, za, 0, 0, opt.color), b = g.vert(xb, Y_WALK, zb, 0.3, 0, opt.color);
      const c = g.vert(xb, Y_SKIRT, zb, 0.3, 0.07, opt.color), d = g.vert(xa, Y_SKIRT, za, 0, 0.07, opt.color);
      g.quad(a, b, c, d);
    };
    for (let i = 1; i < zs.length; i++) side4(back(zs[i - 1]), zs[i - 1], back(zs[i]), zs[i]);
    side4(front(z0), z0, back(z0), z0);
    side4(front(z1), z1, back(z1), z1);
  }

  /* Points along a road edge from zA to zB (either direction), with the curb drop at each. */
  function edgePoints(side, zA, zB) {
    const edge = side === 'W' ? WEST_EDGE : EAST_EDGE;
    const zs = stations(Math.min(zA, zB), Math.max(zA, zB), [edge, DROPS[side]]);
    if (zA > zB) zs.reverse();
    return zs.map((z) => [edge(z), z, DROPS[side](z)]);
  }

  /*
   * Curb along a line of [x, z, drop] points: a 0.24 m strip on the walk side (the left-hand
   * side when the walk is on the left; all the lists below are ordered that way) and the
   * face down to the road.
   */
  function curb(g, pts) {
    const n = pts.length;
    const normals = [];
    for (let i = 0; i < n - 1; i++) {
      const dx = pts[i + 1][0] - pts[i][0], dz = pts[i + 1][1] - pts[i][1];
      const len = Math.hypot(dx, dz);
      normals.push([-dz / len, dx / len]);
    }
    let dist = 0;
    const rows = pts.map((p, i) => {
      const a = normals[Math.max(0, i - 1)], b = normals[Math.min(n - 2, i)];
      let nx = a[0] + b[0], nz = a[1] + b[1];
      const len = Math.hypot(nx, nz);
      nx /= len; nz /= len;
      const w = CURB_W / Math.max(0.5, nx * a[0] + nz * a[1]);   // mitred corner
      if (i > 0) dist += Math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]);
      const y = Y_CURB - DROP * (p[2] || 0);
      const u = dist / 8;
      return [
        g.vert(p[0], y, p[1], u, 0.05),                       // top, street side
        g.vert(p[0] + nx * w, y, p[1] + nz * w, u, 0.95),     // top, walk side
        g.vert(p[0], y, p[1], u, 0.05),                       // face, top
        g.vert(p[0], Y_ROAD - 0.04, p[1], u, 0.75)            // face, foot
      ];
    });
    for (let i = 1; i < n; i++) {
      g.quad(rows[i - 1][0], rows[i - 1][1], rows[i][1], rows[i][0], true);
      g.quad(rows[i - 1][3], rows[i - 1][2], rows[i][2], rows[i][3]);
    }
  }

  /* ---------------- the ground itself ---------------- */

  function buildRoad(g) {
    // Main St: rows across the road every 5 m, 9 points per row (arched).
    const mouthW = (z) => z > -1.5 && z < 10.2;
    const mouthE = (z) => (z > -88.0 && z < -78.4) || (z > 62.4 && z < 68.4);
    const zs = stations(-180, 80, [WEST_EDGE, EAST_EDGE, CROWN_X,
      { breaks: [-88.0, -87.4, -79.0, -78.4, -0.9, 9.6, 62.4, 63.0, 67.8, 68.4] }], 5);
    const DAMP = [0.78, 0.76, 0.74, 1];     // darker, damp strip along each curb
    const rows = zs.map((z) => {
      const c = CROWN_X(z), w = WEST_EDGE(z), e = EAST_EDGE(z);
      const dw = 0.5 / (c - w), de = 0.5 / (e - c);
      return [-1, -1 + dw, -0.6, -0.3, 0, 0.3, 0.6, 1 - de, 1].map((t) => {
        const x = t < 0 ? c + t * (c - w) : c + t * (e - c);
        const damp = (t === -1 && !mouthW(z)) || (t === 1 && !mouthE(z));
        return g.vert(x, Y_ROAD + CROWN * (1 - t * t), z, (x - c) / ROAD_TILE, z / ROAD_TILE, damp ? DAMP : null);
      });
    });
    for (let i = 1; i < rows.length; i++) {
      for (let j = 1; j < 9; j++) g.quad(rows[i - 1][j - 1], rows[i - 1][j], rows[i][j], rows[i][j - 1], true);
    }
    // Side streets (flat): the wheel tracks run along each arm.
    const arm = (outline, zMid) => polygon(g, outline, Y_ROAD, null,
      { uv: (x, z) => [(z - zMid) / ROAD_TILE + 0.5, x / ROAD_TILE] });
    arm([[-6.40, -1.5], [-6.85, 0.9], [-8.4, 2.0], [-60, 2.0], [-60, 8.4], [-6.35, 8.4],
         [-5.08, 8.93], [-4.55, 10.2]], 5.2);                                   // Court St
    arm([[6.40, -78.4], [6.85, -79.45], [7.9, -79.9], [60, -79.9], [60, -86.5], [7.9, -86.5],
         [6.85, -86.95], [6.40, -88.0]], -83.2);                                // Bloomfield Ave
    arm([[6.40, 68.4], [6.9, 67.9], [40, 67.9], [40, 62.9], [6.9, 62.9], [6.40, 62.4]], 65.4);  // Higgins Ave
  }

  function buildWalks(G) {
    const CONC = [3, 3];          // concrete: 3 m tile (as before)
    const FLAG_E = [3.6, 3.6];    // flags 1.8 x 1.2 m (40-46 Main, Stryker plate)
    const FLAG_W = [5.0, 4.5];    // flags 2.5 x 1.5 m (County Hotel)
    const BRICK = [1, 1];
    // Vertex colours (multiplied with the pale ground_detail map). Grass as #lawn-west.
    const rgb = (hex) => { const c = new THREE.Color(hex); return [c.r, c.g, c.b, 1]; };
    const GRASS = rgb('#7d9052');
    const EARTH = rgb('#8c7b62');
    const SOFT = [2, 2];
    const wBack = constant(-10.30);

    // --- West side, north of Court St (walk 3.9 m, unchanged line) ---
    walk(G.concrete, 'W', -180, -139.2, WEST_EDGE, wBack, CONC);            // 27 Main, Palace
    walk(G.brick, 'W', -139.2, -135.9, WEST_EDGE, wBack, BRICK);            // Palace alley crossing
    walk(G.flags, 'W', -135.9, -100.1, WEST_EDGE, wBack, FLAG_W);           // 35-41, County Hotel
    walk(G.concrete, 'W', -100.1, -78.5, WEST_EDGE, wBack, CONC);           // blacksmith's lane, 51-57
    walk(G.concrete, 'W', -78.5, -56, constant(-8.0), wBack, CONC, { flat: true });   // 59-65: 2.3 m walk ...
    walk(G.soft, 'W', -78.5, -56, WEST_EDGE, constant(-8.0), SOFT, { flat: true, color: GRASS });  // ... + grass strip
    walk(G.concrete, 'W', -56, -1.5, WEST_EDGE, wBack, CONC);               // 65, County Offices, courthouse
    polygon(G.concrete, [[-10.30, -1.5], [-6.40, -1.5], [-6.85, 0.9], [-8.4, 2.0], [-60, 2.0],
                         [-60, 0], [-10.30, 0]], Y_WALK, CONC, { skirt: true });       // corner + Court St north walk

    // --- West side, south of Court St (curb 1.85 m further east, walk 3.6 m) ---
    polygon(G.concrete, [[-60, 8.4], [-6.35, 8.4], [-5.08, 8.93], [-4.55, 10.2], [WEST_EDGE(10.4), 10.4],
                         [-8.15, 10.4], [-60, 10.4]], Y_WALK, CONC, { skirt: true });  // Court St south walk + corner
    walk(G.concrete, 'W', 10.4, 80, WEST_EDGE, WEST_BACK_S, CONC);
    rect(G.concrete, -8.72, -8.0, 19.8, 26.4, Y_WALK, CONC, { skirt: true });          // under the porch of 83-87
    rect(G.soft, -13.0, -7.9, 26.4, 58.4, 0.015, SOFT, { color: GRASS });              // front yards of 91-97

    // --- East side, north of Bloomfield Ave (curb slants in, walk 2.85 m + up to each front) ---
    walk(G.flags, 'E', -180, -164, EAST_EDGE, line([[-180, 6.36], [-164, 6.87]]), FLAG_E);
    walk(G.flags, 'E', -164, -140.9, EAST_EDGE, constant(7.40), FLAG_E);               // 24-30
    walk(G.flags, 'E', -140.9, -137.6, EAST_EDGE, line([[-140.9, 7.61], [-137.6, 7.72]]), FLAG_E);  // lane at 32
    walk(G.flags, 'E', -137.6, -124.05, EAST_EDGE, constant(8.64), FLAG_E);            // 32-38
    walk(G.flags, 'E', -124.05, -105.8, EAST_EDGE, constant(8.70), FLAG_E);            // 40-46
    walk(G.concrete, 'E', -105.8, -89.9, EAST_EDGE, constant(10.95), CONC);            // Rea Building
    rect(G.brick, 5.15, 6.15, -128, -126, Y_WALK + 0.004, BRICK);                      // brick patch by 38-40
    // Bloomfield Ave, north side: corner, walk along the Rea wall, grass verge by the road.
    polygon(G.concrete, [[6.40, -89.9], [6.40, -88.0], [6.85, -86.95], [7.9, -86.5], [8.5, -86.5],
                         [8.5, -89.9]], Y_WALK, CONC, { skirt: true });
    rect(G.concrete, 8.5, 60, -89.9, -87.7, Y_WALK, CONC, { skirt: true });
    rect(G.soft, 8.5, 30, -87.7, -86.5, Y_WALK, SOFT, { color: GRASS, skirt: true });
    rect(G.concrete, 30, 60, -87.7, -86.5, Y_WALK, CONC, { skirt: true });

    // --- East side, Bloomfield Ave to Higgins Ave (unchanged line, walk 3.9 m) ---
    polygon(G.concrete, [[6.40, -78.4], [6.85, -79.45], [7.9, -79.9], [60, -79.9], [60, -77.3],
                         [10.30, -77.3], [10.30, -78.4]], Y_WALK, CONC, { skirt: true });  // Bloomfield south walk
    walk(G.concrete, 'E', -78.4, 62.1, EAST_EDGE, constant(10.30), CONC);
    polygon(G.concrete, [[6.40, 62.1], [6.9, 62.1], [6.9, 62.9], [6.40, 62.4]], Y_WALK, CONC, { skirt: true });
    // --- East side, south of Higgins Ave ---
    polygon(G.concrete, [[6.40, 68.4], [6.9, 67.9], [6.9, 68.7], [9.3, 68.7], [9.3, 80], [6.40, 80]],
      Y_WALK, CONC, { skirt: true });
    // Higgins Ave: earth margins instead of walks.
    rect(G.soft, 6.9, 40, 62.1, 62.9, Y_WALK, SOFT, { color: EARTH, skirt: true });
    rect(G.soft, 6.9, 40, 67.9, 68.7, Y_WALK, SOFT, { color: EARTH, skirt: true });

    // --- Bare-earth lanes from the property line back to the mapped back buildings ---
    const lane = (x0, x1, z0, z1) => rect(G.soft, x0, x1, z0, z1, 0.012, SOFT, { color: EARTH });
    lane(-35, -10.3, -139.2, -135.9);     // Palace alley
    lane(-57.5, -10.3, -100.1, -94.5);    // blacksmith's lane
    lane(7.6, 58, -140.9, -137.8);        // lane at 32
    lane(6.3, 10.35, -180, -140.9);       // trodden lot ground up to the 24-30 placeholder (front x 10.3)
    lane(10.3, 36, -49.1, -45.6);         // gap 68 / Union Hotel
    lane(10.3, 45, -15.9, -11.3);         // gap hotel / Nevius
    lane(10.3, 57, -3.3, 1.3);            // alley 80
    lane(10.3, 29, 16.9, 21.7);           // alley 86

    // --- Curbs (walk on the left of each line) ---
    curb(G.curb, edgePoints('W', -180, -1.5).concat([[-6.85, 0.9], [-8.4, 2.0], [-60, 2.0]]));
    curb(G.curb, [[-60, 8.4], [-6.35, 8.4], [-5.08, 8.93]].concat(edgePoints('W', 10.2, 80)));
    curb(G.curb, edgePoints('E', 80, 68.4).concat([[6.9, 67.9], [40, 67.9]]));
    curb(G.curb, [[40, 62.9], [6.9, 62.9]].concat(edgePoints('E', 62.4, -78.4),
      [[6.85, -79.45], [7.9, -79.9], [60, -79.9]]));
    curb(G.curb, [[60, -86.5], [7.9, -86.5], [6.85, -86.95]].concat(edgePoints('E', -88.0, -180)));
    curb(G.curb, [[6.40, 68.4, 1], [6.40, 62.4, 1]]);     // flush stones across the mouth of Higgins Ave
  }

  function buildDecals(g) {
    // Light dirt (owner, 2026-11-11). [x, z, cell, size m, turn deg]; cells: 0 droppings,
    // 1 flattened droppings, 2 paper scraps.
    const spots = [
      [1.2, -22, 0, 0.6, 20], [-0.8, -64, 0, 0.6, 130], [5.3, -33, 0, 0.55, 75], [0.6, -104, 0, 0.6, 200],
      [-5.2, -112, 0, 0.55, 310], [1.8, 24, 0, 0.6, 50], [-1.0, -140, 0, 0.6, 160], [5.2, -70, 0, 0.55, 260],
      [-0.3, -8, 1, 0.8, 5], [0.9, -48, 1, 0.8, 175], [-1.4, -90, 1, 0.75, 12], [2.1, 40, 1, 0.8, 186],
      [0.2, -126, 1, 0.8, 352], [-0.6, -158, 1, 0.75, 8],
      [5.6, -58, 2, 0.7, 40], [-5.7, -30, 2, 0.7, 110], [4.6, -98, 2, 0.7, 230], [-5.6, -118, 2, 0.7, 300],
      [5.5, 8, 2, 0.7, 15], [-3.6, 33, 2, 0.7, 80]
    ];
    const LIFT = 0.012;
    spots.forEach(([x, z, cell, size, deg]) => {
      const u0 = (cell % 2) * 0.5, v0 = cell < 2 ? 0.5 : 0;     // image row 0 is the top (v 0.5 ... 1)
      const a = deg * Math.PI / 180, c = Math.cos(a) * size / 2, s = Math.sin(a) * size / 2;
      const corners = [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([i, j], k) => {
        const px = x + i * c - j * s, pz = z + i * s + j * c;
        return g.vert(px, roadY(px, pz) + LIFT, pz, u0 + (k === 1 || k === 2 ? 0.5 : 0), v0 + (k > 1 ? 0.5 : 0));
      });
      g.quad(corners[0], corners[1], corners[2], corners[3], true);
    });
    // Curved wheel tracks where carts and cars turn into Bloomfield Ave and Court St:
    // quarter circles [centre x, centre z, radius, start deg, end deg], 2 m wide, fading out
    // at both ends. Angles: 0 = east (+x), 90 = south (+z).
    const arcs = [
      [8.2, -78.2, 5, 180, 270],      // from the south into Bloomfield Ave
      [8.2, -88.2, 5, 180, 90],       // from the north into Bloomfield Ave
      [-8.2, 0.2, 5, 0, 90],          // from the north into Court St
      [-8.27, 11.2, 6, 0, -90]        // from the south into Court St
    ];
    const SEG = 14;
    arcs.forEach(([cx, cz, r, a0, a1]) => {
      let prev = null;
      for (let i = 0; i <= SEG; i++) {
        const f = i / SEG;
        const a = (a0 + (a1 - a0) * f) * Math.PI / 180;
        const fade = Math.min(1, Math.min(f, 1 - f) * 5);
        const row = [-1, -0.33, 0.33, 1].map((t) => {
          const x = cx + (r + t) * Math.cos(a), z = cz + (r + t) * Math.sin(a);
          return g.vert(x, roadY(x, z) + LIFT, z, 0.5 + (t + 1) * 0.25, 0.02 + f * 0.46, [1, 1, 1, fade]);
        });
        if (prev) for (let j = 1; j < 4; j++) g.quad(prev[j - 1], prev[j], row[j], row[j - 1], true);
        prev = row;
      }
    });
  }

  AFRAME.registerComponent('street-ground', {
    schema: {
      textures: { default: 'assets/textures/ground/' },
      concrete: { default: 'assets/textures/polyhaven/sidewalk_concrete.jpg' }
    },

    init() {
      const G = {};
      ['road', 'concrete', 'flags', 'brick', 'curb', 'soft', 'decals'].forEach((k) => { G[k] = new Group(); });
      buildRoad(G.road);
      buildWalks(G);
      buildDecals(G.decals);

      const renderer = this.el.sceneEl.renderer;
      const loader = new THREE.TextureLoader();
      const tex = (url) => {
        const t = loader.load(url);
        t.wrapS = t.wrapT = THREE.RepeatWrapping;
        t.colorSpace = THREE.SRGBColorSpace;
        // Sharper at shallow angles (the ground is nearly always seen that way).
        t.anisotropy = renderer ? Math.min(4, renderer.capabilities.getMaxAnisotropy()) : 4;
        return t;
      };
      const dir = this.data.textures;
      const mat = (url, extra) => new THREE.MeshStandardMaterial(Object.assign(
        { map: tex(url), roughness: 1, metalness: 0, vertexColors: true }, extra));
      const mats = {
        road: mat(dir + 'road_oiled_earth.jpg'),
        concrete: mat(this.data.concrete, { side: THREE.DoubleSide }),
        flags: mat(dir + 'walk_bluestone_flags.jpg', { side: THREE.DoubleSide }),
        brick: mat(dir + 'walk_brick.jpg', { side: THREE.DoubleSide }),
        curb: mat(dir + 'curb_stone.jpg', { side: THREE.DoubleSide }),
        soft: mat(dir + 'ground_detail.jpg', { side: THREE.DoubleSide }),
        decals: mat(dir + 'street_decals.png', {
          transparent: true, depthWrite: false, alphaTest: 0.03,
          polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2
        })
      };
      Object.keys(G).forEach((k) => {
        const mesh = new THREE.Mesh(G[k].geometry(), mats[k]);
        mesh.name = 'ground-' + k;
        if (k === 'decals') mesh.renderOrder = 1;
        this.el.setObject3D(k, mesh);
      });
      this.keys = Object.keys(G);
    },

    remove() {
      (this.keys || []).forEach((k) => {
        const mesh = this.el.getObject3D(k);
        if (!mesh) return;
        mesh.geometry.dispose();
        if (mesh.material.map) mesh.material.map.dispose();
        mesh.material.dispose();
        this.el.removeObject3D(k);
      });
    }
  });

  /* ------------------------------------------------------------------ */
  /* box-group                                                           */
  /* ------------------------------------------------------------------ */
  /*
   * A few plain boxes drawn as one mesh (one draw call), in scene metres:
   * "x y z width height depth" per box (centre, then size), separated by commas.
   *
   *   <a-entity box-group="color: #e8dcc4; boxes: -6.6 3.3 23.1 4.2 0.2 6.6, -4.7 1.7 20 0.14 3.1 0.14"></a-entity>
   */
  AFRAME.registerComponent('box-group', {
    schema: {
      boxes: { default: '' },
      color: { type: 'color', default: '#e8dcc4' }
    },

    update() {
      this.remove();
      const pos = [], idx = [];
      this.data.boxes.split(',').forEach((entry) => {
        const v = entry.trim().split(/\s+/).map(Number);
        if (v.length !== 6 || v.some(isNaN)) return;
        const box = new THREE.BoxGeometry(v[3], v[4], v[5]).toNonIndexed();
        const p = box.getAttribute('position');
        for (let i = 0; i < p.count; i++) {
          idx.push(pos.length / 3);
          pos.push(p.getX(i) + v[0], p.getY(i) + v[1], p.getZ(i) + v[2]);
        }
        box.dispose();
      });
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
      geo.setIndex(idx);
      geo.computeVertexNormals();
      const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: this.data.color, roughness: 1 }));
      this.el.setObject3D('mesh', mesh);
    },

    remove() {
      const mesh = this.el.getObject3D('mesh');
      if (!mesh) return;
      mesh.geometry.dispose();
      mesh.material.dispose();
      this.el.removeObject3D('mesh');
    }
  });
})();
