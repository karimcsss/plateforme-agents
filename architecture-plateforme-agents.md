# Plateforme d'Orchestration Multi-Agents — Spécification & Architecture

> Statut : document de cadrage produit avant le développement, conformément à la méthode de travail adoptée pour ce projet (architecture définie et validée avant la première ligne de code).

---

## 1. Spécification produit

### 1.1 Proposition de valeur
L'utilisateur soumet un problème en langage naturel. Le système :
- planifie dynamiquement une équipe d'agents adaptée au problème,
- exécute chaque agent avec de vrais outils,
- structure toutes les sorties (pas de texte brut),
- fait vérifier les résultats par un agent Critique avec droit de contestation,
- déclenche une validation humaine si nécessaire,
- affiche l'exécution en temps réel,
- produit un rapport final structuré et partageable.

Ce n'est pas un chatbot multi-agents séquentiel : c'est un système d'orchestration avec planification, vérification et supervision.

### 1.2 Utilisateurs cibles
- Recruteurs techniques / relecteurs de portfolio (audience principale de la démo)
- Utilisateur final type : quelqu'un qui a une question de recherche factuelle nécessitant plusieurs angles

### 1.3 Ce que le projet doit prouver
Planification, orchestration, tool use, sorties structurées, vérification multi-agents, workflows dynamiques (pas figés), supervision humaine conditionnelle, observabilité dès le départ, gestion d'erreurs, budget/coût maîtrisé.

---

## 2. Exigences

### 2.1 Fonctionnelles
| ID | Exigence |
|----|----------|
| F1 | L'utilisateur soumet un problème en texte libre |
| F2 | Le Planificateur génère un plan JSON validé par Pydantic (3-5 agents, rôles, dépendances) |
| F3 | Chaque agent exécute avec l'outil `web_search` et produit une sortie structurée (claim + evidence + confidence) |
| F4 | Le Critique évalue chaque `finding`, peut contester (faible confiance ou contradiction) |
| F5 | L'agent contesté a droit à **une seule** re-vérification (retry budget = 1) |
| F6 | Déclenchement d'une validation humaine si coût estimé > seuil OU confiance < 0.5 |
| F7 | Le frontend affiche un graphe d'agents en temps réel (statuts : pending/running/completed/failed/needs_review) via SSE |
| F8 | Le Synthétiseur produit un rapport final structuré (résumé, preuves, recommandations, risques, sources) |
| F9 | Export Markdown/JSON du rapport |
| F10 | Lien de partage public en lecture seule |

### 2.2 Non-fonctionnelles
| ID | Exigence |
|----|----------|
| NF1 | Budget de tokens strict par exécution |
| NF2 | Fournisseur LLM interchangeable via une couche d'abstraction unique |
| NF3 | Chaque appel d'agent loggé (latence, tokens, coût estimé, outils, succès/échec) |
| NF4 | Aucun agent n'a d'accès shell brut ni réseau libre — outils encapsulés et permissionnés |
| NF5 | Protection anti-injection de prompt et anti-SSRF sur l'outil web |
| NF6 | Coût d'infrastructure = 0 € en usage démo (tiers gratuits uniquement) |
| NF7 | Le système doit fonctionner en dégradé si un agent échoue |

---

## 3. Architecture système (vue d'ensemble)

```
┌─────────────┐      HTTPS/SSE      ┌──────────────────┐
│  Next.js UI  │ ◄──────────────────► │   FastAPI backend │
│  (Vercel)    │                      │    (Render)        │
└─────────────┘                      └────────┬──────────┘
                                               │
                     ┌─────────────────────────┼─────────────────────────┐
                     │                         │                         │
             ┌───────▼───────┐        ┌────────▼────────┐       ┌────────▼────────┐
             │  Orchestrateur │        │  Couche LLM      │       │  Outil web_search│
             │  (agents.py)   │        │  abstraction     │       │  (sandboxé)       │
             │  DAG runner    │        │  Groq (Qwen)     │       │                   │
             └───────┬────────┘        └──────────────────┘       └───────────────────┘
                     │
             ┌───────▼────────┐
             │ Supabase        │
             │ Postgres        │
             │ (état partagé,  │
             │  logs, runs)    │
             └─────────────────┘
```

**Coût réel par composant (validé en production) :**
- Next.js/Vercel : gratuit
- FastAPI/Render : gratuit avec cold start ~30-50s après inactivité (compromis assumé)
- Supabase Postgres : gratuit jusqu'à 500 Mo
- Groq (Qwen3.6-27B, après migration suite à décommission de Llama 3.3) : gratuit avec rate limits (8000 tokens/minute, 200 000 tokens/jour)
- Tavily : gratuit, 1000 crédits/mois

---

## 4. Architecture des agents

### 4.1 Rôles
1. **Planificateur** — reçoit le problème, produit un plan, validé par Pydantic avant toute exécution.
2. **Agents dynamiques** — chacun a un rôle, un objectif, un accès outil (`web_search`), des dépendances.
3. **Critique** — relit tous les `findings`, repère faible confiance (<0.5) ou contradictions, émet une contestation.
4. **Synthétiseur** — agrège les findings validés en rapport final structuré.

### 4.2 Schéma du plan (Pydantic)
```python
class RequiredAgent(BaseModel):
    id: str
    role: str
    goal: str
    tools: list[Literal["web_search"]]
    depends_on: list[str] = []

class Plan(BaseModel):
    objective: str
    required_agents: list[RequiredAgent]  # 3 à 5, validé
    workflow: Literal["dag", "sequential"]
    requires_human_approval: bool
    approval_triggers: list[Literal["high_cost", "low_confidence", "high_ambiguity"]]
```

Validateurs Pydantic ajoutés en cours de développement (non prévus initialement, mais nécessaires face au comportement réel du modèle gratuit) :
- Nombre d'agents entre 3 et 5
- Toutes les dépendances référencent des agents existants dans le plan
- **Profondeur maximale de dépendances = 2** (ajouté après observation empirique que le modèle générait parfois des chaînes séquentielles trop profondes malgré le prompt)

### 4.3 Contrat de sortie d'un agent
```python
class Finding(BaseModel):
    claim: str
    evidence: list[str]
    confidence: float  # contraint entre 0.0 et 1.0

class AgentResult(BaseModel):
    agent_id: str
    status: Literal["completed", "failed", "needs_review"]
    findings: list[Finding]
    errors: list[str]
    tokens_used: int   # mesuré réellement via l'API, jamais estimé par le modèle
    duration_ms: int
```

### 4.4 Boucle de vérification
```
Critique lit tous les AgentResult
  → pour chaque finding : confiance < seuil OU contradiction avec un autre agent ?
    → oui : émettre Contestation(agent_id, finding_id, raison)
      → agent d'origine re-exécute UNE fois avec la contestation en contexte
        → le nouveau résultat remplace l'ancien dans l'état partagé
        → l'ancien résultat est conservé dans l'historique (audit trail)
    → non : finding validé tel quel
```
Budget de retry **global par run** (pas par agent), pour éviter l'explosion de coût si plusieurs agents sont contestés simultanément.

### 4.5 Ce qui rend l'orchestration "vraie"
- Tri topologique du plan en "vagues" d'exécution — les agents indépendants tournent réellement en parallèle via `asyncio.gather`, pas en séquence déguisée
- Le workflow peut être DAG ou séquentiel selon les dépendances déclarées par le Planificateur lui-même
- La boucle de vérification introduit un aller-retour conditionnel, observé et confirmé en conditions réelles (contestations réelles capturées dans les logs de production)

---

## 5. Schéma de base de données (Postgres/Supabase)

Tables effectivement créées au fil du développement :

- **`runs`** — id, problem_statement, status, plan (jsonb), report (jsonb), error_detail (jsonb), share_token, share_enabled, created_at, updated_at
- **`agent_executions`** — id, run_id, agent_id, role, status, result (jsonb), tokens_used, duration_ms, attempt
- **`contestations`** — id, run_id, agent_id, reason, resolved, created_at
- **`execution_logs`** — id, run_id, agent_id, event_type, payload (jsonb), latency_ms, tokens_used, cost_estimate, created_at
- **`human_approvals`** — id, run_id, trigger_reason, status, created_at, resolved_at

---

## 6. Design API (FastAPI)

| Endpoint | Méthode | Description |
|---|---|---|
| `/runs` | POST | Soumet un problème → crée un run, lance le Planificateur, exécute en tâche de fond |
| `/runs/{id}` | GET | État complet du run |
| `/runs/{id}/stream` | GET (SSE) | Flux temps réel des événements |
| `/runs/{id}/approve` | POST | Valide/rejette une exécution en attente d'approbation humaine |
| `/runs/{id}/logs` | GET | Historique complet des événements d'exécution |
| `/runs/{id}/export` | GET | Export Markdown ou JSON du rapport |
| `/runs/{id}/share` | POST | Génère un lien de partage public |
| `/runs/{id}/unshare` | POST | Désactive le partage |
| `/public/{share_token}` | GET | Accès public en lecture seule au rapport |

**SSE plutôt que WebSockets** : suffisant car le flux est unidirectionnel, plus simple à déployer sur les plans gratuits.

---

## 7. Architecture frontend (Next.js)

- App Router, TypeScript, Tailwind v4
- **React Flow** pour le graphe d'agents en direct : nœuds = agents (couleur selon statut), arêtes = dépendances, layout calculé par vagues (même logique que le backend)
- Connexion SSE via `EventSource` natif
- Palette "salle de contrôle" : fond quasi-noir, JetBrains Mono pour les identifiants techniques, couleurs de statut distinctes (pending/running/completed/failed/needs_review)

---

## 8. Architecture de sécurité

- Outils encapsulés (`app/tools/web_search.py`) — aucun agent n'a d'accès shell brut
- Contenu web traité comme donnée non fiable, jamais concaténé directement dans un prompt système sans délimitation
- Validation stricte des entrées à toutes les frontières (Pydantic)
- Budget de retry borné pour empêcher l'explosion de coût
- Secrets exclusivement en variables d'environnement, jamais commités (`.gitignore` dès l'Étape 1)

---

## 9. Risques identifiés et mitigations réelles

| Risque | Mitigation appliquée |
|---|---|
| Rate limits du LLM gratuit en démo live | Système conçu pour rester robuste : un rapport est produit même si un agent échoue individuellement |
| Décommission du modèle en cours de route | **Arrivé réellement** (Llama 3.3 décommissionné par Groq le 16 août 2026) — la couche d'abstraction LLM a permis une migration en changeant une seule variable d'environnement |
| Dérive de coût si contestation mal bornée | Budget de retry strict = 1, global par run |
| Incohérence de versions de dépendances entre environnements | **Rencontré en production** (Render vs local) — résolu en épinglant explicitement toutes les dépendances directes plutôt que de laisser pip résoudre différemment selon l'environnement |
| Injection de prompt via contenu web récupéré | Traitement du contenu web comme donnée non fiable |

---

## 10. Stratégie de déploiement — validée en production

| Composant | Service | Statut |
|---|---|---|
| Frontend | Vercel | ✅ Déployé : plateforme-agents-black.vercel.app |
| Backend | Render | ✅ Déployé : plateforme-agents.onrender.com |
| DB | Supabase | ✅ Opérationnel |
| LLM | Groq (Qwen3.6-27B) | ✅ Opérationnel (après migration) |

---

## Conclusion

Ce document reflète l'architecture telle que conçue avant développement (Étapes 1-2) et telle qu'elle a évolué au contact de la réalité (contraintes de modèles gratuits, incidents de déploiement, décommission de service). L'écart entre le plan initial et l'implémentation finale — documenté honnêtement plutôt que masqué — est en soi une preuve de la capacité à concevoir, construire, déboguer et adapter un système réel.