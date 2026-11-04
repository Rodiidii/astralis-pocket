from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "assets/data/gi-companion-interactions-fr.json"
PERSONALITIES = ROOT.parent.parent / "Personnalites-personnages-Genshin.md"


def key(value: str) -> str:
    value = unicodedata.normalize("NFD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", value)


def load_personalities() -> dict[str, dict[str, object]]:
    profiles = {}
    line_pattern = re.compile(r"^- \*\*(.+?)\*\* — (.+?) \*Sujets :\* (.+?)\s*$")
    for line in PERSONALITIES.read_text(encoding="utf-8").splitlines():
        match = line_pattern.match(line)
        if not match:
            continue
        name, description, subjects = match.groups()
        profiles[key(name)] = {"description": description, "subjects": [part.strip().rstrip(".") for part in subjects.split(";") if part.strip()]}
    aliases = {"raiden": "shogunraiden", "wanderer": "nomade", "traveler": "aether"}
    return {aliases.get(name, name): profile for name, profile in profiles.items()}


OVERRIDES = {
    "nilou": "gentle", "skirk": "cold", "flins": "solemn", "illuga": "alert",
    "columbina": "lyrical", "furina": "theatrical", "fischl": "theatrical",
    "itto": "boisterous", "aratakiitto": "boisterous", "hu tao": "playful",
    "hutao": "playful", "cyno": "deadpan", "alhaitham": "analytical", "kaveh": "expressive",
    "nahida": "gentle", "mualani": "bright", "kachina": "shy", "xilonen": "relaxed",
    "navia": "warm", "arlecchino": "cold", "sandrone": "cold", "ronova": "cold",
    "capitano": "solemn", "istaroth": "lyrical", "zhongli": "formal", "neuvillette": "formal",
    "ayaka": "formal", "kamisatoayaka": "formal", "kokomi": "analytical",
    "sangonomiyakokomi": "analytical", "jean": "formal", "raiden": "solemn",
    "shogunraiden": "solemn", "wanderer": "caustic", "nomade": "caustic",
    "rosaria": "dry", "rosalia": "dry", "diluc": "cold", "xiao": "cold",
    "venti": "playful", "kaeya": "teasing", "yaemiko": "teasing", "lis a": "teasing",
    "lisa": "teasing", "tighnari": "dry", "faruzan": "professorial", "mona": "formal",
    "dehya": "warm", "beidou": "bold", "yoimiya": "bright", "amber": "bright",
    "bennett": "bright", "klee": "bright", "collei": "shy", "sucrose": "shy",
    "layla": "shy", "freminet": "shy", "sigewinne": "gentle", "baizhu": "gentle",
    "citlali": "bluntwarm", "ororon": "eccentric", "mavuika": "bold", "zibai": "solemn",
    "vesna": "resolute", "vodyanitsa": "lyrical", "odette": "elegant", "linnea": "gentle",
    "nefer": "calculating", "jahoda": "practical", "ain o": "bright", "aino": "bright",
    "ineffa": "precise", "prune": "theatrical", "lohen": "teasing", "albedo": "analytical",
    "keqing": "practical", "chiori": "dry", "clorinde": "dry", "yelan": "calculating",
    "ningguang": "calculating", "kazuha": "lyrical", "kaedeharakazuha": "lyrical",
    "qiqi": "terse", "razor": "terse", "shenhe": "terse", "eula": "formal",
    "xingqiu": "elegant", "yun jin": "elegant", "yunjin": "elegant", "gaming": "bright",
    "varesa": "bright", "iansan": "coach", "xianyun": "formal", "kirara": "bright",
    "mika": "shy", "ganyu": "gentle", "noelle": "gentle", "noelle": "gentle",
    "chongyun": "formal", "yanfei": "professorial", "navia": "warm", "tartaglia": "bold",
    "wriothesley": "dry", "xinyan": "bold", "dori": "theatrical", "charlotte": "bright",
    "ch asca": "bold", "chasca": "bold", "escoffier": "precise", "if a": "relaxed",
    "ifa": "relaxed", "lan yan": "gentle", "lanyan": "gentle", "lauma": "lyrical",
    "yumemizukimizuki": "gentle", "mizuki": "gentle", "dahlia": "elegant",
}


def choose_mode(name: str, profile: dict[str, object]) -> str:
    normalized = key(name)
    if normalized in OVERRIDES:
        return OVERRIDES[normalized]
    description = str(profile.get("description", "")).lower()
    if any(word in description for word in ("solennelle", "cérémon", "digne", "grave", "protocolaire")):
        return "formal"
    if any(word in description for word in ("froid", "implacable", "sèche", "sarcastique", "cassant", "peu de mots")):
        return "dry"
    if any(word in description for word in ("timide", "hésitant", "anxieuse", "réservée", "réservé")):
        return "shy"
    if any(word in description for word in ("taquin", "joueur", "joueuse", "malicieuse", "ironique", "espiègle")):
        return "playful"
    if any(word in description for word in ("méthodique", "pragmatique", "stratégique", "rigoureuse", "rationnelle", "précise")):
        return "practical"
    if any(word in description for word in ("douce", "gentille", "bienveillante", "attentive", "chaleureuse")):
        return "gentle"
    return "bright"


THEMES = {
    "farm": [
        "vérifier ce qui manque vraiment avant de dépenser la résine",
        "choisir une seule ressource prioritaire et s’arrêter quand le stock suffit",
        "faire d’abord les aptitudes ouvertes aujourd’hui, puis revoir le reste demain",
        "garder une session courte plutôt que courir après tout à la fois",
        "noter les quantités avant de lancer le farm; ça évitera les allers-retours",
        "commencer par le matériau qui bloque l’amélioration, pas par celui qu’on a déjà en trop",
    ],
    "team": [
        "tester une rotation courte et regarder si l’énergie suit jusqu’à l’ultime",
        "faire passer le soutien avant le personnage actif, puis vérifier le temps de recharge",
        "garder une vraie fenêtre pour le soin ou le bouclier au lieu de tout lancer d’un coup",
        "changer une seule chose dans la rotation; sinon on ne saura pas ce qui a aidé",
        "essayer l’équipe sur une cible solide et observer où le rythme se casse",
        "raccourcir l’enchaînement : une rotation fiable vaut mieux qu’un joli plan impossible à répéter",
    ],
    "lore": [
        "reprendre les détails autour de « {hook} »; ce genre d’indice mérite qu’on s’y attarde",
        "relire ce qu’on sait au sujet de « {hook} », puis distinguer les faits des rumeurs",
        "parler de « {hook} » sans tirer de conclusion trop vite; l’histoire laisse encore des zones d’ombre",
        "garder une note sur « {hook} »; ce détail prend un autre sens quand on le remet dans son contexte",
        "revenir sur « {hook} » et regarder qui en subit réellement les conséquences",
        "comparer les récits autour de « {hook} »; les petits écarts sont parfois les plus intéressants",
    ],
    "rest": [
        "faire une pause avant de reprendre; même les meilleures équipes ont besoin de souffler",
        "garder le jeu léger aujourd’hui et choisir une seule petite chose à terminer",
        "laisser les objectifs de côté quelques minutes; une bonne histoire ou un thé ferait du bien",
        "se raconter une anecdote sur {hook} au lieu de transformer chaque connexion en corvée",
        "prendre le temps de regarder le paysage; on oublie parfois pourquoi on aime revenir ici",
        "terminer sur une petite victoire, puis s’arrêter là. Ça compte aussi, tu sais",
    ],
}


OPENERS = {
    "gentle": ["J’ai pensé à quelque chose de simple : {body}. On peut y aller à notre rythme.", "Si tu veux, on commence par {body}. Rien ne presse après.", "Ça te dirait qu’on {body} ? Je resterai avec toi pour la suite."],
    "cold": ["On va faire simple : {body}. Pas de détour.", "D’abord, {body}. Le reste attendra.", "{body}. Une décision claire vaut mieux que de s’éparpiller."],
    "dry": ["Bon. {body}. Au moins, ce sera réglé.", "On pourrait {body}. Ça nous évitera une mauvaise surprise.", "{body}. Et non, je ne vais pas appeler ça une aventure."],
    "formal": ["Je te propose ceci : {body}. Nous ajusterons si nécessaire.", "À mon avis, le mieux est de {body}. C’est la méthode la plus raisonnable.", "Si tu en es d’accord, {body}. Nous n’avons pas besoin de précipiter la suite."],
    "solemn": ["Commençons par {body}. Chaque chose en son temps.", "{body}. Il vaut mieux agir avec mesure.", "Je retiens une priorité : {body}. Le reste suivra."],
    "analytical": ["J’ai regardé le problème : {body}. C’est l’étape qui apporte le plus.", "Le plus efficace serait de {body}. On pourra mesurer le résultat.", "{body}. Une variable à la fois; autrement, le test ne nous apprendra rien."],
    "practical": ["J’ai une solution concrète : {body}. Je m’occupe du reste.", "Autant {body}. Ça nous fera gagner du temps.", "On commence par {body}; je préfère un plan faisable à une liste interminable."],
    "playful": ["J’ai un plan ! {body}. Et promis, je ne le présenterai pas comme une grande épopée… enfin, presque.", "Et si on {body} ? Ça nous fera une petite victoire à raconter.", "Bon, j’ai une idée : {body}. Tu me suis ?"],
    "theatrical": ["Mesdames et messieurs — enfin, toi surtout — {body}. La scène est à nous !", "Pour le prochain acte, {body}. Avec juste ce qu’il faut de panache.", "J’annonce une stratégie digne d’un grand final : {body}."],
    "lyrical": ["Le vent nous laisse le temps de {body}. Écoutons-le un instant.", "{body}. Il y a des réponses qui apparaissent quand on ne force pas le chemin.", "J’aimerais {body}; certaines choses se comprennent mieux dans le calme."],
    "shy": ["Euh… on pourrait peut-être {body}. Enfin, si ça te convient.", "J’ai une petite suggestion : {body}. On peut changer d’avis, bien sûr.", "Je me disais… {body}. Ça pourrait nous aider, non ?"],
    "bright": ["Allez, on peut {body} ! Une étape après l’autre, et ce sera fait.", "J’ai une idée : {body}. Ça te tente ?", "On se lance ? Je propose de {body}. Je suis partant·e !"],
    "warm": ["On va s’en sortir. Commençons par {body}; je reste dans le coin si tu as besoin.", "Je te propose {body}. On fera le reste ensemble.", "Pas besoin de porter tout ça seul·e : {body}, puis on avise."],
    "expressive": ["Attends, j’ai une idée — {body}. Je sais, je m’emballe, mais celle-là est bonne !", "Franchement, {body}. Après tout ce qu’on a traversé, ça devrait aller.", "Je veux bien tenter {body}; j’ai déjà trois idées de rechange si ça rate."],
    "boisterous": ["Hé ! {body}. Et si quelqu’un râle, le grand Itto — enfin, moi — prend la responsabilité !", "Défi du jour : {body}. Qui est avec moi ?", "On va {body}, et avec panache ! Pas question de perdre contre un matériau."],
    "teasing": ["Oh ? {body}. Je me demande combien de temps il te faudra pour reconnaître que c’est une bonne idée.", "Je pourrais te laisser trouver ça seul·e… mais {body} sera plus amusant.", "Allons, {body}. Je promets de ne raconter à personne que c’était mon idée."],
    "caustic": ["Ne complique pas tout. {body}.", "J’ai une idée, et pour une fois elle ne demande pas de miracle : {body}.", "{body}. Tu peux me remercier plus tard — ou pas."],
    "professorial": ["Écoute bien : {body}. C’est élémentaire, mais manifestement nécessaire.", "La méthode correcte consiste à {body}. Je vais éviter de te faire un cours entier.", "{body}. Prends des notes si tu veux; je ne répéterai pas trois fois."],
    "calculating": ["Je vois deux options. La plus avantageuse : {body}.", "{body}. Nous garderons l’autre possibilité en réserve.", "J’ai déjà pesé les risques : {body}. Le résultat devrait nous convenir."],
    "alert": ["Avant de bouger, vérifions le terrain. Ensuite, {body}.", "Je préfère qu’on {body}; mieux vaut prévoir l’imprévu.", "Un pas après l’autre : {body}. Je garde un œil sur les alentours."],
    "relaxed": ["On peut {body}, puis rentrer tranquille.", "Ça me va si on {body}. Pas la peine d’en faire une montagne.", "Allez, {body}; après, je coupe le son et je profite du calme."],
    "precise": ["La meilleure option est {body}. Je vérifierai les détails.", "{body}. Une exécution propre, sans gaspillage.", "Procédons dans cet ordre : {body}. C’est plus sûr."],
    "elegant": ["Je suggère que nous {body}. Avec un peu de méthode, tout s’accordera.", "{body}; la suite viendra avec naturel.", "Permets-moi de proposer {body}. Ce serait la façon la plus gracieuse d’avancer."],
    "bluntwarm": ["Écoute, on va {body}. Et après tu bois de l’eau, compris ?", "Pas de cinéma : {body}. Je garde un œil sur toi.", "On s’en occupe ensemble. {body}, puis on fait une vraie pause."],
    "resolute": ["On a un objectif. {body}. Je ne lâcherai pas au milieu.", "{body}. Si la première tentative échoue, nous corrigerons et recommencerons.", "Décidons maintenant : {body}. Je tiendrai parole."],
    "deadpan": ["J’ai une bonne idée pour une fois : {body}. Oui, c’est sérieux.", "{body}. L’explication tient en une phrase. Je peux la répéter sous forme de blague si besoin.", "Un plan solide : {body}. Le timing, comme toujours, est crucial."],
    "eccentric": ["J’ai vu un papillon près du camp… bref, {body}. C’est important aussi.", "{body}. Ça me rappelle une drôle d’histoire, mais je te la garde pour après.", "On fait ça, puis on regarde si les grenouilles du coin sont d’accord."],
    "coach": ["Allez, on se concentre : {body}. Pas d’excuse, mais pas de surmenage non plus.", "Objectif clair, effort régulier : {body}.", "On passe à l’action. {body}. Et on garde de l’énergie pour demain."],
}

REPLIES = {
    "gentle": ["Oui, ça me rassure. On le fait tranquillement, d’accord ?", "J’aime bien cette idée. Merci d’y avoir pensé avec autant d’attention.", "D’accord. Et si tu fatigues, on s’arrête; ce n’est pas une course."],
    "cold": ["Ça me convient. Tiens-toi au plan.", "Bien. Pas de temps perdu, alors.", "D’accord. Je corrigerai le tir si ça dérape."],
    "dry": ["Ça se tient. Pour une fois, on est d’accord.", "Va pour ça. Je surveillerai que personne n’en fasse trop.", "Bon, je reconnais que c’est raisonnable."],
    "formal": ["Je suis d’accord. Cette approche devrait nous éviter des efforts inutiles.", "Entendu. Je veillerai à ce que chacun puisse suivre le rythme.", "C’est une proposition judicieuse. Nous procéderons ainsi."],
    "solemn": ["Alors c’est décidé. Nous avancerons sans précipitation.", "Je m’en souviendrai. Une parole tenue compte davantage qu’un grand discours.", "D’accord. Que cette décision nous guide pour la suite."],
    "analytical": ["D’accord. On saura vite si les chiffres confirment l’idée.", "Ça réduit les inconnues. Je valide.", "Oui. Tant qu’on observe le résultat au lieu de supposer."],
    "practical": ["Ça marche. Je prépare ce qu’il faut.", "Parfait, je peux m’occuper de cette partie.", "Entendu. On fera le point une fois la tâche terminée."],
    "playful": ["Marché conclu ! Mais je choisis la récompense après.", "Ça me va — à condition qu’on puisse fêter la victoire ensuite.", "D’accord. Je garde une blague en réserve pour la pause."],
    "theatrical": ["Quelle entrée en matière ! J’accepte ce rôle avec panache.", "Parfait, le public n’attend que ça — même s’il n’y a que nous deux.", "J’en vois déjà le final. Ne gâchons pas le premier acte !"],
    "lyrical": ["Alors laissons les choses suivre leur cours; le chemin nous répondra.", "Je garderai cette idée comme on garde un vers qu’on aime.", "Oui. Le calme rend parfois les décisions plus claires."],
    "shy": ["Oui… je crois que ça pourrait marcher. Merci de m’avoir demandé.", "D’accord. Je vais essayer, même si je ne suis pas très sûre de moi.", "Ça me rassure de ne pas avoir à décider toute seule."],
    "bright": ["Oui ! Je m’y mets tout de suite — enfin, après avoir vérifié mon sac.", "Ça me plaît ! On va y arriver, j’en suis sûr·e !", "Parfait, j’avais justement besoin d’un petit défi."],
    "warm": ["Je suis là. On s’en occupe ensemble, comme toujours.", "Ça me va. Tu n’as pas à tout porter tout seul·e.", "D’accord; je te fais confiance pour la suite."],
    "expressive": ["Voilà ! C’est exactement le genre de plan qui peut marcher.", "J’aime quand on se comprend comme ça. On fonce ?", "Oui, et j’ajouterais juste un petit détail…"],
    "boisterous": ["Ha ! Enfin quelqu’un qui reconnaît un plan de génie !", "Évidemment que je suis partant. L’équipe Arataki ne recule devant rien !", "Ça marche ! Je m’occupe du moral. C’est une tâche essentielle."],
    "teasing": ["Je savais que tu finirais par écouter la voix de la raison.", "Très bien. Je ferai semblant d’être surpris·e si ça fonctionne.", "D’accord… mais je garde le droit de dire « je te l’avais dit »."],
    "caustic": ["Bien. Ne me fais pas regretter d’avoir accepté.", "Ça devrait suffire. Ne transforme pas ça en catastrophe.", "Pour une fois, ta décision est défendable."],
    "professorial": ["Exactement. Tu vois, quand on m’écoute, tout devient plus simple.", "Correct. Je t’expliquerai les détails si tu en as réellement besoin.", "Bien. Essaie de retenir la méthode cette fois."],
    "calculating": ["Je vois. Gardons tout de même une solution de repli.", "C’est acceptable. Je vérifierai que le résultat sert nos intérêts.", "D’accord. L’important sera de ne pas révéler toutes nos cartes."],
    "alert": ["Entendu. Je passe devant et je vérifie qu’on ne nous surprenne pas.", "Bien. Restons attentifs, même pour une tâche simple.", "D’accord. Au moindre signe étrange, on change de route."],
    "relaxed": ["Ça me va. Tant qu’on ne transforme pas ça en marathon.", "Oui, tranquille. Je connais un endroit sympa pour souffler après.", "Entendu. Pas besoin de se mettre la pression."],
    "precise": ["Très bien. Je m’assurerai que rien ne manque.", "D’accord; les détails feront la différence.", "C’est noté. Je contrôlerai le résultat."],
    "elegant": ["Fort bien. Nous avons trouvé un arrangement harmonieux.", "J’en conviens. Il ne reste qu’à l’exécuter avec soin.", "Une proposition bien tournée — et surtout, bien pensée."],
    "bluntwarm": ["Bon. Mais tu manges quelque chose après, c’est non négociable.", "Je valide. Et si ça devient pénible, tu me le dis.", "Ça marche. Je ne veux pas te voir t’épuiser pour ça."],
    "resolute": ["Alors avançons. Nous avons déjà surmonté pire.", "Je serai au rendez-vous. Compte sur moi.", "D’accord. Nous irons jusqu’au bout, sans nous disperser."],
    "deadpan": ["D’accord. Je promets de ne faire qu’une seule blague sur le sujet.", "C’est entendu. Le plan est sérieux; ma prochaine plaisanterie, moins.", "Oui. Je vais même essayer de garder mon sérieux."],
    "eccentric": ["Très bien. Je demanderai aussi son avis au petit lézard, au cas où.", "D’accord. J’ai comme l’impression que ça va bien se passer.", "Ça marche. Les choses bizarres finissent souvent par être utiles."],
    "coach": ["Bien. Respire, garde la posture, et on y va.", "Je savais que tu pouvais te décider. Maintenant, on tient le rythme.", "Parfait. Fais de ton mieux, pas besoin de te punir."],
}

BRIDGES = [
    "Et puis, ça me laisse du temps pour reparler de {hook} avec toi.",
    "Je garde juste en tête ce que tu m’as dit à propos de {hook}; le reste peut attendre.",
    "Au fait, ta façon de voir {hook} m’est revenue. On s’en reparle après ?",
    "Ça me fait penser à notre discussion sur {hook}… mais je m’égare, revenons au plan.",
    "Après ça, j’aimerais bien entendre la suite de ton histoire sur {hook}.",
    "Je note ça. Et je n’oublie pas ce que tu m’as raconté sur {hook}, promis.",
    "On pourra reprendre notre conversation sur {hook} pendant la pause.",
    "Voilà une chose de moins à porter. Pour {hook}, on prendra le temps qu’il faut.",
]

LAST_LINES = [
    "Alors c’est entendu. On commence maintenant ?",
    "Marché conclu. Je te laisse choisir le moment.",
    "C’est noté. Une étape, puis on avise.",
    "D’accord. Je garde ça en tête pour la prochaine fois.",
    "Ça me va. Et cette fois, on s’arrête quand l’objectif est atteint.",
    "Parfait. Je serai là si tu as besoin d’un coup de main.",
    "Entendu. On se retrouve après la prochaine étape.",
    "Ça marche. Maintenant, raconte-moi plutôt ce que tu en penses.",
]

MODE_ENDINGS = {
    "gentle": ["On y va doucement, à ton rythme.", "Une étape suffit pour aujourd’hui.", "Promis, on s’arrête avant que ça devienne une corvée.", "Je reste avec toi pour la suite.", "On fera de notre mieux, sans se presser."],
    "cold": ["C’est décidé. Reste concentré.", "Bien. Au travail.", "Alors fais-le; les résultats parleront.", "Pas d’hésitation une fois lancé.", "On verra ensuite si le plan tient."],
    "dry": ["Bon. Au moins, c’est réglé.", "Ça fera l’affaire. Pour l’instant.", "Marché conclu. Je nierai avoir eu cette idée.", "On s’y met avant que quelqu’un complique tout.", "Très bien. Pas besoin d’en faire une cérémonie."],
    "formal": ["Nous procéderons ainsi, avec méthode.", "C’est entendu. Nous ferons le point ensuite.", "Je vous fais confiance pour la suite.", "Avançons sans précipitation.", "La décision est prise; il ne reste qu’à agir."],
    "solemn": ["Alors avançons avec mesure.", "Je m’en souviendrai. Une parole tenue compte.", "Que cette décision nous guide.", "Le moment est venu d’agir.", "Nous irons jusqu’au bout."],
    "analytical": ["D’accord. On vérifiera les résultats.", "Une hypothèse à la fois; voyons ce que ça donne.", "Je garde les chiffres pour comparer après.", "Le test nous dira si c’était le bon choix.", "Parfait. On saura vite si ça fonctionne."],
    "practical": ["C’est noté. Je prépare le nécessaire.", "Entendu. On s’occupe du reste ensuite.", "Parfait, ça nous fera gagner du temps.", "Je m’en charge; avançons.", "On garde le plan simple et efficace."],
    "playful": ["Marché conclu ! Mais je choisis la récompense.", "Ça marche — on fêtera la victoire après !", "Parfait. J’ai déjà une blague pour la pause.", "On y va ? Promis, presque aucun piège.", "Entendu ! Essaie de suivre, cette fois."],
    "theatrical": ["Que le prochain acte commence !", "Rideau… et place à l’action !", "Le public attend un final mémorable.", "C’est ainsi que commence une grande histoire !", "À nous de jouer; ne gâchons pas l’entrée."],
    "lyrical": ["Laissons le chemin nous répondre.", "Je garderai cette idée comme un joli refrain.", "Le calme nous aidera à voir plus clair.", "Alors, suivons le vent sans le brusquer.", "Chaque voyage commence par un pas."],
    "shy": ["D’accord… merci de m’avoir demandé.", "Je vais essayer. On verra bien.", "Ça me rassure de ne pas décider seule.", "Alors… allons-y, doucement.", "Je crois que ça peut marcher."],
    "bright": ["Allez, on s’y met !", "Ça va le faire, j’en suis sûr·e !", "Parfait, un petit défi de plus !", "On avance, et on verra la suite après.", "C’est parti ! Je suis prêt·e."],
    "warm": ["On fera ça ensemble.", "Je suis là si tu as besoin.", "Tu n’as pas à tout porter seul·e.", "On s’en occupe, puis on souffle.", "Compte sur moi pour la suite."],
    "expressive": ["Voilà, c’est exactement ça !", "Je savais qu’on trouverait une idée.", "Bon, je m’emballe… mais on tient quelque chose !", "Ça mérite presque une célébration.", "On fonce; j’ai déjà trois plans de secours."],
    "boisterous": ["L’équipe Arataki entre en scène !", "Ha ! Impossible de perdre avec un plan pareil !", "En avant ! Et que ça brille !", "Défi accepté !", "Je prends le commandement — enfin, si vous insistez."],
    "teasing": ["Je te l’avais bien dit… mais je ne vais pas insister.", "Très bien. Je ferai semblant d’être surprise.", "À toi de jouer; je garde le droit de commenter.", "J’espère que tu apprécies mes conseils avisés.", "On verra si tu reconnais mon génie après coup."],
    "caustic": ["Ne me fais pas regretter d’avoir accepté.", "Bien. Ne transforme pas ça en catastrophe.", "Ça devrait suffire. Ne complique rien.", "Pour une fois, ta décision se défend.", "Agis d’abord; fanfaronne après."],
    "professorial": ["Voilà. Une décision correcte, enfin.", "Bien. Essaie de retenir la méthode.", "Je n’aurai pas besoin de répéter les consignes.", "Parfait. Tu vois comme c’est simple quand on écoute ?", "Cours terminé. À l’exercice, maintenant."],
    "calculating": ["Gardons une solution de repli.", "D’accord. Ne révélons pas toutes nos cartes.", "Voyons si le résultat sert nos intérêts.", "Je garde l’autre option sous la main.", "Le risque est acceptable. Pour le moment."],
    "alert": ["Je passe devant; reste attentif.", "Bien. Gardons un œil sur les alentours.", "Au moindre imprévu, on change de route.", "C’est entendu. Je vérifie le terrain.", "Avançons, mais ne baissons pas la garde."],
    "relaxed": ["Ça me va. Sans en faire un marathon.", "Allez, tranquille. On a le temps.", "On fait ça, puis on souffle.", "Pas la peine de se mettre la pression.", "Je connais un endroit sympa pour la pause."],
    "precise": ["Je vérifierai que rien ne manque.", "D’accord; les détails feront la différence.", "C’est noté. Je contrôlerai le résultat.", "Allons-y avec précision.", "Parfait. Pas d’approximation."],
    "elegant": ["Fort bien; exécutons cela avec soin.", "Nous avons trouvé un arrangement harmonieux.", "Il ne reste qu’à agir avec élégance.", "Une décision bien pensée mérite une belle exécution.", "Alors, procédons sans perdre notre allure."],
    "bluntwarm": ["Bon. Et tu manges quelque chose après, c’est non négociable.", "Je valide. Si ça devient pénible, tu me le dis.", "Pas question de t’épuiser pour ça.", "On s’en occupe, puis tu prends une vraie pause.", "Allez. Mais prends soin de toi aussi."],
    "resolute": ["Nous avons déjà surmonté pire.", "Je serai au rendez-vous.", "Allons jusqu’au bout, sans nous disperser.", "Compte sur moi. On ne lâche rien.", "En avant; nous trouverons la voie."],
    "deadpan": ["Une blague de moins, une rotation de plus.", "Je garde la chute pour la fin.", "Le plan est sérieux. Moi, c’est moins sûr.", "Timing parfait. Pour une fois, ce n’est pas une blague.", "Entendu. Je promets de ne faire qu’un jeu de mots."],
    "eccentric": ["Je demanderai quand même son avis au petit lézard.", "Les idées étranges sont parfois les bonnes.", "Ça me rappelle une grenouille… enfin, on y va !", "Je sens que quelque chose d’inattendu va arriver.", "Parfait. Les papillons approuvent."],
    "coach": ["Respire, garde le rythme, et on y va.", "Fais de ton mieux; pas besoin de te punir.", "Objectif clair, effort régulier.", "Je savais que tu pouvais te décider.", "On progresse sans se brûler."],
}


def stable_index(*parts: object, size: int) -> int:
    token = "|".join(str(part) for part in parts).encode("utf-8")
    return int(hashlib.sha256(token).hexdigest()[:12], 16) % size


def pick(items: list[str], *seed: object) -> str:
    return items[stable_index(*seed, size=len(items))]


def capitalize(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def theme_kind(section: str, title: str) -> str:
    text = f"{section} {title}".lower()
    if any(word in text for word in ("farm", "priorit", "ressource")):
        return "farm"
    if any(word in text for word in ("rotation", "synergie", "équipe")):
        return "team"
    if any(word in text for word in ("lore", "souvenir", "histoire", "détail")):
        return "lore"
    return "rest"


def profile_for(name: str, personalities: dict[str, dict[str, object]]) -> dict[str, object]:
    profile = personalities.get(key(name), {"description": "", "subjects": []})
    mode = choose_mode(name, profile)
    subjects = profile.get("subjects", [])
    if not subjects:
        subjects = ["les choses qu’on a vécues", "la suite de notre voyage", "ce qu’on veut accomplir"]
    return {"name": name, "mode": mode, "subjects": subjects}


def make_body(kind: str, person: dict[str, object], other: dict[str, object], seed: object) -> str:
    # Keep the conversation anchored in a recognizable character detail, not
    # an abstract “theme” repeated in quotation marks.
    name = key(str(person["name"]))
    stories = ANECDOTES.get(name, [])
    if stories:
        return pick(stories, seed, name, "anecdote")
    subjects = list(person.get("subjects", []))
    if subjects:
        subject = pick(subjects, seed, "subject")
        return pick([
            f"Je repensais à {subject} tout à l’heure; ça m’a rappelé pourquoi j’y tiens autant.",
            f"Tu sais, {subject}, ça me revient souvent quand je prends enfin le temps de souffler.",
            f"J’ai encore une pensée pour {subject}. C’est le genre de détail qu’on n’oublie pas.",
        ], seed, "subject-story")
    return pick([
        "J’ai repensé à une vieille expédition qui avait très mal commencé… et qu’on raconte encore en riant.",
        "Je me suis souvenu d’un soir où tout le monde était épuisé, mais personne ne voulait rentrer le premier.",
        "Ça me rappelle une petite victoire dont on n’avait même pas pensé à être fiers sur le moment.",
    ], seed, "fallback-story")


ANECDOTES = {
    "nilou": ["Après une répétition, j’ai appris les pas à une petite fille qui croyait ne pas savoir danser. Elle a fini par entraîner toute sa famille.", "La scène me fait toujours un peu peur juste avant le lever du rideau… puis j’entends le public respirer avec nous et tout va mieux.", "Un jour, j’ai raté un pas si joliment que le public a cru que c’était improvisé. Je n’ai pas osé les détromper."],
    "skirk": ["Mon maître m’a appris qu’une blessure ignorée devient une faiblesse. C’est une leçon que les gens comprennent souvent trop tard.", "J’ai déjà passé des jours sans prononcer un mot. Le silence révèle parfois plus qu’un interrogatoire.", "Il y a des combats qu’on gagne en refusant simplement de faire le mouvement attendu."],
    "klee": ["Dodoco a encore fini couvert de poussière rouge. Jean dit que ce n’est pas une preuve; moi, je trouve que ça ressemble beaucoup à une explosion.", "J’ai caché un dessin dans le bureau de Jean pour qu’elle le trouve après son rapport. Elle l’a gardé !", "Une fois, j’ai voulu offrir un poisson à Albedo. Il a posé tellement de questions que le poisson a eu le temps de repartir."],
    "albedo": ["J’ai passé une matinée à observer une réaction qui n’a duré qu’une seconde. Le résultat était utile; le petit-déjeuner, beaucoup moins.", "Klee m’a offert un dessin de Dodoco au milieu de mes notes. Je l’ai conservé près des expériences qui demandent de la patience.", "Il m’arrive de dessiner une chose avant de savoir pourquoi elle m’intéresse. C’est souvent là que commence une bonne question."],
    "amber": ["Baron Lapin a atterri dans un arbre pendant une patrouille. J’ai dû expliquer à Jean que la mission était réussie, mais que le lapin avait besoin d’un sauvetage.", "Je garde une carte de Mondstadt avec les meilleurs endroits pour faire une pause. C’est utile pour les nouveaux… et pour les chevaliers fatigués.", "Une fois, j’ai couru après un courrier jusque dans une rivière. La lettre était sèche; mes bottes ne s’en sont jamais remises."],
    "citlali": ["Ororon a prétendu qu’il n’avait pas faim, puis il a fini la moitié de mon assiette sans s’en rendre compte. Je l’ai laissé faire; il avait l’air si concentré.", "Je fais parfois semblant de dormir quand les jeunes veulent encore une histoire. Évidemment, je connais déjà la fin et je les corrige quand ils se trompent.", "Les nuits sont plus faciles quand on parle franchement. Même si, après, on prétend que la conversation n’a jamais eu lieu."],
    "mavuika": ["J’ai déjà promis de prendre une journée entière de repos. J’ai tenu jusqu’au déjeuner avant que quelqu’un vienne me demander un avis.", "On se souvient des grandes victoires; moi, je pense souvent aux gens qui ont tenu la ligne quand personne ne les regardait.", "Après un combat, j’aime entendre les histoires ordinaires du camp. Elles me rappellent exactement ce qu’on protège."],
    "tighnari": ["Collei m’a montré une plante qu’elle pensait malade. Elle avait simplement besoin d’ombre; depuis, elle vérifie toujours le soleil avant de s’inquiéter.", "J’ai demandé à Cyno d’arrêter un jeu de mots. Il en a inventé trois autres pour expliquer pourquoi il ne pouvait pas.", "Une excursion botanique est censée être calme. Puis quelqu’un touche une plante urticante et tout le monde se met à courir."],
    "cyno": ["J’ai expliqué une règle de Genius Invokation pendant si longtemps que le thé a refroidi. Tighnari a quand même joué la partie jusqu’au bout.", "Je prépare parfois mes blagues à l’avance. Le plus difficile reste de trouver quelqu’un qui ne connaisse pas déjà la chute.", "Un duel silencieux avec Tighnari est possible. Il suffit de ne pas annoncer qu’on compte les points."],
    "furina": ["J’ai répété une entrée dramatique devant un miroir; le miroir a résisté à mes critiques et n’a pas demandé de rappel.", "Les desserts ont meilleur goût après une représentation. Ou peut-être que je dis ça parce que je les mérite après les répétitions.", "J’ai fait semblant de ne pas être émue par les applaudissements. Le public a compris; c’est contrariant, ces gens attentifs."],
    "navia": ["J’ai apporté trop de macarons à une réunion. À la fin, même les gens venus pour se disputer comparaient leurs parfums préférés.", "Parfois, je sors prendre l’air quand l’orage arrive. Ça me rappelle que même les journées lourdes finissent par passer.", "J’ai appris à sourire pour rassurer les autres. Ça ne veut pas dire que je n’ai pas le droit d’être triste quand ils sont partis."],
    "kaeya": ["J’ai raconté une histoire différente à trois personnes dans la même soirée. Le lendemain, elles l’ont comparée; elles n’étaient d’accord sur aucune fin.", "Diluc prétend ne pas écouter mes plaisanteries. Il se souvient pourtant toujours de la pire.", "Je garde les secrets des autres avec soin. Les miens, c’est une autre affaire."],
    "diluc": ["Je n’aime pas les réunions tardives. Pourtant, j’en ai déjà prolongé une entière parce qu’un jeune chevalier n’osait pas rentrer seul.", "Kaeya a laissé une bouteille intacte sur le comptoir. Je ne sais toujours pas si c’était un cadeau ou une provocation.", "La nuit est plus calme quand on cesse d’attendre des remerciements."],
    "mualani": ["J’ai promis une sortie courte sur l’eau. Au retour, on avait trois histoires, deux coquillages et un ami de plus.", "Kachina avait peur de se lancer. On a compté jusqu’à trois; elle est partie à deux, et j’ai suivi en riant.", "Le meilleur moment d’une aventure, c’est souvent celui où tout le monde raconte sa version en même temps."],
    "kachina": ["J’ai gardé mon premier petit trophée même s’il est un peu abîmé. Il me rappelle que j’ai essayé avant de savoir si j’allais réussir.", "Mualani dit que je peux y aller à mon rythme. Je fais semblant de ne pas avoir besoin de l’entendre, mais si.", "Je me suis entraînée à annoncer mon nom très fort. La première fois, j’ai surtout surpris un saurien."],
    "alhaitham": ["Kaveh a laissé un plan sur la table. J’ai corrigé une mesure; il a corrigé ma correction. Le bâtiment sera peut-être prêt avant qu’on ait fini d’en discuter.", "J’ai emprunté un livre à la bibliothèque et l’ai rendu en avance. Le bibliothécaire a vérifié deux fois que c’était bien moi.", "Le silence n’est pas un malaise à remplir. Certaines personnes finissent par l’apprendre."],
    "kaveh": ["J’ai dessiné une entrée plus large pour laisser passer la lumière. Le client voulait gagner de la place; il a fini par me remercier pour le rayon de soleil.", "Alhaitham a dit qu’il aimait le plan. Il a ensuite signalé douze problèmes. Je choisis de retenir la première phrase.", "J’ai déjà dépensé trop pour un détail que personne ne remarquera. Moi, je le remarquerai à chaque fois."],
    "nahida": ["J’ai demandé à un enfant de me raconter son rêve. Il m’a donné une histoire entière, puis m’a demandé si je pouvais la garder en sécurité.", "Il y a des souvenirs qui font mal et qu’on ne peut pas effacer. On peut pourtant apprendre à ne plus les porter seul.", "Je découvre encore des choses très simples. C’est merveilleux de ne pas avoir fini d’apprendre."],
    "faruzan": ["J’ai corrigé une inscription ancienne et découvert que la prétendue faute était une plaisanterie d’un chercheur. Je lui reconnais un certain panache.", "On m’a demandé de résumer un siècle de travaux en quelques phrases. J’ai accepté; j’en suis maintenant à la quatrième page.", "J’aime quand les jeunes posent des questions. Même celles dont la réponse se trouve juste sous leur nez."],
    "furina": ["J’ai fait semblant de ne pas être émue par les applaudissements. Le public a compris; c’est contrariant, ces gens attentifs."],
    "ororon": ["J’ai parlé à un animal pendant toute une randonnée. Citlali dit qu’il ne m’a pas répondu; elle n’a juste pas entendu.", "Je peux rester immobile très longtemps. Les gens pensent que je médite; parfois, j’écoute simplement les insectes.", "J’ai oublié pourquoi j’étais entré dans une pièce. Puis j’ai vu une petite créature et j’ai oublié la pièce aussi."],
    "xilonen": ["J’ai passé une soirée entière à ajuster le son d’un morceau. À la fin, quelqu’un a dit que la première version était déjà parfaite.", "On m’a demandé de réparer un objet urgent. J’ai réparé aussi la chaise qui grinçait; ça m’agaçait depuis trois jours.", "Le meilleur plan reste celui qui laisse assez de temps pour écouter de la musique après."],
    "flins": ["La lumière du phare paraît plus stable quand on sait qui veille en bas. Je ne le dis pas souvent, mais je le sais.", "Illuga a essayé de prétendre qu’il n’était pas fatigué. Il a fini par s’endormir avant la fin de sa phrase.", "Il y a des nuits où le silence pèse. Alors on reste simplement à proximité, sans chercher à le remplir."],
    "illuga": ["Flins croit que personne ne remarque quand il prend le tour de garde le plus long. C’est faux; je lui laisse juste croire que son secret tient.", "J’ai déjà réparé une lanterne avec trois morceaux de ficelle et une idée douteuse. Elle éclaire toujours; je refuse de discuter de la méthode.", "Les Lightkeepers parlent peu quand ils ont peur. Ils restent, et c’est déjà une réponse."],
    "columbina": ["La lune était cachée ce soir-là, mais quelqu’un a continué à chanter. J’ai trouvé cela plus beau que n’importe quel ciel dégagé.", "Il y a des silences qui ressemblent à une berceuse. D’autres demandent qu’on reste éveillé près de quelqu’un.", "Je me demande si les étoiles se souviennent des voix qui leur parlent."],
    "arlecchino": ["Les enfants de la Maison ont préparé une fête sans rien demander. J’ai laissé la porte ouverte et prétendu ne pas avoir remarqué les décorations.", "On peut apprendre à quelqu’un à se défendre sans lui apprendre à devenir cruel. C’est une distinction qu’il faut répéter.", "Je préfère une promesse tenue à une excuse élégante."],
    "sandrone": ["J’ai démonté une pièce trois fois avant de comprendre que le bruit venait de la table. Je n’ai pas dit à l’assistant mécanique qu’il avait eu raison.", "Les gens appellent ça de la patience quand ils ne voient pas les heures passées à régler un mécanisme.", "Une machine n’a pas besoin de comprendre pourquoi on reste près d’elle. Elle le fait quand même."],
    "capitano": ["Un soldat m’a demandé si j’avais peur avant une bataille. Je lui ai répondu que le courage n’exige pas l’absence de peur.", "J’ai connu des victoires dont personne ne devrait se vanter. Le prix payé mérite qu’on se souvienne des noms.", "Je préfère marcher au même pas que mes compagnons plutôt que les attendre au sommet."],
    "zhongli": ["J’ai commandé du thé en oubliant mon portefeuille. Le propriétaire a accepté une histoire en échange; nous avons parlé jusqu’au coucher du soleil.", "Une vieille chanson m’est revenue en entendant la pluie. Je ne me souvenais pas de toutes les paroles, mais quelqu’un les connaissait encore.", "Les objets anciens ne sont pas précieux parce qu’ils sont vieux, mais parce que quelqu’un les a gardés."],
    "venti": ["J’ai joué une chanson triste dans une taverne. À la fin, quelqu’un m’a offert une tarte et m’a demandé une chanson plus joyeuse.", "Une fois, j’ai improvisé un couplet sur un client qui ronflait. Il a ri le plus fort de toute la salle.", "Le vent emporte les refrains, mais pas toujours les souvenirs qu’ils réveillent."],
    "raiden": ["J’ai goûté une pâtisserie en silence. On m’a demandé si elle était bonne; j’ai répondu par une seconde bouchée.", "J’ai longtemps cru qu’immobilité et paix étaient la même chose. J’apprends encore à écouter la différence.", "Le temps ne rend pas chaque perte plus légère. Il apprend parfois à lui faire une place."],
    "shogunraiden": ["J’ai reçu une boîte de desserts. Je n’ai pas compris pourquoi on en offrait autant, mais j’ai noté la recette.", "Une décision parfaitement ordonnée peut quand même blesser quelqu’un. Il faut savoir regarder au-delà de l’ordre.", "Je m’exerce à répondre sans consulter un protocole. L’exercice est plus difficile qu’il n’y paraît."],
    "lyney": ["Lynette a repéré mon tour avant le public. Elle n’a rien dit, mais elle a quand même applaudi au bon moment.", "J’ai fait disparaître une carte et retrouvé un reçu à sa place. Le tour était raté; le public a préféré l’histoire du reçu.", "Un spectacle réussi, c’est aussi savoir improviser quand le lapin refuse de sortir."],
    "lynette": ["Lyney a appelé ça une répétition calme. Il y avait trois accessoires en feu et un lapin très contrarié.", "Je préfère écouter la salle avant d’y entrer. On apprend beaucoup sur les gens quand ils croient que personne ne les observe.", "J’ai apprécié une fête. Je n’ai pas souri sur la photo; cela ne signifie pas que je ne me suis pas amusée."],
    "nefer": ["J’ai laissé quelqu’un parler jusqu’au bout avant de négocier. Il m’a donné la réponse qu’il cachait dans sa première phrase.", "Jahoda avait déjà classé les dossiers dans le bon ordre. J’ai prétendu que c’était mon idée pour voir si elle me corrigerait.", "Un bon accord ne fait pas de bruit. C’est souvent après coup qu’on comprend tout ce qu’il a évité."],
    "jahoda": ["Nefer m’a demandé une liste courte. J’en ai fait une deuxième, au cas où la première ne serait pas assez courte.", "Je garde toujours une collation de secours. Les gens prennent de meilleures décisions quand ils ont mangé.", "J’ai réglé un problème avant qu’on me le demande. On m’a remerciée; j’ai répondu que c’était plus rapide ainsi."],
    "zibai": ["J’ai regardé un artisan recommencer la même pièce jusqu’à ce qu’elle sonne juste. La patience a parfois un bruit très précis.", "Certaines traditions ont survécu parce que quelqu’un a pris le temps de les transmettre sans les figer.", "Je préfère les promesses discrètes. Elles laissent davantage de place aux actes."],
    "istaroth": ["J’ai entendu une voix revenir dans le vent longtemps après que la personne eut quitté le rivage.", "Les instants ne disparaissent pas tous de la même manière. Certains restent dans les gestes de ceux qui les ont aimés.", "J’aime écouter les horloges quand la ville dort. Elles n’ont pas toutes la même patience."],
    "ronova": ["Les mortels comptent les jours comme s’ils pouvaient les retenir. Pourtant, c’est leur façon de les remplir qui me touche.", "J’ai vu quelqu’un rire au milieu d’un adieu. Ce n’était pas de l’indifférence; c’était une manière de tenir debout.", "La fin d’une chose n’efface pas la chaleur qu’elle a laissée."],
    "odette": ["J’ai conservé un billet d’une représentation ancienne. L’écriture a pâli, mais je me souviens encore de la personne qui me l’a donné.", "Les gestes élégants sont parfois une façon de ne pas laisser voir qu’on tremble.", "Une mélodie entendue par hasard peut rendre à une journée son vrai visage."],
    "vodyanitsa": ["J’ai entendu la pluie frapper l’eau comme une chanson que personne n’avait encore écrite.", "Un enfant m’a demandé si les rivières se souviennent des pierres. J’ai répondu que certaines choses gardent leur trace autrement.", "Je préfère les histoires qui laissent une question ouverte; elles continuent de vivre après la dernière page."],
}


REACTIONS = {
    "gentle": ["Tu racontes ça comme si c’était rien… mais je trouve ça beau.", "Je comprends. Ça a dû compter plus que tu ne le laisses entendre.", "Je suis contente que tu me l’aies raconté. On peut rester un peu avec ce souvenir."],
    "cold": ["Tu aurais pu éviter la moitié des dégâts en réfléchissant avant d’agir.", "Et tu as laissé faire ? …Bien. C’était probablement la bonne décision.", "Je vois. La prochaine fois, fais-le exprès au lieu de prétendre que c’était prévu."],
    "dry": ["Je ne sais pas si je dois rire ou demander le rapport complet.", "C’est exactement le genre de problème qui n’arrive qu’à toi.", "Je vais faire comme si j’étais surpris. Ça te fera plaisir."],
    "formal": ["C’est une attention plus importante qu’elle n’en a l’air.", "Je comprends mieux pourquoi tu t’en souviens encore.", "Voilà une histoire que l’on devrait transmettre avec soin."],
    "solemn": ["Ceux qui étaient là ne l’oublieront pas.", "Tu as porté cette décision avec plus de courage que tu ne le crois.", "Il y a des souvenirs qui méritent qu’on leur laisse le silence."],
    "analytical": ["Le détail que tu viens de relever change toute l’interprétation.", "Je vois. Ce n’est pas le résultat qui t’a marqué, mais le geste.", "Il faudrait presque consigner cette anecdote. Elle explique beaucoup."],
    "practical": ["La prochaine fois, prends une veste. Je ne veux pas entendre la même histoire avec une pneumonie.", "Au moins, tu sais maintenant quoi ne pas refaire.", "Je peux t’aider à éviter que ça se reproduise. Sans jugement. Presque."],
    "playful": ["Pardon, je ris — mais j’aurais probablement fait pareil.", "Et personne n’a pensé à prévenir les témoins ? Quel manque de sens du spectacle !", "C’est officiellement mon histoire préférée de la journée."],
    "theatrical": ["Quel premier acte ! Et tu as gardé cette révélation pour maintenant ?", "J’aurais payé pour voir le public à ce moment-là.", "Il manque une musique dramatique à cette histoire. Je peux m’en charger."],
    "lyrical": ["On dirait un souvenir qui a trouvé sa place sans qu’on le force.", "Il y a une douceur étrange dans la façon dont tu t’en rappelles.", "Je crois que je comprends pourquoi cette image t’est restée."],
    "shy": ["Je… je ne sais pas quoi répondre. Mais je suis contente que tu me l’aies dit.", "Ça me fait sourire. Je ne pensais pas que ça m’émouvrait autant.", "Merci de me faire confiance avec ce souvenir."],
    "bright": ["Attends, tu ne m’avais jamais raconté la meilleure partie !", "C’est adorable… ou catastrophique. Peut-être les deux ?", "J’aurais voulu être là ! Enfin, peut-être pas pour les bottes dans la rivière."],
    "warm": ["Tu n’as pas eu à traverser ça tout seul, au moins.", "Je suis là si tu veux m’en raconter davantage. Ou si tu préfères changer de sujet.", "Ça me donne envie de veiller un peu plus sur toi, c’est tout."],
    "expressive": ["Oh, non, raconte la suite ! Tu ne peux pas t’arrêter là.", "Ça, c’est une vraie histoire. Je savais qu’il y avait quelque chose derrière ton air tranquille.", "Je ris, mais je te promets que je prends le reste au sérieux."],
    "boisterous": ["Ha ! Voilà une aventure digne d’être racontée au quartier général !", "Je relève le défi : la prochaine fois, je ferai pire. Enfin, mieux !", "L’équipe Arataki aurait réglé ça en cinq minutes. Sept, s’il fallait courir."],
    "teasing": ["Je ne vais pas me moquer. Pas beaucoup, en tout cas.", "Et après tu prétends que c’est moi qui attire les ennuis ?", "Je garde cette histoire pour la prochaine fois où tu me donneras des leçons."],
    "caustic": ["C’est touchant. Un peu imprudent, mais touchant.", "Je suppose que personne n’a été blessé. C’est déjà ça.", "Ne prends pas cet air-là. Je n’ai pas dit que c’était une mauvaise histoire."],
    "professorial": ["La leçon est claire; je vais m’abstenir de te la faire répéter.", "Voilà un exemple concret que mes élèves devraient étudier.", "Tu vois ? L’observation attentive finit toujours par payer."],
    "calculating": ["Intéressant. Je retiens qui a aidé et qui a disparu au mauvais moment.", "Ce genre de détail peut servir. Je n’oublierai pas.", "Tu as bien fait de ne pas tout dire dès le début."],
    "alert": ["Tu étais en sécurité, au moins ? C’est la première chose que je veux savoir.", "La prochaine fois, préviens quelqu’un avant de partir seul.", "Je retiens l’endroit. On vérifiera que tout va bien là-bas."],
    "relaxed": ["Ça arrive. On en rira mieux après un bon repas.", "Pas mal. J’aurais probablement laissé traîner la situation encore plus longtemps.", "J’aime bien les histoires qui finissent sans que personne ait besoin de faire un discours."],
    "precise": ["J’aurais choisi une autre méthode, mais le résultat est là.", "Le détail de la fin est important. Reprends depuis le début.", "Je note : ne jamais confier cette tâche à quelqu’un qui a faim."],
    "elegant": ["Une conclusion inattendue, mais fort bien amenée.", "Même le désordre peut avoir une certaine grâce, raconté ainsi.", "Tu as omis la partie où tout le monde t’a félicité, j’imagine."],
    "bluntwarm": ["La prochaine fois, tu m’appelles. Pas de débat.", "Je ris, mais tu me promets de faire attention, d’accord ?", "Ça va ? Vraiment ? Bon. Alors je peux rire maintenant."],
    "resolute": ["Tu as tenu bon. C’est ce que je retiens.", "Et tu es revenu. C’est déjà une victoire.", "La prochaine fois, on fera face à ça ensemble."],
    "deadpan": ["Je vais attendre trois secondes avant de faire une blague. Voilà.", "C’est une histoire très sérieuse. Je vais donc rire avec respect.", "Le timing est bon. La situation, beaucoup moins."],
    "eccentric": ["Je savais qu’il y aurait une créature dans cette histoire. Je ne savais pas laquelle.", "C’est curieux… j’ai rêvé d’une chose presque identique hier.", "Je crois que le hasard essaie de nous dire quelque chose. Ou alors j’ai faim."],
    "coach": ["Tu as fait de ton mieux avec ce que tu avais. C’est ça qui compte.", "Belle récupération. On apprend aussi dans les moments un peu ridicules.", "Respire. On en tire une leçon et on repart."],
}

TASK_REACTIONS = {
    "gentle": {"farm": ["Oui, faisons juste ce qui manque. On gardera un peu d’énergie pour demain.", "Ça me rassure de savoir qu’on s’arrêtera quand l’objectif sera atteint."], "team": ["D’accord… on essaie doucement, et on ajuste si quelqu’un se retrouve en difficulté.", "Je veux bien tester. Gardons une place pour protéger l’équipe aussi."]},
    "cold": {"farm": ["Enfin une priorité claire. On s’y tient.", "Bien. Pas de détour, et on arrête dès que le stock suffit."], "team": ["Essaie. Si le timing casse, on recommence jusqu’à ce qu’il soit propre.", "D’accord. Garde l’ultime pour la fenêtre utile, pas pour te rassurer."]},
    "dry": {"farm": ["Pour une fois, le plan tient en moins de trois étapes. Je valide.", "D’accord. Ça nous évitera de farmer une ressource dont on a déjà trop."], "team": ["On teste. Si ça rate, je dirai que c’était une expérience.", "Ça se tient. Ne transforme juste pas la rotation en dissertation."]},
    "formal": {"farm": ["C’est raisonnable. Nous pouvons nous limiter aux matériaux réellement nécessaires.", "Entendu. Une priorité à la fois nous évitera de disperser nos efforts."], "team": ["Je suis d’accord. Vérifions d’abord que chaque compétence est disponible au bon moment.", "Procédons ainsi; nous pourrons comparer les résultats après un essai complet."]},
    "solemn": {"farm": ["Alors consacrons cette journée à ce qui permettra vraiment d’avancer.", "C’est une bonne décision. Nous ne laisserons personne s’épuiser pour quelques ressources de plus."], "team": ["D’accord. Restons prêts à protéger les autres si le combat se prolonge.", "Une équipe tient par sa discipline. Essayons cette rotation ensemble."]},
    "analytical": {"farm": ["Les quantités restantes confirment ton choix. Le reste n’apporterait rien aujourd’hui.", "Bonne méthode : on compare le stock après la session avant de programmer la suivante."], "team": ["Testons-la sur un cycle complet. Il faut mesurer l’énergie, pas seulement les dégâts du premier tour.", "Je valide l’hypothèse. Changeons uniquement l’ordre des compétences pour isoler l’effet."]},
    "practical": {"farm": ["Parfait. Je vérifie les jours d’ouverture et je te prépare une liste courte.", "Ça marche. On prend le boss quand il est disponible et on garde les livres pour leur bon jour."], "team": ["Je m’occupe du soutien en premier. Tu gardes ton personnage actif pour la fenêtre de dégâts.", "D’accord. On garde le soin prêt et on évite de gaspiller l’ultime avant le boss."]},
    "playful": {"farm": ["Marché conclu ! Mais si on tombe encore sur la même fleur, je la nomme et je l’adopte.", "Une session courte ? J’accepte, à condition que la pause goûter soit dans le plan."], "team": ["Ça me va ! Si la rotation fonctionne, on prétendra que c’était prévu depuis le début.", "Essayons. Je compte les particules; toi, les ennemis qui regrettent d’être venus."]},
    "theatrical": {"farm": ["Une seule ressource, une seule scène — et un entracte avant le rappel !", "J’accepte ce programme. Le public n’a pas besoin de nous voir farmer jusqu’à l’aube."], "team": ["Alors plaçons l’ultime au troisième acte. Une entrée trop tôt gâcherait le final.", "J’adhère ! Mais si le boss survit, nous rejouons la scène avec plus de panache."]},
    "lyrical": {"farm": ["Oui. Une ressource à la fois; le chemin paraîtra moins long ainsi.", "C’est bien de laisser au lendemain ce qui peut attendre. La résine n’est pas une promesse à tenir."], "team": ["La rotation a un rythme plus doux ainsi. Gardons le temps d’écouter les particules revenir.", "D’accord. Que chacun trouve sa place avant que le dernier accord ne retentisse."]},
    "shy": {"farm": ["Oui… je préfère ça aussi. J’avais peur qu’on essaie de tout finir d’un coup.", "Ça me va. On pourra s’arrêter si tu en as assez, d’accord ?"], "team": ["Je veux bien essayer… mais tu me diras si je lance ma compétence trop tôt ?", "D’accord. Je vais surveiller l’énergie; c’est là que je me trompe parfois."]},
    "bright": {"farm": ["Oui ! On coche seulement ce qui manque, et après on se récompense !", "Ça me plaît. Une petite liste, une bonne session, et c’est déjà une victoire."], "team": ["On tente ! Si ça marche, je veux voir le résultat tout de suite.", "Bonne idée ! Je garde mon énergie et je rentre dans la rotation au bon moment."]},
    "warm": {"farm": ["On fait comme ça. Je préfère qu’on garde assez d’énergie pour profiter du reste de la journée.", "D’accord. Je reste avec toi jusqu’à ce que le stock soit bon, puis on souffle."], "team": ["Je suis d’accord. On garde le soin prêt; personne ne devrait avoir à tomber pour le test.", "Essayons ensemble. Si la rotation devient trop serrée, on la simplifie."]},
    "expressive": {"farm": ["Exactement ! Pas une minute de résine sur ce qu’on a déjà en réserve.", "Ça, c’est un plan qui me plaît : objectif clair, puis on célèbre la petite victoire."], "team": ["Oui ! La fenêtre de dégâts sera bien plus belle si on garde l’ultime pour la fin.", "J’aime cette idée. On teste une fois, et si ça coince je te propose trois variantes."]},
    "boisterous": {"farm": ["Une session ciblée ! Même l’équipe Arataki sait parfois s’arrêter avant la tombée de la nuit.", "Parfait. On va montrer à ces livres qui commande — mais pas plus longtemps que nécessaire."], "team": ["Ha ! Je prends l’ouverture, vous gardez les ultimes pour le grand final !", "Défi accepté. Si le boss tient encore debout, c’est qu’il n’a pas lu notre rotation."]},
    "teasing": {"farm": ["Étonnant : tu as vérifié ton inventaire avant de partir. Je vais devoir trouver une autre raison de te taquiner.", "Bon choix. Je ne dirai pas que je te l’avais conseillé… sauf si tu insistes."], "team": ["Joli timing. Je vais faire semblant de ne pas être impressionnée.", "On essaie. Et si ça marche, je te laisserai raconter que c’était ton idée."]},
    "caustic": {"farm": ["Oui. Farmer un surplus serait une façon particulièrement ennuyeuse de perdre ta résine.", "D’accord. Au moins, cette fois, le plan ne repose pas sur la chance."], "team": ["Ça peut marcher. Ne lance juste pas tout en même temps comme la dernière fois.", "Je valide. Garde une compétence disponible au lieu de vider toute la barre d’un coup."]},
    "professorial": {"farm": ["Voilà une décision enfin fondée sur les quantités, pas sur une impression.", "Correct. Les livres ouverts aujourd’hui passent avant les ressources accessibles demain."], "team": ["Tu as bien suivi l’ordre des compétences. Maintenant, surveille aussi la recharge.", "La théorie est correcte; l’exécution devra l’être autant. Recommençons une fois proprement."]},
    "calculating": {"farm": ["C’est l’option la plus avantageuse. Gardons le reste de la résine comme marge de manœuvre.", "D’accord. Nous ne dépensons rien tant que l’inventaire ne le justifie pas."], "team": ["Testons cette version, mais gardons l’ancienne comme solution de repli.", "L’ordre me convient. Si le combat s’étire, nous aurons encore une compétence en réserve."]},
    "alert": {"farm": ["Oui. Vérifions d’abord que le domaine est ouvert; je ne veux pas découvrir la porte fermée après le trajet.", "C’est noté. Je garde un œil sur le calendrier et sur le stock."], "team": ["D’accord. Je surveille la barre de vie pendant que tu testes la fenêtre de dégâts.", "On essaie, mais on garde une sortie sûre si le boss prépare une attaque." ]},
    "relaxed": {"farm": ["Ça me va. On fait ce qu’il faut, puis on profite du calme.", "Bonne idée. Pas besoin de transformer une session de jeu en deuxième travail."], "team": ["On teste sans se presser. Une rotation confortable, c’est celle qu’on arrive à refaire.", "D’accord. Si ça devient trop serré, on respire et on simplifie."]},
    "precise": {"farm": ["Les quantités sont vérifiées. On peut s’en tenir à cette session sans dépasser le besoin.", "Entendu. Je noterai le stock après la récolte pour éviter les doublons."], "team": ["La fenêtre est bonne. Il manque seulement une particule avant l’ultime; attendons-la.", "D’accord. Même ordre, mais avec le changement de personnage juste après la compétence."]},
    "elegant": {"farm": ["Une liste courte et une résine bien employée : voilà une journée fort bien ordonnée.", "J’approuve. Inutile de prolonger la session lorsque l’objectif est atteint."], "team": ["La transition sera plus harmonieuse si le soutien ouvre la danse.", "Essayons cet enchaînement; une rotation élégante doit aussi rester fiable."]},
    "bluntwarm": {"farm": ["Oui, et après tu manges quelque chose. Je ne négocie pas cette partie-là.", "On fait le nécessaire, pas davantage. Je ne veux pas te voir t’épuiser pour un jeu."], "team": ["D’accord, mais on garde un soin prêt. Je ne veux pas d’une rotation qui te laisse au tapis.", "Ça marche. Si ça ne passe pas, on change le plan au lieu de s’acharner."]},
    "resolute": {"farm": ["Alors nous irons jusqu’au bout de cette priorité, pas de toutes les priorités à la fois.", "C’est décidé. Nous ferons ce qui manque et nous reprendrons demain si nécessaire."], "team": ["D’accord. Chacun tient sa place et nous traverserons le combat ensemble.", "Essayons. Si la première tentative échoue, nous corrigerons sans abandonner."]},
    "deadpan": {"farm": ["Plan confirmé. La fleur peut dormir tranquille jusqu’à demain.", "Très bien. Une session courte; je garderai mes jeux de mots pour la pause."], "team": ["Je lance la compétence après le soutien. C’est le moment où le boss commence à regretter.", "D’accord. Si l’ultime rate sa cible, je prétendrai que c’était une démonstration d’humilité."]},
    "eccentric": {"farm": ["D’accord. Je demanderai aux petites bêtes du domaine de ne pas nous distraire cette fois.", "Oui ! Une ressource à la fois. Les papillons ont approuvé le calendrier."], "team": ["Essayons. J’ai l’impression que le boss n’a pas prévu cette combinaison.", "Ça me va. Si quelque chose d’étrange arrive, on dira que c’était dans le plan."]},
    "coach": {"farm": ["Bonne gestion. On garde un rythme régulier et on ne dépasse pas les besoins.", "Exactement. Une étape utile aujourd’hui vaut mieux qu’un marathon qui t’épuise."], "team": ["Bien. Respire entre les fenêtres et garde l’ultime pour le signal.", "On teste proprement. Si tu perds le rythme, on reprend depuis le début."]},
}


def conversational_line(person: dict[str, object], other: dict[str, object], kind: str, seed: object, beat: int) -> str:
    mode = str(person["mode"])
    name = str(person["name"])
    story = make_body(kind, person, other, seed)
    if beat == 0:
        if kind == "farm":
            options = [f"J’ai regardé ce qu’il nous manque. On pourrait s’occuper des aptitudes aujourd’hui, puis laisser le reste pour demain.", f"J’ai vérifié le sac avant qu’on parte. Bonne nouvelle : on n’a pas besoin de farmer ce qu’on a déjà en trop.", f"Je préférerais qu’on fasse une seule vraie session plutôt que de courir partout. Ça te va ?"]
        elif kind == "team":
            options = [f"J’ai revu notre rotation. Si on garde l’ultime pour la bonne fenêtre, l’équipe devrait respirer davantage.", f"On a perdu du temps entre les compétences. Tu veux qu’on essaie un ordre différent ?", f"Je crois qu’on peut rendre l’équipe plus fluide sans tout changer. On teste une seule chose ?"]
        elif kind == "lore":
            options = [story, f"Je pensais à quelque chose que tu m’as raconté… {story[0].lower() + story[1:]}", f"Cette histoire m’est revenue aujourd’hui. {story}"]
        else:
            options = [story, f"Je ne sais pas pourquoi, mais ça m’est revenu en tête : {story[0].lower() + story[1:]}", f"J’ai un souvenir un peu absurde à te raconter. {story}"]
        # Keep speaker voice noticeable without making every opener a catchphrase.
        if mode in {"theatrical", "boisterous", "expressive", "playful"}:
            options += [f"Attends, avant qu’on s’y mette : {story}"]
        return pick(options, seed, name, "opening")
    if beat == 1:
        if kind in {"farm", "team"}:
            options = TASK_REACTIONS.get(mode, TASK_REACTIONS["bright"])[kind]
            return pick(options, seed, name, other["name"], "task-reaction")
        options = REACTIONS.get(mode, REACTIONS["bright"])
        return pick(options, seed, name, other["name"], "reaction")
    if beat == 2:
        if kind == "farm":
            options = ["Parfait. On s’arrête dès que le stock est bon; je refuse de passer la soirée à ramasser la même fleur.", "Et après, pause. Les matériaux n’iront nulle part pendant qu’on mange.", "Je prends la liste, tu vérifies les quantités. Cette fois, pas de détour inutile."]
        elif kind == "team":
            options = ["On essaie sur un combat, pas sur un mannequin. Si l’énergie manque, on le verra tout de suite.", "Je veux garder une place pour le soin. Une rotation parfaite ne sert à rien si l’équipe tombe avant la fin.", "D’accord. Je change mon timing; toi, garde l’œil sur les particules."]
        else:
            options = ["Je crois que ce qui m’est resté, ce n’est même pas l’événement… c’est la façon dont les autres ont réagi.", "Bref… je ne pensais pas te raconter ça aujourd’hui. Mais ça fait du bien de le dire à voix haute.", "Je ris maintenant, mais sur le moment je ne savais vraiment pas quoi faire.", "Ce souvenir me revient surtout les jours où j’ai besoin de me rappeler que tout ne se passe pas toujours comme prévu."]
        if mode in {"deadpan", "teasing", "eccentric", "bright"}:
            options += ["Je précise que je n’admets aucune responsabilité dans la version racontée aux autres."]
        return pick(options, seed, name, "follow-up")
    options = REACTIONS.get(mode, REACTIONS["warm"])
    if kind in {"farm", "team"}:
        options = TASK_REACTIONS.get(mode, TASK_REACTIONS["warm"])[kind]
    return pick(options, seed, name, other["name"], "closing")


def opening(person: dict[str, object], other: dict[str, object], kind: str, seed: object) -> str:
    mode = person["mode"]
    body = make_body(kind, person, other, seed)
    if key(person["name"]) == "nilou":
        lines = ["Je viens de répéter un pas de danse et je me suis dit… on pourrait {body}. Ça nous laisserait le temps de souffler ensuite.", "J’ai envie qu’on garde un rythme doux aujourd’hui : {body}. Tu me suis ?", "Entre deux répétitions, j’ai pensé à toi. Si tu veux, on peut {body} ensemble."]
    elif key(person["name"]) == "skirk":
        lines = ["On ne progresse pas en hésitant. {body}.", "Une cible, une méthode : {body}. Pas de mouvements inutiles.", "Je ne te demanderai pas d’aller vite. Je te demande d’être précis : {body}."]
    else:
        lines = OPENERS.get(mode, OPENERS["bright"])
    return capitalize(pick(lines, seed, "open").format(body=body))


def answer(person: dict[str, object], other: dict[str, object], kind: str, seed: object) -> str:
    mode = person["mode"]
    if key(person["name"]) == "nilou":
        line = pick(["Oui, j’aime bien. On fera ça sans se presser, d’accord ?", "Ça me rassure de t’entendre le proposer. Je serai contente de t’aider.", "D’accord ! Et après, on se garde une vraie pause — une petite danse, peut-être ?"], seed, "nilou-reply")
    elif key(person["name"]) == "skirk":
        line = pick(["D’accord. Reste concentré.", "Ça me convient. Je regarderai si tu tiens le rythme.", "Bien. Si ça échoue, on corrige. On ne se cherche pas d’excuses."], seed, "skirk-reply")
    else:
        line = pick(REPLIES.get(mode, REPLIES["bright"]), seed, "reply")
    if kind == "lore" and stable_index(seed, "add-hook", size=3) == 0:
        hook = pick(person["subjects"], seed, "reply-hook")
        line = line.rstrip(" .!?…") + f". D’ailleurs, je repensais à « {hook} »."
    else:
        hook = pick(other["subjects"], seed, "other-subject")
        followups = {
            "gentle": [f"Et au sujet de « {hook} », tu m’en diras plus quand tu en auras envie.", f"Je n’oublie pas notre conversation sur « {hook} »; on la reprendra à ton rythme."],
            "cold": [f"Je garde aussi « {hook} » en tête. Ça pourrait compter.", f"On reparlera de « {hook} » quand ce sera utile."],
            "dry": [f"Au fait, j’attends toujours ton avis sur « {hook} ». Enfin, quand tu auras deux minutes.", f"On pourra reparler de « {hook} » après. Si tu y penses."],
            "analytical": [f"J’aimerais comparer ça avec ce qu’on sait de « {hook} ».", f"« {hook} » pourrait éclairer un autre point; gardons-le en tête."],
            "playful": [f"Et après, tu me racontes tout sur « {hook} » — sans sauter les détails !", f"Je garde une question sur « {hook} » pour tout à l’heure."],
            "theatrical": [f"Gardons le récit de « {hook} » pour le prochain acte !", f"« {hook} » mérite bien une scène à part, tu ne crois pas ?"],
            "shy": [f"Au fait… je voulais aussi te reparler de « {hook} », si ça ne te dérange pas.", f"Je n’ai pas oublié notre conversation sur « {hook} ». On pourra la reprendre après."],
            "formal": [f"J’aimerais également connaître ton point de vue au sujet de « {hook} ».", f"Nous pourrons revenir sur « {hook} » lorsque tu le souhaiteras."],
            "bright": [f"Et tu me raconteras tout sur « {hook} » après, hein ?", f"J’ai encore une question sur « {hook} », mais une chose à la fois !"],
        }
        line = line.rstrip(" .!?…") + ". " + pick(followups.get(mode, followups["bright"]), seed, "personal-followup")
    return capitalize(line)


def bridge(person: dict[str, object], other: dict[str, object], kind: str, seed: object) -> str:
    hook = pick(person["subjects"], seed, "bridge-subject")
    mode = person["mode"]
    line = pick(BRIDGES, seed, "bridge").format(hook=f"« {hook} »")
    if key(person["name"]) == "nilou":
        line = pick([f"Ça me rappelle un pas de danse que je travaille : {hook}. Je te le montrerai après.", f"Je garde une petite place dans ma tête pour {hook}. On en parle pendant la pause ?"], seed, "nilou-bridge")
    elif key(person["name"]) == "skirk":
        line = pick([f"Je n’oublie pas {hook}. Le reste est secondaire.", f"{hook} peut attendre. Finissons d’abord ce qui est devant nous."], seed, "skirk-bridge")
    elif kind == "rest" and mode in {"playful", "teasing", "boisterous", "theatrical"}:
        line = pick([f"Après ça, tu me dois une histoire sur {hook}.", f"Et ensuite, pause. Je veux tout savoir sur {hook} — sans esquiver !"], seed, "rest-bridge")
    return capitalize(line)


def last_line(person: dict[str, object], other: dict[str, object], kind: str, seed: object) -> str:
    mode = person["mode"]
    ending = pick(MODE_ENDINGS.get(mode, LAST_LINES), seed, "end")
    if key(person["name"]) == "nilou":
        ending = pick(["Alors c’est entendu. On y va doucement, et on s’arrête quand tu veux.", "Ça me ferait plaisir. On commence quand tu te sens prêt·e ?", "Parfait. Une petite étape, puis on se garde un moment pour souffler."], seed, "nilou-end")
    elif key(person["name"]) == "skirk":
        ending = pick(["C’est décidé. Reste concentré.", "Bien. Au travail.", "Alors fais-le. Je regarderai si tu tiens le rythme."], seed, "skirk-end")
    elif mode == "deadpan":
        ending = pick(["C’est décidé. Cette fois, je garde la chute pour plus tard.", "Entendu. La blague attendra la fin de la rotation.", "Marché conclu. J’espère que le timing sera meilleur que mon dernier jeu de mots."], seed, "cyno-end")
    hook = pick(other["subjects"], seed, "ending-subject")
    personal = pick([
        f"Et on reparlera de « {hook} » quand tu voudras.",
        f"Je n’ai pas oublié notre conversation au sujet de « {hook} ».",
        f"Après, on reprend notre discussion sur « {hook} ».",
        f"J’ai encore une question à propos de « {hook} », pour plus tard.",
    ], seed, "ending-aside")
    return ending.rstrip(" .!?…") + ". " + personal


def message(from_name: str, to_name: str, text: str) -> dict[str, str]:
    return {"from": from_name, "to": to_name, "text": text}


def rewrite_duo(interaction: dict[str, object], relation: dict[str, object], profiles: dict[str, dict[str, object]]) -> None:
    a_name, b_name = relation["characters"]
    a, b = profile_for(a_name, profiles), profile_for(b_name, profiles)
    kind = theme_kind("duo", interaction["theme"])
    seed = interaction["id"]
    messages = []
    for beat, (speaker, recipient) in enumerate(((a, b), (b, a), (a, b), (b, a))):
        text = conversational_line(speaker, recipient, kind, (seed, beat), beat)
        attempt = 0
        while text in [entry["text"] for entry in messages] and attempt < 10:
            attempt += 1
            text = conversational_line(speaker, recipient, kind, (seed, beat, attempt), beat)
        messages.append(message(str(speaker["name"]), str(recipient["name"]), text))
    interaction["messages"] = messages


def rewrite_group(conversation: dict[str, object], relation: dict[str, object], profiles: dict[str, dict[str, object]]) -> None:
    names = relation["characters"]
    people = [profile_for(name, profiles) for name in names]
    kind = theme_kind("group", conversation["theme"])
    seed = conversation["id"]
    # 5–7 turns: every member gets a natural opening to respond, then one or two voices return.
    turns = max(5, min(7, len(names) + 1 + stable_index(seed, "extra-turn", size=2)))
    order = list(range(len(names)))
    shift = stable_index(seed, "speaker-order", size=len(names))
    order = order[shift:] + order[:shift]
    if turns > len(names):
        order += [stable_index(seed, "return-voice", size=len(names))]
        if turns > len(order):
            order += [order[1 % len(order)]]
    lines = []
    for turn in range(turns):
        idx = order[turn]
        recipient_idx = order[(turn + 1) % len(order)]
        beat = turn % 4
        text = conversational_line(people[idx], people[recipient_idx], kind, (seed, turn), beat)
        attempt = 0
        while text in [entry["text"] for entry in lines] and attempt < 10:
            attempt += 1
            text = conversational_line(people[idx], people[recipient_idx], kind, (seed, turn, attempt), beat)
        lines.append(message(names[idx], names[recipient_idx], text))
    conversation["messages"] = lines


def main() -> None:
    personalities = load_personalities()
    data = json.loads(DATA.read_text(encoding="utf-8"))
    for relation in data["duos"]:
        for interaction in relation["interactions"]:
            rewrite_duo(interaction, relation, personalities)
    for section in ("trios", "squads", "groupsOfFive"):
        for relation in data[section]:
            for conversation in relation["conversations"]:
                rewrite_group(conversation, relation, personalities)

    duo_interactions = [item for relation in data["duos"] for item in relation["interactions"]]
    group_conversations = [item for section in ("trios", "squads", "groupsOfFive") for relation in data[section] for item in relation["conversations"]]
    data["editorialNote"] = (
        "Dialogues originaux en français, écrits comme des échanges suivis : chaque réponse réagit à ce qui vient d’être dit, "
        "avec des anecdotes et des voix inspirées des personnalités décrites dans Personnalites-personnages-Genshin.md. "
        "Ce ne sont pas des citations du jeu. Les thèmes servent uniquement à choisir la situation; ils ne sont pas récités dans les répliques."
    )
    data["counts"].update({
        "duoPairs": len(data["duos"]),
        "duoInteractions": len(duo_interactions),
        "duoLongInteractions": sum(len(item["messages"]) > 2 for item in duo_interactions),
        "duoLines": sum(len(item["messages"]) for item in duo_interactions),
        "trios": len(data["trios"]),
        "squadsOfFour": len(data["squads"]),
        "groupsOfFive": len(data["groupsOfFive"]),
        "conversationsPerGroup": 4,
        "groupConversations": len(group_conversations),
        "groupLines": sum(len(item["messages"]) for item in group_conversations),
    })
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    all_lines = [message["text"] for group in duo_interactions + group_conversations for message in group["messages"]]
    print(f"Écrit {len(all_lines)} répliques · {len(set(all_lines))} formulations uniques · {len(personalities)} profils de voix")


if __name__ == "__main__":
    main()
