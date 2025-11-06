#!/bin/bash
# Script interactif pour configurer les chemins des bibliothèques

echo "╔════════════════════════════════════════╗"
echo "║   CONFIGURATION DES CHEMINS            ║"
echo "╚════════════════════════════════════════╝"
echo

# Vérifier si config.yaml existe
if [ ! -f config.yaml ]; then
    echo "📄 config.yaml n'existe pas, copie depuis config.example.yaml..."
    cp config.example.yaml config.yaml
    echo "✓ config.yaml créé"
    echo
fi

echo "Chemins actuels dans config.yaml:"
echo
python3 << 'PYEOF'
import yaml

try:
    with open('config.yaml') as f:
        config = yaml.safe_load(f)
        paths = config.get('gaston', {}).get('library_paths', [])
        if paths:
            for i, path in enumerate(paths, 1):
                print(f"  {i}. {path}")
        else:
            print("  (aucun chemin configuré)")
except Exception as e:
    print(f"  Erreur: {e}")
PYEOF

echo
echo "════════════════════════════════════════"
echo

echo "Options:"
echo "  1) Ajouter un nouveau chemin"
echo "  2) Remplacer tous les chemins"
echo "  3) Afficher le config complet"
echo "  4) Quitter"
echo
read -p "Votre choix: " choice

case $choice in
    1)
        echo
        read -p "Nouveau chemin (ex: /home/user/BD): " new_path

        if [ ! -d "$new_path" ]; then
            echo "⚠️  ATTENTION: Le dossier n'existe pas encore"
            read -p "Continuer quand même ? (oui/non): " confirm
            if [ "$confirm" != "oui" ]; then
                echo "❌ Annulé"
                exit 0
            fi
        fi

        python3 << PYEOF
import yaml

with open('config.yaml') as f:
    config = yaml.safe_load(f)

if 'gaston' not in config:
    config['gaston'] = {}
if 'library_paths' not in config['gaston']:
    config['gaston']['library_paths'] = []

config['gaston']['library_paths'].append('$new_path')

with open('config.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

print(f"✅ Chemin ajouté: $new_path")
PYEOF
        ;;

    2)
        echo
        echo "Entrez les nouveaux chemins (un par ligne, ligne vide pour terminer):"

        paths=()
        while true; do
            read -p "Chemin: " path
            if [ -z "$path" ]; then
                break
            fi
            paths+=("$path")
        done

        if [ ${#paths[@]} -eq 0 ]; then
            echo "❌ Aucun chemin saisi"
            exit 0
        fi

        # Créer un fichier Python temporaire pour mettre à jour le YAML
        python3 << PYEOF
import yaml

with open('config.yaml') as f:
    config = yaml.safe_load(f)

if 'gaston' not in config:
    config['gaston'] = {}

paths = [$(printf '"%s",' "${paths[@]}" | sed 's/,$//')]
config['gaston']['library_paths'] = paths

with open('config.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

print("✅ Chemins mis à jour:")
for path in paths:
    print(f"  • {path}")
PYEOF
        ;;

    3)
        echo
        echo "════════════════════════════════════════"
        echo "Contenu de config.yaml:"
        echo "════════════════════════════════════════"
        cat config.yaml
        ;;

    4)
        echo "Au revoir !"
        exit 0
        ;;

    *)
        echo "❌ Choix invalide"
        exit 1
        ;;
esac

echo
echo "════════════════════════════════════════"
echo "✅ Configuration terminée !"
echo
echo "Pour scanner vos bibliothèques:"
echo "  ./scan_config.sh"
