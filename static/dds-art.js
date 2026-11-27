/* Zero-dependency pure-JS local Stellaris .dds art loader (100% client-side).
   Reads the player's own locally installed Steam Stellaris folder via Chrome/Edge
   showDirectoryPicker() without uploading or redistributing any game assets. */
(() => {
  const DDS_MAGIC = 0x20534444; // "DDS "
  const FOURCC_DXT1 = 0x31545844;
  const FOURCC_DXT3 = 0x33545844;
  const FOURCC_DXT5 = 0x35545844;
  const DDPF_ALPHAPIXELS = 0x1;
  const DDPF_FOURCC = 0x4;
  const DDPF_RGB = 0x40;
  const MAX_DDS_BYTES = 8 * 1024 * 1024;
  const MAX_DIM = 2048;
  const MAX_INDEX_FILES = 5000;
  const MAX_CACHE_URLS = 300;
  const SAFE_KEY = /^[a-z0-9_]+$/;

  function rgb565(c) {
    return [
      (((c >> 11) & 31) * 255 + 15) / 31 | 0,
      (((c >> 5) & 63) * 255 + 31) / 63 | 0,
      ((c & 31) * 255 + 15) / 31 | 0,
    ];
  }

  function maskShiftAndMax(mask) {
    if (!mask) return {shift: 0, max: 0};
    let shift = 0;
    let m = mask >>> 0;
    while ((m & 1) === 0 && shift < 32) { m >>>= 1; shift++; }
    return {shift, max: m};
  }

  function decodeDds(arrayBuffer) {
    if (!(arrayBuffer instanceof ArrayBuffer) || arrayBuffer.byteLength < 128 || arrayBuffer.byteLength > MAX_DDS_BYTES) {
      throw new Error('Invalid or oversized DDS file.');
    }
    const view = new DataView(arrayBuffer);
    if (view.getUint32(0, true) !== DDS_MAGIC || view.getUint32(4, true) !== 124) {
      throw new Error('Not a valid DDS header.');
    }
    const height = view.getUint32(12, true);
    const width = view.getUint32(16, true);
    if (width < 1 || height < 1 || width > MAX_DIM || height > MAX_DIM) {
      throw new Error('Unsupported DDS dimensions.');
    }
    const pfFlags = view.getUint32(80, true);
    const fourCC = view.getUint32(84, true);
    const rgba = new Uint8ClampedArray(width * height * 4);

    if (pfFlags & DDPF_FOURCC) {
      const isDxt1 = fourCC === FOURCC_DXT1;
      const isDxt3 = fourCC === FOURCC_DXT3;
      const isDxt5 = fourCC === FOURCC_DXT5;
      if (!isDxt1 && !isDxt3 && !isDxt5) throw new Error('Unsupported DDS compression format.');
      const blockSize = isDxt1 ? 8 : 16;
      const blocksX = Math.max(1, (width + 3) >> 2);
      const blocksY = Math.max(1, (height + 3) >> 2);
      if (128 + blocksX * blocksY * blockSize > arrayBuffer.byteLength) {
        throw new Error('Truncated DDS pixel data.');
      }
      const bytes = new Uint8Array(arrayBuffer);
      const palette = new Uint8Array(16);
      const alphas = new Uint8Array(8);
      let off = 128;

      for (let by = 0; by < blocksY; by++) {
        for (let bx = 0; bx < blocksX; bx++) {
          let aLo = 0;
          let aHi = 0;
          const alphaOff = off;
          if (isDxt5) {
            const a0 = bytes[off];
            const a1 = bytes[off + 1];
            alphas[0] = a0;
            alphas[1] = a1;
            if (a0 > a1) {
              for (let i = 1; i <= 6; i++) alphas[i + 1] = ((7 - i) * a0 + i * a1 + 3) / 7 | 0;
            } else {
              for (let i = 1; i <= 4; i++) alphas[i + 1] = ((5 - i) * a0 + i * a1 + 2) / 5 | 0;
              alphas[6] = 0;
              alphas[7] = 255;
            }
            aLo = bytes[off + 2] | (bytes[off + 3] << 8) | (bytes[off + 4] << 16);
            aHi = bytes[off + 5] | (bytes[off + 6] << 8) | (bytes[off + 7] << 16);
            off += 8;
          } else if (isDxt3) {
            off += 8;
          }

          const c0 = view.getUint16(off, true);
          const c1 = view.getUint16(off + 2, true);
          const [r0, g0, b0] = rgb565(c0);
          const [r1, g1, b1] = rgb565(c1);
          palette[0] = r0; palette[1] = g0; palette[2] = b0; palette[3] = 255;
          palette[4] = r1; palette[5] = g1; palette[6] = b1; palette[7] = 255;
          if (!isDxt1 || c0 > c1) {
            palette[8] = (2 * r0 + r1 + 1) / 3 | 0;
            palette[9] = (2 * g0 + g1 + 1) / 3 | 0;
            palette[10] = (2 * b0 + b1 + 1) / 3 | 0;
            palette[11] = 255;
            palette[12] = (r0 + 2 * r1 + 1) / 3 | 0;
            palette[13] = (g0 + 2 * g1 + 1) / 3 | 0;
            palette[14] = (b0 + 2 * b1 + 1) / 3 | 0;
            palette[15] = 255;
          } else {
            palette[8] = (r0 + r1) >> 1;
            palette[9] = (g0 + g1) >> 1;
            palette[10] = (b0 + b1) >> 1;
            palette[11] = 255;
            palette[12] = 0; palette[13] = 0; palette[14] = 0; palette[15] = 0;
          }
          const colorBits = view.getUint32(off + 4, true);
          off += 8;

          for (let py = 0; py < 4; py++) {
            const y = (by << 2) + py;
            if (y >= height) continue;
            for (let px = 0; px < 4; px++) {
              const x = (bx << 2) + px;
              if (x >= width) continue;
              const idx = py * 4 + px;
              const ci = ((colorBits >>> (idx * 2)) & 3) * 4;
              let alpha = palette[ci + 3];
              if (isDxt3) {
                const byteVal = bytes[alphaOff + (idx >> 1)];
                alpha = ((idx & 1) ? (byteVal >>> 4) : (byteVal & 0xf)) * 17;
              } else if (isDxt5) {
                const ai = idx < 8 ? ((aLo >>> (idx * 3)) & 7) : ((aHi >>> ((idx - 8) * 3)) & 7);
                alpha = alphas[ai];
              }
              const dst = (y * width + x) * 4;
              rgba[dst] = palette[ci];
              rgba[dst + 1] = palette[ci + 1];
              rgba[dst + 2] = palette[ci + 2];
              rgba[dst + 3] = alpha;
            }
          }
        }
      }
      return {width, height, rgba};
    }

    if (pfFlags & DDPF_RGB) {
      const bpp = view.getUint32(88, true);
      if (bpp !== 24 && bpp !== 32) throw new Error('Unsupported uncompressed DDS bit depth.');
      const stride = bpp / 8;
      if (128 + width * height * stride > arrayBuffer.byteLength) {
        throw new Error('Truncated uncompressed DDS data.');
      }
      const rSpec = maskShiftAndMax(view.getUint32(92, true));
      const gSpec = maskShiftAndMax(view.getUint32(96, true));
      const bSpec = maskShiftAndMax(view.getUint32(100, true));
      const aSpec = (pfFlags & DDPF_ALPHAPIXELS) ? maskShiftAndMax(view.getUint32(104, true)) : {shift: 0, max: 0};
      const bytes = new Uint8Array(arrayBuffer);
      let off = 128;
      for (let i = 0; i < width * height; i++) {
        const px = bpp === 32
          ? (bytes[off] | (bytes[off + 1] << 8) | (bytes[off + 2] << 16) | (bytes[off + 3] << 24)) >>> 0
          : (bytes[off] | (bytes[off + 1] << 8) | (bytes[off + 2] << 16)) >>> 0;
        off += stride;
        const dst = i * 4;
        rgba[dst] = rSpec.max ? ((((px >>> rSpec.shift) & rSpec.max) >>> 0) * 255 / rSpec.max) | 0 : 0;
        rgba[dst + 1] = gSpec.max ? ((((px >>> gSpec.shift) & gSpec.max) >>> 0) * 255 / gSpec.max) | 0 : 0;
        rgba[dst + 2] = bSpec.max ? ((((px >>> bSpec.shift) & bSpec.max) >>> 0) * 255 / bSpec.max) | 0 : 0;
        rgba[dst + 3] = aSpec.max ? ((((px >>> aSpec.shift) & aSpec.max) >>> 0) * 255 / aSpec.max) | 0 : 255;
      }
      return {width, height, rgba};
    }
    throw new Error('Unsupported DDS pixel format.');
  }

  async function trySubdir(handle, segments) {
    let cur = handle;
    for (const seg of segments) {
      try { cur = await cur.getDirectoryHandle(seg); }
      catch { return null; }
    }
    return cur;
  }

  async function indexImageHandles(dirHandle, targetMap) {
    if (!dirHandle) return 0;
    let count = 0;
    for await (const [name, entry] of dirHandle.entries()) {
      if (count >= MAX_INDEX_FILES) break;
      if (entry.kind !== 'file') continue;
      const lower = name.toLowerCase();
      let ext = '';
      if (lower.endsWith('.dds')) ext = '.dds';
      else if (lower.endsWith('.png')) ext = '.png';
      else if (lower.endsWith('.webp')) ext = '.webp';
      else continue;
      const stem = lower.slice(0, -ext.length);
      if (!SAFE_KEY.test(stem)) continue;
      // Prefer .png/.webp if both exist, otherwise .dds.
      if (!targetMap.has(stem) || ext !== '.dds') {
        targetMap.set(stem, {handle: entry, ext});
      }
      count++;
    }
    return targetMap.size;
  }

  const techHandles = new Map();
  const planetHandles = new Map();
  const urlCache = new Map();
  const inflight = new Map();
  let folderLabel = '';
  let generation = 0;

  function revokeUrl(url) {
    if (!url) return;
    if (typeof document !== 'undefined') {
      document.querySelectorAll('img[data-local-art-loaded]').forEach(img => {
        if (img.src === url) {
          img.hidden = true;
          img.removeAttribute('src');
          delete img.dataset.localArtLoaded;
        }
      });
    }
    if (typeof URL !== 'undefined' && URL.revokeObjectURL) URL.revokeObjectURL(url);
  }

  function cacheSet(cacheKey, url) {
    if (urlCache.has(cacheKey)) {
      const old = urlCache.get(cacheKey);
      urlCache.delete(cacheKey);
      if (old && old !== url) revokeUrl(old);
    }
    urlCache.set(cacheKey, url);
    while (urlCache.size > MAX_CACHE_URLS) {
      const oldestKey = urlCache.keys().next().value;
      const oldestUrl = urlCache.get(oldestKey);
      urlCache.delete(oldestKey);
      revokeUrl(oldestUrl);
    }
  }

  async function decodeHandleToBlobUrl(entry) {
    const file = await entry.handle.getFile();
    if (file.size > MAX_DDS_BYTES) return null;
    if (entry.ext !== '.dds') return URL.createObjectURL(file);
    const decoded = decodeDds(await file.arrayBuffer());
    const canvas = document.createElement('canvas');
    canvas.width = decoded.width;
    canvas.height = decoded.height;
    try {
      const ctx = canvas.getContext('2d');
      if (!ctx) return null;
      const imgData = new ImageData(decoded.rgba, decoded.width, decoded.height);
      ctx.putImageData(imgData, 0, 0);
      const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
      return blob ? URL.createObjectURL(blob) : null;
    } finally {
      canvas.width = 0;
      canvas.height = 0;
    }
  }

  async function getUrl(kind, rawKey) {
    const key = String(rawKey || '').toLowerCase().trim();
    if (!SAFE_KEY.test(key)) return null;
    const handles = kind === 'planet' ? planetHandles : techHandles;
    const entry = handles.get(key);
    if (!entry) return null;
    const cacheKey = `${kind}:${key}`;
    if (urlCache.has(cacheKey)) {
      const hit = urlCache.get(cacheKey);
      urlCache.delete(cacheKey);
      urlCache.set(cacheKey, hit);
      return hit;
    }
    if (inflight.has(cacheKey)) return inflight.get(cacheKey);
    const gen = generation;
    const promise = decodeHandleToBlobUrl(entry)
      .then(url => {
        if (gen !== generation) {
          if (url && typeof URL !== 'undefined' && URL.revokeObjectURL) URL.revokeObjectURL(url);
          return null;
        }
        inflight.delete(cacheKey);
        if (url) cacheSet(cacheKey, url);
        return url;
      })
      .catch(() => {
        if (gen === generation) inflight.delete(cacheKey);
        return null;
      });
    inflight.set(cacheKey, promise);
    return promise;
  }

  function clear() {
    generation++;
    techHandles.clear();
    planetHandles.clear();
    inflight.clear();
    for (const url of urlCache.values()) {
      if (url && typeof URL !== 'undefined' && URL.revokeObjectURL) URL.revokeObjectURL(url);
    }
    urlCache.clear();
    folderLabel = '';
    if (typeof document !== 'undefined') {
      document.querySelectorAll('img[data-local-art-loaded]').forEach(img => {
        img.hidden = true;
        img.removeAttribute('src');
        delete img.dataset.localArtLoaded;
      });
    }
  }

  async function pickDirectory() {
    if (typeof window === 'undefined' || typeof window.showDirectoryPicker !== 'function') {
      throw new Error('Local game art loading requires Chrome, Edge, or Brave.');
    }
    const root = await window.showDirectoryPicker({mode: 'read'});
    const rootLower = String(root.name || '').toLowerCase();
    const isPlanetDirDirect = rootLower === 'planet_classes';
    const techDir = isPlanetDirDirect ? null : (
      (await trySubdir(root, ['gfx', 'interface', 'icons', 'technologies']))
      || (await trySubdir(root, ['interface', 'icons', 'technologies']))
      || (await trySubdir(root, ['icons', 'technologies']))
      || (await trySubdir(root, ['technologies']))
      || root
    );
    const planetDir = isPlanetDirDirect ? root : (
      (await trySubdir(root, ['gfx', 'interface', 'icons', 'concepts', 'planet_classes']))
      || (await trySubdir(root, ['interface', 'icons', 'concepts', 'planet_classes']))
      || (await trySubdir(root, ['icons', 'concepts', 'planet_classes']))
      || (await trySubdir(root, ['concepts', 'planet_classes']))
      || (await trySubdir(root, ['planet_classes']))
    );

    const nextTech = new Map();
    const nextPlanet = new Map();
    await indexImageHandles(techDir, nextTech);
    await indexImageHandles(planetDir, nextPlanet);
    if (!nextTech.size && !nextPlanet.size) {
      throw new Error('No Stellaris .dds/.png icons found. Select your Stellaris folder or gfx/interface/icons/technologies.');
    }
    clear();
    for (const [k, v] of nextTech.entries()) techHandles.set(k, v);
    for (const [k, v] of nextPlanet.entries()) planetHandles.set(k, v);
    folderLabel = root.name || 'Stellaris';
    hydrate(document);
    return status();
  }

  function hydrate(root) {
    if (!techHandles.size && !planetHandles.size) return;
    const scope = root && typeof root.querySelectorAll === 'function' ? root : (typeof document !== 'undefined' ? document : null);
    if (!scope) return;
    const gen = generation;
    scope.querySelectorAll('img[data-local-art-kind][data-local-art-key]').forEach(img => {
      const kind = img.dataset.localArtKind;
      const key = String(img.dataset.localArtKey || '').toLowerCase();
      if (!key || img.dataset.localArtLoaded === `${kind}:${key}`) return;
      getUrl(kind, key).then(url => {
        if (gen !== generation || !url || img.dataset.localArtKey?.toLowerCase() !== key) return;
        img.src = url;
        img.hidden = false;
        img.dataset.localArtLoaded = `${kind}:${key}`;
      });
    });
  }

  function status() {
    return {
      active: techHandles.size > 0 || planetHandles.size > 0,
      techCount: techHandles.size,
      planetCount: planetHandles.size,
      label: folderLabel,
    };
  }

  const api = {
    isSupported: () => typeof window !== 'undefined' && typeof window.showDirectoryPicker === 'function',
    decodeDds,
    pickDirectory,
    getUrl,
    hydrate,
    clear,
    status,
  };
  if (typeof window !== 'undefined') window.StellarisLocalArt = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})();
