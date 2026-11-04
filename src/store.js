const prefix = 'astralis:';

function read(key, fallback) {
  try { return JSON.parse(localStorage.getItem(prefix + key)) ?? fallback; }
  catch { return fallback; }
}

function write(key, value) {
  localStorage.setItem(prefix + key, JSON.stringify(value));
  window.dispatchEvent(new CustomEvent('astralis:change', { detail: key }));
}

export function favorites() { return read('favs', {}); }
export function isFavorite(game, category, id) { return !!favorites()[`${game}:${category}:${id}`]; }
export function toggleFavorite(game, category, id) {
  const all = favorites(), key = `${game}:${category}:${id}`;
  if (all[key]) delete all[key]; else all[key] = true;
  write('favs', all);
}

export function ownedMap(game) { return read(`owned:${game}`, {}); }
export function isOwned(game, id) { return !!ownedMap(game)[id]; }
export function toggleOwned(game, id) {
  const all = ownedMap(game);
  if (all[id]) delete all[id]; else all[id] = true;
  write(`owned:${game}`, all);
}

export function teams(game) { return read(`teams:${game}`, []); }
export function saveTeam(game, team) {
  const all = teams(game).filter(item => item.id !== team.id);
  all.unshift(team);
  write(`teams:${game}`, all);
}
export function deleteTeam(game, id) { write(`teams:${game}`, teams(game).filter(item => item.id !== id)); }

export function notes(game) { return read(`notes:${game}`, []); }
export function saveNote(game, note) {
  const all = notes(game).filter(item => item.id !== note.id);
  all.unshift(note);
  write(`notes:${game}`, all);
}
export function deleteNote(game, id) { write(`notes:${game}`, notes(game).filter(item => item.id !== id)); }

export function tasks(game) { return read(`tasks:${game}`, []); }
export function allTasks() { return ['hsr', 'gi', 'ww'].flatMap(game => tasks(game).map(task => ({ ...task, game }))); }
export function saveTask(game, task) {
  const all = tasks(game).filter(item => item.id !== task.id);
  all.unshift({ ...task, updated: Date.now() });
  write(`tasks:${game}`, all);
}
export function updateTask(game, id, patch) {
  write(`tasks:${game}`, tasks(game).map(task => task.id === id ? { ...task, ...patch, updated: Date.now() } : task));
}
export function deleteTask(game, id) { write(`tasks:${game}`, tasks(game).filter(item => item.id !== id)); }

export function dailyTeam(game) { return read(`daily-team:${game}`, null); }
export function saveDailyTeam(game, team) { write(`daily-team:${game}`, team); }

export function exportData() {
  const games = ['hsr', 'gi', 'ww'];
  return {
    format: 'astralis-save', version: 5, exportedAt: new Date().toISOString(), favorites: favorites(),
    owned: Object.fromEntries(games.map(game => [game, ownedMap(game)])),
    games: Object.fromEntries(games.map(game => [game, { teams: teams(game), notes: notes(game), tasks: tasks(game), dailyTeam: dailyTeam(game) }])),
  };
}

export function importData(data) {
  if (!data || typeof data !== 'object') throw new Error('Sauvegarde invalide.');
  write('favs', data.favorites || data.favs || {});
  for (const game of ['hsr', 'gi', 'ww']) {
    if (data.owned?.[game]) write(`owned:${game}`, data.owned[game]);
    if (data.games?.[game]?.teams) write(`teams:${game}`, data.games[game].teams);
    if (data.games?.[game]?.notes) write(`notes:${game}`, data.games[game].notes);
    if (data.games?.[game]?.tasks) write(`tasks:${game}`, data.games[game].tasks);
    if (data.games?.[game]?.dailyTeam) write(`daily-team:${game}`, data.games[game].dailyTeam);
  }
}

export function statSnapshot() {
  const allFavorites = favorites();
  return ['hsr', 'gi', 'ww'].map(game => ({
    game,
    owned: Object.keys(ownedMap(game)).length,
    favorites: Object.keys(allFavorites).filter(key => key.startsWith(`${game}:`)).length,
    teams: teams(game).length,
  }));
}

