# Mode opératoire — CityDataHub

Procédures d'installation, d'exploitation et de dépannage, geste par geste.
Machine de référence : `cdh2026` (NixOS 26.05), utilisateur `ericd`, projet `~/citydatahub`, PostgreSQL 18, venv Python 3.14.7.

Horizon : chaque procédure est rejouable (idempotente) et rend un verdict lisible.

---

## 1. Installation complète (machine neuve)

**Prérequis** : NixOS installé, dépôt cloné.

1. **Système** — déployer la configuration :
   ```bash
   sudo nixos-rebuild switch
   ```
   Installe et configure PostgreSQL 18 (bases `citydatahub` et `citydatahub_test`), les services ordonnés (schéma appliqué au boot), les deux timers, le pare-feu (port 8000).
   ⚠ Frictions connues : bibliothèques manquantes sous systemd → résolues par `lib.makeLibraryPath` dans `citydatahub.nix` ; version PostgreSQL unique partout (`postgresql_18`).

2. **Application** — l'environnement Python :
   ```bash
   cd ~/citydatahub
   python -m venv venv
   ./venv/bin/pip install -r requirements.txt
   ```

3. **Données + vérification** — la démonstration complète :
   ```bash
   bash scripts/demo.sh
   ```
   Enchaîne schéma → référentiels → seuil → données fictives si absentes → collecte → import → bilan SQL → tests (47 verts) → rappels du serveur.

4. **Service web** :
   ```bash
   ./venv/bin/python manage.py runserver 0.0.0.0:8000
   ```

**Verdict** : les 47 tests verts et le badge d'accueil = installation réussie.

## 2. Exploitation quotidienne (automatique)

Rien à faire — c'est le point. Vérifier seulement, pas déclencher :

```bash
systemctl list-timers | grep citydatahub        # les deux horaires
journalctl -u citydatahub-pipeline -n 20        # bilan de la collecte 04:00
ls -l backups/                                  # le dump du jour présent
```

Le timer `Persistent` rattrape un retard si la machine dormait (preuve vécue : rattrapage 24 h).

## 3.Importer un fichier CSV (administrateur)

1. Se connecter sur `/admin/` (authentification) ;
2. Suivre le lien d'import (visible uniquement connecté) ;
3. Choisir le fichier (4 colonnes : date, valeur, ville, indicateur) ;
4. Lire la page de confirmation : mesures nouvelles et alertes créées.

Chaque tentative est historisée dans la table `imports`. Rejouer le même fichier = 0 inséré (idempotence prouvée à l'échelle du million).

## 4. Sauvegarder (manuellement ou sur horloge)

```bash
bash scripts/sauvegarde.sh
```
Dump compressé horodaté dans `backups/`, rotation automatique à 7 jours. Timer systemd à 03:15 le fait chaque nuit.

## 5. Prouver une sauvegarde (la contre-épreuve)

```bash
bash scripts/verif_sauvegarde.sh
```
Restaure le dernier dump dans une base jetable, compare les comptages des six tables avec la production, rend un verdict, purge. Tout écart = base conservée + `exit 1`.

## 6. Restaurer sur la production (urgence)

```bash
bash scripts/restore_sauvegarde.sh
```
Procédure à double barrière : affichage du dump et de sa cible, **confirmation tapée au clavier** (le nom exact de la base), dump de sécurité de l'état courant AVANT l'opération, comparaison des comptages après. Un valid en fin de parcours = opération réussie.

## 7. Réinitialiser (tests et démo uniquement)

```bash
psql -d citydatahub_test -f sql/reinitialisation.sql
```
`BEGIN` + `TRUNCATE` des six tables + référentiels + `COMMIT`, `ON_ERROR_STOP`. Jamais sur la production : le `psql -d <base>` explicite est le garde-fou.

## 8. Dérouler la démonstration du système

```bash
bash scripts/demo.sh                 # le produit de bout en bout
bash scripts/demo_integration.sh     # les preuves d'intégration (5 propriétés)
```
Deux exécutions de suite = plateau identique aux bilans près (l'idempotence se démontre, pas seulement se déclare).

## 9. Ajouter une source de données

1. **Extracteur** (`modules/sources/extracteurs.py`) : une fonction de parsing vers le format commun (le vrai travail — le monde extérieur se paie ici) ;
2. **Registre** (`modules/sources/fournisseurs.py**) : la ligne `FOURNISSEURS`/`COMBINAISONS` correspondante ;
3. **Référentiel** (`sql/referentiels.sql`) : la ligne de l'indicateur (unité, catégorie) et celle de la source, avec `ON CONFLICT DO NOTHING`, puis l'exécuter sur les deux bases ;
4. **Seuil** sur `/admin/` si la donnée doit générer des alertes (sans seuil, détection silencieusement ignorée — découplage voulu) ;
5. **Test** dans `tests/test_extracteurs.py`.

Le pipeline, le formulaire Django et le timer s'adaptent seuls : aucun changement ailleurs.

## 10. Dépannage (diagnostic par symptôme)

| Symptôme | Première action |
|---|---|
| Le run échoue sous systemd mais marche en shell | L'environnement du service est stérile : vérifier l'unité (`path`, `LD_LIBRARY_PATH`) — *un service ne doit son fonctionnement qu'à son unité* |
| Le test tourne « bizarrement » | Vérifier `current_database()` — le shell `PGDATABASE` peut dévier l'appel (corrigé : un paramètre explicite prime) |
| Le badge dit N alertes, la page est vide | Croiser le log d'écriture avec un `count` SQL — toujours |
| Le LAN n'atteint pas le site | Diagnostic en étages : `ss` (écoute) → `iptables nixos-fw` (pare-feu) → `ALLOWED_HOSTS` (hôte) → `ping` vs `curl` (réseau vs appli) ; forcer `http://` explicite (piège HTTPS du navigateur) |
| Le build Nix échoue avec un caractère invisible | `grep '[^ -~\t]'` — chaînes en ASCII strict |
| Une mesure entre mais n'apparaît nulle part | Vérifier le JOIN par nom : casse ou accent différent du référentiel |

## 11. Règles de sécurité à respecter en toutes circonstances

- Les tests ne touchent jamais la production (`citydatahub_test`, garde-fou `current_database() endswith '_test'`) ;
- Aucun secret dans le dépôt (SSH, clé protégée par passephrase) ;
- Toute opération destructive a une barrière (confirmation) et un filet (dump de sécurité) ;
- Une sauvegarde n'est prouvée bonne qu'après avoir été restaurée et comparée.
