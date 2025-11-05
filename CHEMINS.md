# Comment configurer les chemins vers vos BD

Il y a **3 façons** de spécifier où se trouvent vos BD.

## 🎯 Méthode 1: Script interactif (RECOMMANDÉ)

Le plus simple, utilisez le script de configuration:

```bash
./configure_paths.sh
```

Ce script vous permet de:
- Voir les chemins actuels
- Ajouter un nouveau chemin
- Remplacer tous les chemins

**Exemple:**
```bash
./configure_paths.sh
# Choisir option 2 (Remplacer tous les chemins)
# Entrer: /home/guillaume/Documents/BD
# Entrer: /home/guillaume/Downloads/Comics
# Ligne vide pour terminer
```

Ensuite, scannez avec:
```bash
./scan_config.sh
```

## 📝 Méthode 2: Éditer config.yaml manuellement

Éditez directement le fichier de configuration:

```bash
nano config.yaml
```

Modifiez la section `library_paths`:

```yaml
gaston:
  library_paths:
    - /home/guillaume/Documents/BD
    - /home/guillaume/Documents/Comics
    - /media/usb/Manga
```

**Important**: Utilisez des chemins absolus (complets), pas relatifs.

Ensuite, scannez avec:
```bash
./scan_config.sh
```

## 🚀 Méthode 3: Passer le chemin en paramètre

Pour un scan ponctuel sans modifier la config:

```bash
./scan_all.sh 8080 /chemin/vers/dossier
```

**Exemples:**
```bash
# Scanner un dossier spécifique
./scan_all.sh 8080 /home/guillaume/Documents/BD

# Scanner depuis une clé USB
./scan_all.sh 8080 /media/usb/Comics

# Scanner le dossier de test (par défaut)
./scan_all.sh
```

## 📂 Où sont vos BD ?

Pour trouver vos dossiers de BD:

```bash
# Lister vos dossiers Documents
ls -la ~/Documents

# Chercher les dossiers contenant "BD" ou "Comic"
find ~ -type d -iname "*bd*" -o -iname "*comic*" 2>/dev/null

# Voir les disques montés
df -h
```

## ✅ Workflow complet

### Option A: Avec config.yaml

```bash
# 1. Configurer les chemins
./configure_paths.sh

# 2. Scanner tous les dossiers configurés
./scan_config.sh

# 3. Enrichir les métadonnées
./enrich_all.sh

# 4. Vérifier le résultat
./status.sh
```

### Option B: Sans config.yaml

```bash
# Scanner directement un dossier
./scan_all.sh 8080 /home/guillaume/Documents/BD

# Enrichir
./enrich_all.sh

# Vérifier
./status.sh
```

## 🔍 Vérifier la configuration actuelle

```bash
# Voir les chemins configurés
grep -A 5 "library_paths:" config.yaml

# Ou avec le script de configuration
./configure_paths.sh
# Choisir option 3 (Afficher le config complet)
```

## ⚙️ Configuration actuelle

Actuellement, votre `config.yaml` contient:

```yaml
library_paths:
  - /mnt/nas/BD
  - /mnt/nas/Comics
  - /mnt/nas/Manga
```

Ces chemins sont des **exemples**. Vous devez les remplacer par vos vrais chemins.

## 📋 Exemples de chemins courants

**Linux:**
```yaml
library_paths:
  - /home/votre_nom/Documents/BD
  - /media/votre_nom/USB_Drive/Comics
  - /mnt/nas/Manga
```

**Dossier actuel (test):**
```yaml
library_paths:
  - /home/guillaume/work/Gaston/bd_sample
```

## 🐛 Problèmes courants

### "Le dossier n'existe pas"

Vérifiez que le chemin est correct:
```bash
ls -la /votre/chemin/vers/BD
```

### "Permission denied"

Vérifiez les permissions:
```bash
# Voir les permissions
ls -ld /votre/chemin/vers/BD

# Donner les permissions si nécessaire
chmod 755 /votre/chemin/vers/BD
```

### "Aucun fichier trouvé"

Vérifiez que le dossier contient des fichiers supportés:
```bash
# Lister les fichiers BD
find /votre/chemin -type f \( -name "*.cbz" -o -name "*.cbr" -o -name "*.pdf" -o -name "*.epub" \)
```

## 📊 Extensions supportées

Gaston supporte les formats suivants:
- `.cbz` (Comic Book ZIP)
- `.cbr` (Comic Book RAR)
- `.pdf` (Portable Document Format)
- `.epub` (Electronic Publication)

## 🎯 Résumé

**Pour commencer rapidement:**

1. **Configurer:**
   ```bash
   ./configure_paths.sh
   ```

2. **Scanner:**
   ```bash
   ./scan_config.sh
   ```

3. **Enrichir:**
   ```bash
   ./enrich_all.sh
   ```

4. **Vérifier:**
   ```bash
   ./status.sh
   ```

C'est tout ! 🎉
