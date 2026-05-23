#!/usr/bin/env node
// Generates solid-color PWA icons using only Node.js built-ins (no npm deps).
// Output: mobile/public/icons/doglog-192.png and doglog-512.png
const zlib = require('node:zlib')
const fs = require('node:fs')
const path = require('node:path')

const crcTable = new Uint32Array(256)
for (let i = 0; i < 256; i++) {
  let c = i
  for (let j = 0; j < 8; j++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1)
  crcTable[i] = c
}
function crc32(buf) {
  let c = 0xFFFFFFFF
  for (const b of buf) c = crcTable[(c ^ b) & 0xFF] ^ (c >>> 8)
  return (c ^ 0xFFFFFFFF) >>> 0
}

function makeChunk(type, data) {
  const typeBuf = Buffer.from(type, 'ascii')
  const len = Buffer.allocUnsafe(4)
  len.writeUInt32BE(data.length)
  const crc = Buffer.allocUnsafe(4)
  crc.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])))
  return Buffer.concat([len, typeBuf, data, crc])
}

function solidColorPNG(size, r, g, b) {
  const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])
  const ihdr = Buffer.allocUnsafe(13)
  ihdr.writeUInt32BE(size, 0)
  ihdr.writeUInt32BE(size, 4)
  ihdr[8] = 8; ihdr[9] = 2; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0
  const rowBytes = 1 + size * 3
  const raw = Buffer.allocUnsafe(size * rowBytes)
  for (let y = 0; y < size; y++) {
    raw[y * rowBytes] = 0
    for (let x = 0; x < size; x++) {
      const o = y * rowBytes + 1 + x * 3
      raw[o] = r; raw[o + 1] = g; raw[o + 2] = b
    }
  }
  return Buffer.concat([
    sig,
    makeChunk('IHDR', ihdr),
    makeChunk('IDAT', zlib.deflateSync(raw)),
    makeChunk('IEND', Buffer.alloc(0)),
  ])
}

const dir = path.join(__dirname, '../public/icons')
fs.mkdirSync(dir, { recursive: true })
fs.writeFileSync(path.join(dir, 'doglog-192.png'), solidColorPNG(192, 91, 141, 217))
fs.writeFileSync(path.join(dir, 'doglog-512.png'), solidColorPNG(512, 91, 141, 217))
console.log('Icons generated: doglog-192.png, doglog-512.png')
