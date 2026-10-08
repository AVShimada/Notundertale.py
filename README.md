# Notundertale.py

Petit jeu d'esquive en Python / Pygame pour apprendre à programmer.

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
Aucune police ni image supplémentaire n'est à installer. Les projectiles et le
décor pendant la partie sont conservés pour une étape ultérieure.

## Personnages miniatures

Quatre astronautes morts, animés par une substance inconnue, sont jouables dans le
mode Infini : **Le Rémanent** (cyan), **Le Scaphandre** (ambre), **La Colonie**
(violet) et **Le Dériveur** (vert pâle). Le Rémanent est sélectionné au démarrage.

Leurs PNG transparents font **32 × 48 pixels** et sont agrandis en jeu à la
**même hauteur visible que le skin 2**, dans un cadre de 100 × 100 pixels.
Leurs proportions sont conservées, sans lissage des pixels. Les six cartes du menu
sont réparties sur deux lignes, avec les deux apparences classiques à la
suite des nouvelles. Cliquer sur une carte ou utiliser gauche / droite au clavier
ou à la manette, puis lancer **Mode Infini**.

Les collisions suivent les pixels du sprite, y compris après retournement ; les
marges transparentes ne subissent pas de dégâts. Les commandes, la vitesse, les
vies et le dash restent les mêmes. Les personnages classiques gardent leurs
dimensions précédentes.

Cette première intégration utilise des poses fixes qui se retournent selon le
déplacement, avec les effets existants de dash et de dégâts. Les cycles d'animation
de déplacement et de dash pourront être ajoutés ensuite. Les images sont dans
`Notundertale/characters/`, et les noms et dimensions dans `Notundertale/skins.py`.

## Commandes par défaut

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
2. Choisir une ligne (déplacement, dash ou pause), puis la colonne **Clavier**
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
| `assets.py` | Chargement et cache des images |
| `skins.py` | Catalogue, dimensions et aperçus des personnages |
| `audio.py` | Musique, effets et volume |
| `scores.py` | Lecture et sauvegarde du classement |
| `controls.py` | Affectations, validation et sauvegarde des commandes |
| `input.py` | Clavier, manettes, branchement à chaud et navigation |
| `controls_menu.py` | Écran de personnalisation des commandes |

`main.py` lance l'application. `Notundertale/notundertalev1006.py` reste un
petit lanceur de compatibilité. Importer un module n'ouvre aucune fenêtre.
Chaque nouvelle partie possède ses propres groupes de sprites et échéances.

## Sons

Quatre sons chiptune originaux sont inclus dans `Notundertale/sounds/` :

- `hit.wav` : lorsqu'une vie est réellement perdue ;
- `dash.wav` : au déclenchement d'un dash accepté ;
- `power_up.wav` : lors du ramassage d'un cœur ou d'un bouclier ;
- `game_over.wav` : une seule fois à la fin de la partie.

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
Cette version passe 58 tests automatisés, dont le démarrage des lanceurs,
la sélection des six personnages à la souris, au clavier et à la manette,
les collisions des miniatures et les clics dans les menus agrandis ou affichés
avec des marges. Le rendu a été
inspecté en 1280 × 720, 1920 × 1080 et 1024 × 768.
Une vérification complémentaire avec
une manette virtuelle SDL a couvert les événements réels du pilote, le stick,
la gâchette, le branchement et la déconnexion. Aucun essai avec une manette
physique n'a été possible dans l'environnement de développement.
Le déplacement reste calculé par image, avec une limite à 60 images par seconde,
comme dans le prototype. Un essai réel permet de juger la sensation de jeu et les sons.

## Suite du projet

- Première étape faite : séparation du code, jauge de dash, quatre effets sonores.
- Troisième étape faite : interface et menus pixel art, bleu nuit et cyan.
- Quatrième étape faite : quatre astronautes undead miniatures jouables dans le mode Infini.
- À définir ensemble : animations des personnages, projectiles et décor en jeu.
- Deuxième étape faite : manette, navigation complète des menus et commandes personnalisables.
- À concevoir : scénario, dialogues, niveaux et progression du mode Histoire.

Le bouton Histoire affiche encore un écran « à venir » ; aucun scénario n'a été ajouté.
