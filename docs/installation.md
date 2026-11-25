# Installation depuis zéro — CityDataHub

Dossier projet : monter l'application complète sur une machine vierge, du bare metal au service web, avec vérification à chaque étape.

Machine cible : « cdh2026 » (VM 1 processeur / 4 cœurs, 8 Go de RAM, 60 Go de disque), NixOS 26.05, PostgreSQL 18, Python 3.14.7 en venv. Ubuntu n'est plus en jeu depuis le changement de système en S1 : tout l'OS est déclaré par NixOS.

Ces caractéristiques tiennent la charge démontrée : l'import de 2,4 millions de lignes à ~24 000-lignes/s et les tests de bout en bout ont tourné sur cette configuration, mémoire constante par construction (traitement par lots de 10 000).

---

## 0. Prérequis à réunir avant de commencer

- Une machine ou VM vierge (aucune trace d'un PostgreSQL antérieur — une version qui traîne est le premier risque d'installation) ;
- L'image ISO NixOS 26.05 ;
- Un terminal et un navigateur : tout se fait en console et en web, aucun autre outil ;
- Le dépôt GitHub accessible (clé SSH déjà générée et enregistrée sur le compte — la clé protégée par passphrase, jamais de secret dans le dépôt) ;
- Réseau local fonctionnel pour les APIs publiques et le Git.

## 1. Créer la VM (VMware Workstation)

1. **Télécharger l'ISO** : NixOS x86_64 depuis nixos.org (image GNOME ou minimal), vérifier la somme `sha256sum` publiée ;
2. **Create a New Virtual Machine → Typical**, disque ISO en source. VMware détecte « Other Linux 5.x kernel 64-bit » : c'est normal. Nom : la machine du projet ;
3. **Customize Hardware avant de finir** : 8192 Mo de mémoire, 4 cœurs, disque **60 Go en fichier unique**, CD/DVD sur l'ISO, réseau **NAT** ;
4. Power on : au menu GRUB, choisir l'installateur (ou prompt `nixos@nixos` = live chargé).

## 2. Installer NixOS (le live)

1. **Passer root** (`sudo -i`), **clavier FR** (`loadkeys fr`), **réseau vérifié** (`ip a` puis `ping -c 3 nixos.org`, `dhclient` si besoin) ;
2. **Activer SSH dans le live** (pratique pour coller les commandes depuis l'hôte) : `passwd root` puis `systemctl start sshd` ;
3. **Partitionner** — détecter d'abord le mode : `ls /sys/firmware/efi/efivars` existe → UEFI (recommandé, VMware réglé en UEFI) ; erreur → BIOS legacy.

   **Version UEFI (celle utilisée)** :
   ```bash
   lsblk                                   # identifier le disque (/dev/sda)
   parted /dev/sda -- mklabel gpt
   parted /dev/sda -- mkpart primary 512MiB -8MiB   # racine
   parted /dev/sda -- mkpart ESP fat32 1MiB 512MiB   # boot EFI
   parted /dev/sda -- set 2 esp on
   mkfs.ext4 -L nixos /dev/sda1
   mkfs.fat -F 32 -n boot /dev/sda2
   ```
   *(Variante BIOS legacy : `mklabel msdos`, partition bootable simple.)*

4. **Monter par label et générer la configuration** :
   ```bash
   mount /dev/disk/by-label/nixos /mnt
   mkdir -p /mnt/boot && mount /dev/disk/by-label/boot /mnt/boot
   nixos-generate-config --root /mnt
   ```
   Deux fichiers naissent : `configuration.nix` (à éditer, cœur du système) et `hardware-configuration.nix` (généré, ne jamais l'éditer à la main — UUID du disque) ;
5. **Éditer `/mnt/etc/nixos/configuration.nix`** : hostname, fuseau `Europe/Paris`, locales FR, l'utilisateur (`wheel`, mot de passe à changer au premier login), SSH, pare-feu, PostgreSQL et les paquets Python. *C'est ce fichier, versionné, qui sera remplacé par celui du dépôt sur une machine neuve* ;
6. **Installer** : `nixos-install` (demande le mot de passe root à la fin), **détacher l'ISO** dans VMware (sinon reboucle sur le live), `reboot`.

**Vérification** : au redémarrage, `login` utilisateur fonctionne, `passwd` pour changer le mot de passe initial, puis `nixos-version`, `git --version`, `python3 -c "import pandas; print('ok')"`, `systemctl status postgresql`.

## 3. Récupérer le dépôt et déployer le système déclaré

Le projet embarque déjà toute sa configuration système :

```bash
git clone git@github.com:ExpertAsAService/citydatahub.git
cd citydatahub
sudo cp nixos/configuration.nix /etc/nixos/configuration.nix
sudo cp nixos/citydatahub.nix /etc/nixos/
sudo nixos-rebuild switch
```

`nixos-rebuild switch` installe et configure en une commande :

- **PostgreSQL 18** (version unique alignée partout, un seul alias de paquet dans la configuration), bases `citydatahub` et `citydatahub_test` créées, propriétaire `ericd` ;
- **Les services ordonnés** appliquent le schéma (schéma idempotent) ;
- **Les deux timers systemd** : pipeline de collecte (04:00) et sauvegarde `pg_dump` (03:15), `Persistent = true` — la machine peut dormir, la nuit est rattrapée ;
- **Le pare-feu** : port 8000 ouvert uniquement (le LAN voit le site, rien d'autre).

**Vérifications** après rebuild :

```bash
psql -d citydatahub -c "\dt"       # les six tables + tables cadre Django existent
systemctl list-timers | grep citydatahub   # deux horaires visibles
```

## 4. Poser l'environnement Python

```bash
cd ~/citydatahub
python -m venv venv
./venv/bin/pip install -r requirements.txt
```

**Vérification** : `./venv/bin/python -c "import django, pandas, sqlalchemy; print(django.get_version())"` affiche 6.1.2.

## 5. Schéma, référentiels et données : `demo.sh`

Une seule commande enchaîne tout le cycle de vie de la base :

```bash
bash scripts/demo.sh
```

Déroulé : schéma SQL → référentiels (`ON CONFLICT DO NOTHING`, rejouable) → seuil d'admin → données fictives (générées si absentes) → collecte des trois sources API + import CSV → bilan SQL GROUP BY → 47 tests verts → rappel du serveur web et du LAN.

**Vérification** : les 47 tests verts ; le bilan affiche 2,4 millions de mesures, 74 doublons absorbés, idempotence prouvée.

## 6. Créer l'administrateur du site

Le formulaire d'import ne trouve son lien que chez un utilisateur authentifié :

```bash
./venv/bin/python manage.py createsuperuser
```

(`utilisateur admin`, mot de passe en coffre-fort, jamais dans le dépôt.)

## 7. Lancer le serveur web et l'ouvrir

```bash
./venv/bin/python manage.py runserver 0.0.0.0:8000
```

**Vérification** : `http://cdh2026:8000` ou l'IP LAN — la page d'accueil montre le badge de mesure totale, les dashboards répondent, `/admin/` s'ouvre. En cas de blocage LAN, le diagnostic en cascade : écoute (`ss -tlnp`) → pare-feu (`sudo iptables -L nixos-fw -n`) → `ALLOWED_HOSTS`.

## 8. Feuille de route du premier tour de l'application

1. Accueil anonyme : pages mesures et alertes, graphiques Chart.js ;
2. `/admin/` → se connecter → changer un seuil -> le badge change après relance ;
3. Import d'un CSV de test → confirmation chiffrée, rejeu = 0 inséré ;
4. Laisser la nuit passer : `journalctl -u citydatahub-pipeline` raconte la collecte, `backups/` contient le dump du jour, `verif_sauvegarde.sh` rend son verdict.

## 9. Dépanner d'urgence

| Symptôme | Le geste |
|---|---|
| `nixos-rebuild` échoue sur un caractère invisible | `grep '[^ -~\t]'` — chaînes ASCII strictes |
| Le service échoue en systemd mais pas en shell | vérifier l'unité environnement : `path`, `LD_LIBRARY_PATH` |
| Le test frôle une base inattendue | vérifier `current_database()` — jamais la prod en test |
| Un souci d'accès Git | la passphrase SSH est demandée en local ; aucun secret dans le dépôt |

## 10. Ce qui n'est pas couvert ici

Le dépôt (et ce dossier) n'installe pas : le routeur LAN, la redirection HTTPS (usage interne, pas de TLS), ni la supervision externe. Chaque ajout se pose dans NixOS (déclaratif) ou dans `scripts/` — jamais à la main sur la machine : ce qui n'est pas écrit n'est pas reproductible.