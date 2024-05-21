# keabot-py
## Build
`docker build -t keabot:latest .`
## Persistant data
`docker volume create data`
`docker volume create token`
## Deploy
`docker run --restart always -d -v <data>:/app/Data:rw -v <token>:/secret:ro keabot:latest`
`<data>` should be a volume containing `/images`, `/logs`, and `/backup`.
Use the same name as the data volume above.
`<token>` should be a volume containing a token file (default name `token`).
Use the same name as the token volume above.
## Assumptions
A `clownScore.json` in the project's root directory at build time.

