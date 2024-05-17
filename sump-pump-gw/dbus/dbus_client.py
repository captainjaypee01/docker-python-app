from pydbus import SystemBus
from gi.repository import GLib, GObject

class DBusClient:
    def __init__(self, service_name):
        self.bus = SystemBus()
        self.service_name = service_name
        self.interface = None
        self.object = None
        self.loop = GLib.MainLoop()

    def _on_message_received(self, message):
        print(f"Received message: {message}")
        # Call your processing function here with the received message
        self.on_message_received(message)

    def on_message_received(self, message):
        pass
        # Your processing logic goes here

    def start_publisher(self):
        self.interface = self.bus.publish(self.service_name)
        self.object = self.bus.get(self.service_name)

    def start_subscriber(self):
        self.object = self.bus.get(self.service_name)
        self.object.onMessageReceived = self._on_message_received

    def publish_message(self, message):
        if self.interface:
            self.interface.publish_message(message)
        else:
            print("Error: Client is not configured as a publisher.")

    def start_listening(self):
        if self.object:
            self.loop.run()
        else:
            print("Error: Client is not configured as a subscriber.")
