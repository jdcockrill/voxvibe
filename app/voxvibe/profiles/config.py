"""Profiles configuration management for VoxVibe."""

import logging
import tomllib
from pathlib import Path
from typing import Optional

from ..config import XDG_CONFIG_HOME
from .matcher import Profile, ProfileMatcher, ProfileMatcherService

logger = logging.getLogger(__name__)

PROFILES_CONFIG_FILENAME = 'profiles.toml'


def find_profiles_config_file() -> Optional[Path]:
    """Find the profiles configuration file in XDG-compliant locations."""
    config_dir = XDG_CONFIG_HOME / 'voxvibe'
    config_file = config_dir / PROFILES_CONFIG_FILENAME
    
    if config_file.exists():
        logger.debug(f"Found profiles configuration file: {config_file}")
        return config_file
    
    logger.debug("No profiles configuration file found")
    return None


def create_default_profiles_config() -> Path:
    """Create a default profiles configuration file."""
    config_dir = XDG_CONFIG_HOME / 'voxvibe'
    config_dir.mkdir(parents=True, exist_ok=True)
    
    config_file = config_dir / PROFILES_CONFIG_FILENAME
    
    default_config = """# VoxVibe Profiles Configuration
# This file defines custom post-processing profiles for different applications

# Define profiles with custom prompts
[[profile]]
name = "senior_engineer"
prompt = '''
You are a senior software engineer skilled at clear technical communication. Your task is to refine transcribed voice notes into high-quality technical descriptions, code comments, or step-by-step instructions.

1. Correct transcription errors and typos
2. Apply the correct formatting, markup, or comment syntax appropriate to the context
3. Express technical concepts precisely using appropriate terminology
4. Ensure comments are concise, clear, and professional
5. Use proper punctuation, capitalization, and identifier casing
6. Break complex sentences into bullet points or shorter sentences when it aids readability
7. Preserve the speaker's intent—do not add new information or change meaning

Return only the improved text, no explanations or commentary.
'''

# Define matchers to link window information to profiles
# You can specify title_matcher, wm_class_matcher, or both

[[profile_matcher]]
profile_name = "senior_engineer"
wm_class_matcher = "Code|Visual Studio|IntelliJ|Windsurf"
"""

    with open(config_file, 'w') as f:
        f.write(default_config)
    
    logger.info(f"Created default profiles configuration file: {config_file}")
    return config_file


def load_profiles_config() -> Optional[ProfileMatcherService]:
    """Load profiles configuration and return ProfileMatcherService.
    
    Returns:
        ProfileMatcherService instance if configuration is valid, None otherwise
    """
    config_file = find_profiles_config_file()
    
    if config_file is None:
        logger.info("No profiles configuration found, creating default")
        config_file = create_default_profiles_config()
    
    try:
        with open(config_file, 'rb') as f:
            config_data = tomllib.load(f)
        
        # Parse profiles
        profiles = []
        for profile_data in config_data.get('profile', []):
            try:
                profile = Profile(
                    name=profile_data['name'],
                    prompt=profile_data['prompt']
                )
                profiles.append(profile)
            except KeyError as e:
                logger.warning(f"Invalid profile configuration missing key {e}: {profile_data}")
                continue
        
        # Parse profile matchers
        profile_matchers = []
        for matcher_data in config_data.get('profile_matcher', []):
            try:
                matcher = ProfileMatcher(
                    profile_name=matcher_data['profile_name'],
                    title_matcher=matcher_data.get('title_matcher'),
                    wm_class_matcher=matcher_data.get('wm_class_matcher')
                )
                profile_matchers.append(matcher)
            except (KeyError, ValueError) as e:
                logger.warning(f"Invalid profile matcher configuration: {e}: {matcher_data}")
                continue
        
        if not profiles:
            logger.warning("No valid profiles found in configuration")
            return None
        
        if not profile_matchers:
            logger.warning("No valid profile matchers found in configuration")
            return None
        
        logger.info(f"Loaded {len(profiles)} profiles and {len(profile_matchers)} matchers from {config_file}")
        return ProfileMatcherService(profile_matchers, profiles)
        
    except Exception as e:
        logger.error(f"Failed to load profiles configuration from {config_file}: {e}")
        # Attempt to recreate a fresh default config and parse it once more
        try:
            logger.info("Regenerating default profiles configuration due to previous error")
            new_config_file = create_default_profiles_config()
            with open(new_config_file, 'rb') as f:
                config_data = tomllib.load(f)
            # Recursively parse using in-memory data to avoid infinite recursion
            return load_profiles_config()
        except Exception as inner_e:
            logger.error(f"Failed to regenerate default profiles configuration: {inner_e}")
            return None