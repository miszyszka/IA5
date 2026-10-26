// Dane z gałęzi `data` na GitHub (Z2: świece i wyniki nie są czytane z Firestore).
// Adres zawiera SHA commita, więc przeglądarka i CDN nie podają starych plików.
import { DATA_OVERRIDE, REPO } from './config.js';
import { asyncBufferFromUrl, cachedAsyncBuffer, parquetReadObjects } from '../vendor/hyparquet/index.js';

const raw = (ref) => `https://raw.githubusercontent.com/${REPO.owner}/${REPO.name}/${ref}/`;
let baseP = null;

export function refreshData() { baseP = null; }

export function dataBase() {
  if (DATA_OVERRIDE) return Promise.resolve(DATA_OVERRIDE.endsWith('/') ? DATA_OVERRIDE : DATA_OVERRIDE + '/');
  if (!baseP) {
    baseP = (async () => {
      try {
        const r = await fetch(`https://api.github.com/repos/${REPO.owner}/${REPO.name}/branches/${REPO.dataBranch}`, { cache: 'no-store' });
        if (r.ok) return raw((await r.json()).commit.sha);
      } catch { /* limit API albo brak sieci — niżej nazwa gałęzi */ }
      return raw(REPO.dataBranch);
    })();
  }
  return baseP;
}

export async function getJSON(path) {
  const r = await fetch((await dataBase()) + path);
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return r.json();
}

export async function getText(path) {
  const r = await fetch((await dataBase()) + path);
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return r.text();
}

const buffers = new Map();
async function parquetFile(url) {
  if (!buffers.has(url)) {
    buffers.set(url, (async () => {
      try {
        // zakresy HTTP: czytamy tylko potrzebne grupy wierszy
        return cachedAsyncBuffer(await asyncBufferFromUrl({ url }));
      } catch {
        const r = await fetch(url);
        if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
        return r.arrayBuffer();
      }
    })());
  }
  return buffers.get(url);
}

const plain = (row) => {
  for (const k in row) if (typeof row[k] === 'bigint') row[k] = Number(row[k]);
  return row;
};

/** Wiersze [rowStart, rowEnd) pliku Parquet z gałęzi data. */
export async function readRows(path, rowStart, rowEnd) {
  const url = (await dataBase()) + path;
  try {
    const rows = await parquetReadObjects({ file: await parquetFile(url), rowStart, rowEnd });
    return rows.map(plain);
  } catch (e) {
    // serwer bez obsługi zakresów — jeszcze raz z całym plikiem
    buffers.delete(url);
    const r = await fetch(url);
    if (!r.ok) throw e;
    const ab = await r.arrayBuffer();
    buffers.set(url, Promise.resolve(ab));
    return (await parquetReadObjects({ file: ab, rowStart, rowEnd })).map(plain);
  }
}
