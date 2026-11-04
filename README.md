# ASTRALIS · v75

Atelier local de collection et de composition d’équipes pour **Honkai: Star Rail**, **Genshin Impact** et **Wuthering Waves**.

## Utiliser Astralis comme une application

### Windows

Double-clique sur `Installer et lancer Astralis.bat`. Le programme installe Python si nécessaire, démarre le moteur local, puis ouvre Astralis dans une fenêtre d’application sans barre d’adresse. Un raccourci **Astralis** est créé sur le Bureau. Microsoft Edge ou Google Chrome est requis pour afficher l’interface; les données personnelles restent sur ce PC.

### iPhone

Pour utiliser Astralis sans laisser le PC allumé, il faut publier le moteur sur un hébergement gratuit. Le dépôt contient `render.yaml` pour créer le service Render et demande un mot de passe d’au moins 16 caractères. Une fois l’adresse HTTPS créée, ouvre-la dans Safari, touche **Partager → Sur l’écran d’accueil**, puis lance Astralis depuis sa nouvelle icône : l’app s’ouvre en plein écran, comme une application installée. iOS ne permet pas d’installer directement un `.exe` Windows; une app iPhone native signée exigerait une compilation Xcode sur Mac.

Les collections et réglages restent enregistrés localement dans l’application de chaque appareil; ils ne se synchronisent pas automatiquement entre PC et iPhone. L’hébergement gratuit Render peut se mettre en veille après 15 minutes sans visite, puis prendre un moment à redémarrer. HoYoLAB reste connecté en mémoire uniquement et peut demander une reconnexion après un redémarrage. Ne publie jamais `assets/user` ni un cookie HoYoLAB.


## Mise à jour v74 · Genshin

### 10 améliorations majeures

1. Le tableau de bord affiche un agenda compact issu du calendrier GenshinFlex, avec événements, bannières personnages et bannières d’armes.
2. L’onglet Événements reprend les données structurées du calendrier, actualisées chaque heure et datées selon la source.
3. Le Théâtre récupère et affiche les boss annoncés par acte, en plus des personnages et éléments de la saison.
4. Les éléments d’endgame utilisent maintenant leurs icônes dans les pastilles.
5. Le simulateur de vœux permet de choisir C0, C1, C2, C0R1 ou C2R1 et trace une courbe de probabilité cumulée.
6. Le simulateur affiche aussi une estimation de médiane et l’intervalle P10–P90; le modèle reste une approximation communautaire.
7. L’export PNG d’équipe et de build convertit temporairement les images autorisées via le serveur local afin d’éviter les blocages CORS.
8. Les cartes PNG de build conservent un cadrage sans étirement et montrent l’image distincte de chaque pièce d’artéfact.
9. Les fiches Genshin affichent toutes les entrées du catalogue sans bouton « afficher plus »; cliquer sur le splash ouvre son aperçu grand format.
10. Une tier list personnelle modifiable et sauvegardée localement est ajoutée.

### 20 améliorations d’usage et de présentation

1. Le formulaire de planification de farm utilise une grille qui garde ses champs lisibles.
2. Le panneau d’EXP partage correctement l’espace entre le résumé et les stocks de livres.
3. Les portraits de farm du tableau de bord ont une taille plafonnée.
4. Les images d’événements sont limitées à une vignette compacte.
5. Les images des personnages suivis ne recouvrent plus le contenu du tableau de bord.
6. Les pièces d’artéfact reçoivent une icône distincte fleur/plume/sablier/coupe/couronne.
7. L’export de build utilise ces cinq icônes de pièces.
8. Les images de talents Genshin pointent vers les icônes NA/compétence/déchaînement correspondantes.
9. Les constellations Genshin disposent de leurs icônes C1–C6.
10. Les icônes de talents gardent le cadrage « contain » pour ne pas être coupées.
11. Les aperçus splash peuvent s’ouvrir dans une visionneuse.
12. Les cartes Calc Sheets proposent une saisie assistée des personnages.
13. Les armes Calc Sheets disposent d’une recherche par nom.
14. Les sets Calc Sheets disposent d’une recherche par nom.
15. La cellule Calc affiche l’illustration de l’objet choisi.
16. L’export d’équipe attend le décodage des images avant la capture.
17. Les images externes d’export sont mises en cache localement une journée.
18. Le serveur limite les domaines images acceptés et la taille de chaque fichier.
19. Le nombre de réglages affiché dans la navigation est calculé depuis la configuration réelle.
20. La version des ressources statiques est incrémentée pour forcer le rafraîchissement du navigateur.

Les ressources communautaires Skowt sont accessibles par son site; Skowt n’expose pas d’API publique documentée permettant une recherche d’images intégrée automatisée. Les images personnalisées restent importables dans les zones prévues par Astralis.

## Dans l’application

- Trois univers séparés avec une identité colorée adaptée au jeu, et une navigation utilisable sur mobile.
- Bibliothèques de personnages, d’armes/cônes et de sets/reliques/échos avec recherche, filtres, tri, rareté, mode liste et chargement progressif des cartes pour limiter les images simultanées.
- Cartes à illustrations dynamiques : splash arts HSR et Genshin, rendus détourés Wuwa en haute résolution, mise en mouvement légère, kits et talents, astuces personnelles et accès aux showcases.
- Favoris et suivi des éléments possédés, enregistrés séparément pour chaque jeu.
- Planificateur d’équipe à quatre personnages : arme et set par personnage, splash arts plein cadre, compétences avec icônes et portrait, ajout sans saut de page, répétitions `N3` et enchaînement `N > E > Q`. Les attaques chargées/plongeantes et `hE` apparaissent selon le kit documenté du personnage.
- Fiche d’équipe avec notes de build, ordre/timing libre, meilleur résultat de dégâts et capture compressée conservée localement.
- Carnet personnel relié aux personnages, notes épinglées et classées, tâches avec échéance et priorité, 7 modèles de plan (28 étapes), vues « aujourd’hui / retard / terminé », raccourci `/` et sauvegarde JSON. La page objectifs répertorie 51 outils personnels dans l’application.
- Liens rapides vers les vidéos de gameplay et d’animation de pulls, les illustrations et les discussions de builds.
- Tableau de bord par univers : favoris récents, équipes, objectifs à échéance, notes et conseils; il n’attend pas le chargement des catalogues lorsqu’aucun favori n’est enregistré.
- Personnalisation enregistrée localement : 191 réglages en groupes détaillés, dont 51 nouveaux contrôles visuels et de visibilité, six palettes, nom/logo de l’application, Inter/Circular Std, largeur, colonnes, formes, affichage, mouvements, audio et cache. Une piste audio personnelle peut être importée (32 Mo maximum).
- Optimiseurs par jeu : Fribbels (HSR), Genshin Optimizer et gcsim (Genshin), WutheringTools et Tacet Lab (Wuwa). Fribbels ne peut pas recevoir l’inventaire directement depuis Astralis : le JSON HoYoLAB est conservé ici, puis copié pour être collé une fois dans son import.
- Le profil HSR fourni est intégré par défaut dans le stockage local et visible dans l’aperçu du profil. Les personnages de ce profil absents du catalogue communautaire sont ajoutés au catalogue HSR.
- Équipes aléatoires quotidiennes par jeu et roue visuelle, plus un plan de farm du jour. Les icônes de farm sont des repères de catégorie; les disponibilités détaillées HSR/Wuwa sont à vérifier dans le jeu.
- Galerie d’images personnelle dans chaque fiche personnage; les images et la musique sont conservées localement. Une sauvegarde portable peut contenir profil, galerie, musique, préférences, équipes, favoris, tâches et notes (120 Mo maximum).
- Données de catalogues mises en cache dans IndexedDB; affichage du cache immédiatement et revalidation discrète selon le réglage (1 à 30 jours). Chaque réponse JSON est plafonnée à 16 Mo et rejetée avant d’être entièrement téléchargée si elle dépasse cette limite.
- Page Skowt qui ouvre les ressources officielles à la demande. Skowt ne fournit pas d’API publique documentée, Astralis ne copie donc pas ses archives.

## Structure

- `index.html` : point d’entrée.
- `styles.css` : thème, cartes, fiches, responsive et atelier d’équipe.
- `design.css` : couche visuelle « Aurore » (barre latérale, barre du haut, bandeau, tableau de bord, cartes), chargée après `styles.css`.
- `src/icons.js` : jeu d’icônes SVG intégré (plus de glyphes dépendant des polices).
- `src/app.js` : interface et interactions.
- `src/data.js` : normalisation des trois bases, détails, compétences et stratégies d’images de secours.
- `src/store.js` : favoris, collection, équipes, notes et sauvegardes locales.
- `server.py` : serveur local et pont de données sans dépendance supplémentaire.

L’interface utilise Inter en fichier WOFF2 local (48 Ko), avec Circular Std puis les polices système en secours. Les illustrations sont chargées en différé, avec décodage asynchrone, et les catalogues affichent 24 cartes par page.

Préférences, favoris, équipes, notes et captures sont conservés dans le stockage local du navigateur et IndexedDB. Exporte une sauvegarde avant d’effacer les données de navigation. Les bases sont fournies par des projets communautaires externes et leur couverture dépend de leur mise à jour. Les portraits transparents Wuwa viennent du dépôt communautaire d’assets Encore; les cartes les chargent à la demande. Les bases de personnages jouables évoluent selon la publication des sources. Les entrées de préversion annoncées (dont Mitya et le catalyseur Starsealed Edict) sont signalées séparément; valeurs, stats et matériaux non publiés ne sont pas inventés.

## Outils Genshin ajoutés dans Astralis v67

- **Calc Sheets** : feuille fixe de comparaison par équipe avec quatre personnages, DPS perso, part de l’équipe, arme, set, rotation, temps, DPR et DPS. Les parts du DPS se calculent automatiquement; notes, photo, couleurs et export CSV sont conservés.
- **Plan de farm** : coûts exacts calculés pour les six ascensions jusqu’au niveau 90 et trois talents jusqu’au niveau 10, avec les icônes des matériaux et un suivi local par matériau. Les coûts proviennent des tables communautaires GenshinDB fusionnées aux assets locaux.
- **Endgame** : récupère la rotation de l’Abîme (étages 9–12, chambres, moitiés, ennemis et bénédiction) et la saison actuelle du Théâtre depuis GenshinFlex. La réponse est mise en cache 15 minutes; tes équipes et notes restent locales. Cette source communautaire peut être temporairement indisponible.
- La roue Genshin tire dans les personnages marqués possédés, et revient à l’ensemble du catalogue si aucun n’est marqué.
- Nouvel onglet **Mes builds** : plusieurs fiches par personnage, arme, set, constellation, huit stats, cinq artéfacts avec une stat principale et quatre sous-stats, notes, couleur et image de fond personnelle. Les fiches se sauvegardent localement et s’exportent en HTML imprimable.
- Les playlists audio de plusieurs fichiers passent les pistes en aléatoire et sont incluses dans la sauvegarde portable avec les feuilles et le suivi de farm.

Pour garder l’ancienne version intacte, cette copie de développement utilise `http://127.0.0.1:8766/`. Le lanceur de cette archive ne touche qu’au serveur du port 8766.


La rotation d’endgame est fournie par une source communautaire (GenshinFlex), et non par HoYoverse. Les fiches Akasha/Celestia avec classements de compte et le journal de différences automatique des données ne sont pas intégrés dans cette version.

- Les icônes Genshin passent en priorité par les fichiers d’assets directs Enka/Yatta; le chargement remplace les initiales par un glyphe neutre si une source reste indisponible.
- Le menu latéral possède son propre défilement vertical au pavé tactile. Les musiques existantes n’ont pas été modifiées.

- **Profil Akasha / vitrine** : champ UID Genshin avec chargement explicite du showcase public via Enka, cache serveur local, aperçu des personnages et sauvegarde portable. Enka fournit la vitrine, pas les classements Akasha/Celestia.


### Nouveautés de cette révision

- **Fiches de build illustrées** : en-tête splash plus ample, visuels distincts pour les cinq pièces d’artéfact, icônes et descriptions de talents, constellations, stats, notes, couleur personnalisée et export HTML imprimable.
- **Thèmes Genshin** : thème manuel par personnage, personnage du jour d’anniversaire ou rotation aléatoire quotidienne; splash en arrière-plan discret et accent lié à l’élément.
- **Prochains vœux** : compteurs de version et de phases, portraits quand la base les connaît, vedettes et raretés, repères distincts pour les informations d’armes/4★ pas encore confirmées.
- **Mitya et Starsealed Edict** sont ajoutés aux catalogues comme contenus annoncés. Les valeurs de kit, matériaux, statistiques et passif encore absents sont explicitement indiqués comme en attente. Le visuel de l’arme est un repère provisoire, pas un asset officiel.
- **Icône du site** importable depuis Personnaliser; l’image est réduite avant stockage.
- **Plan de farm** : plusieurs personnages suivis ensemble, inventaire de matériaux partagé, besoins restants, calendrier de sessions et aperçu des prochaines sessions sur l’accueil.
- **Profils Enka** : import des personnages exposés puis création d’une fiche de build à partir des armes, reliques et stats présentes dans la vitrine publique.
- **Vœux & objectifs** : pity personnage/arme, garantie, historique quotidien de primogemmes et de vœux, objectif de constellation/arme et estimation probabiliste locale.
- **Carnage** figure dans l’espace Endgame; la rotation et les boss restent indiqués en attente tant que la source publique connectée ne les fournit pas.


## Atelier Genshin · nouveautés v68

- Splash arts de builds en grand format paysage, avec portrait, éléments, constellation C0–C6, statistiques, talents, arme et les cinq pièces d’artéfact sur une seule carte PNG.
- Sélection d’un ensemble dans chaque build : les images de fleur, plume, sablier, coupe et couronne viennent automatiquement des données du set; chaque pièce conserve ses statistiques et peut recevoir une image personnelle.
- Export de fiche en PNG ou HTML; export PNG d’une équipe Genshin avec sa composition, les armes, sets, compétences, rotation et notes.
- Équipes à quatre colonnes sur ordinateur, illustrations agrandies et zoomables, équipement et icônes de compétences par personnage.
- Tableau de bord avec compte à rebours au format `00J : 00h : 00m : 00s`, prochain reset du Théâtre, boss d’étage 12, boss du Carnage chtonien, bannières et armes annoncées, et solde de primogemmes sauvegardé.
- Endgame alimenté par GenshinFlex : Abîme, bénédiction, ennemis/étage, Théâtre et Carnage chtonien avec boss, éléments et avantage de combat lorsqu’ils sont publiés. Les champs absents de la source restent signalés comme en attente.
- Planification multi-semaines du farm : personnage et catégorie par session, tags personnalisés, XP, Mora, matériaux et boss hebdomadaires. Livres d’aptitude placés sur leurs jours (dimanche ouvert; première semaine du patch ouverte) et inventaire soustrait des besoins.
- XP de personnage avec conversion exacte des livres bleus (5 000 EXP) et violets (20 000 EXP, soit 4 bleus), besoins consolidés et fiches matériaux exportables.
- Fiches des personnages suivis dans l’accueil avec splash, ressources, quantités restantes et export PNG.
- Calendrier Genshin dédié aux mises à jour, bannières de personnages/armes, événements et rotations; les dates non annoncées sont marquées en attente.
- Lore Genshin par personnage, avec région, affiliation, récits issus des fiches publiques et illustration.
- Probabilités de vœux affichées en barres comparatives C0, C1, C2, C0R1 et C2R1; la simulation est stable à entrées identiques et le modèle est décrit dans l’interface.
- Primogemmes actuelles, pity, garanties, Radiance, pity d’arme et gains quotidiens conservés localement.

## 51 nouveaux réglages visuels

- **10 palettes manuelles** : fond, surface, surface secondaire, texte, texte secondaire, bordures, accent secondaire, or, réussite et alerte.
- **10 réglages de proportions** : largeur du contenu, hauteur des en-têtes, zoom et point focal du splash, espacement des cartes, marges des panneaux, taille des icônes de compétences et d’artéfacts, colonnes des équipes et arrondis.
- **10 choix de présentation** : composition du tableau de bord, cartes de personnages, disposition des équipes, style de build, style de bannière, menu latéral, ambiance de fond, cadre d’image, forme d’icône et mouvement.
- **21 interrupteurs de visibilité** : agenda, fiches de farm, faits de lore, descriptions de talents, images d’artéfacts, équipement d’équipe, codes de rotation, armes de bannière, boss, casting du Théâtre, compteurs, solde de primogemmes, conversion EXP, tags du planning, planning automatique, comparaison de probabilités, constellations, signature des exports, galerie, ambiance d’anniversaire et splash en fond.

## 30 fonctions pratiques à découvrir

1. Favoris séparés par univers.
2. Indicateur « possédé » pour personnages et équipement.
3. Recherche dans les catalogues.
4. Filtres d’élément et de rareté.
5. Tri alphabétique et par catégories.
6. Affichage en grille ou liste.
7. Chargement progressif des cartes.
8. Détails des talents et valeurs de compétences.
9. Icônes des talents en fiche et dans les équipes.
10. Composition d’équipe à quatre emplacements.
11. Réutilisation d’équipes sauvegardées.
12. Sélection rapide d’un personnage, d’une arme et d’un set.
13. Rotation de compétences ordonnée.
14. Compteur d’attaques répétées `N3`.
15. Portrait de personnage dans chaque action de rotation.
16. Notes de rotation par équipe.
17. Enregistrement de DPS, DPR et durée.
18. Capture d’écran liée à une équipe.
19. Résumé des buffs cumulés et des réductions de résistance reconnues.
20. Bibliothèque de builds multiples par personnage.
21. Statistiques principales et secondaires par pièce.
22. Images personnelles par pièce d’artéfact.
23. Galerie personnelle dans chaque fiche.
24. Import et lecture d’une playlist personnelle.
25. Roue d’équipe quotidienne par jeu.
26. Favoris utilisés pour la roue quand une collection possédée existe.
27. Tâches, échéances et priorités.
28. Carnet avec notes épinglées et filtres.
29. Import du profil public Genshin par UID.
30. Export/import portable des données personnelles.

## Sources et limites des données

L’endgame est récupéré de GenshinFlex à l’ouverture du tableau de bord puis mis en cache localement pendant 15 minutes. Les infos de bannière et d’événements suivent les publications officielles disponibles au moment de l’intégration; les compositions 4★/armes non confirmées restent clairement marquées. Les probabilités sont des simulations, pas une garantie de résultat. Les fiches de matériaux s’appuient sur les données du catalogue et du kit accessible; les sorties futures ou détails bêta non publiés ne sont pas inventés.


## Mise à jour v75

- Le splash art s’ouvre maintenant depuis un bouton dans la fiche détaillée du personnage; cliquer sur la carte ouvre seulement sa fiche.
- Les cartes personnage conservent la même composition que les aperçus d’équipe : illustration, nom et emblème d’élément du jeu.
- L’onglet Profil utilise l’UID saisi pour préparer deux cartes côte à côte : Akasha System et Celestia.cv. Chaque carte mène au profil public de cet UID. Ces services bloquent l’intégration en iframe tierce, donc le profil complet s’ouvre sur leur site.
- Le nouveau lanceur Windows installe Python depuis python.org s’il n’est pas présent. Aucun paquet Python supplémentaire n’est requis.
