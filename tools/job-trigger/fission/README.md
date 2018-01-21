# Fission deployment

### Status

Currently unclear on to send a message to fission NATS deployment, i.e. the following fails

```bash
python nats-pub.py checkpoint-events -s http://localhost:4222 -d 'hi'
Handling connection for 4222
E0120 16:47:05.760734   14632 portforward.go:331] an error occurred forwarding 4222 -> 4222: error forwarding port 4222 to pod 375c007b49eac75f372ee4fc13874a0699222bd5ca5e940353b1a968c80ee352, uid : exit status 1: 2018/01/21 00:47:05 socat[11993] E connect(6, AF=2 127.0.0.1:4222, 16): Connection refused
```

despite the NATS pod 4222 was proxied to the same on localhost with the following

```bash
NATS_POD_NAME=$(kubectl -n fission get pod -o name|grep nats|cut -f2 -d'/')
kubectl -n fission port-forward ${NATS_POD_NAME} 4222:4222 &
```
