# Mode Histoire — direction et choses à faire

Statut : **prototype jouable avec génération, progression et deux armes**, accessible par le bouton Histoire.
Ce document rassemble les idées retenues, l'architecture et les étapes restantes.
Les cases cochées décrivent ce qui est présent ; les autres restent à réaliser.

Les développements décrits ici concernent uniquement le mode Histoire. Le mode
Infini reste dans son état actuel ; sa nouvelle direction sera définie séparément.

## Étape 1 — historique du premier prototype

- [x] Vue de côté avec saut et dash, confirmée par le joueur.
- [x] Courte prise de possession dans le cockpit, avec l'apparence sélectionnée.
- [x] Deux salles fixes reliées par des portes : cockpit et coursive.
- [x] Caméra horizontale, plateformes et collisions ; sprite du joueur en 100 × 100.
- [x] Marche en six images, pose de saut et pose de dash pour les quatre astronautes ; animations arrêtées pendant la pause.
- [x] Pistolet à rayons à ramasser, tir horizontal, son chiptune et impacts.
- [x] Premier alien violet/noir : approche, avertissement, bond offensif et défaite.
- [x] Vie, protection temporaire après un dégât, jauge de dash et objectifs contextuels.
- [x] Clavier et Xbox, commandes personnalisables par mode, pause et redémarrage.
- [x] Conservation de l'arme et de l'état de l'ennemi lors des allers-retours.
- [x] Fin du prototype au sas de la coursive après la défaite de l'alien.
- [ ] Retour du joueur sur la sensation de déplacement, la visée et le combat à la manette physique.

Cette première étape comportait deux salles et un ennemi. Elle est conservée ici
comme historique ; l'étape 2 ci-dessous décrit la version actuelle. Le sas reste
une fin de prototype et ne représente pas encore la sortie finale du vaisseau.
Les décors, poses et effets sont une première base visuelle.

Commandes retenues : A = saut, X = dash, B = tir, Y = interaction ; au clavier/souris, clic gauche = tir. Ces actions restent personnalisables.

Réglages du premier prototype : cinq points de vie, dash de 0,16 s avec recharge
de 1,2 s, ray gun sans munitions limitées et trois impacts pour vaincre l'alien.
Les valeurs de vie, d'armes et d'ennemis ont été remplacées par celles de l'étape 2.

## Étape 2 — progression et combat pendant une expédition

- [x] Générer sept salles : le cockpit, puis six salles de combat en ordre variable.
- [x] Renouveler les largeurs, plateformes, positions des ennemis, décors et armes à chaque nouvelle tentative.
- [x] Placer sept ou huit aliens par salle de combat et augmenter leur résistance, leurs dégâts et leur récompense au fil du parcours.
- [x] Laisser des restes verts sur chaque ennemi vaincu, absorbés en passant à proximité.
- [x] Montrer l'absorption et la montée de niveau sans interrompre le déplacement ou le combat.
- [x] Augmenter les PV maximum et les dégâts des armes avec le niveau.
- [x] Porter deux armes différentes, avec sélection directe RB / RT ou 1 / 2.
- [x] Proposer un fusil à impulsions rapide et un raygun lourd plus lent.
- [x] Se soigner sur LB / R, puis recharger les doses en abattant des ennemis.
- [x] Débloquer une deuxième place de soin au niveau 5, avec sa nouvelle charge prête.
- [x] Tout réinitialiser à la mort : niveau, XP, armes, soins, ennemis, objets et exploration.
- [x] Conserver les préférences de commandes précédentes lors de l'ajout des nouvelles actions.
- [ ] Ajuster la difficulté et la durée d'une expédition après les essais du joueur.
- [ ] Ajouter le boss pour utiliser sa récompense préparée de 250 XP et la recharge d'une dose de soin.

### Expérience et puissance de l'hôte

La substance se nourrit des ennemis vaincus : **l'XP est attribuée à l'absorption
des restes**, pas directement à la mort de la créature. Les premiers aliens
donnent 10 XP. Leur palier augmente avec l'avancée dans les salles : chaque
palier ajoute 5 XP de récompense, 10 PV à l'alien et 4 dégâts à son attaque.
Les valeurs de départ sont 30 PV et 20 dégâts par attaque.

| Règle actuelle | Valeur |
| --- | --- |
| Niveau initial | 1 |
| Coût du niveau 1 au niveau 2 | 100 XP |
| Coût du niveau suivant | `100 × 1,35^(niveau - 1)`, arrondi au multiple de 5 supérieur |
| Premiers coûts successifs | 100, 135, 185, 250 XP |
| PV maximum | `100 + 20 × (niveau - 1)` |
| Multiplicateur de dégâts | `1 + 0,12 × (niveau - 1)` |
| Récompense du futur premier boss | 250 XP ; règle préparée, boss à créer |

L'XP excédentaire passe au niveau suivant, y compris si une absorption fait
gagner plusieurs niveaux. La montée de niveau ajoute aussi le gain de PV
maximum à la vie actuelle : les blessures précédentes ne sont pas effacées.
L'animation est un effet temporaire pendant le jeu, sans pause ni blocage.

### Soins rechargeables au combat

- Une charge prête au départ ; capacité portée à deux au niveau 5.
- La nouvelle place débloquée au niveau 5 arrive chargée, sans remplir une autre charge déjà dépensée.
- LB / R soigne 40 % des PV maximum, sans dépasser le maximum.
- Cinq ennemis abattus rechargent **une dose manquante** ; la règle d'un boss pour une dose est prête pour son ajout.
- Les charges se rechargent successivement : si les deux sont vides, il faut dix ennemis pour les remplir toutes les deux.
- Les victimes ne sont pas mises en réserve quand toutes les charges sont pleines.
- Une recharge partielle continue si le joueur consomme l'autre dose ; se soigner à pleine vie ne dépense rien.

La mort réinitialise entièrement l'expédition. Il n'y a actuellement ni
amélioration permanente ni sauvegarde de la partie en cours. Les réglages de
commandes et l'apparence choisie ne sont pas de la progression à réinitialiser.

## Direction retenue

Un jeu **2D roguelike**, inspiré de Dead Cells pour l'exploration, les combats et
le système d'armes, dans l'univers spatial et undead de Notundertale.
Le personnage est un cadavre d'astronaute possédé par une substance inconnue
**vert foncé**. Les armes et les installations ont une identité futuriste.

Les personnages conservent la direction graphique déjà travaillée : pixel art
lisible en 100 × 100, combinaisons principalement blanches, visières réfléchissantes,
usure, déchirures, traces bordeaux et contamination verte. Les menus restent dans
le thème spatial bleu nuit et cyan.

## Zone 1 — le vaisseau échoué

### Début de la partie

- [x] Faire commencer la partie dans le **cockpit d'un vaisseau spatial**.
- [ ] Montrer que le vaisseau s'est écrasé sur une **planète inconnue**, il y a déjà longtemps.
- [x] Mettre en scène le réveil et la prise de contrôle d'un des cadavres d'astronautes par la substance du joueur (courte scène de prototype).
- [x] Introduire les commandes pendant les premiers déplacements et affrontements.

Le prototype possède automatiquement le personnage choisi dans le menu. Une
mise en scène plus complète, le choix du cadavre dans la salle et la présence de
dialogues restent à définir. La durée écoulée depuis le crash n'est pas fixée.

### Exploration et décor

- [x] Créer une première zone de vaisseau à **sept salles**, avec six salles de combat après le cockpit.
- [x] Générer les variantes de salles et leur ordre pour renouveler l'exploration **à chaque partie**.
- [ ] Enrichir les gabarits et leur identité visuelle pour obtenir la grande zone finale.
- [x] Prévoir des fenêtres dans certaines salles, avec une vue sur la planète inconnue (premier paysage provisoire).
- [x] Rendre les dégâts visibles dans les installations : équipements abîmés, structures endommagées et traces du crash (premier décor).
- [ ] Faire ressentir l'abandon ancien du vaisseau à travers l'état des lieux.
- [ ] Placer une salle de boss au bout du parcours, **avant la sortie du vaisseau**.

Salles présentes : cockpit, coursive, soute, infirmerie, réacteur, laboratoire
et hangar. Le cockpit est fixe au début ; les six autres sont mélangées. Les
cabines, l'atelier et d'autres salles restent des pistes pour enrichir le vaisseau.
L'apparence de la planète et la zone suivante restent ouvertes.

### Ennemis de la zone

- [x] Créer un premier petit alien hostile évoquant un mélange de **rat et de petit singe**.
- [x] Utiliser des teintes **violettes et noires** pour cette créature.
- [x] Lui donner des comportements d'approche et d'attaque adaptés aux salles du vaisseau.
- [ ] Prévoir des animations permettant de lire leurs déplacements, attaques et dégâts.

Le nombre de variantes et leurs capacités précises restent à définir.

### Boss de fin de zone

- [ ] Créer un soldat de type **space marine corrompu**, avec un design original.
- [ ] Montrer un corps maintenu en **demi-vie** par une substance **violette**.
- [ ] Distinguer cette substance de la contamination vert foncé du personnage joueur.
- [ ] Placer l'affrontement à l'extrémité du vaisseau, avant de pouvoir en sortir.
- [ ] Concevoir ses attaques, leurs signes annonciateurs et sa défaite.
- [x] Préparer la récompense de 250 XP et la recharge d'une dose de soin lors d'une victoire contre un boss.

Le boss n'est pas implémenté. Ses armes, ses éventuelles phases et le lien entre
les aliens et la substance violette ne sont pas encore décidés. La fin du
prototype demande actuellement de vaincre tous les aliens puis d'utiliser le sas.

## Combat, armes et orientation

### Armes futuristes

- [x] Intégrer un premier ray gun à ramasser, avec tir horizontal, impacts et son.
- [x] Découvrir des armes dans les salles et porter deux types différents.
- [x] Sélectionner directement l'arme 1 avec RB / 1 et l'arme 2 avec RT / 2.
- [x] Différencier le fusil à impulsions et le raygun lourd par leurs dégâts, cadence et projectiles.
- [x] Prévoir l'échange de l'arme active avec le butin si les deux emplacements sont pleins ; les doublons ne prennent pas de place supplémentaire.
- [ ] Enrichir le catalogue avec d'autres **pistolets, ray guns et armes laser**.
- [ ] Poursuivre les visuels, sons spécifiques et retours d'impact des armes.
- [x] Rendre les actions du prototype Histoire utilisables au clavier et à la manette Xbox, avec commandes personnalisables.

| Arme | Dégâts de base | Temps entre deux tirs | Usage |
| --- | --- | --- | --- |
| Fusil à impulsions | 9 | 0,10 s | Tir rapide maintenu |
| Raygun lourd | 30 | 0,55 s | Tirs plus lents et puissants |

Le ramassage utilise Y / E. Les deux armes sont disponibles dès les deux premières
salles, avec un premier type choisi au hasard. Les exemplaires suivants et leur
emplacement varient. Avec seulement deux types actuels, une fois les deux armes
portées les autres exemplaires sont des doublons ; la règle d'échange accueillera
les types supplémentaires. Changer d'arme ne réinitialise pas sa cadence de tir.
La visée est horizontale et les munitions illimitées pour le moment. Une visée
plus libre, les munitions ou la surchauffe, les améliorations propres aux armes
et la présence d'armes de mêlée restent à choisir.

### Mini-carte

- [ ] Afficher une **petite carte en haut à droite** pendant l'exploration.
- [ ] Y indiquer les salles ou endroits **déjà visités**.
- [ ] Distinguer clairement la position actuelle du joueur.
- [ ] Mettre à jour la carte lors de la découverte de nouvelles salles.
- [ ] Garder la carte lisible avec les autres informations de combat.

Proposition : représenter les salles et leurs connexions, sans dévoiler les salles
encore inexplorées. Le détail des icônes et des portes visibles reste à préciser.

## Architecture — base réalisée et extensions prévues

Le mode Infini actuel repose sur des déplacements libres et l'esquive. Le mode
Histoire utilise désormais une **vue de côté avec plateformes**, gravité, saut
et dash, suivant la direction confirmée.

Un mode dédié permet de faire évoluer ces règles tout en conservant le mode
Infini. `story/game.py`, `rooms.py`, `physics.py`, `player.py`, `enemies.py`,
`weapons.py`, `progression.py`, `experience.py` et `rendering.py` existent.
La génération est dans `rooms.py`, la graine, la caméra et les visites dans
`StoryGame`, les niveaux et soins dans `Progression`, l'interface dans `rendering.py`.
Le tableau distingue les fichiers présents des extractions ou ajouts futurs.

| Élément | Responsabilité et état |
| --- | --- |
| `story/game.py` — `StoryGame` | Boucle du mode Histoire, démarrage d'une partie, transitions de salles, mort et sortie de zone. |
| `story/run_state.py` — futur | Extraction éventuelle de l'état actuellement réparti dans `StoryGame`, `Progression`, les salles et l'équipement. |
| `story/generation.py` — futur | Extraction éventuelle de la génération actuellement dans `rooms.py`, si le plan devient plus complexe. |
| `story/rooms.py` — présent | Génération reproductible de sept salles, route, portes, plateformes, butin, ennemis et restes d'XP. |
| `story/player.py`, `story/physics.py` — présents | Déplacements propres au mode, gravité, saut, dash, collisions et vie de l'hôte. |
| `story/camera.py` — futur | Extraction éventuelle du suivi actuellement géré dans `StoryGame`. |
| `story/enemies.py` — présent ; `story/boss.py` — futur | Aliens par paliers déjà présents ; soldat corrompu à créer. |
| `story/weapons.py` — présent | Catalogue, deux emplacements, sélection directe, projectiles et cadences indépendantes. |
| `story/progression.py` — présent | Expérience, seuils, niveaux, PV, dégâts et recharge des soins pendant une partie. |
| `story/experience.py` — présent | Restes d'expérience et absorption à proximité du joueur. |
| `story/rendering.py` — présent | Décors, ennemis, armes, interface et effets du mode Histoire. |
| `story/hud.py`, `story/minimap.py` — futurs | Extraire l'interface si nécessaire et ajouter la représentation des lieux explorés. |
| Données de salles et d'armes — à enrichir | Paramètres actuellement dans `rooms.py`, `enemies.py`, `weapons.py` et `progression.py` ; gabarits plus riches à ajouter. |

### Raccordement au projet existant

- [x] Ajouter le lancement de `StoryGame` depuis `app.py`.
- [x] Réutiliser la gestion des ressources et des sons (`assets.py`, `audio.py`).
- [x] Étendre les actions dans `input.py`, `controls.py` et le menu des commandes pour le prototype Histoire.
- [x] Réutiliser les éléments de thème et d'interface (`theme.py`, `ui.py`) pour la cohérence des menus.
- [x] Prévoir la pause et les transitions avec une gestion du temps cohérente.
- [x] Garder les règles et les scores du mode Infini indépendants de la progression du mode Histoire.

Les commandes Histoire utilisent `controls_story.json`, séparé du fichier de
commandes Infini existant. Les deux fichiers sont personnels et exclus des archives.
Le format Histoire passe en version 3 : les profils précédents sont complétés
avec les sélections d'armes et le soin, sans remplacer les commandes personnalisées.
En cas de conflit avec une nouvelle valeur par défaut, une commande libre est choisie.

### Génération des salles

La version actuelle génère une **route linéaire bidirectionnelle** de sept salles.
Elle mélange l'ordre des salles après le cockpit et tire leurs dimensions,
passerelles facultatives, décors, positions des ennemis et armes. Un trajet au
sol continu rend les sorties accessibles sans saut obligatoire. Des gabarits
plus riches et un plan avec embranchements restent des extensions possibles.

- [x] Utiliser une graine de génération pour pouvoir reproduire une partie lors des corrections de bugs.
- [x] Garantir un parcours connecté du cockpit au sas provisoire, avec retours possibles.
- [ ] Garantir un parcours connecté du cockpit à la salle du boss, puis à la sortie.
- [x] Garder les portes accessibles, les entrées dégagées et les passerelles facultatives.
- [x] Espacer les apparitions des ennemis et conserver un trajet continu au sol.
- [ ] Réserver des emplacements cohérents pour les fenêtres et les dégâts du décor.
- [x] Conserver l'état des salles pendant une partie : ennemis vaincus, objets ramassés et restes d'XP.
- [ ] Alimenter la mini-carte depuis le même plan de salles et l'ensemble des lieux visités.
- [x] Recréer le plan et réinitialiser la découverte au début d'une nouvelle partie.

La règle de mort est désormais fixée : toute la progression de l'expédition
est perdue et une nouvelle tentative génère un nouveau vaisseau. Une éventuelle
sauvegarde temporaire entre sessions reste à définir ; aucune progression
permanente n'est ajoutée par cette étape.

## Ordre de réalisation proposé

1. **Prototype de déplacement et de combat — livré** : cockpit, une salle reliée, une arme et un ennemi ; valider maintenant la sensation avec le joueur au clavier et à la manette.
2. **Exploration et progression — première version livrée** : sept salles, parcours renouvelé, ennemis nombreux, XP, niveaux, deux armes, soins et remise à zéro à la mort.
3. **Mini-carte et enrichissement de la génération** : lieux visités visibles en haut à droite, gabarits plus variés et éventuels embranchements.
4. **Identité de la première zone** : fenêtres sur la planète, installations abîmées, aliens violet/noir, sons et animations.
5. **Boss et sortie** : soldat corrompu violet, affrontement lisible et accès à la sortie après sa défaite.
6. **Variété et équilibrage** : davantage d'armes et de salles, ajustement des courbes d'XP, dégâts et soins, puis décisions sur la suite du récit.

### Vérifications à prévoir lors de l'implémentation

- [x] Une nouvelle partie commence dans le cockpit avec la prise de contrôle du cadavre.
- [x] Plusieurs graines produisent des variantes et ordres de salles différents, avec un chemin praticable jusqu'au sas provisoire.
- [x] Une même graine permet de reproduire le plan pour diagnostiquer un problème.
- [x] Revenir dans une salle conserve son état pendant la partie.
- [ ] Afficher son statut visité et la position courante sur la carte.
- [x] Attribuer une seule récompense par ennemi et gagner l'XP seulement à l'absorption.
- [x] Conserver l'excédent d'XP et gérer plusieurs niveaux gagnés ensemble.
- [x] Recharger les soins par groupes de cinq victimes sans accumulation quand ils sont pleins.
- [x] Sélectionner directement les deux armes sans réinitialiser leur cadence de tir.
- [x] Recommencer avec niveau 1, inventaire vide, soin initial et nouvel environnement.
- [ ] Le boss empêche la sortie tant qu'il n'est pas vaincu.
- [x] Pause, commandes personnalisées et déconnexion de manette fonctionnent dans ce mode (tests avec périphériques simulés ; essai physique à faire).
- [x] Le lancement et le fonctionnement du mode Infini restent opérationnels.

## Choix à préciser ensemble au fil du développement

- Sensation du saut et du dash ; éventuelles capacités de déplacement supplémentaires.
- Possession automatique au réveil ou choix du cadavre par le joueur.
- Visée plus libre ; munitions, recharge ou surchauffe. Les deux emplacements d'armes et leur sélection directe sont confirmés.
- Taille cible du vaisseau, durée d'une partie et quantité de salles.
- Éventuelle sauvegarde temporaire entre sessions ; la mort réinitialise désormais toute l'expédition, sans progression permanente.
- Attaques et histoire du boss ; apparence de la planète et contenu après la sortie.
