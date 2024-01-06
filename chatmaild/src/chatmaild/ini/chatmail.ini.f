[params]

# mail domain (MUST be set to fully qualified chat mail domain)
mail_domain = {mail_domain}

#
# If you only do private test deploys, you don't need to modify any settings below
#

#
# Account Restrictions
#

# how many mails a user can send out per minute
max_user_send_per_minute = 60

# maximum mailbox size of a chatmail account
max_mailbox_size = 100M

# days after which mails are unconditionally deleted
delete_mails_after = 40

# minimum length a username must have
username_min_length = 9

# maximum length a username can have
username_max_length = 9

# minimum length a password must have
password_min_length = 9

# list of chatmail accounts which can send outbound un-encrypted mail
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

