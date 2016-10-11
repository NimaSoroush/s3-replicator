import unittest
from mock import patch, Mock


class TestHandlerFlow(unittest.TestCase):

    def setUp(self):
        self.record = {
            "s3": {
                "bucket": {
                    "name": "sourcebucket"
                },
                "object": {
                    "key": "folder/file",
                    "versionId": "version1"
                }
            },
            "awsRegion": "region1"
        }
        
        self.unversioned_record = {
            "s3": {
                "bucket": {
                    "name": "sourcebucket"
                },
                "object": {
                    "key": "folder/file",
                }
            },
            "awsRegion": "region1"
        }

    @patch('main.S3Service')
    def test_process_record_calls_functions_with_correct_input(self, S3Service):
        mock_s3_service = S3Service.return_value
        mock_s3_service.bucket_name = 'foo'
        mock_s3_service.get_targets.return_value = ['s3-target-1@region1'], ''
        mock_s3_service.copy.return_value = 'Success'
        mock_s3_service.delete.return_value = 'Success'

        from main import process_record

        self.record['eventName'] = 'ObjectCreated:Put'
        process_record(self.record, Mock())
        mock_s3_service.copy.assert_called_with("folder/file", "version1", mock_s3_service)
        
        self.record['eventName'] = 'ObjectCreated:Copy'
        process_record(self.record, Mock())
        mock_s3_service.copy.assert_called_with("folder/file", "version1", mock_s3_service)

        self.record['eventName'] = 'ObjectRemoved:Delete'
        process_record(self.record, Mock())
        mock_s3_service.delete.assert_called_with("folder/file")
        
    @patch('main.S3Service')
    def test_process_record_calls_functions_with_correct_input_unversioned_record(self, S3Service):
        mock_s3_service = S3Service.return_value
        mock_s3_service.bucket_name = 'foo'
        mock_s3_service.get_targets.return_value = ['s3-target-1@region1'], ''
        mock_s3_service.copy.return_value = 'Success'
        mock_s3_service.delete.return_value = 'Success'

        from main import process_record

        self.unversioned_record['eventName'] = 'ObjectCreated:Put'
        process_record(self.unversioned_record, Mock())
        mock_s3_service.copy.assert_called_with("folder/file", None, mock_s3_service)
        
        self.unversioned_record['eventName'] = 'ObjectCreated:Copy'
        process_record(self.unversioned_record, Mock())
        mock_s3_service.copy.assert_called_with("folder/file", None, mock_s3_service)
        
        self.unversioned_record['eventName'] = 'ObjectRemoved:Delete'
        process_record(self.unversioned_record, Mock())
        mock_s3_service.delete.assert_called_with("folder/file")

    @patch('main.get_logger_by_namespace')
    @patch('main.S3Service')
    def test_process_record_handle_wrong_bucket_tagging(self, S3Service, get_logger_by_namespace):
        mock_s3_service = S3Service.return_value
        mock_s3_service.get_targets.return_value = ['s3-target-1'], ''

        logger = get_logger_by_namespace.return_value

        from main import process_record
        self.record['eventName'] = 'ObjectCreated:Put'
        process_record(self.record, logger)
        logger.info.assert_called_with("Target bucket names are not in format of (bucket1@region1 bucket2@region2 ...)")
