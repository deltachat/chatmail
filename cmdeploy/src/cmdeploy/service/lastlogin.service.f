[Unit]
Description=Dict proxy for last-login tracking

[Service]
ExecStart={execpath} /run/chatmail-lastlogin/lastlogin.socket {config_path}
Restart=always
RestartSec=30
User=vmail
RuntimeDirectory=chatmail-lastlogin

[Install]
WantedBy=multi-user.target
