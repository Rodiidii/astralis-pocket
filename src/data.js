import { getLocal, putLocal } from './persistence.js?v=20261028-team-buffs-78';
import { ic } from './icons.js?v=20261028-team-buffs-78';

export const GAMES = {
  hsr: { label: 'Honkai: Star Rail', short: 'Star Rail', icon: ic('hsr'), accent: '#c1a7ff', source: 'StarRailStaticAPI' },
  gi: { label: 'Genshin Impact', short: 'Genshin', icon: ic('gi'), accent: '#e8c788', source: 'Nanoka + Genshin-DB + Enka.Network' },
  ww: { label: 'Wuthering Waves', short: 'Wuthering', icon: ic('ww'), accent: '#7ed7cf', source: 'Encore API · catalogue Beta' },
};

const ELEMENTS_FR = { Fire: 'Feu', Ice: 'Glace', Thunder: 'Foudre', Wind: 'Vent', Quantum: 'Quantique', Imaginary: 'Imaginaire', Physical: 'Physique', Geo: 'Géo', Dendro: 'Dendro', Hydro: 'Hydro', Pyro: 'Pyro', Electro: 'Électro', Cryo: 'Cryo', Anemo: 'Anémo', Spectro: 'Spectro', Havoc: 'Havoc', Glacio: 'Glacio', Fusion: 'Fusion' };
const PATHS_FR = { Knight: 'Préservation', Rogue: 'Chasse', Mage: 'Érudition', Warlock: 'Nihilité', Shaman: 'Harmonie', Warrior: 'Destruction', Priest: 'Abondance', Memory: 'Souvenir' };
const WEAPONS_FR = { Sword: 'Épée', Claymore: 'Épée à deux mains', Bow: 'Arc', Catalyst: 'Catalyseur', Polearm: 'Lance', Broadblade: 'Épée large', Gauntlets: 'Gantelets', Pistols: 'Pistolets', Rectifier: 'Rectificateur', 'Sword': 'Épée' };
export function frenchTerm(value) { const raw = String(value ?? ''); return ELEMENTS_FR[raw] || PATHS_FR[raw] || WEAPONS_FR[raw] || raw; }

const catalogCache = new Map();
const detailCache = new Map();
const levelStatsCache = new Map();
const skillCache = new Map();
let hsrRankCache;
let nanokaManifestPromise;
let nanokaGiCharacterIndexPromise;
const refreshing = new Map();
function cacheTtl(){try{const days=Number(JSON.parse(localStorage.getItem('astralis:preferences')||'{}').dataRefreshDays)||1;return Math.max(1,Math.min(30,days))*24*60*60*1000;}catch{return 24*60*60*1000;}}
const MAX_JSON_BYTES = 16 * 1024 * 1024;
async function nanokaLatestVersion(game='hsr'){if(!nanokaManifestPromise)nanokaManifestPromise=json('https://static.nanoka.cc/manifest.json',AbortSignal.timeout(12000)).catch(()=>null);const manifest=await nanokaManifestPromise;return String(manifest?.[game]?.latest||'4.6.54');}

export const slugify = value => String(value ?? '')
  .normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
  .replace(/[’']/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

function displayName(game, item, fallback) {
  const raw = item?.name ?? item?.Name ?? item?.item_name ?? item?.en ?? fallback ?? 'Sans nom';
  if (game === 'gi' && String(raw).toLowerCase() === 'traveler') {
    const element = item?.vision || item?.element || 'Anemo';
    return `Voyageur · ${element}`;
  }
  if (raw !== '{NICKNAME}') return String(raw);
  const names = {
    playerboy: 'Pionnier (Homme)', playergirl: 'Pionnière (Femme)',
    playerboy2: 'Pionnier · Feu (Homme)', playergirl2: 'Pionnière · Feu (Femme)',
    playerboy3: 'Pionnier · Imaginaire (Homme)', playergirl3: 'Pionnière · Imaginaire (Femme)',
  };
  return names[item?.tag] || 'Pionnier';
}

function entityId(game, item, fallback) {
  if (game === 'ww') return String(item?.id ?? fallback);
  if (game === 'gi') {
    const name = String(item?.name || fallback || '');
    return name.toLowerCase() === 'traveler' ? `traveler-${slugify(item?.vision || item?.element || 'anemo')}` : slugify(name);
  }
  return String(item?.id ?? item?.Id ?? item?.ID ?? fallback);
}

function normalize(game, category, item, fallback) {
  if (!item || typeof item !== 'object') item = { name: String(item ?? fallback) };
  const id = entityId(game, item, fallback);
  return { ...item, _id: id, _name: displayName(game, item, id), _game: game, _category: category };
}

async function mergeEnkaCharacterIndex(data) {
  const rows = Array.isArray(data)
    ? data.map(row => ({ ...row }))
    : Object.entries(data || {}).map(([id, row]) => ({ id: row?.id ?? id, ...row }));
  try {
    const [avatars, localizations] = await Promise.all([
      json('https://raw.githubusercontent.com/EnkaNetwork/API-docs/master/store/gi/avatars.json', AbortSignal.timeout(20000)),
      json('https://raw.githubusercontent.com/EnkaNetwork/API-docs/master/store/gi/locs.json', AbortSignal.timeout(20000)),
    ]);
    const names = localizations?.fr || localizations?.en || {};
    const byId = new Map(rows.map(row => [String(row.id ?? ''), row]));
    const byName = new Map(rows.map(row => [slugify(row.name || row.Name || ''), row]));
    const elementMap = { Fire: 'Pyro', Water: 'Hydro', Ice: 'Cryo', Electric: 'Electro', Wind: 'Anemo', Rock: 'Geo', Grass: 'Dendro' };
    const elementFrench = { Pyro: 'Pyro', Hydro: 'Hydro', Cryo: 'Cryo', Electro: 'Électro', Anemo: 'Anémo', Geo: 'Géo', Dendro: 'Dendro' };
    const weaponMap = { WEAPON_SWORD_ONE_HAND: 'Sword', WEAPON_CLAYMORE: 'Claymore', WEAPON_BOW: 'Bow', WEAPON_CATALYST: 'Catalyst', WEAPON_POLE: 'Polearm' };
    const weaponFrench = { Sword: 'Épée', Claymore: 'Épée à deux mains', Bow: 'Arc', Catalyst: 'Catalyseur', Polearm: 'Lance' };
    for (const [id, avatar] of Object.entries(avatars || {})) {
      const name = names[String(avatar?.NameTextMapHash)] || localizations?.en?.[String(avatar?.NameTextMapHash)];
      if (!name || !avatar) continue;
      const sideFile = String(avatar.SideIconName || '').split('/').pop().replace(/\.png$/i, '');
      const iconFile = sideFile.replace(/^UI_AvatarIcon_Side_/, 'UI_AvatarIcon_');
      const element = elementMap[avatar.Element] || '';
      const weaponType = weaponMap[avatar.WeaponType] || '';
      const existing = byId.get(String(id)) || byName.get(slugify(name));
      if (existing) {
        existing.images = {
          ...(existing.images || {}),
          filename_icon: existing.images?.filename_icon || iconFile,
          filename_sideIcon: existing.images?.filename_sideIcon || sideFile,
          filename_gachaSplash: existing.images?.filename_gachaSplash || iconFile.replace('UI_AvatarIcon_', 'UI_Gacha_AvatarImg_'),
        };
        existing.element ||= element;
        existing.elementText ||= elementFrench[element] || element;
        existing.weaponType ||= weaponType;
        existing.weaponText ||= weaponFrench[weaponType] || weaponType;
        existing.sourceId ||= String(id);
        continue;
      }
      const quality = String(avatar.QualityType || '');
      const item = {
        id: String(id), name, rarity: quality.includes('ORANGE') ? 5 : quality.includes('PURPLE') ? 4 : 0,
        element, elementText: elementFrench[element] || element,
        weaponType, weaponText: weaponFrench[weaponType] || weaponType,
        images: { filename_icon: iconFile, filename_sideIcon: sideFile, filename_gachaSplash: iconFile.replace('UI_AvatarIcon_', 'UI_Gacha_AvatarImg_') },
        sourceId: String(id), source: 'Enka.Network', catalogSupplement: true,
      };
      rows.push(item);
      byId.set(String(id), item);
      byName.set(slugify(name), item);
    }
  } catch (error) {
    console.info('Index Enka indisponible; catalogue Genshin principal conservé.', error?.message || error);
  }
  return rows;
}

// Genshin-DB lags behind beta-only entries. Nanoka's versioned public index
// contains the authoritative game IDs for these entries; merge only missing
// records so the richer localized Genshin-DB data remains preferred.
async function mergeNanokaGiCharacterIndex(data) {
  const rows = Array.isArray(data) ? data.map(row => ({ ...row }))
    : Object.entries(data || {}).map(([id, row]) => ({ id: row?.id ?? id, ...row }));
  try {
    if (!nanokaGiCharacterIndexPromise) nanokaGiCharacterIndexPromise = (async () => {
      const manifest = await json('https://static.nanoka.cc/manifest.json', AbortSignal.timeout(12000));
      const version = String(manifest?.gi?.latest || manifest?.gi?.live || '');
      if (!version) throw new Error('Version GI Nanoka indisponible.');
      const index = await json(`https://static.nanoka.cc/gi/${encodeURIComponent(version)}/character.json`, AbortSignal.timeout(20000));
      return Object.entries(index || {}).map(([id, value]) => ({ id: String(id), ...value }));
    })().catch(error => { nanokaGiCharacterIndexPromise = null; throw error; });
    const latest = await nanokaGiCharacterIndexPromise;
    const byId = new Map(rows.map(row => [String(row.id ?? ''), row]));
    const byName = new Map(rows.map(row => [slugify(row.name || row.Name || ''), row]));
    const elementMap = { Fire:'Pyro', Water:'Hydro', Ice:'Cryo', Electric:'Electro', Wind:'Anemo', Rock:'Geo', Grass:'Dendro' };
    const weaponMap = { WEAPON_SWORD_ONE_HAND:'Sword', WEAPON_CLAYMORE:'Claymore', WEAPON_BOW:'Bow', WEAPON_CATALYST:'Catalyst', WEAPON_POLE:'Polearm' };
    const elementFrench = { Pyro:'Pyro', Hydro:'Hydro', Cryo:'Cryo', Electro:'Électro', Anemo:'Anémo', Geo:'Géo', Dendro:'Dendro' };
    const weaponFrench = { Sword:'Épée', Claymore:'Épée à deux mains', Bow:'Arc', Catalyst:'Catalyseur', Polearm:'Lance' };
    for (const record of latest) {
      const name = String(record.en || record.name || '').trim();
      if (!name) continue;
      const existing = byId.get(String(record.id)) || byName.get(slugify(name));
      const element = elementMap[record.element] || record.element || '';
      const weaponType = weaponMap[record.weapon] || '';
      const images = { filename_icon:record.icon, filename_sideIcon:record.icon?.replace('UI_AvatarIcon_', 'UI_AvatarIcon_Side_'), filename_gachaSplash:record.icon?.replace('UI_AvatarIcon_', 'UI_Gacha_AvatarImg_') };
      if (existing) {
        existing.images = { ...images, ...(existing.images || {}) };
        existing.element ||= element;
        existing.elementText ||= elementFrench[element] || element;
        existing.weaponType ||= weaponType;
        existing.weaponText ||= weaponFrench[weaponType] || weaponType;
        continue;
      }
      const item = {
        id:String(record.id), sourceId:String(record.id), name, rarity:String(record.rank || '').includes('ORANGE') ? 5 : 4,
        element, elementText:elementFrench[element] || element, weaponType, weaponText:weaponFrench[weaponType] || weaponType,
        description:record.desc || '', images, source:'Nanoka', catalogSupplement:true,
        preRelease:!record.release || String(record.release).startsWith('1970-'),
      };
      rows.push(item); byId.set(String(record.id), item); byName.set(slugify(name), item);
    }
  } catch (error) {
    console.info('Index Genshin Nanoka indisponible; catalogues existants conservés.', error?.message || error);
  }
  return rows;
}

async function supplementCatalog(game, category, items) {
  if (game !== 'gi' || category !== 'character') return items;
  const merged = await mergeNanokaGiCharacterIndex(items);
  const result = ensureAnnouncedCharacters(game, category, merged.map(item => item._id ? item : normalize(game, category, item, item.id)));
  if (result.length !== items.length) {
    const savedAt = Date.now();
    catalogCache.set(`studio64:${game}:${category}`, { items:result, savedAt });
    putLocal('cache', `catalog:studio64:${game}:${category}`, { items:result, savedAt, source:'Nanoka + catalogue principal' }).catch(() => {});
  }
  return result;
}

function ensureAnnouncedCharacters(game,category,items){if(game!=='gi')return items;const officialArt='/assets/images/mitya-splash.png';if(category==='character'&&!items.some(x=>String(x._name||x.name||'').toLowerCase()==='mitya'))items.push(normalize('gi','character',{id:'mitya-preview',name:'Mitya',rarity:5,element:'Electro',elementText:'Électro',weaponType:'Catalyst',weaponText:'Catalyseur',version:'7.2',preRelease:true,images:{cover1:officialArt,portrait:officialArt,image:officialArt,filename_icon:'UI_AvatarIcon_Mitya',filename_gachaSplash:'UI_Gacha_AvatarImg_Mitya',mihoyo_icon:'https://upload-os-bbs.mihoyo.com/game_record/genshin/character_icon/UI_AvatarIcon_Mitya.png',mihoyo_sideIcon:'https://upload-os-bbs.mihoyo.com/game_record/genshin/character_side_icon/UI_AvatarIcon_Side_Mitya.png'},title:'Rules Set at Naught',constellation:'Nodus Gordianus',substatType:'FIGHT_PROP_CRITICAL_HURT',substatText:'DGT CRIT',description:'Personnage annoncé en version 7.2. Fiche de kit de bêta v7.1.53, avec valeurs susceptibles de changer avant la sortie.'},'mitya-preview'));if(category==='character'){const m=items.find(x=>String(x._name||x.name||'').toLowerCase()==='mitya');if(m&&(m.preRelease||m._id==='mitya-preview')){m.preRelease=true;m.version='7.2';m.element='Electro';m.elementText='Électro';m.weaponType='Catalyst';m.weaponText='Catalyseur';m.images={...(m.images||{}),cover1:officialArt,portrait:officialArt,image:officialArt,filename_icon:'UI_AvatarIcon_Mitya',filename_gachaSplash:'UI_Gacha_AvatarImg_Mitya'};m.title='Rules Set at Naught';m.constellation='Nodus Gordianus';m.substatType='FIGHT_PROP_CRITICAL_HURT';m.substatText='DGT CRIT';m.description='Personnage annoncé en version 7.2. Fiche de kit de bêta v7.1.53, avec valeurs susceptibles de changer avant la sortie.';}}if(category==='weapon'&&!items.some(x=>String(x._name||x.name||'').toLowerCase()==='starsealed edict'))items.push(normalize('gi','weapon',{id:'starsealed-edict-preview',name:'Starsealed Edict',rarity:5,weaponType:'Catalyst',weaponText:'Catalyseur',version:'7.2',preRelease:true,images:{icon:'/assets/images/weapon-preview-catalyst.svg',mihoyo_icon:'/assets/images/weapon-preview-catalyst.svg'},description:'Nouveau catalyseur 5★ présenté dans les informations de la version 7.2. Le visuel actuel est un repère provisoire; statistiques, passif, icône officielle et détails de bannière : en cours d’informations.'},'starsealed-edict-preview'));return items;}

async function json(url, signal) {
  const response = await fetch(url, { signal, cache: 'no-cache' });
  if (!response.ok) throw new Error(`La source répond avec HTTP ${response.status}`);
  const headerSize = Number(response.headers.get('content-length') || 0);
  if (headerSize > MAX_JSON_BYTES) throw new Error('Mise à jour ignorée : la base dépasse la limite locale de 16 Mo.');
  let payload;
  if (response.body?.getReader) {
    const reader = response.body.getReader(), chunks = [];
    let total = 0;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      total += value.byteLength;
      if (total > MAX_JSON_BYTES) { await reader.cancel(); throw new Error('Mise à jour ignorée : la base dépasse la limite locale de 16 Mo.'); }
      chunks.push(value);
    }
    const joined = new Uint8Array(total); let offset = 0;
    for (const chunk of chunks) { joined.set(chunk, offset); offset += chunk.byteLength; }
    payload = new TextDecoder().decode(joined);
  } else payload = await response.text();
  const result = JSON.parse(payload);
  if (result?.error) throw new Error(result.detail || result.error);
  return result;
}

export async function catalog(game, category, { force = false } = {}) {
  const key = `studio64:${game}:${category}`;
  const cached = catalogCache.get(key);
  const ttl=cacheTtl();
  if (!force && cached && Date.now() - cached.savedAt < ttl) return supplementCatalog(game,category,cached.items);
  if (!force && cached?.pending) return cached.pending;
  if (!force) {
    try {
      const saved = await getLocal('cache', `catalog:${key}`);
      if (Array.isArray(saved?.items) && saved.items.length) {
        const savedAt=Number(saved.savedAt)||0;
        catalogCache.set(key, { items: saved.items, savedAt });
        let autoRefresh=true;try{autoRefresh=JSON.parse(localStorage.getItem('astralis:preferences')||'{}').autoRefresh!==false;}catch{}
        if (autoRefresh&&Date.now()-savedAt>=ttl&&!refreshing.has(key)) {
          const refresh = fetchCatalog(game, category, false).then(items => {
            const previous = catalogCache.get(key)?.items;
            if (game === 'gi' && category === 'character' && previous?.length > 40 && items.length < previous.length * 0.75) throw new Error('Mise à jour partielle ignorée : conservation du catalogue Genshin déjà valide.');
            catalogCache.set(key, { items, savedAt: Date.now() });
            putLocal('cache', `catalog:${key}`, { items, savedAt: Date.now(), source: GAMES[game].source }).catch(() => {});
            window.dispatchEvent(new CustomEvent('astralis:catalog-updated', { detail: key }));
          }).catch(() => {}).finally(() => refreshing.delete(key));
          refreshing.set(key, refresh);
        }
        return supplementCatalog(game,category,saved.items);
      }
    } catch { /* Cache absente : lecture réseau ci-dessous. */ }
  }
  const pending = fetchCatalog(game, category, force).then(items => {
    if (game === 'gi' && category === 'character' && cached?.items?.length > 40 && items.length < cached.items.length * 0.75) throw new Error('Mise à jour partielle ignorée : conservation du catalogue Genshin déjà valide.');
    const savedAt = Date.now();
    catalogCache.set(key, { items, savedAt });
    putLocal('cache', `catalog:${key}`, { items, savedAt, source: GAMES[game].source }).catch(() => {});
    return items;
  }).catch(error => { if (cached?.items) { catalogCache.set(key, cached); return cached.items; } catalogCache.delete(key); throw error; });
  catalogCache.set(key, { pending });
  return pending;
}

async function fetchCatalog(game, category, force) {
  let data;
  if (game === 'gi') {
    const file = category === 'character' ? 'characters' : category === 'weapon' ? 'weapons' : category === 'artifact' ? 'artifacts' : category==='material'?'materials':'';
    if (file) {
      const endpoint = file;
      const url = `https://genshin-db-api.vercel.app/api/v5/${endpoint}?query=names&matchCategories=true&verboseCategories=true&queryLanguages=french&resultLanguage=French`;
      data = await json(url, AbortSignal.timeout(30000)).then(payload => { const rows = Array.isArray(payload) ? payload : Object.values(payload || {}); if (!rows.length || rows.every(row => !row || typeof row !== 'object' || !(row.name || row.id))) throw new Error('La source a renvoyé un catalogue vide ou invalide.'); return payload; }).catch(() => json(`assets/data/gi-${file}.json`, AbortSignal.timeout(30000)));
      // The live database has French text; the bundled Hakushin-era export is
      // retained only as a complete source for stable icon filenames and costs.
      try {
        const local = await json(`assets/data/gi-${file}.json`, AbortSignal.timeout(20000));
        const localRows = Array.isArray(local) ? local : Object.values(local || {});
        const byId = new Map(localRows.map(row => [String(row.id ?? row.name ?? '').toLowerCase(), row]));
        const byName = new Map(localRows.map(row => [String(row.name || '').toLowerCase(), row]));
        const merge = (remote, original) => {
          const key = String(remote.id ?? remote.name ?? '').toLowerCase();
          const saved = byId.get(key) || byName.get(String(remote.name || '').toLowerCase()) || {};
          return { ...saved, ...remote, id: remote.id ?? saved.id, costs: remote.costs || saved.costs,
            images: { ...(saved.images || {}), ...(remote.images || {}),
              filename_icon: remote.images?.filename_icon || saved.images?.filename_icon,
              filename_flower: remote.images?.filename_flower || saved.images?.filename_flower } };
        };
        data = Array.isArray(data) ? data.map(row => merge(row)) : Object.fromEntries(Object.entries(data || {}).map(([key,row]) => [key, merge(row)]));
      } catch { /* Les assets locaux sont un enrichissement, la source principale reste utilisable. */ }
    } else data = [];
  } else if (game === 'hsr') {
    const file = category === 'character' ? 'character' : category === 'weapon' ? 'lightcone' : category === 'artifact' ? 'relicset' : category==='material'?'item':'';
    if (file) {
      const supplemental = await json(`assets/data/hsr-nanoka-${file}.json`, AbortSignal.timeout(30000));
      const base = ['character','weapon','artifact'].includes(category) ? await json(`/data/hsr/${category}${force ? '?refresh=1' : ''}`, AbortSignal.timeout(30000)).catch(() => ({})) : {};
      const merged = { ...supplemental, ...base };
      data = Object.fromEntries(Object.entries(merged).map(([id, value]) => {
        const nanoka = supplemental[id] || {};
        return [id, { ...value, id, name: value.name || nanoka.item_name || nanoka.fr || nanoka.en, nanokaIcon: nanoka.icon, item_figure_icon_path:nanoka.item_figure_icon_path, en: nanoka.en, path: value.path || nanoka.baseType, element: value.element || nanoka.damageType, baseType: nanoka.baseType, damageType: nanoka.damageType, rarity: nanoka.rank?.match(/Type(\d+)/)?.[1] || ({SuperRare:5,VeryRare:4,Rare:3,Normal:2,NotNormal:1})[nanoka.rarity] || value.rarity }];
      }));
    } else data = await json(`/data/${game}/${category}${force ? '?refresh=1' : ''}`, AbortSignal.timeout(30000));
  } else if (game === 'ww' && category==='material') data=await json('assets/data/ww-items.json',AbortSignal.timeout(30000));
  else data = await json(`/data/${game}/${category}${force || game === 'ww' ? '?refresh=1' : ''}`, AbortSignal.timeout(30000));
    if (game === 'gi' && category === 'character') {
      data = await mergeEnkaCharacterIndex(data);
      data = await mergeNanokaGiCharacterIndex(data);
    }
    const entries = Array.isArray(data) ? data.map((value, index) => [value?.id ?? index, value]) : Object.entries(data || {});
    const items = ensureAnnouncedCharacters(game,category,entries.map(([id, value]) => normalize(game, category, value, id))
      .filter(item => item._name && item._name !== 'Sans nom' && !/^\s*\.{2,}\s*$/.test(item._name)));
    if(game==='ww'&&category==='character'&&!items.some(item=>item._name.toLowerCase()==='lily'))items.push(normalize(game,category,{id:'lily-preview',name:'Lily',rarity:5,preRelease:true,description:'Résonatrice annoncée pour la version 3.8. Les coefficients, compétences détaillées et builds seront complétés quand une base publique les publiera.'},'lily-preview'));
    if(game==='gi'&&category==='character'&&!items.some(item=>item._name.toLowerCase()==='mitya'))items.push(normalize(game,category,{id:'mitya-preview',name:'Mitya',rarity:5,element:'Electro',elementText:'Électro',weaponType:'Catalyst',weaponText:'Catalyseur',version:'7.2',preRelease:true,images:{filename_icon:'UI_AvatarIcon_Mitya',filename_gachaSplash:'UI_Gacha_AvatarImg_Mitya',cover1:'https://fastcdn.hoyoverse.com/content-v2/hk4e/165002/ecd34b52bd4a26b227fdbb58215fe46c_8363697304532950719.jpg'},description:'Personnage annoncé pour la version 7.2. Fiche de kit de bêta v7.1.53, avec valeurs susceptibles de changer avant la sortie.'},'mitya-preview'));
    if(game==='hsr'&&category==='character'){
      try{const profile=await getLocal('profiles','hsr');for(const avatar of profile?.data?.avatar_list||[]){const id=String(avatar.id);if(items.some(item=>item._id===id))continue;items.push(normalize(game,category,{id,name:avatar.name,element:avatar.element,rarity:avatar.rarity,icon:avatar.icon,portrait:avatar.image,preview:avatar.image,profileOnly:true},id));}}catch{/* No profile imported yet. */}
    }
    await putLocal('cache', `catalog:${game}:${category}`, { items, savedAt: Date.now(), source: GAMES[game].source });
    return items;
}

export async function levelStatsFor(folder,item) {
  const key=`${folder}:${item?.name||item?._name||item?._id||''}`;
  if(levelStatsCache.has(key))return levelStatsCache.get(key);
  const pending=(async()=>{
    try{const cached=await getLocal('cache',`gi-level-stats:${key}`);if(cached?.items&&Date.now()-(Number(cached.savedAt)||0)<30*86400000)return cached.items;}catch{}
    const query=encodeURIComponent(item?.name||item?._name||item?._id||'');
    const result=await json(`https://genshin-db-api.vercel.app/api/v5/stats?folder=${encodeURIComponent(folder)}&query=${query}&queryLanguages=English&resultLanguage=English`,AbortSignal.timeout(25000));
    const rows=result?.stats||result?.result?.stats||result;
    if(!rows||typeof rows!=='object')throw new Error('Courbe de statistiques indisponible.');
    await putLocal('cache',`gi-level-stats:${key}`,{items:rows,savedAt:Date.now()}).catch(()=>{});return rows;
  })();
  levelStatsCache.set(key,pending);
  try{return await pending;}catch(error){levelStatsCache.delete(key);throw error;}
}

export async function gameSkills(game) {
  if (skillCache.has(game)) return skillCache.get(game);
  let value;
  if (game === 'hsr') value = await json('/data/hsr/skills', AbortSignal.timeout(30000));
  else value = {};
  skillCache.set(game, value);
  return value;
}

export async function hsrCharacterRanks(){
  if(hsrRankCache)return hsrRankCache;
  hsrRankCache=(async()=>{
    const saved=await getLocal('cache','hsr:character-ranks').catch(()=>null);
    if(saved?.items)return saved.items;
    const data=await json('assets/data/hsr-character-ranks-fr.json',AbortSignal.timeout(30000));
    await putLocal('cache','hsr:character-ranks',{items:data,savedAt:Date.now(),source:'StarRailStaticAPI FR'});
    return data;
  })().catch(error=>{hsrRankCache=null;throw error;});
  return hsrRankCache;
}

export async function characterDetails(game, character) {
  const key = `${game}:${character._id}`;
  // Never fuzzy-query unreleased/announced characters: Genshin-DB may return a
  // different character (e.g. Ayato for Mitya) and poison the build with false data.
  if (game === 'gi' && character.preRelease) {
    if (String(character._name||'').toLowerCase()==='mitya') {
      const kit=[
        {name:'Chain Reaction',unlock:'Attaque normale',description:'Enchaîne jusqu’à 3 attaques Électro. L’attaque chargée inflige des DGT Électro de zone. Lorsque son Détecteur : Surcharge est actif et qu’il possède au moins 1 Balise de gradient, l’attaque chargée devient Détonation de gradient : elle ne consomme pas d’endurance et consomme les balises tant que l’attaque est maintenue; chaque balise inflige des DGT de réaction Conduction stellaire.',values:['1er coup · 105,8 %','2e coup · 86,9 %','3e coup · 124,2 %','Attaque chargée · 246,4 %','Détonation de gradient · 302,4 %','DGT Conduction stellaire / balise · 403,2 % de la maîtrise élémentaire']},
        {name:'Principle: Variable Detection',unlock:'Compétence élémentaire',description:'Inflige des DGT Électro de zone et crée un Détecteur en état Stable (appui) ou Surcharge (maintien). Un nouvel appui dans les 6 s peut changer son état, au plus une fois toutes les 1,5 s. En état Stable, le Détecteur suit les ennemis, attaque périodiquement et consomme les balises excédentaires; à sa disparition, il consomme les balises restantes. En état Surcharge, Mitya peut maintenir son attaque chargée pour consommer les balises.',values:['DGT appui · 163,3 %','DGT maintien · 233,3 %','Détecteur stable · 129,6 %','Consommation de balise · 144 % de la maîtrise élémentaire','Détonation · 165,6 % de la maîtrise élémentaire par balise','Durée · 25 s · TdR · 18 s']},
        {name:'Analysis: Gradient Theory',unlock:'Déchaînement élémentaire',description:'Laisse les éléments jaillir comme l’inspiration : inflige des DGT Électro de zone et crée immédiatement 3 Balises de gradient.',values:['DGT · 600,5 % ATQ + 1 201 % maîtrise élémentaire','Balises créées · 3','TdR · 15 s · Énergie · 60']}
      ];
      const passives=[
        {name:'Baseline Stress Test',description:'Améliore le Détecteur : en état Stable, chaque Balise de gradient possédée confère 30 pts de maîtrise élémentaire aux personnages proches. En état Surcharge, les réactions Conduction stellaire de l’équipe créent une balise toutes les 1,5 s pendant 3 s.'},
        {name:'Explosive Reagent: Safe Limits Exceeded',description:'Les Balises de gradient durent 10 s. Après la création d’une balise, le taux CRIT de Mitya augmente de 5 % pendant 15 s. Cumulable 4 fois.'},
        {name:'Stellar Jubilee: Top-Secret Protocol',description:'Le Superconducteur de l’équipe devient Conduction stellaire : il crée une Balise de gradient toutes les 1,5 s pendant 3 s. Chaque point de maîtrise élémentaire de Mitya augmente les DGT de base de Conduction stellaire de 0,028 %, jusqu’à 14 %. Dans un Champ polaire, Mitya entre en état Rayonnement : Conduction stellaire.'},
        {name:'Energy Catalysis',description:'Le Détecteur en état Stable détruit rapidement certains rochers de Snezhnaya. La création d’une Source de chaleur de base du Construct de glace primordial ne consomme pas d’énergie Kresnik lorsque Mitya fait partie de l’équipe.'}
      ];
      const constellationNames=['The Observer Seeking What Is Missing','The Matter That Slumbers Beyond Inertness','The Knotted String of Invariant Topology','The Isotopes Born of Decay','The Periodic Law That Orders All','Elemental Transition at the Gate of Reason'];
      const constellationDescriptions=['La limite de Balises de gradient passe à 5 et la compétence crée 1 Balise supplémentaire. Tant que le Détecteur est présent, le personnage déployé gagne 50 % de DGT CRIT. Mitya récupère 10 pts d’énergie lorsqu’une balise est créée, une fois toutes les 8 s.','Dans le Champ polaire, la RÉS Cryo et Électro des ennemis diminue de 25 %. En état Stable, les personnages proches gagnent 100 pts de maîtrise élémentaire; en état Surcharge, le personnage déployé gagne 200 pts.','Le niveau de la compétence élémentaire augmente de 3.','Pour chaque tranche de 5 Balises consommées, le Détecteur inflige une instance de DGT de Conduction stellaire équivalente à 400 % de la maîtrise élémentaire de Mitya.','Le niveau de l’attaque normale augmente de 3.','Lorsqu’un Détecteur Stable est actif, ses DGT augmentent de 15 %. En état Surcharge, chaque balise consommée a 30 % de chances d’en créer une nouvelle. Les DGT de réaction Conduction stellaire de l’équipe augmentent de 20 %.'];
      const details={...character,levelStats:{'90+':{level:90,ascension:6,hp:11634,attack:263,defense:792,elementalMastery:100,specialized:.384}},baseStats:{hp:11634,attack:263,defense:792,elementalMastery:100,critDamage:38.4},ascensionStat:{name:'DGT CRIT',value:38.4,elementalMastery:100},skillTalents:kit,talentValues:null,passives,constellations:constellationNames.map((name,i)=>({name:`C${i+1} · ${name}`,description:constellationDescriptions[i],icon:'https://genshin.jmp.blue/elements/electro.png'})),announcedKitUrl:'https://genshin.hoyoverse.com/en/news/detail/167047',betaKitUrl:'https://gi.gachabase.net/characters/10000136/mitya/beta',kitVersion:'Bêta 7.1.53 · valeurs non définitives'};
      detailCache.set(key,details);return details;
    }
    const details = { ...character, levelStats: null, skillTalents: [], talentValues: null, passives: [], constellations: [], announcedKitUrl: 'https://genshin.hoyoverse.com/fr/news/detail/167047' };
    detailCache.set(key, details);
    return details;
  }
  if (detailCache.has(key)) return detailCache.get(key);
  try{const saved=await getLocal('cache',`detail:studio69:${key}`);if(saved?.items&&Date.now()-(Number(saved.savedAt)||0)<cacheTtl()){detailCache.set(key,saved.items);return saved.items;}}catch{}
  let details = character;
  if (game === 'gi') {
    const options = `query=${encodeURIComponent(character.name || character._name)}&matchCategories=true&verboseCategories=true&queryLanguages=french&resultLanguage=French`;
    const statsQuery=encodeURIComponent(character.name||character._name);
    const [talentValues,constellations,levelStats] = await Promise.all([
      json(`https://genshin-db-api.vercel.app/api/v5/talents?${options}`, AbortSignal.timeout(25000)),
      json(`https://genshin-db-api.vercel.app/api/v5/constellations?${options}`, AbortSignal.timeout(25000)).catch(()=>null),
      levelStatsFor('characters',character).catch(()=>null),
    ]);
    const skillTalents=['combat1','combat2','combat3'].map(key=>talentValues?.[key]).filter(Boolean);
    details = { ...character, description:character.description, levelStats, talentValues, skillTalents:skillTalents.map((skill,index)=>{const legacy=`https://genshin.jmp.blue/characters/${encodeURIComponent(character._id)}/talent-${['na','skill','burst'][index]}`;const filename=talentValues?.images?.[`filename_combat${index+1}`];return {...skill,icon:filename?`https://enka.network/ui/${encodeURIComponent(filename)}.png`:legacy,iconFallbacks:[legacy]}}), talentCosts:talentValues?.costs||{}, passives:['passive1','passive2','passive3'].map(key=>talentValues?.[key]).filter(Boolean), constellations:constellations?['c1','c2','c3','c4','c5','c6'].map((key,index)=>constellations[key]&&({name:`Constellation ${index+1} · ${constellations[key].name}`,description:constellations[key].description,icon:`https://genshin.jmp.blue/characters/${encodeURIComponent(character._id)}/constellation-${index+1}`,level:10})).filter(Boolean):[] };
  }
  if (game === 'ww'&&!character.preRelease) details = { ...character, ...await json(`/detail/ww/character/${encodeURIComponent(character.apiId||character._id)}`, AbortSignal.timeout(25000)) };
  if (game === 'hsr') {
    const [skills,ranks] = await Promise.all([gameSkills(game),hsrCharacterRanks()]);
    const eidolons=Object.values(ranks||{}).filter(rank=>String(rank.id||'').startsWith(String(character._id))&&Number(rank.rank)>0).sort((a,b)=>Number(a.rank)-Number(b.rank));
    let kit=(character.skills||[]).map(id=>skills[id]).filter(Boolean);
    let nanokaRanks=[];
    {
      try{
        const version=await nanokaLatestVersion('hsr'),key=`hsr:nanoka-character:${character._id}`;
        const cached=await getLocal('cache',key).catch(()=>null);let remote=cached?.items;
        if(!remote||cached.version!==version||Date.now()-(Number(cached.savedAt)||0)>cacheTtl()){
          try{remote=await json(`https://static.nanoka.cc/hsr/${encodeURIComponent(version)}/en/character/${encodeURIComponent(character._id)}.json`,AbortSignal.timeout(20000));await putLocal('cache',key,{items:remote,version,savedAt:Date.now(),source:`Nanoka HSR ${version}`});}
          catch(error){if(!remote)throw error;}
        }
        const renderDesc=(text,params=[])=>String(text||'').replace(/<[^>]*>/g,'').replace(/#(\d+)\[i\](%?)/g,(_,n,pct)=>{const value=Number(params[Number(n)-1]);return Number.isFinite(value)?`${Number((value*(pct?100:1)).toFixed(2))}${pct?'%':''}`:`#${n}`;});
        const remoteSkills=Object.values(remote.skills||{}).filter(skill=>skill.type_name&&skill.type!=='MazeNormal').map(skill=>{
          const level=skill.level?.['10']||Object.values(skill.level||{}).at(-1)||{};
          const values=level.param_list||[];
          return {id:String(skill.id),name:skill.name,type:skill.type,type_text:skill.type_name,desc:renderDesc(skill.desc,values),simple_desc:skill.simple_desc,max_level:10,params:values.map(value=>Array(10).fill(value)),icon:''};
        });
        if(remoteSkills.length)kit=remoteSkills;
        nanokaRanks=Object.entries(remote.ranks||{}).map(([rank,value])=>({id:String(value.id),rank:Number(rank),name:value.name,desc:renderDesc(value.desc,value.param_list||[]),icon:''}));
      }catch{/* La fiche reste utilisable avec le kit français déjà en cache. */}
    }
    details = { ...character, kit, eidolons:nanokaRanks.length?nanokaRanks:eidolons };
  }
  detailCache.set(key, details);
  putLocal('cache',`detail:studio69:${key}`,{items:details,savedAt:Date.now()}).catch(()=>{});
  return details;
}

// Sources de secours par nom interne (UI_AvatarIcon_<Nom>) pour les personnages récents
// dont l'image n'existe pas encore sur genshin.jmp.blue.
function genshinNameSources(item) {
  const raw = String(item?.name || item?._name || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  const pascal = raw.split(/[^A-Za-z0-9]+/).filter(Boolean).map(w => w[0].toUpperCase() + w.slice(1)).join('');
  if (!pascal || /^Traveler|^Voyageur/i.test(pascal)) return [];
  return [
    `https://gi.yatta.moe/assets/UI/UI_AvatarIcon_${pascal}.png`,
    `https://enka.network/ui/UI_AvatarIcon_${pascal}.png`,
    `https://api.ambr.top/assets/UI/UI_AvatarIcon_${pascal}.png`,
  ];
}

export function imageSet(game, item, category = item?._category || 'character') {
  const id = encodeURIComponent(item?._id || '');
  if (game === 'hsr') {
    const prefix = 'https://vizualabstract.github.io/StarRailStaticAPI/assets/';
    const fields = category === 'character' ? [item?.portrait, item?.preview, item?.icon] : [item?.icon, item?.preview, item?.portrait];
    const urls = fields.filter(Boolean).map(path => path.startsWith('http') ? path : prefix + path);
    if (category === 'character' && /^\d+$/.test(String(item?._id || ''))) {
      const id = encodeURIComponent(item._id);
      urls.push(`https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/image/character_portrait/${id}.png`);
      urls.push(`https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/image/character_preview/${id}.png`);
    }
    if (item?.nanokaIcon) {
      const assetType = category === 'character' ? 'avatarshopicon' : 'lightconemediumicon';
      urls.unshift(`https://static.nanoka.cc/assets/hsr/${assetType}/${encodeURIComponent(item._id)}.webp`);
    }
    // The bundled Nanoka light-cone catalogue is broader than the current
    // StarRailStaticAPI index and does not carry icon paths for every entry.
    // StarRailRes keeps portraits keyed by the same stable game ID.
    if (category === 'weapon' && /^\d+$/.test(String(item?._id || ''))) {
      urls.push(`https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/image/light_cone_portrait/${encodeURIComponent(item._id)}.png`);
    }
    return [...new Set(urls)];
  }
  if (game === 'gi') {
    if (category === 'character') {
      const rawIcon=String(item?.images?.filename_icon||item?._name||'').replace(/^UI_AvatarIcon_(?:Side_)?/,'').replace(/_Card$/,'');
      const generatedSlug=rawIcon.replace(/([a-z0-9])([A-Z])/g,'$1-$2').replace(/[^A-Za-z0-9]+/g,'-').replace(/^-|-$/g,'').toLowerCase();
      const prydwenAliases={ayaka:'kamisato-ayaka',ayato:'kamisato-ayato',kazuha:'kaedehara-kazuha',kokomi:'sangonomiya-kokomi',itto:'arataki-itto',sara:'kujou-sara',heizou:'shikanoin-heizou',heizo:'shikanoin-heizou',yae:'yae-miko',miko:'yae-miko',alhatham:'alhaitham',ambor:'amber',baizhuer:'baizhu',hutao:'hu-tao',qin:'jean',momoka:'kirara',shinobu:'kuki-shinobu',lanyan:'lan-yan',linette:'lynette',liney:'lyney',noel:'noelle',olorun:'ororon',shougun:'raiden-shogun','marionette-new':'sandrone','skirk-new':'skirk',tohma:'thoma',liuyun:'xianyun',feiyan:'yanfei',mizuki:'yumemizuki-mizuki',yunjin:'yun-jin'};
      const prydwenSlug=prydwenAliases[generatedSlug]||generatedSlug;
      return [
      // Prydwen's character portrait is the preferred compact avatar. The
      // shared image fallback handler advances through the other sources if
      // a character is not present there yet.
      prydwenSlug&&`https://cdn.prydwen.gg/images/genshin-impact/characters/${prydwenSlug}_icon.webp`,
      item?.images?.filename_icon && `https://enka.network/ui/${encodeURIComponent(item.images.filename_icon)}.png`,
      item?.images?.filename_icon && `https://gi.yatta.moe/assets/UI/${encodeURIComponent(item.images.filename_icon)}.png`,
      item?.images?.['mihoyo_icon'], item?.images?.portrait, item?.images?.image,
      `https://genshin.jmp.blue/characters/${id}/portrait`,
      `https://genshin.jmp.blue/characters/${id}/gacha-card`,
      `https://genshin.jmp.blue/characters/${id}/icon-big`,
      ...genshinNameSources(item),
    ].filter(Boolean);
    }
    if (category === 'weapon') return [
      item?.images?.filename_icon && `https://enka.network/ui/${encodeURIComponent(item.images.filename_icon)}.png`,
      item?.images?.filename_icon && `https://gi.yatta.moe/assets/UI/${encodeURIComponent(item.images.filename_icon)}.png`,
      item?.images?.['mihoyo_icon'], item?.images?.icon, item?.images?.['hoyowiki_icon'], `https://genshin.jmp.blue/weapons/${id}/icon.png`, `https://genshin.jmp.blue/weapons/${id}/icon`].filter(Boolean);
    if (category === 'artifact') return [
      item?.images?.filename_flower && `https://enka.network/ui/${encodeURIComponent(item.images.filename_flower)}.png`,
      item?.images?.filename_flower && `https://gi.yatta.moe/assets/UI/${encodeURIComponent(item.images.filename_flower)}.png`,
      item?.images?.flower, item?.images?.circlet, `https://genshin.jmp.blue/artifacts/${id}/flower-of-life`].filter(Boolean);
    if (category === 'material') {
      const filename=item?.images?.filename_icon;
      return [filename&&`https://gi.yatta.moe/assets/UI/${encodeURIComponent(filename)}.png`,
        filename&&`https://enka.network/ui/${encodeURIComponent(filename)}.png`,
        item?.images?.icon, item?.images?.item, item?.images?.['hoyowiki_icon'], item?.icon,
        filename&&`https://upload-os-bbs.hoyolab.com/game_record/genshin/item_icon/${encodeURIComponent(filename)}.png`,
        filename&&`https://api.ambr.top/assets/UI/item/${encodeURIComponent(filename)}.png`,
        filename&&`https://genshin-impact.fandom.com/wiki/Special:FilePath/${encodeURIComponent(filename)}.png`].filter(Boolean);
    }
  }
  if (game === 'ww') {
    const urls = [item?.portraitUrl, item?.imageUrl, item?.image, item?.iconUrl, item?.icon].filter(Boolean);
    return [...new Set(urls.map(sharpenWuwa))];
  }
  return [];
}

export function splashImage(game, item) {
  if (game === 'gi' && item?._category === 'character') {
    if (item?.preRelease && item?.images?.cover1) return item.images.cover1;
    const iconName = item?.images?.filename_icon || '';
    const gacha = iconName.replace('UI_AvatarIcon_', 'UI_Gacha_AvatarImg_');
    return gacha && gacha !== iconName ? `https://enka.network/ui/${encodeURIComponent(gacha)}.png` : (item?.images?.cover1 || item?.images?.card || `https://genshin.jmp.blue/characters/${encodeURIComponent(item._id)}/gacha-splash`);
  }
  if (game === 'hsr' && item?._category === 'character' && item?.preview) return `https://vizualabstract.github.io/StarRailStaticAPI/assets/${item.preview}`;
  return imageSet(game, item)[0] || '';
}

export function setBonuses(item, game) {
  const raw = item || {};
  if (game === 'gi') return [
    (raw['2-piece_bonus']||raw.effect2Pc) && { pieces: 2, text: raw['2-piece_bonus']||raw.effect2Pc },
    (raw['4-piece_bonus']||raw.effect4Pc) && { pieces: 4, text: raw['4-piece_bonus']||raw.effect4Pc },
  ].filter(Boolean);
  if (game === 'hsr') {
    const desc = Array.isArray(raw.desc) ? raw.desc : [];
    return desc.map((text, index) => ({ pieces: index ? 4 : 2, text, properties: raw.properties?.[index] || [] })).filter(row => row.text);
  }
  const text = raw.description || raw.desc || raw.subtitle || '';
  return text ? [{ pieces: 5, text }] : [];
}

export function skillList(game, character, details) {
  if (game === 'hsr') return (details?.kit || []).map(skill => {
    const typeLabels={ 'Basic ATK':'Attaque normale', Skill:'Compétence', Ultimate:'Ultime', Talent:'Talent', Technique:'Technique', 'Elation Skill':'Compétence d’Élation', 'Elation DMG':'DGT d’Élation', Assist:'Assistance', 'Memosprite Skill':'Compétence du mémosprite' };
    const rawLabel = skill.type_text || skill.type || 'Action';
    const label = typeLabels[rawLabel] || rawLabel;
    const code = /basic|normal|attaque de base/i.test(label) ? 'N' : /ultimate|ultime/i.test(label) ? 'Q' : /skill|compétence/i.test(label) ? 'E' : /talent|follow.?up/i.test(label) ? 'F' : 'T';
    const params = skill.params || [];
    const sourceLevel = Math.min(10, params[0]?.length || skill.max_level || 1);
    const levelIndex = sourceLevel - 1;
    const description = String(skill.desc || skill.simple_desc || '').replace(/#(\d+)\[(?:i|f1|f2|f3|s)\](%?)/g, (token, index, percent) => {
      const value = params[Number(index) - 1]?.[levelIndex];
      if (value == null) return token;
      const rendered = percent ? Number(value) * 100 : Number(value);
      return `${Number(rendered.toFixed(2))}${percent}`;
    });
    return { id: String(skill.id), name: skill.name || label, label, description, level: sourceLevel, image: skill.icon ? (skill.icon.startsWith('http') ? skill.icon : `https://vizualabstract.github.io/StarRailStaticAPI/assets/${skill.icon}`) : '', variants: [code] };
  });
  if (game === 'gi') {
    const types = ['talent-na', 'talent-skill', 'talent-burst'];
    return (details?.skillTalents || []).map((skill, index) => {
      const label = skill.unlock || ['Normal Attack', 'Elemental Skill', 'Elemental Burst'][index] || 'Talent';
      const description = skill.description || '';
      const hasHold = /\bhold\b|press and hold|can be held|while holding|maintain(?:ed|ing)?|hold to|appui long|maintenir|maintenez|maintenue|maintenu/i.test(description);
      const variants = index === 0
        ? ['N', 'C', 'Pa']
        : index === 1 ? ['E', ...(hasHold ? ['hE'] : []) ]
          : index === 2 ? ['Q'] : [];
      const table = details?.talentValues?.[`combat${index + 1}`]?.attributes;
      const values = table?.labels?.length ? table.labels.map(line => formatTalentValue(line, table.parameters)).filter(Boolean) : (skill.values || []);
      return { id: `gi-${index}`, name: skill.name || 'Compétence', label, description, level: 10, values, image: skill.icon || `https://genshin.jmp.blue/characters/${encodeURIComponent(character._id)}/${types[index] || 'talent-skill'}`, fallbacks: skill.iconFallbacks || [], variants };
    });
  }
  const types = details?.skills || [];
  return types.map((skill, index) => {
    const label = skill.label || skill.name || 'Compétence';
    const description = skill.description || '';
    const hasHold = /\bhold\b|press and hold|can be held|while holding|maintain(?:ed|ing)?|hold to|appui long|maintenir|maintenez|maintenue|maintenu/i.test(description);
    const variants = /basic attack|attaque normale|attaque de base/i.test(label) ? ['N', 'C', 'Pa']
      : /resonance skill|compétence de résonance/i.test(label) ? ['E', ...(hasHold ? ['hE'] : []) ]
        : /resonance liberation/i.test(label) ? ['Q'] : /intro skill/i.test(label) ? ['I'] : /outro skill/i.test(label) ? ['O'] : ['F'];
    return { ...skill, id: skill.id || `ww-${index}`, label, description, image: skill.icon || '', variants };
  });
}

function formatTalentValue(line, parameters) {
  const [label, template = ''] = String(line).split('|');
  const formatted = template.replace(/\{(param\d+):([^}]+)\}/g, (_, key, format) => {
    const value = parameters?.[key]?.[9];
    if (value == null) return '—';
    const percent = format.includes('P');
    const decimals = Number((format.match(/F(\d)/) || [])[1] || 0);
    return `${(Number(value) * (percent ? 100 : 1)).toLocaleString('fr-FR', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}${percent ? '%' : ''}`;
  });
  return `${label.trim()} · ${formatted}`;
}

function sharpenWuwa(url) {
  return String(url).replaceAll('&amp;', '&')
    .replace(/\/_ipx\/q_\d+&s_\d+x\d+\//, '/_ipx/q_95&s_700x700/');
}

export function equipmentImage(game, item, category) {
  return imageSet(game, item, category)[0] || '';
}

