from kubernetes import client, config
import logging
import subprocess

logger = logging.getLogger(__name__)

class K8sManager:
    def __init__(self):
        try:
            # Try to load incluster config (If running inside a pod)
            config.load_incluster_config()
            logger.info("Loaded in-cluster Kubernetes config.")
        except Exception:
            # Fallback to local kubeconfig (If running on a local machine)
            try:
                config.load_kube_config()
                logger.info("Loaded local Kubernetes config.")
            except Exception as e:
                logger.error(f"Could not load Kubernetes configuration: {e}")
        
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()

    def execute_action(self, action_data: dict):
        action = action_data.get("action")
        namespace = action_data.get("namespace", "default")

        try:
            if action == "delete_pod":
                pod = action_data.get("pod")
                if pod and pod != "unknown":
                    logger.info(f"Executing: Deleting pod {pod} in {namespace}")
                    self.v1.delete_namespaced_pod(name=pod, namespace=namespace)
                    logger.info("Action executed successfully.")
                else:
                    logger.error("Pod name not provided for delete_pod action.")

            elif action == "scale_deployment":
                deployment = action_data.get("deployment")
                replicas = action_data.get("replicas", 1)
                if deployment:
                    logger.info(f"Executing: Scaling deployment {deployment} in {namespace} to {replicas}")
                    body = {"spec": {"replicas": replicas}}
                    self.apps_v1.patch_namespaced_deployment_scale(
                        name=deployment, 
                        namespace=namespace, 
                        body=body
                    )
                    logger.info("Action executed successfully.")
                else:
                    logger.error("Deployment name not provided for scale_deployment action.")

            elif action == "cordon_node":
                node = action_data.get("node")
                if node and node != "unknown":
                    logger.info(f"Executing: Cordoning node {node}")
                    body = {"spec": {"unschedulable": True}}
                    self.v1.patch_node(name=node, body=body)
                    logger.info("Action executed successfully.")
                else:
                    logger.error("Node name not provided for cordon_node action.")

            elif action == "run_kubectl":
                command = action_data.get("command")
                if command and command.startswith("kubectl "):
                    logger.info(f"Executing arbitrary kubectl command: {command}")
                    try:
                        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
                        if result.returncode == 0:
                            logger.info(f"Command successful: {result.stdout.strip()}")
                        else:
                            logger.error(f"Command failed: {result.stderr.strip()}")
                    except subprocess.TimeoutExpired:
                        logger.error("Command timed out after 60 seconds.")
                    except Exception as e:
                        logger.error(f"Error running kubectl: {e}")
                else:
                    logger.error("Invalid command provided. Must start with 'kubectl '.")

            elif action == "no_action":
                reason = action_data.get("reason", "Unknown")
                logger.info(f"LLM decided to take no action. Reason: {reason}")
            
            else:
                logger.warning(f"Unknown action received from LLM: {action}")

        except client.exceptions.ApiException as e:
            logger.error(f"Kubernetes API Error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error executing Kubernetes action: {e}")
