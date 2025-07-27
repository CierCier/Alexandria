import secretstorage
import keyring
from secretstorage import dbus_init
import os


class PasswordManager:
    def __init__(self):
        self.dbus = dbus_init()
        self.collection = secretstorage.get_default_collection(self.dbus)
        self.collection.unlock()
        self.service = "alexandria"
        self.username = os.getenv("USER", "default_user")

    def save_password(self, password):
        """Save a password to the secret storage."""
        item = secretstorage.Item.new(
            self.collection, self.service, {"username": self.username}, password
        )
        item.create()
        return True

    def get_password(self):
        """Retrieve a password from the secret storage."""
        items = self.collection.get_all_items()
        for item in items:
            if (
                item.get_label() == self.service
                and item.get_attributes().get("username") == self.username
            ):
                return item.get_secret()
        return None

    def delete_password(self):
        """Delete a password from the secret storage."""
        items = self.collection.get_all_items()
        for item in items:
            if (
                item.get_label() == self.service
                and item.get_attributes().get("username") == self.username
            ):
                item.delete()
                return True
        return False
