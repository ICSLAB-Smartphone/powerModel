import os
import sys
import logging
logging.basicConfig()
import logging.handlers
import colorlog
from configs import config


logger = logging.getLogger(config.ProjectName)
logger.propagate = False
logger.setLevel(logging.DEBUG)

#fmt = logging.Formatter('[%(asctime)s]%(levelname)s:%(name)s:%(module)s:%(message)s')
log_colors_config = {
    'DEBUG': 'cyan',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'bold_red',
}
fmt = colorlog.ColoredFormatter(
    #输出那些信息，时间，文件名，函数名等等
    fmt='%(log_color)s[%(asctime)s] %(filename)s -> %(funcName)s line:%(lineno)d [%(levelname)s] : %(message)s',
    #时间格式
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors=log_colors_config
)

# log information on the screen
streamhandler = logging.StreamHandler(sys.stdout)
streamhandler.setFormatter(fmt)
#streamhandler.setLevel(logging.WARNING)
streamhandler.setLevel(logging.DEBUG)
logger.addHandler(streamhandler)

log_dir = os.path.join(config.RootPath, 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, config.ProjectName + ".log")
log_file_handler = logging.FileHandler(log_file)
log_file_handler.setFormatter(fmt)
log_file_handler.setLevel(logging.DEBUG)
logger.addHandler(log_file_handler)

''' Advanced log file usage
log_file_handler = TimedRotatingFileHandler(filename=log_file, when="D", interval=1, backupCount=3)
log_file_handler.suffix = "%Y-%m-%d_%H-%M-%S.log"
log_file_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}.log$")
'''

