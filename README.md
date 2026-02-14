# Docker → Kubernetes → Argo CD → Prometheus → Grafana

**End-to-End læringsprosjekt**

Dette prosjektet viser hele flyten fra lokal Python-app til full GitOps-deploy i Kubernetes med overvåkning.

Målet er å lære:

* Containerisering (Docker)
* Kubernetes (Deployments, Services, HPA, ConfigMap, Secret)
* GitOps med Argo CD
* Observability med Prometheus + Grafana

---

# Arkitektur – mentalt bilde

```
Python App
   ↓
Docker Image → Docker Hub
   ↓
Kubernetes (Deployment + Service + HPA)
   ↓
Argo CD (GitOps Sync)
   ↓
Prometheus (samler metrics)
   ↓
Grafana (dashboards)
```

---

# Forutsetninger

* Windows + **WSL2**
* **Docker Desktop** (Kubernetes enabled)
* `kubectl` installert i WSL
* GitHub/GitLab konto
* Docker Hub konto

Sjekk at Kubernetes kjører:

```bash
kubectl cluster-info
kubectl get nodes
```

---

# DEL 1 – App + Docker

## 1. Lag Python app

FastAPI-app med endpoints:

* `/` – info
* `/healthz` – liveness
* `/readyz` – readiness
* `/metrics` – Prometheus metrics

Dette gjør appen klar for både Kubernetes og observability.

---

## 2. Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 3. Bygg image

```bash
docker build -t observability-app:1.0 .
```

---

## 4. Push til Docker Hub

```bash
docker login
docker tag observability-app:1.0 <brukernavn>/observability-app:1.0
docker push <brukernavn>/observability-app:1.0
```

---

## 5. Test lokalt

```bash
docker run -p 8000:8000 observability-app:1.0
curl http://localhost:8000/metrics
```

---

# DEL 2 – Kubernetes + Argo CD

## Struktur

```
k8s/
  base/
  overlays/
    dev/
    prod/
```

---

## Base inneholder

* `deployment.yaml`
* `service.yaml`
* `configmap.yaml`
* `secret.yaml`
* `hpa.yaml`
* `kustomization.yaml`

Dette er **felles oppsett**.

---

## Overlays (dev / prod)

Inneholder:

* `namespace.yaml`
* `patch-deployment.yaml`
* `patch-hpa.yaml`
* `servicemonitor.yaml`
* `kustomization.yaml`

Forskjell mellom dev og prod:

| Dev            | Prod           |
| -------------- | -------------- |
| færre replicas | flere replicas |
| latest image   | pinned versjon |
| lavere HPA     | høyere HPA     |

---

## Test lokalt uten Argo CD

```bash
kubectl apply -k k8s/overlays/dev
kubectl get all -n obsapp-dev
```

---

## Installer Argo CD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

Port-forward:

```bash
kubectl -n argocd port-forward svc/argocd-server 8080:443
```

Åpne: [https://localhost:8080](https://localhost:8080)

---

## Argo Applications

* `argocd-app-dev.yaml`
* `argocd-app-prod.yaml`

Disse peker til:

```
path: k8s/overlays/dev
path: k8s/overlays/prod
```

Apply:

```bash
kubectl apply -f argocd-app-dev.yaml
kubectl apply -f argocd-app-prod.yaml
```

---

# HPA Testing

HPA trenger **metrics-server**.

## Installer metrics-server

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

Patch for Docker Desktop:

```bash
kubectl -n kube-system patch deployment metrics-server \
--type=json \
-p='[
{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}
]'
```

Test:

```bash
kubectl top nodes
```

CPU-load test:

```bash
kubectl exec -it deploy/obsapp -n obsapp-dev -- python -c "while True: pass"
```

Se skalering:

```bash
kubectl get hpa -n obsapp-dev -w
```

---

# DEL 3 – Prometheus + Grafana

## Installer Monitoring Stack via Argo CD (Helm)

Application installerer:

* Prometheus
* Grafana
* Prometheus Operator
* CRDs (ServiceMonitor)

---

## Viktig rekkefølge

1. **Monitoring**
2. **Dev / Prod**

Ellers feiler `ServiceMonitor`.

---

## ServiceMonitor

Forteller Prometheus hvordan den skal scrape appen:

```yaml
endpoints:
  - port: http
    path: /metrics
```

---

## Åpne Grafana

```bash
kubectl -n monitoring port-forward svc/monitoring-grafana 3000:80
```

Login:

```
admin / admin
```

---

## Prometheus Targets

```bash
kubectl -n monitoring port-forward svc/monitoring-kube-prometheus-prometheus 9090
```

`Status → Targets` skal vise appen.

---

# Viktige Læringspunkter

| Tema       | Hva du lærte                   |
| ---------- | ------------------------------ |
| Docker     | bygge + pushe images           |
| Kubernetes | Deployments, Services, HPA     |
| GitOps     | Argo CD synker fra Git         |
| Metrics    | Prometheus scraper endpoints   |
| Dashboards | Grafana visualiserer           |
| Kustomize  | miljø-overlays                 |
| CRDs       | ServiceMonitor krever operator |

---

# Vanlige Feil

| Problem                   | Årsak                      |
| ------------------------- | -------------------------- |
| Metrics API not available | metrics-server mangler     |
| ServiceMonitor unknown    | monitoring ikke installert |
| Argo Sync Error           | feil path eller repo       |
| HPA skalerer ikke         | ingen CPU-load             |

---

# Sluttresultat

Du kan nå:

* Bygge og pushe en app
* Deploye den i Kubernetes
* Skalere automatisk
* Deploye via Git
* Se metrics og dashboards

Dette er i praksis en **mini-DevOps pipeline lokalt**.
