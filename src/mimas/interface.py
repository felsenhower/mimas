from abc import ABC, abstractmethod, ABCMeta


def route(path: str, method: str, url_args: tuple[str] | None = None):
    def decorator(func):
        func._path = path
        func._is_route_definition = True
        assert method in {
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "OPTIONS",
            "HEAD",
            "PATCH",
            "TRACE",
        }
        func._method = method
        return staticmethod(abstractmethod(func))

    return decorator


def get(path: str, url_args: tuple[str] | None = None):
    return route(path, "GET", url_args)


def post(path: str, url_args: tuple[str] | None = None):
    return route(path, "POST", url_args)


def put(path: str, url_args: tuple[str] | None = None):
    return route(path, "PUT", url_args)


def delete(path: str, url_args: tuple[str] | None = None):
    return route(path, "DELETE", url_args)


def options(path: str, url_args: tuple[str] | None = None):
    return route(path, "OPTIONS", url_args)


def head(path: str, url_args: tuple[str] | None = None):
    return route(path, "HEAD", url_args)


def patch(path: str, url_args: tuple[str] | None = None):
    return route(path, "PATCH", url_args)


def trace(path: str, url_args: tuple[str] | None = None):
    return route(path, "TRACE", url_args)


class InterfaceDefinitionMeta(ABCMeta):
    def __new__(cls, name, bases, dct):
        cls_obj = super().__new__(cls, name, bases, dct)
        cls_obj._route_definitions = [
            attr_name
            for attr_name, attr_value in dct.items()
            if getattr(
                getattr(attr_value, "__func__", attr_value),
                "_is_route_definition",
                False,
            )
        ]
        return cls_obj


class InterfaceDefinition(ABC, metaclass=InterfaceDefinitionMeta):
    pass


def require_interface_definition_cls(cls: type):
    if cls.__bases__ != (InterfaceDefinition,):
        raise ValueError(
            f'"{cls}" is not a valid Interface Definition class. Interface Definition classes must directly inherit from InterfaceDefinition and no other base classes.'
        )


def require_interface_implementation_cls(cls: type):
    incorrect_base_class_error_msg = f"{cls} is not a valid Interface Implementation class. Interface Definition classes must directly inherit from an Interface Definition class and no other base classes."
    if len(cls.__bases__) != 1:
        raise ValueError(incorrect_base_class_error_msg)
    base = cls.__base__
    try:
        require_interface_definition_cls(base)
    except ValueError as e:
        raise ValueError(incorrect_base_class_error_msg) from e
    try:
        cls()
    except TypeError as e:
        raise ValueError(
            f'"{cls}" is not a valid Interface Implementation class because it is not constructable.'
        ) from e
