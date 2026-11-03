/*
 * kit.js — a small "kit of parts" for building period architecture in code.
 *
 * A KitBuilder collects simple shapes (boxes, columns, gable roofs, mansard roofs,
 * arches, domes, textured panels). When you call build(), every shape that shares a
 * material is merged into ONE mesh. A whole building therefore costs only a handful
 * of draw calls, which keeps the Quest 2 running smoothly.
 *
 * Coordinates inside a builder are the building's LOCAL space:
 *   x = along the street (left/right as you face the building),
 *   y = up from the ground,
 *   z = toward the street (+z) or back from it (-z). z = 0 is the front line.
 *
 * Loaded after components.js (it reuses makeCanvas, canvasToTexture and
 * makeWindowBayTexture from there).
 */

/* ------------------------------------------------------------------ */
/* Shared materials                                                    */
/* ------------------------------------------------------------------ */

// Plain-colour materials are cached and shared between buildings.
// They are flagged `shared` so a building never disposes them.
const KIT_MATERIAL_CACHE = {};
function kitMaterial(color, roughness = 0.9) {
  const key = color + '|' + roughness;
  if (!KIT_MATERIAL_CACHE[key]) {
    const m = new THREE.MeshStandardMaterial({ color, roughness });
    m.userData.shared = true;
    KIT_MATERIAL_CACHE[key] = m;
  }
  return KIT_MATERIAL_CACHE[key];
}

// A material for a texture that has transparent parts (railings, arch cut-outs).
function kitCutoutMaterial(texture) {
  return new THREE.MeshStandardMaterial({
    map: texture, alphaTest: 0.5, side: THREE.DoubleSide, roughness: 0.9
  });
}

/* ------------------------------------------------------------------ */
/* Custom shapes                                                       */
/* ------------------------------------------------------------------ */

// Build a geometry from a list of triangles [[x,y,z],[x,y,z],[x,y,z], ...].
// Each triangle must be listed counter-clockwise as seen from outside.
function geometryFromTriangles(points) {
  const pos = new Float32Array(points.flat());
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array((points.length) * 2), 2));
  g.computeVertexNormals(); // flat shading, since no vertices are shared
  return g;
}

// Two triangles for a four-cornered face (corners counter-clockwise from outside).
function quad(a, b, c, d) {
  return [a, b, c, a, c, d];
}

// Gable roof: a triangular prism. Ridge runs front-to-back (along z),
// so the triangular gable end faces the street.
function gableGeometry(width, height, depth) {
  const w = width / 2, d = depth / 2;
  const A = [-w, 0, d], B = [w, 0, d], C = [0, height, d];
  const A2 = [-w, 0, -d], B2 = [w, 0, -d], C2 = [0, height, -d];
  return geometryFromTriangles([
    A, B, C,             // front gable
    B2, A2, C2,          // back gable
    ...quad(A2, A, C, C2), // left slope
    ...quad(B, B2, C2, C)  // right slope
  ]);
}

// Mansard / hip roof: a box whose sides slope inward by `inset` at the top.
function frustumGeometry(width, depth, height, inset) {
  const w = width / 2, d = depth / 2, h = height;
  const tw = w - inset, td = d - inset;
  return geometryFromTriangles([
    ...quad([-w, 0, d], [w, 0, d], [tw, h, td], [-tw, h, td]),     // front
    ...quad([w, 0, -d], [-w, 0, -d], [-tw, h, -td], [tw, h, -td]), // back
    ...quad([-w, 0, -d], [-w, 0, d], [-tw, h, td], [-tw, h, -td]), // left
    ...quad([w, 0, d], [w, 0, -d], [tw, h, -td], [tw, h, td]),     // right
    ...quad([-tw, h, td], [tw, h, td], [tw, h, -td], [-tw, h, -td]) // top
  ]);
}

/* ------------------------------------------------------------------ */
/* Merging                                                             */
/* ------------------------------------------------------------------ */

// Merge many geometries into one (positions, normals and UVs).
function mergeGeometries(list) {
  const parts = list.map((g) => (g.index ? g.toNonIndexed() : g));
  const count = parts.reduce((n, g) => n + g.attributes.position.count, 0);
  const pos = new Float32Array(count * 3);
  const nor = new Float32Array(count * 3);
  const uv = new Float32Array(count * 2);
  let offset = 0;
  for (const g of parts) {
    const n = g.attributes.position.count;
    pos.set(g.attributes.position.array, offset * 3);
    nor.set(g.attributes.normal.array, offset * 3);
    if (g.attributes.uv) uv.set(g.attributes.uv.array, offset * 2);
    offset += n;
  }
  list.forEach((g) => g.dispose());
  parts.forEach((g) => g.dispose());
  const merged = new THREE.BufferGeometry();
  merged.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  merged.setAttribute('normal', new THREE.BufferAttribute(nor, 3));
  merged.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  return merged;
}

/* ------------------------------------------------------------------ */
/* KitBuilder                                                          */
/* ------------------------------------------------------------------ */

class KitBuilder {
  constructor() {
    this.buckets = new Map(); // material -> list of geometries
  }

  // Add any positioned geometry with a material.
  add(material, geometry) {
    if (!this.buckets.has(material)) this.buckets.set(material, []);
    this.buckets.get(material).push(geometry);
    return this;
  }

  // Box centred at (x, y, z).
  box(material, w, h, d, x, y, z) {
    return this.add(material, new THREE.BoxGeometry(w, h, d).translate(x, y, z));
  }

  // Box sitting on the ground (or on y = base), centred in x/z.
  block(material, w, h, d, x, z, base = 0) {
    return this.box(material, w, h, d, x, base + h / 2, z);
  }

  // Round column standing on y = base, slightly tapered toward the top.
  column(material, radius, height, x, z, base = 0, segments = 10) {
    const g = new THREE.CylinderGeometry(radius * 0.88, radius, height, segments);
    return this.add(material, g.translate(x, base + height / 2, z));
  }

  // Vertical cylinder (drums, cupolas, chimney pots) centred at (x, y, z).
  cylinder(material, radius, height, x, y, z, segments = 8) {
    const g = new THREE.CylinderGeometry(radius, radius, height, segments);
    return this.add(material, g.translate(x, y, z));
  }

  // Gable roof sitting on y = base, centred on (x, z).
  gable(material, w, h, d, x, z, base) {
    return this.add(material, gableGeometry(w, h, d).translate(x, base, z));
  }

  // Mansard or hip roof sitting on y = base, centred on (x, z).
  mansard(material, w, d, h, inset, x, z, base) {
    return this.add(material, frustumGeometry(w, d, h, inset).translate(x, base, z));
  }

  // Half-round arch shape facing the street: a half cylinder with its flat side down.
  // Used for curved pediments and arched roofs.
  arch(material, radius, depth, x, y, z, segments = 12) {
    const g = new THREE.CylinderGeometry(radius, radius, depth, segments, 1, false, -Math.PI / 2, Math.PI);
    g.rotateX(-Math.PI / 2);
    return this.add(material, g.translate(x, y, z));
  }

  // Half-sphere dome sitting on y = base.
  dome(material, radius, x, z, base) {
    const g = new THREE.SphereGeometry(radius, 12, 6, 0, Math.PI * 2, 0, Math.PI / 2);
    return this.add(material, g.translate(x, base, z));
  }

  // Flat panel facing the street (+z), centred at (x, y, z). Used for textured
  // facades, signs, doors and railings.
  panel(material, w, h, x, y, z) {
    return this.add(material, new THREE.PlaneGeometry(w, h).translate(x, y, z));
  }

  // Flight of `count` steps leading down from a floor at height `top`.
  // The flight starts at z = zTop and runs toward the street (+z).
  // Example: top 0.8, count 3 gives steps 0.6, 0.4 and 0.2 m high.
  steps(material, width, top, count, tread, x, zTop) {
    for (let i = 0; i < count; i++) {
      const h = top * (count - i) / (count + 1);
      this.block(material, width, h, tread, x, zTop + tread * (i + 0.5));
    }
    return this;
  }

  // Merge everything into one mesh per material and return a THREE.Group.
  build() {
    const group = new THREE.Group();
    for (const [material, geometries] of this.buckets) {
      group.add(new THREE.Mesh(mergeGeometries(geometries), material));
    }
    this.buckets.clear();
    return group;
  }
}

/* ------------------------------------------------------------------ */
/* Kit textures                                                        */
/* ------------------------------------------------------------------ */

// Balustrade: top and bottom rails with turned balusters, transparent between.
// One tile is about 0.9 m wide.
function makeBalustradeTexture(color, tiles) {
  const c = makeCanvas(128, 64);
  const ctx = c.getContext('2d');
  ctx.fillStyle = color;
  ctx.fillRect(0, 0, 128, 9);    // hand rail
  ctx.fillRect(0, 55, 128, 9);   // bottom rail
  for (let x = 8; x < 128; x += 20) ctx.fillRect(x, 9, 7, 46); // balusters
  return canvasToTexture(c, tiles, 1);
}

// Arcade band: a solid band with a round-arched opening cut out of each tile.
// Used for the upper gallery of the Union Hotel's veranda.
function makeArcadeTexture(color, tiles) {
  const c = makeCanvas(128, 64);
  const ctx = c.getContext('2d');
  ctx.fillStyle = color;
  ctx.fillRect(0, 0, 128, 64);
  ctx.globalCompositeOperation = 'destination-out';
  ctx.beginPath();
  ctx.moveTo(10, 64); ctx.lineTo(10, 62); ctx.arc(64, 62, 54, Math.PI, 0); ctx.lineTo(118, 64);
  ctx.fill();
  ctx.globalCompositeOperation = 'source-over';
  return canvasToTexture(c, tiles, 1);
}

// A painted sign: light lettering on a dark ground.
function makeSignTexture(text, ground = '#3b2f25', ink = '#f1e6c8') {
  const c = makeCanvas(512, 96);
  const ctx = c.getContext('2d');
  ctx.fillStyle = ground;
  ctx.fillRect(0, 0, 512, 96);
  ctx.fillStyle = ink;
  ctx.font = 'bold 58px Georgia, serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, 256, 52);
  return canvasToTexture(c, 1, 1);
}

// Dispose a group built by KitBuilder, keeping shared materials alive.
function disposeKitGroup(group) {
  group.traverse((obj) => {
    if (!obj.isMesh) return;
    obj.geometry.dispose();
    if (!obj.material.userData.shared) {
      if (obj.material.map) obj.material.map.dispose();
      obj.material.dispose();
    }
  });
}
