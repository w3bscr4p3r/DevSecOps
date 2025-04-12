backup-system/
├── docker-compose.yml
├── .env (arquivo de variáveis de ambiente)
├── mysql/
│   ├── conf/
│   │   └── my.cnf (configurações customizadas)
│   └── data/
├── backup/
│   ├── scripts/
│   │   ├── backup_manager.py
│   │   ├── restore_tool.py
│   │   ├── encryption.py
│   │   └── retention_policy.py
│   ├── logs/
│   ├── config/
│   │   └── settings.ini
│   └── requirements.txt
├── backups/
└── monitoring/
    ├── disk_check.py
    └── healthcheck.sh
