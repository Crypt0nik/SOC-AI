


SOC-AI
Security Operations Center — Intelligence Artificielle



BUSINESS PLAN
Stratégie de commercialisation — Open Source & SaaS



Champ
Valeur
Produit
SOC-AI v1.0 — Open Source
Modèle économique
Open Core + SaaS Cloud + Services
Marché cible primaire
PME/ETI françaises (10–500 salariés)
Marché secondaire
MSSP, intégrateurs cybersécurité
Équipe projet
Étudiants B3 Cybersécurité — Ynov Sophia Antipolis
Horizon plan
3 ans (2026–2028)
Version document
1.0 — Juin 2026

1. Executive Summary
SOC-AI est une plateforme open source de triage automatisé des alertes de sécurité, conçue pour les PME et ETI qui ne disposent pas d'une équipe SOC dédiée. En combinant des règles de détection standardisées (Sigma/MITRE ATT&CK) avec un Large Language Model, SOC-AI qualifie automatiquement chaque alerte et fournit une recommandation d'action en langage naturel.

Proposition de valeur — SOC-AI en 3 points

  1.  ACCESSIBILITÉ    → Déployable en 5 minutes via Docker Compose, sans expertise SOC
  2.  INTELLIGENCE     → Triage LLM : severity, type d'attaque MITRE, recommandation concrète
  3.  ÉCONOMIE         → Version community 100% gratuite ; support et cloud en option payante


Chiffres clés du marché adressé
Indicateur
Valeur
Source
Pertinence
PME françaises sans SOC
~250 000
ANSSI 2025
Marché core
Coût moyen d'une cyberattaque PME
~90 000 €
Hiscox 2025
Douleur client
Marché SIEM/SOC mondial 2026
6,2 Mds €
Gartner 2025
Taille marché
Croissance annuelle segment SMB
+18% / an
IDC 2025
Dynamique

2. Analyse du marché
2.1 Problème identifié
Les solutions SOC actuelles (Splunk, IBM QRadar, Microsoft Sentinel) sont conçues pour les grandes entreprises : coût annuel de 50 000 à 500 000 €, nécessitent une équipe d'analystes certifiés, et génèrent des milliers d'alertes par jour dont 90 à 95% sont des faux positifs (source : Ponemon Institute 2024).

Les PME et ETI se retrouvent dans une situation paradoxale : exposées aux mêmes menaces que les grandes entreprises, mais sans les ressources humaines ni financières pour opérer un SOC traditionnel.

2.2 Segmentation clients
Segment
Profil
Besoin prioritaire
PME IT (10–100 sal.)
DSI seul ou équipe 2–3 pers.
Visibilité et triage automatique
ETI industrielle (100–500 sal.)
Responsable sécu + équipe IT
Conformité NIS2 + alerting
MSSP / Intégrateur
Prestataire multi-clients
Outil mutualisé white-label
Collectivités locales
DSI publique contrainte budgétaire
Solution souveraine open source
Startups tech
CTO + dev, pas d'équipe sécu
Déploiement rapide, coût zéro

2.3 Analyse concurrentielle
Solution
Prix annuel
Complexité déploiement
Cible réelle
Splunk Enterprise
50 000 – 500 000 €
Très élevée (équipe dédiée)
Grands comptes
Microsoft Sentinel
Variable (par GB)
Élevée (Azure natif)
Entreprises Microsoft
Elastic SIEM
Gratuit / 10 000 €+
Élevée (stack ELK)
Équipes techniques
Wazuh (open source)
Gratuit / support payant
Moyenne
PME techniques
SOC-AI (notre produit)
Gratuit / 99–499 €/mois
Faible (docker-compose up)
PME/ETI tous secteurs

Avantage concurrentiel différenciateur

  SOC-AI est la seule solution combinant :
  • Déploiement < 5 minutes (vs semaines pour les concurrents)
  • Triage en langage naturel par LLM (recommandation lisible sans formation)
  • Standard Sigma + MITRE ATT&CK (compatible avec l'écosystème existant)
  • Licence MIT (pas de vendor lock-in, souveraineté totale des données)


3. Modèle économique
3.1 Stratégie Open Core
SOC-AI adopte le modèle Open Core, éprouvé par des succès comme GitLab, HashiCorp (avant BSL) ou Wazuh : le cœur du produit est open source et gratuit ; les fonctionnalités avancées, le support et l'hébergement cloud sont monétisés.

Tier
Nom
Prix
Community
Open Source — GitHub
Gratuit
Pro
Fonctionnalités avancées
99 € / mois / organisation
Enterprise
Multi-tenant + SLA + support
499 € / mois / organisation
Services
Déploiement + formation + audit
Sur devis (TJM 600–900 €)

3.2 Fonctionnalités par tier
Fonctionnalité
Community
Pro
Enterprise
Ingestion logs SSH/Apache/Windows
✅
✅
✅
10 règles Sigma incluses
✅
✅
✅
Triage LLM (clé API propre)
✅
✅
✅
Dashboard web
✅
✅
✅
Support communautaire GitHub
✅
✅
✅
Règles Sigma premium (50+)
❌
✅
✅
Alertes Slack / Teams / PagerDuty
❌
✅
✅
Corrélation temporelle avancée
❌
✅
✅
Score de risque par actif
❌
✅
✅
Multi-tenant (plusieurs clients)
❌
❌
✅
SLA 99,9% + support 8x5
❌
❌
✅
SSO (SAML / OIDC)
❌
❌
✅
Rapport de conformité NIS2/ISO27001
❌
❌
✅

3.3 Revenus prévisionnels — 3 ans
Hypothèses de conversion (modèle SaaS open source standard)
  • Ratio GitHub stars → utilisateurs actifs : 1 pour 10
  • Taux de conversion Community → Pro : 2 à 5% (benchmark industrie : 2–8%)
  • Taux de conversion Pro → Enterprise : 15 à 20%
  • Churn mensuel estimé : 3%

Période
GitHub Stars
Clients Pro
Clients Enterprise
ARR estimé
An 1 — 2026
500
8
2
~12 000 €
An 2 — 2027
2 000
35
8
~52 000 €
An 3 — 2028
6 000
90
20
~120 000 €

Note : Ces projections représentent un scénario réaliste-conservateur. Un seul contrat Enterprise MSSP (white-label, 10+ clients gérés) peut multiplier l'ARR par 3 à 5 en an 2.

4. Stratégie Go-To-Market
4.1 Phase 1 — Traction open source (Mois 1–6)
Publication GitHub avec README soigné, GIF démo, architecture diagram
Soumission sur Hacker News (Show HN), Reddit r/netsec, r/selfhosted
Article de blog technique : 'Comment nous avons construit un mini-SOC avec un LLM en 2 jours'
Présentation à des meetups cybersécurité locaux (Toulon, Nice, Marseille, Sophia)
Outreach ciblé vers les RSSI de PME locales (PACA) pour un pilote gratuit

4.2 Phase 2 — Premières ventes (Mois 6–18)
Programme Early Adopter : 3 mois Pro gratuit pour 20 bêta-testeurs en échange de feedback
Partenariat avec 1 ou 2 intégrateurs MSP/MSSP régionaux (apporteur d'affaires, commission 20%)
Référencement sur le catalogue ANSSI / Cybermalveillance.gouv.fr
Démarchage direct : campagne email froide ciblée RSSI/DSI ETI 50–200 salariés

4.3 Phase 3 — Scale (Mois 18–36)
Marketplace : listing AWS Marketplace, OVHcloud, Scaleway
Certification SecNumCloud (différenciateur fort marché public français)
Développement module NIS2 Compliance Report (levier réglementaire fort, deadline 2026–2027)
Internationalisation : README EN, documentation EN, ciblage marché allemand et belge

4.4 Canaux d'acquisition
Canal
Coût
Délai premiers leads
GitHub organique (SEO + stars)
Zéro
3–6 mois
Articles de blog technique
Temps rédaction
1–3 mois
Meetups / conférences (FIC, Hack-In-Paris)
Frais déplacement
1–6 mois
Partenariats MSP/MSSP
Commission 20%
3–9 mois
LinkedIn outreach ciblé RSSI
Temps prospection
1–4 mois
Marketplaces cloud
Commission 15–30%
6–12 mois

5. Roadmap produit
v1.0 — Sprint initial (Juin 2026)
Parser SSH + Apache + Windows Event Log
10 règles Sigma opérationnelles
Triage LLM avec JSON structuré (severity, MITRE, recommandation)
Dashboard web React + FastAPI
Docker Compose clé en main

v1.5 — Q3 2026
Alertes webhook Slack / Microsoft Teams
Score de risque cumulatif par IP source (corrélation temporelle)
50 règles Sigma premium
Export PDF rapport de sécurité hebdomadaire

v2.0 — Q1 2027
Module NIS2 Compliance Dashboard (mesures article 21)
Connecteur Elastic/OpenSearch (ingestion native)
API REST complète (intégration SOAR tiers)
Multi-tenant pour MSSP (gestion de plusieurs clients)

v3.0 — 2028
Agent de réponse automatique : blocage IP, quarantaine endpoint
Cartographie MITRE ATT&CK visuelle (heatmap par organisation)
Fine-tuning LLM sur dataset d'alertes réelles anonymisées
Certification Common Criteria / SecNumCloud

6. Équipe & compétences
Le projet est développé dans le cadre d'un sprint pédagogique par des étudiants de B3 Cybersécurité (Ynov Sophia Antipolis), sous supervision académique. La composition type d'une équipe projet optimale pour ce produit :

Rôle
Compétences clés
Contribution principale
Lead Dev Backend
Python, FastAPI, Docker, SQLite
Parser, Sigma engine, API
Lead Dev Frontend
React, TailwindCSS, REST API
Dashboard, UX, export
LLM / Prompt Engineer
Anthropic API, prompt design, JSON
Agent triage, tests qualité
DevSecOps
GitHub Actions, Docker, Linux
CI/CD, déploiement, sécurité
Product Owner
Cybersécurité, rédaction, Sigma
Règles, README, go-to-market

Valeur CV — Ce que ce projet apporte concrètement

  • Expérience open source réelle (GitHub public, issues, PR, CI/CD)
  • Maîtrise d'un stack pro complet : Python · FastAPI · React · Docker · LLM API
  • Connaissance des standards industrie : Sigma Rules · MITRE ATT&CK · NIS2
  • Capacité à expliquer une architecture SOC en entretien
  • Démonstration concrète en entretien : git clone && docker-compose up
  • Projet potentiellement monetisable : différenciateur rare pour un profil B3


7. Analyse des risques
Risque
Probabilité
Impact
Mitigation
Dépendance API LLM (coût, dispo)
Moyenne
Élevé
Support Ollama local en alternative offline
Faible traction initiale GitHub
Moyenne
Moyen
Stratégie contenu + meetups + Show HN
Concurrence Wazuh (déjà établi)
Élevée
Moyen
Différenciation LLM triage + UX simplifiée
Qualité des règles Sigma insuffisante
Faible
Élevé
Utilisation du repository sigma-rules/sigma officiel
Violation RGPD (logs contenant PII)
Faible
Très élevé
Anonymisation logs + documentation DPIA
Burn-out équipe (sprint intense)
Moyenne
Moyen
Découpage clair des tâches + MVP strict

Risque RGPD — Point critique à traiter

  Les logs de sécurité peuvent contenir des données personnelles (adresses IP, noms
  d'utilisateurs, emails). SOC-AI doit inclure dans sa documentation :
  • Une politique de rétention des données (ex. 90 jours maximum)
  • Une fonctionnalité d'anonymisation des logs avant traitement LLM
  • Un SECURITY.md précisant les bonnes pratiques de déploiement
  • Une mention explicite dans le README : 'Ne pas envoyer de PII au LLM cloud'


8. Synthèse & prochaines étapes
Pourquoi SOC-AI est un projet sérieux
Le problème est réel et douloureux : 250 000 PME françaises sans SOC, NIS2 en vigueur
Le timing est parfait : les LLMs sont désormais assez capables pour du triage d'alertes fiable
Le modèle open source est éprouvé : Wazuh, Graylog, Suricata ont tous commencé ainsi
La barrière d'entrée est faible : Docker Compose + Claude API = déployable en 2 jours
La crédibilité GitHub est immédiate : un README soigné + GIF démo convaincra un recruteur en 30 secondes

Prochaines étapes immédiates
Priorité
Action
Deadline
P0 — BLOQUANT
Créer le repo GitHub + structure
Jour 1 matin
P0 — BLOQUANT
MVP fonctionnel docker-compose up
Fin Jour 1
P0 — BLOQUANT
Dashboard + 10 règles Sigma
Fin Jour 2
P1 — IMPORTANT
README professionnel + GIF démo
Fin Jour 2
P1 — IMPORTANT
Soumission Hacker News / Reddit
Semaine suivante
P2 — OPTIONNEL
Première règle Sigma custom originale
Semaine suivante
P2 — OPTIONNEL
Contacter 3 PME locales pour pilote
Mois suivant


Message final aux étudiants

  Dans 2 jours, vous aurez sur votre GitHub un projet que 99% des candidats B3 n'ont pas :
  une plateforme de sécurité fonctionnelle, documentée, déployable en 1 commande,
  avec un vrai modèle économique derrière.

  Ce n'est pas un TP. C'est le début d'un produit.
  À vous de décider jusqu'où vous voulez aller.


