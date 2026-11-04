const DB_NAME = 'astralis-local-v2';
const STORES = ['cache', 'profiles', 'media', 'galleries', 'settings'];
let opening;

function openDb() {
  if (!('indexedDB' in globalThis)) return Promise.reject(new Error('IndexedDB indisponible'));
  if (opening) return opening;
  opening = new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => {
      for (const name of STORES) if (!request.result.objectStoreNames.contains(name)) request.result.createObjectStore(name);
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error('Ouverture du stockage local impossible'));
  }).catch(error => { opening = null; throw error; });
  return opening;
}

export async function getLocal(store, key) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const request = db.transaction(store, 'readonly').objectStore(store).get(key);
    request.onsuccess = () => resolve(request.result ?? null);
    request.onerror = () => reject(request.error);
  });
}

export async function putLocal(store, key, value) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store, 'readwrite');
    tx.objectStore(store).put(value, key);
    tx.oncomplete = () => resolve(true);
    tx.onerror = tx.onabort = () => reject(tx.error || new Error('Écriture locale impossible'));
  });
}

export async function deleteLocal(store, key) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store, 'readwrite');
    tx.objectStore(store).delete(key);
    tx.oncomplete = () => resolve(true);
    tx.onerror = tx.onabort = () => reject(tx.error || new Error('Suppression locale impossible'));
  });
}

export async function listLocal(store, key) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const request = db.transaction(store, 'readonly').objectStore(store).getAll(key);
    request.onsuccess = () => resolve(request.result || []);
    request.onerror = () => reject(request.error);
  });
}

export async function entriesLocal(store) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const output = [];
    const request = db.transaction(store, 'readonly').objectStore(store).openCursor();
    request.onsuccess = () => { const cursor = request.result; if (!cursor) return resolve(output); output.push([cursor.key, cursor.value]); cursor.continue(); };
    request.onerror = () => reject(request.error);
  });
}

