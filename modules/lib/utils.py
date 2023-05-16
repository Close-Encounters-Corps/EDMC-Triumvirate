from ..release import Environment, Release
from .context import global_context
from settings import canonn_live_url, canonn_staging_url, canonn_dev_url


def get_endpoint(is_beta=False):
    urls = {
        Environment.LIVE: canonn_live_url,
        Environment.STAGING: canonn_staging_url,
        Environment.DEVELOPMENT: canonn_dev_url,
    }
    if is_beta:
        return urls[Environment.STAGING]
    env = env = global_context.by_class(Release).env
    return urls[env]
