/* Mini map: the 1921 Sanborn fire-insurance map (faded onto cream paper) with a clean
   Main St band, building names + addresses, people to talk to, a red "you" arrow and a
   north badge. North is always up; the window follows the player.

   - Desktop: an HTML canvas in the top-right corner. N shows / hides it.
   - VR (HTML is not drawn inside the headset): the Y button on the left controller pops the
     same canvas up on a small panel in front of you; Y again hides it.
     One draw call while shown, none while hidden.

   The map image and labels come from tools/prepare_minimap.py
   (assets/maps/minimap-1921.jpg + data/minimap.json). */
(function () {
  const PAPER = '#f4ecd8';
  const BROWN = '#5a3e28';

  AFRAME.registerComponent('minimap', {
    schema: {
      src: { default: 'data/minimap.json' },
      span: { default: 60 },          // metres shown across the map window
      size: { default: 512 },         // canvas pixels (square)
      cssSize: { default: 230 },      // desktop overlay size in CSS pixels
      panelWidth: { default: 0.6 },   // VR panel width, metres
      panelDistance: { default: 0.7 },
      panelDrop: { default: 0.22 },   // how far below eye level the VR panel sits
    },

    init() {
      const d = this.data;
      this.ready = false;
      this.desktopOn = true;
      this.vrOn = false;
      this.last = { t: -1e9, x: NaN, z: NaN, yaw: NaN };
      this.tmpV = new THREE.Vector3();
      this.tmpD = new THREE.Vector3();

      // Canvas (shared by the desktop overlay and the VR panel).
      this.canvas = document.createElement('canvas');
      this.canvas.width = this.canvas.height = d.size;
      this.ctx = this.canvas.getContext('2d');
      this.box = document.createElement('div');
      this.box.id = 'minimap-box';
      this.box.style.width = this.box.style.height = d.cssSize + 'px';
      this.canvas.style.width = this.canvas.style.height = '100%';
      this.box.appendChild(this.canvas);
      document.body.appendChild(this.box);

      // VR panel: a plane with the canvas as texture, child of the rig so it walks with you.
      this.texture = new THREE.CanvasTexture(this.canvas);
      this.texture.colorSpace = THREE.SRGBColorSpace;
      this.texture.anisotropy = 4;
      const mat = new THREE.MeshBasicMaterial({
        map: this.texture, transparent: true, depthTest: false, depthWrite: false, fog: false,
      });
      this.panel = new THREE.Mesh(new THREE.PlaneGeometry(d.panelWidth, d.panelWidth), mat);
      this.panel.renderOrder = 20;     // drawn after everything, never clipped by buildings
      this.panel.visible = false;
      this.panel.frustumCulled = false;

      fetch(d.src).then((r) => r.json()).then((json) => {
        this.map = json;
        this.img = new Image();
        this.img.onload = () => { this.ready = true; this.last.t = -1e9; this.last.x = NaN; };
        this.img.src = json.image;
      });

      this.onKey = (e) => {
        if (e.code !== 'KeyN' || e.repeat) return;
        this.setDesktop(!this.desktopOn);
      };
      this.onY = () => this.toggleVR();
      this.onEnterVR = () => { this.box.style.display = 'none'; };
      this.onExitVR = () => { this.setVR(false); this.setDesktop(this.desktopOn); };
      window.addEventListener('keydown', this.onKey);
      this.el.sceneEl.addEventListener('enter-vr', this.onEnterVR);
      this.el.sceneEl.addEventListener('exit-vr', this.onExitVR);

      this.el.sceneEl.addEventListener('loaded', () => {
        this.cam = document.getElementById('camera');
        this.rig = document.getElementById('rig');
        this.rig.object3D.add(this.panel);
        this.left = document.getElementById('left-hand');
        if (this.left) this.left.addEventListener('ybuttondown', this.onY);
      });
    },

    remove() {
      window.removeEventListener('keydown', this.onKey);
      this.el.sceneEl.removeEventListener('enter-vr', this.onEnterVR);
      this.el.sceneEl.removeEventListener('exit-vr', this.onExitVR);
      if (this.left) this.left.removeEventListener('ybuttondown', this.onY);
      if (this.panel.parent) this.panel.parent.remove(this.panel);
      this.panel.geometry.dispose(); this.panel.material.dispose(); this.texture.dispose();
      this.box.remove();
    },

    setDesktop(on) {
      this.desktopOn = on;
      this.box.style.display = on && !this.el.sceneEl.is('vr-mode') ? 'block' : 'none';
      this.last.x = NaN;   // redraw on next tick
    },

    /* Pop the panel up in front of the user (VR), or hide it. Also callable from the console. */
    toggleVR() { this.setVR(!this.vrOn); },

    setVR(on) {
      this.vrOn = on;
      this.panel.visible = on;
      if (!on || !this.cam) return;
      const cam = this.cam.object3D;
      cam.updateMatrixWorld();
      const eye = cam.getWorldPosition(this.tmpV);
      const fwd = cam.getWorldDirection(this.tmpD).negate();   // camera looks along −Z
      fwd.y = 0;
      if (fwd.lengthSq() < 1e-6) fwd.set(0, 0, -1);
      fwd.normalize();
      const d = this.data;
      const p = eye.clone().addScaledVector(fwd, d.panelDistance);
      p.y -= d.panelDrop;
      // Place it (in rig space, so it walks with you) and face the eye: tilted up a little.
      this.panel.position.copy(this.rig.object3D.worldToLocal(p));
      this.panel.lookAt(eye);
      this.panel.updateMatrixWorld();
      this.last.x = NaN;
    },

    tick(t) {
      if (!this.ready || !this.cam) return;
      const vr = this.el.sceneEl.is('vr-mode');
      const showing = vr ? this.vrOn : (this.desktopOn || this.vrOn);
      if (!showing || t - this.last.t < 100) return;            // ≤ 10 Hz
      const cam = this.cam.object3D;
      const pos = cam.getWorldPosition(this.tmpV);
      const dir = cam.getWorldDirection(this.tmpD);              // points backwards
      const yaw = Math.atan2(-dir.x, dir.z);                     // 0 = north, clockwise
      const L = this.last;
      let dy = Math.abs(yaw - L.yaw); if (dy > Math.PI) dy = 2 * Math.PI - dy;
      if (Math.hypot(pos.x - L.x, pos.z - L.z) < 0.15 && dy < 0.03) return;
      L.t = t; L.x = pos.x; L.z = pos.z; L.yaw = yaw;
      this.draw(pos.x, pos.z, yaw);
      this.texture.needsUpdate = true;
    },

    draw(px, pz, yaw) {
      const c = this.ctx, W = this.canvas.width, m = this.map, b = m.bounds;
      const S = W / this.data.span;                               // canvas px per metre
      const k = W / this.data.cssSize;                            // css px -> canvas px
      const X = (x) => W / 2 + (x - px) * S;
      const Z = (z) => W / 2 + (z - pz) * S;
      const r = 14 * k;

      c.clearRect(0, 0, W, W);
      c.save();
      roundRect(c, 0, 0, W, W, r); c.clip();
      c.fillStyle = PAPER; c.fillRect(0, 0, W, W);
      c.drawImage(this.img, X(b.x0), Z(b.z0), (b.x1 - b.x0) * S, (b.z1 - b.z0) * S);

      // Clean street bands with their names.
      for (const s of m.streets) {
        c.fillStyle = 'rgba(236, 224, 198, 0.82)';
        c.fillRect(X(s.x0), Z(s.z0), (s.x1 - s.x0) * S, (s.z1 - s.z0) * S);
        c.strokeStyle = 'rgba(90, 62, 40, 0.55)'; c.lineWidth = 1.2 * k;
        if (s.vertical) {
          c.beginPath();
          c.moveTo(X(s.x0), 0); c.lineTo(X(s.x0), W); c.moveTo(X(s.x1), 0); c.lineTo(X(s.x1), W);
          c.stroke();
        } else {
          c.strokeRect(X(s.x0), Z(s.z0), (s.x1 - s.x0) * S, (s.z1 - s.z0) * S);
        }
      }
      c.fillStyle = 'rgba(90, 62, 40, 0.6)';
      c.textAlign = 'center'; c.textBaseline = 'middle';
      c.font = `bold ${8 * k}px Georgia, serif`;
      for (const s of m.streets) {
        if (s.vertical) {
          // Repeat the name every 40 m so it is always somewhere in view.
          const x = X((s.x0 + s.x1) / 2);
          for (let z = Math.ceil(pz / 40) * 40 - 80; z <= pz + 80; z += 40) {
            if (z < s.z0 || z > s.z1) continue;
            c.save(); c.translate(x, Z(z)); c.rotate(-Math.PI / 2);
            c.fillText(s.name.split('').join(' '), 0, 0); c.restore();
          }
        } else {
          const cx = Math.min(Math.max(X((s.x0 + s.x1) / 2), X(s.x0) + 50 * k), X(s.x1) - 50 * k);
          c.fillText(s.name, Math.min(Math.max(cx, 50 * k), W - 50 * k), Z((s.z0 + s.z1) / 2));
        }
      }

      // Building tags: rounded cream tags (name + address), kept inside the window,
      // with a short leader to the building front.
      const pad = 4 * k;
      for (const l of m.labels) {
        const ax = X(l.atX), az = Z(l.atZ);
        if (az < -20 * k || az > W + 20 * k) continue;
        c.font = `bold ${9.5 * k}px Georgia, serif`;
        const w1 = c.measureText(l.name).width;
        c.font = `${8.5 * k}px Georgia, serif`;
        const w2 = c.measureText(l.addr).width;
        const tw = Math.max(w1, w2) + 2 * pad, th = 23 * k;
        let tx = X(l.x) - tw / 2;
        tx = Math.min(Math.max(tx, 3 * k), W - tw - 3 * k);
        const ty = Z(l.z) - th / 2;
        if (ty < 38 * k && tx < 36 * k) tx = 36 * k;              // keep clear of the north badge
        c.strokeStyle = 'rgba(90, 62, 40, 0.8)'; c.lineWidth = 1 * k;
        c.beginPath(); c.moveTo(ax, az); c.lineTo(tx + tw / 2, ty + th / 2); c.stroke();
        c.fillStyle = BROWN; c.beginPath(); c.arc(ax, az, 2.2 * k, 0, 7); c.fill();
        c.fillStyle = 'rgba(250, 244, 228, 0.94)';
        roundRect(c, tx, ty, tw, th, 5 * k); c.fill(); c.stroke();
        c.fillStyle = '#3b2717'; c.textAlign = 'center';
        c.font = `bold ${9.5 * k}px Georgia, serif`;
        c.fillText(l.name, tx + tw / 2, ty + 7.5 * k);
        c.fillStyle = '#6b4f38';
        c.font = `${8.5 * k}px Georgia, serif`;
        c.fillText(l.addr, tx + tw / 2, ty + 16.5 * k);
      }

      // People you can talk to.
      for (const p of m.people || []) {
        const x = X(p.x), z = Z(p.z);
        if (z < -20 * k || z > W + 20 * k) continue;
        c.fillStyle = '#2f5d8a'; c.strokeStyle = '#fff'; c.lineWidth = 1.5 * k;
        c.beginPath(); c.arc(x, z, 4 * k, 0, 7); c.fill(); c.stroke();
        c.font = `italic bold ${8.5 * k}px Georgia, serif`;
        c.textAlign = 'center';                                   // caption above the dot
        c.lineWidth = 3 * k; c.strokeStyle = 'rgba(250, 244, 228, 0.95)';
        const txt = p.name + (p.note ? ' (' + p.note + ')' : '');
        c.strokeText(txt, x, z - 10 * k); c.fillStyle = '#2f5d8a'; c.fillText(txt, x, z - 10 * k);
      }

      // "You" arrow at the centre, turned to the view direction.
      c.save();
      c.translate(W / 2, W / 2); c.rotate(yaw);
      c.beginPath();
      c.moveTo(0, -11 * k); c.lineTo(7.5 * k, 8 * k); c.lineTo(0, 4 * k); c.lineTo(-7.5 * k, 8 * k);
      c.closePath();
      c.fillStyle = '#c62f22'; c.strokeStyle = '#fff'; c.lineWidth = 1.8 * k;
      c.fill(); c.stroke();
      c.restore();

      // North badge.
      const nx = 20 * k, ny = 22 * k;
      c.fillStyle = 'rgba(250, 244, 228, 0.95)'; c.strokeStyle = BROWN; c.lineWidth = 1.5 * k;
      c.beginPath(); c.arc(nx, ny, 13 * k, 0, 7); c.fill(); c.stroke();
      c.fillStyle = '#c62f22';
      c.beginPath(); c.moveTo(nx, ny - 11 * k); c.lineTo(nx + 4 * k, ny - 3 * k);
      c.lineTo(nx - 4 * k, ny - 3 * k); c.closePath(); c.fill();
      c.fillStyle = BROWN; c.textAlign = 'center';
      c.font = `bold ${10 * k}px Georgia, serif`;
      c.fillText('N', nx, ny + 4 * k);
      c.restore();

      // Frame.
      c.strokeStyle = BROWN; c.lineWidth = 3 * k;
      roundRect(c, 1.5 * k, 1.5 * k, W - 3 * k, W - 3 * k, r - 1.5 * k); c.stroke();
    },
  });

  function roundRect(c, x, y, w, h, r) {
    c.beginPath();
    c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r);
    c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath();
  }
})();
