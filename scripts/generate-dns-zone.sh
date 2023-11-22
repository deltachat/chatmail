#!/bin/sh
: ${CHATMAIL_DOMAIN:=c1.testrun.org}
: ${CHATMAIL_SSH:=$CHATMAIL_DOMAIN}

set -e
SSH="ssh root@$CHATMAIL_SSH"
EMAIL="root@$CHATMAIL_DOMAIN"
ACME_ACCOUNT_URL="$($SSH -- acmetool account-url)"

cat <<EOF
$CHATMAIL_DOMAIN. MX 10 $CHATMAIL_DOMAIN.
$CHATMAIL_DOMAIN. TXT "v=spf1 a:$CHATMAIL_DOMAIN -all"
_dmarc.$CHATMAIL_DOMAIN. TXT "v=DMARC1;p=reject;rua=mailto:$EMAIL;ruf=mailto:$EMAIL;fo=1;adkim=r;aspf=r"
_submission._tcp.$CHATMAIL_DOMAIN.  SRV 0 1 587 $CHATMAIL_DOMAIN.
_submissions._tcp.$CHATMAIL_DOMAIN. SRV 0 1 465 $CHATMAIL_DOMAIN.
_imap._tcp.$CHATMAIL_DOMAIN.        SRV 0 1 143 $CHATMAIL_DOMAIN.
_imaps._tcp.$CHATMAIL_DOMAIN.       SRV 0 1 993 $CHATMAIL_DOMAIN.
$CHATMAIL_DOMAIN. IN CAA 128 issue "letsencrypt.org;accounturi=$ACME_ACCOUNT_URL"
_mta-sts.$CHATMAIL_DOMAIN. IN TXT "v=STSv1; id=$(date -u '+%Y%m%d%H%M')"
mta-sts.$CHATMAIL_DOMAIN. IN CNAME $CHATMAIL_DOMAIN.
_smtp._tls.$CHATMAIL_DOMAIN. IN TXT "v=TLSRPTv1;rua=mailto:$EMAIL"
EOF
$SSH opendkim-genzone -F | sed 's/^;.*$//;/^$/d'
