import unittest
from mock import Mock, patch
import boto3
import placebo
import os
import shutil
import config
from app.services.s3_service import S3Service


class TestS3Service(unittest.TestCase):
    def setUp(self):
        self.session = boto3.Session()
        try:
            os.makedirs('tests/unit/services/responses')
        except OSError:
            pass

        self.data_path = os.path.join(os.path.dirname(__file__), 'responses')
        self.pill = placebo.attach(self.session, data_path=self.data_path)

        s3_client = self.session.client('s3')
        S3Service._get_client = Mock()
        S3Service._get_client.return_value = s3_client

        self.s3_source = S3Service('foo', 'region1')
        self.s3_source.metrics_service = Mock()

    def test_get_targets(self):
        self.pill.playback()

        get_bucket_tagging_response = {'TagSet': [{'Key': 'Contact', 'Value': 'a@a.com'},
                                                  {'Key': 'ReplicatedTargetBuckets', 'Value': 'target-bucket-1@region1 target-bucket-2@region2'},
                                                  {'Key': 'AWSAccount', 'Value': 'sandbox'}]}
        self.pill.save_response(service='s3',
                                operation='GetBucketTagging',
                                response_data=get_bucket_tagging_response,
                                http_response=200)

        target_buckets = self.s3_source.get_targets()
        self.assertEqual(target_buckets, (['target-bucket-1@region1', 'target-bucket-2@region2'], 'sandbox'), "Failed to get target buckets")

    def test_get_acl(self):
        self.pill.playback()
        get_object_acl_response = {
            'Owner': {},
            'Grants': [],
            'RequestCharged': 'requester'
        }

        self.pill.save_response(service='s3',
                                operation='GetObjectAcl',
                                response_data=get_object_acl_response,
                                http_response=200)

        actual_policy = self.s3_source.get_acl('file', 'version1')
        expected_policy = {'Owner': {}, 'Grants': [],}
        self.assertEqual(actual_policy, expected_policy, "Failed to get object ACL buckets")

    @patch('app.services.s3_service.get_logger_by_class')
    def test_get_targets_handle_get_tag_failure(self, get_logger_by_class):
        self.pill.playback()

        logger = get_logger_by_class.return_value

        get_bucket_tagging_response = None
        self.pill.save_response(service='s3',
                                operation='GetBucketTagging',
                                response_data=get_bucket_tagging_response,
                                http_response=200)

        self.s3_source = S3Service('foo', 'region1')
        self.s3_source.get_targets()
        logger.exception.assert_called_with('Failed to retrieve tags from : foo with exception: ')

    def test_get_targets_return_empty_touple_when_fail_to_get_bucket_tag(self):
        self.pill.playback()

        get_bucket_tagging_response = {'TagSet': [{'Key': 'Contact','Value': 'a@a.com'}]}
        self.pill.save_response(service='s3',
                                operation='GetBucketTagging',
                                response_data=get_bucket_tagging_response,
                                http_response=200)

        target_buckets = self.s3_source.get_targets()
        self.assertEqual(target_buckets, ([], ''), "Failed to get target buckets")

    def test_copy_object(self):
        self.pill.playback()

        self.pill.save_response(service='s3',
                                operation='GetObjectAcl',
                                response_data={},
                                http_response=200)

        self.pill.save_response(service='s3',
                                operation='PutObjectAcl',
                                response_data={},
                                http_response=200)

        self.pill.save_response(service='s3',
                                operation='CopyObject',
                                response_data={'key': 'value'},
                                http_response=200)

        s3_target = S3Service('target', 'region1')
        s3_target.metrics_service = Mock()
        result = s3_target.copy('file', 'version1', self.s3_source)
        self.assertEqual(result, 'Success', "Failed to copy object")
        
    def test_copy_object_unversioned(self):
        self.pill.playback()

        self.pill.save_response(service='s3',
                                operation='GetObjectAcl',
                                response_data={},
                                http_response=200)

        self.pill.save_response(service='s3',
                                operation='PutObjectAcl',
                                response_data={},
                                http_response=200)

        self.pill.save_response(service='s3',
                                operation='CopyObject',
                                response_data={'key': 'value'},
                                http_response=200)

        s3_target = S3Service('target', 'region1')
        s3_target.metrics_service = Mock()
        result = s3_target.copy('file', None, self.s3_source)
        self.assertEqual(result, 'Success', "Failed to copy object")

    def test_copy_catch_exception(self):
        self.s3_source = S3Service('foo', 'region1')
        self.s3_source.metrics_service = Mock()
        self.assertRaises(TypeError, self.s3_source.copy('file', 'version1', self.s3_source))
        self.assertEqual("Failed", self.s3_source.copy('file', 'version1', self.s3_source), "Copy succeed unexpectedly!")

    def test_delete_object(self):
        self.pill.playback()

        delete_object_response = {
            'DeleteMarker': True|False,
            'VersionId': 'string',
            'RequestCharged': 'requester'
        }

        self.pill.save_response(service='s3',
                                operation='DeleteObject',
                                response_data=delete_object_response,
                                http_response=200)

        result = self.s3_source.delete('file')
        self.assertEqual(result, 'Success', "Failed to copy object")

    def test_delete_catch_exception(self):
        self.s3_source = S3Service('foo', 'region1')
        self.s3_source.metrics_service = Mock()
        self.assertRaises(TypeError, self.s3_source.delete('file'))
        self.assertEqual("Failed", self.s3_source.delete('file'), "Copy succeed unexpectedly!")

    @patch('app.services.metrics_service.Metrics')
    @patch('app.services.metrics_service.get_logger_by_class')
    def test_initializemetrics_get_correct_env(self, get_logger_by_class, Metrics):
        logger = get_logger_by_class.return_value
        config.METRICS_GRAPPLER_ENDPOINT = {
            'prod': 'kafka-prod-endpoint',
            'sandbox': 'kafka-sandbox-endpoint',
        }
        config.set_environment('prod')
        self.s3_source.initialize_metrics()
        logger.info.assert_called_with('Using Kafka endpoint: kafka-prod-endpoint (namespace: s3-replicator.prod)')

    def tearDown(self):
        try:
            shutil.rmtree(self.data_path)
        except:
            pass
