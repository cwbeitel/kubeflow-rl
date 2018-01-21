# Kubeless deployment

### Status

Currently the following

```bash
kubeless function deploy checkpoint-responder --runtime python2.7 \
                                --handler responder_kubeless.main \
                                --from-file responder_kubeless.py \
                                --trigger-topic checkpoint-events

kubeless topic create checkpoint-events

kubeless topic publish --topic checkpoint-events --data "Hello World!"
```

yields

```bash
> kubeless function ls
NAME                	NAMESPACE	HANDLER                	RUNTIME  	TYPE  	TOPIC            	DEPENDENCIES	STATUS
checkpoint-responder	default  	responder_kubeless.main	python2.7	PubSub	checkpoint-events	            	MISSING: Check controller logs

> kubectl logs kubeless-controller-58676964bb-d5mjk -n kubeless
...
E0120 23:49:37.589589       1 reflector.go:201] github.com/kubeless/kubeless/pkg/controller/controller.go:122: Failed to list *spec.Function: functions.k8s.io is forbidden: User "system:serviceaccount:kubeless:controller-acct" cannot list functions.k8s.io at the cluster scope: clusterrole.rbac.authorization.k8s.io "kubeless-controller-deployer" not found
Unknown user "system:serviceaccount:kubeless:controller-acct"
```
