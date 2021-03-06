# Copyright 2020 The Kale Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Suite of helpers regarding workflow manipulation."""

from kale.common import podutils


ARGO_WORKFLOW_LABEL_KEY = "workflows.argoproj.io/workflow"
ARGO_COMPLETED_LABEL_KEY = "workflows.argoproj.io/completed"
ARGO_PHASE_LABEL_KEY = "workflows.argoproj.io/phase"


def find_pod_parents(node_name, workflow):
    """Find all direct pod-type parents of a node.

    If a parent node is not of type `Pod' (it could be, for example, a `Retry'
    node), search for its parents' parents.
    """
    parents = []

    workflow_name = workflow.get("metadata", {}).get("name")
    nodes = workflow.get("status", {}).get("nodes")
    if not (workflow_name and nodes):
        return parents

    for name, node in nodes.items():
        if node_name in node.get("children", []) and name != workflow_name:
            if node.get("type") == "Pod":
                parents.append(name)
            else:
                parents.extend(find_pod_parents(name, workflow))

    return parents


def get_workflow_name(pod_name, namespace):
    """Get the workflow name associated to a pod (pipeline step)."""
    v1_client = podutils._get_k8s_v1_client()
    pod = v1_client.read_namespaced_pod(pod_name, namespace)

    # Obtain the workflow name
    labels = pod.metadata.labels
    workflow_name = labels.get("workflows.argoproj.io/workflow", None)
    if workflow_name is None:
        msg = ("Could not retrieve workflow name from pod"
               "{}/{}".format(namespace, pod_name))
        raise RuntimeError(msg)
    return workflow_name


def get_workflow(name, namespace):
    """Get a workflow."""
    api_group = "argoproj.io"
    api_version = "v1alpha1"
    co_name = "workflows"
    co_client = podutils._get_k8s_custom_objects_client()
    return co_client.get_namespaced_custom_object(api_group, api_version,
                                                  namespace, co_name, name)
