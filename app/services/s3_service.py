import boto3
from app.utils.custom_logging import get_logger_by_class


class S3Service:
    def __init__(self, name, region):
        self.bucket_name = name
        self._bucket_region = region
        self._client = self._get_client()
        self.logger = get_logger_by_class(self)

    def get_targets(self):
        try:
            tag_set = self._client.get_bucket_tagging(Bucket=self.bucket_name)['TagSet']
            target_buckets, aws_account = ([], '')
            for tag in tag_set:
                if tag['Key'] == 'ReplicatedTargetBuckets':
                    target_buckets = tag['Value'].split(' ')
                elif tag['Key'] == 'AWSAccount':
                    aws_account = tag['Value']
            self.logger.info('Tags retrieved. ReplicatedTargetBuckets={}, AWSAccount={}'.format(target_buckets, aws_account))
            return target_buckets, aws_account
        except Exception as err:
            self.logger.exception('Failed to retrieve tags from : {} with exception: '.format(self.bucket_name, err.message))
        return [], ''

    def get_acl(self, object_key, object_version_id):
        params = {
            'Bucket': self.bucket_name,
            'Key': object_key,
        }
        if object_version_id:
            params['VersionId'] = object_version_id
        access_control_policy = self._client.get_object_acl(**params)
        access_control_policy = {key: value for key, value in access_control_policy.items()
                                 if key == "Grants" or key == "Owner"}
        return access_control_policy

    def set_acl(self, key, version_id, access_control_policy):
        params = {
            'Bucket': self.bucket_name,
            'Key': key,
            'AccessControlPolicy': access_control_policy,
        }
        if version_id:
            params['VersionId'] = version_id
        self._client.put_object_acl(**params)

    def copy(self, object_key, object_version_id, source_bucket):
        target_uri = 's3://{}/{}...'.format(self.bucket_name, object_key)
        copy_source = {'Bucket': source_bucket.bucket_name, 'Key': object_key}
        if object_version_id:
            copy_source['VersionId'] = object_version_id

        self.logger.info('Saving to S3 at {}...'.format(target_uri))
        try:
            result = self._client.copy_object(Bucket=self.bucket_name, CopySource=copy_source, Key=object_key)
            if result:
                try:
                    access_control_policy = source_bucket.get_acl(object_key, object_version_id)
                    self.set_acl(object_key, result.get('VersionId'), access_control_policy)
                except:
                    self.logger.exception('Cannot apply ACL rules to target')

                self.logger.info('Copy completed: {}'.format(result))
                return 'Success'
        except Exception as err:
            self.logger.exception('Failed to copy {}, with exeption={}'.format(object_key, err.message))
            return 'Failed'

    def delete(self, object_key):
        target_uri = 's3://{}/{}...'.format(self.bucket_name, object_key)
        self.logger.info('Deleting from S3 at {}...'.format(target_uri))
        try:
            result = self._client.delete_object(Bucket=self.bucket_name, Key=object_key)
            if result:
                self.logger.info('Delete completed: {}'.format(result))
                return 'Success'
        except Exception as err:
            self.logger.exception('Failed to delete {}, with exeption={}'.format(object_key, err.message))
            return 'Failed'

    def _get_client(self):
        client = boto3.client('s3', region_name=self._bucket_region)
        return client
