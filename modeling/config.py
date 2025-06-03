import logging
import sys

logger = logging.getLogger(__name__)

# mlflow
# sometimes when saving links in text.. there is a new line .. strip removes that
try:
    TRACKING_URI = open("../.mlflow_uri").read().strip()
except:
    print('Please create a file .mflow_uri with the URL to the MLFlow server', file=sys.stderr)

EXPERIMENT_NAME = "0-template-ds-modeling"