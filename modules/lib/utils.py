from ..release import Environment, Release
from .context import global_context
from settings import canonn_live_url, canonn_staging_url, canonn_dev_url, canonn_env


def get_endpoint(is_beta=False):
    environ = Environment(canonn_env)
    urls = {
        Environment.LIVE: canonn_live_url,
        Environment.STAGING: canonn_staging_url,
        Environment.DEVELOPMENT: canonn_dev_url,
    }
    if is_beta:
        return urls[Environment.STAGING]
    return urls.get(environ, canonn_live_url)
