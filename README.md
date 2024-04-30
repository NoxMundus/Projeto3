## Instalação do docker.
sudo yum install -y yum-utils

sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

sudo yum install docker

sudo groupadd docker

sudo usermod -aG docker ${USER}

sudo chmod 666 /var/run/docker.sock

sudo systemctl restart docker

## Instalação do kubectl
### fez a instalação do kubectl https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/

curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl.sha256"

echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check

sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

kubectl version --client

## Instalação do k3d/Criação do cluster
### fez a instalação do k3d usando o site https://k3d.io/v5.6.3/#install-specific-release

wget -q -O - https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | TAG=v5.0.0 bash

k3d cluster create clusterprojeto

## Na pasta onde está suba o deploy2.yaml, use o comando para subir o projeto
kubectl apply -f deploy2.yaml --validate=false

### Use o logs paras pegar o reseultado do pod do consumer, vai mostrar que o consumer pegou as mensagem e fez a validação
kubectl logs consumer-XXXXXXXXXX-XXXXX > app.txt
