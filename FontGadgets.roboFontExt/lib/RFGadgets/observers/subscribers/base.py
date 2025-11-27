from re import S
from mojo.subscriber import Subscriber
from mojo.roboFont import AllFonts
from typing import Any, Optional
from Foundation import NSTimer

class BaseSubscriber(Subscriber):
    """
    A base class providing a simplified API for managing subscriber lifecycles.

    This class, inheriting from `mojo.subscriber.Subscriber`, is designed
    to be subclassed. It offers class-level methods to activate,
    deactivate, and check the status of a subscriber, preventing the
    creation of multiple instances.

    Attributes:
        checkbox (str): Default text for settings window checkbox.
    """

    debug: bool = False
    checkbox: str = "Used in settings window, keep it short."
    description: str = "Subclass long description goes here."
    _instances: dict = {}  # store the singleton instance for each subclass

    def __new__(cls, *args: Any, **kwargs: Any):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if getattr(self, "_initialized", False):
            return
        super().__init__(*args, **kwargs)
        self._initialized = True

    @classmethod
    def activate(cls) -> "BaseSubscriber":
        """
        Activates the subscriber, creating a new instance if none exists.

        This method ensures that only one instance of the subscriber is
        active at any time. If an instance is already registered, it
        returns that instance. Otherwise, it instantiates the class to
        register it.

        You can also override it by using these functions from subscriber
        module depending on what methods you're using:
        `registerCurrentFontSubscriber`
        `registerCurrentGlyphSubscriber`
        `registerSpaceCenterSubscriber`
        `registerGlyphEditorSubscriber`
        `registerFontOverviewSubscriber`
        `registerRoboFontSubscriber`

        Refer to:
        https://robofont.com/documentation/reference/api/mojo/mojo-subscriber/

        Returns:
            An active instance of the subscriber class.
        """
        return cls()

    @classmethod
    def deactivate(cls) -> None:
        """
        Finds the active subscriber instance and deactivates it.

        This method searches for a registered instance of the class and, if
        found, calls its `terminate()` and `destroy()` methods to properly
        unregister and remove it.

        You can also override it by using these functions from subscriber
        module depending on what methods you're using:

        `unregisterCurrentFontSubscriber`
        `unregisterCurrentGlyphSubscriber`
        `unregisterSpaceCenterSubscriber`
        `unregisterGlyphEditorSubscriber`
        `unregisterFontOverviewSubscriber`
        `unregisterRoboFontSubscriber`

        Refer to:
        https://robofont.com/documentation/reference/api/mojo/mojo-subscriber/
        """
        if cls in cls._instances:
            instance = cls._instances[cls]
            instance.terminate()
            instance.destroy()
            del cls._instances[cls]
            if hasattr(instance, "_initialized"):
                del instance._initialized

    @classmethod
    def isActive(cls) -> bool:
        """
        Checks if the subscriber is currently active.

        Returns:
            True if an instance is registered, False otherwise.
        """
        return cls in cls._instances

    @classmethod
    def activeInstance(cls) -> Optional["BaseSubscriber"]:
        """
        Retrieves the active instance of the subscriber.

        Returns:
            The subscriber instance if found, otherwise None.
        """
        return cls._instances.get(cls)


class LazyGlyphSubscriber(BaseSubscriber):
    """
    This subscriber is designed for tasks that do not require immediate
    feedback inside the font and they can be applied to glyphs when user is
    going to open them for example. You need to collect all the changes from
    the `adjunct*` methods of the Subscriber in the subclass and update those
    changes lazily in `updateChanges` when user has stopped interactions that
    require immediate feedback (e.g. saving the font or switching
    glyph/window.)

    Example:
        class MyLazySubscriber(LazyGlyphSubscriber):

            def build(self):
                self.changes['outlines'] = []

            def adjunctGlyphDidChangeOutline(self, info):
                # collect changes
                glyph = info['glyph']
                self.changes.setdefault('outlines', []).append(glyph)

            def updateChanges(self, info) -> None:
                # apply changes on low feedback UI events to prevent
                # interruption on less frequent basis
                # eventName = info.get("subscriberEventName")
                for glyph in self.changes.get('outlines', []):
                    if glyph.name in glyph.font:
                        print('do calculations on', glyph.name)
                        pass

    """

    updateDelay: float = 0.000

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._timer = None
        self._pendingInfo = None
        self._refreshObjectsToObserve()

    def updateChanges(self, info: dict) -> None:
        """
        Processes collected changes; must be implemented by a subclass.

        This method is called by less frequent events to perform updates based
        on the data accumulated. Subclasses must override this method to
        implement their logic.

        Args:
            changed_objects (list): List of objects that will be passed to this
            method that has received change notifications (e.g. glyphs,
            fonts, etc).
        """
        raise NotImplementedError()

    def destroy(self):
        self._stop()
        self.clearObservedAdjunctObjects()

    def _refreshObjectsToObserve(self) -> None:
        objectsToObserver = []
        for f in AllFonts():
            objectsToObserver.extend([g for g in f])
        self.setAdjunctObjectsToObserve(objectsToObserver)

    def fontDocumentDidClose(self, info: dict) -> None:
        self._refreshObjectsToObserve()

    def fontDocumentDidOpen(self, info: dict) -> None:
        self._refreshObjectsToObserve()

    # --- NSTimer Delay Logic ---

    def trigger(self, info: dict) -> None:
        self._pendingInfo = info
        if self._timer is not None:
            self._stop()
        self._makeTimer()

    def _stop(self) -> None:
        if self._timer is None:
            return
        if self._timer.isValid():
            self._timer.invalidate()
            self._timer = None

    def _makeTimer(self) -> None:
        self._timer = (
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                self.updateDelay, self, "timerCallback:", None, False
            )
        )

    def timerCallback_(self, timer: Any) -> None:
        self._stop()
        if self._pendingInfo is not None:
            self.updateChanges(self._pendingInfo)
            self._pendingInfo = None


GLYPH_EVENTS = {
    "roboFontDidSwitchCurrentGlyph",
    "glyphEditorWillSetGlyph",
    "spaceCenterWillOpen",
    "spaceCenterWillClose",
    "scriptingWindowWillOpen",
    "scriptingWindowWillClose",
}

APPLICATION_EVENTS = {
    "roboFontDidBecomeActive",
    "currentFontDidSetFont",
    "roboFontDidChangeScreen",
    "roboFontDidChangePreferences",
    "fontDocumentWillOpen",
    "fontDocumentDidBecomeCurrent",
    "fontDocumentWindowWillOpen",
    "fontOverviewWillOpen",
    "fontOverviewWillClose",
    "glyphEditorWillClose",
}

SAVE_EVENTS = {
    "fontDocumentWillSave",
    "fontDocumentWillAutoSave",
    "fontDocumentWillGenerate",
    "fontDocumentWillTestInstall",
}

for event in GLYPH_EVENTS | APPLICATION_EVENTS | SAVE_EVENTS:
    if event in SAVE_EVENTS:

        def method(self, info):
            self._stop()
            self._pendingInfo = None
            self.updateChanges(info)

    else:

        def method(self, info):
            self.trigger(info)

    setattr(LazyGlyphSubscriber, event, method)
