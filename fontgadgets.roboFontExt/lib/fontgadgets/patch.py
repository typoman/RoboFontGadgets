import functools
import sys
from warnings import warn

DEBUG = False  # Global flag for debug mode

def method(*target_classes, override=True):
    """
    A decorator that can either add a new method or replace an existing one on the given
    classes.

    When `override` is True (default), replaces the existing method in the target classes,
    allowing access to the original via `original()`. When `override` is False, adds
    the method with conflict checks based on the module.

    Args:
        *target_classes: The classes to be decorated.
        override (bool): Determines behavior (True for replace, False for add). Defaults to True.

    Raises:
        TypeError: If no target classes are provided or any target is not a class.
        ValueError: If override is True and the method doesn't exist, or if conflicts occur when override is False.
    """

    def decorator(func):
        if not target_classes:
            raise TypeError("No target classes provided to the decorator.")

        for cls in target_classes:
            if not isinstance(cls, type):
                raise TypeError(f"Expected a class in the decorator, but got:\n{type(cls)}")

        method_name = func.__name__
        module_name = func.__module__
        class_orginal_methods = {}

        def wrapper_with_orignal(orig_method, target_cls):
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                # Bind the original method to the instance
                bound_original = orig_method.__get__(self, target_cls)
                module = sys.modules[module_name]
                original_in_module = module.__dict__.get('original', None)

                # Temporarily set original() in the module
                module.__dict__['original'] = lambda: type(
                    '_OriginalWrapper', (), {method_name: bound_original}
                )()
                try:
                    result = func(self, *args, **kwargs)
                finally:
                    # Restore the original state
                    if original_in_module is not None:
                        module.__dict__['original'] = original_in_module
                    else:
                        del module.__dict__['original']
                return result
            return wrapper

        @functools.wraps(func)
        def default_wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        for _cls in target_classes:
            # Check if the method exists in the class's own __dict__
            original_method = _cls.__dict__.get(method_name, None)

            if not hasattr(_cls, '__patched_methods__'):
                setattr(_cls, '__patched_methods__', {})
            patched_methods = _cls.__patched_methods__
            wrapper = default_wrapper

            if original_method is not None:
                if override is False:
                    if method_name in patched_methods:
                        existing_module = patched_methods[method_name]
                        if existing_module == module_name:
                            warn(f"Overriding already patched method '{method_name}'.", Warning)
                        else:
                            if not DEBUG:
                                raise ValueError(
                                    f"Method '{method_name}' in {_cls.__name__} was patched from module '{existing_module}'. Conflict from '{module_name}'."
                                )
                            else:
                                warn(f"DEBUG: Overriding method '{method_name}' from different module.", Warning)
                    else:
                        if not DEBUG:
                            raise ValueError(
                                f"Method '{method_name}' already exists in {_cls.__name__} and was not patched."
                            )
                        else:
                            warn(f"DEBUG: Overriding method '{method_name}'.", Warning)
                else:
                    delattr(_cls, method_name)
                    wrapper = wrapper_with_orignal(original_method, _cls)
            setattr(_cls, method_name, wrapper)
            patched_methods[method_name] = module_name  # Track addition

        return func

    return decorator
