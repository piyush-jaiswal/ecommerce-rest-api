#!/bin/bash
set -euo pipefail # Exit on error, undefined vars, and pipeline failures
IFS=$'\n\t'       # Stricter word splitting

# Capture ALL Docker rules BEFORE any flushing
echo "Capturing existing Docker rules..."
DOCKER_NAT_CHAINS=$(iptables-save -t nat | grep "^-N DOCKER" || true)
DOCKER_NAT_RULES=$(iptables-save -t nat | grep -E "^-A (DOCKER|PREROUTING|OUTPUT|POSTROUTING).*(docker|DOCKER|127\.0\.0\.11)" || true)
DOCKER_FILTER_CHAINS=$(iptables-save -t filter | grep "^-N DOCKER" || true)
DOCKER_FILTER_RULES=$(iptables-save -t filter | grep -E "^-A (DOCKER|FORWARD).*(docker|DOCKER|docker0)" || true)

# Flush existing rules and delete existing ipsets
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X
ipset destroy allowed-domains 2>/dev/null || true

# Ensure default chain policies are permissive before applying rules or making network calls
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT

# Restore Docker NAT chains and rules
echo "Restoring Docker NAT chains..."
for chain in DOCKER DOCKER-INGRESS DOCKER_OUTPUT DOCKER_POSTROUTING; do
	iptables -t nat -N "$chain" 2>/dev/null || true
done
# Also replay any chains captured from the live ruleset
if [ -n "$DOCKER_NAT_CHAINS" ]; then
	while IFS= read -r rule; do
		iptables -t nat $rule 2>/dev/null || true
	done <<<"$DOCKER_NAT_CHAINS"
fi
if [ -n "$DOCKER_NAT_RULES" ]; then
	echo "Restoring Docker NAT rules..."
	while IFS= read -r rule; do
		iptables -t nat $rule 2>/dev/null || true
	done <<<"$DOCKER_NAT_RULES"
else
	echo "No Docker NAT rules to restore"
fi

# Restore Docker filter chains and rules
echo "Restoring Docker filter chains..."
for chain in DOCKER DOCKER-ISOLATION-STAGE-1 DOCKER-ISOLATION-STAGE-2 DOCKER-USER; do
	iptables -N "$chain" 2>/dev/null || true
done
if [ -n "$DOCKER_FILTER_CHAINS" ]; then
	while IFS= read -r rule; do
		iptables $rule 2>/dev/null || true
	done <<<"$DOCKER_FILTER_CHAINS"
fi
if [ -n "$DOCKER_FILTER_RULES" ]; then
	echo "Restoring Docker filter rules..."
	while IFS= read -r rule; do
		iptables $rule 2>/dev/null || true
	done <<<"$DOCKER_FILTER_RULES"
else
	echo "No Docker filter rules to restore"
fi

# Allow established/related traffic (both directions)
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# allow outbound DNS (UDP; allow TCP fallback too)
iptables -A OUTPUT -p udp --dport 53 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT

# allow outbound SSH
iptables -A OUTPUT -p tcp --dport 22 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT

# Allow localhost
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow Docker bridge networking
iptables -A INPUT -i docker0 -j ACCEPT
iptables -A OUTPUT -o docker0 -j ACCEPT
iptables -A FORWARD -i docker0 -j ACCEPT
iptables -A FORWARD -o docker0 -j ACCEPT

# Create ipset with CIDR support
ipset create allowed-domains hash:net -exist
ipset flush allowed-domains

# Fetch GitHub meta information and aggregate + add their IP ranges
echo "Fetching GitHub IP ranges..."
gh_ranges=$(curl -s https://api.github.com/meta)
if [ -z "$gh_ranges" ]; then
	echo "ERROR: Failed to fetch GitHub IP ranges"
	exit 1
fi

if ! echo "$gh_ranges" | jq -e '.web and .api and .git' >/dev/null; then
	echo "ERROR: GitHub API response missing required fields"
	exit 1
fi

echo "Processing GitHub IPs..."
while read -r cidr; do
	if [[ ! "$cidr" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/[0-9]{1,2}$ ]]; then
		echo "ERROR: Invalid CIDR range from GitHub meta: $cidr"
		exit 1
	fi
	echo "Adding GitHub range $cidr"
	ipset add allowed-domains "$cidr" -exist
done < <(echo "$gh_ranges" | jq -r '(.web + .api + .git)[]' | aggregate -q)

# Resolve and add other allowed domains
for domain in \
	"marketplace.visualstudio.com" \
	"*.gallerycdn.vsassets.io" \
	"vscode.blob.core.windows.net" \
	"update.code.visualstudio.com" \
	"pypi.org" \
	"files.pythonhosted.org" \
	"auth.docker.io" \
	"index.docker.io" \
	"registry-1.docker.io"; do
	echo "Resolving $domain..."
	ips=$(dig +noall +answer A "$domain" | awk '$4 == "A" {print $5}')
	if [ -z "$ips" ]; then
		echo "ERROR: Failed to resolve $domain"
		exit 1
	fi

	while read -r ip; do
		if [[ ! "$ip" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
			echo "ERROR: Invalid IP from DNS for $domain: $ip"
			exit 1
		fi
		echo "Adding $ip for $domain"
		ipset add allowed-domains "$ip" -exist
	done < <(echo "$ips")
done

# Get host IP from default route
HOST_IP=$(ip route | grep default | cut -d" " -f3)
if [ -z "$HOST_IP" ]; then
	echo "ERROR: Failed to detect host IP"
	exit 1
fi

HOST_NETWORK=$(echo "$HOST_IP" | sed "s/\.[0-9]*$/.0\/24/")
echo "Host network detected as: $HOST_NETWORK"

# Set up remaining iptables rules
iptables -A INPUT -s "$HOST_NETWORK" -j ACCEPT
iptables -A OUTPUT -d "$HOST_NETWORK" -j ACCEPT

# Set default policies to DROP first
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT DROP

# First allow established connections for already approved traffic
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Then allow only specific outbound traffic to allowed domains
iptables -A OUTPUT -m set --match-set allowed-domains dst -j ACCEPT

# Explicitly REJECT all other outbound traffic for immediate feedback
iptables -A OUTPUT -j REJECT --reject-with icmp-admin-prohibited

echo "Firewall configuration complete"
echo "Verifying firewall rules..."
if curl --connect-timeout 5 https://example.com >/dev/null 2>&1; then
	echo "ERROR: Firewall verification failed - was able to reach https://example.com"
	exit 1
else
	echo "Firewall verification passed - unable to reach https://example.com as expected"
fi

# Verify GitHub API access
if ! curl --connect-timeout 5 https://api.github.com/zen >/dev/null 2>&1; then
	echo "ERROR: Firewall verification failed - unable to reach https://api.github.com"
	exit 1
else
	echo "Firewall verification passed - able to reach https://api.github.com as expected"
fi
