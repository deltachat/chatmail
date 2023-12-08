[Unit]
Description=Chatmail Postfix BeforeQeue filter 

[Service]
ExecStart={execpath} {config_path}
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
