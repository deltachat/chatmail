[Unit]
Description=Chatmail Postfix before queue filter

[Service]
ExecStart={execpath} {config_path}
Restart=always
RestartSec=30
User=filtermail

[Install]
WantedBy=multi-user.target
