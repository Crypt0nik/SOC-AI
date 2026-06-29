


SOC-AI
Security Operations Center propulsé par l'Intelligence Artificielle



CAHIER DES CHARGES TECHNIQUE
Document de référence — Projet open source B3 Cybersécurité



Champ
Valeur
Projet
SOC-AI v1.0
Type
Open Source — Licence MIT
Auteurs
Étudiants B3 Cybersécurité — Ynov Sophia Antipolis
Encadrement
J. Catena — QuantumCatena
Version
1.0 — Juin 2026
Durée de réalisation
2 jours (Sprint intensif)
Cible GitHub
github.com/<org>/soc-ai

1. Présentation du projet
1.1 Contexte et problématique
Les équipes SOC (Security Operations Center) des PME et ETI sont confrontées à un volume d'alertes de sécurité croissant — des centaines à des milliers par jour — dont la grande majorité sont des faux positifs. Le triage manuel est coûteux, lent, et épuisant pour les analystes.

SOC-AI propose une solution open source, légère et déployable en moins de 5 minutes, qui automatise le premier niveau de triage en s'appuyant sur un Large Language Model (LLM) pour qualifier chaque alerte avec un niveau de criticité, un type d'attaque identifié et une recommandation d'action.

1.2 Objectifs
Objectif 1 — Réduire le bruit d'alertes (noise reduction) en automatisant le triage L1
Objectif 2 — Fournir un dashboard web temps réel consultable sans formation spécialisée
Objectif 3 — Proposer une architecture Docker 100% portable et déployable on-premise ou cloud
Objectif 4 — Respecter les standards industrie : règles Sigma, framework MITRE ATT&CK
Objectif 5 — Produire un projet GitHub professionnel, présentable en entretien et commercialisable

1.3 Périmètre
IN SCOPE — Ce que couvre la v1.0
• Ingestion de logs SSH, Apache/Nginx, Windows Event Log (formats standard)
• Détection par règles Sigma (10 règles minimum : brute force, scan, escalade...)
• Triage automatique via LLM (Claude API ou Ollama local)
• Dashboard web : liste alertes, criticité colorée, détail LLM
• Persistence SQLite + export JSON
• Déploiement complet via Docker Compose
• README professionnel avec démo GIF et architecture diagram

OUT OF SCOPE — Hors v1.0 (roadmap future)
• Connecteur SIEM (Splunk, Microsoft Sentinel, Elastic)
• Authentification multi-utilisateurs
• Corrélation d'événements temporelle avancée
• Agent de réponse automatique (blocage IP, quarantaine)
• Intégration SOAR

2. Architecture technique
2.1 Vue d'ensemble
L'architecture est composée de 4 modules indépendants communicant via une base SQLite centrale. Chaque module est conteneurisé et orchestré par Docker Compose.

Pipeline de traitement — Flux de données

  [Sources de logs]  →  [Parser Python]  →  [Sigma Engine]  →  [LLM Triage Agent]
       SSH / Apache / Windows Event              Détection               Qualification

                                                     ↓
                                              [SQLite DB]
                                                     ↓
                                        [Dashboard Web FastAPI]
                                       Alertes • Criticité • Recommandations


2.2 Stack technologique
Module
Technologie
Justification
Ingestion logs
Python 3.11 + Watchdog
Surveillance filesystem temps réel
Parsing
Python + regex / PyYAML
Flexibilité, formats standards
Détection
Sigma rules (YAML) + pySigma
Standard industrie, compatible SIEM
Triage LLM
Claude API (Sonnet) ou Ollama
Option cloud + option offline
Base de données
SQLite 3
Zéro configuration, portable
API backend
FastAPI (Python)
Async, OpenAPI auto-généré
Dashboard frontend
React + TailwindCSS
Moderne, responsive
Conteneurisation
Docker + Docker Compose
Déploiement 1 commande
CI/CD
GitHub Actions
Tests auto + badge Build

2.3 Structure du repository GitHub
Arborescence cible — github.com/<org>/soc-ai

  soc-ai/
  ├── docker-compose.yml          # Orchestration complète
  ├── README.md                   # Documentation principale
  ├── CONTRIBUTING.md             # Guide de contribution
  ├── SECURITY.md                 # Politique de sécurité
  ├── LICENSE                     # MIT
  ├── .github/workflows/          # GitHub Actions CI
  ├── parser/                     # Module d'ingestion
  │   ├── Dockerfile
  │   ├── parser.py
  │   └── formats/                # Parsers SSH, Apache, WinEvent
  ├── engine/                     # Sigma detection engine
  │   ├── Dockerfile
  │   ├── engine.py
  │   └── rules/                  # Fichiers .yml Sigma
  ├── llm_agent/                  # Module triage LLM
  │   ├── Dockerfile
  │   ├── agent.py
  │   └── prompts/                # Prompt templates
  ├── api/                        # FastAPI backend
  │   ├── Dockerfile
  │   └── main.py
  └── dashboard/                  # React frontend
      ├── Dockerfile
      └── src/


3. Spécifications fonctionnelles
3.1 Module Parser — Ingestion des logs
3.1.1 Formats supportés (v1.0)
SSH auth logs — /var/log/auth.log (Linux)
Apache/Nginx access & error logs
Windows Event Log — format XML exporté (Security, System)
Logs génériques JSON ligne par ligne

3.1.2 Comportement attendu
Le parser surveille un répertoire /logs en temps réel (inotify)
Chaque nouvelle ligne est parsée vers un objet Event normalisé
L'objet Event contient : timestamp, source_ip, user, action, raw_log, source_type
L'Event est poussé dans la table events de SQLite

3.2 Module Sigma Engine — Détection
3.2.1 Règles Sigma minimales à implémenter
ID Règle
Nom
Criticité
SSH-001
Brute Force SSH (> 5 échecs / 60s)
HIGH
SSH-002
Connexion root directe SSH
HIGH
SSH-003
Connexion depuis IP inconnue hors plage
MEDIUM
WEB-001
SQL Injection pattern en URL
HIGH
WEB-002
Path traversal (../)
MEDIUM
WEB-003
Scanner HTTP détecté (User-Agent)
LOW
WIN-001
Escalade de privilèges Windows (Event 4672)
CRITICAL
WIN-002
Création de compte (Event 4720)
MEDIUM
WIN-003
Accès SAM registry
CRITICAL
NET-001
Port scan (> 20 ports / 5s)
HIGH

3.3 Module LLM Triage Agent
3.3.1 Input / Output
Pour chaque alerte déclenchée par le Sigma Engine, le LLM Agent reçoit un contexte structuré et retourne un JSON normalisé.

Prompt System — Template de triage LLM

  System: You are a senior SOC analyst. Analyze the security alert below and
  return ONLY a valid JSON object with these fields:
  - severity: CRITICAL | HIGH | MEDIUM | LOW | INFO
  - attack_type: (string, MITRE ATT&CK technique name if applicable)
  - mitre_id: (string, e.g. T1110.001 or null)
  - confidence: (integer 0-100)
  - summary: (string, max 2 sentences in French)
  - recommendation: (string, concrete action, max 2 sentences in French)
  - false_positive_risk: LOW | MEDIUM | HIGH

  User: [Contexte de l'alerte : règle Sigma déclenchée, log brut, IP source, timestamp]


3.3.2 Exemple de réponse attendue
Output JSON — Exemple alerte brute force SSH

  {
    "severity": "HIGH",
    "attack_type": "Brute Force SSH",
    "mitre_id": "T1110.001",
    "confidence": 92,
    "summary": "Tentative de brute force SSH détectée depuis 192.168.1.45.
                27 tentatives d'authentification échouées en 45 secondes.",
    "recommendation": "Bloquer immédiatement l'IP 192.168.1.45 via iptables.
                       Vérifier les logs des 6 dernières heures pour cette source.",
    "false_positive_risk": "LOW"
  }


3.4 Dashboard Web
3.4.1 Vues requises
Vue principale — Liste des alertes paginée, triée par timestamp desc
Filtre par severity (CRITICAL / HIGH / MEDIUM / LOW)
Détail alerte — Affichage complet du triage LLM + log brut
Compteurs en temps réel — Nombre d'alertes par severity (dernières 24h)
Export — Bouton export JSON de toutes les alertes filtrées

3.4.2 Codes couleur severity
Severity
Couleur
Action recommandée
CRITICAL
#FF0000 — Rouge vif
Intervention immédiate < 15 min
HIGH
#FF6600 — Orange
Traitement dans l'heure
MEDIUM
#FFB300 — Ambre
Traitement dans la journée
LOW
#0066CC — Bleu
Revue hebdomadaire
INFO
#666666 — Gris
Archivage, pas d'action

4. Planning de réalisation — Sprint 2 jours
Jour 1 — Backend & moteur de détection
Créneau
Tâche
Livrable attendu
9h00 – 9h30
Setup GitHub repo + structure + README squelette
Repo public créé, branches main/dev
9h30 – 11h00
Module Parser — SSH + Apache
parser.py fonctionnel, tests unitaires
11h00 – 12h30
Sigma Engine — 5 premières règles
engine.py + rules/ SSH-001 à WEB-001
12h30 – 13h30
Pause
13h30 – 15h30
LLM Triage Agent — intégration Claude API
agent.py + prompt + JSON valide
15h30 – 17h00
FastAPI backend — endpoints /alerts /stats
API testable via curl / Postman
17h00 – 18h00
Docker Compose — parser + engine + agent + api
docker-compose up fonctionnel

Jour 2 — Dashboard, polish & livraison
Créneau
Tâche
Livrable attendu
9h00 – 11h00
Dashboard React — liste alertes + couleurs severity
Dashboard fonctionnel connecté à l'API
11h00 – 12h30
Dashboard — vue détail + filtres + compteurs
Dashboard complet responsive
12h30 – 13h30
Pause
13h30 – 14h30
5 règles Sigma supplémentaires (WIN + NET)
10 règles totales opérationnelles
14h30 – 16h00
README professionnel + architecture diagram + GIF démo
README niveau production
16h00 – 17h00
CONTRIBUTING.md + SECURITY.md + LICENSE MIT
Repo 100% prêt open source
17h00 – 18h00
Tests end-to-end + push final + présentation
GitHub public finalisé

5. Exigences qualité GitHub
5.1 README.md — Structure obligatoire
Badges : Build CI, License MIT, Python version, Docker
Screenshot du dashboard (PNG haute résolution)
GIF de démo animée du triage LLM en action (outil : Asciinema ou Terminalizer)
Section Quick Start : git clone && docker-compose up en moins de 5 lignes
Architecture diagram (Mermaid ou image PNG)
Section Features avec liste des capacités
Section Roadmap : 5+ améliorations futures crédibles
Section Contributing avec lien vers CONTRIBUTING.md

5.2 Qualité du code
PEP8 respecté (flake8 ou ruff en CI)
Docstrings sur toutes les fonctions publiques
Variables d'environnement via .env (jamais de secrets hardcodés)
Gestion des erreurs : try/except sur tous les appels LLM et DB
Logs applicatifs : module logging Python, niveau INFO/WARNING/ERROR

5.3 GitHub Actions CI
Pipeline CI minimal — .github/workflows/ci.yml

  Déclencheur : push sur main et pull_request

  Jobs :
  1. lint        → ruff check . (Python style)
  2. test        → pytest tests/ (tests unitaires parser + engine)
  3. build       → docker compose build (validation images)

  Badge résultant : ✅ Build Passing affiché dans le README


6. Critères de succès
Le projet est considéré livré et présentable en entretien si et seulement si les critères suivants sont tous validés :

Critère
Validation
Priorité
docker-compose up démarre sans erreur
Test manuel
BLOQUANT
Un log SSH brute force est détecté et trié
Test end-to-end
BLOQUANT
Le LLM retourne un JSON valide pour chaque alerte
Test unitaire
BLOQUANT
Le dashboard affiche les alertes avec codes couleur
Revue visuelle
BLOQUANT
README contient screenshot + GIF + Quick Start
Revue manuelle
BLOQUANT
Badge Build Passing vert sur GitHub
GitHub Actions CI
IMPORTANT
10 règles Sigma opérationnelles
Test engine.py
IMPORTANT
Export JSON fonctionnel
Test API /export
IMPORTANT
CONTRIBUTING.md + SECURITY.md présents
Revue fichiers
IMPORTANT
Zéro secret hardcodé dans le code
Revue sécurité
IMPORTANT


