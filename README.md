# Notundertale.py

Jeu en Python / Pygame : mode Infini d'esquive et premier prototype de plateforme
et de combat pour le mode Histoire.

## Lancer le jeu

Avec Python 3.10 ou plus récent installé, ouvrir un terminal dans ce dossier :

```sh
python -m pip install -r requirements.txt
python main.py
```

Pour jouer en fenêtre (1280 × 720) :

```sh
python main.py --windowed
```

Le lancement historique fonctionne aussi :

```sh
python Notundertale/notundertalev1006.py
```

On peut également utiliser `python -m Notundertale` ou lancer directement
`python Notundertale/__main__.py`. Les images et sons sont
recherchés à côté du code du jeu, quel que soit le dossier depuis lequel il est lancé.
Sous Windows, `py` peut remplacer `python` selon l'installation.

## Interface pixel art

Les menus utilisent un thème spatial bleu nuit et cyan : fond étoilé, planète
pixelisée, panneaux anguleux et typographie bitmap avec accents français.
Le menu principal, la sélection des skins, la pause, les commandes et le Game Over
partagent ce style. Les jauges de vie, de bouclier et de dash sont intégrées à des
panneaux assortis ; la recharge du dash reste liée au chronomètre de jeu.

Le bouton actif se distingue par une bordure cyan, une flèche et un repère carré.
Le survol à la souris et la navigation à la manette utilisent le même indicateur.
Les menus gardent leurs proportions en plein écran et ajustent aussi les zones
de clic. Des marges peuvent apparaître sur un écran qui n'est pas au format 16:9.

La palette et le dessin des éléments sont regroupés dans `Notundertale/theme.py`.
Aucune police ni image supplémentaire n'est à installer. Le mode Histoire a son
premier décor de vaisseau. Les développements actuels concernent uniquement le
mode Histoire ; le mode Infini conserve son fonctionnement pour une évolution ultérieure.

## Personnages miniatures

Quatre astronautes en combinaison blanche abandonnée, contaminés par une substance
vert foncé, sont jouables dans les deux modes. **Le Rémanent** présente des
déchirures au torse et au genou ; **Le Scaphandre** a perdu un avant-bras ;
**La Colonie** est davantage envahie autour du casque et du gant ; **Le Dériveur**
a perdu une partie de sa jambe, prolongée par une masse informe de contamination,
et sa visière brisée laisse déborder la même matière. Le Rémanent est sélectionné
au démarrage.

Les dessins ont été simplifiés en pixel art : grandes formes, contours francs
et ombrages limités, pour rester lisibles à taille réelle. Ils comportent des
visières réfléchissantes qui masquent le
visage, des zones de tissu blanc/gris/beige, des trous et une contamination vert
foncé. Des traces de sang séché bordeaux bordent les déchirures et tachent le
tissu. Le Rémanent porte une empreinte de main sur la visière, le Scaphandre
une autre sur le torse.
Les PNG transparents font **100 × 100 pixels** et sont affichés directement à
cette taille en jeu. Le corps garde la même hauteur visible que le skin 2.
Les six cartes du menu
sont réparties sur deux lignes, avec les deux apparences classiques à la
suite des nouvelles. Cliquer sur une carte ou utiliser gauche / droite au clavier
ou à la manette, puis lancer **Mode Infini** ou **Mode Histoire**.

En mode Infini, les collisions suivent les pixels du sprite, y compris après retournement ; les
marges transparentes ne subissent pas de dégâts. Les commandes, la vitesse, les
vies et le dash restent les mêmes. Les personnages classiques gardent leurs
dimensions précédentes. En Histoire, une boîte de collision de 44 × 86 pixels
sert au déplacement sur les plateformes et aux dégâts ; le sprite reste en 100 × 100.

Les quatre astronautes disposent maintenant d'une **boucle de marche de six images**,
d'une pose en l'air pour le saut et d'une pose penchée pour le dash. Chaque image
mesure 100 × 100 pixels. La marche suit le déplacement réel, s'arrête contre un mur
ou au repos, se retourne vers la gauche et reste figée pendant la pause.
Les deux apparences classiques conservent leur pose fixe.

Les planches de huit poses sont dans `Notundertale/characters/animations/`
(quatre colonnes, deux lignes), avec un lecteur commun dans `Notundertale/animation.py`.
La pose de repos et les aperçus des menus restent dans `Notundertale/characters/`.
En Infini, le masque de collision suit chaque image affichée ; la boîte de collision
du mode Histoire reste stable pendant les animations.

## Mode Histoire — exploration, combat et progression

Choisir **Mode Histoire** dans le menu. Une courte scène montre la contamination
verte prenant possession de l'astronaute dans le cockpit. L'apparence sélectionnée
dans le menu est utilisée.

Le jeu se joue **de côté, avec saut et dash**. Explorer le cockpit, récupérer une
arme avec **E / Y**, puis emprunter la porte à droite. La partie comporte **sept
salles** : le cockpit et six salles de combat (coursive, soute, infirmerie,
réacteur, laboratoire et hangar), dont l'ordre change. Leur largeur, leurs
plateformes, le décor, les positions des ennemis et les armes varient selon la
graine de la partie. Chaque salle de combat contient sept ou huit aliens.

Les aliens violet/noir annoncent leur bond par un point d'exclamation : sauter
ou dasher pour l'éviter. Les ennemis deviennent plus résistants et rapportent
davantage d'expérience au fil du parcours. Les salles restent reliées dans les
deux sens ; leurs ennemis vaincus, armes ramassées et restes d'expérience sont
conservés lors des allers-retours. Vaincre toutes les créatures, puis interagir
avec le sas de la dernière salle termine cette version. **Le boss n'est pas
encore présent** : ce sas reste une fin provisoire.

| Action Histoire | Clavier | Manette Xbox |
| --- | --- | --- |
| Se déplacer | Flèches gauche / droite | Stick gauche ou croix |
| Sauter | Espace | A |
| Dash | Maj gauche ou droite | X |
| Tirer | Clic gauche | B |
| Ramasser / ouvrir une porte / utiliser le sas | E | Y |
| Sélectionner l'arme 1 | 1 | RB |
| Sélectionner l'arme 2 | 2 | RT |
| Se soigner | R | LB |
| Pause | Échap | Start / Menu |

Le tir est horizontal dans la direction regardée ; maintenir la commande permet
de tirer en continu. Les armes n'ont pas de limite de munitions dans ce prototype.
Relâcher le saut plus tôt réduit sa hauteur. Le dash protège pendant 0,16 seconde
et recharge en 1,2 seconde ; un nouvel appui est nécessaire pour le relancer.

Deux armes différentes peuvent être portées. **RB / 1 choisit directement le
premier emplacement**, **RT / 2 le second**. Le fusil à impulsions tire vite
(9 dégâts, un tir toutes les 0,10 s) ; le raygun lourd tire plus lentement mais
frappe plus fort (30 dégâts, un tir toutes les 0,55 s). Ce sont les valeurs au
niveau 1. Une arme déjà portée n'occupe pas une deuxième place. Le système permet
d'échanger l'arme active si les deux places sont occupées ; avec les deux types
actuels, les autres exemplaires rencontrés sont des doublons. Les deux types
sont accessibles dès le cockpit et la première salle de combat, dans un ordre variable.

Les armes ont des silhouettes pixel art détaillées : crosse, viseur, chargeur et
évents pour le fusil ; batterie, cage et bobines cyan pour le raygun. Les bras
tiennent la poignée et soutiennent le canon, avec une posture adaptée à la marche,
au saut, au dash et à la direction regardée. La substance remplace l'avant-bras
manquant du Scaphandre. Le tir ajoute un bref recul et un éclair à la bouche du
canon, d'où part aussi le projectile. Ces poses sont composées uniquement dans
le mode Histoire, sans modifier les images originales des personnages.

### La substance se nourrit

Un ennemi vaincu laisse des **restes verts à absorber en passant à proximité**.
L'expérience est gagnée à leur absorption, avec une courte animation ; tuer
l'ennemi ne l'ajoute pas directement à la jauge. Les premiers aliens donnent
**10 XP**, puis les récompenses augmentent par paliers de 5 XP au fil du parcours.
Le passage du niveau 1 au niveau 2 coûte **100 XP**. Les coûts suivants suivent
`100 × 1,35^(niveau - 1)`, arrondis au multiple de 5 supérieur : 135, 185, 250…
L'excédent d'XP est conservé après une montée de niveau.

L'hôte commence avec **100 PV**. Chaque niveau ajoute **20 PV maximum** et
**12 % des dégâts de base** des armes. Il gagne aussi les 20 PV supplémentaires
sur sa vie actuelle, sans effacer les dégâts déjà subis. L'effet visuel de
montée de niveau laisse le déplacement et les combats continuer.

### Soins et nouvelle tentative

**LB / R** rend **40 % des PV maximum**, dans la limite de la vie maximale.
Une charge est prête au départ. Au **niveau 5**, une deuxième place de soin se
débloque avec sa charge prête. Chaque groupe de **cinq ennemis abattus** recharge
une seule charge manquante ; les deux charges se rechargent l'une après l'autre.
Les victimes tuées lorsque toutes les charges sont pleines ne sont pas mises
en réserve. Une recharge déjà partiellement gagnée est conservée si l'autre
charge est consommée. Se soigner à pleine vie ne consomme rien.

La règle de recharge d'**une charge après un boss** et sa récompense de **250 XP**
sont préparées pour la suite ; aucun boss n'est encore jouable.

**La mort remet la partie à zéro** : niveau, expérience, armes, ennemis, salles
visitées et soins repartent de leur état initial. Recommencer tire une nouvelle
graine et renouvelle les salles et les armes. Il n'y a aucune amélioration
permanente ni sauvegarde de l'expédition à la fermeture.

Dans **Commandes**, cliquer sur le nom du mode en haut à droite, ou utiliser
**Tab / Y**, pour passer d'Infini à Histoire. Depuis la pause, la page du mode actif
s'ouvre directement. Toutes les actions Histoire sont réaffectables. Les commandes
Histoire sont sauvegardées séparément dans `Notundertale/controls_story.json` :
les réglages Infini existants restent disponibles. Sur une manette générique
sans profil SDL, le tir utilise par défaut le bouton 2 et peut être réaffecté.
Les anciens profils Histoire sont complétés avec les trois nouvelles actions,
en conservant les touches personnalisées et en évitant les doublons.

Le prototype initial comportait deux salles fixes et un alien. Cette étape
ajoute la génération, les niveaux, les soins et les deux armes ; les décors et
animations restent une base à développer. La mini-carte, le boss, la variété
des armes et la suite du récit restent dans la [feuille de route](docs/MODE_HISTOIRE.md).
Les scores et les règles du mode Infini restent indépendants.

## Commandes par défaut — mode Infini

| Action | Clavier | Manette Xbox |
| --- | --- | --- |
| Se déplacer | Flèches directionnelles | Stick gauche ou croix directionnelle |
| Dash | Maj gauche ou droite | A |
| Ouvrir la pause | Échap | Start / Menu |
| Choisir dans les menus | Entrée ou clic gauche | A |
| Retour / reprendre depuis la pause | Échap | B ou Start |
| Naviguer dans un menu | Haut / bas | Stick ou croix haut / bas |
| Choisir le skin dans le menu principal | Gauche / droite | Stick ou croix gauche / droite |

Les manettes Xbox reconnues par le système peuvent être branchées avant ou
pendant le jeu. La première manette connectée est utilisée. La déconnecter
sélectionne la suivante s'il y en a une. Si la manette utilisée pour jouer
est déconnectée, la partie se met en pause. Le clavier reste disponible.

La lecture utilise les boutons standardisés de
[Pygame / SDL](https://www.pygame.org/docs/ref/sdl2_controller.html).
Un mode générique permet aussi d'affecter les boutons et axes des périphériques
qui ne disposent pas d'un profil standard. Pour ces modèles, les numéros de
boutons remplacent les noms Xbox et peuvent nécessiter un réglage manuel.

## Changer les commandes

1. Ouvrir **Commandes** depuis le menu principal ou la pause.
2. Choisir une action du mode affiché, puis la colonne **Clavier / souris**
   ou **Manette**. Utiliser les directions ou cliquer sur la case.
3. Appuyer sur Entrée / A, puis sur la nouvelle touche, le nouveau bouton,
   la gâchette ou la direction du stick souhaitée.
4. Revenir avec Échap / B. Les choix sont enregistrés automatiquement.

Pour annuler une affectation en cours : Échap, le bouton **Annuler** à la
souris, ou attendre dix secondes. Pendant l'affectation, B est une commande
assignable, pas une annulation. Relâcher un stick déjà incliné avant de le
déplacer pour l'affecter.

Si une commande est déjà utilisée, les deux affectations sont échangées et
le tableau est mis à jour. Une exception protège Échap : on ne peut pas
l'échanger avec un déplacement. Entrée et Échap, ainsi que A et B dans les
menus, restent disponibles pour naviguer. La navigation au stick et à la croix
reste également accessible dans les menus, même après une réaffectation.

Une nouvelle affectation remplace l'ancienne pour cette action. Par exemple,
changer « Monter » remplace le couple par défaut stick + croix par la direction
ou le bouton choisi. **Réglages par défaut** réinitialise le clavier,
la manette courante et la zone morte. Les profils des autres modèles sont gardés.

La **zone morte** ignore les petites variations du stick : 20 % par défaut,
réglable entre 10 et 50 %. Augmenter ce réglage si le personnage bouge sans toucher
au stick. Sur cette ligne, utiliser gauche / droite ou cliquer sur la barre.
Le déplacement au stick est progressif au-delà de cette zone.

Les réglages sont enregistrés dans `Notundertale/controls.json`, ignoré par Git,
avec un profil par modèle de manette. Si la sauvegarde échoue, un message le
signale et les changements restent actifs pour la session. Le fichier n'est
pas livré dans l'archive : chacun conserve ses propres commandes.

Le dash dure 0,2 seconde et protège des dégâts pendant son déplacement.
La recharge dure 5 secondes **à partir du début du dash**. La jauge en bas à
gauche affiche sa progression et le temps restant. Sans direction pressée,
le dash part vers la droite, comme dans la version d'origine. Maintenir la commande de dash
déclenche un nouveau dash quand la recharge est terminée.

La pause suspend le score, le dash, les protections, les bonus et les apparitions.
Le volume du menu pause contrôle la musique **et** les effets sonores. À la
manette, sélectionner le volume avec bas, puis régler avec gauche / droite.
La pause reste active pendant la modification des commandes.

## Organisation du code

| Fichier dans `Notundertale/` | Rôle |
| --- | --- |
| `app.py` | Initialisation et passage d'un écran à l'autre |
| `game.py` | Partie : apparitions, collisions, score et rendu |
| `player.py` | Déplacement, dash et points de vie |
| `sprites.py` | Météores, lasers, avertissements et bonus |
| `menus.py` | Menu principal, pause et Game Over |
| `ui.py` | Jauge de dash, boutons et halo du bouclier |
| `theme.py` | Palette, typographie pixel, panneaux et adaptation à l'écran |
| `config.py` | Couleurs, chemins et réglages de durée/difficulté |
| `difficulty.py` | Progression et choix des variantes de météores |
| `timing.py` | Horloge qui exclut le temps passé en pause |
| `assets.py` | Chargement et cache des images et planches de personnages |
| `animation.py` | Lecture des poses de repos, marche, saut et dash |
| `skins.py` | Catalogue, dimensions et aperçus des personnages |
| `audio.py` | Musique, effets et volume |
| `scores.py` | Lecture et sauvegarde du classement |
| `controls.py` | Affectations, validation et sauvegarde séparée des commandes Infini / Histoire |
| `input.py` | Clavier, manettes, branchement à chaud et navigation |
| `controls_menu.py` | Écran de personnalisation des commandes |
| `story/game.py` | Réveil, boucle Histoire, transitions, objectifs et fin du prototype |
| `story/rooms.py` | Génération de sept salles, portes et état des objets / ennemis |
| `story/physics.py`, `story/player.py` | Collisions, gravité, saut, dash et vie de l'hôte |
| `story/enemies.py`, `story/weapons.py` | Aliens par paliers, deux emplacements d'armes, tirs et impacts |
| `story/progression.py` | Niveaux, seuils d'XP, PV, dégâts et charges de soin de la partie |
| `story/experience.py` | Restes d'expérience et absorption à proximité |
| `story/rendering.py` | Décors du vaisseau, créature et interface Histoire |

`main.py` lance l'application. `Notundertale/notundertalev1006.py` reste un
petit lanceur de compatibilité. Importer un module n'ouvre aucune fenêtre.
Chaque nouvelle partie possède ses propres groupes de sprites et échéances.

## Sons

Cinq sons chiptune originaux sont inclus dans `Notundertale/sounds/` :

- `hit.wav` : lorsqu'une vie est réellement perdue ;
- `dash.wav` : au déclenchement d'un dash accepté ;
- `power_up.wav` : lors du ramassage d'un cœur ou d'un bouclier ;
- `game_over.wav` : une seule fois à la fin de la partie.
- `ray.wav` : tir du pistolet à rayons en Histoire.

On peut les remplacer par des fichiers WAV portant les mêmes noms. Pour
régénérer les effets fournis : `python tools/generate_sounds.py`.
Ils sont synthétisés sans échantillon externe. La musique existante est conservée.
Si un effet, la musique ou le périphérique audio manque, le jeu continue sans
le son concerné et indique le problème dans le terminal.

## Scores

Le classement reste dans `Notundertale/scores.json`, au même format qu'avant.
Les dix meilleurs scores sont conservés et les cinq premiers sont affichés.
Ce fichier personnel est ignoré par Git. Les entrées invalides sont ignorées
pour éviter qu'un fichier abîmé bloque le lancement du jeu.

## Vérifications

```sh
python -m unittest discover -s tests -v
```

Les tests utilisent l'affichage et l'audio factices de SDL : ils n'ouvrent pas de
fenêtre et ne font pas de bruit. Ils couvrent les limites de recharge, la pause,
les dégâts, les sons, les bonus, les apparitions, les scores et le redémarrage,
ainsi que les commandes Xbox simulées, les réaffectations, les sauvegardes,
les menus, les déconnexions, la zone morte et les appuis maintenus.
Les vérifications couvrent également le démarrage des lanceurs,
la sélection des six personnages à la souris, au clavier et à la manette,
les collisions des miniatures et les clics dans les menus agrandis ou affichés
avec des marges. Les tests Histoire couvrent aussi la génération reproductible,
le ramassage, le combat, les collisions, l'expérience, les niveaux, les soins,
les deux emplacements d'armes, la pause, le redémarrage et l'isolation des commandes.
Les nouveaux profils sont testés avec migration des préférences et appuis maintenus.
Le rendu a été
inspecté en 1280 × 720, 1920 × 1080 et 1024 × 768.
Une vérification complémentaire avec
une manette virtuelle SDL a couvert les événements réels du pilote, le stick,
la gâchette, le branchement et la déconnexion. Aucun essai avec une manette
physique n'a été possible dans l'environnement de développement.
En Infini, le déplacement reste calculé par image, avec une limite à 60 images
par seconde, comme dans le prototype d'origine. En Histoire, il utilise le temps
écoulé et des petits pas de simulation ; il a été vérifié à 30, 60 et 144 images
par seconde. Un essai réel permet de juger la sensation de jeu et les sons.

## Suite du projet

- Première étape faite : séparation du code, jauge de dash, quatre effets sonores.
- Troisième étape faite : interface et menus pixel art, bleu nuit et cyan.
- Quatrième étape faite : quatre astronautes undead miniatures jouables dans le mode Infini.
- Animations de déplacement intégrées aux quatre astronautes ; animations de combat, projectiles et décor à poursuivre.
- Deuxième étape faite : manette, navigation complète des menus et commandes personnalisables.
- Première étape Histoire jouable : cockpit, coursive, saut, dash, ray gun et un alien.
- Deuxième étape Histoire : sept salles renouvelées, absorption d'XP, niveaux,
  soins rechargeables au combat et deux armes portées avec sélection directe.
- Suite du mode Histoire : [direction, architecture et liste des choses à faire](docs/MODE_HISTOIRE.md).
  Première zone : vaisseau échoué, salles générées à chaque partie, aliens violet/noir,
  boss corrompu, armes futuristes et mini-carte des lieux visités.

Le bouton Histoire lance le prototype actuel. La mini-carte, le boss, l'identité
visuelle détaillée des salles et la suite du récit restent à développer.
Ces nouvelles mécaniques concernent uniquement Histoire ; le mode Infini sera
repris séparément plus tard.
