""" init file for the app module: mainly initializes the webserver component """

import logging
import time
from logging.handlers import RotatingFileHandler

from flask import Flask
from app.data_ingestor import DataIngestor
from app.task_runner import ThreadPool

# Create logger with a circular handler
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
HANDLER = RotatingFileHandler('webserver.log', mode='a', maxBytes=60000, backupCount=10)
FORMATTER = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
FORMATTER.converter = time.gmtime
HANDLER.setFormatter(FORMATTER)
LOGGER.addHandler(HANDLER)

# initialize server
webserver = Flask(__name__)

# set the data ingestor to non-existent to prevent some premature access
webserver.data_ingestor = None
webserver.logger = LOGGER
webserver.tasks_runner = ThreadPool()

# now actually set the data ingestor
webserver.data_ingestor = DataIngestor("./nutrition_activity_obesity_usa_subset.csv")

from app import routes
