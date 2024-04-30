1 - Fazer o ingress funcionar (possivelmente o ingress ja funciona se for utilizado em um maquina local ao invés de rodar na AWS como no meu caso)

2 - Colocar um SECRET

3 - Colocar no yaml o initContainers nos pods do consumer e producer de forma a garantir que eles só subam após os podes do rabbitmq/redis/minio