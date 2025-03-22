# Emby Media Cleanup Script

A utility script that lists all shows and movies in your Emby server that have not been watched in a specified period. It can also integrate with Sonarr and Radarr to get size information and delete unwatched media.

## Features

- Lists unwatched movies and TV shows
- Whitelist users whose watch history should be preserved
- Deletes media via Sonarr and Radarr API
- Delete unwatched media automatically or interactively
- Run as a one-time script or at scheduled intervals
- Filter by specific media libraries

## Usage

### Basic Usage

```bash
python script.py --server http://your-emby-server:8096 --api-key YOUR_API_KEY
```

### Run at Scheduled Intervals

```bash
python script.py --server http://your-emby-server:8096 --api-key YOUR_API_KEY --interval 24 --run-at-start
```

This will run the script every 24 hours, with an initial run at startup.

## Command Line Arguments

| Argument | Description |
|----------|-------------|
| `--server`, `-s` | Emby server URL (e.g., http://localhost:8096) |
| `--api-key`, `-k` | Emby API key for authentication |
| `--days`, `-d` | Number of days to look back for unwatched media (default: 90) |
| `--whitelist`, `-w` | Comma-separated list of whitelisted users (default: will) |
| `--libraries` | Comma-separated list of library names to check (default: all libraries) |
| `--list-libraries` | List all available libraries and exit |
| `--sonarr-url` | Sonarr server URL (e.g., http://localhost:8989) |
| `--sonarr-api-key` | Sonarr API key for authentication |
| `--radarr-url` | Radarr server URL (e.g., http://localhost:7878) |
| `--radarr-api-key` | Radarr API key for authentication |
| `--delete-mode` | Mode for deleting unwatched media: `interactive`, `all`, or `none` (default) |
| `--delete-files` | When deleting from Sonarr/Radarr, also delete the files from disk |
| `--dry-run` | Show what would be deleted without actually deleting anything |
| `--interval` | Run the script at specified interval (in hours) |
| `--run-at-start` | When using --interval, also run the script immediately at startup |

## Docker Usage

You can run the script in a Docker container with environment variables for configuration.

### Using docker-compose

1. Edit the provided `docker-compose.yml` file with your specific configuration.
2. Run the container:

```bash
docker-compose up -d
```

### Using Docker Run

```bash
docker run -d \
  --name media-cleanup \
  --restart unless-stopped \
  -e EMBY_SERVER=http://emby:8096 \
  -e EMBY_API_KEY=your_api_key_here \
  -e DAYS=90 \
  -e WHITELIST=will,jane \
  -e INTERVAL=24 \
  -e RUN_AT_START=true \
  -e SONARR_URL=http://sonarr:8989 \
  -e SONARR_API_KEY=your_sonarr_api_key \
  -e RADARR_URL=http://radarr:7878 \
  -e RADARR_API_KEY=your_radarr_api_key \
  -e DELETE_MODE=none \
  -e DRY_RUN=true \
  media-cleanup
```

### Environment Variables

All command-line options are available as environment variables:

| Environment Variable | Corresponding Argument |
|----------------------|------------------------|
| `EMBY_SERVER` | `--server` |
| `EMBY_API_KEY` | `--api-key` |
| `DAYS` | `--days` |
| `WHITELIST` | `--whitelist` |
| `LOG_LEVEL` | `--log-level` |
| `DEBUG_WHITELIST` | `--debug-whitelist` (set to "true" to enable) |
| `INCLUDE_RECENT` | `--include-recent` (set to "true" to enable) |
| `IGNORE_EPISODES` | `--ignore-episodes` (set to "true" to enable) |
| `IGNORE_RECENT_EPISODES` | `--ignore-recent-episodes` (set to "true" to enable) |
| `SONARR_URL` | `--sonarr-url` |
| `SONARR_API_KEY` | `--sonarr-api-key` |
| `RADARR_URL` | `--radarr-url` |
| `RADARR_API_KEY` | `--radarr-api-key` |
| `SORT_BY_SIZE` | `--sort-by-size` (set to "true" to enable) |
| `DELETE_MODE` | `--delete-mode` |
| `DELETE_FILES` | `--delete-files` (set to "true" to enable) |
| `MIN_AGE_DAYS` | `--min-age-days` |
| `DRY_RUN` | `--dry-run` (set to "true" to enable) |
| `LIBRARIES` | `--libraries` |
| `LIST_LIBRARIES` | `--list-libraries` (set to "true" to enable) |
| `INTERVAL` | `--interval` |
| `RUN_AT_START` | `--run-at-start` (set to "true" to enable) |

## Examples

### List All Libraries

```bash
python script.py --server http://your-emby-server:8096 --api-key YOUR_API_KEY --list-libraries
```

### Check Specific Libraries

```bash
python script.py --server http://your-emby-server:8096 --api-key YOUR_API_KEY --libraries "Movies,TV Shows"
```

### Automatic Deletion

```bash
python script.py --server http://your-emby-server:8096 --api-key YOUR_API_KEY --sonarr-url http://localhost:8989 --sonarr-api-key YOUR_SONARR_KEY --radarr-url http://localhost:7878 --radarr-api-key YOUR_RADARR_KEY --delete-mode all --dry-run
```

### Scheduled Clean-up

Run every week (168 hours) and automatically delete unwatched media:

```bash
python script.py --server http://your-emby-server:8096 --api-key YOUR_API_KEY --sonarr-url http://localhost:8989 --sonarr-api-key YOUR_SONARR_KEY --radarr-url http://localhost:7878 --radarr-api-key YOUR_RADARR_KEY --delete-mode all --interval 168 --run-at-start
```
