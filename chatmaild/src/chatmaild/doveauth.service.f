[Unit]
Description=Dict authentication proxy for dovecot

[Service]
ExecStart={execpath} /run/dovecot/doveauth.socket vmail /home/vmail/passdb.sqlite
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
