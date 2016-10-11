import unittest
import config


class TestConfig(unittest.TestCase):
    def test_setting_environment(self):
        config.set_environment('sandbox')
        config.METRICS_GRAPPLER_ENDPOINT['sandbox'] = 'variant1'
        config.METRICS_GRAPPLER_ENDPOINT['prod'] = 'variant2'
        self.assertEquals(config.get_env_parameter(config.METRICS_GRAPPLER_ENDPOINT), 'variant1')
        config.set_environment('prod')
        self.assertEquals(config.get_env_parameter(config.METRICS_GRAPPLER_ENDPOINT), 'variant2')
        config.set_environment('invalid')
        self.assertEquals(config.get_env_parameter(config.METRICS_GRAPPLER_ENDPOINT), 'variant1')
        config.set_environment('')
        self.assertEquals(config.get_env_parameter(config.METRICS_GRAPPLER_ENDPOINT), 'variant1')

