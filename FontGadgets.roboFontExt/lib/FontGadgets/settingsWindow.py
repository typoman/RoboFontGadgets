import vanilla
from mojo.extensions import getExtensionDefault, setExtensionDefault
from RFGadgets.observers.startup import getRoboFontGadgetsSubscribers, EXTENSION_ID

class SettingsWindow:

    def __init__(self):
        self.availableSubscribers = getRoboFontGadgetsSubscribers()
        height = len(self.availableSubscribers) * 30 + 20
        self.w = vanilla.Window((300, height), "Subscribers Settings")
        self.extensionSettings = getExtensionDefault(f"{EXTENSION_ID}.subscribers", {})
        for i, subClass in enumerate(self.availableSubscribers):
            isActive = subClass.isActive()
            title = getattr(subClass, "checkbox", subClass.__name__)
            checkbox = vanilla.CheckBox(
                (20, 10 + (i * 30), -10, 22), title, callback=self.checkboxCallback
            )
            checkbox.set(isActive)
            checkbox.subClass = subClass
            setattr(self.w, f"checkbox_{i}", checkbox)
        self.w.open()

    def checkboxCallback(self, sender):
        shouldBeActive = sender.get()
        subClass = sender.subClass
        if shouldBeActive:
            self.extensionSettings[subClass.__name__] = 1
            if not subClass.isActive():
                subClass.activate()
        elif not shouldBeActive:
            self.extensionSettings[subClass.__name__] = 0
            if subClass.isActive():
                subClass.deactivate()
        setExtensionDefault(f"{EXTENSION_ID}.subscribers", self.extensionSettings)

if __name__ == "__main__":
    SettingsWindow()

