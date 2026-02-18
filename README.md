# Ankigate

**Ankigate** is a system-wide network gatekeeper. It intercepts traffic at the OS level to ensure that specified domains are unreachable until you have earned a break through Anki.

---

### Mechanics

* **OS-Level Block:** Reroutes traffic to `127.0.0.1`.
* **Anki Integration:** Real-time progress tracking via AnkiConnect.

---

### Usage

**Requirement:** Run terminal as **Administrator**.

```bash
python ankigate.py [-d] [-<minutes>] [-u]

```

| Option | Effect |
| --- | --- |
| **(no args)** | Displays usage manual. |
| **-d** | Start session with default reward time. |
| **-<num>** | Start session with custom reward minutes (e.g., `-10`). |
| **-u** | **Emergency Unblock:** Cleans `hosts` file and exits. |

---

### Setup

1. **AnkiConnect:** Install the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on.
2. **Configuration:** Run once to generate `config.json`, then populate `WEBSITES`.

```json
{
    "ANKI_URL": "http://localhost:8765",
    "WEBSITES": ["example.com", "www.example.com"],
    "CARD_TO_MINUTE_RATIO": 5,
    "DEFAULT_REWARD_IN_MINUTE": 1
}

```

---

### Disclaimer

Modifies system files. Use `-u` to manually revert changes. Ensure Anki is open before starting.
