# DevOps Autohealing Agent

This is an autonomous autohealing backend that receives Prometheus webhook alerts, uses a Local LLM to decide on a course of action, and executes Kubernetes API calls automatically without human intervention.

## Architecture
1. **FastAPI Webhook Server (`main.py`)**: Receives JSON payloads from Prometheus Alertmanager `/webhook`.
2. **Local LLM Agent (`agent.py`)**: Connects to an instance of [Ollama](https://ollama.com/) (running models like Mistral, Llama 3) running locally on port 11434. It constructs a prompt with alert state. The LLM dictates the action.
3. **K8s Manager (`k8s_manager.py`)**: Responsible for securely connecting to the Kubernetes cluster and safely executing the exact action specified by the LLM (Pod Restarts, Scaling, Node Cordoning, etc.).

## Prerequisites
1. **Python 3.9+**
2. **Ollama**: Installed and running locally.
   ```bash
   ollama pull mistral
   ollama serve
   ```
3. **Kubernetes Cluster**: Ensure you have an active `.kube/config` or are running this inside a Pod with sufficient RBAC permissions (Roles/ClusterRoles for Pod deletion, Deployments scaling, Node patching).

## How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the API:
   ```bash
   python main.py
   ```

## Configuring Prometheus Alertmanager
Add this route to your `alertmanager.yml`:
```yaml
receivers:
- name: 'autohealing-agent'
  webhook_configs:
  - url: 'http://<YOUR_API_IP>:8080/webhook'
    send_resolved: false
```
