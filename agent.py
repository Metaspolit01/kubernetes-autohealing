import requests
import json
import logging
import os
from k8s_manager import K8sManager

logger = logging.getLogger(__name__)

# Point this to your local LLM (like Ollama running Mistral or Llama3)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3")

k8s = K8sManager()

async def process_alert(alert):
    labels = alert.get("labels", {})
    annotations = alert.get("annotations", {})
    
    alert_name = labels.get("alertname", "UnknownAlert")
    namespace = labels.get("namespace", "default")
    pod_name = labels.get("pod", "unknown")
    node_name = labels.get("node", "unknown")
    description = annotations.get("description", "No description available")
    
    logger.info(f"Analyzing Alert: {alert_name} in {namespace}")

    prompt = f"""
    You are an autonomous DevOps autohealing agent with full cluster-admin access.
    Your job is to resolve Kubernetes cluster issues.
    
    An alert has fired with the following context:
    - Alert Name: {alert_name}
    - Namespace: {namespace}
    - Pod: {pod_name}
    - Node: {node_name}
    - Description: {description}
    - Full Labels: {json.dumps(labels)}
    - Full Annotations: {json.dumps(annotations)}

    Based on the context, what exact Kubernetes action should be taken to fix this? 
    You have the ability to run ANY kubectl command.
    Return ONLY a JSON object with the action details. Do NOT include markdown blocks or conversational text.
    
    Possible actions:
    1. {{"action": "run_kubectl", "command": "kubectl <your exact command here>"}} (Use this to perform ANY custom task like patching, restarting, scaling, rolling back, cordoning, deleting any resource, etc.)
    2. {{"action": "no_action", "reason": "<why>"}} (Use if it requires human intervention or cannot be solved safely via kubectl)
    """

    try:
        response = requests.post(OLLAMA_URL, json={
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }, timeout=60)
        
        response.raise_for_status()
        result_text = response.json().get("response", "{}")
        
        logger.info(f"LLM Decision: {result_text}")
        
        action_data = json.loads(result_text)
        k8s.execute_action(action_data)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to communicate with Local LLM: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"LLM did not return valid JSON: {e}. Output was: {result_text}")
    except Exception as e:
        logger.error(f"Error during agent execution: {e}")
