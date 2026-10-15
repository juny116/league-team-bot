"""Load an explicitly supplied execution configuration."""
from functools import wraps

def configured(function):
    @wraps(function)
    def run(config=None):
        if config is None:
            import argparse
            from omegaconf import OmegaConf
            parser = argparse.ArgumentParser(description=function.__doc__)
            parser.add_argument("--config", required=True, help="Path to your execution configuration")
            args = parser.parse_args()
            config = OmegaConf.load(args.config)
        return function(config)
    return run
