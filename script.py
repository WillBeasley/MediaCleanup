import requests
import datetime
import logging
import sys
import argparse
from typing import List, Dict, Any, Optional, Set
from requests.exceptions import RequestException
import time
import signal
import os

#!/usr/bin/env python3
"""
script.py - Emby Media Cleanup Script
Lists all shows and movies that have not been watched in the last X days.
Integrates with Sonarr and Radarr to support deleting media from the library.
Can run as a one-time script or at scheduled intervals.
"""


# Configure logging - updated to remove milliseconds
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',  # Format without milliseconds
    force=True  # Ensure logging configuration is applied even if previously configured
)
logger = logging.getLogger(__name__)

# Force unbuffered output for Docker compatibility
if os.environ.get('PYTHONUNBUFFERED') != '1':
    # Auto-flush stdout
    os.environ['PYTHONUNBUFFERED'] = '1'
    
# Add helper function for print with flush
def print_flush(*args, **kwargs):
    """Print with flush=True to ensure output is immediately visible."""
    kwargs['flush'] = True
    print(*args, **kwargs)

class EmbyClient:
    def __init__(self, server_url: str, api_key: str, whitelisted_users: Set[str] = None):
        """Initialize the Emby API client.
        
        Args:
            server_url: The base URL of the Emby server
            api_key: The API key for authentication
            whitelisted_users: Set of usernames whose watched history should prevent deletion
        """
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'X-Emby-Token': api_key,
            'Content-Type': 'application/json'
        }
        self.whitelisted_users = whitelisted_users or set()
        logger.info(f"Initialized EmbyClient for server: {server_url}")
        logger.info(f"Whitelisted users: {', '.join(self.whitelisted_users) if self.whitelisted_users else 'None'}")
    
    def get_libraries(self) -> List[Dict[str, Any]]:
        """Get all media libraries from the Emby server."""
        logger.info("Fetching media libraries")
        try:
            response = requests.get(
                f"{self.server_url}/emby/Library/VirtualFolders",
                headers=self.headers
            )
            response.raise_for_status()
            libraries = response.json()
            logger.info(f"Found {len(libraries)} libraries")
            return libraries
        except RequestException as e:
            logger.error(f"Error fetching libraries: {e}")
            return []
    
    def get_items_by_library(self, library_id: str) -> List[Dict[str, Any]]:
        """Get all media items from a specific library."""
        logger.info(f"Fetching items from library ID: {library_id}")
        try:
            response = requests.get(
                f"{self.server_url}/emby/Items",
                headers=self.headers,
                params={
                    'ParentId': library_id,
                    'Recursive': True,
                    'IncludeItemTypes': 'Movie,Series',
                    'Fields': 'DateLastPlayed,Path,MediaStreams,Overview,DateCreated',
                    'SortBy': 'DateCreated,SortName',
                    'SortOrder': 'Descending'
                }
            )
            response.raise_for_status()
            items = response.json().get('Items', [])
            logger.info(f"Found {len(items)} items in library")
            return items
        except RequestException as e:
            logger.error(f"Error fetching items from library {library_id}: {e}")
            return []
    
    def get_users(self) -> List[Dict[str, Any]]:
        """Get all users from the Emby server."""
        logger.info("Fetching users")
        try:
            response = requests.get(
                f"{self.server_url}/emby/Users",
                headers=self.headers
            )
            response.raise_for_status()
            users = response.json()
            logger.info(f"Found {len(users)} users")
            return users
        except RequestException as e:
            logger.error(f"Error fetching users: {e}")
            return []
    
    def get_user_items_by_library(self, user_id: str, library_id: str) -> List[Dict[str, Any]]:
        """Get all media items from a specific library for a specific user."""
        logger.info(f"Fetching items from library ID: {library_id} for user ID: {user_id}")
        try:
            response = requests.get(
                f"{self.server_url}/emby/Users/{user_id}/Items",
                headers=self.headers,
                params={
                    'ParentId': library_id,
                    'Recursive': True,
                    'IncludeItemTypes': 'Movie,Series',
                    'Fields': 'DateLastPlayed,Path,MediaStreams,Overview,UserData',
                    'SortBy': 'DateCreated,SortName',
                    'SortOrder': 'Descending'
                }
            )
            response.raise_for_status()
            items = response.json().get('Items', [])
            logger.info(f"Found {len(items)} items in library for user")
            return items
        except RequestException as e:
            logger.error(f"Error fetching items from library {library_id} for user {user_id}: {e}")
            return []
    
    def get_episodes_by_series(self, series_id: str) -> List[Dict[str, Any]]:
        """Get all episodes for a specific series."""
        logger.info(f"Fetching episodes for series ID: {series_id}")
        try:
            response = requests.get(
                f"{self.server_url}/emby/Items",
                headers=self.headers,
                params={
                    'ParentId': series_id,
                    'Recursive': True,
                    'IncludeItemTypes': 'Episode',
                    'Fields': 'DateLastPlayed,Path,MediaStreams,Overview,UserData,DateCreated',
                    'SortBy': 'DateCreated',
                    'SortOrder': 'Descending'
                }
            )
            response.raise_for_status()
            items = response.json().get('Items', [])
            logger.info(f"Found {len(items)} episodes for series")
            return items
        except RequestException as e:
            logger.error(f"Error fetching episodes for series {series_id}: {e}")
            return []
    
    def get_user_episodes_by_series(self, user_id: str, series_id: str) -> List[Dict[str, Any]]:
        """Get all episodes for a specific series for a specific user."""
        logger.info(f"Fetching episodes for series ID: {series_id} for user ID: {user_id}")
        try:
            response = requests.get(
                f"{self.server_url}/emby/Users/{user_id}/Items",
                headers=self.headers,
                params={
                    'ParentId': series_id,
                    'Recursive': True,
                    'IncludeItemTypes': 'Episode',
                    'Fields': 'DateLastPlayed,Path,MediaStreams,Overview,UserData',
                    'SortBy': 'SortName',
                    'SortOrder': 'Ascending'
                }
            )
            response.raise_for_status()
            items = response.json().get('Items', [])
            logger.info(f"Found {len(items)} episodes for series for user")
            return items
        except RequestException as e:
            logger.error(f"Error fetching episodes for series {series_id} for user {user_id}: {e}")
            return []
    
    def get_unwatched_items(self, days: int = 90, library_names: Set[str] = None) -> List[Dict[str, Any]]:
        """Get all items that haven't been watched in the specified number of days
           by anyone, excluding items watched by whitelisted users and recently added items.
        
        Args:
            days: Number of days to look back
            library_names: Set of library names to check (if None, check all libraries)
            
        Returns:
            List of unwatched items
        """
        logger.info(f"Looking for items not watched in the last {days} days")
        cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        
        # Get all users first to identify whitelisted users by ID
        users = self.get_users()
        whitelisted_user_ids = set()
        whitelisted_user_names = set()
        for user in users:
            user_name = user.get('Name', '')
            if user_name.lower() in [name.lower() for name in self.whitelisted_users]:
                whitelisted_user_ids.add(user.get('Id'))
                whitelisted_user_names.add(user_name)
                logger.info(f"Found whitelisted user: {user_name} (ID: {user.get('Id')})")
        
        # Log if any whitelisted users weren't found
        for whitelist_name in self.whitelisted_users:
            if not any(wname.lower() == whitelist_name.lower() for wname in whitelisted_user_names):
                logger.warning(f"Whitelisted user '{whitelist_name}' not found on the server")
        
        unwatched_items = []
        watched_by_whitelisted = set()  # Item IDs watched by whitelisted users
        libraries = self.get_libraries()
        
        # Filter libraries if library_names is specified
        if library_names:
            filtered_libraries = []
            for library in libraries:
                if library.get('Name') and library.get('Name') in library_names:
                    filtered_libraries.append(library)
                    logger.info(f"Including library: {library.get('Name')}")
                else:
                    logger.debug(f"Excluding library: {library.get('Name')}")
            
            if not filtered_libraries:
                logger.warning(f"None of the specified libraries were found. Available libraries: {', '.join([lib.get('Name', 'Unknown') for lib in libraries])}")
                return []
                
            libraries = filtered_libraries
            logger.info(f"Checking {len(libraries)} libraries based on specified filter")
        else:
            logger.info(f"Checking all {len(libraries)} available libraries")
        
        # First, get items watched by whitelisted users
        if whitelisted_user_ids:
            logger.info(f"Checking watch history for {len(whitelisted_user_ids)} whitelisted users")
            for library in libraries:
                library_id = library.get('ItemId')
                if not library_id:
                    continue
                
                for user_id in whitelisted_user_ids:
                    user_items = self.get_user_items_by_library(user_id, library_id)
                    for item in user_items:
                        # Check the user-specific watching data
                        user_data = item.get('UserData', {})
                        last_played = user_data.get('LastPlayedDate')
                        played_percentage = user_data.get('PlayedPercentage', 0)
                        played = user_data.get('Played', False)
                        
                        # Consider an item as watched if:
                        # 1. It was played recently OR
                        # 2. It was played at all AND marked as "played" OR
                        # 3. It was played more than a certain percentage
                        if ((last_played and last_played > cutoff_date) or 
                            played or 
                            played_percentage > 75):
                            # Log which items are being excluded and why
                            logger.debug(f"Whitelisted exclusion: {item.get('Name')} - " +
                                        f"Last played: {last_played}, " +
                                        f"Played: {played}, " +
                                        f"Percentage: {played_percentage}%")
                            watched_by_whitelisted.add(item.get('Id'))
                            
                            # For TV shows, also check if any episodes were watched recently
                            if item.get('Type') == 'Series':
                                series_id = item.get('Id')
                                logger.debug(f"Checking episodes for series: {item.get('Name')}")
                                episodes = self.get_user_episodes_by_series(user_id, series_id)
                                
                                # Check if any episodes were watched recently
                                for episode in episodes:
                                    ep_user_data = episode.get('UserData', {})
                                    ep_last_played = ep_user_data.get('LastPlayedDate')
                                    ep_played = ep_user_data.get('Played', False)
                                    ep_played_percentage = ep_user_data.get('PlayedPercentage', 0)
                                    
                                    if ((ep_last_played and ep_last_played > cutoff_date) or 
                                        ep_played or 
                                        ep_played_percentage > 75):
                                        # If any episode was watched, exclude the whole series
                                        logger.debug(f"Series exclusion: {item.get('Name')} - episode {episode.get('Name')} was watched")
                                        watched_by_whitelisted.add(series_id)
                                        break
            
            logger.info(f"Found {len(watched_by_whitelisted)} items watched by whitelisted users")
        
        # Now get items not watched by anyone
        for library in libraries:
            library_id = library.get('ItemId')
            library_name = library.get('Name')
            
            if not library_id:
                continue
            
            logger.info(f"Processing library: {library_name}")
            items = self.get_items_by_library(library_id)
            
            for item in items:
                item_id = item.get('Id')
                item_name = item.get('Name', 'Unknown')
                
                if item_id in watched_by_whitelisted:
                    logger.debug(f"Skipping {item_name} - watched by whitelisted user")
                    continue
                
                # For TV shows, check if any episodes were recently watched by anyone
                if item.get('Type') == 'Series' and item_id not in watched_by_whitelisted:
                    series_id = item.get('Id')
                    episodes = self.get_episodes_by_series(series_id)
                    
                    # Check if any episode was recently watched
                    recently_watched = False
                    for episode in episodes:
                        ep_last_played = episode.get('DateLastPlayed')
                        if ep_last_played and ep_last_played > cutoff_date:
                            logger.debug(f"Skipping {item_name} - episode {episode.get('Name')} recently watched")
                            recently_watched = True
                            break
                    
                    if recently_watched:
                        continue
                
                # Skip recently added items
                date_created = item.get('DateCreated')
                if date_created and date_created > cutoff_date:
                    logger.debug(f"Skipping {item_name} - recently added (after {cutoff_date})")
                    continue
                    
                last_played = item.get('DateLastPlayed')
                if not last_played or last_played < cutoff_date:
                    item['LibraryName'] = library_name
                    unwatched_items.append(item)
        
        logger.info(f"Found {len(unwatched_items)} unwatched items (excluding those watched by whitelisted users and recently added items)")
        return unwatched_items

class SonarrClient:
    """Client for interacting with the Sonarr API."""
    
    def __init__(self, server_url: str, api_key: str):
        """Initialize Sonarr API client.
        
        Args:
            server_url: Base URL of the Sonarr server
            api_key: API key for authentication
        """
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.headers = {'X-Api-Key': api_key}
        self._series_cache = None
        logger.info(f"Initialized SonarrClient for server: {server_url}")
    
    def get_all_series(self) -> List[Dict[str, Any]]:
        """Fetch all series from Sonarr."""
        if self._series_cache is not None:
            logger.debug("Using cached Sonarr series data")
            return self._series_cache
        
        logger.info("Fetching all series from Sonarr")
        try:
            response = requests.get(
                f"{self.server_url}/api/v3/series",
                headers=self.headers
            )
            response.raise_for_status()
            series_list = response.json()
            self._series_cache = series_list
            logger.info(f"Found {len(series_list)} series in Sonarr")
            return series_list
        except RequestException as e:
            logger.error(f"Error fetching series from Sonarr: {e}")
            return []
    
    def find_series_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """Find a series by title."""
        logger.debug(f"Looking for series '{title}' in Sonarr")
        all_series = self.get_all_series()
        
        # Try exact match first
        for series in all_series:
            if series.get('title', '').lower() == title.lower():
                return series
        
        # Try fuzzy matching if exact match fails
        for series in all_series:
            if title.lower() in series.get('title', '').lower() or series.get('title', '').lower() in title.lower():
                return series
        
        return None
    
    def delete_series(self, series_id: int, delete_files: bool = False) -> bool:
        """Delete a series from Sonarr.
        
        Args:
            series_id: The ID of the series to delete
            delete_files: Whether to delete the series files from disk
            
        Returns:
            Whether the operation was successful
        """
        # Get the series name before deletion
        series_name = next((s.get('title', 'Unknown') for s in self.get_all_series() if s.get('id') == series_id), 'Unknown')
        logger.info(f"Deleting series '{series_name}' (ID: {series_id}) from Sonarr (delete_files={delete_files})")
        try:
            response = requests.delete(
                f"{self.server_url}/api/v3/series/{series_id}",
                headers=self.headers,
                params={
                    'deleteFiles': str(delete_files).lower()
                }
            )
            response.raise_for_status()
            
            # Update cache if successful deletion
            if self._series_cache is not None:
                self._series_cache = [s for s in self._series_cache if s.get('id') != series_id]
                logger.debug(f"Updated series cache after deletion")
                
            logger.info(f"Successfully deleted series '{series_name}' (ID: {series_id})")
            return True
        except RequestException as e:
            logger.error(f"Error deleting series '{series_name}' (ID: {series_id}): {e}")
            return False

class RadarrClient:
    """Client for interacting with the Radarr API."""
    
    def __init__(self, server_url: str, api_key: str):
        """Initialize Radarr API client.
        
        Args:
            server_url: Base URL of the Radarr server
            api_key: API key for authentication
        """
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.headers = {'X-Api-Key': api_key}
        self._movies_cache = None
        logger.info(f"Initialized RadarrClient for server: {server_url}")
    
    def get_all_movies(self) -> List[Dict[str, Any]]:
        """Fetch all movies from Radarr."""
        if self._movies_cache is not None:
            logger.debug("Using cached Radarr movies data")
            return self._movies_cache
            
        logger.info("Fetching all movies from Radarr")
        try:
            response = requests.get(
                f"{self.server_url}/api/v3/movie",
                headers=self.headers
            )
            response.raise_for_status()
            movie_list = response.json()
            self._movies_cache = movie_list
            logger.info(f"Found {len(movie_list)} movies in Radarr")
            return movie_list
        except RequestException as e:
            logger.error(f"Error fetching movies from Radarr: {e}")
            return []
    
    def find_movie_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """Find a movie by title."""
        logger.debug(f"Looking for movie '{title}' in Radarr")
        all_movies = self.get_all_movies()
        
        # Try exact match first
        for movie in all_movies:
            if movie.get('title', '').lower() == title.lower():
                return movie
        
        # Try fuzzy matching if exact match fails
        for movie in all_movies:
            if title.lower() in movie.get('title', '').lower() or movie.get('title', '').lower() in title.lower():
                return movie
        
        return None
    
    def delete_movie(self, movie_id: int, delete_files: bool = False) -> bool:
        """Delete a movie from Radarr.
        
        Args:
            movie_id: The ID of the movie to delete
            delete_files: Whether to delete the movie files from disk
            
        Returns:
            Whether the operation was successful
        """
        logger.info(f"Deleting movie ID {movie_id} from Radarr (delete_files={delete_files})")
        try:
            response = requests.delete(
                f"{self.server_url}/api/v3/movie/{movie_id}",
                headers=self.headers,
                params={
                    'deleteFiles': str(delete_files).lower()
                }
            )
            response.raise_for_status()
            
            # Update cache if successful deletion
            if self._movies_cache is not None:
                # Store the movie name before removing from cache
                movie_name = next((m.get('title', 'Unknown') for m in self._movies_cache if m.get('id') == movie_id), 'Unknown')
                self._movies_cache = [m for m in self._movies_cache if m.get('id') != movie_id]
                logger.debug(f"Updated movies cache after deletion")
                
            logger.info(f"Successfully deleted movie '{movie_name}' (ID: {movie_id})")
            return True
        except RequestException as e:
            # Try to get the movie name even when deletion fails
            movie_name = next((m.get('title', 'Unknown') for m in self.get_all_movies() if m.get('id') == movie_id), 'Unknown')
            logger.error(f"Error deleting movie '{movie_name}' (ID: {movie_id}): {e}")
            return False

def format_size(size_in_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.2f} KB"
    elif size_in_bytes < 1024 * 1024 * 1024:
        return f"{size_in_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_in_bytes / (1024 * 1024 * 1024):.2f} GB"

def prompt_for_deletion(item_name: str, item_type: str, size_str: str) -> bool:
    """Prompt the user to confirm deletion of an item.
    
    Args:
        item_name: Name of the item
        item_type: Type of the item (Movie/Show)
        size_str: Size of the item as a formatted string
        
    Returns:
        Whether the user confirmed deletion
    """
    while True:
        response = input(f"Delete {item_type} '{item_name}' ({size_str})? [y/n/q]: ").lower()
        if response in ('y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        elif response in ('q', 'quit'):
            logger.info("User quit the deletion process")
            sys.exit(0)
        else:
            print("Please enter 'y' for yes, 'n' for no, or 'q' to quit.")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Emby Media Cleanup Script')
    
    # Existing arguments
    parser.add_argument('--server', '-s', required=True,
                        help='Emby server URL (e.g., http://localhost:8096)')
    
    parser.add_argument('--api-key', '-k', required=True,
                        help='Emby API key for authentication')
    
    parser.add_argument('--days', '-d', type=int, default=90,
                        help='Number of days to look back for unwatched media (default: 90)')
    
    parser.add_argument('--whitelist', '-w', type=str, default="",
                        help='Comma-separated list of whitelisted users (default: none)')
    
    parser.add_argument('--log-level', '-l', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO', help='Set the logging level (default: INFO)')
    
    parser.add_argument('--debug-whitelist', action='store_true',
                        help='Enable detailed debugging for whitelist functionality')
    
    parser.add_argument('--include-recent', action='store_true',
                        help='Include recently added items in the unwatched list')
    
    parser.add_argument('--ignore-episodes', action='store_true',
                        help='Only consider the show as a whole, ignore episode watch status')
    
    parser.add_argument('--ignore-recent-episodes', action='store_true',
                        help='Include shows that have recent episodes in the unwatched list')
    
    # New arguments for Sonarr and Radarr integration
    parser.add_argument('--sonarr-url',
                        help='Sonarr server URL (e.g., http://localhost:8989)')
    
    parser.add_argument('--sonarr-api-key',
                        help='Sonarr API key for authentication')
    
    parser.add_argument('--radarr-url',
                        help='Radarr server URL (e.g., http://localhost:7878)')
    
    parser.add_argument('--radarr-api-key',
                        help='Radarr API key for authentication')
    
    parser.add_argument('--sort-by-size', action='store_true',
                        help='Sort unwatched media by size (largest first)')
    
    # New arguments for media deletion
    parser.add_argument('--delete-mode', choices=['interactive', 'all', 'none'], default='none',
                        help='Mode for deleting unwatched media: interactive (prompt for each item), '
                             'all (delete all unwatched), or none (default, don\'t delete)')
    
    parser.add_argument('--delete-files', action='store_true',
                        help='When deleting media from Sonarr/Radarr, also delete the files from disk')
    
    parser.add_argument('--min-age-days', type=int, default=90,
                        help='Minimum age in days for media to be eligible for deletion (default: 90)')
    
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be deleted without actually deleting anything')
    
    parser.add_argument('--libraries',
                        help='Comma-separated list of library names to check (default: all libraries)')
    
    parser.add_argument('--list-libraries', action='store_true',
                        help='List all available libraries and exit')
    
    # New arguments for scheduled execution
    parser.add_argument('--interval', type=int, 
                        help='Run the script at specified interval (in hours)')
    
    parser.add_argument('--run-at-start', action='store_true',
                        help='When using --interval, also run the script immediately at startup')
    
    parser.add_argument('--daemon', action='store_true',
                        help='Run as a daemon process in the background')
    
    return parser.parse_args()

def setup_signal_handlers(stop_event):
    """Set up signal handlers for graceful shutdown."""
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down gracefully...")
        stop_event["stop"] = True
        # When running in non-daemon mode, ensure we exit the process
        if sig == signal.SIGINT:  # SIGINT is signal 2
            logger.info("SIGINT received, exiting process")
            sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def run_scheduled(args, interval_hours):
    """Run the script at scheduled intervals."""
    stop_event = {"stop": False}
    setup_signal_handlers(stop_event)
    
    logger.info(f"Running in scheduled mode with {interval_hours} hour interval")
    
    # Track the last time the script was run
    last_run = None
    
    # Run immediately at start if requested
    if args.run_at_start:
        logger.info("Running script immediately due to --run-at-start flag")
        process_unwatched_media(args)
        last_run = datetime.datetime.now()
        # Add a clear separator after each run
        print_flush("\n" + "="*50)
        print_flush(f"END OF RUN: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")
        print_flush(f"NEXT RUN SCHEDULED: {(last_run + datetime.timedelta(hours=interval_hours)).strftime('%Y-%m-%d %H:%M:%S')}")
        print_flush("="*50 + "\n")
        sys.stdout.flush()
    
    try:
        while not stop_event["stop"]:
            now = datetime.datetime.now()
            
            # Calculate the time for the next run
            if last_run:
                next_run = last_run + datetime.timedelta(hours=interval_hours)
                time_until_next_run = next_run - now
                
                # Check if it's time to run the script again
                if time_until_next_run.total_seconds() <= 0:
                    logger.info(f"Running scheduled execution (interval: {interval_hours} hours)")
                    process_unwatched_media(args)
                    last_run = now
                    # Add a clear separator after each run
                    print_flush("\n" + "="*50)
                    print_flush(f"END OF RUN: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")
                    print_flush(f"NEXT RUN SCHEDULED: {(last_run + datetime.timedelta(hours=interval_hours)).strftime('%Y-%m-%d %H:%M:%S')}")
                    print_flush("="*50 + "\n")
                    sys.stdout.flush()
                else:
                    # Log time until next run
                    hours, remainder = divmod(time_until_next_run.total_seconds(), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    logger.debug(f"Next run in: {int(hours)}h {int(minutes)}m {int(seconds)}s")
            
            # Sleep for a bit to avoid consuming CPU
            # Use a shorter sleep interval and check stop_event
            # to ensure we can exit more quickly when a signal is received
            for _ in range(60):  # Still check every minute in total
                if stop_event["stop"]:
                    logger.info("Stop event detected, breaking loop")
                    break
                time.sleep(1)  # Sleep for 1 second at a time
                
        logger.info("Exiting scheduled run loop")
    
    except Exception as e:
        logger.error(f"Error in scheduled execution: {e}", exc_info=True)
    
    logger.info("Scheduled execution stopped")
    # Ensure we exit the process if we break out of the loop
    sys.exit(0)

def process_unwatched_media(args):
    """Process unwatched media based on the provided arguments.
    This function contains the main logic extracted from the main function.
    """
    try:
        # Get configuration from arguments
        server_url = args.server
        api_key = args.api_key
        days = args.days
        
        # Set up whitelisted users from arguments
        whitelisted_users = {user.strip() for user in args.whitelist.split(',') if user.strip()}
        
        # Create Emby client
        client = EmbyClient(server_url, api_key, whitelisted_users)
        
        # Parse libraries to check if specified
        libraries_to_check = None
        if args.libraries:
            libraries_to_check = {lib.strip() for lib in args.libraries.split(',') if lib.strip()}
            logger.info(f"Will only check these libraries: {', '.join(libraries_to_check)}")
        
        # Initialize Sonarr and Radarr clients if URLs and API keys are provided
        sonarr_client = None
        radarr_client = None
        
        if args.sonarr_url and args.sonarr_api_key:
            sonarr_client = SonarrClient(args.sonarr_url, args.sonarr_api_key)
        
        if args.radarr_url and args.radarr_api_key:
            radarr_client = RadarrClient(args.radarr_url, args.radarr_api_key)
        
        # If ignore-episodes flag is set, monkey patch methods to not check episodes
        if args.ignore_episodes:
            logger.info("Ignoring episode watch status, only checking shows as a whole")
            original_get_episodes = client.get_episodes_by_series
            original_get_user_episodes = client.get_user_episodes_by_series
            
            # Return empty lists to effectively ignore episodes
            client.get_episodes_by_series = lambda series_id: []
            client.get_user_episodes_by_series = lambda user_id, series_id: []
        
        # Update the get_items_by_library method to include DateCreated field
        original_get_items = client.get_items_by_library
        def updated_get_items(library_id):
            logger.info(f"Fetching items from library ID: {library_id}")
            try:
                response = requests.get(
                    f"{client.server_url}/emby/Items",
                    headers=client.headers,
                    params={
                        'ParentId': library_id,
                        'Recursive': True,
                        'IncludeItemTypes': 'Movie,Series',
                        'Fields': 'DateLastPlayed,Path,MediaStreams,Overview,DateCreated',
                        'SortBy': 'DateCreated,SortName',
                        'SortOrder': 'Descending'
                    }
                )
                response.raise_for_status()
                items = response.json().get('Items', [])
                logger.info(f"Found {len(items)} items in library")
                return items
            except RequestException as e:
                logger.error(f"Error fetching items from library {library_id}: {e}")
                return []
        
        # Override the method if we want to consider newly added items
        if not args.include_recent:
            client.get_items_by_library = updated_get_items
            logger.info("Excluding recently added items from unwatched list")
        
        unwatched_items = client.get_unwatched_items(days, libraries_to_check)
        
        # Organize results by media type
        movies = []
        shows = []
        cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        
        # Check for recently added episodes for TV shows
        recently_updated_series_ids = set()
        if not args.ignore_recent_episodes:
            logger.info("Checking for TV shows with recently added episodes")
            for item in unwatched_items:
                if item.get('Type') == 'Series':
                    series_id = item.get('Id')
                    series_name = item.get('Name', 'Unknown')
                    
                    # Get all episodes to check their creation dates
                    episodes = client.get_episodes_by_series(series_id)
                    
                    # Enhanced debugging for episode dates
                    if args.log_level == 'DEBUG':
                        recent_episodes = [e for e in episodes if e.get('DateCreated') and e.get('DateCreated') > cutoff_date]
                        if recent_episodes:
                            logger.debug(f"Series '{series_name}' has {len(recent_episodes)} recent episodes:")
                            for ep in recent_episodes[:3]:  # Show up to 3 examples
                                logger.debug(f"  - {ep.get('Name')}: Created {ep.get('DateCreated')}")
                    
                    for episode in episodes:
                        date_created = episode.get('DateCreated')
                        if date_created and date_created > cutoff_date:
                            logger.info(f"Excluding series '{series_name}' - has episode {episode.get('Name')} added after {cutoff_date}")
                            recently_updated_series_ids.add(series_id)
                            break
            
            logger.info(f"Found {len(recently_updated_series_ids)} TV shows with recently added episodes")
        
        # Gather movie and show data with size info from Sonarr/Radarr if available
        total_movie_size = 0
        total_show_size = 0
        
        for item in unwatched_items:
            item_type = item.get('Type')
            item_name = item.get('Name', 'Unknown')
            item_path = item.get('Path', '')
            item_size = 0
            item_id = None
            arr_item = None
            
            # Skip series that have recently added episodes
            if item_type == 'Series' and item.get('Id') in recently_updated_series_ids:
                continue
                
            if item_type == 'Movie':
                # Get size from Radarr if available
                if radarr_client:
                    movie_in_radarr = radarr_client.find_movie_by_title(item_name)
                    if movie_in_radarr:
                        item_size = movie_in_radarr.get('sizeOnDisk', 0)
                        item_id = movie_in_radarr.get('id')
                        arr_item = movie_in_radarr
                        logger.debug(f"Found movie '{item_name}' in Radarr with size {format_size(item_size)}")
                
                movie_data = {
                    'Name': item_name,
                    'Path': item_path,
                    'Library': item.get('LibraryName'),
                    'Overview': item.get('Overview', '')[:100] + '...' if item.get('Overview') else 'No overview',
                    'Size': item_size,
                    'Id': item_id,
                    'ArrData': arr_item
                }
                movies.append(movie_data)
                total_movie_size += item_size
                
            elif item_type == 'Series':
                # Get size from Sonarr if available
                if sonarr_client:
                    series_in_sonarr = sonarr_client.find_series_by_title(item_name)
                    if series_in_sonarr:
                        item_size = series_in_sonarr.get('statistics', {}).get('sizeOnDisk', 0)
                        item_id = series_in_sonarr.get('id')
                        arr_item = series_in_sonarr
                        logger.debug(f"Found series '{item_name}' in Sonarr with size {format_size(item_size)}")
                
                show_data = {
                    'Name': item_name,
                    'Path': item_path,
                    'Library': item.get('LibraryName'),
                    'Overview': item.get('Overview', '')[:100] + '...' if item.get('Overview') else 'No overview',
                    'Size': item_size,
                    'Id': item_id,
                    'ArrData': arr_item
                }
                shows.append(show_data)
                total_show_size += item_size
        
        # Sort by size if requested
        if args.sort_by_size:
            movies.sort(key=lambda x: x['Size'], reverse=True)
            shows.sort(key=lambda x: x['Size'], reverse=True)
        
        # Calculate the total size (combined movies and shows)
        total_size = total_movie_size + total_show_size
        
        # Print results - always do this even in interval mode
        print_flush("\n" + "="*50)
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print_flush(f"UNWATCHED MEDIA REPORT ({timestamp})")
        print_flush(f"Not watched in the last {days} days")
        print_flush("="*50)
        
        print_flush(f"\nUNWATCHED MOVIES ({len(movies)}) - Total size: {format_size(total_movie_size)}")
        print_flush("-" * 50)
        for i, movie in enumerate(movies, 1):
            size_info = f" - {format_size(movie['Size'])}" if movie['Size'] > 0 else ""
            print_flush(f"{i}. {movie['Name']}{size_info}")
        
        print_flush(f"\nUNWATCHED SHOWS ({len(shows)}) - Total size: {format_size(total_show_size)}")
        print_flush("-" * 50)
        for i, show in enumerate(shows, 1):
            size_info = f" - {format_size(show['Size'])}" if show['Size'] > 0 else ""
            print_flush(f"{i}. {show['Name']}{size_info}")
        
        # Print grand total
        print_flush("\n" + "="*50)
        print_flush(f"TOTAL UNWATCHED MEDIA SIZE: {format_size(total_size)}")
        print_flush("="*50)
        
        # Handle deletion if requested
        if args.delete_mode != 'none':
            print_flush("\n" + "="*50)
            if args.dry_run:
                print_flush("DRY RUN: Items that would be deleted (no actual deletion will occur)")
            else:
                print_flush("DELETION MODE")
            print_flush("="*50)
            
            deleted_movie_size = 0
            deleted_show_size = 0
            deleted_movie_count = 0
            deleted_show_count = 0
            
            # Process movies
            if radarr_client:
                print_flush("\nMOVIES:")
                for i, movie in enumerate(movies, 1):
                    if movie['Id'] is None:
                        continue
                    
                    should_delete = False
                    if args.delete_mode == 'all':
                        should_delete = True
                    elif args.delete_mode == 'interactive':
                        # Skip interactive mode when running in scheduled/interval mode
                        if args.interval:
                            logger.info("Skipping interactive deletion in scheduled mode")
                            # Still print what would be deleted for visibility
                            print_flush(f"Would delete (if not in interval mode): {movie['Name']} - {format_size(movie['Size'])}")
                            continue
                        should_delete = prompt_for_deletion(movie['Name'], "Movie", format_size(movie['Size']))
                    
                    if should_delete:
                        if args.dry_run:
                            print_flush(f"Would delete: {movie['Name']} - {format_size(movie['Size'])}")
                            deleted_movie_size += movie['Size']
                            deleted_movie_count += 1
                        else:
                            print_flush(f"Deleting: {movie['Name']} - {format_size(movie['Size'])}")
                            success = radarr_client.delete_movie(movie['Id'], args.delete_files)
                            if success:
                                deleted_movie_size += movie['Size']
                                deleted_movie_count += 1
                                print_flush(f"Successfully deleted movie: {movie['Name']}")
                            else:
                                print_flush(f"Failed to delete movie: {movie['Name']}")
            
            # Process shows
            if sonarr_client:
                print_flush("\nSHOWS:")
                for i, show in enumerate(shows, 1):
                    if show['Id'] is None:
                        continue
                    
                    should_delete = False
                    if args.delete_mode == 'all':
                        should_delete = True
                    elif args.delete_mode == 'interactive':
                        # Skip interactive mode when running in scheduled/interval mode
                        if args.interval:
                            logger.info("Skipping interactive deletion in scheduled mode")
                            # Still print what would be deleted for visibility
                            print_flush(f"Would delete (if not in interval mode): {show['Name']} - {format_size(show['Size'])}")
                            continue
                        should_delete = prompt_for_deletion(show['Name'], "Show", format_size(show['Size']))
                    
                    if should_delete:
                        if args.dry_run:
                            print_flush(f"Would delete: {show['Name']} - {format_size(show['Size'])}")
                            deleted_show_size += show['Size']
                            deleted_show_count += 1
                        else:
                            print_flush(f"Deleting: {show['Name']} - {format_size(show['Size'])}")
                            success = sonarr_client.delete_series(show['Id'], args.delete_files)
                            if success:
                                deleted_show_size += show['Size']
                                deleted_show_count += 1
                                print_flush(f"Successfully deleted show: {show['Name']}")
                            else:
                                print_flush(f"Failed to delete show: {show['Name']}")
            
            # Print deletion summary
            print_flush("\n" + "="*50)
            if args.dry_run:
                print_flush("DRY RUN SUMMARY - What would be deleted:")
            else:
                print_flush("DELETION SUMMARY:")
            print_flush("="*50)
            print_flush(f"Movies: {deleted_movie_count} ({format_size(deleted_movie_size)})")
            print_flush(f"Shows: {deleted_show_count} ({format_size(deleted_show_size)})")
            print_flush(f"Total: {deleted_movie_count + deleted_show_count} items ({format_size(deleted_movie_size + deleted_show_size)})")
        
        # Only log completion in scheduled mode; otherwise the main function handles this
        if args.interval:
            logger.info("Scheduled execution completed successfully")
            # Add an extra separator to distinguish between runs
            print_flush("\n" + "="*50)
            print_flush(f"END OF RUN: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print_flush("="*50 + "\n")
        
        # Ensure all output is flushed
        sys.stdout.flush()
        sys.stderr.flush()
    
    except Exception as e:
        logger.error(f"Error processing unwatched media: {e}", exc_info=True)
        # Ensure error output is flushed
        sys.stderr.flush()

def main():
    """Main function to run the script."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Set logging level based on argument
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Clear existing handlers to prevent duplicate logging
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add a single handler with proper formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        '%Y-%m-%d %H:%M:%S'  # Format without milliseconds
    ))
    console_handler.flush = lambda: True  # Force handler to flush
    root_logger.addHandler(console_handler)
    
    # No need for Docker-specific handling since we're using a consistent setup
    if os.environ.get('DOCKER_CONTAINER', '').lower() in ('1', 'true', 'yes'):
        logger.info("Running in Docker environment")
    
    logger.info("Starting Emby Media Cleanup Script")
    
    try:
        # Check for list-libraries flag first
        if args.list_libraries:
            # Create Emby client
            client = EmbyClient(args.server, args.api_key)
            libraries = client.get_libraries()
            print_flush("\n=== AVAILABLE LIBRARIES ===")
            for i, library in enumerate(libraries, 1):
                library_name = library.get('Name', 'Unknown')
                library_type = library.get('LibraryOptions', {}).get('TypeOptions', [{}])[0].get('Type', 'Unknown')
                print_flush(f"{i}. {library_name} (Type: {library_type})")
            print_flush("\nUse --libraries option to specify which libraries to check.")
            sys.stdout.flush()
            return
            
        # Check if we're running in interval mode
        if args.interval:
            if args.interval <= 0:
                logger.error("Interval must be greater than 0")
                return
                
            # If interactive deletion is selected, warn the user and disable it
            if args.delete_mode == 'interactive':
                logger.warning("Interactive deletion mode is not compatible with scheduled execution. "
                             "Either use --delete-mode=all or --delete-mode=none instead.")
                args.delete_mode = 'none'
            
            # Set up signal handler for the main process too
            def main_signal_handler(sig, frame):
                logger.info(f"Main process received signal {sig}, exiting...")
                sys.exit(0)
            
            signal.signal(signal.SIGINT, main_signal_handler)
            signal.signal(signal.SIGTERM, main_signal_handler)
            
            # This will run until terminated by a signal
            run_scheduled(args, args.interval)
        else:
            # Run in single execution mode
            process_unwatched_media(args)
            logger.info("Script completed successfully")
    
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
        sys.exit(0)  # Ensure we exit on keyboard interrupt
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)  # Exit with error code

if __name__ == "__main__":
    main()