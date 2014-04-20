import subprocess
import json
import time
import logging
import os

logging.basicConfig()
logger = logging.getLogger("docker-watcher")
logger.setLevel(logging.INFO)

_containers = {}

BOOLEANS = {"true": True, "false": False}
CID_DIR = "/var/run/"


class Container(object):
    _previous_state = None
    docker_path = "/usr/bin/docker"

    def __init__(self, name, image, publish=None, autostart=True,
            autorestart=True, logfile=None):
        self.name = name
        self.image = image
        self.publish = publish
        self.autostart = autostart
        self.autorestart = autorestart
        self.logfile = logfile

        _containers[self.name] = self

    @classmethod
    def from_dict(cls, name, dic):
        image = dic["image"]
        publish = dic.get("publish", None)
        autostart = BOOLEANS[dic.get("autostart", "true")]
        autorestart = BOOLEANS[dic.get("autorestart", "true")]
        logfile = dic.get("logfile", None)

        return cls(name, image, publish=publish, autostart=autostart,
                   autorestart=autorestart, logfile=logfile)

    def make_cid_path(self):
        return os.path.join(CID_DIR, "%s.cid" % self.name)

    def save_cid(self, cid):
        fp = file(self.make_cid_path(), "w")
        fp.write(cid)
        fp.close()

    def delete_cid(self):
        if os.path.exists(self.make_cid_path()):
            os.unlink(self.make_cid_path())

    def cid_exists(self):
        return os.path.exists(self.make_cid_path())

    def start(self):
        if self.inspect():
            logger.info("Container %s is already running" % self.name)
            return

        params = [self.docker_path, "run", "-d", "--name=" + self.name]
        if self.publish:
            params.extend(["-p", self.publish])
        params.append(self.image)
        output = subprocess.check_output(params, stderr=subprocess.STDOUT)
        self.save_cid(output.strip())

    def stop(self):
        if not self.inspect():
            logger.info("Container %s is not running" % self.name)
            return

        self.delete_cid()
        params = [self.docker_path, "rm", "-f", self.name]
        output = subprocess.check_output(params, stderr=subprocess.STDOUT)

    def inspect(self):
        params = [self.docker_path, "inspect", self.name]
        try:
            output = subprocess.check_output(params, stderr=subprocess.STDOUT)
            j = json.loads(output)
            return j
        except (subprocess.CalledProcessError, ValueError) as e:
            return None


_commands = {}
def cmd_autostart():
    for name, container in _containers.items():
        if not container.autostart:
            continue

        container.start()
_commands["autostart"] = cmd_autostart


def cmd_start(name):
    container = _containers[name]
    container.start()
_commands["start"] = cmd_start


def cmd_stop(name):
    container = _containers[name]
    container.stop()
_commands["stop"] = cmd_stop


def cmd_watch(interval=3):
    cmd_autostart()
    logger.info("Watching containers to restart")

    while True:
        time.sleep(interval)
        for name, container in _containers.items():
            new_state = bool(container.inspect())
            if not new_state and container.autorestart and container.cid_exists():
                logger.info("Restarting container %s" % name)
                container.start()
            container._previous_state = new_state
_commands["watch"] = cmd_watch
