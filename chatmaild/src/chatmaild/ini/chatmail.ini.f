[params]

# mail domain (MUST be set to fully qualified chat mail domain)
mail_domain = {mail_domain}

#
# If you only do private test deploys, you don't need to modify any settings below
#

#
# Restrictions on user addresses
#

# how many mails a user can send out per minute
max_user_send_per_minute = 60

# maximum mailbox size of a chatmail address
max_mailbox_size = 100M

# maximum message size for an e-mail in bytes
max_message_size = 31457280

# days after which mails are unconditionally deleted
delete_mails_after = 20

# days after which users without a login are deleted (database and mails)
delete_inactive_users_after = 100

# minimum length a username must have
username_min_length = 9

# maximum length a username can have
username_max_length = 9

# minimum length a password must have
password_min_length = 9

# list of chatmail addresses which can send outbound un-encrypted mail
passthrough_senders =

# list of e-mail recipients for which to accept outbound un-encrypted mails
passthrough_recipients = xstore@testrun.org groupsbot@hispanilandia.net

#
# Deployment Details
#

# where the filtermail SMTP service listens
filtermail_smtp_port = 10080

# postfix accepts on the localhost reinject SMTP port
postfix_reinject_port = 10025

# if set to "True" IPv6 is disabled
disable_ipv6 = False

#
# Privacy Policy
#

# postal address of privacy contact
privacy_postal =

# email address of privacy contact
privacy_mail =

# postal address of the privacy data officer
privacy_pdo =

# postal address of the privacy supervisor
privacy_supervisor =
