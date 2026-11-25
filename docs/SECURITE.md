# Sécurité — CityDataHub

Document de référence de la démarche sécurité du projet.
Le README du projet en donne le résumé ; ce document détaille
chaque mesure, la raison de son choix, et la vérification possible.

Auteur : Eric Diologeant — novembre 2026

## 1. Principes

Le projet repose sur quatre principes simples, appliqués de bout en bout :

1. **L'intégrité des données est exécutoire au niveau SQL** — jamais
   laissée à la seule discipline du code applicatif.
2. **Les tests ne touchent jamais la production.**
3. **Aucun secret n'est committed** dans le dépôt Git.
4. **Toute opération destructrice a une barrière de confirmation
   et un filet de sécurité.**

## 2. Intégrité des données (exécutoire en SQL)

| Mesure | Rôle | Où |
|---|---|---|
| `UNIQUE (ville, indicateur, date)` sur `mesures` | une mesure métier existe une seule fois, quel que soit le chemin d'arrivée (API, CSV, rejeu) | `sql/schema.sql` |
| `ON CONFLICT ... DO NOTHING` | les imports rejouables n'insèrent que du nouveau | `modules/stockage/stockage_postgres.py` |
| `UNIQUE (mesure_id) ... ON CONFLICT DO NOTHING` sur `alertes` | une mesure au-dessus du seuil produit exactement une alerte, jamais deux | `sql/alertes.sql` |
| Clés étrangères réelles (`alertes.mesure_id`, `alertes.indicateur_id`, `indicateurs_ref.categorie_id`) | impossible de référencer une mesure ou un indicateur inexistant | `indicateurs/models.py`, `sql/schema.sql` |

**Vérification** : un `INSERT` d'une alerte orpheline est rejeté par la
base elle-même (démonstration `demo_integration.sh`, étape 4) — la
violation de FK lève une erreur PostgreSQL, pas une exception applicative.

## 3. Isolement des environnements

- Production : `citydatahub`.
- Tests et intégration continue : `citydatahub_test`, base éphémère
  recréée à chaque session (`tests/conftest.py`).

Les tests ne peuvent donc **pas** altérer les données de production :
ils opèrent sur une autre base, au propriétaire dédié, jetée après usage.
La confusion d'environnement (le plus grand risque opérationnel d'un
projet data) est éliminée par construction.

## 4. Gestion des secrets

- **Base PostgreSQL** : pas de mot de passe dans le code ni dans un
  fichier d'environnement committed ; accès locaux à la base.
- **Publication Git** : transfert par SSH, clé privée protégée par
  **passephrase** (double facteur appliqué à Git : possession de la clé
  + connaissance du secret). Aucun identifiant ni token stocké sur la
  machine ni dans le dépôt.
- **Dépôt public** : rien dans le dépôt ne permet d'accéder à la base,
  aux APIs (publiques, sans clé) ou à GitHub.

## 5. Planification sous systemd

Les opérations planifiées (collecte 04:00, sauvegarde 03:15) tournent
sous des identités dédiées déclarées dans la configuration NixOS
(`nixos/citydatahub.nix`) — pas en root. Un service ne doit son
fonctionnement qu'à son unité : tout est déclaré, rien n'est artisanal,
et la configuration du système est versionnée avec le projet.

## 6. Réseau et pare-feu

Le pare-feu NixOS (`networking.firewall`) n'ouvre que le **port 8000**
(serveur Django), à destination du réseau local. PostgreSQL n'écoute
pas sur le réseau : rien n'expose la base au-delà de la machine.

## 7. Sauvegardes et restauration

La chaîne complète, avec ses barrières :

1. **Sauvegarde quotidienne** (`scripts/sauvegarde.sh`, timer 03:15) :
   `pg_dump -Fc` compressé, horodaté, rotation automatique à 7 jours.
2. **Contre-épreuve** (`scripts/verif_sauvegarde.sh`) : restauration
   du dernier dump dans une base jetable `citydatahub_verif`,
   comparaison des comptages table par table avec la production,
   verdict en une ligne, puis suppression de la base jetable.
   En cas d'écart : garde de la base et `exit 1` (échec visible).
3. **Restauration d'urgence** (`scripts/restore_sauvegarde.sh`) :
   opération à **double barrière** — affichage du dump et de sa
   cible, confirmation tapée au clavier (le nom exact de la base),
   dump de sécurité de l'état courant AVANT toute restauration,
   comparaison des comptages avant/après. Le repentir est toujours
   possible : le dump de sécurité horodaté à la seconde est affiché
   en fin d'opération.

Règle d'or : une sauvegarde n'est prouvée bonne qu'après avoir été
restaurée et comparée. C'est la contre-épreuve qui le fait.

## 8. Solidité applicative

- **Panne partielle tolérée** : chaque source est isolée par son
  exception dédiée (`erreur_api`, `erreur_csv`, `erreur_stockage`) ;
  une source en panne n'interrompt pas les autres, le pipeline rend
  un bilan par source et `exit 1` si échec (visible dans systemd).
- **Validation des entrées** : fichiers CSV et réponses API vérifiés
  (format, colonnes, valeurs) avant insertion ; l'URL de l'API est
  vérifiée avant requête.
- **Idempotence générale** : schéma rejouable, imports rejouables,
  détection rejouable — rejouer ne casse rien, ne double rien.

## 9. Journalisation

Chaque exécution (pipeline, sauvegarde) rend un compte rendu structuré
dans le journal systemd (`journalctl -u citydatahub-pipeline`,
`-u citydatahub-sauvegarde`) : bilan par source, nouveautés, alertes,
erreurs. La journalisation est portée par `modules/journalisation.py`,
utilisée par tous les modules.

## 10. Limites connues et pistes (honnêteté de soutenance)

- La rotation à 7 jours reste locale : une copie hors site (chiffrée)
  serait l'étape suivante.
- Le serveur Django est servi sans HTTPS sur le LAN (usage interne) ;
  un reverse proxy avec TLS serait le raffinement suivant.
- Les mises à jour système suivent le canal NixOS ; les mises à jour
  de sécurité (`nixos-rebuild switch --upgrade`) sont à cadencer.