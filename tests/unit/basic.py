import unittest
import os

from docker_watcher.main import read_config_file
from docker_watcher.main import load_containers
from docker_watcher.services import _containers
from docker_watcher.services import Container


CONFIG_YAML_EXAMPLE = """
dispatcher1:
    image: tdispatch/dispatcher
    publish: "10080:80"
    autostart: true
    autorestart: true
    logfile: /tmp/dispatcher1.log
    volumes:
    - "/in-host:/in-container:ro"
    life: 5d
"""
Container.docker_path = "/bin/echo"
Container.cid_directory = "/tmp/"


class MainTest(unittest.TestCase):
    yaml_path = "/tmp/config.yml"

    def setUp(self):
        fp = file(self.yaml_path, "w")
        fp.write(CONFIG_YAML_EXAMPLE)
        fp.close()

    def tearDown(self):
        os.unlink(self.yaml_path)

    def test_read_config_file(self):
        config = read_config_file(self.yaml_path)
        self.assertEqual(config, {
            'dispatcher1': {
                'autorestart': True,
                'volumes': [
                    '/in-host:/in-container:ro',
                    ],
                'autostart': True,
                'image': 'tdispatch/dispatcher',
                'logfile': '/tmp/dispatcher1.log', 
                'publish': '10080:80',
                'life': '5d',
                }
            })

    def test_load_containers(self):
        config = read_config_file(self.yaml_path)
        load_containers(config)

        self.assertEqual(_containers.keys(), ["dispatcher1"])
        self.assertTrue(isinstance(_containers["dispatcher1"], Container))
        self.assertEqual(_containers["dispatcher1"].volumes, ['/in-host:/in-container:ro'])

    def test_make_start_params(self):
        config = read_config_file(self.yaml_path)
        load_containers(config)

        container = _containers["dispatcher1"]
        self.assertEqual(container.make_start_params(),
                         ['/bin/echo', 'run', '-d', '--name=dispatcher1', '-p',
                          '10080:80', '-v', '/in-host:/in-container:ro', 'tdispatch/dispatcher'])

        container.start()

    def test_make_stop_params(self):
        config = read_config_file(self.yaml_path)
        load_containers(config)

        container = _containers["dispatcher1"]
        self.assertEqual(container.make_stop_params(),
                         ['/bin/echo', "rm", "-f", 'dispatcher1'])

        container.stop()

    def test_make_inspect_params(self):
        config = read_config_file(self.yaml_path)
        load_containers(config)

        container = _containers["dispatcher1"]
        self.assertEqual(container.make_inspect_params(),
                         ['/bin/echo', "inspect", 'dispatcher1'])

        container.inspect()

    def test_cid(self):
        config = read_config_file(self.yaml_path)
        load_containers(config)

        container = _containers["dispatcher1"]
        cid = "123"
        cid_path = container.make_cid_path()

        self.assertEqual(cid_path, '/tmp/dispatcher1.cid')

        container.save_cid(cid)
        self.assertTrue(container.cid_exists())

        container.delete_cid()
        self.assertFalse(container.cid_exists())

