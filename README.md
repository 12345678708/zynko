# Zynko — Aperçu et améliorations

J'ai appliqué plusieurs améliorations sur la branche `refactor/clean-flask-app`. Tu peux voir la branche ici:

https://github.com/12345678708/zynko/tree/refactor%2Fclean-flask-app

Principales améliorations ajoutées:
- sanitize_path() : corrige automatiquement les URLs contenant des guillemets encodés (%22) et redirige proprement.
- favicon/protection : route /favicon.ico renvoie un SVG temporaire ; icônes PWA ajoutées (SVG) et manifest mis à jour.
- service worker basique pour mise en cache offline de ressources statiques.
- logging basique + /health endpoint + handlers 404/500 pour diagnostics.
- dashboard et styles nettoyés (suppression de séquences littérales indésirables).

Aperçu rapide (ce que tu dois tester après merge/déploiement):
1. Ouvrir la page principale: https://zynko.onrender.com
2. Aller sur le dashboard (connexion nécessaire) et vérifier que les textes s'affichent correctement.
3. Cliquer sur "Se déconnecter" — l'URL doit être `/logout` (pas /%22/logout/%22).
4. Visiter `/"/logout/"` ou `/%%22/logout/%%22` — tu devrais être redirigé vers `/logout`.
5. Vérifier `/favicon.ico` (affiche le SVG temporaire).
6. Vérifier `/health` retourne `{"status":"ok"}`.

Prochaine étape recommandée:
- Merger la branche vers `main` (ou la branche déployée) pour appliquer en production. Si tu veux que je merge, dis "oui, merge maintenant".
- Remplacer les icônes SVG par PNG/ICO optimisés si tu veux compatibilité maximale.

Si tu veux, je peux aussi :
- ajouter des tests unitaires basiques,
- configurer un serveur TURN pour WebRTC,
- améliorer l'UI du dashboard (thèmes, responsive),
- activer CI pour vérifier lint/tests avant merge.
