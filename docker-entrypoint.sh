#!/bin/bash

# Build command-line arguments from environment variables
ARGS=""

# Mapping environment variables to command-line arguments
if [ -n "$EMBY_SERVER" ]; then
  ARGS="$ARGS --server $EMBY_SERVER"
fi

if [ -n "$EMBY_API_KEY" ]; then
  ARGS="$ARGS --api-key $EMBY_API_KEY"
fi

if [ -n "$DAYS" ]; then
  ARGS="$ARGS --days $DAYS"
fi

if [ -n "$WHITELIST" ]; then
  ARGS="$ARGS --whitelist $WHITELIST"
fi

if [ -n "$LOG_LEVEL" ]; then
  ARGS="$ARGS --log-level $LOG_LEVEL"
fi

if [ -n "$DEBUG_WHITELIST" ] && [ "$DEBUG_WHITELIST" = "true" ]; then
  ARGS="$ARGS --debug-whitelist"
fi

if [ -n "$INCLUDE_RECENT" ] && [ "$INCLUDE_RECENT" = "true" ]; then
  ARGS="$ARGS --include-recent"
fi

if [ -n "$IGNORE_EPISODES" ] && [ "$IGNORE_EPISODES" = "true" ]; then
  ARGS="$ARGS --ignore-episodes"
fi

if [ -n "$IGNORE_RECENT_EPISODES" ] && [ "$IGNORE_RECENT_EPISODES" = "true" ]; then
  ARGS="$ARGS --ignore-recent-episodes"
fi

if [ -n "$SONARR_URL" ]; then
  ARGS="$ARGS --sonarr-url $SONARR_URL"
fi

if [ -n "$SONARR_API_KEY" ]; then
  ARGS="$ARGS --sonarr-api-key $SONARR_API_KEY"
fi

if [ -n "$RADARR_URL" ]; then
  ARGS="$ARGS --radarr-url $RADARR_URL"
fi

if [ -n "$RADARR_API_KEY" ]; then
  ARGS="$ARGS --radarr-api-key $RADARR_API_KEY"
fi

if [ -n "$SORT_BY_SIZE" ] && [ "$SORT_BY_SIZE" = "true" ]; then
  ARGS="$ARGS --sort-by-size"
fi

if [ -n "$DELETE_MODE" ]; then
  ARGS="$ARGS --delete-mode $DELETE_MODE"
fi

if [ -n "$DELETE_FILES" ] && [ "$DELETE_FILES" = "true" ]; then
  ARGS="$ARGS --delete-files"
fi

if [ -n "$MIN_AGE_DAYS" ]; then
  ARGS="$ARGS --min-age-days $MIN_AGE_DAYS"
fi

if [ -n "$DRY_RUN" ] && [ "$DRY_RUN" = "true" ]; then
  ARGS="$ARGS --dry-run"
fi

if [ -n "$LIBRARIES" ]; then
  ARGS="$ARGS --libraries $LIBRARIES"
fi

if [ -n "$LIST_LIBRARIES" ] && [ "$LIST_LIBRARIES" = "true" ]; then
  ARGS="$ARGS --list-libraries"
fi

if [ -n "$INTERVAL" ]; then
  ARGS="$ARGS --interval $INTERVAL"
fi

if [ -n "$RUN_AT_START" ] && [ "$RUN_AT_START" = "true" ]; then
  ARGS="$ARGS --run-at-start"
fi

if [ -n "$DAEMON" ] && [ "$DAEMON" = "true" ]; then
  ARGS="$ARGS --daemon"
fi

# Output the constructed command for debugging
echo "Running command: python script.py $ARGS"

# Execute the script with the generated arguments
exec python script.py $ARGS
