# Security Policy — SOC-AI

## Supported versions

| Version | Support |
|---------|---------|
| 1.x (main) | ✅ Active |
| dev branch | ⚠️ Development only |

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.
Send a private report to: **security@your-org.example** (or open a
[GitHub Security Advisory](https://github.com/your-org/soc-ai/security/advisories/new)).

We aim to acknowledge within 48h and patch within 7 days for critical issues.

---

## RGPD / PII — Traitement des données personnelles

### Nature des données traitées
Les logs de sécurité peuvent contenir des **données personnelles** au sens du RGPD :
adresses IP (données personnelles selon la CJUE), noms d'utilisateurs, adresses email.

### Mesures techniques mises en œuvre

#### 1. Anonymisation avant LLM cloud (`ANONYMIZE_PII=true`)
Lorsque `ANONYMIZE_PII=true` (valeur par défaut), le module `llm_agent` remplace
toute PII détectée par des jetons neutres **avant** d'envoyer le contexte au LLM :

| Original | Token envoyé au LLM |
|----------|---------------------|
| `192.168.1.45` | `IP_1` |
| `jdupont` | `USER_1` |
| `j.dupont@corp.fr` | `EMAIL_1` |

La table de correspondance (`pii_mapping`) reste strictement locale (SQLite on-premise).

> ⚠️ **Pour les logs contenant des données sensibles, utilisez Ollama en local**
> (`LLM_BACKEND=ollama`). Aucune donnée ne quitte alors votre infrastructure.

#### 2. Rétention configurable
La variable `RETENTION_DAYS` (défaut : 90 jours) contrôle la durée de conservation
des événements et triages. Un job de purge automatique supprime les données expirées.

#### 3. Stockage local uniquement
Toutes les données (logs bruts, alertes, triage) sont stockées dans une base SQLite
locale. Aucune télémétrie n'est envoyée par SOC-AI.

### Recommandations de déploiement

- Déployez SOC-AI **on-premise** ou dans un cloud souverain (OVHcloud, Scaleway).
- Chiffrez le volume Docker contenant `soc.db` (LUKS, dm-crypt, ou équivalent).
- Restreignez l'accès réseau au dashboard (`:3000`) et à l'API (`:8000`) par pare-feu.
- Utilisez **Ollama** (`LLM_BACKEND=ollama`) pour tout environnement traitant des PII.
- Réalisez une **DPIA** (analyse d'impact) avant déploiement en production (art. 35 RGPD).
- Configurez `RETENTION_DAYS` selon votre politique interne (max 90j recommandé).
- Ne commettez **jamais** le fichier `.env` contenant votre `ANTHROPIC_API_KEY`.

### Base légale
Le traitement des logs de sécurité peut reposer sur l'**intérêt légitime** (art. 6.1.f RGPD)
de l'organisation à protéger ses systèmes d'information, sous réserve d'une mise en balance
documentée et d'une information des personnes concernées (mention dans la politique de sécurité SI).

---

## Bonnes pratiques de déploiement général

- Gardez Docker, Python et les dépendances à jour.
- Ne pas exposer l'API (`:8000`) directement sur Internet sans authentification.
- Auditez régulièrement les accès à la base SQLite (`soc.db`).
- Activez les journaux Docker et centralisez-les si possible.
