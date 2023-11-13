#!/bin/sh
: ${CHATMAIL_DOMAIN:=c1.testrun.org}
: ${CHATMAIL_SERVER:=$CHATMAIL_DOMAIN}
: ${CHATMAIL_SSH:=$CHATMAIL_DOMAIN}

set -e
SSH="ssh root@$CHATMAIL_SSH"
EMAIL="root@$CHATMAIL_DOMAIN"
ACME_ACCOUNT_URL="$($SSH -- acmetool account-url)"

cat <<EOF
$CHATMAIL_DOMAIN. MX 10 $CHATMAIL_SERVER.
$CHATMAIL_DOMAIN. TXT "v=spf1 a:$CHATMAIL_SERVER -all"
_dmarc.$CHATMAIL_DOMAIN. TXT "v=DMARC1;p=reject;rua=mailto:$EMAIL;ruf=mailto:$EMAIL;fo=1;adkim=r;aspf=r"
_submission._tcp.$CHATMAIL_SERVER.  SRV 0 1 587 $CHATMAIL_SERVER.
_submissions._tcp.$CHATMAIL_SERVER. SRV 0 1 465 $CHATMAIL_SERVER.
_imap._tcp.$CHATMAIL_SERVER.        SRV 0 1 143 $CHATMAIL_SERVER.
_imaps._tcp.$CHATMAIL_SERVER.       SRV 0 1 993 $CHATMAIL_SERVER.
$CHATMAIL_DOMAIN. IN CAA 128 issue "letsencrypt.org;accounturi=$ACME_ACCOUNT_URL"
_mta-sts.$CHATMAIL_DOMAIN. IN TXT "v=STSv1; id=$(date -u '+%Y%m%d%H%M')"
mta-sts.$CHATMAIL_SERVER. IN CNAME $CHATMAIL_SERVER.
_smtp._tls.$CHATMAIL_SERVER. IN TXT "v=TLSRPTv1;rua=mailto:$EMAIL"
EOF
if [ "$CHATMAIL_DOMAIN" != "$CHATMAIL_SERVER" ]; then
cat <<EOF
mta-sts.$CHATMAIL_DOMAIN. IN CNAME mta-sts.$CHATMAIL_SERVER.
_smtp._tls.$CHATMAIL_DOMAIN. IN CNAME _smtp._tls.$CHATMAIL_SERVER.
EOF
fi
$SSH opendkim-genzone -F | sed 's/^;.*$//;/^$/d'
