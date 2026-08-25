/* IndexedDB 封装（离线优先存储） */
const DB_NAME = 'cfa-compliance';
const DB_VERSION = 2;
const STORES = ['submissions', 'pending_queue', 'standards_cache', 'declarations'];

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (e) => {
      const db = e.target.result;
      STORES.forEach(name => {
        if (!db.objectStoreNames.contains(name)) {
          db.createObjectStore(name, { keyPath: 'id', autoIncrement: name === 'submissions' || name === 'pending_queue' });
        }
      });
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function dbPut(store, value) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store, 'readwrite');
    tx.objectStore(store).put(value);
    tx.oncomplete = () => resolve(value);
    tx.onerror = () => reject(tx.error);
  });
}

async function dbGetAll(store) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const req = db.transaction(store, 'readonly').objectStore(store).getAll();
    req.onsuccess = () => resolve(req.result || []);
    req.onerror = () => reject(req.error);
  });
}

async function dbDelete(store, id) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store, 'readwrite');
    tx.objectStore(store).delete(id);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

async function dbClear(store) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store, 'readwrite');
    tx.objectStore(store).clear();
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

const Storage = {
  saveSubmission: (sub) => dbPut('submissions', sub),
  getSubmissions: () => dbGetAll('submissions'),
  deleteSubmission: (id) => dbDelete('submissions', id),
  clearSubmissions: () => dbClear('submissions'),

  savePending: (item) => dbPut('pending_queue', item),
  getPending: () => dbGetAll('pending_queue'),
  deletePending: (id) => dbDelete('pending_queue', id),

  saveStandardsCache: (data) => dbPut('standards_cache', { id: 'standards', data }),
  getStandardsCache: async () => {
    const all = await dbGetAll('standards_cache');
    return all.length ? all[0].data : null;
  },

  saveDeclaration: (d) => dbPut('declarations', d),
  getDeclarations: () => dbGetAll('declarations'),
  updateDeclaration: (d) => dbPut('declarations', d),
  clearDeclarations: () => dbClear('declarations'),
};
