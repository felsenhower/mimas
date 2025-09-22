from abc import ABC, abstractmethod, ABCMeta

def route(path: str, url_args: tuple[str] | None = None):
    def decorator(func):
        func._my_path = path
        func._is_route_definition = True
        return staticmethod(abstractmethod(func))
    return decorator

class InterfaceDefinitionMeta(ABCMeta):
    def __new__(cls, name, bases, dct):
        cls_obj = super().__new__(cls, name, bases, dct)
        cls_obj._route_definitions = [
            attr_name
            for attr_name, attr_value in dct.items()
            if getattr(getattr(attr_value, "__func__", attr_value), "_is_route_definition", False)
        ]
        return cls_obj

class InterfaceDefinition(ABC, metaclass=InterfaceDefinitionMeta):
    pass

def is_interface_definition_class(cls):
    # TODO
    pass

def is_interface_implementation_class(cls):
    # TODO
    pass
