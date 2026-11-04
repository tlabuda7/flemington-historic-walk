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
    boundsX:   { default: 10.2 },  // stay on the street and sidewalks
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
 */
const MERGE_SIZE = 1024;   // colour textures must be this size to go into the array

AFRAME.registerComponent('baked-lighting', {
  schema: {
    lightmap:  { default: '' },
    intensity: { default: 1.0 },
    merge:     { default: true }
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
    root.traverse((obj) => { if (obj.isMesh) meshes.push(obj); });

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
        lightMapIntensity: this.data.intensity   // undoes the bake's 0..1 scaling
      });
      old.dispose();
    }

    const name = this.el.id || 'model';
    if (!merged.length) {
      console.info(`baked-lighting ${name}: not merged` +
        (this.data.merge ? ` (${skipped.join(', ') || 'too few meshes'})` : ' (merge: false)'));
      return;
    }
    const nMaterials = new Set(merged.map((m) => m.material)).size;
    this.mergeMeshes(root, merged);
    console.info(`baked-lighting ${name}: merged ${nMaterials} materials → 1 call` +
      (skipped.length ? `; kept separate: ${skipped.join(', ')}` : ''));
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
