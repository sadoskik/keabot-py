# keabot-py
## Build and Deploy
`docker compose build`
### Persistant data
Place a folder named "data" in this directory. It will be mounted in the container and give persistent data access across instances of the bot. Additionally, you are able to view logs here and inspect the database without needing to exec into the running container.
### Credentials
Place your discord developer token in a file named discord_secret.token in this directory

`./discord_secret.token`

### Launch
Launch bot detached (no interactive terminal)

`docker compose up -d`

## Technology

### discord.py
This python library wraps the Discord API and provides some great abstraction of a Discord bot's runtime environment.

https://discordpy.readthedocs.io/en/stable/

Thanks to the tools it provides, Keabot only needs to implement event listeners to add functionality. This is done entirely in the keabot.py module. A `Keabot` class extends the discord.py class so that metadata can be accesible to the event listeners. For instance, the database connection is accessed frequently in the image functionality, but the connection does not exist until Keabot is instatiated.

### Image Tagging
Keabot supports user submissions of photos/videos (`..addImage`) with at least one tag associated. Typically the tag is the name of a person in the photo, but could be anything. Keabot now supports multiple tags for a single image. These tags are used with the `..postImage` command so that Keabot will select a random image with that tag and post it. Tags can be enumerated (`..tags`) for a server and deleted (`..deleteTag`). Currently there is not support for orphaned image detection/deletion.

To support the image tagging and fetching feature, an SQLite3 database keeps track of image names and their corresponding tags. This is achieved with three tables `image`, `tag`, and `image_tag`. `image_tag` facilitates the many-many relationship between images and tags.

#### Image Table
```python
cursor.execute('''
        CREATE TABLE IF NOT EXISTS image (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            server_id TEXT NOT NULL
        )
```
#### Tag Table
```python
cursor.execute('''
        CREATE TABLE IF NOT EXISTS tag (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            server_id TEXT NOT NULL,
            UNIQUE(name, server_id)  -- Ensures unique combinations of 'name' and 'server_id'
        )
    ''')
```
#### Image_tag Table
```python
cursor.execute('''
        CREATE TABLE IF NOT EXISTS image_tag (
            image_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            FOREIGN KEY (image_id) REFERENCES image(id),
            FOREIGN KEY (tag_id) REFERENCES tag(id),
            PRIMARY KEY (image_id, tag_id)
        )
    ''')
```
### User Scoring
Keabot's original purpose was to track when users' messages are given "gold". This generates a score for each user on a server. That scoring system is also tracked in the SQLite3 database under a `user` table. Additionally, it tracks how generous people are (`given`) and how often they give themselves gold (`self`)
#### User Table
```python
cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            score INTEGER NOT NULL,
            given INTEGER NOT NULL,
            self INTEGER NOT NULL,
            UNIQUE(server_id, user_id)  -- Ensures unique combinations of 'server_id' and 'user_id'
        )
    ''')
```
