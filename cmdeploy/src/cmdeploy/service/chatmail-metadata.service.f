[Unit]
Description=Chatmail dict proxy for IMAP METADATA

[Service]
ExecStart={execpath} /run/chatmail-metadata/metadata.socket /home/vmail/mail/{mail_domain}
Restart=always
RestartSec=30
User=vmail
RuntimeDirectory=chatmail-metadata

[Install]
WantedBy=multi-user.target
