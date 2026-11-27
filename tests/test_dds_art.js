const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ddsArt = require('../static/dds-art.js');

function makeDdsHeader(width, height, pfFlags, fourCC = 0, bpp = 0, masks = [0, 0, 0, 0]) {
  const buf = new ArrayBuffer(128);
  const view = new DataView(buf);
  view.setUint32(0, 0x20534444, true); // "DDS "
  view.setUint32(4, 124, true);
  view.setUint32(12, height, true);
  view.setUint32(16, width, true);
  view.setUint32(76, 32, true);
  view.setUint32(80, pfFlags, true);
  view.setUint32(84, fourCC, true);
  view.setUint32(88, bpp, true);
  view.setUint32(92, masks[0], true);
  view.setUint32(96, masks[1], true);
  view.setUint32(100, masks[2], true);
  view.setUint32(104, masks[3], true);
  return new Uint8Array(buf);
}

function concatBytes(a, b) {
  const out = new Uint8Array(a.length + b.length);
  out.set(a, 0);
  out.set(b, a.length);
  return out.buffer;
}

// 1. DXT1 opaque (c0 > c1): c0 = pure red (0xF800), c1 = pure blue (0x001F).
{
  const hdr = makeDdsHeader(4, 4, 0x4, 0x31545844);
  const block = new Uint8Array(8);
  const dv = new DataView(block.buffer);
  dv.setUint16(0, 0xF800, true);
  dv.setUint16(2, 0x001F, true);
  // pixel 0 -> index 0 (red), pixel 1 -> index 1 (blue), pixel 2 -> index 2 (2/3 red + 1/3 blue)
  dv.setUint32(4, 0 | (1 << 2) | (2 << 4), true);
  const img = ddsArt.decodeDds(concatBytes(hdr, block));
  assert.equal(img.width, 4);
  assert.equal(img.height, 4);
  assert.deepEqual([...img.rgba.slice(0, 4)], [255, 0, 0, 255]);
  assert.deepEqual([...img.rgba.slice(4, 8)], [0, 0, 255, 255]);
  assert.equal(img.rgba[8], 170);
  assert.equal(img.rgba[10], 85);
}

// 2. DXT1 1-bit transparency (c0 <= c1): index 3 -> transparent black.
{
  const hdr = makeDdsHeader(4, 4, 0x4, 0x31545844);
  const block = new Uint8Array(8);
  const dv = new DataView(block.buffer);
  dv.setUint16(0, 0x001F, true);
  dv.setUint16(2, 0xF800, true);
  dv.setUint32(4, 3, true); // pixel 0 -> index 3 (transparent)
  const img = ddsArt.decodeDds(concatBytes(hdr, block));
  assert.deepEqual([...img.rgba.slice(0, 4)], [0, 0, 0, 0]);
}

// 3. DXT5 interpolated alpha: a0=200, a1=60, pixel 0 -> idx 0 (200), pixel 1 -> idx 1 (60).
{
  const hdr = makeDdsHeader(4, 4, 0x4, 0x35545844);
  const block = new Uint8Array(16);
  const dv = new DataView(block.buffer);
  block[0] = 200;
  block[1] = 60;
  // pixel 0 -> 0 (bits 0..2), pixel 1 -> 1 (bits 3..5) => 0b001_000 = 8
  block[2] = 8;
  dv.setUint16(8, 0x07E0, true); // pure green
  dv.setUint16(10, 0x0000, true);
  dv.setUint32(12, 0, true);
  const img = ddsArt.decodeDds(concatBytes(hdr, block));
  assert.deepEqual([...img.rgba.slice(0, 4)], [0, 255, 0, 200]);
  assert.deepEqual([...img.rgba.slice(4, 8)], [0, 255, 0, 60]);
}

// 4. DXT3 explicit 4-bit alpha: pixel 0 -> 0xF (255), pixel 1 -> 0x8 (136).
{
  const hdr = makeDdsHeader(4, 4, 0x4, 0x33545844);
  const block = new Uint8Array(16);
  const dv = new DataView(block.buffer);
  block[0] = 0x8F; // low nibble=15 (255), high nibble=8 (136)
  dv.setUint16(8, 0xFFFF, true);
  dv.setUint16(10, 0x0000, true);
  const img = ddsArt.decodeDds(concatBytes(hdr, block));
  assert.equal(img.rgba[3], 255);
  assert.equal(img.rgba[7], 136);
}

// 5. Uncompressed 32-bit BGRA8888 (with DDPF_ALPHAPIXELS) and X8R8G8B8 (without DDPF_ALPHAPIXELS).
{
  const hdr = makeDdsHeader(2, 1, 0x41, 0, 32, [0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000]);
  const pixels = new Uint8Array([10, 20, 30, 200, 255, 128, 64, 255]); // BGRA
  const img = ddsArt.decodeDds(concatBytes(hdr, pixels));
  assert.deepEqual([...img.rgba.slice(0, 4)], [30, 20, 10, 200]);
  assert.deepEqual([...img.rgba.slice(4, 8)], [64, 128, 255, 255]);

  // X8R8G8B8 (pfFlags = 0x40, DDPF_ALPHAPIXELS not set): unused byte 0 must decode as opaque 255.
  const hdrX = makeDdsHeader(1, 1, 0x40, 0, 32, [0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000]);
  const imgX = ddsArt.decodeDds(concatBytes(hdrX, new Uint8Array([10, 20, 30, 0])));
  assert.deepEqual([...imgX.rgba.slice(0, 4)], [30, 20, 10, 255]);
}

// 6. Failure paths: bad magic, truncated data, oversized dimensions, unknown FourCC.
assert.throws(() => ddsArt.decodeDds(new ArrayBuffer(128)), /valid DDS header/);
assert.throws(() => ddsArt.decodeDds(makeDdsHeader(4, 4, 0x4, 0x35545844).buffer), /Truncated DDS/);
assert.throws(() => ddsArt.decodeDds(makeDdsHeader(4096, 4, 0x4, 0x31545844).buffer), /Unsupported DDS dimensions/);
assert.throws(() => ddsArt.decodeDds(concatBytes(makeDdsHeader(4, 4, 0x4, 0x30315844), new Uint8Array(16))), /Unsupported DDS compression/);

// 7. Upgraded art.js produces distinct framed emblems with unique gradient IDs.
const artCtx = {window: {}};
vm.createContext(artCtx);
vm.runInContext(fs.readFileSync('static/art.js', 'utf8'), artCtx);
const art = artCtx.window.StellarisArt;
const laserSvg = art.techSvg('physics', 'tech_lasers_2');
const shieldSvg = art.techSvg('physics', 'tech_shields_2');
const megaSvg = art.techSvg('engineering', 'tech_mega_engineering');
const hallsSvg = art.techSvg('society', 'tech_galactic_halls');
assert.notEqual(laserSvg, shieldSvg);
assert.notEqual(megaSvg, hallsSvg);
assert.match(laserSvg, /sg-tech-svg/);
assert.notEqual(laserSvg.match(/id="sg-tbg-\d+"/)[0], shieldSvg.match(/id="sg-tbg-\d+"/)[0]);
assert.match(art.shipSvg('arkship'), /sg-svg-art/);
assert.match(art.planetSvg('pc_city'), /sg-planet-svg/);

// 8. loadFromFileList indexes technologies & planet_classes from webkitdirectory paths (works inside Program Files).
const info = ddsArt.loadFromFileList([
  {name: 'tech_lasers_1.dds', webkitRelativePath: 'icons/technologies/tech_lasers_1.dds'},
  {name: 'pc_continental.dds', webkitRelativePath: 'icons/concepts/planet_classes/pc_continental.dds'},
  {name: 'ignore_me.txt', webkitRelativePath: 'icons/readme.txt'},
  {name: 'unrelated.dds', webkitRelativePath: 'icons/jobs/job_miner.dds'},
]);
assert.equal(info.active, true);
assert.equal(info.techCount, 1);
assert.equal(info.planetCount, 1);
assert.equal(info.label, 'icons');
assert.throws(() => ddsArt.loadFromFileList([{name: 'readme.txt', webkitRelativePath: 'foo/readme.txt'}]), /No Stellaris/);
ddsArt.clear();
assert.equal(ddsArt.status().active, false);

console.log('DDS decoder (DXT1/DXT3/DXT5/BGRA + errors), file-list loader, and framed SVG art passed');
