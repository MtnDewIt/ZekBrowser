// Lightweight TypeScript port of the C# EmblemGenerator for canvas-based emblems
import { ref } from 'vue';

type RGB = { r: number; g: number; b: number };

const ColorValuesHex = [
  '#585758','#a7a6a7','#d7d8d7','#893139','#d26163','#ea7d7d','#d28800','#f6a34b','#fbbe93','#bfa12a',
  '#e2b02a','#fbd375','#4b702b','#839252','#cdea93','#2b7475','#4bafb2','#8ce8e5','#3d518c','#4b84d2',
  '#93a9f3','#4b3d8c','#8c70e1','#bdacfb','#7d003d','#c83d7d','#fb88ad','#4b352b','#a0876b','#d7af9b'
];

const ColorValues: RGB[] = ColorValuesHex.map(h => hexToRgb(h));

function hexToRgb(hex: string): RGB {
  const c = hex.replace('#','');
  return { r: parseInt(c.substring(0,2),16), g: parseInt(c.substring(2,4),16), b: parseInt(c.substring(4,6),16) };
}

enum ColorPolicy { KeepEven = 'KeepEven', KeepBlue = 'KeepBlue' }

interface EmblemData {
  backgroundColor: RGB;
  secondaryColor: RGB;
  primaryColor: RGB;
  foregroundIndex: number;
  backgroundIndex: number;
  toggleSecondary: boolean;
}

const ASSET_BASE = '/assets/emblems';

function getEmblemColor(value: string | undefined): RGB {
  if (!value) return ColorValues[0];
  if (value.length === 6 && /^[0-9a-fA-F]+$/.test(value)) {
    return hexToRgb('#' + value);
  }
  const idx = parseInt(value, 10);
  if (!isNaN(idx) && idx >= 0 && idx < ColorValues.length) return ColorValues[idx];
  return ColorValues[0];
}

function extractEmblemData(emblem: string): EmblemData {
  emblem = emblem.replace(/^\?/, '');
  const parts = emblem.split('&').filter(p => p.length > 0);
  const data: EmblemData = {
    backgroundColor: ColorValues[0],
    secondaryColor: ColorValues[0],
    primaryColor: ColorValues[0],
    foregroundIndex: 0,
    backgroundIndex: 0,
    toggleSecondary: false,
  };
  for (const part of parts) {
    const [k,v] = part.split('=');
    if (!k || v === undefined) continue;
    switch (k) {
      case '1': data.backgroundColor = getEmblemColor(v); break;
      case '2': data.secondaryColor = getEmblemColor(v); break;
      case '3': data.primaryColor = getEmblemColor(v); break;
      case 'fi': data.foregroundIndex = parseInt(v,10) || 0; break;
      case 'bi': data.backgroundIndex = parseInt(v,10) || 0; break;
      case 'fl': data.toggleSecondary = (parseInt(v,10) === 1); break;
    }
  }
  return data;
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => resolve(img);
    img.onerror = (e) => reject(e);
    img.src = src;
  });
}

/* loadFirstAvailable removed — generator uses exact filenames now */

async function colorPixelsOnCanvas(sourceImg: HTMLImageElement, ctx: CanvasRenderingContext2D, userColor: RGB, sampling: ColorPolicy, maxChannelValue: number, alphaBlend = true) {
  const w = sourceImg.width, h = sourceImg.height;
  // draw and modify on a temporary canvas to avoid overwriting the main canvas before compositing
  const tmp = document.createElement('canvas');
  tmp.width = w; tmp.height = h;
  const tctx = tmp.getContext('2d');
  if (!tctx) return;
  tctx.clearRect(0,0,w,h);
  tctx.drawImage(sourceImg, 0, 0, w, h);
  const imgData = tctx.getImageData(0,0,w,h);
  const data = imgData.data; // RGBA
  for (let i = 0; i < data.length; i += 4) {
    const r = data[i], g = data[i+1], b = data[i+2], a = data[i+3];
    const blueDominant = (b - r) > 10;
    const evenColors = (b - r < 10) && (g - b < 10);
    let channelValue = 0;
    switch (sampling) {
      case ColorPolicy.KeepEven:
        channelValue = blueDominant ? 0 : (r / maxChannelValue);
        break;
      case ColorPolicy.KeepBlue:
        channelValue = evenColors ? 0 : (b / maxChannelValue);
        break;
    }
    channelValue = Math.min(1, Math.max(0, channelValue));
    data[i]   = Math.round(userColor.r * channelValue);
    data[i+1] = Math.round(userColor.g * channelValue);
    data[i+2] = Math.round(userColor.b * channelValue);
    data[i+3] = Math.round(alphaBlend ? (255 * channelValue) : 255);
  }
  tctx.putImageData(imgData, 0, 0);

  // composite the modified temp canvas onto the target canvas
  ctx.drawImage(tmp, 0, 0);
}

const cache = new Map<string, string>();

export default async function generateEmblem(emblem: string): Promise<string> {
  if (!emblem) return '';
  if (cache.has(emblem)) return cache.get(emblem) as string;

  const data = extractEmblemData(emblem);

  // create base canvas 128x128
  const baseW = 128, baseH = 128;
  const canvas = document.createElement('canvas');
  canvas.width = baseW; canvas.height = baseH;
  const ctx = canvas.getContext('2d');
  if (!ctx) return '';
  ctx.clearRect(0,0,baseW,baseH);

  // draw background if any
  try {
    if (data.backgroundIndex >= 0) {
      const bgPath = `${ASSET_BASE}/background/emblem_backgrounds_${String(data.backgroundIndex).padStart(2,'0')}.png`;
      
      const bgImg = await loadImage(bgPath);
      await colorPixelsOnCanvas(bgImg, ctx, data.backgroundColor, ColorPolicy.KeepEven, 101);
    }
  } catch (e) {
    // ignore background load errors
  }

  // draw foreground (primary)
  try {
    const fgPath = `${ASSET_BASE}/foreground/emblem_foregrounds_${String(data.foregroundIndex).padStart(3,'0')}.png`;
    
    const fgImg = await loadImage(fgPath);
    await colorPixelsOnCanvas(fgImg, ctx, data.primaryColor, ColorPolicy.KeepEven, 177);
    if (data.toggleSecondary) {
      await colorPixelsOnCanvas(fgImg, ctx, data.secondaryColor, ColorPolicy.KeepBlue, 236);
    }
  } catch (e) {
    // ignore foreground load errors
  }

  // downscale to 28x28
  const outW = 28, outH = 28;
  const outCanvas = document.createElement('canvas');
  outCanvas.width = outW; outCanvas.height = outH;
  const outCtx = outCanvas.getContext('2d');
  if (!outCtx) return '';
  outCtx.imageSmoothingEnabled = true;
  outCtx.imageSmoothingQuality = 'high';
  outCtx.drawImage(canvas, 0, 0, outW, outH);

  const dataUrl = outCanvas.toDataURL('image/png');
  cache.set(emblem, dataUrl);
  return dataUrl;
}
