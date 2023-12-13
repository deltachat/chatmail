{chatmail_domain}.                   A     {ipv4}
{chatmail_domain}.                   AAAA  {ipv6}
{chatmail_domain}.                   MX 10 {chatmail_domain}.
_submission._tcp.{chatmail_domain}.  SRV 0 1 587 {chatmail_domain}.
_submissions._tcp.{chatmail_domain}. SRV 0 1 465 {chatmail_domain}.
_imap._tcp.{chatmail_domain}.        SRV 0 1 143 {chatmail_domain}.
_imaps._tcp.{chatmail_domain}.       SRV 0 1 993 {chatmail_domain}.
{chatmail_domain}.                IN CAA 128 issue "letsencrypt.org;accounturi={acme_account_url}"
{chatmail_domain}.                   TXT "v=spf1 a:{chatmail_domain} -all"
_dmarc.{chatmail_domain}.            TXT "v=DMARC1;p=reject;rua=mailto:{email};ruf=mailto:{email};fo=1;adkim=r;aspf=r"
_mta-sts.{chatmail_domain}.          TXT "v=STSv1; id={sts_id}"
mta-sts.{chatmail_domain}.        IN CNAME {chatmail_domain}.
_smtp._tls.{chatmail_domain}.        TXT "v=TLSRPTv1;rua=mailto:{email}"
{dkim_entry}
