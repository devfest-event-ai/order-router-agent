import logging
import json
import sys
class JsonFormatter(logging.Formatter):
def format(self, record):
log_record = {
"timestamp": self.formatTime(record, self.datefmt),
"level": record.levelname,
"logger": record.name,
"message": record.getMessage(),
"module": record.module,
"function": record.funcName,
"line": record.lineno
}
if record.exc_info:
log_record["exception"] = self.formatException(record.exc_info)
return json.dumps(log_record)
def setup_structured_logging():
logger = logging.getLogger("OrderRouter")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)

return logger

app_logger = setup_structured_logging()

