/* ------------------------------------------------------------------ */
/* street-ambience                                                     */
/* ------------------------------------------------------------------ */
/*
 * Ambient street sound (PLAN.md "Street ambiance", pass 1, part B).
 * Put it on the scene:  <a-scene street-ambience> ... </a-scene>
 *
 * - Silent until the visitor's first click / key / touch / Enter VR / VR trigger
 *   (browsers block sound before that). The AudioContext is only created then, so
 *   there is no autoplay warning.
 * - One shared Web Audio context and one listener, attached to the active camera
 *   (in VR three.js moves that camera with the headset, so the listener follows).
 * - Every clip is downloaded once after the scene has loaded and decoded once at the
 *   first gesture; voices reuse the decoded buffers.
 * - At most MAX_VOICES sounds play at once (3 loops + up to 3 one-shots).
 * - Timers run on the scene clock (tick), so they stop while the tab is hidden; the
 *   audio context is suspended then too.
 * - M mutes / unmutes.
 */
(function () {
  const DIR = 'assets/audio/';
  const FILES = [
    'amb-town-bed', 'amb-walla',
    'bird-robin', 'bird-cardinal', 'bird-titmouse', 'bird-catbird',
    'horse-carriage', 'horse-buckboard', 'horse-neigh', 'horse-snort',
    'modelt-run', 'modelt-stop', 'horn-oogah',
    'bell-five', 'shop-bell', 'train-whistle'
  ];
  const BIRDS = ['bird-robin', 'bird-cardinal', 'bird-titmouse', 'bird-catbird'];
  const MAX_VOICES = 6;

  // Unseen routes for passing traffic (PLAN.md): behind the buildings or far in the haze.
  const ROUTES = [
    [[-55, 1, 40], [-55, 1, -120]],    // R1 west back lane
    [[60, 1, -130], [60, 1, 40]],      // R2 east back lane
    [[220, 1, -84], [120, 1, -84]],    // R3 Bloomfield Ave, far east
    [[3, 1, -270], [3, 1, -200]]       // R4 Main St, far north
  ];

  const rand = (a, b) => a + Math.random() * (b - a);
  const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];

  AFRAME.registerComponent('street-ambience', {
    schema: {
      enabled: { default: true }
    },

    init() {
      this.raw = {};          // name -> ArrayBuffer (downloaded, not yet decoded)
      this.buffers = {};      // name -> AudioBuffer
      this.started = false;
      this.ready = false;
      this.muted = false;
      this.t = 0;             // seconds of (visible) running time since sound started
      this.events = {};       // scheduler name -> time (this.t) it fires next
      this.passes = [];       // moving traffic passes in progress
      this.voices = [];       // every THREE.Audio we made (for the voice cap)
      this.lastBird = '';
      this.tmpV = new THREE.Vector3();

      // Download the clips once the scene is up (not in <a-assets>: they must not
      // delay the first frame).
      const sceneEl = this.el.sceneEl;
      const fetchAll = () => {
        if (!this.data.enabled) return;
        FILES.forEach((name) => {
          fetch(DIR + name + '.ogg')
            .then((r) => { if (!r.ok) throw new Error(r.status); return r.arrayBuffer(); })
            .then((ab) => { this.raw[name] = ab; if (this.started) this.decode(name); })
            .catch((err) => console.warn('street-ambience: could not load', name, err));
        });
      };
      if (sceneEl.hasLoaded) fetchAll(); else sceneEl.addEventListener('loaded', fetchAll, { once: true });

      // First user gesture starts the sound.
      this.onGesture = (e) => {
        if (e && e.type === 'keydown') {
          if (e.code === 'KeyM' && !e.repeat) { this.toggleMute(); }
        }
        this.start();
      };
      ['pointerdown', 'touchstart', 'keydown', 'click'].forEach((type) =>
        window.addEventListener(type, this.onGesture, true));
      this.onEnterVR = () => {
        this.start();
        // Inside the headset, a controller trigger also counts as a gesture.
        const session = sceneEl.xrSession || (sceneEl.renderer && sceneEl.renderer.xr.getSession());
        if (session && !session._ambienceHooked) {
          session._ambienceHooked = true;
          session.addEventListener('selectstart', () => this.start());
          session.addEventListener('squeezestart', () => this.start());
        }
      };
      sceneEl.addEventListener('enter-vr', this.onEnterVR);

      this.onVisibility = () => {
        if (!this.ctx) return;
        if (document.hidden) this.ctx.suspend();
        else if (this.started) this.ctx.resume();
      };
      document.addEventListener('visibilitychange', this.onVisibility);

      this.onCameraActive = (evt) => {
        const cam = evt.detail.cameraEl.getObject3D('camera');
        if (this.listener && cam) cam.add(this.listener);
      };
      sceneEl.addEventListener('camera-set-active', this.onCameraActive);
    },

    /* Called on every gesture: the first one builds the audio graph; later ones just
       make sure the context is running (mobile/Quest browsers can suspend it). */
    start() {
      if (!this.data.enabled) return;
      if (this.started) {
        if (this.ctx && this.ctx.state !== 'running' && !document.hidden) this.ctx.resume();
        return;
      }
      this.started = true;
      const sceneEl = this.el.sceneEl;

      // One listener (creates the shared AudioContext inside the gesture).
      this.listener = sceneEl.audioListener || new THREE.AudioListener();
      sceneEl.audioListener = this.listener;
      this.ctx = this.listener.context;
      if (sceneEl.camera) sceneEl.camera.add(this.listener);
      this.ctx.resume();
      this.listener.gain.gain.value = this.muted ? 0 : 1;

      this.buildVoices();
      Object.keys(this.raw).forEach((name) => this.decode(name));
    },

    decode(name) {
      const ab = this.raw[name];
      if (!ab || this.buffers[name]) return;
      this.raw[name] = null;   // decodeAudioData detaches the ArrayBuffer
      this.ctx.decodeAudioData(ab).then((buf) => {
        this.buffers[name] = buf;
        this.onDecoded(name);
      }, (err) => console.warn('street-ambience: could not decode', name, err));
    },

    /* Fixed set of voices, made once. Positions/volumes from the PLAN.md table. */
    buildVoices() {
      const scene = this.el.sceneEl.object3D;
      const L = this.listener;
      const positional = (pos, ref, max, rolloff, parent) => {
        const a = new THREE.PositionalAudio(L);
        a.setDistanceModel('inverse');
        a.setRefDistance(ref);
        a.setMaxDistance(max);
        a.setRolloffFactor(rolloff);
        if (pos) a.position.set(pos[0], pos[1], pos[2]);
        (parent || scene).add(a);
        this.voices.push(a);
        return a;
      };

      // Town bed: non-positional loop.
      this.bed = new THREE.Audio(L);
      this.bed.setLoop(true);
      this.bed.gain.gain.value = 0;
      this.voices.push(this.bed);

      // Walla: hotel veranda and courthouse steps.
      this.wallaHotel = positional([10.5, 1.6, -30.75], 5, 45, 1.2);
      this.wallaCourt = positional([-15.5, 1.6, -6.85], 4, 35, 1.2);
      [this.wallaHotel, this.wallaCourt].forEach((a) => { a.setLoop(true); a.gain.gain.value = 0; });
      this.wallaCourt.offset = 20;

      // Birds: two voices so one can tail off while the next starts.
      this.birdVoices = [positional(null, 6, 60, 1), positional(null, 6, 60, 1)];
      this.treeCrowns = Array.from(document.querySelectorAll('#street-trees > a-entity')).map((el) => {
        const p = el.object3D.position;
        return [p.x, p.y + 6.5, p.z];
      });

      // Traffic: one moving emitter each for horses and the Model T, plus an "extra"
      // voice riding along for the neigh / snort / horn.
      this.horseMover = new THREE.Object3D();
      this.carMover = new THREE.Object3D();
      scene.add(this.horseMover, this.carMover);
      this.horseVoice = positional(null, 8, 120, 1, this.horseMover);
      this.horseExtra = positional(null, 8, 120, 1, this.horseMover);
      this.carVoice = positional(null, 8, 150, 1, this.carMover);
      this.carVoice.setLoop(true);
      this.carExtra = positional(null, 8, 150, 1, this.carMover);
      this.carStop = positional(null, 8, 150, 1);

      // Church bell (Baptist church, S end of Main), shop bell (Nevius door), train.
      this.bell = positional([30, 30, 260], 80, 600, 1);
      this.shopBell = positional([10.5, 2.2, -7.33], 2, 20, 2);
      this.train = positional([-500, 20, 150], 150, 800, 1);
      this.train.setPlaybackRate(0.8);

      // First times (seconds after the sound starts).
      this.events = {
        bird: rand(4, 10),
        horse: rand(25, 60),
        car: rand(90, 180),
        bell: 75,
        shop: rand(40, 120),
        train: rand(480, 840)
      };
    },

    onDecoded(name) {
      if (name === 'amb-town-bed') this.startLoop(this.bed, name, 0.35, 3);
      if (name === 'amb-walla') {
        this.startLoop(this.wallaHotel, name, 0.30, 3);
        this.startLoop(this.wallaCourt, name, 0.20, 3);
      }
      if (BIRDS.every((b) => this.buffers[b]) &&
          ['horse-carriage', 'modelt-run', 'bell-five', 'shop-bell'].every((b) => this.buffers[b])) {
        this.ready = true;
      }
    },

    /* ---------- helpers ---------- */

    startLoop(a, name, vol, fade) {
      if (a.isPlaying) return;
      a.setBuffer(this.buffers[name]);
      a.gain.gain.value = 0;
      a.play();
      this.snapPanner(a);
      this.fade(a, vol, fade);
    },

    fade(a, to, secs) {
      const g = a.gain.gain, now = this.ctx.currentTime;
      g.cancelScheduledValues(now);
      g.setValueAtTime(g.value, now);
      g.linearRampToValueAtTime(to, now + Math.max(0.01, secs));
    },

    /* Play a one-shot on voice `a` (if the voice cap allows). Returns true if it played. */
    shot(a, name, vol) {
      const buf = this.buffers[name];
      if (!buf || a.isPlaying || this.activeVoices() >= MAX_VOICES) return false;
      a.setBuffer(buf);
      a.setLoop(false);
      a.gain.gain.cancelScheduledValues(this.ctx.currentTime);
      a.gain.gain.setValueAtTime(vol, this.ctx.currentTime);
      a.play();
      this.snapPanner(a);
      return true;
    },

    /* Put a positional voice's panner straight at its object's position (three.js
       would otherwise glide it there from the last position over one frame). */
    snapPanner(a) {
      if (!a.panner) return;
      a.updateMatrixWorld(true);
      const p = a.getWorldPosition(this.tmpV), n = this.ctx.currentTime, pn = a.panner;
      if (pn.positionX) {
        pn.positionX.cancelScheduledValues(n); pn.positionX.setValueAtTime(p.x, n);
        pn.positionY.cancelScheduledValues(n); pn.positionY.setValueAtTime(p.y, n);
        pn.positionZ.cancelScheduledValues(n); pn.positionZ.setValueAtTime(p.z, n);
      } else {
        pn.setPosition(p.x, p.y, p.z);
      }
    },

    fadeOutStop(a, secs) {
      if (!a.isPlaying || !a.source) return;
      this.fade(a, 0, secs);
      a.source.stop(this.ctx.currentTime + secs + 0.05);   // onended clears isPlaying
    },

    activeVoices() {
      let n = 0;
      for (const v of this.voices) if (v.isPlaying) n++;
      return n;
    },

    toggleMute() {
      this.muted = !this.muted;
      if (!this.listener) return;   // applied when the sound starts
      const g = this.listener.gain.gain, now = this.ctx.currentTime;
      g.cancelScheduledValues(now);
      g.setValueAtTime(g.value, now);
      g.linearRampToValueAtTime(this.muted ? 0 : 1, now + 0.3);
    },

    listenerPos() {
      return this.listener.getWorldPosition(this.tmpV);
    },

    /* ---------- schedulers ---------- */

    tick(time, dtMs) {
      if (!this.ready || document.hidden || this.ctx.state !== 'running') return;
      const dt = Math.min(dtMs / 1000, 0.1);
      this.t += dt;
      const ev = this.events;

      if (this.t >= ev.bird) {
        ev.bird = this.t + (this.playBird() ? rand(8, 25) : 3);
      }
      if (this.t >= ev.horse) {
        ev.horse = this.t + (this.startHorsePass() ? rand(70, 150) : 15);
      }
      if (this.t >= ev.car) {
        ev.car = this.t + (this.startCarPass() ? rand(180, 360) : 15);
      }
      if (this.t >= ev.bell) {
        ev.bell = this.t + (this.shot(this.bell, 'bell-five', 0.6) ? 360 : 5);
      }
      if (this.t >= ev.shop) {
        // Only while the visitor is within 20 m of the Nevius door.
        const near = this.listenerPos().distanceTo(this.shopBell.position) <= 20;
        if (near) this.shot(this.shopBell, 'shop-bell', 0.5);
        ev.shop = this.t + rand(40, 120);
      }
      if (this.t >= ev.train) {
        ev.train = this.t + (this.shot(this.train, 'train-whistle', 0.35) ? rand(480, 840) : 20);
      }

      this.updatePasses(dt);
    },

    playBird() {
      if (!this.treeCrowns.length) return false;
      const voice = this.birdVoices.find((v) => !v.isPlaying);
      if (!voice) return false;
      const name = pick(BIRDS.filter((b) => b !== this.lastBird));
      const c = pick(this.treeCrowns);
      voice.position.set(c[0], c[1], c[2]);
      if (!this.shot(voice, name, rand(0.35, 0.5))) return false;
      this.lastBird = name;
      return true;
    },

    /* Horse + wagon: the clip (25-30 s) covers about 50-60 m of a random route at
       2 m/s, centred on the point of the route nearest the visitor. */
    startHorsePass() {
      if (this.horseVoice.isPlaying || this.carVoice.isPlaying || this.carStop.isPlaying) return false;
      if (this.activeVoices() >= MAX_VOICES - 1) return false;
      const name = pick(['horse-carriage', 'horse-buckboard'].filter((n) => this.buffers[n]));
      if (!name) return false;
      const buf = this.buffers[name];
      const route = this.orientedRoute();
      const len = this.routeLength(route);
      const seg = Math.min(len, buf.duration * 2.0);
      const near = this.nearestOnRoute(route) * len;
      const s0 = Math.max(0, Math.min(len - seg, near - seg / 2));
      const pass = {
        kind: 'horse', route, len, speed: 2.0, s: s0, sEnd: s0 + seg,
        mover: this.horseMover, voice: this.horseVoice, extra: this.horseExtra,
        age: 0, dur: seg / 2.0, extraAt: -1
      };
      if (Math.random() < 0.3) pass.extraAt = rand(0.3, 0.7) * pass.dur;
      this.placeMover(pass);
      this.horseVoice.setBuffer(buf);
      this.horseVoice.setLoop(false);
      this.horseVoice.gain.gain.value = 0;
      this.horseVoice.play();
      this.snapPanner(this.horseVoice);
      this.fade(this.horseVoice, 0.8, 2);
      this.passes.push(pass);
      return true;
    },

    /* Model T: modelt-run loops while it drives the whole route at 6 m/s. */
    startCarPass() {
      if (this.carVoice.isPlaying || this.carStop.isPlaying || this.horseVoice.isPlaying) return false;
      if (this.activeVoices() >= MAX_VOICES - 1 || !this.buffers['modelt-run']) return false;
      const route = this.orientedRoute();
      const len = this.routeLength(route);
      const pass = {
        kind: 'car', route, len, speed: 6.0, s: 0, sEnd: len,
        mover: this.carMover, voice: this.carVoice, extra: this.carExtra,
        age: 0, dur: len / 6.0, extraAt: -1,
        stops: Math.random() < 0.25 && !!this.buffers['modelt-stop']
      };
      if (Math.random() < 0.4) pass.extraAt = rand(0.2, 0.8) * pass.dur;
      this.placeMover(pass);
      this.carVoice.setBuffer(this.buffers['modelt-run']);
      this.carVoice.setLoop(true);
      this.carVoice.gain.gain.value = 0;
      this.carVoice.play();
      this.snapPanner(this.carVoice);
      this.fade(this.carVoice, 0.6, 2);
      this.passes.push(pass);
      return true;
    },

    updatePasses(dt) {
      for (let i = this.passes.length - 1; i >= 0; i--) {
        const p = this.passes[i];
        p.age += dt;
        p.s = Math.min(p.sEnd, p.s + p.speed * dt);
        this.placeMover(p);

        if (p.extraAt >= 0 && p.age >= p.extraAt) {
          p.extraAt = -1;
          if (p.kind === 'horse') this.shot(p.extra, pick(['horse-neigh', 'horse-snort']), 0.7);
          else this.shot(p.extra, 'horn-oogah', 0.5);
        }

        const left = p.dur - p.age;
        if (!p.fading && left <= 2) {
          p.fading = true;
          if (p.kind === 'car' && p.stops) {
            // Ends by pulling up and stopping where the route ends.
            this.fadeOutStop(p.voice, 1);
            this.carStop.position.copy(p.mover.position);
            this.shot(this.carStop, 'modelt-stop', 0.6);
          } else {
            this.fadeOutStop(p.voice, Math.max(0.1, left));
          }
        }
        if (p.age >= p.dur) this.passes.splice(i, 1);
      }
    },

    orientedRoute() {
      const r = pick(ROUTES);
      return Math.random() < 0.5 ? r : [r[1], r[0]];
    },

    routeLength(r) {
      return Math.hypot(r[1][0] - r[0][0], r[1][2] - r[0][2]);
    },

    /* 0..1 along the route of the point nearest the visitor. */
    nearestOnRoute(r) {
      const p = this.listenerPos();
      const ax = r[0][0], az = r[0][2], bx = r[1][0] - ax, bz = r[1][2] - az;
      const u = ((p.x - ax) * bx + (p.z - az) * bz) / (bx * bx + bz * bz);
      return Math.max(0, Math.min(1, u));
    },

    placeMover(p) {
      const u = p.s / p.len, a = p.route[0], b = p.route[1];
      p.mover.position.set(a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u);
    },

    remove() {
      ['pointerdown', 'touchstart', 'keydown', 'click'].forEach((type) =>
        window.removeEventListener(type, this.onGesture, true));
      this.el.sceneEl.removeEventListener('enter-vr', this.onEnterVR);
      this.el.sceneEl.removeEventListener('camera-set-active', this.onCameraActive);
      document.removeEventListener('visibilitychange', this.onVisibility);
      this.voices.forEach((v) => { if (v.isPlaying) v.stop(); if (v.parent) v.parent.remove(v); });
      this.voices = [];
      this.passes = [];
    }
  });
})();
