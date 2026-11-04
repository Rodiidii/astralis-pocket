import { EQUIPMENT_CARDS as SOURCE_EQUIPMENT_CARDS } from './equipment-cards.js?v=20261101-equipment-4';
const EQUIPMENT_CARDS = [...new Map(SOURCE_EQUIPMENT_CARDS.map(card=>{
  const key=`${card.game}:${card.itemId||card.name}`;
  return [key,{...card,kind:'equipment',equipmentType:card.kind,rarity:'equipment',rarityLabel:'Équipement',id:`${card.game}-equipment-${String(card.itemId||card.name).toLowerCase().replace(/[^a-z0-9]+/g,'-')}`,number:`${card.game.toUpperCase()}-E-${String(card.index||1).padStart(3,'0')}`}];
})).values()];

export const BINDER_CHARACTERS = [
  { game:'gi', name:'Furina', element:'Hydro', skills:['Salon Solitaire','Let the People Rejoice'], flavor:'La scène est prête. À toi de jouer !' },
  { game:'gi', name:'Arlecchino', element:'Pyro', skills:['All-Reign Overworld','Balemoon Rising'], flavor:'La Maison veille toujours sur les siens.' },
  { game:'gi', name:'Alhaitham', element:'Dendro', skills:['Universality: An Elaboration on Form','Particular Field: Fetters of Phenomena'], flavor:'Une conclusion efficace vaut mieux qu’un long discours.' },
  { game:'gi', name:'Nilou', element:'Hydro', skills:['Dance of Haftkarsvar','Dance of Abzendegi: Distant Dreams, Listening Spring'], flavor:'Quand la musique commence, la scène appartient à tous.' },
  { game:'gi', name:'Neuvillette', element:'Hydro', skills:['O Tears, I Shall Repay','O Tide, I Have Returned'], flavor:'La justice suit son cours, avec calme et mesure.' },
  { game:'hsr', name:'Acheron', element:'Lightning', skills:['Slashed Dream','Stygian Resurge'], flavor:'Le chemin s’efface derrière moi.' },
  { game:'hsr', name:'Robin', element:'Physical', skills:['Pinion’s Aria','Vox Harmonique, Opus Cosmique'], flavor:'Que cette chanson accompagne chacun de vos pas.' },
  { game:'hsr', name:'Aventurine', element:'Imaginary', skills:['Bingo!','Roulette Shark'], flavor:'Tout est une question de mise… et de timing.' },
  { game:'ww', name:'Rover', element:'Spectro', skills:['Resonance Skill','Resonance Liberation'], flavor:'Le voyage continue, au rythme des résonances.' },
  { game:'ww', name:'Jiyan', element:'Aero', skills:['Windqueller','Emerald Storm: Oath'], flavor:'Une décision, puis une charge sans hésitation.' },
  { game:'ww', name:'Changli', element:'Fusion', skills:['Blazing Brilliance','Radiance of Fealty'], flavor:'Chaque mouvement prépare le suivant.' },
  { game:'ww', name:'Shorekeeper', element:'Spectro', skills:['Chaos Theory','Endless Collapse'], flavor:'Même au bord du chaos, une lumière demeure.' },
  { game:'ww', name:'Camellya', element:'Havoc', skills:['Valse of Bloom','Fervor of Chaos'], flavor:'La floraison n’attend jamais la permission.' },
];

const PRINTS = [
  ['common','Commune'], ['super','Super commune'], ['rare','Rare'], ['epic','Épique'],
];

const characterCards = BINDER_CHARACTERS.flatMap((character, index) => PRINTS.map(([rarity, rarityLabel], print) => ({
  id:`${character.game}-${index+1}-${rarity}`, game:character.game, kind:'character', categoryLabel:'Personnage', name:character.name,
  element:character.element, rarity, rarityLabel, number:`${character.game==='gi'?'GI':'HSR'}-${String(index+1).padStart(3,'0')}-${String(print+1).padStart(2,'0')}`,
  cardArtIndex:print, skills:character.skills, flavor:character.flavor,
  talent:print%2===0?character.skills[0]:null,
})));

export const BINDER_CARDS = [...characterCards, ...EQUIPMENT_CARDS];
