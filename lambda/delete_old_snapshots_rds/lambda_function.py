'''
Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at

    http://aws.amazon.com/apache2.0/

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
'''

# delete_old_snapshots_rds
# This Lambda function will delete snapshots that have expired and match the regex set in the PATTERN environment variable. It will also look for a matching timestamp in the following format: YYYY-MM-DD-HH-mm
# Set PATTERN to a regex that matches your RDS Instance identifiers
import boto3
from datetime import datetime
import time
import os
import logging
import re
from snapshots_tool_utils import *

LOGLEVEL = os.getenv('LOG_LEVEL', 'ERROR').strip()
PATTERN = os.getenv('PATTERN', 'ALL_INSTANCES')
RETENTION_DAYS = int(os.getenv('RETENTION_DAYS', '7'))
TIMESTAMP_FORMAT = '%Y-%m-%d-%H-%M'
RETENTION_YEARLY = os.getenv('RETENTION_YEARLY', 'NO')
RETENTION_MONTH = int(os.getenv('RETENTION_MONTH', '12'))
RETENTION_YEARSTOKEEP = int(os.getenv('RETENTION_YEARSTOKEEP', '7'))

if os.getenv('REGION_OVERRIDE', 'NO') != 'NO':
    REGION = os.getenv('REGION_OVERRIDE').strip()
else:
    REGION = os.getenv('AWS_DEFAULT_REGION')


logger = logging.getLogger()
logger.setLevel(LOGLEVEL.upper())


def lambda_handler(event, context):
    pending_delete = 0
    client = boto3.client('rds', region_name=REGION)
    response = paginate_api_call(client, 'describe_db_snapshots', 'DBSnapshots')

    filtered_list = get_own_snapshots_source(PATTERN, response)

    for snapshot in filtered_list.keys():

        creation_date = get_timestamp(snapshot, filtered_list)

        if creation_date:
			monthnum = datetime.datetime.strptime(creation_date, "%m")
			yearnum = datetime.datetime.strptime(datetime.now(), "%Y") - datetime.datetime.strptime(creation_date, "%Y")
            difference = datetime.now() - creation_date
            days_difference = difference.total_seconds() / 3600 / 24
            logger.debug('%s created %s days ago' %
                         (snapshot, days_difference))

			if days_difference > RETENTION_DAYS and RETENTION_YEARLY = 'YES' and monthnum !=  RETENTION_MONTH and yearnum > RETENTION_YEARSTOKEEP:
                # delete it
                logger.info('Deleting %s' % snapshot)

                try:
                    client.delete_db_snapshot(
                        DBSnapshotIdentifier=snapshot)

                except Exception:
                    pending_delete += 1
                    logger.info('Could not delete %s ' % snapshot)

        else: 
            	# if we are past RETENTION_DAYS
				if days_difference > RETENTION_DAYS:
					# delete it
					logger.info('Deleting %s' % snapshot)

					try:
						client.delete_db_snapshot(
							DBSnapshotIdentifier=snapshot)

					except Exception:
						pending_delete += 1
						logger.info('Could not delete %s ' % snapshot)

			else: 
				logger.info('Not deleting %s. Created only %s' % (snapshot, days_difference))
	

    if pending_delete > 0:
        message = 'Snapshots pending delete: %s' % pending_delete
        logger.error(message)
        raise SnapshotToolException(message)


if __name__ == '__main__':
    lambda_handler(None, None)


