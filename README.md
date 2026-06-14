# Zero Parades — Traduction Française 🕵️

> Fan translation non-officielle · 69 944 lignes · IA (Claude Haiku) · Installation 1 clic

---

## 📥 Obtenir la traduction (version prête à l'emploi)

**→ [Télécharger sur netroia.tech](https://netroia.tech)**

Le pack contient le fichier de traduction pré-appliqué + l'installateur automatique.  
Aucune compétence technique requise — double-clic et c'est installé.

---

## ⚠️ Important — Activation dans le jeu

La traduction FR remplace le slot **"Allemand"** dans le jeu.

**Dans le jeu : Paramètres → Langue → sélectionner "Allemand (German)"**  
→ Le jeu s'affiche entièrement en français ✅

---

## 🛠️ Pour les développeurs — Créer votre propre traduction

Ce repo contient le toolkit complet pour traduire Zero Parades dans n'importe quelle langue.

### Prérequis
```bash
pip install -r requirements.txt
```

### Pipeline complet
```bash
# 1. Extraire le texte du jeu
python bundle_to_po.py --bundle "path/to/game.bundle" --lang de --output source.po

# 2. Traduire via Claude Haiku (moins cher)
export ANTHROPIC_API_KEY=sk-ant-...
python translate_po_claude.py --input source.po --output translated.po --target-lang French --source-lang de

# 3. Injecter dans le jeu
python po_to_bundle.py --bundle "path/to/game.bundle" --po translated.po --lang-name fr
```

### Mise à jour après patch du jeu
```bash
python refresh_po.py --input nouvelle_reference.po --output translated.po
# Puis relancer translate_po_claude.py pour traduire uniquement les nouvelles entrées
```

---

## 📊 Statistiques de la traduction FR

| Info | Détail |
|------|--------|
| Volume | 69 944 entrées |
| Source | Allemand (DE) |
| Cible | Français (FR) |
| Modèle IA | Claude Haiku 4.5 |
| Durée | ~6-8h (parallel=3) |
| Coût | ~$20-25 API |

---

## 📁 Fichiers

| Fichier | Rôle |
|---------|------|
| `bundle_to_po.py` | Extraction bundle Unity → .po |
| `translate_po_claude.py` | Traduction via Claude API (Haiku) |
| `po_to_bundle.py` | Réinjection .po → bundle Unity |
| `refresh_po.py` | Fusion nouvelles entrées après patch |
| `language_codes.py` | Codes de langue FELD Engine |
| `llm_translation_context.md` | Contexte jeu injecté dans chaque appel LLM |
| `install.bat` | Installateur automatique (utilisateurs finaux) |

---

## ❤️ Soutenir

Si ce projet vous a plu : **[netroia.tech](https://netroia.tech)**  
TikTok : [@captainNetroia](https://tiktok.com/@captainnetroia)

---

*Fan project — Zero Parades est une propriété de ZAUM Studio. Aucune affiliation officielle.*
