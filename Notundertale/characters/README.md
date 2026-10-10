# Personnages originaux

Les quatre PNG transparents font 100 × 100 pixels et sont affichés à cette taille
en jeu, sans agrandissement supplémentaire. Le corps fait 93 pixels de haut,
comme le skin 2. Les images ont été redessinées avec l'outil intégré de génération
d'images : grandes formes pixel art, contours sombres francs, ombrages simplifiés
et visières lisibles. Export au plus proche voisin, sans lissage. Les sources
et prompts de cette révision sont dans le livrable astronautes-pixel-100x100.

- `remanent.png` : combinaison blanche déchirée au torse et au genou,
  empreinte de main bordeaux sur la visière.
- `scaphandre.png` : avant-bras manquant et manche ouverte,
  empreinte de main bordeaux sur le torse.
- `colonie.png` : contamination plus étendue au casque, à l'épaule et au gant.
- `deriveur.png` : bas de jambe remplacé par une masse informe de contamination,
  vêtement jauni et visière partiellement brisée d'où déborde la même matière.

Toutes les variantes ont une visière opaque réfléchissante, des salissures,
des trous et une matière contaminante vert foncé. Du sang séché rouge bordeaux
marque les contours des déchirures et certaines zones du tissu blanc.
Les faces ne montrent pas de crâne.

Le fond et les marges sont transparents. En mode Infini, le masque de collision utilise l'alpha
du sprite, pas le rectangle complet. En Histoire, le personnage utilise une boîte
de collision de 44 × 86 pixels. Conserver ces propriétés pour les remplacer.
La pose de repos reste dans ces quatre PNG. Les planches `animations/*.png`
contiennent huit images transparentes de 100 × 100 dans une grille de quatre colonnes
et deux lignes (400 × 200) : six images de marche, une pose de saut et une pose de dash.
Elles se retournent vers la gauche et s'arrêtent à l'arrêt du personnage. Les pieds
sont alignés à la ligne 97. Les poses proviennent de l'outil intégré image_gen,
puis sont découpées et exportées au plus proche voisin sans lissage. Sources,
aperçus animés et prompts : livrable `astronautes-animations`.

Les références détaillées, les sources de génération et les prompts sont fournis
séparément avec les livrables artistiques du projet.
