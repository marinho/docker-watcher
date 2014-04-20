_containers = {}

BOOLEANS = {"true": True, "false": False}


class Container(object):
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

_commands = {}
def cmd_autostart():
    for name, container in _containers.items():
        if not container.autostart:
            continue

        print name, container
_commands["autostart"] = cmd_autostart
