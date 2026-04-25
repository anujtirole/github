from loguru import logger

try:
    from plyer import notification as _plyer
    _PLYER_OK = True
except Exception:
    _PLYER_OK = False


def notify(title: str, message: str, timeout: int = 10) -> None:
    logger.info(f"[NOTIFY] {title}: {message}")
    if _PLYER_OK:
        try:
            _plyer.notify(
                title=title,
                message=message,
                app_name="JobHunterX",
                timeout=timeout,
            )
        except Exception as e:
            logger.warning(f"Desktop notification failed: {e}")
