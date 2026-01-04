from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EvolveRequest(_message.Message):
    __slots__ = ("slatArray", "handleArray", "parameters", "slatTypes", "connectionAngle", "coordinateMap", "handleLinks")
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
    class CoordinateMapEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: CoordinateList
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[CoordinateList, _Mapping]] = ...) -> None: ...
    SLATARRAY_FIELD_NUMBER: _ClassVar[int]
    HANDLEARRAY_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    SLATTYPES_FIELD_NUMBER: _ClassVar[int]
    CONNECTIONANGLE_FIELD_NUMBER: _ClassVar[int]
    COORDINATEMAP_FIELD_NUMBER: _ClassVar[int]
    HANDLELINKS_FIELD_NUMBER: _ClassVar[int]
    slatArray: _containers.RepeatedCompositeFieldContainer[Layer3D]
    handleArray: _containers.RepeatedCompositeFieldContainer[Layer3D]
    parameters: _containers.ScalarMap[str, str]
    slatTypes: _containers.ScalarMap[str, str]
    connectionAngle: str
    coordinateMap: _containers.MessageMap[str, CoordinateList]
    handleLinks: HandleLinkData
    def __init__(self, slatArray: _Optional[_Iterable[_Union[Layer3D, _Mapping]]] = ..., handleArray: _Optional[_Iterable[_Union[Layer3D, _Mapping]]] = ..., parameters: _Optional[_Mapping[str, str]] = ..., slatTypes: _Optional[_Mapping[str, str]] = ..., connectionAngle: _Optional[str] = ..., coordinateMap: _Optional[_Mapping[str, CoordinateList]] = ..., handleLinks: _Optional[_Union[HandleLinkData, _Mapping]] = ...) -> None: ...

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

class CoordinateList(_message.Message):
    __slots__ = ("coords",)
    COORDS_FIELD_NUMBER: _ClassVar[int]
    coords: _containers.RepeatedCompositeFieldContainer[Coordinate]
    def __init__(self, coords: _Optional[_Iterable[_Union[Coordinate, _Mapping]]] = ...) -> None: ...

class Coordinate(_message.Message):
    __slots__ = ("x", "y")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    x: int
    y: int
    def __init__(self, x: _Optional[int] = ..., y: _Optional[int] = ...) -> None: ...

class HandleKey(_message.Message):
    __slots__ = ("slatId", "position", "side")
    SLATID_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    SIDE_FIELD_NUMBER: _ClassVar[int]
    slatId: str
    position: int
    side: int
    def __init__(self, slatId: _Optional[str] = ..., position: _Optional[int] = ..., side: _Optional[int] = ...) -> None: ...

class PhantomSlatEntry(_message.Message):
    __slots__ = ("phantomSlatId", "parentSlatId", "coordinates")
    PHANTOMSLATID_FIELD_NUMBER: _ClassVar[int]
    PARENTSLATID_FIELD_NUMBER: _ClassVar[int]
    COORDINATES_FIELD_NUMBER: _ClassVar[int]
    phantomSlatId: str
    parentSlatId: str
    coordinates: CoordinateList
    def __init__(self, phantomSlatId: _Optional[str] = ..., parentSlatId: _Optional[str] = ..., coordinates: _Optional[_Union[CoordinateList, _Mapping]] = ...) -> None: ...

class HandleLinkGroup(_message.Message):
    __slots__ = ("groupId", "handles", "hasEnforcedValue", "enforcedValue")
    GROUPID_FIELD_NUMBER: _ClassVar[int]
    HANDLES_FIELD_NUMBER: _ClassVar[int]
    HASENFORCEDVALUE_FIELD_NUMBER: _ClassVar[int]
    ENFORCEDVALUE_FIELD_NUMBER: _ClassVar[int]
    groupId: str
    handles: _containers.RepeatedCompositeFieldContainer[HandleKey]
    hasEnforcedValue: bool
    enforcedValue: int
    def __init__(self, groupId: _Optional[str] = ..., handles: _Optional[_Iterable[_Union[HandleKey, _Mapping]]] = ..., hasEnforcedValue: bool = ..., enforcedValue: _Optional[int] = ...) -> None: ...

class HandleLinkData(_message.Message):
    __slots__ = ("linkGroups", "blockedHandles", "phantomSlats")
    LINKGROUPS_FIELD_NUMBER: _ClassVar[int]
    BLOCKEDHANDLES_FIELD_NUMBER: _ClassVar[int]
    PHANTOMSLATS_FIELD_NUMBER: _ClassVar[int]
    linkGroups: _containers.RepeatedCompositeFieldContainer[HandleLinkGroup]
    blockedHandles: _containers.RepeatedCompositeFieldContainer[HandleKey]
    phantomSlats: _containers.RepeatedCompositeFieldContainer[PhantomSlatEntry]
    def __init__(self, linkGroups: _Optional[_Iterable[_Union[HandleLinkGroup, _Mapping]]] = ..., blockedHandles: _Optional[_Iterable[_Union[HandleKey, _Mapping]]] = ..., phantomSlats: _Optional[_Iterable[_Union[PhantomSlatEntry, _Mapping]]] = ...) -> None: ...
