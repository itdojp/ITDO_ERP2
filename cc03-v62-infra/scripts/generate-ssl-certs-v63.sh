#!/bin/bash
# CC03 v63.0 - SSL証明書生成スクリプト
# Day 1: 開発・本番対応SSL設定

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/../config"
SSL_DIR="${CONFIG_DIR}/ssl"

# 色付きログ関数
log_info() { echo -e "\033[36m[INFO]\033[0m $1"; }
log_success() { echo -e "\033[32m[SUCCESS]\033[0m $1"; }
log_warn() { echo -e "\033[33m[WARN]\033[0m $1"; }
log_error() { echo -e "\033[31m[ERROR]\033[0m $1"; }

# SSL証明書ディレクトリ作成
create_ssl_directory() {
    log_info "SSL証明書ディレクトリ作成中..."
    mkdir -p "${SSL_DIR}"
    chmod 755 "${SSL_DIR}"
    log_success "SSL証明書ディレクトリ作成完了: ${SSL_DIR}"
}

# 自己署名証明書生成 (開発環境用)
generate_self_signed_cert() {
    log_info "自己署名証明書生成中..."
    
    local domains=(
        "itdo-erp-v63.com"
        "www.itdo-erp-v63.com"
        "api.itdo-erp-v63.com"
        "auth.itdo-erp-v63.com"
        "monitor.itdo-erp-v63.com"
        "deploy.itdo-erp-v63.com"
        "localhost"
        "127.0.0.1"
    )
    
    # SAN設定作成
    local san_config="[SAN]\nsubjectAltName="
    for domain in "${domains[@]}"; do
        if [[ "${domain}" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            san_config+="\nIP:${domain}"
        else
            san_config+="\nDNS:${domain}"
        fi
        san_config+=","
    done
    san_config="${san_config%,}"  # 最後のカンマを削除
    
    # 証明書設定ファイル作成
    cat > "${SSL_DIR}/cert.conf" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = JP
ST = Tokyo
L = Tokyo
O = ITDO ERP Systems
OU = Infrastructure Team
CN = itdo-erp-v63.com

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = itdo-erp-v63.com
DNS.2 = www.itdo-erp-v63.com
DNS.3 = api.itdo-erp-v63.com
DNS.4 = auth.itdo-erp-v63.com
DNS.5 = monitor.itdo-erp-v63.com
DNS.6 = deploy.itdo-erp-v63.com
DNS.7 = localhost
IP.1 = 127.0.0.1
IP.2 = 10.0.0.1
EOF

    # 秘密鍵生成
    openssl genrsa -out "${SSL_DIR}/key.pem" 4096
    
    # 証明書署名要求 (CSR) 生成
    openssl req -new -key "${SSL_DIR}/key.pem" -out "${SSL_DIR}/cert.csr" -config "${SSL_DIR}/cert.conf"
    
    # 自己署名証明書生成
    openssl x509 -req -in "${SSL_DIR}/cert.csr" -signkey "${SSL_DIR}/key.pem" -out "${SSL_DIR}/cert.pem" \
        -days 365 -extensions v3_req -extfile "${SSL_DIR}/cert.conf"
    
    # 権限設定
    chmod 600 "${SSL_DIR}/key.pem"
    chmod 644 "${SSL_DIR}/cert.pem"
    
    # クリーンアップ
    rm -f "${SSL_DIR}/cert.csr" "${SSL_DIR}/cert.conf"
    
    log_success "自己署名証明書生成完了"
}

# Let's Encrypt証明書生成 (本番環境用)
generate_letsencrypt_cert() {
    log_info "Let's Encrypt証明書生成準備中..."
    
    if ! command -v certbot &> /dev/null; then
        log_warn "certbotがインストールされていません。自己署名証明書を使用します。"
        generate_self_signed_cert
        return
    fi
    
    read -p "メールアドレスを入力してください: " email
    read -p "ドメイン名を入力してください (例: itdo-erp-v63.com): " domain
    
    if [[ -z "${email}" || -z "${domain}" ]]; then
        log_warn "メールアドレスまたはドメイン名が未入力です。自己署名証明書を使用します。"
        generate_self_signed_cert
        return
    fi
    
    log_info "Let's Encrypt証明書を${domain}で生成中..."
    
    # Certbot実行 (スタンドアローンモード)
    certbot certonly --standalone \
        --email "${email}" \
        --agree-tos \
        --no-eff-email \
        -d "${domain}" \
        -d "www.${domain}" \
        -d "api.${domain}" \
        -d "auth.${domain}"
    
    # 証明書をNginx用にコピー
    if [[ -f "/etc/letsencrypt/live/${domain}/fullchain.pem" ]]; then
        cp "/etc/letsencrypt/live/${domain}/fullchain.pem" "${SSL_DIR}/cert.pem"
        cp "/etc/letsencrypt/live/${domain}/privkey.pem" "${SSL_DIR}/key.pem"
        chmod 644 "${SSL_DIR}/cert.pem"
        chmod 600 "${SSL_DIR}/key.pem"
        log_success "Let's Encrypt証明書設定完了"
    else
        log_error "Let's Encrypt証明書生成に失敗しました。自己署名証明書を使用します。"
        generate_self_signed_cert
    fi
}

# 証明書自動更新設定
setup_cert_renewal() {
    log_info "証明書自動更新設定中..."
    
    # 自動更新スクリプト作成
    cat > "${SCRIPT_DIR}/renew-ssl-certs.sh" << 'EOF'
#!/bin/bash
# SSL証明書自動更新スクリプト

set -euo pipefail

log_info() { echo -e "\033[36m[INFO]\033[0m $1"; }
log_success() { echo -e "\033[32m[SUCCESS]\033[0m $1"; }
log_error() { echo -e "\033[31m[ERROR]\033[0m $1"; }

log_info "SSL証明書更新チェック開始..."

if command -v certbot &> /dev/null; then
    # Let's Encrypt証明書更新
    if certbot renew --quiet; then
        log_success "証明書更新チェック完了"
        
        # Nginx設定テスト
        if docker exec itdo-nginx-v63 nginx -t; then
            # Nginx再読み込み
            docker exec itdo-nginx-v63 nginx -s reload
            log_success "Nginx設定再読み込み完了"
        else
            log_error "Nginx設定エラー"
            exit 1
        fi
    else
        log_info "証明書更新の必要なし"
    fi
else
    log_info "certbotがインストールされていません"
fi

log_success "証明書更新チェック完了"
EOF

    chmod +x "${SCRIPT_DIR}/renew-ssl-certs.sh"
    
    # Crontab設定追加
    (crontab -l 2>/dev/null || true; echo "0 3 * * * ${SCRIPT_DIR}/renew-ssl-certs.sh >> /var/log/ssl-renewal.log 2>&1") | crontab -
    
    log_success "証明書自動更新設定完了"
}

# 証明書情報表示
display_cert_info() {
    if [[ -f "${SSL_DIR}/cert.pem" ]]; then
        log_info "証明書情報:"
        openssl x509 -in "${SSL_DIR}/cert.pem" -text -noout | grep -A 10 "Subject:"
        echo
        log_info "証明書有効期限:"
        openssl x509 -in "${SSL_DIR}/cert.pem" -enddate -noout
        echo
        log_info "SAN (Subject Alternative Names):"
        openssl x509 -in "${SSL_DIR}/cert.pem" -text -noout | grep -A 20 "Subject Alternative Name"
    fi
}

# メイン実行
main() {
    log_info "CC03 v63.0 SSL証明書生成開始"
    
    create_ssl_directory
    
    echo "証明書タイプを選択してください:"
    echo "1) 自己署名証明書 (開発環境)"
    echo "2) Let's Encrypt証明書 (本番環境)"
    read -p "選択 (1 or 2): " cert_type
    
    case "${cert_type}" in
        1)
            generate_self_signed_cert
            ;;
        2)
            generate_letsencrypt_cert
            ;;
        *)
            log_warn "無効な選択です。自己署名証明書を生成します。"
            generate_self_signed_cert
            ;;
    esac
    
    setup_cert_renewal
    display_cert_info
    
    log_success "SSL証明書生成完了"
    log_info "証明書場所: ${SSL_DIR}"
    log_info "Nginx設定ファイル: ${CONFIG_DIR}/nginx-v63.conf"
}

# スクリプト実行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi