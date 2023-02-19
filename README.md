# python-concurrent-ingestion-redis

[![CI](https://github.com/rcbop/python-concurrent-ingestion-redis-exercise/actions/workflows/ci.yaml/badge.svg)](https://github.com/rcbop/python-concurrent-ingestion-redis-exercise/actions/workflows/ci.yaml)

exercise demo of concurrent consumers using redis cached data structure for synchronization

```bash
REDIS_PASS=12345 docker compose up --build
```

![docs](docs/concurrent-workers-shared.drawio.png)