const GROUPS = {
  "Profil de voyage": [
    "Mémoriser le nom du voyageur", "Choisir un personnage compagnon", "Choisir une région préférée", "Noter les personnages favoris", "Mémoriser les objectifs du patch", "Garder le niveau d’aventure", "Garder le rang d’exploration", "Noter le temps de jeu souhaité", "Choisir un ton de rappel discret", "Exporter le profil compagnon"
  ],
  "Objectifs & rappels": [
    "Rappeler les tâches du jour", "Rappeler la résine à dépenser", "Rappeler les expéditions", "Rappeler les commissions", "Rappeler les tâches hebdomadaires", "Rappeler les boss hebdomadaires", "Rappeler les événements suivis", "Rappeler les bannières suivies", "Préparer une session courte", "Préparer une session longue"
  ],
  "Farm & ressources": [
    "Prioriser les matériaux manquants", "Éviter les ressources déjà suffisantes", "Repérer les livres disponibles aujourd’hui", "Répartir l’EXP sur plusieurs jours", "Répartir les Moras", "Prévoir les matériaux de boss", "Placer les boss hebdomadaires", "Réserver les jours d’artéfacts", "Convertir les livres bleus en EXP", "Résumer le stock restant"
  ],
  "Personnages & builds": [
    "Rappeler un personnage à monter", "Comparer deux builds enregistrés", "Préparer les matériaux jusqu’au niveau 90", "Préparer les talents 10/10/10", "Repérer une arme non attribuée", "Repérer les sets incomplets", "Noter une statistique cible", "Rappeler une rotation à tester", "Garder une note liée au personnage", "Retrouver une capture de build"
  ],
  "Équipes & combat": [
    "Suggérer de revoir les rôles d’équipe", "Rappeler une équipe d’endgame", "Préparer une équipe du Théâtre", "Préparer deux équipes d’Abîme", "Vérifier la présence de soin", "Vérifier la présence de bouclier", "Relire les buffs saisis", "Rappeler le personnage actif", "Garder une rotation de référence", "Comparer le temps d’une équipe"
  ],
  "Vœux & épargne": [
    "Suivre les primogemmes quotidiennes", "Calculer les vœux disponibles", "Rappeler l’objectif de bannière", "Afficher la pity saisie", "Afficher la garantie saisie", "Comparer C0 et les constellations", "Comparer l’objectif d’arme", "Tracer les gains de la semaine", "Tracer les gains du mois", "Préparer une épargne de patch"
  ],
  "Lore & collection": [
    "Retrouver la fiche lore d’un personnage", "Explorer une région favorite", "Retrouver une faction", "Relier un personnage à sa région", "Rappeler un anniversaire", "Suggérer une page lore à lire", "Garder un ship favori sans notification", "Garder une citation personnelle", "Retrouver les médias d’un personnage", "Découvrir une anecdote enregistrée"
  ],
  "Veille & actualités": [
    "Résumer les actualités non lues", "Signaler une vidéo disponible", "Rappeler un programme spécial", "Suivre une bannière", "Suivre un événement à primogemmes", "Afficher la date de fin d’un événement", "Repérer les nouvelles fiches", "Signaler une actualisation de catalogue", "Garder une annonce en favori", "Marquer les nouveautés comme lues"
  ],
  "Carnet & organisation": [
    "Créer une note rapide", "Épingler une note", "Retrouver les notes d’un personnage", "Créer une tâche depuis une fiche", "Classer une tâche par priorité", "Répartir un objectif sur la semaine", "Reprendre les tâches en retard", "Préparer une checklist hebdomadaire", "Garder un résultat de test", "Rappeler une date personnelle"
  ],
  "Confort & accompagnement": [
    "Proposer une action courte", "Proposer une action sans résine", "Éviter les rappels répétitifs", "Respecter les préférences de région", "Adapter les conseils aux favoris", "Utiliser le compagnon choisi", "Désactiver l’accompagnement", "Réinitialiser les informations du compagnon", "Exporter les informations du compagnon", "Expliquer d’où vient une suggestion"
  ]
};

export const ASSISTANT_FEATURES = Object.entries(GROUPS).flatMap(([category, items]) => items.map((label, index) => ({ id: `${category}-${index}`, category, label })));
export const ASSISTANT_GROUPS = GROUPS;
export const ASSISTANT_PROFILE_KEY = 'astralis:gi:assistant-profile';
export const ASSISTANT_PROFILES_KEY = 'astralis:gi:assistant-profiles';
export function readAssistantProfiles(storage = localStorage) {
  const defaults = { name:'', companion:'', region:'', favorites:[], ships:[], goal:'', enabled:true, personaCharacter:'', proactive:true, proactiveSound:false, proactiveInterval:5, messageDuration:90 };
  try {
    let rows = JSON.parse(storage.getItem(ASSISTANT_PROFILES_KEY) || 'null');
    if (!Array.isArray(rows) || !rows.length) {
      rows = [{ id:'companion-1', label:'Compagnon 1', ...defaults, ...JSON.parse(storage.getItem(ASSISTANT_PROFILE_KEY) || '{}') }];
      storage.setItem(ASSISTANT_PROFILES_KEY, JSON.stringify(rows));
    }
    return rows.slice(0,5);
  } catch { return [{ id:'companion-1', label:'Compagnon 1', ...defaults }]; }
}
export function saveAssistantProfile(profile, storage = localStorage) {
  const rows=readAssistantProfiles(storage), index=rows.findIndex(x=>x.id===profile.id);
  if(index<0) rows[0]={...rows[0],...profile}; else rows[index]={...rows[index],...profile};
  storage.setItem(ASSISTANT_PROFILES_KEY,JSON.stringify(rows.slice(0,5)));
  storage.setItem(ASSISTANT_PROFILE_KEY,JSON.stringify(rows[index<0?0:index]));
  return rows[index<0?0:index];
}
export function selectAssistantProfile(id, storage = localStorage) {
  const profile=readAssistantProfiles(storage).find(x=>x.id===id); if(!profile)return null;
  storage.setItem(ASSISTANT_PROFILE_KEY,JSON.stringify(profile)); return profile;
}
export function addAssistantProfile(storage = localStorage) {
  const rows=readAssistantProfiles(storage); if(rows.length>=5)return null;
  const token=globalThis.crypto?.randomUUID?.()||`${Date.now()}-${Math.random().toString(36).slice(2,8)}`;
  const profile={...rows[0],id:`companion-${token}`,label:`Compagnon ${rows.length+1}`,name:'',companion:'',personaCharacter:'',favorites:[],ships:[],goal:''};
  rows.push(profile);storage.setItem(ASSISTANT_PROFILES_KEY,JSON.stringify(rows));storage.setItem(ASSISTANT_PROFILE_KEY,JSON.stringify(profile));return profile;
}
export function deleteAssistantProfile(storage = localStorage) {
  const rows=readAssistantProfiles(storage);if(rows.length<=1)return rows[0];
  const active=readAssistantProfile(storage),next=rows.filter(x=>x.id!==active.id);storage.setItem(ASSISTANT_PROFILES_KEY,JSON.stringify(next));storage.setItem(ASSISTANT_PROFILE_KEY,JSON.stringify(next[0]));return next[0];
}

export const ASSISTANT_SUGGESTIONS = [
  ['farm','Vérifier les matériaux manquants d’un personnage','Plan de farm'],['builds','Comparer les recommandations de build','Mes builds'],['lore','Ouvrir une fiche lore liée à tes favoris','Lore & archives'],['wishes','Mettre à jour le solde de primogemmes','Vœux & objectifs'],['endgame','Préparer les équipes du prochain endgame','Endgame'],['teams','Revoir la rotation de ta dernière équipe','Équipes'],['events','Consulter les événements qui se terminent bientôt','Événements Genshin'],['events','Lire les actualités non consultées','Événements Genshin'],['characters','Vérifier les talents d’un personnage favori','Personnages'],['weapons','Comparer les armes disponibles','Armes'],['sets','Voir les sets compatibles avec ton équipe','Sets & reliques'],['tasks','Créer une petite tâche pour la prochaine session','Tâches & objectifs'],['notes','Ajouter une note à ton carnet','Carnet'],['media','Regarder une bande-annonce de personnage','Médias'],['favorites','Ranger tes favoris par priorité','Favoris'],['calc','Compléter les résultats d’une feuille de calcul','Calc Sheets'],['profile','Actualiser ton profil public','Profil Akasha'],['hoyolab','Vérifier la résine HoYoLAB enregistrée','HoYoLAB'],['farming','Planifier une session courte de farm','Plan de farm'],['endgame','Choisir des équipes pour les étages 9 et 10','Endgame'],['endgame','Noter les boss du Théâtre','Endgame'],['endgame','Préparer une stratégie de Carnage','Endgame'],['wishes','Comparer les scénarios C0 et C1','Vœux & objectifs'],['wishes','Ajouter les vœux gagnés aujourd’hui','Vœux & objectifs'],['characters','Consulter les matériaux d’ascension','Personnages'],['builds','Créer une variante de build sauvegardée','Mes builds'],['teams','Associer les builds enregistrés à une équipe','Équipes'],['events','Vérifier les dates et récompenses des événements','Événements Genshin'],['lore','Explorer une région ou une faction','Lore & archives'],['tasks','Marquer les objectifs terminés','Tâches & objectifs'],['data','Vérifier la date de mise à jour des données','Sources & données'],['changelog','Lire les changements de la dernière mise à jour','Journal des données'],['tierlist','Comparer les rôles des personnages','Tier list'],['optimizer','Ouvrir l’optimiseur de personnage','Optimiseurs'],['skowt','Parcourir les modèles 3D disponibles','Skowt · modèles & médias'],['dashboard','Revenir au résumé du compte','Tableau de bord'],['materials','Vérifier les matériaux déjà en stock','Objets & matériaux'],['farming','Revoir le calendrier de farm de la semaine','Plan de farm'],['sets','Enregistrer un set à farmer','Sets & reliques'],['characters','Ajouter un favori à la collection','Personnages']
].map(([section,text,title])=>({section,text,title}));

export function readAssistantProfile(storage = localStorage) {
  try {
    const value = JSON.parse(storage.getItem(ASSISTANT_PROFILE_KEY) || '{}');
    const profiles=readAssistantProfiles(storage),active=profiles.find(x=>x.id===value.id);
    return { name: '', companion: '', region: '', favorites: [], ships: [], goal: '', enabled: true, personaCharacter: '', proactive: true, proactiveSound: false, proactiveInterval: 5, messageDuration: 90, ...(active||{}), ...value, id:value.id||active?.id||profiles[0]?.id||'companion-1' };
  } catch {
    return { name: '', companion: '', region: '', favorites: [], ships: [], goal: '', enabled: true, proactiveInterval:5, messageDuration:90 };
  }
}

// 30 openings × 10 context-sensitive endings = 300 short, locally generated lines
// per selected character. These are original companion prompts, not game quotations.
const VOICE_BANK = {
  nilou: [
    'Je viens de répéter une chorégraphie… et j’ai pensé à toi. On prépare doucement les matériaux qu’il te manque ?',
    'Pas besoin de tout faire aujourd’hui. Quelques pas bien choisis, comme dans une danse, et tu auras déjà avancé.',
    'La scène est plus belle quand chacun trouve son rythme. Pour ton équipe aussi, on peut chercher une rotation qui te ressemble.',
    'J’espère que ta journée se passe bien ! Si tu veux, je peux t’aider à choisir une petite chose à faire, sans te presser.'
  ],
  skirk: [
    'Tu veux progresser ? Choisis une cible. Termine ce que tu commences.',
    'Ta rotation manque de cohérence. Reprends-la lentement, puis recommence jusqu’à ce qu’elle devienne naturelle.',
    'Ne gaspille pas ta résine. Vérifie les matériaux manquants avant de partir.',
    'Un combat perdu révèle une faille. Regarde ton équipe, pas la chance.'
  ],
  furina: [
    'Une nouvelle scène s’offre à nous ! Choisissons d’abord notre objectif… le grand final attendra un peu.',
    'Même une star doit parfois consulter son planning. Voyons ce qui mérite vraiment ton attention aujourd’hui !',
    'Je propose une répétition générale de ta rotation. Avec un peu de panache, elle sera inoubliable !'
  ],
  nahida: [
    'J’ai une petite question : quelle ressource te manque le plus en ce moment ? On pourrait commencer par celle-là.',
    'Les progrès ressemblent à une graine. Un peu de soin chaque jour, et tu verras bientôt la différence.',
    'J’ai remarqué un lien intéressant entre tes objectifs et ton équipe. Tu veux qu’on l’explore ensemble ?'
  ],
  zhongli: [
    'Toute préparation gagne à être menée avec mesure. Commençons par les ressources réellement nécessaires.',
    'Une équipe bien bâtie repose sur des fondations solides. Souhaites-tu revoir ses rôles et sa rotation ?',
    'Les souvenirs de tes anciens combats peuvent encore t’être utiles. J’ai conservé tes notes à portée de main.'
  ],
  alhaitham: [
    'J’ai vérifié tes priorités. La tâche la plus efficace est aussi la plus évidente : commence par ce qui te manque réellement.',
    'Inutile d’ajouter une étape si elle ne sert pas ton objectif. Ton plan de farm peut être simplifié.',
    'Ta rotation est enregistrée. Vérifie simplement que les temps de recharge s’alignent.'
  ],
  kaveh: [
    'Ton équipe a du potentiel ! Avec quelques ajustements, elle pourrait être aussi harmonieuse qu’un projet bien pensé.',
    'Tu as déjà fait une bonne partie du travail. Ne laisse pas les derniers matériaux te décourager, on va organiser ça.',
    'J’ai regardé tes builds… On peut faire quelque chose de vraiment élégant avec ce que tu possèdes déjà !'
  ],
  cyno: [
    'J’ai un conseil sérieux pour ton farm. Promis, je ne le transformerai pas en blague… enfin, j’essaierai.',
    'Une rotation bien répétée devient un réflexe. C’est presque comme raconter une blague : le timing fait tout.',
    'Tu veux une anecdote ? Après le farm, bien sûr. Un bon jugement commence par les priorités.'
  ],
  dehya: [
    'Pas besoin de porter tout le poids d’un coup. Dis-moi ce qui te manque et on s’en occupe étape par étape.',
    'Si un combat te résiste, on peut revoir la protection de l’équipe. Je serai là pour couvrir tes arrières.',
    'Tu as assez travaillé pour aujourd’hui ? Même les plus solides doivent souffler.'
  ],
  itto: [
    'Hé ! On va régler ce farm en deux temps trois mouvements. L’Onikabuto… euh, moi, je m’occupe du moral !',
    'Ton équipe est presque prête. Il lui manque quoi ? Dis-le et le grand Arataki Itto te trouvera une solution !',
    'Petit défi : une session, un objectif, zéro abandon. Tu relèves le pari ?'
  ],
  navia: [
    'On ne va pas laisser quelques matériaux gâcher la journée. Je t’aide à organiser tout ça avec méthode.',
    'J’ai préparé plusieurs pistes pour ton équipe. Choisissons celle qui te met le plus à l’aise.',
    'Une petite pause, puis on reprend ensemble. L’important, c’est de garder le cap.'
  ],
  citlali: [
    'Hm… assieds-toi deux secondes. On va regarder ce qu’il te manque, sans courir partout comme Ororon.',
    'J’ai vu ton planning. Il est faisable, mais ne sacrifie pas ton repos pour quelques matériaux.',
    'Tu veux un conseil ? Commence par le plus urgent. Après, on pourra se servir un verre et parler d’autre chose.'
  ],
  mavuika: [
    'On avance ensemble. Fixe une priorité claire et on fera le reste avec détermination.',
    'Une équipe solide se construit par l’action. Vérifions les rôles, puis passons à l’entraînement.',
    'Tu as déjà parcouru beaucoup de chemin. Garde ton énergie pour ce qui compte vraiment.'
  ],
  collei: [
    'Euh… j’ai préparé une petite liste pour t’aider. On peut la suivre tranquillement, si tu veux !',
    'Je sais que ça peut sembler beaucoup, mais une étape à la fois, ça devient plus facile.',
    'Tu veux revoir ton équipe avec moi ? Je prendrai des notes pour ne rien oublier !'
  ],
  paimon: [
    'Paimon a vérifié ton plan ! On commence par les matériaux manquants, et après… petite pause gourmande ?',
    'Hé, ne pars pas sans regarder les récompenses du jour ! Paimon ne veut pas que tu rates quelque chose.',
    'Cette équipe a l’air forte ! Mais Paimon a une question très importante : qui apporte les snacks ?'
  ]
};

export function characterNudge(character, context = {}) {
  const raw=String(character?._name||character?.name||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z]/g,'');
  const bank=VOICE_BANK[raw];
  if(bank){
    if(raw==='nilou'&&context.farmCount)return ['Entre deux pas de danse, je me suis dit qu’on pourrait préparer les matériaux des '+context.farmCount+' personnages de ta liste. Sans se presser !','Ta prochaine chorégraphie peut attendre un peu… On regarde ensemble les ressources qu’il te manque ?'][Math.floor(Math.random()*2)];
    if(raw==='skirk'&&context.farmCount)return `Tu as ${context.farmCount} personnage(s) à préparer. Commence par leurs matériaux prioritaires. N’en néglige aucun.`;
    if(raw==='nahida'&&context.openTasks)return `Il reste ${context.openTasks} objectif(s). Lequel te semble le plus important aujourd’hui ?`;
    if(raw==='alhaitham'&&context.teamCount)return `Tu as ${context.teamCount} équipe(s) enregistrée(s). Choisis celle qui sert ton objectif actuel.`;
    return bank[Math.floor(Math.random()*bank.length)];
  }
  const element=String(character?.elementText||character?.element||'').toLowerCase();
  const tone={pyro:'On passe à l’action',hydro:'Gardons le rythme',cryo:'Restons méthodiques',electro:'J’ai repéré une piste utile',dendro:'Faisons pousser ta progression',anemo:'Un petit détour peut aider',geo:'Bâtissons la suite',glacio:'Un pas après l’autre',havoc:'Concentrons-nous sur la cible',spectro:'Voyons plus clair'}[element]||'J’ai regardé tes priorités';
  if(context.farmCount)return `${tone} : ${context.farmCount} personnage(s) figurent dans ton plan de farm. Vérifie les ressources restantes avant de choisir ta prochaine session.`;
  if(context.openTasks)return `${tone} : il reste ${context.openTasks} objectif(s) ouverts. Lequel veux-tu terminer en premier ?`;
  if(context.teamCount)return `${tone} : tu as ${context.teamCount} équipe(s) enregistrée(s). On peut reprendre une rotation ou revoir un build.`;
  const lines=['Je peux t’aider à choisir une prochaine étape. Qu’est-ce qui te ferait le plus avancer aujourd’hui ?','On peut revoir ton farm, tes équipes ou tes objectifs. Tu préfères commencer par quoi ?','Pas besoin de tout faire d’un coup. Choisissons une priorité, puis on verra la suite.'];
  return lines[Math.floor(Math.random()*lines.length)];
}

export function assistantReply(message, profile, snapshot = {}) {
  const q = String(message || '').trim().toLocaleLowerCase('fr');
  const name = profile.name ? `${profile.name}, ` : '';
  if (!q) return `${name}je peux t’aider à choisir une prochaine action. Demande-moi par exemple quoi farmer aujourd’hui, quels objectifs restent, ou combien de vœux tu as préparés.`;
  if (/farm|farmer|résine|materiau|matériau|livre|mora|xp/.test(q)) return `${name}${snapshot.farmCount ? `tu as ${snapshot.farmCount} personnage(s) dans ton plan de farm. ` : 'ton plan de farm est encore vide. '}Commence par les ressources qui manquent vraiment; le calendrier tient compte des stocks saisis et des jours de disponibilité des livres.`;
  if (/équipe|team|abyss|abîme|theatre|théâtre|carnage|rotation/.test(q)) return `${name}${snapshot.teamCount ? `tu as ${snapshot.teamCount} équipe(s) enregistrée(s). ` : 'aucune équipe n’est encore enregistrée. '}Choisis une équipe sauvegardée dans l’atelier, puis vérifie ses rôles, son soin ou bouclier et sa rotation.`;
  if (/voeu|vœu|primo|pity|banni/.test(q)) return `${name}le suivi des vœux est enregistré sur cet appareil. Ouvre « Vœux & objectifs » pour mettre à jour tes primogemmes, ta pity, ta garantie et comparer les probabilités cumulées.`;
  if (/lore|histoire|region|région|faction|ship/.test(q)) return `${name}${profile.region ? `tu préfères ${profile.region}. ` : ''}Ouvre « Lore & archives » et utilise la recherche pour relier régions, personnages, factions et événements historiques. Tes ships restent privés dans ton profil local.`;
  if (/objectif|tache|tâche|aujourd|aujourd'hui|journée|rappel/.test(q)) return `${name}${snapshot.openTasks ? `${snapshot.openTasks} objectif(s) sont encore ouverts. ` : ''}Choisis une tâche prioritaire et une action réalisable aujourd’hui; tes échéances et rappels sont conservés dans Astralis.`;
  return `${name}j’ai gardé ta préférence${profile.goal ? ` « ${profile.goal} »` : ''}. Je peux t’orienter vers le farm, les équipes, les vœux, le lore, les objectifs ou les nouveautés. Les données personnelles du compagnon restent stockées localement.`;
}
