from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EvolveRequest(_message.Message):
    __slots__ = ("slatArray", "handleArray", "parameters", "slatTypes", "connectionAngle")
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class SlatTypesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    SLATARRAY_FIELD_NUMBER: _ClassVar[int]
    HANDLEARRAY_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    SLATTYPES_FIELD_NUMBER: _ClassVar[int]
    CONNECTIONANGLE_FIELD_NUMBER: _ClassVar[int]
    slatArray: _containers.RepeatedCompositeFieldContainer[Layer3D]
    handleArray: _containers.RepeatedCompositeFieldContainer[Layer3D]
    parameters: _containers.ScalarMap[str, str]
    slatTypes: _containers.ScalarMap[str, str]
    connectionAngle: str
    def __init__(self, slatArray: _Optional[_Iterable[_Union[Layer3D, _Mapping]]] = ..., handleArray: _Optional[_Iterable[_Union[Layer3D, _Mapping]]] = ..., parameters: _Optional[_Mapping[str, str]] = ..., slatTypes: _Optional[_Mapping[str, str]] = ..., connectionAngle: _Optional[str] = ...) -> None: ...

class Layer3D(_message.Message):
    __slots__ = ("layers",)
    LAYERS_FIELD_NUMBER: _ClassVar[int]
    layers: _containers.RepeatedCompositeFieldContainer[Layer2D]
    def __init__(self, layers: _Optional[_Iterable[_Union[Layer2D, _Mapping]]] = ...) -> None: ...

class Layer2D(_message.Message):
    __slots__ = ("rows",)
    ROWS_FIELD_NUMBER: _ClassVar[int]
    rows: _containers.RepeatedCompositeFieldContainer[Layer1D]
    def __init__(self, rows: _Optional[_Iterable[_Union[Layer1D, _Mapping]]] = ...) -> None: ...

class Layer1D(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, values: _Optional[_Iterable[int]] = ...) -> None: ...

class ProgressUpdate(_message.Message):
    __slots__ = ("hamming", "physics", "isComplete")
    HAMMING_FIELD_NUMBER: _ClassVar[int]
    PHYSICS_FIELD_NUMBER: _ClassVar[int]
    ISCOMPLETE_FIELD_NUMBER: _ClassVar[int]
    hamming: float
    physics: float
    isComplete: bool
    def __init__(self, hamming: _Optional[float] = ..., physics: _Optional[float] = ..., isComplete: bool = ...) -> None: ...

class StopRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PauseRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ExportResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ExportRequest(_message.Message):
    __slots__ = ("folderPath",)
    FOLDERPATH_FIELD_NUMBER: _ClassVar[int]
    folderPath: str
    def __init__(self, folderPath: _Optional[str] = ...) -> None: ...

class FinalResponse(_message.Message):
    __slots__ = ("handleArray",)
    HANDLEARRAY_FIELD_NUMBER: _ClassVar[int]
    handleArray: _containers.RepeatedCompositeFieldContainer[Layer3D]
    def __init__(self, handleArray: _Optional[_Iterable[_Union[Layer3D, _Mapping]]] = ...) -> None: ...
