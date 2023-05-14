from main.logger import logger
from main.config import settings
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes.client import CustomObjectsApi
from datetime import datetime
import time, json

# API Key kube access
def getAPIClient():
    configuration = client.Configuration()
    configuration.api_key['authorization'] = settings.K8S_API_KEY
    configuration.api_key_prefix['authorization'] = 'Bearer'
    configuration.host = settings.K8S_HOST_URL
    configuration.verify_ssl = False
    client.Configuration.set_default(configuration)

# Collect current state from k8s
def getMetrics():
    logger.info('Get k8s object metrics')

    getAPIClient()

    _return = []
    _pods = getPods()
    for _entry in _pods:
        if _entry is not None:
            _return.append(_entry)

    _workloads = getWorkloads()
    for _entry in _workloads:
        if _entry is not None:
            _return.append(_entry)


    _supplychains = getSupplyChains()
    for _entry in _supplychains:
        if _entry is not None:
            _return.append(_entry)

    return _return


# Get list of current deployed pods across all namespaces
def getPods():
    logger.info('Get list of pods running in cluster')

    getAPIClient()

    v1 = client.CoreV1Api()
    ret = v1.list_pod_for_all_namespaces(watch=False)

    _json = []
    _time = time.mktime(datetime.now().timetuple())
    try:

        for _entry in ret.items:
            if _entry is not None:
                if _entry.metadata.labels is not None:
                    _labels = _entry.metadata.labels

                if _entry.metadata.annotations is not None:
                    _annotations = _entry.metadata.annotations

                _info = {
                    'id': _entry.metadata.uid,
                    'name': _entry.metadata.name,
                    'creationDate': time.mktime(_entry.metadata.creation_timestamp.timetuple()),
                    'address': _entry.status.pod_ip,
                    'labels':  _labels,
                    'annotations': _annotations,
                    'type': 'pod',
                    'status': _entry.status.phase,
                    'namespace': _entry.metadata.namespace,
                    'date': _time
                }
            _json.append(_info)

    except ApiException as e:
        logger.info("Exception when calling CustomObjectsApi->get_cluster_custom_object_scale: %s\n" % e)
    except:
        logger.info("Exception occured in Pod list")

    return _json

# get a list of the Workload objects deployed
def getWorkloads():
    logger.info('Get list of cartographer workloads deployed in cluster')

    getAPIClient()
    _return = []
    with client.ApiClient() as api_client:
        api_instance = client.CustomObjectsApi(api_client)
        group = 'carto.run' # str | the custom resource's group
        version = 'v1alpha1' # str | the custom resource's version
        plural = 'workloads' # str | the custom resource's plural name. For TPRs this would be lowercase plural kind.
        namespace = 'default'
        _time = time.mktime(datetime.now().timetuple())

        try:
            _response = api_instance.list_namespaced_custom_object(group, version, namespace, plural)
            for _entry in _response["items"]:

                if _entry['metadata']['labels'] is not None:
                    _labels = _entry['metadata']['labels']

                _annotations = []
                if _entry['spec']['params'] is not None:
                    for _annotation in _entry['spec']['params']:
                        if _annotation['name'] == 'annotations':
                            _annotations = _annotation['value']
                            break

                for _actions in _entry['status']['resources']:
                    logger.info('Workload task: %s current status is %s at %s' , 
                                _actions['name'], 
                                _actions['conditions'][len(_actions['conditions'])-1]['status'], 
                                _actions['conditions'][len(_actions['conditions'])-1]['lastTransitionTime'])


                _createdOn = time.mktime(datetime.strptime(_entry['metadata']['creationTimestamp'], "%Y-%m-%dT%H:%M:%SZ").timetuple())

                _info = {
                    'id': _entry['metadata']['uid'],
                    'name': _entry['metadata']['name'],
                    'creationDate': _createdOn,
                    'address': _entry['status']['supplyChainRef']['name'],
                    'labels': _labels,
                    'annotations': _annotations,
                    'type': 'workload',
                    'status': _entry['status']['conditions'][0]['reason'],
                    'namespace': namespace,
                    'date': _time
                }
                _return.append(_info)
        except ApiException as e:
            logger.info("Exception when calling CustomObjectsApi->get_cluster_custom_object_scale: %s\n" % e)
        except:
            logger.info("Exception occured in workload list")

    return _return


# Geta list of the Carytogrpaher SupplyChains deployed into the cluster
def getSupplyChains():
    logger.info('Get list of cartographer Supply Chains deployed in cluster')

    getAPIClient()
    _return = []
    with client.ApiClient() as api_client:
        api_instance = client.CustomObjectsApi(api_client)
        group = 'carto.run' # str | the custom resource's group
        version = 'v1alpha1' # str | the custom resource's version
        plural = 'clustersupplychains' # str | the custom resource's plural name. For TPRs this would be lowercase plural kind.
        _time = time.mktime(datetime.now().timetuple())

        try:
            _response = api_instance.list_cluster_custom_object(group, version, plural)
            for _entry in _response["items"]:
                if 'labels' in _entry['metadata']:
                    _labels = _entry['metadata']['labels']

                _params = []
                if _entry['spec']['params'] is not None:
                    for _param in _entry['spec']['params']:
                        if 'default' in _param:
                            _default = _param['default']
                        else:
                            _default = None
                        if 'value' in _param:
                            _value = _param['value']
                        else:
                            _value = None

                        _a = {
                            'name': _param['name'],
                            'value': _value,
                            'default': _default
                        }
                        _params.append(_a)

                    _annotations = _entry['spec']['params']

                _createdOn = time.mktime(datetime.strptime(_entry['metadata']['creationTimestamp'], "%Y-%m-%dT%H:%M:%SZ").timetuple())

                _info = {
                    'id': _entry['metadata']['uid'],
                    'name': _entry['metadata']['name'],
                    'creationDate': _createdOn,
                    'address': '',
                    'labels': _labels,
                    'annotations': None,
                    'parameters': _params,
                    'type': 'supplychain',
                    'status': _entry['status']['conditions'][0]['reason'],
                    'namespace': '',
                    'date': _time
                }
                _return.append(_info)

        except ApiException as e:
            logger.info("Exception when calling CustomObjectsApi->get_cluster_custom_object_scale: %s\n" % e)
        except:
            logger.info("Exception occured in Supplychain list")

    return _return
