/*
 * people.js — townspeople you can talk to.
 *
 *   npc          A person who notices you when you walk up, turns to face you and talks.
 *                Their lines come from a JSON file in data/dialogue/ (one file per person).
 *   blob-shadow  A soft dark patch on the ground under someone's feet (1 draw call).
 *   dialogue     (system) The one shared speech panel, plus the controls that pick replies:
 *                  VR:      point the right controller's laser at a reply, pull the right trigger.
 *                  Desktop: click a reply with the mouse, or press 1, 2 or 3.
 *
 * Usage (see index.html):
 *   <a-entity id="npc-pickell" position="9.5 0.15 -8.45" rotation="0 -60 0"
 *     gltf-model="url(assets/models/npc-pickell.glb)"
 *     animation-mixer="clip: Idle; crossFadeDuration: 0.4"
 *     npc="dialogue: data/dialogue/pickell.json; radius: 2.5; closeRadius: 4"
 *     blob-shadow></a-entity>
 *
 * `animation-mixer` comes from aframe-extras (loaders bundle), loaded in index.html.
 * Adding another person = one more JSON file + one more entity like the one above.
 */

/* ------------------------------------------------------------------ */
/* Where the next line comes from: the "provider"                      */
/* ------------------------------------------------------------------ */
/*
 * scriptedProvider reads the hand-written dialogue from the person's JSON file.
 * getNode() returns a Promise so that a slower provider (e.g. an AI) can drop in later
 * without changing the panel code. A node is { text: "...", replies: [{ text, next }] };
 * next: null means "close the conversation".
 */
const scriptedProvider = {
  getNode(dialogue, nodeId /* , history */) {
    return Promise.resolve(dialogue.nodes[nodeId] || null);
  }
};

/*
 * ===== AI HOOK (future, NOT implemented, makes no network calls) =====
 * Idea: let a person answer free questions. The panel would ask an `aiProvider` instead of
 * scriptedProvider when the entity has `npc="...; ai: true"`. It would POST the
 * conversation so far plus the JSON's "brief" (who they are, the sourced facts, and
 * "say you don't know rather than invent") to a small server of our own (for example a
 * Cloudflare Worker that keeps the Claude API key secret; never put a key in this file),
 * and get back { text, replies: [2-3 suggested replies] }. A 4th reply such as
 * "Ask something else..." would then offer picked prompts or speech-to-text.
 * The owner has to decide on the running cost first. Sketch only:
 *
 *   const aiProvider = {
 *     async getNode(dialogue, nodeId, history) {
 *       // const res = await fetch('https://<our-worker>/talk', {
 *       //   method: 'POST',
 *       //   headers: { 'Content-Type': 'application/json' },
 *       //   body: JSON.stringify({ id: dialogue.id, brief: dialogue.brief, history })
 *       // });
 *       // return res.json();   // { text, replies: [{ text, next: 'ai' | null }] }
 *     }
 *   };
 */
function providerFor(npcData) {
  if (npcData.ai) {
    console.warn('npc: ai is not implemented yet; using the scripted dialogue.');
  }
  return scriptedProvider;
}

/* ------------------------------------------------------------------ */
/* npc                                                                 */
/* ------------------------------------------------------------------ */
AFRAME.registerComponent('npc', {
  schema: {
    dialogue:    { default: '' },   // URL of the JSON file
    radius:      { default: 2.5 },  // walk this close (m, horizontal) to start talking
    closeRadius: { default: 4 },    // walk further than this away to end the conversation
    turnTime:    { default: 0.6 },  // seconds to turn to face you (and back)
    brightness:  { default: 1.0 },  // scales the material colour if he looks too dark/bright
    ai:          { default: false } // future: use the AI provider (see AI HOOK above)
  },

  init() {
    this.dialogue = null;
    this.talking = false;      // panel open for this person
    this.talkedBefore = false; // this visit: use the "returnStart" node next time
    this.armed = true;         // must walk away past closeRadius before it can re-open
    this.history = [];         // [{ node, reply }] — for the future AI provider
    this.homeYaw = null;       // default facing, read from rotation on the first tick
    this.talkUntil = 0;        // play Talk until this time, then Idle
    this.lastCheck = 0;
    this.headPos = new THREE.Vector3();
    this.myPos = new THREE.Vector3();
    this.provider = providerFor(this.data);

    if (this.data.dialogue) {
      fetch(this.data.dialogue)
        .then((r) => r.json())
        .then((d) => { this.dialogue = d; })
        .catch((e) => console.error('npc: could not load ' + this.data.dialogue, e));
    }

    // Brightness tweak (one number), instead of adding lights.
    this.onModel = () => {
      if (this.data.brightness === 1) return;
      this.el.getObject3D('mesh').traverse((o) => {
        if (o.isMesh && o.material && o.material.color) o.material.color.multiplyScalar(this.data.brightness);
      });
    };
    this.el.addEventListener('model-loaded', this.onModel);
  },

  remove() {
    this.el.removeEventListener('model-loaded', this.onModel);
    if (this.talking) this.talkPanel().close();
  },

  talkPanel() { return this.el.sceneEl.systems.dialogue; },

  tick(time, delta) {
    const obj = this.el.object3D;
    if (this.homeYaw === null) this.homeYaw = obj.rotation.y;
    const cam = this.el.sceneEl.camera;
    if (!cam) return;
    cam.getWorldPosition(this.headPos);
    obj.getWorldPosition(this.myPos);

    // 1) Proximity check, ten times a second.
    if (time - this.lastCheck > 100 && this.dialogue) {
      this.lastCheck = time;
      const dist = Math.hypot(this.headPos.x - this.myPos.x, this.headPos.z - this.myPos.z);
      if (this.talking && dist > this.data.closeRadius) this.talkPanel().close();
      if (!this.talking && dist > this.data.closeRadius) this.armed = true;
      if (!this.talking && this.armed && dist <= this.data.radius && !this.talkPanel().active) {
        this.startConversation();
      }
    }

    // 2) Turn (yaw only): toward the visitor while talking, back home afterwards.
    //    Exponential easing: ~98% of the turn is done after `turnTime`.
    const target = this.talking
      ? Math.atan2(this.headPos.x - this.myPos.x, this.headPos.z - this.myPos.z)
      : this.homeYaw;
    let diff = target - obj.rotation.y;
    diff = Math.atan2(Math.sin(diff), Math.cos(diff)); // shortest way round
    if (Math.abs(diff) > 0.001) {
      const k = 1 - Math.exp(-(Math.min(delta, 100) / 1000) / (this.data.turnTime / 4));
      obj.rotation.y += diff * k;
    }

    // 3) Mouth/hands: Talk while he is "speaking" a line, then Idle.
    if (this.talkUntil && time > this.talkUntil) {
      this.talkUntil = 0;
      this.setClip('Idle');
    }
  },

  setClip(name) {
    const mixer = this.el.getAttribute('animation-mixer');
    if (mixer && mixer.clip !== name) this.el.setAttribute('animation-mixer', 'clip', name);
  },

  startConversation() {
    const d = this.dialogue;
    const first = this.talkedBefore && d.returnStart ? d.returnStart : d.start;
    this.talking = true;
    this.talkedBefore = true;
    this.armed = false;
    this.history = [];
    this.talkPanel().open(this);
    this.goTo(first);
  },

  // Ask the provider for a node and show it.
  goTo(nodeId) {
    this.currentId = nodeId;
    this.provider.getNode(this.dialogue, nodeId, this.history).then((node) => {
      if (!this.talking || this.currentId !== nodeId) return; // walked away meanwhile
      if (!node) { this.talkPanel().close(); return; }
      this.node = node;
      this.talkPanel().show(this.dialogue.title || this.dialogue.name, node);
      // Speaking time: about 14 characters a second, at least 3 s (one Talk loop).
      const secs = THREE.MathUtils.clamp(node.text.length / 14, 3, 12);
      this.talkUntil = this.el.sceneEl.time + secs * 1000;
      this.setClip('Talk');
    });
  },

  // Called by the dialogue system when the visitor picks reply number `index` (0-based).
  choose(index) {
    const reply = this.node && this.node.replies[index];
    if (!reply) return;
    this.history.push({ node: this.currentId, reply: reply.text });
    if (reply.next === null || reply.next === undefined) this.talkPanel().close();
    else this.goTo(reply.next);
  },

  // Called by the dialogue system when the panel closes (walked away or "[Walk on]").
  onClosed() {
    this.talking = false;
    this.node = null;
    this.currentId = null;
    this.talkUntil = 0;
    this.setClip('Idle');
  }
});

/* ------------------------------------------------------------------ */
/* blob-shadow                                                         */
/* ------------------------------------------------------------------ */
/*
 * A flat, soft-edged dark ellipse just above the ground under a person (the scene has
 * no real-time shadows). Costs 1 draw call; the first thing to drop if the budget is tight.
 */
let blobTexture = null;
function getBlobTexture() {
  if (blobTexture) return blobTexture;
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const ctx = c.getContext('2d');
  const g = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  g.addColorStop(0, 'rgba(0,0,0,1)');
  g.addColorStop(0.45, 'rgba(0,0,0,0.75)');
  g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 128, 128);
  blobTexture = new THREE.CanvasTexture(c);
  return blobTexture;
}

AFRAME.registerComponent('blob-shadow', {
  schema: {
    width:   { default: 0.9 },   // across the shoulders (m)
    depth:   { default: 0.6 },   // front to back (m)
    opacity: { default: 0.45 },
    y:       { default: 0.002 }  // above the entity's ground level, to avoid flicker
  },

  init() {
    const d = this.data;
    this.mesh = new THREE.Mesh(
      new THREE.PlaneGeometry(d.width, d.depth),
      new THREE.MeshBasicMaterial({
        color: 0x000000, alphaMap: getBlobTexture(), transparent: true,
        opacity: d.opacity, depthWrite: false
      })
    );
    this.mesh.rotation.x = -Math.PI / 2;
    this.mesh.position.y = d.y;
    this.mesh.renderOrder = 1;
    this.el.setObject3D('blob-shadow', this.mesh);
  },

  remove() {
    this.el.removeObject3D('blob-shadow');
    this.mesh.geometry.dispose();
    this.mesh.material.dispose();
  }
});

/* ------------------------------------------------------------------ */
/* dialogue (system): the speech panel and reply picking               */
/* ------------------------------------------------------------------ */
/*
 * One canvas-texture plane (0.80 x 0.50 m, 1 draw call) shared by everyone. Text and
 * reply boxes are drawn on a 2D canvas; picking works out which box was hit from the
 * ray's texture coordinate (uv) on the plane.
 */
const PANEL = {
  w: 0.8, h: 0.5,                 // metres
  cw: 1024, ch: 640,              // canvas pixels
  distance: 1.1,                  // from the visitor's head, along the line to the person
  side: 0.35,                     // shifted sideways so the person's face stays visible
  below: 0.45,                    // below head height (chest height)
  tilt: -10,                      // degrees; top leans back
  replaceAfter: 1.0,              // re-place when the visitor has moved this far (m)
  font: 'Georgia, "Times New Roman", serif',
  paper: 'rgba(243, 234, 214, 0.92)',
  ink: '#2b2118',
  rule: '#8a6a45',
  hover: 'rgba(196, 160, 104, 0.45)'
};

AFRAME.registerSystem('dialogue', {
  init() {
    this.active = null;     // the npc component currently talking
    this.node = null;
    this.title = '';
    this.hoverIndex = -1;
    this.mouseIndex = -1;
    this.boxes = [];        // reply boxes in canvas pixels: { x, y, w, h }
    this.lastPlaced = new THREE.Vector3(1e9, 0, 0);
    this.tmpHead = new THREE.Vector3();
    this.tmpNpc = new THREE.Vector3();
    this.ray = new THREE.Raycaster();
    this.ndc = new THREE.Vector2();

    // The canvas and its texture.
    this.canvas = document.createElement('canvas');
    this.canvas.width = PANEL.cw;
    this.canvas.height = PANEL.ch;
    this.ctx = this.canvas.getContext('2d');
    this.texture = new THREE.CanvasTexture(this.canvas);
    this.texture.colorSpace = THREE.SRGBColorSpace;
    this.texture.anisotropy = 4;

    // The panel entity (class dialogue-hit, so the controller laser can hit it).
    this.mesh = new THREE.Mesh(
      new THREE.PlaneGeometry(PANEL.w, PANEL.h),
      new THREE.MeshBasicMaterial({ map: this.texture, transparent: true, fog: false, depthTest: true })
    );
    this.mesh.renderOrder = 10;
    this.panelEl = document.createElement('a-entity');
    this.panelEl.id = 'dialogue-panel';
    this.panelEl.classList.add('dialogue-hit');
    this.panelEl.setAttribute('visible', false);
    this.panelEl.addEventListener('loaded', () => {
      this.panelEl.setObject3D('mesh', this.mesh);
      this.panelEl.object3D.rotation.order = 'YXZ';
    });
    this.el.appendChild(this.panelEl);

    // Desktop: keys 1-3 and mouse.
    this.onKey = (e) => {
      if (!this.active) return;
      const m = /^(?:Digit|Numpad)([1-9])$/.exec(e.code);
      if (m) this.pick(Number(m[1]) - 1);
    };
    window.addEventListener('keydown', this.onKey);
    this.onMouseMove = (e) => {
      if (!this.active) return;
      this.mouseIndex = this.indexFromMouse(e);
      this.el.canvas.style.cursor = this.mouseIndex >= 0 ? 'pointer' : '';
    };
    this.onClick = (e) => {
      if (!this.active) return;
      const i = this.indexFromMouse(e);
      if (i >= 0) this.pick(i);
    };
    const hookCanvas = () => {
      this.el.canvas.addEventListener('mousemove', this.onMouseMove);
      this.el.canvas.addEventListener('click', this.onClick);
    };
    if (this.el.canvas) hookCanvas();
    else this.el.addEventListener('render-target-loaded', hookCanvas, { once: true });

    // VR: right-controller laser (#right-laser in index.html), right trigger picks.
    // (The left trigger is the sprint button in `locomotion`; it is not used here.)
    this.onTrigger = () => {
      if (!this.active) return;
      const i = this.indexFromLaser();
      if (i >= 0) this.pick(i);
    };
    this.el.addEventListener('loaded', () => {
      this.laser = document.getElementById('right-laser');
      if (this.laser) this.laser.addEventListener('triggerdown', this.onTrigger);
    });
  },

  /* ---- opening, showing, closing ---- */

  open(npc) {
    this.active = npc;
    this.lastPlaced.set(1e9, 0, 0);
    this.place(true);
    this.panelEl.object3D.visible = true;
    // Desktop: free the mouse so replies can be clicked (click the scene again to look).
    const look = this.lookControls();
    if (look) look.el.setAttribute('look-controls', 'pointerLockEnabled', false);
    if (document.pointerLockElement) document.exitPointerLock();
    // VR: show the laser only while a panel is open (saves a draw call otherwise).
    if (this.laser) {
      this.laser.setAttribute('raycaster', 'enabled', true);
      this.laser.object3D.visible = true;
      const rc = this.laser.components.raycaster;
      if (rc) rc.refreshObjects();
    }
  },

  show(title, node) {
    this.title = title;
    this.node = node;
    this.hoverIndex = -1;
    this.mouseIndex = -1;
    this.draw();
  },

  close() {
    const npc = this.active;
    this.active = null;
    this.node = null;
    this.panelEl.object3D.visible = false;
    this.el.canvas.style.cursor = '';
    const look = this.lookControls();
    if (look) look.el.setAttribute('look-controls', 'pointerLockEnabled', true);
    if (this.laser) {
      this.laser.setAttribute('raycaster', 'enabled', false);
      this.laser.object3D.visible = false;
    }
    if (npc) npc.onClosed();
  },

  pick(index) {
    if (!this.active || !this.node || index < 0 || index >= this.node.replies.length) return;
    this.active.choose(index);
  },

  lookControls() {
    const cam = this.el.camera && this.el.camera.el;
    return cam && cam.components['look-controls'];
  },

  /* ---- placement: 1.1 m toward the person, 0.35 m aside, chest height ---- */

  place(force) {
    const cam = this.el.camera;
    if (!cam || !this.active) return;
    const head = cam.getWorldPosition(this.tmpHead);
    if (!force && head.distanceTo(this.lastPlaced) < PANEL.replaceAfter) return;
    this.lastPlaced.copy(head);
    const npcPos = this.active.el.object3D.getWorldPosition(this.tmpNpc);
    let fx = npcPos.x - head.x;
    let fz = npcPos.z - head.z;
    const dist = Math.hypot(fx, fz) || 1;
    fx /= dist; fz /= dist;
    // Stay in front of the person even if the visitor is very close.
    const along = Math.min(PANEL.distance, Math.max(0.6, dist - 0.5));
    // Visitor's right is (-fz, fx). Pick the side nearer the street's centre line, so the
    // panel never ends up inside a shop front.
    const rx = -fz * PANEL.side;
    const rz = fx * PANEL.side;
    const bx = head.x + fx * along;
    const bz = head.z + fz * along;
    const sign = Math.abs(bx + rx) <= Math.abs(bx - rx) ? 1 : -1;
    const o = this.panelEl.object3D;
    o.position.set(bx + sign * rx, head.y - PANEL.below, bz + sign * rz);
    o.rotation.set(THREE.MathUtils.degToRad(PANEL.tilt), Math.atan2(-fx, -fz), 0);
  },

  /* ---- drawing the canvas ---- */

  wrap(text, maxWidth) {
    const ctx = this.ctx;
    const lines = [];
    let line = '';
    for (const word of text.split(/\s+/)) {
      const test = line ? line + ' ' + word : word;
      if (line && ctx.measureText(test).width > maxWidth) {
        lines.push(line);
        line = word;
      } else line = test;
    }
    if (line) lines.push(line);
    return lines;
  },

  // Work out where everything goes. Shrinks the font if a long line would not fit.
  layout() {
    const ctx = this.ctx;
    const W = PANEL.cw, H = PANEL.ch, M = 44;
    for (let body = 42; body >= 26; body -= 2) {   // largest text that fits (max 42 px)
      const reply = Math.round(body * 0.9);
      ctx.font = `${body}px ${PANEL.font}`;
      const textLines = this.wrap(this.node.text, W - 2 * M);
      const bodyLH = Math.round(body * 1.28);
      let y = 104 + textLines.length * bodyLH + 16;
      ctx.font = `${reply}px ${PANEL.font}`;
      const replyLH = Math.round(reply * 1.22);
      const boxes = this.node.replies.map((r, i) => {
        const lines = this.wrap(r.text, W - 2 * M - 76);
        const h = lines.length * replyLH + 22;
        const box = { x: M - 8, y, w: W - 2 * M + 16, h, lines, label: String(i + 1) };
        y += h + 10;
        return box;
      });
      if (y <= H - 40 || body === 26) return { body, bodyLH, reply, replyLH, textLines, boxes, M };
    }
  },

  draw() {
    const ctx = this.ctx;
    const W = PANEL.cw, H = PANEL.ch;
    const L = this.layout();
    this.boxes = L.boxes;
    ctx.clearRect(0, 0, W, H);

    // Paper card with a double rule border.
    roundRect(ctx, 6, 6, W - 12, H - 12, 22);
    ctx.fillStyle = PANEL.paper;
    ctx.fill();
    ctx.lineWidth = 4;
    ctx.strokeStyle = PANEL.rule;
    ctx.stroke();
    roundRect(ctx, 18, 18, W - 36, H - 36, 14);
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Header: name and place, small caps feel, with a rule underneath.
    ctx.fillStyle = PANEL.ink;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'alphabetic';
    ctx.font = `italic bold 34px ${PANEL.font}`;
    ctx.fillText(this.title, W / 2, 66);
    ctx.fillStyle = PANEL.rule;
    ctx.fillRect(W / 2 - 220, 82, 440, 2);

    // What he says.
    ctx.textAlign = 'left';
    ctx.fillStyle = PANEL.ink;
    ctx.font = `${L.body}px ${PANEL.font}`;
    L.textLines.forEach((line, i) => ctx.fillText(line, L.M, 104 + L.body + i * L.bodyLH));

    // Numbered replies.
    ctx.font = `${L.reply}px ${PANEL.font}`;
    L.boxes.forEach((b, i) => {
      roundRect(ctx, b.x, b.y, b.w, b.h, 10);
      ctx.fillStyle = i === this.hoverIndex ? PANEL.hover : 'rgba(255, 250, 238, 0.55)';
      ctx.fill();
      ctx.lineWidth = i === this.hoverIndex ? 3 : 1.5;
      ctx.strokeStyle = PANEL.rule;
      ctx.stroke();
      ctx.fillStyle = PANEL.ink;
      ctx.font = `bold ${L.reply}px ${PANEL.font}`;
      ctx.fillText(b.label + '.', b.x + 22, b.y + 11 + L.reply);
      ctx.font = `${L.reply}px ${PANEL.font}`;
      b.lines.forEach((line, j) => ctx.fillText(line, b.x + 76, b.y + 11 + L.reply + j * L.replyLH));
    });

    // Small hint along the bottom.
    ctx.textAlign = 'center';
    ctx.fillStyle = 'rgba(43, 33, 24, 0.7)';
    ctx.font = `italic 22px ${PANEL.font}`;
    const hint = this.el.is('vr-mode')
      ? 'Point with the right controller and pull the trigger'
      : 'Click a reply, or press 1–3';
    ctx.fillText(hint, W / 2, H - 28);

    this.texture.needsUpdate = true;
  },

  /* ---- picking: which reply box is under the mouse / laser? ---- */

  indexFromUv(uv) {
    if (!uv) return -1;
    const px = uv.x * PANEL.cw;
    const py = (1 - uv.y) * PANEL.ch;
    return this.boxes.findIndex((b) => px >= b.x && px <= b.x + b.w && py >= b.y && py <= b.y + b.h);
  },

  indexFromMouse(e) {
    const cam = this.el.camera;
    if (!cam || !this.panelEl.object3D.visible) return -1;
    const rect = this.el.canvas.getBoundingClientRect();
    this.ndc.set(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1);
    this.ray.setFromCamera(this.ndc, cam);
    const hit = this.ray.intersectObject(this.mesh, false)[0];
    return hit ? this.indexFromUv(hit.uv) : -1;
  },

  indexFromLaser() {
    const rc = this.laser && this.laser.components.raycaster;
    if (!rc || !rc.data.enabled) return -1;
    const hit = rc.getIntersection(this.panelEl);
    return hit ? this.indexFromUv(hit.uv) : -1;
  },

  tick() {
    if (!this.active || !this.node) return;
    this.place(false);
    // Highlight: the laser in VR, the mouse on desktop.
    const laserIndex = this.el.is('vr-mode') ? this.indexFromLaser() : -1;
    const index = laserIndex >= 0 ? laserIndex : this.mouseIndex;
    if (index !== this.hoverIndex) {
      this.hoverIndex = index;
      this.draw();
    }
  },

  remove() {
    window.removeEventListener('keydown', this.onKey);
    if (this.el.canvas) {
      this.el.canvas.removeEventListener('mousemove', this.onMouseMove);
      this.el.canvas.removeEventListener('click', this.onClick);
    }
    if (this.laser) this.laser.removeEventListener('triggerdown', this.onTrigger);
    this.texture.dispose();
  }
});

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}
