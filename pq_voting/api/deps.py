from functools import lru_cache

from pq_voting.crypto.keygen import AuthorityKeys, load_or_create_authority_keys


@lru_cache
def get_authority_keys() -> AuthorityKeys:
    return load_or_create_authority_keys()
