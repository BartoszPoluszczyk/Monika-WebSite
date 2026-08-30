from .settings import *  # noqa: F403


# Codex uruchamia testy w odizolowanym interpreterze, który nie ładuje
# binarnego modułu Pillow z lokalnego środowiska projektu.
SILENCED_SYSTEM_CHECKS = ["fields.E210"]
