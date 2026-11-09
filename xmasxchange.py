import json
import logging
import random
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
HISTORY_PATH = BASE_DIR / "history_data.json"
LOG_PATH = BASE_DIR / "xmasxchange.log"

logger = logging.getLogger("xmasxchange")


def configure_logging() -> None:
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


def load_draw(path: Path):
    """Load the roster and gift history. The people list is the draw when present."""
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except FileNotFoundError:
        logger.error("History file not found: %s", path)
        raise
    except json.JSONDecodeError as exc:
        logger.error("History file is not valid JSON: %s", exc)
        raise
    except OSError as exc:
        logger.error("Could not read history file %s: %s", path, exc)
        raise

    history = defaultdict(list)
    found = set()
    for entry in data.get("history", []):
        try:
            giver = entry["giver"]
            recipient = entry["recipient"]
            year = int(entry["year"])
        except (KeyError, TypeError, ValueError) as exc:
            logger.error("Skipping invalid history row %s: %s", entry, exc)
            continue
        history[giver].append((year, recipient))
        found.add(giver)
        found.add(recipient)

    for giver in history:
        history[giver].sort()
        history[giver] = [recipient for _, recipient in history[giver]]

    listed = data.get("people")
    if isinstance(listed, list) and listed:
        people = sorted({name.strip() for name in listed if isinstance(name, str) and name.strip()})
    else:
        people = sorted(found)
        logger.info("No people list found; using names from history")

    logger.info("Loaded %d people: %s", len(people), ", ".join(people))
    return dict(history), people


def is_valid_assignment(giver: str, recipient: str, history) -> bool:
    """A person cannot give to themself or to either of their last two recipients."""
    if giver == recipient:
        return False

    recent_recipients = history.get(giver, [])[-2:]
    return recipient not in recent_recipients


def generate_assignments(history, people, max_attempts: int = 1000):
    """Generate valid gift exchange assignments."""
    for _attempt in range(max_attempts):
        assignments = []
        available_recipients = people.copy()
        givers = people.copy()
        random.shuffle(givers)

        success = True
        for giver in givers:
            valid_recipients = [
                recipient for recipient in available_recipients
                if is_valid_assignment(giver, recipient, history)
            ]

            if not valid_recipients:
                success = False
                break

            recipient = random.choice(valid_recipients)
            assignments.append((giver, recipient))
            available_recipients.remove(recipient)

        if success:
            logger.info("Found a valid draw")
            return assignments

    logger.error("Could not find valid assignments after %d attempts", max_attempts)
    raise RuntimeError("Could not find valid assignments after maximum attempts")


def main() -> None:
    configure_logging()
    try:
        history, people = load_draw(HISTORY_PATH)
        assignments = generate_assignments(history, people)
    except Exception as exc:
        logger.exception("Gift exchange failed: %s", exc)
        raise SystemExit(1) from exc

    print("\nNew Gift Exchange Assignments:")
    for giver, recipient in sorted(assignments):
        line = f"{giver} -> {recipient}"
        print(line)
        logger.info(line)


if __name__ == "__main__":
    main()
