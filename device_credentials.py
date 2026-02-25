from db.settings import Settings


class DeviceCredentials:
    username: str
    password: str

    def __init__(self):
        settings = Settings()
        self.username = settings.get_setting("network_automation_username")["settingValue"]
        self.password = settings.get_setting("network_automation_password")["settingValue"]
