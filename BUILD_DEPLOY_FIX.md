# Fix pour l'action Build and Deploy #181

## Problème identifié

L'exécution du workflow "Build and Deploy" #181 a échoué lors de la tentative de publication sur PyPI.

### Analyse de l'erreur

L'action #181 a été déclenchée sur la branche `0.6.1` avec le commit `219d7b5` qui a été taggé `0.6.1`. Cependant:

1. Le fichier `pyproject.toml` contenait toujours `version = "0.6.0"`
2. Le workflow a construit la version 0.6.0 (basée sur pyproject.toml)
3. PyPI a rejeté l'upload avec une erreur HTTP 400: "File already exists"
4. La version 0.6.0 existait déjà sur PyPI depuis un déploiement précédent

### Cause racine

**Désynchronisation entre le tag Git et la version dans pyproject.toml**

Le tag Git était `0.6.1` mais le fichier `pyproject.toml` contenait `version = "0.6.0"`, causant une tentative de re-publication de la version 0.6.0 qui était déjà sur PyPI.

## Solution appliquée

### Changement effectué

Mise à jour de la version dans `pyproject.toml`:
- **Avant**: `version = "0.6.0"`
- **Après**: `version = "0.6.1"`

### Vérification

```bash
poetry build
```

Le build produit maintenant:
- `baygon-0.6.1-py3-none-any.whl`
- `baygon-0.6.1.tar.gz`

## Comment éviter ce problème à l'avenir

1. **Toujours mettre à jour la version dans pyproject.toml avant de créer un tag Git**
2. **Utiliser un outil de gestion de versions automatique** comme `poetry version` pour synchroniser les versions
3. **Ajouter une vérification dans le CI** pour s'assurer que la version dans pyproject.toml correspond au tag Git

### Script recommandé pour créer une release

```bash
# 1. Mettre à jour la version dans pyproject.toml
poetry version 0.6.1

# 2. Committer le changement
git add pyproject.toml
git commit -m "Bump version to 0.6.1"

# 3. Créer le tag
git tag 0.6.1

# 4. Pousser les changements et le tag
git push origin main
git push origin 0.6.1
```

## Résultat

Avec ce fix:
- ✅ Le build Poetry produit la version 0.6.1
- ✅ Le tag Git 0.6.1 correspond à la version dans pyproject.toml
- ✅ Le déploiement PyPI devrait réussir car la version 0.6.1 est nouvelle
