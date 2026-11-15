# REPRISE PROJET — Fire Emblem Engage Language Plugin

**Dernière mise à jour : 15 novembre 2026**  
**Dépôt :** https://github.com/Deklou/Engage_Language_Plugin  
**Branche stable :** master  
**État fusionné dans master :** V10.27i, PR #2 (merge 160aa397). **Dernier test validé :** V10.28b sur la PR #4 (encore à fusionner au 15/11/2026).

> Ce fichier est la mémoire de reprise **opérationnelle** du projet. Il ne remplace ni les sources GitHub ni les logs d'exécution. En début de nouvelle conversation, vérifier les commits et PR actuels avant de considérer cet état comme toujours à jour.

## 1. Démarrage rapide d'une nouvelle conversation

Message à envoyer à ChatGPT dans le projet Engage Modding :

> On reprend Fire Emblem Engage Language Plugin. Lis d'abord le fichier REPRISE_PROJET.md sur la branche master du dépôt GitHub Deklou/Engage_Language_Plugin. Vérifie que son état correspond au code et aux PR actuels. Nous travaillons avec GitHub, Ghidra Engage (lecture seule, si tunnel actif), WSL et Ryujinx. Propose une investigation avant toute modification, préserve master et donne chaque commande terminal dans un bloc séparé. Je te communiquerai l'objectif de cette session.

**Principe :** l'utilisateur formule le comportement attendu et vérifie dans le jeu ; l'assistant enquête, prépare le code sur une branche, produit une PR et analyse les résultats. Limiter autant que possible les manipulations et les copier-coller côté utilisateur.

## 2. État technique du projet

- Jeu : **Fire Emblem Engage v2.0.0**, sur Ryujinx.
- Plugin : **Rust / Skyline / Cobalt**, compilation via Cargo Skyline, binaire NRO.
- Dépôt : **Deklou/Engage_Language_Plugin**, branche **master** protégée par la convention de travail : pas de modification directe ; passer par une PR.
- Fichiers principaux :
  - src/config_hook.rs : interception de la construction du menu Settings ; capture des clés MSBT ; rafraîchissement des options natives, de la barre de titre et des entrées tierces.
  - src/language.rs : changement de langue et déclenchement des rafraîchissements.
  - src/voice.rs : gestion des voix.
  - src/interface.rs : liaisons vers les fonctions du jeu.
  - deploy.sh : compilation et déploiement dans la SD virtuelle de Ryujinx.
- La PR #2 (« V10.27i ») a été **fusionnée le 15/11/2026** ; la nouvelle version a été **retestée en jeu depuis master** sans problème signalé.
- La **V10.28b**, branche `feature/map-system-live-localization-probe`, PR #4, est **compilée et validée dans Ryujinx mais pas encore fusionnée** à la date du document. Elle rafraîchit à chaud les noms et textes d'aide des menus de carte `MapSystemMenu` et `SubSystemMenu`, ainsi que le cartouche du chapitre, après `ReflectSetting` / `Mess.Reload`. Le triangle des armes se mettait déjà à jour spontanément.
- Les fonctionnalités validées comprennent le changement de langue à chaud des paramètres natifs, des textes du bandeau Settings et des trois entrées supplémentaires **MyCodeMods**, **Cobalt Settings**, **Plugin Settings**.
- Tests fonctionnels des traductions tierces : passages entre **anglais, français et espagnol**, sans fermer Settings, avec titres, commandes et aides actualisés, sans crash lors des scénarios testés.
- Des chaînes sont prévues pour le **japonais, le chinois simplifié et le coréen**, reprises des localisations publiques Cobalt, mais leur affichage n'a **pas été validé dans cette session**. Certaines autres langues retombent sur l'anglais. Ne pas confondre « implémenté » et « testé ».
- **Limite assumée :** les textes arbitraires de futurs plugins ne sont pas traduits magiquement. Le catalogue de correspondances doit contenir les textes/locales nécessaires ; l'identification du mécanisme, elle, ne dépend pas des noms de classes des plugins.

### Résultat des investigations V10.27

1. Le menu Settings étudié contient **25 entrées natives et 3 entrées tierces**, soit **28 entrées**.
2. Une liste Unity peut avoir une **capacité de 32** pour seulement **28 éléments valides**. Dans cette configuration, parcourir directement list.iter() explorait aussi les quatre emplacements non utilisés et provoquait probablement les accès mémoire invalides observés. Toujours borner les parcours à **list.len()** : en pratique, list.iter().take(list.len()).
3. Les fonctions Rust SetCommandText / SetHelpText des extensions Cobalt sont appelées **à la construction** des éléments. Elles ne sont **pas enregistrées comme méthodes virtuelles IL2CPP** par ConfigBasicMenuItem::new_command dans la bibliothèque étudiée. Les chercher avec get_virtual_method renvoie MISSING ; ne pas bâtir une correction sur l'hypothèse contraire.
4. La solution fonctionnelle V10.27i reconnaît les titres dans **toutes les variantes connues du catalogue**, puis remplace directement les champs title_text, command_text et help_text avant d'appeler update_text(). Cela gère les changements successifs sans recréer le menu.
5. Les données de traduction de Cobalt sont disponibles dans le dépôt public DivineDragonFanClub/localize, notamment message/us/uses/table.json pour l'espagnol et message/eu/eufr/table.json pour le français.
6. Les logs utiles incluent **ELP V10.27i** et la synthèse de type « DONE rows=28 translated=3 unknown=0 lang=... ». Toujours vérifier les valeurs réelles dans les logs et sur l'écran.

### Validation V10.28b — menus de carte

- Le jeu conserve deux menus parents lors de l'ouverture de Settings : `ConfigSequence → SubSystemMenu → MapSystemMenu`. Détecté dans Ghidra et confirmé en jeu par V10.28a.
- Structure mesurée : sous-menu **5 entrées, capacité 8** ; menu racine **7 entrées, capacité 8**. Toujours utiliser `list.iter().take(list.len())`.
- Les lignes existantes sont rafraîchies par l'IL2CPP natif `App.BasicMenuItemContent.BuildText` (offset `0x2467490`) : la fonction redemande les noms localisés aux méthodes virtuelles `GetName`.
- Les aides du menu racine sont recalculées par `GetHelpText` et `App.InfoUtil.TrySetText` (offset `0x290f0a0`). Les aides et noms utilisent les MSBT du jeu, pas un catalogue manuel.
- Le cartouche du chapitre (titre, objectifs, tours, etc.) est actualisé par `App.SortieTopMenuContent.UpdateInfo(false)` (offset `0x24ec450`).
- Journal Ryujinx de validation, transitions observées **français ↔ espagnol** : `SUBMENU DONE size=5 titles=4 helps=4 no_content=1`, `ROOT DONE size=7 titles=7 helps=7 no_content=0`, `CHAPTER INFO refreshed`, `ALL DONE` à chaque changement enregistré. Le contenu d'une des cinq entrées du sous-menu était absent au moment du rafraîchissement, sans crash observé. Ne pas prétendre que son affichage hors écran a été rafraîchi immédiatement : vérifier sa reconstruction à l'affichage si nécessaire.
- Dans le même log, V10.27i continue à traduire **3/3 entrées** des plugins. L'utilisateur confirme visuellement que l'objectif des trois niveaux de menus est atteint. Les autres langues n'ont pas toutes été testées exhaustivement dans cette session.
- **Leçon compile :** `Cargo.lock` épingle `engage v0.6.3` au commit `0911ded709890bfc4f74b53420b40fb4b9778aee`. La branche `master` du dépôt de la dépendance peut exposer des méthodes ou champs absents de cette version. Toujours consulter le **commit épinglé** avant d'implémenter ; `BasicMenuItem::rebuild_text()` n'existe pas dans cette version et `BasicMenu.menu_content` y est un `*const u8`.

## 3. Outils et accès

### GitHub (connecté à ChatGPT)

Le dépôt est accessible via le connecteur GitHub. L'assistant peut consulter les sources, créer une branche, commiter des modifications et ouvrir une PR.

**Règle :** chaque évolution de code passe par une branche et une PR. L'utilisateur fusionne après validation. Ne jamais présenter une PR non compilée comme un correctif vérifié. Un simple git pull sur master ne récupère pas une branche expérimentale non fusionnée.

### Ghidra Engage (connecté à ChatGPT quand le PC est prêt)

- Outil : plugin personnalisé **Ghidra Engage**, relié au serveur local GhidrAssistMCP via un tunnel OpenAI.
- Programme analysé : **main_200**, AArch64, base **0x7100000000** (Fire Emblem Engage 2.0.0).
- **17 outils en lecture seule** exposés : recherches de fonctions et chaînes, pseudocode, désassemblage, appels, références, informations de classes/types/programme. Ne pas présumer d'accès en écriture.
- Fonctions-repères :
  - ConfigSequence.CreateConfigMenu : 0x710253a470 (offset Skyline 0x253a470).
  - ConfigMenu.CreateBind : 0x7102538a10 (offset 0x2538a10).
  - ConfigBasicMenuItem.UpdateText : 0x7102537000 (offset 0x2537000).
  - App.Mess.Get : offset Skyline 0x25c9240.
  - App.Mess.GetLanguageDirectoryName : 0x71025d6ac0.
- Pour activer : ouvrir Ghidra et main_200, cocher **Enable MCP Server** dans GhidrAssistMCP, puis lancer le tunnel depuis PowerShell avec le profil **ghidra-engage**. Le serveur Ghidra utilise le port **8080** et le tunnel a été lancé avec le port de santé **8081** pour éviter le conflit.
- Pour couper : **Ctrl+C** dans le PowerShell qui exécute le tunnel, puis décocher Enable MCP Server. Le plugin ChatGPT n'a pas besoin d'être déconnecté.
- Le tunnel nécessite une authentification configurée localement. **Ne jamais publier ni coller de clé API dans ChatGPT ou dans ce dépôt.**
- Si le tunnel est inactif, travailler avec les sources GitHub et demander l'activation de Ghidra seulement lorsque l'analyse du binaire en a vraiment besoin.

### WSL et Ryujinx

- Dossier principal dans la configuration actuelle : /mnt/c/Jeux/Fire_Emblem_Engage/Modding/Engage_Language_Plugin
- Depuis ce dossier, **deploy.sh** compile le NRO et le déploie automatiquement dans Ryujinx. Il sauvegarde le NRO précédent sous l'extension **.bak** avant de le remplacer.
- Redémarrer Ryujinx après chaque déploiement ; transmettre le log complet et, si nécessaire, une capture ou les étapes de reproduction.
- **Attention aux modifications locales** : lors du précédent diagnostic, git status signalait des modifications de .vscode/launch.json, Cargo.lock, Cargo.toml et src/interface.rs dans le projet principal. Leur état peut avoir changé depuis. Toujours refaire git status --short et ne jamais écraser des modifications non vérifiées.
- Le dépôt suit aussi des fichiers de compilation dans target/ ; des sorties modifiées dans ce dossier ne signifient pas forcément que le code source a été modifié. Les examiner avant toute opération destructrice.

## 4. Procédure de travail convenue

**A — Cadrer.** Définir l'effet visible attendu, les langues ou situations à couvrir, le résultat à ne pas casser et les critères du test. Distinguer les contraintes essentielles des souhaits secondaires.

**B — Enquêter.** Lire d'abord le code actuel, puis la source de la dépendance ou du plugin concerné. Utiliser Ghidra pour les questions internes au jeu ou sans source. Consulter les logs pour vérifier les hypothèses. Chercher activement ce qui pourrait invalider une hypothèse avant de coder.

**C — Préparer.** Changer uniquement ce qui est nécessaire sur une branche isolée. Ajouter des logs courts et discriminants. Ouvrir une **PR en brouillon** si le code n'est ni compilé ni testé ; indiquer explicitement les risques et l'attendu du test.

**D — Tester.** L'utilisateur récupère la branche, lance deploy.sh, redémarre Ryujinx, suit un scénario de reproduction précis et envoie le résultat. Si une compilation échoue, corriger d'abord cette erreur ; si le jeu plante, analyser le journal avant de proposer une nouvelle version.

**E — Valider.** Vérifier les deux sens des transitions de langue, les textes natifs, les plugins tiers, les textes d'aide, l'absence de crash et le résultat du déploiement. Ne pas supposer qu'un scénario non testé fonctionne.

**F — Intégrer.** Lorsque la PR est validée : fusionner dans master, revenir au dossier principal, récupérer master, déployer, faire un test final depuis master. Nettoyer ensuite les éventuels worktrees de test.

**G — Documenter.** Actualiser ce fichier lors de chaque étape majeure : état, PR/commit fusionné, résultats réellement testés, nouvelles découvertes, limites et prochain sujet.

### Commandes WSL usuelles — une commande par bloc

Se placer dans le dépôt principal :

~~~bash
cd /mnt/c/Jeux/Fire_Emblem_Engage/Modding/Engage_Language_Plugin
~~~

Examiner les modifications avant une opération Git :

~~~bash
git status --short
~~~

Récupérer master **après fusion d'une PR**, si la situation locale le permet :

~~~bash
git pull
~~~

Compiler et déployer depuis le dossier actif :

~~~bash
bash deploy.sh
~~~

Pour une branche expérimentale, préférer un **git worktree séparé** lorsque le dépôt principal contient des changements locaux. Vérifier la branche et l'état Git avant de créer ou de retirer un worktree. Ne pas employer git reset --hard, git restore ou worktree remove --force sans avoir vérifié ce qui serait perdu.

## 5. Leçons de méthode : ce qu'on doit améliorer

- Ne pas confondre une fonction Rust trouvée dans les sources avec une méthode virtuelle IL2CPP accessible à l'exécution.
- Vérifier les bornes et les invariants de structure (taille vs capacité, indices, pointeurs, durée de vie des objets) **avant** le premier test.
- Préférer les mécanismes génériques ; lorsqu'une traduction dépend d'un catalogue, dire clairement qu'il s'agit d'une **couverture par données**, pas d'une traduction universelle.
- Éviter d'enchaîner des itérations de code lorsqu'une vérification dans les sources ou Ghidra pourrait lever l'incertitude en amont.
- Pour les tests, fournir le scénario précis et les traces attendues, pas seulement « essaie et dis-moi ».
- **Une commande par bloc de code** dans toutes les réponses destinées au terminal : l'utilisateur utilise la fonction Copier le code.
- Garder les réponses conversationnelles brèves, directes et en français ; limiter les comptes rendus trop longs hors demande d'audit.
- Ne jamais stocker de secrets, clés ou jetons dans la documentation, les commits ou les logs partagés.

## 6. Suite du projet

**À examiner ensuite, sans considérer ces pistes comme déjà résolues :**

- Les trois niveaux de menus (Settings, System et menu de carte) et le cartouche de chapitre ont été validés dans les scénarios testés ; étudier **d'autres interfaces persistantes** (barres, panneaux, inventaire, unités, etc.) uniquement si de nouveaux besoins apparaissent.
- Vérifier d'autres langues et scénarios sur les entrées tierces ; les catalogues prévus dans le code ne constituent pas une validation complète en jeu.
- Étendre le catalogue de textes uniquement pour les nouveaux plugins et langues dont les traductions peuvent être établies de manière fiable.
- Réduire les avertissements Rust et les traces historiques lorsque la stabilité du comportement est confirmée ; éviter le nettoyage cosmétique pendant un diagnostic fonctionnel.

## 7. Check-list de reprise

1. Vérifier la branche master, les PR ouvertes et les commits récents sur GitHub.
2. Lire ce fichier et la partie du code concernée par l'objectif du jour.
3. Demander si Ghidra/tunnel est actif **uniquement si l'analyse Ghidra est nécessaire** ; sinon continuer sur GitHub.
4. Confirmer si la tâche est investigation seule ou modification + PR.
5. Préserver les fichiers locaux, garder le travail expérimental sur une branche, donner les commandes séparément.
6. Après validation, mettre à jour le présent document pour la prochaine conversation.
