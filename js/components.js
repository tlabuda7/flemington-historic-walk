/*
 * components.js — custom A-Frame components for the Flemington 1920 walk.
 *
 *   building       A placeholder building (box + facade) that can take a photo later.
 *   canvas-texture Cheap procedural textures (dirt road, wooden planks) drawn in code.
 *   gradient-sky   A soft vertical sky gradient (blue overhead, hazy at the horizon).
 *   locomotion     Walking: WASD/arrows on desktop, thumbstick + snap turn in VR.
 *
 * Everything here uses plain three.js (bundled inside A-Frame as THREE),
 * so there is nothing extra to download.
 */

/* ------------------------------------------------------------------ */
/* Small helpers                                                       */
/* ------------------------------------------------------------------ */

// Seeded random numbers, so procedural textures look identical on every load.
function makeRandom(seed) {
  let s = seed;
  return () => (s = (s * 16807) % 2147483647) / 2147483647;
}

function makeCanvas(width, height) {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  return canvas;
}

// Turn a canvas into a tiling texture. Small power-of-two canvases keep GPU memory low.
function canvasToTexture(canvas, repeatX = 1, repeatY = 1) {
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(repeatX, repeatY);
  tex.anisotropy = 4; // keeps the ground sharp at shallow viewing angles
  return tex;
}

// Run fn(mesh) once the entity (and its geometry/material components) has loaded.
function onMeshReady(el, fn) {
  const go = () => fn(el.getObject3D('mesh'));
  if (el.hasLoaded) go();
  else el.addEventListener('loaded', go, { once: true });
}

/* ------------------------------------------------------------------ */
/* Facade textures for placeholder buildings                           */
/* ------------------------------------------------------------------ */

// Faint brick courses or clapboard lines drawn over the wall colour.
// wallType: 'brick', 'wood' (clapboard) or 'plain' (stucco, painted trim).
function drawWallPattern(ctx, w, h, wallType) {
  if (wallType === 'plain') return;
  ctx.globalAlpha = wallType === 'brick' ? 0.12 : 0.22;
  ctx.fillStyle = '#000';
  const step = wallType === 'brick' ? 6 : 9;
  for (let y = 0; y < h; y += step) {
    ctx.fillRect(0, y, w, 1);
    if (wallType === 'brick') {
      // staggered vertical joints between bricks
      const offset = (y / step) % 2 ? 0 : 8;
      for (let x = offset; x < w; x += 16) ctx.fillRect(x, y, 1, step);
    }
  }
  ctx.globalAlpha = 1;
}

// One "bay" of an upper floor: a patch of wall with a single sash window.
// Repeated across and up the facade by the texture's repeat setting.
// style: 'sash' (square-headed window) or 'arched' (round-headed window).
function makeWindowBayTexture(wallColor, trimColor, wallType, bays, floors, style = 'sash') {
  const c = makeCanvas(128, 128);
  const ctx = c.getContext('2d');
  ctx.fillStyle = wallColor;
  ctx.fillRect(0, 0, 128, 128);
  drawWallPattern(ctx, 128, 128, wallType);

  if (style === 'arched') {
    // Frame with a semicircular head, then the glass inside it.
    ctx.fillStyle = trimColor;
    ctx.beginPath();
    ctx.moveTo(40, 100); ctx.lineTo(40, 42); ctx.arc(64, 42, 24, Math.PI, 0); ctx.lineTo(88, 100);
    ctx.fill();
    ctx.fillRect(36, 98, 56, 6);   // sill
    ctx.fillStyle = '#28303a';
    ctx.beginPath();
    ctx.moveTo(46, 95); ctx.lineTo(46, 42); ctx.arc(64, 42, 18, Math.PI, 0); ctx.lineTo(82, 95);
    ctx.fill();
    ctx.fillStyle = trimColor;
    ctx.fillRect(46, 64, 36, 4);   // sash bar
  } else {
    ctx.fillStyle = trimColor;
    ctx.fillRect(39, 20, 50, 8);   // lintel above the window
    ctx.fillRect(41, 28, 46, 70);  // window frame
    ctx.fillRect(37, 98, 54, 6);   // sill
    ctx.fillStyle = '#28303a';
    ctx.fillRect(46, 33, 36, 60);  // glass
    ctx.fillStyle = trimColor;
    ctx.fillRect(46, 61, 36, 4);   // sash bar between upper and lower panes
  }
  ctx.fillStyle = 'rgba(255,255,255,0.12)';
  ctx.fillRect(48, 45, 10, 16);    // a hint of reflection

  return canvasToTexture(c, bays, floors);
}

// One bay of a ground-floor shopfront: sign band, transom, big display glass, kickplate.
function makeStorefrontTexture(wallColor, trimColor, bays) {
  const c = makeCanvas(128, 128);
  const ctx = c.getContext('2d');
  ctx.fillStyle = wallColor;
  ctx.fillRect(0, 0, 128, 128);

  ctx.fillStyle = '#2f3a2c';
  ctx.fillRect(0, 6, 128, 18);    // painted sign band
  ctx.fillStyle = trimColor;
  ctx.fillRect(8, 28, 112, 96);   // shopfront frame
  ctx.fillStyle = '#3a4650';
  ctx.fillRect(13, 32, 102, 14);  // transom windows
  ctx.fillStyle = '#222a33';
  ctx.fillRect(13, 50, 102, 52);  // display window
  ctx.fillStyle = 'rgba(255,255,255,0.10)';
  ctx.fillRect(18, 54, 30, 44);   // reflection
  ctx.fillStyle = '#5a3f2a';
  ctx.fillRect(13, 106, 102, 16); // wooden kickplate

  return canvasToTexture(c, bays, 1);
}

/* ------------------------------------------------------------------ */
/* building                                                            */
/* ------------------------------------------------------------------ */
/*
 * Usage:
 *   <a-entity id="bldg-w01" position="-9 0 -54" rotation="0 90 0"
 *             building="width: 12; height: 8; stories: 2; depth: 14;
 *                       color: #8e4a36; wall: brick; photo: "></a-entity>
 *
 * The entity's position is the CENTRE OF THE FRONT WALL at ground level.
 * The building extends backwards (local -Z) from there, and the front faces local +Z.
 *
 * To use a real photo later, set `photo` to an image path, e.g.
 *   photo: assets/photos/bldg-w01.jpg
 * The photo is stretched over the whole front wall, so crop it to the facade
 * (straight-on, roughly width:height of the building). The procedural windows,
 * shopfront and cornice are hidden when a photo is set.
 */
AFRAME.registerComponent('building', {
  schema: {
    width:   { default: 8 },             // metres along the street
    height:  { default: 8 },             // metres
    depth:   { default: 12 },            // metres back from the sidewalk
    stories: { default: 2 },
    color:   { type: 'color', default: '#8e4a36' },  // wall colour
    trim:    { type: 'color', default: '#e8dcc4' },  // window frames / cornice
    wall:    { default: 'brick', oneOf: ['brick', 'wood'] },
    bays:    { default: 0 },             // windows per floor; 0 = one per ~3 m
    photo:   { default: '' }             // path to a facade photo (optional)
  },

  // update() runs on creation and every time an attribute changes,
  // so el.setAttribute('building', 'photo', 'assets/photos/x.jpg') just works.
  update() {
    this.disposeMesh();
    const d = this.data;
    const group = new THREE.Group();
    const storyHeight = d.height / d.stories;

    // 1) The main body: one box.
    const body = new THREE.Mesh(
      new THREE.BoxGeometry(d.width, d.height, d.depth),
      new THREE.MeshStandardMaterial({ color: d.color, roughness: 0.95 })
    );
    body.position.set(0, d.height / 2, -d.depth / 2);
    body.name = 'body';
    group.add(body);

    // 2) The front face, sitting 2 cm in front of the box to avoid flicker.
    if (d.photo) {
      const tex = new THREE.TextureLoader().load(d.photo);
      tex.colorSpace = THREE.SRGBColorSpace;
      const facade = new THREE.Mesh(
        new THREE.PlaneGeometry(d.width, d.height),
        new THREE.MeshStandardMaterial({ map: tex, roughness: 1 })
      );
      facade.position.set(0, d.height / 2, 0.02);
      facade.name = 'facade';
      group.add(facade);
    } else {
      const bays = d.bays || Math.max(1, Math.round(d.width / 3));

      // Ground floor shopfronts.
      const shop = new THREE.Mesh(
        new THREE.PlaneGeometry(d.width, storyHeight),
        new THREE.MeshStandardMaterial({
          map: makeStorefrontTexture(d.color, d.trim, Math.max(1, Math.round(d.width / 4))),
          roughness: 0.9
        })
      );
      shop.position.set(0, storyHeight / 2, 0.02);
      shop.name = 'facade-ground';
      group.add(shop);

      // Upper floors with repeating windows.
      const upperHeight = d.height - storyHeight;
      const upper = new THREE.Mesh(
        new THREE.PlaneGeometry(d.width, upperHeight),
        new THREE.MeshStandardMaterial({
          map: makeWindowBayTexture(d.color, d.trim, d.wall, bays, d.stories - 1),
          roughness: 0.9
        })
      );
      upper.position.set(0, storyHeight + upperHeight / 2, 0.02);
      upper.name = 'facade-upper';
      group.add(upper);

      // 3) A simple cornice ledge along the roofline.
      const cornice = new THREE.Mesh(
        new THREE.BoxGeometry(d.width + 0.3, 0.45, 0.5),
        new THREE.MeshStandardMaterial({ color: d.trim, roughness: 0.9 })
      );
      cornice.position.set(0, d.height - 0.22, 0.1);
      cornice.name = 'cornice';
      group.add(cornice);
    }

    this.el.setObject3D('mesh', group);
  },

  remove() {
    this.disposeMesh();
  },

  // Free GPU memory for the old meshes when rebuilding or removing.
  disposeMesh() {
    const old = this.el.getObject3D('mesh');
    if (!old) return;
    old.traverse((obj) => {
      if (!obj.isMesh) return;
      obj.geometry.dispose();
      if (obj.material.map) obj.material.map.dispose();
      obj.material.dispose();
    });
    this.el.removeObject3D('mesh');
  }
});

/* ------------------------------------------------------------------ */
/* canvas-texture                                                      */
/* ------------------------------------------------------------------ */
/*
 * Usage: <a-plane ... canvas-texture="pattern: dirt; repeat: 1 20">
 * Replace with a real texture later via material="src: assets/textures/dirt.jpg".
 */
const PATTERNS = {
  // Packed dirt with speckles and two faint wagon-wheel ruts running along the road.
  dirt(ctx, size, rand) {
    ctx.fillStyle = '#8b6d4b';
    ctx.fillRect(0, 0, size, size);
    for (let i = 0; i < 2500; i++) {
      const shade = rand() < 0.5 ? '#6f5438' : '#a68862';
      ctx.globalAlpha = 0.25 + rand() * 0.35;
      ctx.fillStyle = shade;
      ctx.fillRect(rand() * size, rand() * size, 1 + rand() * 2, 1 + rand() * 2);
    }
    ctx.globalAlpha = 0.16;
    ctx.fillStyle = '#4b3824';
    for (const u of [0.3, 0.7]) {
      ctx.fillRect(u * size - 10, 0, 20, size);
      ctx.fillRect(u * size - 5, 0, 10, size);
    }
    ctx.globalAlpha = 1;
  },

  // Weathered boards laid across the sidewalk, with dark gaps between them.
  planks(ctx, size, rand) {
    const boards = 8;
    const bh = size / boards;
    for (let i = 0; i < boards; i++) {
      ctx.fillStyle = `hsl(30, 30%, ${34 + rand() * 12}%)`;
      ctx.fillRect(0, i * bh, size, bh);
      ctx.globalAlpha = 0.15; // wood grain
      ctx.fillStyle = '#2a1c10';
      for (let g = 0; g < 4; g++) ctx.fillRect(0, i * bh + 4 + rand() * (bh - 8), size, 1);
      ctx.globalAlpha = 1;
      ctx.fillStyle = '#24170d';
      ctx.fillRect(0, i * bh, size, 2); // gap between boards
    }
  }
};

AFRAME.registerComponent('canvas-texture', {
  schema: {
    pattern: { default: 'dirt', oneOf: Object.keys(PATTERNS) },
    repeat:  { type: 'vec2', default: { x: 1, y: 1 } },
    seed:    { default: 7 }
  },

  init() {
    const size = 256;
    const canvas = makeCanvas(size, size);
    PATTERNS[this.data.pattern](canvas.getContext('2d'), size, makeRandom(this.data.seed));
    this.texture = canvasToTexture(canvas, this.data.repeat.x, this.data.repeat.y);

    onMeshReady(this.el, (mesh) => {
      mesh.material.map = this.texture;
      mesh.material.color.set('#ffffff'); // show the texture's own colours
      mesh.material.needsUpdate = true;
    });
  },

  remove() {
    this.texture.dispose();
  }
});

/* ------------------------------------------------------------------ */
/* gradient-sky                                                        */
/* ------------------------------------------------------------------ */
/*
 * Put on a large inward-facing sphere. Blends from `top` overhead to `horizon`
 * at eye level; keep `horizon` close to the scene's fog colour so distant
 * buildings melt into the haze.
 */
AFRAME.registerComponent('gradient-sky', {
  schema: {
    top:     { type: 'color', default: '#a9bfd2' },
    horizon: { type: 'color', default: '#ecdfc4' }
  },

  init() {
    const canvas = makeCanvas(4, 256);
    const ctx = canvas.getContext('2d');
    const grad = ctx.createLinearGradient(0, 0, 0, 256);
    grad.addColorStop(0, this.data.top);       // straight up
    grad.addColorStop(0.5, this.data.horizon); // horizon (middle of the sphere)
    grad.addColorStop(1, this.data.horizon);   // below the horizon
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 4, 256);
    this.texture = canvasToTexture(canvas);

    onMeshReady(this.el, (mesh) => {
      mesh.material.map = this.texture;
      mesh.material.color.set('#ffffff');
      mesh.material.needsUpdate = true;
    });
  },

  remove() {
    this.texture.dispose();
  }
});

/* ------------------------------------------------------------------ */
/* locomotion                                                          */
/* ------------------------------------------------------------------ */
/*
 * Put on the camera rig (the parent of the camera and controllers).
 * Moves the whole rig, so the camera and hands travel together.
 *
 *   Desktop: W/A/S/D or arrow keys to walk, Shift to walk faster.
 *            Mouse looks around (handled by look-controls on the camera).
 *   VR:      Left thumbstick walks in the direction you are looking.
 *            Right thumbstick left/right snap-turns by `snapAngle` degrees.
 */
AFRAME.registerComponent('locomotion', {
  schema: {
    speed:     { default: 2.0 },   // metres per second (a brisk stroll)
    snapAngle: { default: 45 },    // degrees per snap turn
    deadzone:  { default: 0.15 },  // ignore tiny thumbstick drift
    boundsX:   { default: 10.2 },  // stay on the street and sidewalks
    minZ:      { default: -160 },  // north end of the walkable street
    maxZ:      { default: 60 }     // south end of the walkable street
  },

  init() {
    this.keys = new Set();
    this.stick = { x: 0, y: 0 };
    this.turnReady = true;

    this.camera = this.el.querySelector('[camera]');
    this.quat = new THREE.Quaternion();
    this.euler = new THREE.Euler();
    this.camPos = new THREE.Vector3();
    this.offset = new THREE.Vector3();
    this.up = new THREE.Vector3(0, 1, 0);

    // Keyboard
    this.onKeyDown = (e) => this.keys.add(e.code);
    this.onKeyUp = (e) => this.keys.delete(e.code);
    this.onBlur = () => this.keys.clear(); // avoid "stuck" keys when the window loses focus
    window.addEventListener('keydown', this.onKeyDown);
    window.addEventListener('keyup', this.onKeyUp);
    window.addEventListener('blur', this.onBlur);

    // VR controllers (they emit thumbstickmoved with x/y in the range -1..1)
    this.el.querySelector('#left-hand').addEventListener('thumbstickmoved', (e) => {
      this.stick.x = e.detail.x;
      this.stick.y = e.detail.y;
    });
    this.el.querySelector('#right-hand').addEventListener('thumbstickmoved', (e) => {
      this.handleSnapTurn(e.detail.x);
    });
  },

  remove() {
    window.removeEventListener('keydown', this.onKeyDown);
    window.removeEventListener('keyup', this.onKeyUp);
    window.removeEventListener('blur', this.onBlur);
  },

  tick(time, delta) {
    const dt = Math.min(delta, 100) / 1000; // seconds; capped so a hiccup doesn't teleport you
    const k = this.keys;

    // Input as "strafe right" (x) and "forward" (z), each roughly -1..1.
    let x = 0;
    let z = 0;
    if (k.has('KeyW') || k.has('ArrowUp')) z += 1;
    if (k.has('KeyS') || k.has('ArrowDown')) z -= 1;
    if (k.has('KeyD') || k.has('ArrowRight')) x += 1;
    if (k.has('KeyA') || k.has('ArrowLeft')) x -= 1;
    if (Math.hypot(this.stick.x, this.stick.y) > this.data.deadzone) {
      x += this.stick.x;
      z -= this.stick.y; // pushing the stick forward gives a negative y
    }
    if (x === 0 && z === 0) return;

    const len = Math.hypot(x, z);
    if (len > 1) { x /= len; z /= len; }

    // Which way is the head facing? Use only the left/right angle (yaw),
    // so looking up or down doesn't make you fly or sink.
    this.camera.object3D.getWorldQuaternion(this.quat);
    this.euler.setFromQuaternion(this.quat, 'YXZ');
    const sin = Math.sin(this.euler.y);
    const cos = Math.cos(this.euler.y);

    const fast = k.has('ShiftLeft') || k.has('ShiftRight') ? 2 : 1;
    const step = this.data.speed * fast * dt;
    const pos = this.el.object3D.position;
    // forward = (-sin, -cos), right = (cos, -sin) in the X/Z plane
    pos.x += (x * cos - z * sin) * step;
    pos.z += (-x * sin - z * cos) * step;

    // Simple boundaries instead of full collision detection.
    pos.x = THREE.MathUtils.clamp(pos.x, -this.data.boundsX, this.data.boundsX);
    pos.z = THREE.MathUtils.clamp(pos.z, this.data.minZ, this.data.maxZ);
  },

  // Turn once per flick: the stick must return near centre before the next turn.
  handleSnapTurn(stickX) {
    if (this.turnReady && Math.abs(stickX) > 0.7) {
      this.turnReady = false;
      this.snapTurn(-Math.sign(stickX) * THREE.MathUtils.degToRad(this.data.snapAngle));
    } else if (Math.abs(stickX) < 0.3) {
      this.turnReady = true;
    }
  },

  // Rotate the rig around the HEAD's position (not the rig centre),
  // so you turn on the spot instead of swinging sideways.
  snapTurn(angle) {
    const rig = this.el.object3D;
    this.camera.object3D.getWorldPosition(this.camPos);
    this.offset.copy(rig.position).sub(this.camPos).applyAxisAngle(this.up, angle);
    rig.position.copy(this.camPos).add(this.offset);
    rig.rotation.y += angle;
  }
});
