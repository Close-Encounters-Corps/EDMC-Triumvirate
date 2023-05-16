from ..release import Environment, Release
from .context import global_context
import settings


def get_endpoint(is_beta=False):
    urls = {
        Environment.LIVE: settings.canonn_live_url,
        Environment.STAGING: settings.canonn_staging_url,
        Environment.DEVELOPMENT: settings.canonn_dev_url,
    }
    if is_beta:
        return urls[Environment.STAGING]
    env = env = global_context.by_class(Release).env
    return urls[env]
