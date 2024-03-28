[Unit]
Description=Chatmail echo bot for testing it works

[Service]
ExecStart={execpath} {config_path}
Environment="PATH={remote_venv_dir}:$PATH"
Restart=always
RestartSec=30

# Apply security restrictions suggested by
#   systemd-analyze security echobot.service
CapabilityBoundingSet=
LockPersonality=true
MemoryDenyWriteExecute=true
NoNewPrivileges=true
PrivateDevices=true
PrivateMounts=true
PrivateTmp=true
PrivateUsers=true
ProtectClock=true
ProtectControlGroups=true
ProtectHostname=true
ProtectKernelLogs=true
ProtectKernelModules=true
ProtectKernelTunables=true
ProtectProc=noaccess

# Should be "strict", but we currently write /accounts folder in a protected path
ProtectSystem=full

RemoveIPC=true
RestrictAddressFamilies=AF_INET AF_INET6
RestrictNamespaces=true
RestrictRealtime=true
RestrictSUIDSGID=true
SystemCallArchitectures=native
SystemCallFilter=~@clock
SystemCallFilter=~@cpu-emulation
SystemCallFilter=~@debug
SystemCallFilter=~@module
SystemCallFilter=~@mount
SystemCallFilter=~@obsolete
SystemCallFilter=~@raw-io
SystemCallFilter=~@reboot
SystemCallFilter=~@resources
SystemCallFilter=~@swap
UMask=0077

[Install]
WantedBy=multi-user.target
