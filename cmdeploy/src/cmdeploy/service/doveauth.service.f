[Unit]
Description=Chatmail dict authentication proxy for dovecot

[Service]
ExecStart={execpath} /run/dovecot/doveauth.socket vmail /home/vmail/passdb.sqlite {config_path}
Restart=always
RestartSec=30
User=vmail

[Install]
WantedBy=multi-user.target
