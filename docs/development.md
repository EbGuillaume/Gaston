# Guide de Développement - Gaston

## Installation pour le développement

### Prérequis
- Python 3.10+
- pip
- virtualenv (recommandé)

### Installation

1. **Cloner le repository**
```bash
git clone https://github.com/EbGuillaume/Gaston.git
cd Gaston
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Installer les dépendances**
```bash
pip install -r requirements-dev.txt
pip install -e .
```

4. **Installer les hooks pre-commit**
```bash
pre-commit install
```

5. **Initialiser la base de données**
```bash
gaston init
```

## Lancer l'application

### Mode développement (avec auto-reload)
```bash
gaston dev
```

### Mode production
```bash
gaston start
```

L'application sera accessible sur http://127.0.0.1:8080

## Tests

### Lancer tous les tests
```bash
pytest
```

### Lancer les tests avec coverage
```bash
pytest --cov=backend --cov-report=html
```

### Lancer un fichier de test spécifique
```bash
pytest tests/unit/test_scanner.py
```

## Structure du projet

```
gaston/
├── backend/           # Code backend Python
│   ├── api/          # Endpoints FastAPI
│   ├── core/         # Logique métier principale
│   ├── database/     # Modèles et CRUD
│   ├── utils/        # Utilitaires
│   └── config.py     # Configuration
├── tests/            # Tests unitaires et d'intégration
├── docs/             # Documentation
└── scripts/          # Scripts utilitaires
```

## Workflow de développement

1. Créer une branche depuis `develop`
```bash
git checkout develop
git pull origin develop
git checkout -b feature/votre-feature
```

2. Développer et tester

3. Committer les changements
```bash
git add .
git commit -m "feat: description de la feature"
```

4. Pousser et créer une PR vers `develop`
```bash
git push -u origin feature/votre-feature
```

## Conventions

### Code Style
- Python: PEP 8 (appliqué par Black)
- Longueur de ligne: 100 caractères
- Imports triés avec isort

### Commits
Format: `type: description`

Types:
- `feat`: Nouvelle fonctionnalité
- `fix`: Correction de bug
- `docs`: Documentation
- `test`: Tests
- `refactor`: Refactoring
- `style`: Formatage
- `chore`: Tâches de maintenance

## Configuration

Copier `config.example.yaml` vers `config.yaml` et adapter à vos besoins.

## Variables d'environnement

Créer un fichier `.env` à la racine:
```
DATABASE_URL=sqlite:///./gaston.db
DEBUG=true
```

## Dépannage

### Problèmes d'installation
- Vérifier la version de Python: `python --version`
- Mettre à jour pip: `pip install --upgrade pip`

### Tests échouent
- Vérifier que toutes les dépendances sont installées
- Vérifier que la base de données de test est accessible

## Ressources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pytest Documentation](https://docs.pytest.org/)
