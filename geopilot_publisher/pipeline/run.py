"""
Pipeline entry point (local + CI).

Example:
  python -m geopilot_publisher.pipeline.run --publish false
"""
import argparse
from geopilot_publisher.pipeline.stages import run_all

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--publish", default="false")
    return p.parse_args()

def main():
    args = parse_args()
    publish = str(args.publish).strip().lower() in {"true", "1", "yes", "y"}
    print(f"[pipeline] publish={publish} (raw={args.publish})")
    run_all(publish=publish)

if __name__ == "__main__":
    main()
