# Discord AE

Le bot du discord de l'AE

## Contribuer

Si uv n'est pas installé sur votre machine :

```shell
# Linux/MacOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Puis :

```shell
uv sync
```

Une fois les dépendances installées, copiez la configuration :

```shell
cp bot.toml.example bot.toml
```

Puis remplissez les variables manquantes.
Vous aurez notamment besoin d'un token de bot discord 
(que vous pouvez obtenir sur le portail développeurs de discord)
et d'une clef d'API pour le site AE 
(pour ça, il faut demander directement au pôle info).

Pour lancer le bot :

```shell
uv run -m src.main
```
