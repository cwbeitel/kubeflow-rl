# Deploy kubeless

### Status:

Currently RBAC deployment, i.e. CHART=https://github.com/kubeless/kubeless/releases/download/$RELEASE/kubeless-rbac-$RELEASE.yaml, fails with

```bash
Error from server (Forbidden): error when creating "https://github.com/kubeless/kubeless/releases/download/v0.3.4/kubeless-rbac-v0.3.4.yaml": clusterroles.rbac.authorization.k8s.io "kubeless-controller-deployer" is forbidden: attempt to grant extra privileges: [...] user=&{myemail@gmail.com  [system:authenticated] map[]} ownerrules=[PolicyRule{Resources:["selfsubjectaccessreviews"], APIGroups:["authorization.k8s.io"], Verbs:["create"]} PolicyRule{NonResourceURLs:["/api" "/api/*" "/apis" "/apis/*" "/healthz" "/swagger-2.0.0.pb-v1" "/swagger.json" "/swaggerapi" "/swaggerapi/*" "/version"], Verbs:["get"]}] ruleResolutionErrors=[]
```

Possibly related to issues when attempting to deploy a function

```bash
> kubeless function ls
NAME                	NAMESPACE	HANDLER                	RUNTIME  	TYPE  	TOPIC            	DEPENDENCIES	STATUS
checkpoint-responder	default  	responder_kubeless.main	python2.7	PubSub	checkpoint-events	            	MISSING: Check controller logs

> kubectl logs kubeless-controller-58676964bb-d5mjk -n kubeless
...
E0120 23:49:37.589589       1 reflector.go:201] github.com/kubeless/kubeless/pkg/controller/controller.go:122: Failed to list *spec.Function: functions.k8s.io is forbidden: User "system:serviceaccount:kubeless:controller-acct" cannot list functions.k8s.io at the cluster scope: clusterrole.rbac.authorization.k8s.io "kubeless-controller-deployer" not found
Unknown user "system:serviceaccount:kubeless:controller-acct"
```
