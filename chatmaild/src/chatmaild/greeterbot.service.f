[Unit]
Description=Chatmail greeterbot, a Delta Chat bot to greet new users

[Service]
ExecStart={execpath} --passdb {passdb_path} --db_path /home/vmail/greeterbot/ --show-ffi
User=vmail
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
