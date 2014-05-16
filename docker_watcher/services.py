import subprocess
import json
import time
import logging
import os
import re
import pytz
from datetime import datetime, timedelta

FORMAT = "%(asctime)-15s %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("docker-watcher")
logger.setLevel(logging.INFO)

_containers = {}

BOOLEANS = {"true": True, "false": False}
EXP_LIFE = re.compile("^(\d+)(s|m|h|d)$")
LIFE_RATES = {"s": 1, "m": 60, "h": 60 * 60, "d": 60 * 60 * 24}


# TODO:
# - logs monitoring
# - command to clean unused/removed containers


class Container(object):
    _previous_state = None
    _cid = None
    _creation = None
    docker_path = "/usr/bin/docker"
    cid_directory = "/var/run/"

    def __init__(self, name, image, publish=None, autostart=True,
            autorestart=True, logfile=None, life=None, volumes=None):
        self.name = name
        self.image = image
        self.publish = publish
        self.autostart = autostart
        self.autorestart = autorestart
        self.logfile = logfile
        self.life = self.parse_life(life) if life else None

        self.volumes = {}
        if volumes:
            for volume in volumes:
                in_host, in_container = map(str.strip, volume.split(":"))
                self.volumes[in_host] = in_container

        _containers[self.name] = self

    @classmethod
    def from_dict(cls, name, dic):
        image = dic["image"]
        publish = dic.get("publish", None)
        autostart = dic.get("autostart", True)
        autorestart = dic.get("autorestart", True)
        logfile = dic.get("logfile", None)
        life = dic.get("life", None)
        volumes = dic.get("volumes", None)

        return cls(name, image, publish=publish, autostart=autostart,
                   autorestart=autorestart, logfile=logfile, life=life,
                   volumes=volumes)

    def parse_life(self, life):
        m = EXP_LIFE.match(life)
        interval, unit = m.groups()
        delta = timedelta(seconds=int(interval) * LIFE_RATES[unit])
        return delta

    def make_cid_path(self):
        return os.path.join(self.cid_directory, "%s.cid" % self.name)

    def save_cid(self, cid):
        self._cid = cid
        fp = file(self.make_cid_path(), "w")
        fp.write(cid)
        fp.close()

    def delete_cid(self):
        if os.path.exists(self.make_cid_path()):
            os.unlink(self.make_cid_path())

    def cid_exists(self):
        return os.path.exists(self.make_cid_path())

    def make_start_params(self):
        params = [self.docker_path, "run", "-d", "--name=" + self.name]

        if self.publish:
            params.extend(["-p", self.publish])

        for in_host, in_container in self.volumes.items():
            params.extend(["-v", "%s:%s" % (in_host, in_container)])

        params.append(self.image)

        return params

    def start(self):
        j = self.inspect()
        if j:
            logger.info("Container %s is already running as %s" % (self.name, self._cid))
            return

        # Run command with needed params
        params = self.make_start_params()
        output = subprocess.check_output(params, stderr=subprocess.STDOUT)

        # Cid file and creation time object
        self._creation = pytz.utc.localize(datetime.utcnow())
        self.save_cid(output.strip())

        # Attach volumes

    def make_stop_params(self):
        return [self.docker_path, "rm", "-f", self.name]

    def stop(self):
        if not self.inspect():
            logger.info("Container %s is not running" % self.name)
            return

        self.delete_cid()
        params = self.make_stop_params()
        output = subprocess.check_output(params, stderr=subprocess.STDOUT)

    def make_inspect_params(self):
        return [self.docker_path, "inspect", self.name]

    def inspect(self):
        params = self.make_inspect_params()
        try:
            output = subprocess.check_output(params, stderr=subprocess.STDOUT)
            j = json.loads(output)
        except (subprocess.CalledProcessError, ValueError) as e:
            return None

        self._cid = j[0]["ID"]
        self._creation = pytz.utc.localize(datetime(*map(int, re.split('[^\d]', j[0]["Created"])[:-2])))
        return j


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


def cmd_restart(name):
    container = _containers[name]
    container.stop()
    container.start()
_commands["restart"] = cmd_restart


def cmd_stop(name):
    container = _containers[name]
    container.stop()
_commands["stop"] = cmd_stop


def cmd_list():
    print("Available containers")
    now = pytz.utc.localize(datetime.utcnow())
    _list = sorted(_containers.values(), key=lambda c: c.name)

    for container in _list:
        container.inspect()
        print
        print container.name
        print "Image:", container.image
        if container._creation:
            print "Container ID:", container._cid
            print "Started: %s (%d secs)" % (container._creation.strftime("%d/%m/%Y at %H:%M:%S"),
                                             (now - container._creation).total_seconds())
_commands["list"] = cmd_list


def cmd_watch(interval=1):
    cmd_autostart()
    logger.info("Watching containers to restart")

    while True:
        time.sleep(interval)
        for name, container in _containers.items():
            new_state = bool(container.inspect())

            # Kills if life is out
            if new_state and container.life:
                now = pytz.utc.localize(datetime.utcnow())
                diff = now - container._creation
                if diff > container.life:
                    logger.info("Stoping container %s after life limit" % name)
                    container.stop()

                    if container.autorestart:
                        logger.info("Starting container %s again" % name)
                        container.start()

            # Restarts if crashed
            if not new_state and container.autorestart and container.cid_exists():
                logger.info("Restarting container %s" % name)
                container.start()

            container._previous_state = new_state
_commands["watch"] = cmd_watch
