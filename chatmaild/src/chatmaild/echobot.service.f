[Unit]
Description=Chatmail echo bot for testing it works

[Service]
ExecStart={execpath} {config_path}
Environment="PATH={remote_venv_dir}:$PATH"
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
