#!/bin/bash

# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем необходимые пакеты
sudo apt install -y curl wget nginx certbot python3-certbot-nginx

# Устанавливаем k3s (Kubernetes)
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable traefik" sh -s -

# Ждем запуска k3s
sleep 30

# Получаем токен доступа
TOKEN=$(sudo cat /var/lib/rancher/k3s/server/node-token)
KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# Настраиваем kubectl
mkdir -p ~/.kube
sudo cp $KUBECONFIG ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config
export KUBECONFIG=~/.kube/config

# Устанавливаем Kubernetes Dashboard
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

# Создаем административный аккаунт для Dashboard
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin-user
  namespace: kubernetes-dashboard
EOF

# Даем права администратора
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-user
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: admin-user
  namespace: kubernetes-dashboard
EOF

# Получаем токен для входа в Dashboard
DASHBOARD_TOKEN=$(kubectl -n kubernetes-dashboard create token admin-user --duration=8760h)

# Устанавливаем cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.2/cert-manager.yaml

# Ждем запуска cert-manager
sleep 60

# Устанавливаем Nginx Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# Ждем запуска ingress-nginx
sleep 60

# Получаем сертификат Let's Encrypt для домена
DOMAIN="k8s.46.173.28.175.nip.io"
sudo certbot certonly --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@example.com

# Создаем секрет с TLS-сертификатом
sudo kubectl create secret tls dashboard-tls --cert=/etc/letsencrypt/live/$DOMAIN/fullchain.pem --key=/etc/letsencrypt/live/$DOMAIN/privkey.pem -n kubernetes-dashboard

# Создаем Ingress для доступа к Dashboard с HTTPS
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dashboard-ingress
  namespace: kubernetes-dashboard
  annotations:
    nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
    nginx.ingress.kubernetes.io/ssl-passthrough: "true"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - $DOMAIN
    secretName: dashboard-tls
  rules:
  - host: $DOMAIN
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: kubernetes-dashboard
            port:
              number: 443
EOF

# Настраиваем Nginx как reverse proxy с HTTPS
sudo rm /etc/nginx/sites-enabled/default
sudo bash -c "cat > /etc/nginx/sites-available/k8s-dashboard <<EOF
server {
    listen 80;
    server_name $DOMAIN 46.173.28.175;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name $DOMAIN 46.173.28.175;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    location / {
        proxy_pass https://kubernetes-dashboard.kubernetes-dashboard.svc.cluster.local:443;
        proxy_ssl_verify off;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Authorization \"Bearer $DASHBOARD_TOKEN\";
    }
}
EOF"

sudo ln -s /etc/nginx/sites-available/k8s-dashboard /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# Выводим информацию для доступа
echo "=================================================="
echo "Kubernetes Dashboard доступен по адресу:"
echo "https://46.173.28.175"
echo "Или:"
echo "https://k8s.46.173.28.175.nip.io"
echo ""
echo "Токен для входа в Dashboard:"
echo "$DASHBOARD_TOKEN"
echo ""
echo "ВНИМАНИЕ: При первом входе браузер может предупредить о недоверенном сертификате."
echo "Это нормально, так как используется самоподписанный сертификат."
echo "Нужно принять исключение безопасности в браузере."
echo "=================================================="