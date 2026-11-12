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
 *   VR:      Left thumbstick walks in the direction you are looking;
 *            hold the left trigger to walk faster.
 *            Right thumbstick left/right snap-turns by `snapAngle` degrees.
 */
AFRAME.registerComponent('locomotion', {
  schema: {
    speed:     { default: 2.0 },   // metres per second (a brisk stroll)
    snapAngle: { default: 45 },    // degrees per snap turn
    deadzone:  { default: 0.15 },  // ignore tiny thumbstick drift
    boundsX:   { default: 10.2 },  // stay on the street and sidewalks (see STREET_GROUND.limits)
    minZ:      { default: -160 },  // north end of the walkable street
    maxZ:      { default: 60 }     // south end of the walkable street
  },

  init() {
    this.keys = new Set();
    this.stick = { x: 0, y: 0 };          // left stick (walk)
    this.turnStick = 0;                   // right stick x (snap turn)
    this.sprint = false;                  // left trigger held (VR sprint)
    this.inputSource = 'none';            // where the stick values came from (for stick-debug)
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

    // VR controllers, method 1: thumbstickmoved events from oculus-touch-controls
    // (x/y in the range -1..1). Method 2, polling the gamepads, is in readGamepads().
    this.el.querySelector('#left-hand').addEventListener('thumbstickmoved', (e) => {
      this.stick.x = e.detail.x;
      this.stick.y = e.detail.y;
      this.inputSource = 'events';
    });
    // Hold the left trigger to sprint (double speed), like Shift on the keyboard.
    this.el.querySelector('#left-hand').addEventListener('triggerdown', () => { this.sprint = true; });
    this.el.querySelector('#left-hand').addEventListener('triggerup', () => { this.sprint = false; });
    this.el.querySelector('#right-hand').addEventListener('thumbstickmoved', (e) => {
      this.turnStick = e.detail.x;
      this.inputSource = 'events';
      this.handleSnapTurn(e.detail.x);
    });
  },

  // VR controllers, method 2: read the WebXR gamepads directly every frame.
  // On Quest Touch controllers (xr-standard mapping) the thumbstick is axes[2] (x)
  // and axes[3] (y). This works even if the controller component never loads.
  readGamepads() {
    const xr = this.el.sceneEl.renderer && this.el.sceneEl.renderer.xr;
    const session = xr && xr.getSession && xr.getSession();
    if (!session) return;
    for (const source of session.inputSources) {
      const pad = source.gamepad;
      if (!pad || pad.axes.length < 4) continue;
      if (source.handedness === 'left') {
        this.stick.x = pad.axes[2];
        this.stick.y = pad.axes[3];
        this.sprint = !!(pad.buttons[0] && pad.buttons[0].pressed); // trigger
        this.inputSource = 'gamepad';
      } else if (source.handedness === 'right') {
        this.turnStick = pad.axes[2];
        this.inputSource = 'gamepad';
        this.handleSnapTurn(pad.axes[2]);
      }
    }
  },

  remove() {
    window.removeEventListener('keydown', this.onKeyDown);
    window.removeEventListener('keyup', this.onKeyUp);
    window.removeEventListener('blur', this.onBlur);
  },

  tick(time, delta) {
    const dt = Math.min(delta, 100) / 1000; // seconds; capped so a hiccup doesn't teleport you
    const k = this.keys;
    this.readGamepads();

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

    const fast = k.has('ShiftLeft') || k.has('ShiftRight') || this.sprint ? 2 : 1;
    const step = this.data.speed * fast * dt;
    const pos = this.el.object3D.position;
    // forward = (-sin, -cos), right = (cos, -sin) in the X/Z plane
    pos.x += (x * cos - z * sin) * step;
    pos.z += (-x * sin - z * cos) * step;

    // Simple boundaries instead of full collision detection. The street is not the same
    // width everywhere (it narrows north of Bloomfield Ave and south of Court St), so
    // js/ground.js gives the limits for each stretch; boundsX is the fallback.
    const lim = window.STREET_GROUND ? window.STREET_GROUND.limits(pos.z) : null;
    pos.x = THREE.MathUtils.clamp(pos.x, lim ? lim.min : -this.data.boundsX, lim ? lim.max : this.data.boundsX);
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

/* ------------------------------------------------------------------ */
/* baked-lighting                                                      */
/* ------------------------------------------------------------------ */
/*
 * For models whose sunlight, shadows and ambient occlusion were baked in Blender
 * (see tools/blender/union_hotel_bake.py). Put it next to gltf-model:
 *
 *   <a-entity gltf-model="url(assets/models/union-hotel.glb)"
 *             baked-lighting="lightmap: assets/textures/union-hotel-lightmap.jpg; intensity: 1.24">
 *
 * Every material becomes unlit (MeshBasicMaterial): colour texture x lightmap.
 * The scene's lights no longer affect the model, and it is very cheap to draw.
 * `intensity` is the LIGHTMAP_SCALE value the bake script prints.
 *
 * merge (on by default): the whole building is then drawn in ONE draw call instead of
 * one per material. All its colour textures go into one texture array (one layer each,
 * still tiling normally), and all its meshes become one mesh whose vertices remember
 * their texture layer and colour tint. Anything unusual (see mergeProblem) keeps the
 * normal one-material-per-call path. `merge: false` turns it off.
 *
 * keep (default "glass"): materials with these names are left exactly as exported
 * (not lightmapped, not merged), so see-through glass stays transparent. Add the
 * glass-reflect component to give them a sky reflection.
 */
const MERGE_SIZE = 1024;   // colour textures must be this size to go into the array

AFRAME.registerComponent('baked-lighting', {
  schema: {
    lightmap:  { default: '' },
    intensity: { default: 1.0 },
    merge:     { default: true },
    keep:      { type: 'array', default: ['glass'] }
  },

  init() {
    this.texture = new THREE.TextureLoader().load(this.data.lightmap);
    this.texture.flipY = false;                       // glTF UV convention
    this.texture.channel = 1;                         // second UV map ("Lightmap")
    this.texture.colorSpace = THREE.SRGBColorSpace;   // stored gamma-encoded
    this.onLoaded = () => this.apply();
    this.el.addEventListener('model-loaded', this.onLoaded);
    if (this.el.getObject3D('mesh')) this.apply();
  },

  apply() {
    const root = this.el.getObject3D('mesh');
    if (!root || root.userData.bakedLightingDone) return;
    root.userData.bakedLightingDone = true;

    const meshes = [];
    const kept = [];
    root.traverse((obj) => {
      if (!obj.isMesh) return;
      if (!Array.isArray(obj.material) && this.data.keep.includes(obj.material.name)) kept.push(obj);
      else meshes.push(obj);
    });

    let merged = [];
    const skipped = [];
    if (this.data.merge && this.el.sceneEl.renderer.capabilities.isWebGL2) {
      for (const m of meshes) {
        const why = this.mergeProblem(m);
        if (why) skipped.push(`${m.name} (${why})`);
        else merged.push(m);
      }
      if (merged.length < 2) merged = [];   // nothing to gain
    }

    // Meshes that are not merged: one unlit material each (the original path).
    for (const obj of meshes) {
      if (merged.includes(obj)) continue;
      const old = obj.material;
      obj.material = new THREE.MeshBasicMaterial({
        map: old.map,
        color: old.color,
        lightMap: this.texture,
        lightMapIntensity: this.data.intensity,  // undoes the bake's 0..1 scaling
        alphaTest: old.alphaTest,                // keep cut-outs (hedge leaves) cut out
        side: old.side,
        transparent: old.transparent,
        opacity: old.opacity
      });
      old.dispose();
    }

    const name = this.el.id || 'model';
    if (!merged.length) {
      console.info(`baked-lighting ${name}: not merged` +
        (this.data.merge ? ` (${skipped.join(', ') || 'too few meshes'})` : ' (merge: false)') +
        (kept.length ? `; left as exported: ${kept.map((m) => m.material.name).join(', ')}` : ''));
      return;
    }
    const nMaterials = new Set(merged.map((m) => m.material)).size;
    this.mergeMeshes(root, merged);
    console.info(`baked-lighting ${name}: merged ${nMaterials} materials → 1 call` +
      (skipped.length ? `; kept separate: ${skipped.join(', ')}` : '') +
      (kept.length ? `; left as exported: ${kept.map((m) => m.material.name).join(', ')}` : ''));
  },

  // Why a mesh can't go into the merged mesh ('' = it can).
  mergeProblem(m) {
    const mat = m.material;
    const geo = m.geometry;
    if (m.isSkinnedMesh || m.isInstancedMesh || m.morphTargetInfluences) return 'skinned/instanced/morph';
    if (Array.isArray(mat)) return 'multi-material';
    if (mat.transparent || mat.alphaTest > 0 || mat.opacity < 1) return 'transparent/alpha';
    if (!geo.attributes.uv1) return 'no uv1';
    if (geo.morphAttributes && Object.keys(geo.morphAttributes).length) return 'morph targets';
    const map = mat.map;
    if (map) {
      const img = map.image;
      if (!img || img.width !== MERGE_SIZE || img.height !== MERGE_SIZE) return 'texture not 1024²';
      if (!geo.attributes.uv) return 'no uv';
      if (map.channel !== 0 || map.flipY || map.rotation !== 0 || map.offset.x || map.offset.y ||
          map.repeat.x !== 1 || map.repeat.y !== 1) return 'texture transform';
      if (map.wrapS !== THREE.RepeatWrapping || map.wrapT !== THREE.RepeatWrapping) return 'not repeat-wrapped';
    }
    return '';
  },

  mergeMeshes(root, meshes) {
    // 1) One texture-array layer per distinct colour image.
    const layerOf = new Map();       // texture source uuid -> layer
    const images = [];
    let anisotropy = 1;
    for (const m of meshes) {
      const map = m.material.map;
      if (!map || layerOf.has(map.source.uuid)) continue;
      layerOf.set(map.source.uuid, images.length);
      images.push(map.image);
      anisotropy = Math.max(anisotropy, map.anisotropy);
    }
    const S = MERGE_SIZE;
    const layerBytes = S * S * 4;
    const pixels = new Uint8Array(layerBytes * Math.max(1, images.length));
    const canvas = makeCanvas(S, S);
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    images.forEach((img, i) => {
      ctx.clearRect(0, 0, S, S);
      ctx.drawImage(img, 0, 0, S, S);       // no flip: glTF maps use flipY = false
      pixels.set(ctx.getImageData(0, 0, S, S).data, i * layerBytes);
    });
    if (!images.length) pixels.fill(255);   // only plain colours: one white layer
    const arrayMap = new THREE.DataArrayTexture(pixels, S, S, Math.max(1, images.length));
    arrayMap.format = THREE.RGBAFormat;
    arrayMap.type = THREE.UnsignedByteType;
    arrayMap.colorSpace = THREE.SRGBColorSpace;
    arrayMap.wrapS = arrayMap.wrapT = THREE.RepeatWrapping;
    arrayMap.magFilter = THREE.LinearFilter;
    arrayMap.minFilter = THREE.LinearMipmapLinearFilter;
    arrayMap.generateMipmaps = true;
    arrayMap.anisotropy = anisotropy;
    arrayMap.needsUpdate = true;
    // Once on the GPU, drop the CPU copy (tens of MB per building).
    arrayMap.onUpdate = () => { arrayMap.image.data = null; arrayMap.onUpdate = null; };

    // 2) One geometry in the model root's local space.
    root.updateMatrixWorld(true);
    const toRoot = new THREE.Matrix4().copy(root.matrixWorld).invert();
    let nVerts = 0;
    let nIdx = 0;
    for (const m of meshes) {
      nVerts += m.geometry.attributes.position.count;
      nIdx += m.geometry.index ? m.geometry.index.count : m.geometry.attributes.position.count;
    }
    const pos = new Float32Array(nVerts * 3);
    const nor = new Float32Array(nVerts * 3);
    const uv = new Float32Array(nVerts * 2);
    const uv1 = new Float32Array(nVerts * 2);
    const layer = new Float32Array(nVerts);
    const tint = new Float32Array(nVerts * 3);
    const index = nVerts > 65535 ? new Uint32Array(nIdx) : new Uint16Array(nIdx);
    const mat4 = new THREE.Matrix4();
    const nmat = new THREE.Matrix3();
    const v = new THREE.Vector3();
    let vo = 0;
    let io = 0;
    for (const m of meshes) {
      const g = m.geometry;
      const a = g.attributes;
      const mat = m.material;
      mat4.multiplyMatrices(toRoot, m.matrixWorld);
      nmat.getNormalMatrix(mat4);
      const L = mat.map ? layerOf.get(mat.map.source.uuid) : -1;   // -1 = plain colour
      const c = mat.color;
      const n = a.position.count;
      for (let i = 0; i < n; i++) {
        const k = vo + i;
        v.fromBufferAttribute(a.position, i).applyMatrix4(mat4);
        pos[k * 3] = v.x; pos[k * 3 + 1] = v.y; pos[k * 3 + 2] = v.z;
        if (a.normal) {
          v.fromBufferAttribute(a.normal, i).applyMatrix3(nmat).normalize();
          nor[k * 3] = v.x; nor[k * 3 + 1] = v.y; nor[k * 3 + 2] = v.z;
        }
        if (a.uv) { uv[k * 2] = a.uv.getX(i); uv[k * 2 + 1] = a.uv.getY(i); }
        uv1[k * 2] = a.uv1.getX(i); uv1[k * 2 + 1] = a.uv1.getY(i);
        layer[k] = L;
        tint[k * 3] = c.r; tint[k * 3 + 1] = c.g; tint[k * 3 + 2] = c.b;
      }
      // Mirrored transforms flip the winding; swap two corners to keep front faces.
      const flip = mat4.determinant() < 0;
      const count = g.index ? g.index.count : n;
      for (let i = 0; i < count; i += 3) {
        const i0 = g.index ? g.index.getX(i) : i;
        const i1 = g.index ? g.index.getX(i + 1) : i + 1;
        const i2 = g.index ? g.index.getX(i + 2) : i + 2;
        index[io++] = vo + i0;
        index[io++] = vo + (flip ? i2 : i1);
        index[io++] = vo + (flip ? i1 : i2);
      }
      vo += n;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setAttribute('normal', new THREE.BufferAttribute(nor, 3));
    geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    geo.setAttribute('uv1', new THREE.BufferAttribute(uv1, 2));
    geo.setAttribute('aLayer', new THREE.BufferAttribute(layer, 1));
    geo.setAttribute('aTint', new THREE.BufferAttribute(tint, 3));
    geo.setIndex(new THREE.BufferAttribute(index, 1));
    geo.computeBoundingBox();
    geo.computeBoundingSphere();

    // 3) One unlit material: array texture x per-vertex tint x lightmap.
    // Same maths as MeshBasicMaterial's map x color: the array is sRGB (decoded to linear
    // by the GPU when sampled, like the original maps) and the tint is three.js's linear colour.
    const material = new THREE.MeshBasicMaterial({
      lightMap: this.texture,
      lightMapIntensity: this.data.intensity
    });
    material.userData.arrayMap = arrayMap;
    material.onBeforeCompile = (shader) => {
      shader.uniforms.arrayMap = { value: arrayMap };
      shader.vertexShader = shader.vertexShader
        .replace('#include <common>', `#include <common>
          attribute float aLayer;
          attribute vec3 aTint;
          flat varying float vLayer;
          varying vec3 vTint;
          varying vec2 vArrayUv;`)
        .replace('#include <uv_vertex>', `#include <uv_vertex>
          vLayer = aLayer;
          vTint = aTint;
          vArrayUv = uv;`);
      shader.fragmentShader = shader.fragmentShader
        .replace('#include <common>', `#include <common>
          uniform highp sampler2DArray arrayMap;
          flat varying float vLayer;
          varying vec3 vTint;
          varying vec2 vArrayUv;`)
        .replace('#include <map_fragment>', `
          // Sample outside the branch so mipmap derivatives stay valid.
          vec4 arrayTexel = texture(arrayMap, vec3(vArrayUv, max(vLayer, 0.0)));
          diffuseColor.rgb *= (vLayer < 0.0 ? vec3(1.0) : arrayTexel.rgb) * vTint;`);
    };
    material.customProgramCacheKey = () => 'baked-lighting-merged';

    // 4) Swap in the merged mesh; free the old meshes, materials and textures.
    const oldTextures = new Set();
    const oldMaterials = new Set();
    for (const m of meshes) {
      if (m.material.map) oldTextures.add(m.material.map);
      oldMaterials.add(m.material);
      m.geometry.dispose();
      m.removeFromParent();
    }
    // (Meshes kept separate are still in root and keep their textures.)
    oldMaterials.forEach((mt) => mt.dispose());
    root.traverse((o) => { if (o.isMesh && o.material.map) oldTextures.delete(o.material.map); });  // still used
    oldTextures.forEach((t) => {
      t.dispose();
      if (t.image && t.image.close) t.image.close();   // ImageBitmap
    });
    // Remove groups left empty by the merge.
    const empties = [];
    root.traverse((o) => { if (o !== root && !o.isMesh && !o.children.length) empties.push(o); });
    empties.forEach((o) => o.removeFromParent());

    const mergedMesh = new THREE.Mesh(geo, material);
    mergedMesh.name = 'baked-merged';
    root.add(mergedMesh);
    this.merged = mergedMesh;
  },

  remove() {
    this.el.removeEventListener('model-loaded', this.onLoaded);
    this.texture.dispose();
    if (this.merged) {
      this.merged.geometry.dispose();
      this.merged.material.userData.arrayMap.dispose();
      this.merged.material.dispose();
    }
  }
});

/* ------------------------------------------------------------------ */
/* glass-reflect                                                       */
/* ------------------------------------------------------------------ */
/*
 * Window glass that reflects the sky photo. Put it on a model entity (next to
 * baked-lighting, whose `keep` option leaves the "glass" material untouched):
 *
 *   <a-entity gltf-model="url(assets/models/nevius-store.glb)"
 *             baked-lighting="lightmap: ...; intensity: 1.1" glass-reflect>
 *
 * Every material named in `materials` (default "glass") becomes a smooth, non-metal
 * MeshStandardMaterial with the sky as its environment map: reflection is weak when
 * you look straight at the pane and strong at a glancing angle (Fresnel), like real
 * glass. The reflection is added on top of what shows through, so the glass keeps
 * its exported see-through alpha (the window backs behind it stay visible).
 * Still one draw call per glass mesh; no textures besides the shared environment map.
 *
 * The environment map is made ONCE for the whole scene (the glass-reflect system):
 * a PMREM (pre-blurred cube map) of the same equirectangular photo the #sky sphere
 * shows, turned to match the sky entity's rotation.
 */
AFRAME.registerSystem('glass-reflect', {
  schema: {
    sky: { default: '#sky' },                                         // the sky sphere entity
    src: { default: 'assets/textures/sky/sky-late-afternoon.jpg' }    // used if #sky has no src
  },

  // Promise of { texture, rotationY } (shared by all glass).
  getEnvMap() {
    if (this.envPromise) return this.envPromise;
    const skyEl = document.querySelector(this.data.sky);
    let src = this.data.src;
    let skyRotY = 0;
    if (skyEl) {
      const mat = skyEl.getAttribute('material');
      if (mat && typeof mat.src === 'string' && mat.src) src = mat.src;
      else if (mat && mat.src && mat.src.src) src = mat.src.src;      // <img> asset
      skyRotY = skyEl.object3D.rotation.y;
    }
    src = src.replace(/^url\((.*)\)$/, '$1');
    // The sky sphere (scale -1 1 1) puts the photo's u = 0 at azimuth atan2(z, x) = 0;
    // three.js's equirect lookup puts u = 0.5 there, i.e. half a turn apart. So the
    // env map is turned by the sky's rotation minus 180 degrees to line the two up.
    const rotationY = skyRotY - Math.PI;
    this.envPromise = new Promise((resolve) => {
      new THREE.TextureLoader().load(src, (tex) => {
        tex.colorSpace = THREE.SRGBColorSpace;
        tex.mapping = THREE.EquirectangularReflectionMapping;
        const pmrem = new THREE.PMREMGenerator(this.el.renderer);
        const rt = pmrem.fromEquirectangular(tex);
        pmrem.dispose();
        tex.dispose();
        this.envTarget = rt;
        resolve({ texture: rt.texture, rotationY });
      }, undefined, () => {
        console.warn(`glass-reflect: could not load sky ${src}; glass stays as exported`);
        resolve(null);
      });
    });
    return this.envPromise;
  },

  remove() {
    if (this.envTarget) this.envTarget.dispose();
  }
});

AFRAME.registerComponent('glass-reflect', {
  schema: {
    materials: { type: 'array', default: ['glass'] },
    intensity: { default: 1.2 },     // envMapIntensity: strength of the sky reflection (2.5 looked milky; owner 2026-11-10)
    roughness: { default: 0.05 }
  },

  init() {
    this.onLoaded = () => this.apply();
    this.el.addEventListener('model-loaded', this.onLoaded);
    if (this.el.getObject3D('mesh')) this.apply();
  },

  update() {
    // Live tweaks (e.g. from the console) on glass that is already converted.
    if (!this.glass) return;
    for (const m of this.glass) {
      m.envMapIntensity = this.data.intensity;
      m.roughness = this.data.roughness;
    }
  },

  apply() {
    const root = this.el.getObject3D('mesh');
    if (!root) return;
    const meshes = [];
    root.traverse((obj) => {
      if (!obj.isMesh || Array.isArray(obj.material)) return;
      const mat = obj.material;
      if (this.data.materials.includes(mat.name) && !mat.userData.glassReflect) meshes.push(obj);
    });
    if (!meshes.length) return;
    meshes.forEach((m) => { m.material.userData.glassReflect = true; });   // only once
    this.el.sceneEl.systems['glass-reflect'].getEnvMap().then((env) => {
      if (!env) return;
      const glassFor = new Map();       // exported material -> glass material
      for (const obj of meshes) {
        const old = obj.material;
        if (!glassFor.has(old)) {
          let mat = old;
          if (!old.isMeshStandardMaterial) {    // glTF gives Standard; be safe anyway
            mat = new THREE.MeshStandardMaterial({ name: old.name, color: old.color,
              map: old.map || null, opacity: old.opacity, side: old.side });
          }
          this.makeGlass(mat, env);
          glassFor.set(old, mat);
        }
        obj.material = glassFor.get(old);
      }
      glassFor.forEach((mat, old) => { if (mat !== old) old.dispose(); });
      this.glass = [...glassFor.values()];
      console.info(`glass-reflect ${this.el.id || 'model'}: ${this.glass.length} glass material(s), ` +
        `${meshes.length} mesh(es) reflect the sky`);
    });
  },

  makeGlass(mat, env) {
    mat.userData.glassReflect = true;
    mat.metalness = 0;
    mat.roughness = this.data.roughness;
    mat.envMap = env.texture;
    mat.envMapIntensity = this.data.intensity;
    if (mat.envMapRotation) mat.envMapRotation.set(0, env.rotationY, 0);   // three r162+
    mat.transparent = true;
    mat.depthWrite = false;
    // Blending is colour x alpha + behind x (1 - alpha). Dividing the reflected part
    // by alpha makes it add on top at full strength (real glass reflects regardless of
    // how much shows through), while the see-through amount stays the exported alpha.
    mat.onBeforeCompile = (shader) => {
      shader.fragmentShader = shader.fragmentShader.replace('#include <opaque_fragment>',
        `#include <opaque_fragment>
        gl_FragColor.rgb = totalDiffuse + totalEmissiveRadiance +
          totalSpecular / max(gl_FragColor.a, 0.05);`);
    };
    mat.customProgramCacheKey = () => 'glass-reflect';
    mat.needsUpdate = true;
  },

  remove() {
    this.el.removeEventListener('model-loaded', this.onLoaded);
  }
});

/* ------------------------------------------------------------------ */
/* gltf-places                                                         */
/* ------------------------------------------------------------------ */
/*
 * Loads ONE .glb that holds several separate objects (root nodes) and stands each
 * named node at its own spot, so the file, its textures and its lightmap are loaded
 * once. Each place is "node-name x y z turn" (scene metres; turn = degrees about Y),
 * separated by commas. Nodes that are not listed are left out.
 *
 *   <a-entity gltf-places="src: url(assets/models/vehicles.glb);
 *                          places: model-t 5.3 0 -30 0, buggy 5.4 0 -72 0"
 *             baked-lighting="lightmap: ...; intensity: 1.5; keep: glass, enamel"
 *             glass-reflect paint-reflect></a-entity>
 *
 * The nodes are moved BEFORE 'model-loaded' fires, so baked-lighting (which merges the
 * meshes in place) and the reflection components see them where they stand.
 */
AFRAME.registerComponent('gltf-places', {
  schema: {
    src:    { default: '' },
    places: { default: '' }
  },

  init() {
    const src = this.data.src.replace(/^url\((.*)\)$/, '$1');
    const places = this.data.places.split(',').map((s) => s.trim().split(/\s+/)).filter((p) => p.length >= 4);
    new THREE.GLTFLoader().load(src, (gltf) => {
      const root = new THREE.Group();
      for (const [name, x, y, z, turn] of places) {
        const node = gltf.scene.getObjectByName(name);
        if (!node) { console.warn(`gltf-places: no node "${name}" in ${src}`); continue; }
        const t = THREE.MathUtils.degToRad(+turn || 0);
        let py = +y, roll = 0;
        if (y === 'road' && window.STREET_GROUND) {
          // Stand on the crowned road: height under the left and right wheels (0.7 m
          // either side of the centre line) gives the height and the sideways lean.
          const rx = Math.cos(t) * 0.7, rz = -Math.sin(t) * 0.7;
          const yR = STREET_GROUND.roadY(+x + rx, +z + rz);
          const yL = STREET_GROUND.roadY(+x - rx, +z - rz);
          py = (yR + yL) / 2;
          roll = Math.atan2(yR - yL, 1.4);
        } else if (y === 'road') py = 0;
        node.position.set(+x, py, +z);
        node.rotation.order = 'YXZ';
        node.rotation.set(0, t, roll);
        root.add(node);
      }
      this.el.setObject3D('mesh', root);
      this.el.emit('model-loaded', { format: 'gltf', model: root });
    }, undefined, (err) => console.warn(`gltf-places: could not load ${src}`, err));
  },

  remove() {
    this.el.removeObject3D('mesh');
  }
});

/* ------------------------------------------------------------------ */
/* hide-beyond                                                         */
/* ------------------------------------------------------------------ */
/*
 * Stops drawing an entity while the viewer is further than `distance` metres from the
 * point (x, z). For side-street backdrops and their trees: they can only be seen from
 * near their own street mouth, but would otherwise be drawn (hidden behind the Main St
 * buildings) from everywhere. Checked twice a second.
 *
 *   <a-entity gltf-model="..." hide-beyond="x: -75; z: 5; distance: 90"></a-entity>
 */
AFRAME.registerComponent('hide-beyond', {
  schema: {
    x:        { default: 0 },
    z:        { default: 0 },
    distance: { default: 90 }
  },

  init() {
    this.pos = new THREE.Vector3();
    this.tick = AFRAME.utils.throttleTick(this.tick, 500, this);
  },

  tick() {
    const cam = this.el.sceneEl.camera;
    if (!cam) return;
    cam.getWorldPosition(this.pos);
    const dx = this.pos.x - this.data.x, dz = this.pos.z - this.data.z;
    this.el.object3D.visible = dx * dx + dz * dz <= this.data.distance * this.data.distance;
  }
});

/* ------------------------------------------------------------------ */
/* paint-reflect                                                       */
/* ------------------------------------------------------------------ */
/*
 * Glossy paint (a car's enamel): keeps the baked lightmap for its shading and adds a
 * reflection of the sky on top, from the same environment map the window glass uses.
 * Needs baked-lighting on the same entity with the paint's material name in its `keep`
 * list (so it is not flattened into the merged unlit mesh).
 */
AFRAME.registerComponent('paint-reflect', {
  schema: {
    materials: { type: 'array', default: ['enamel'] },
    intensity: { default: 0.8 }      // strength of the sky reflection
  },

  init() {
    this.onLoaded = () => this.apply();
    this.el.addEventListener('model-loaded', this.onLoaded);
    if (this.el.getObject3D('mesh')) this.apply();
  },

  update() {
    if (this.paint) this.paint.forEach((m) => { m.envMapIntensity = this.data.intensity; });
  },

  apply() {
    const root = this.el.getObject3D('mesh');
    const baked = this.el.components['baked-lighting'];
    if (!root) return;
    const mats = new Set();
    root.traverse((obj) => {
      if (obj.isMesh && !Array.isArray(obj.material) && obj.material.isMeshStandardMaterial &&
          this.data.materials.includes(obj.material.name)) mats.add(obj.material);
    });
    if (!mats.size) return;
    this.el.sceneEl.systems['glass-reflect'].getEnvMap().then((env) => {
      if (!env) return;
      mats.forEach((mat) => {
        if (baked) { mat.lightMap = baked.texture; mat.lightMapIntensity = baked.data.intensity; }
        mat.envMap = env.texture;
        mat.envMapIntensity = this.data.intensity;
        if (mat.envMapRotation) mat.envMapRotation.set(0, env.rotationY, 0);
        // The baked lightmap already holds the daylight. Without this the scene's own
        // lights are added on top and black paint turns primer-grey. Keep only the
        // lights' mirror-like highlight (the sun glint), drop their diffuse part.
        mat.onBeforeCompile = (shader) => {
          shader.fragmentShader = shader.fragmentShader.replace('#include <lights_fragment_begin>',
            `#include <lights_fragment_begin>
            irradiance = vec3(0.0);
            reflectedLight.directDiffuse = vec3(0.0);`);
        };
        mat.customProgramCacheKey = () => 'paint-reflect';
        mat.needsUpdate = true;
      });
      this.paint = [...mats];
      console.info(`paint-reflect ${this.el.id || 'model'}: ${mats.size} paint material(s) reflect the sky`);
    });
  },

  remove() {
    this.el.removeEventListener('model-loaded', this.onLoaded);
  }
});

/* ------------------------------------------------------------------ */
/* ground-patches                                                      */
/* ------------------------------------------------------------------ */
/*
 * Several flat rectangles on the ground (paths, walks) drawn as ONE mesh, so they
 * cost one draw call instead of one each. Each rectangle is "x z width depth"
 * (centre in scene metres, width along X, depth along Z); separate them with commas:
 *
 *   <a-entity ground-patches="rects: -12.85 -24.07 5.1 1.6, -11.75 -51.2 2.9 1.4;
 *                             y: 0.03; color: #b9b0a0"></a-entity>
 */
AFRAME.registerComponent('ground-patches', {
  schema: {
    rects: { default: '' },
    y:     { default: 0.03 },
    color: { type: 'color', default: '#b9b0a0' }
  },

  update() {
    this.remove();
    const pos = [];
    const idx = [];
    this.data.rects.split(',').forEach((r) => {
      const v = r.trim().split(/\s+/).map(Number);
      if (v.length !== 4 || v.some(isNaN)) return;
      const [x, z, w, d] = v;
      const i = pos.length / 3;
      pos.push(x - w / 2, 0, z - d / 2,  x + w / 2, 0, z - d / 2,
               x + w / 2, 0, z + d / 2,  x - w / 2, 0, z + d / 2);
      idx.push(i, i + 2, i + 1,  i, i + 3, i + 2);   // counter-clockwise seen from above
    });
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    geo.setIndex(idx);
    geo.computeVertexNormals();
    const mat = new THREE.MeshStandardMaterial({ color: this.data.color, roughness: 1 });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.y = this.data.y;
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

/* ------------------------------------------------------------------ */
/* foliage                                                             */
/* ------------------------------------------------------------------ */
/*
 * For tree models with leaf cards (see tools/blender/street_tree.py). Put it next to
 * gltf-model. Any material whose texture has transparency is drawn as a hard
 * cut-out (alpha test) and double-sided: no sorting problems, and cheap on Quest.
 */
AFRAME.registerComponent('foliage', {
  init() {
    this.onLoaded = () => {
      this.el.getObject3D('mesh').traverse((obj) => {
        const m = obj.material;
        if (!obj.isMesh || !m.map || !(m.transparent || m.alphaTest > 0 || m.name.includes('Leaves'))) return;
        m.transparent = false;
        m.alphaTest = 0.5;
        m.depthWrite = true;
        m.side = THREE.DoubleSide;
        m.needsUpdate = true;
      });
    };
    this.el.addEventListener('model-loaded', this.onLoaded);
  },

  remove() {
    this.el.removeEventListener('model-loaded', this.onLoaded);
  }
});

/* ------------------------------------------------------------------ */
/* instanced-trees                                                     */
/* ------------------------------------------------------------------ */
/*
 * Many copies of one tree model drawn with instancing: the model is loaded once and
 * each of its parts (bark, leaves, soil, edging) is ONE draw call for all the trees.
 * Each child entity marks one tree (position, rotation, scale); it has no model itself:
 *
 *   <a-entity id="street-trees" instanced-trees="src: url(assets/models/street-tree.glb)">
 *     <a-entity id="tree-1" position="7.5 0.175 -44" rotation="0 90 0" scale="1 1 1"></a-entity>
 *   </a-entity>
 *
 * Leaf materials get the same treatment as `foliage` (hard cut-out, double-sided).
 * The trees are lit by the scene's lights, exactly as single gltf-model trees would be.
 */
AFRAME.registerComponent('instanced-trees', {
  schema: {
    src: { type: 'model' }
  },

  init() {
    new THREE.GLTFLoader().load(this.data.src, (gltf) => this.build(gltf.scene),
      undefined, (err) => console.error('instanced-trees: could not load', this.data.src, err));
  },

  build(model) {
    // One transform per child entity, relative to this entity.
    const trees = Array.from(this.el.children).filter((c) => c.object3D);
    const matrices = trees.map((c) => { c.object3D.updateMatrix(); return c.object3D.matrix.clone(); });

    model.updateMatrixWorld(true);
    const group = new THREE.Group();
    model.traverse((obj) => {
      if (!obj.isMesh) return;
      // Bake the part's own offset inside the model into its geometry.
      const geo = obj.geometry.clone().applyMatrix4(obj.matrixWorld);
      const m = obj.material;
      if (m.map && (m.transparent || m.alphaTest > 0 || m.name.includes('Leaves'))) {
        m.transparent = false;
        m.alphaTest = 0.5;
        m.depthWrite = true;
        m.side = THREE.DoubleSide;
      }
      const inst = new THREE.InstancedMesh(geo, m, matrices.length);
      matrices.forEach((mx, i) => inst.setMatrixAt(i, mx));
      inst.instanceMatrix.needsUpdate = true;
      inst.computeBoundingBox();
      inst.computeBoundingSphere();   // covers every tree, so none pops out at the edges
      inst.name = obj.name;
      group.add(inst);
      obj.geometry.dispose();
    });
    this.el.setObject3D('mesh', group);
  },

  remove() {
    const group = this.el.getObject3D('mesh');
    if (!group) return;
    group.children.forEach((inst) => {
      inst.geometry.dispose();
      if (inst.material.map) inst.material.map.dispose();
      inst.material.dispose();
      inst.dispose();
    });
    this.el.removeObject3D('mesh');
  }
});

/* ------------------------------------------------------------------ */
/* street-props                                                        */
/* ------------------------------------------------------------------ */
/*
 * Street furniture from one kit model (assets/models/street-props.glb: one node per
 * prop, all at the origin, one shared material). Each child entity is one placement;
 * `data-prop` names the node(s) to stamp there (several separated by spaces):
 *
 *   <a-entity street-props="src: url(assets/models/street-props.glb)">
 *     <a-entity id="pole-W1" data-prop="pole pole_lamp" position="-6.9 0.15 -0.6" rotation="0 90 0"></a-entity>
 *     <a-entity id="arc-A1" data-prop="arc_lamp" data-span="pole-W1 pole-E1" position="0 8.35 1.2"></a-entity>
 *   </a-entity>
 *
 * All placements are baked into a few static meshes, one per z band (`bands` = the z
 * values where a new band starts), so the whole kit costs one draw call per band and
 * bands behind you are culled. The props keep the model's own lit material (no lightmap).
 *
 * It also draws the overhead wires (one more draw call): 6 sagging wires between each
 * pair of neighbouring poles on the same side of the street (from the insulators), and
 * for each placement with `data-span`, a span wire from one pole's eye bolt to the lamp's
 * hook and on to the other pole.
 */
const POLE_WIRES = [   // insulator wire grooves on the pole node (glTF local, metres)
  [0.148, 10.325, -1.05], [0.148, 10.325, -0.40], [0.148, 10.325, 0.40], [0.148, 10.325, 1.05],
  [0.151, 9.625, -1.05], [0.151, 9.625, 1.05]
];
const POLE_EYE = [0, 8.6, 0.18];   // eye bolt for cross-street span wires

AFRAME.registerComponent('street-props', {
  schema: {
    src:      { type: 'model' },
    bands:    { default: '-20, -60' },   // band edges along z (north = -z)
    sag:      { default: 0.012 },        // wire sag as a fraction of the span
    segments: { default: 12 },           // straight pieces per wire span
    wireColor: { type: 'color', default: '#1e1a17' }
  },

  init() {
    new THREE.GLTFLoader().load(this.data.src, (gltf) => this.build(gltf.scene),
      undefined, (err) => console.error('street-props: could not load', this.data.src, err));
  },

  build(model) {
    model.updateMatrixWorld(true);
    const nodes = new Map();
    let material = null;
    model.traverse((obj) => {
      if (!obj.isMesh) return;
      nodes.set(obj.name, obj);
      material = material || obj.material;
    });

    const edges = this.data.bands.split(',').map(Number).filter((n) => !isNaN(n)).sort((a, b) => b - a);
    const bands = edges.map(() => []).concat([[]]);   // one list of geometries per band
    const bandOf = (z) => { const i = edges.findIndex((e) => z > e); return i < 0 ? edges.length : i; };

    const places = Array.from(this.el.children).filter((c) => c.object3D && c.dataset.prop);
    const poles = [];
    let tris = 0;
    for (const c of places) {
      c.object3D.updateMatrix();
      const mx = c.object3D.matrix;
      for (const name of c.dataset.prop.trim().split(/\s+/)) {
        const node = nodes.get(name);
        if (!node) { console.warn('street-props: no node', name, 'for', c.id); continue; }
        const geo = node.geometry.clone().applyMatrix4(new THREE.Matrix4().multiplyMatrices(mx, node.matrixWorld));
        bands[bandOf(c.object3D.position.z)].push(geo);
        tris += (geo.index ? geo.index.count : geo.attributes.position.count) / 3;
        if (name === 'pole') poles.push(c);
      }
    }

    const group = new THREE.Group();
    bands.forEach((list, i) => {
      if (!list.length) return;
      const geo = mergeGeometries(list);   // js/kit.js
      geo.computeBoundingSphere();
      const mesh = new THREE.Mesh(geo, material);
      mesh.name = `street-props-band-${i}`;
      group.add(mesh);
    });
    nodes.forEach((n) => n.geometry.dispose());

    const wires = this.buildWires(poles, places);
    if (wires) group.add(wires);
    this.el.setObject3D('mesh', group);
    console.info(`street-props: ${places.length} placements, ${Math.round(tris)} triangles in ` +
      `${group.children.length - (wires ? 1 : 0)} meshes + wires`);
  },

  // Points along a hanging wire from a to b (a parabola, lowest by `sag` metres mid-span).
  wire(out, a, b, sag) {
    const n = this.data.segments;
    let prev = a;
    for (let i = 1; i <= n; i++) {
      const t = i / n;
      const p = new THREE.Vector3().lerpVectors(a, b, t);
      p.y -= 4 * sag * t * (1 - t);
      out.push(prev.x, prev.y, prev.z, p.x, p.y, p.z);
      prev = p;
    }
  },

  buildWires(poles, places) {
    const pts = [];
    const at = (c, local) => new THREE.Vector3(...local).applyMatrix4(c.object3D.matrix);
    // Along each side of the street: neighbouring poles, sorted north to south.
    for (const side of [-1, 1]) {
      const line = poles.filter((c) => Math.sign(c.object3D.position.x) === side)
        .sort((p, q) => p.object3D.position.z - q.object3D.position.z);
      for (let i = 0; i + 1 < line.length; i++) {
        for (const w of POLE_WIRES) {
          const a = at(line[i], w);
          const b = at(line[i + 1], w);
          this.wire(pts, a, b, this.data.sag * a.distanceTo(b));
        }
      }
    }
    // Span wires across the street, pulled down to the lamp hook in the middle.
    for (const c of places) {
      if (!c.dataset.span) continue;
      const hook = c.object3D.position.clone();
      for (const id of c.dataset.span.trim().split(/\s+/)) {
        const pole = document.getElementById(id);
        if (!pole) { console.warn('street-props: no pole', id, 'for', c.id); continue; }
        const eye = at(pole, POLE_EYE);
        this.wire(pts, eye, hook, this.data.sag * eye.distanceTo(hook));
      }
    }
    if (!pts.length) return null;
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
    geo.computeBoundingSphere();
    const lines = new THREE.LineSegments(geo, new THREE.LineBasicMaterial({ color: this.data.wireColor }));
    lines.name = 'street-props-wires';
    return lines;
  },

  remove() {
    const group = this.el.getObject3D('mesh');
    if (!group) return;
    const mats = new Set();
    group.children.forEach((m) => { m.geometry.dispose(); mats.add(m.material); });
    mats.forEach((m) => { if (m.map) m.map.dispose(); m.dispose(); });
    this.el.removeObject3D('mesh');
  }
});

/* ------------------------------------------------------------------ */
/* stick-debug (temporary)                                             */
/* ------------------------------------------------------------------ */
/*
 * Shows the thumbstick values in VR, just below your view, so you can check
 * that controller input is arriving. Put it on the camera:
 *   <a-entity id="camera" camera ... stick-debug></a-entity>
 * To remove it later, delete `stick-debug` from the camera (and this block if you like).
 */
AFRAME.registerComponent('stick-debug', {
  init() {
    this.rig = this.el.closest('[locomotion]');
    this.label = document.createElement('a-entity');
    this.label.setAttribute('position', '0 -0.32 -0.9');
    this.label.setAttribute('text', 'value: sticks; align: center; width: 0.9; color: #fff8e6');
    this.label.setAttribute('visible', false);  // only shown in VR
    this.el.appendChild(this.label);
    this.lastUpdate = 0;
    this.onEnter = () => this.label.setAttribute('visible', true);
    this.onExit = () => this.label.setAttribute('visible', false);
    this.el.sceneEl.addEventListener('enter-vr', this.onEnter);
    this.el.sceneEl.addEventListener('exit-vr', this.onExit);
  },

  remove() {
    this.el.sceneEl.removeEventListener('enter-vr', this.onEnter);
    this.el.sceneEl.removeEventListener('exit-vr', this.onExit);
    this.label.remove();
  },

  tick(time) {
    if (time - this.lastUpdate < 100 || !this.rig) return; // update ten times a second
    this.lastUpdate = time;
    const loco = this.rig.components.locomotion;
    const f = (n) => (n >= 0 ? ' ' : '') + n.toFixed(2);
    this.label.setAttribute('text', 'value',
      `L  x ${f(loco.stick.x)}  y ${f(loco.stick.y)}    R  x ${f(loco.turnStick)}\n` +
      `input: ${loco.inputSource}`);
  }
});


/* ------------------------------------------------------------------
   follow-rig: moves this entity in x/z to `factor` × the player rig's
   position (y stays). Used by the ground disc so its edge always meets
   the distant landscape ring (see far-landscape). Updates only when the
   rig has moved.
   ------------------------------------------------------------------ */
AFRAME.registerComponent('follow-rig', {
  schema: { factor: { default: 0.85 }, rig: { default: '#rig' } },
  init: function () { this.lastX = NaN; this.lastZ = NaN; },
  tick: function () {
    var rig = document.querySelector(this.data.rig);
    if (!rig) return;
    var p = rig.object3D.position;
    if (p.x === this.lastX && p.z === this.lastZ) return;
    this.lastX = p.x; this.lastZ = p.z;
    this.el.object3D.position.x = p.x * this.data.factor;
    this.el.object3D.position.z = p.z * this.data.factor;
  }
});

/* ------------------------------------------------------------------
   far-landscape: sets up assets/models/landscape.glb (tools/blender/landscape.py).
   - node landscape_far (terrain ring + tree lines, distance-compressed, haze baked
     into vertex colours): unlit, fog off; follows the rig at `factor` (0.85) so the
     hills do not slide past as you walk.
   - node landscape_town (house / tree / steeple silhouettes): unlit vertex colours,
     fog on, fixed in place.
   Entity sits at 0 0 0, rotation 0 0 0.
   ------------------------------------------------------------------ */
AFRAME.registerComponent('far-landscape', {
  schema: { factor: { default: 0.85 }, rig: { default: '#rig' } },
  init: function () {
    this.far = null; this.lastX = NaN; this.lastZ = NaN;
    this.el.addEventListener('model-loaded', this.setup.bind(this));
  },
  setup: function () {
    var root = this.el.getObject3D('mesh');
    if (!root) return;
    var far = root.getObjectByName('landscape_far');
    var town = root.getObjectByName('landscape_town');
    function convert(obj, fog) {
      if (!obj) return;
      obj.traverse(function (o) {
        if (!o.isMesh) return;
        var old = o.material;
        var opts = { vertexColors: true, fog: fog };
        if (old && old.map) {
          opts.map = old.map;
          opts.alphaTest = 0.5;
          opts.side = THREE.DoubleSide;
          old.map.generateMipmaps = true;
          old.map.minFilter = THREE.LinearMipmapLinearFilter;
          old.map.needsUpdate = true;
        }
        o.material = new THREE.MeshBasicMaterial(opts);
        if (old && old.dispose) old.dispose();
      });
    }
    convert(far, false);
    convert(town, true);
    this.far = far;
    this.lastX = NaN;
  },
  tick: function () {
    if (!this.far) return;
    var rig = document.querySelector(this.data.rig);
    if (!rig) return;
    var p = rig.object3D.position;
    if (p.x === this.lastX && p.z === this.lastZ) return;
    this.lastX = p.x; this.lastZ = p.z;
    this.far.position.x = p.x * this.data.factor;
    this.far.position.z = p.z * this.data.factor;
  }
});
