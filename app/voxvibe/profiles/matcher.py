"""Profile matching system for customizing post-processing based on window information."""

import logging
import re
from dataclasses import dataclass
from typing import List, Optional

from ..models import WindowInfo

logger = logging.getLogger(__name__)


@dataclass
class ProfileMatcher:
    """Configuration for matching windows to profiles."""
    profile_name: str
    title_matcher: Optional[str] = None
    wm_class_matcher: Optional[str] = None
    
    def __post_init__(self):
        """Validate the matcher configuration."""
        if not self.title_matcher and not self.wm_class_matcher:
            raise ValueError("At least one of title_matcher or wm_class_matcher must be provided")
        
        # Validate regex patterns
        if self.title_matcher:
            try:
                re.compile(self.title_matcher)
            except re.error as e:
                raise ValueError(f"Invalid title_matcher regex pattern '{self.title_matcher}': {e}")
        
        if self.wm_class_matcher:
            try:
                re.compile(self.wm_class_matcher)
            except re.error as e:
                raise ValueError(f"Invalid wm_class_matcher regex pattern '{self.wm_class_matcher}': {e}")


@dataclass
class Profile:
    """Configuration for a post-processing profile."""
    name: str
    prompt: str


class ProfileMatcherService:
    """Service for matching window information to profiles."""
    
    def __init__(self, profile_matchers: List[ProfileMatcher], profiles: List[Profile]):
        """Initialize the profile matcher service.
        
        Args:
            profile_matchers: List of matchers to apply
            profiles: List of available profiles
        """
        self.profile_matchers = profile_matchers
        self.profiles = {profile.name: profile for profile in profiles}
        
        # Validate that all matchers reference existing profiles
        for matcher in profile_matchers:
            if matcher.profile_name not in self.profiles:
                logger.warning(f"Profile matcher references unknown profile: {matcher.profile_name}")
    
    def find_matching_profile(self, window_info: WindowInfo) -> Optional[Profile]:
        """Find the first matching profile for the given window information.
        
        Args:
            window_info: Window information to match against
            
        Returns:
            Matching Profile if found, None otherwise
        """
        if not window_info:
            logger.debug("No window info provided for profile matching")
            return None
        
        for matcher in self.profile_matchers:
            try:
                title_matches = True
                wm_class_matches = True
                match_details = []
                
                # Check title matcher if provided
                if matcher.title_matcher:
                    title = window_info.get("title", "")
                    title_matches = bool(re.search(matcher.title_matcher, title, re.IGNORECASE))
                    if title_matches:
                        match_details.append(f"title pattern '{matcher.title_matcher}' matched '{title}'")
                
                # Check wm_class matcher if provided
                if matcher.wm_class_matcher:
                    wm_class = window_info.get("wm_class", "")
                    wm_class_matches = bool(re.search(matcher.wm_class_matcher, wm_class, re.IGNORECASE))
                    if wm_class_matches:
                        match_details.append(f"wm_class pattern '{matcher.wm_class_matcher}' matched '{wm_class}'")
                
                # Both conditions must match (if both are specified)
                if title_matches and wm_class_matches:
                    profile = self.profiles.get(matcher.profile_name)
                    if profile:
                        logger.info(f"Window matched profile '{matcher.profile_name}' using {', '.join(match_details)}")
                        return profile
                    else:
                        logger.warning(f"Matched profile '{matcher.profile_name}' not found")
                        
            except re.error as e:
                logger.error(f"Regex error in matcher for profile '{matcher.profile_name}': {e}")
                continue
        
        logger.info(f"No matching profile found for window: {window_info.get('title', 'Unknown')} and wm_class: {window_info.get('wm_class', 'Unknown')}")
        return None
    
    def get_custom_prompt(self, window_info: WindowInfo) -> Optional[str]:
        """Get custom prompt for the given window information.
        
        Args:
            window_info: Window information to match against
            
        Returns:
            Custom prompt if a matching profile is found, None otherwise
        """
        profile = self.find_matching_profile(window_info)
        return profile.prompt if profile else None