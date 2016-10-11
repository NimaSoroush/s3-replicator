import json
import urllib
import config
from app.services.s3_service import S3Service
from app.utils.custom_logging import get_logger_by_namespace


def process_record(record, logger):
    source_bucket_name = record['s3']['bucket']['name']
    source_bucket_region = record['awsRegion']
    object_key = urllib.unquote(record['s3']['object']['key'])
    object_version_id = record['s3']['object'].get('versionId')
    event_name = record['eventName']

    source_s3 = S3Service(source_bucket_name, source_bucket_region)
    target_buckets, aws_region = source_s3.get_targets()
    config.set_environment(aws_region or 'sandbox')
    for target_bucket in target_buckets:
        try:
            target_bucket_name, target_bucket_region = target_bucket.split('@', 1)
            target_s3 = S3Service(target_bucket_name, target_bucket_region)
            target_s3.initialize_metrics()
            if event_name.startswith("ObjectCreated:"):
                target_s3.copy(object_key, object_version_id, source_s3)
            elif event_name == "ObjectRemoved:Delete":
                target_s3.delete(object_key)
        except ValueError:
            logger.info("Target bucket names are not in format of (bucket1@region1 bucket2@region2 ...)")
        except:
            logger.info("Unable to (copy)/(delete) item from target bucket:" + target_bucket)


def handler(event, context):
    logger = get_logger_by_namespace('app')
    logger.info("Received event: " + json.dumps(event, indent=2))
    for record in event.get('Records'):
        process_record(record, logger)
