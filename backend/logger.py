import logging

LEVEL_NAME = 'INFO' #INFO, WARNING, CRITICAL, NOTSET
LEVEL = getattr(logging, LEVEL_NAME.upper(), logging.INFO)

log = logging.getLogger("ar_log")
log.setLevel(LEVEL)

console_handler = logging.StreamHandler()
console_handler.setLevel(LEVEL)

formatter = logging.Formatter(
    fmt='[%(asctime)s.%(msecs)03d] %(module)15s:%(lineno)-3d %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(formatter)

if not log.hasHandlers():
    log.addHandler(console_handler)
