# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: exit.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='exit.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\nexit.proto\"+\n\x04\x45xit\x12\x11\n\tclusterId\x18\x01 \x01(\x05\x12\x10\n\x08serverId\x18\x02 \x01(\x05\x62\x06proto3'
)




_EXIT = _descriptor.Descriptor(
  name='Exit',
  full_name='Exit',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='clusterId', full_name='Exit.clusterId', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='serverId', full_name='Exit.serverId', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=14,
  serialized_end=57,
)

DESCRIPTOR.message_types_by_name['Exit'] = _EXIT
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Exit = _reflection.GeneratedProtocolMessageType('Exit', (_message.Message,), {
  'DESCRIPTOR' : _EXIT,
  '__module__' : 'exit_pb2'
  # @@protoc_insertion_point(class_scope:Exit)
  })
_sym_db.RegisterMessage(Exit)


# @@protoc_insertion_point(module_scope)
