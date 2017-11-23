# -*- coding: utf-8 -*-
__author__ = 'xtwxfxk'

import json, uuid
from collections import OrderedDict
from django.db import models
from jsonfield import JSONCharField, JSONField

class JSONSortField(JSONField, models.TextField):

    def __init__(self, *args, **kwargs):
        self.sort_by = kwargs.pop('sort_by', [])
        super(JSONSortField, self).__init__(*args, **kwargs)

    def get_db_prep_value(self, value, connection, prepared=False):
        """Convert JSON object to a string"""
        if self.null and value is None:
            return None

        if self.sort_by:
            return json.dumps(OrderedDict(sorted(value.items(), key=lambda item: self.sort_by.index(item[0]) + 1 if item[0] in self.sort_by else 999)), **self.dump_kwargs)
        else:
            return json.dumps(value, **self.dump_kwargs)

    def dumps_for_display(self, value):
        kwargs = { "indent": 2 }
        kwargs.update(self.dump_kwargs)

        if self.sort_by:
            return json.dumps(OrderedDict(sorted(value.items(), key=lambda item: self.sort_by.index(item[0]) + 1 if item[0] in self.sort_by else 999)), **kwargs)
        else:
            return json.dumps(value, **kwargs)

# >>> json.dumps(OrderedDict(sorted(s.items(), key=lambda k: 1 if k[0]=='domain' else 2)))
class JSONCharSortField(JSONCharField, models.CharField):

    def __init__(self, *args, **kwargs):
        self.sort_by = kwargs.pop('sort_by', [])
        super(JSONCharSortField, self).__init__(*args, **kwargs)

    def get_db_prep_value(self, value, connection, prepared=False):
        """Convert JSON object to a string"""
        if self.null and value is None:
            return None

        if self.sort_by:
            return json.dumps(OrderedDict(sorted(value.items(), key=lambda item: self.sort_by.index(item[0]) + 1 if item[0] in self.sort_by else 999)), **self.dump_kwargs)
        else:
            return json.dumps(value, **self.dump_kwargs)

    def dumps_for_display(self, value):
        if self.sort_by:
            return json.dumps(OrderedDict(sorted(value.items(), key=lambda item: self.sort_by.index(item[0]) + 1 if item[0] in self.sort_by else 999)), **self.dump_kwargs)
        else:
            return json.dumps(value, **self.dump_kwargs)


class UUIDField(models.Field):

    def __init__(self, version=4, node=None, clock_seq=None,
                 namespace=None, name=None, auto=False, hyphenate=False, *args, **kwargs):
        assert version in (1, 3, 4, 5), "UUID version %s is not supported." % version
        self.auto = auto
        self.version = version
        self.hyphenate = hyphenate
        # We store UUIDs in hex format, which is fixed at 32 characters.
        kwargs['max_length'] = 32
        if auto:
            # Do not let the user edit UUIDs if they are auto-assigned.
            kwargs['editable'] = False
            kwargs['blank'] = True
            kwargs['unique'] = True
        if version == 1:
            self.node, self.clock_seq = node, clock_seq
        elif version in (3, 5):
            self.namespace, self.name = namespace, name
        super(UUIDField, self).__init__(*args, **kwargs)

    def _create_uuid(self):
        if self.version == 1:
            args = (self.node, self.clock_seq)
        elif self.version in (3, 5):
            error = None
            if self.name is None:
                error_attr = 'name'
            elif self.namespace is None:
                error_attr = 'namespace'
            if error is not None:
                raise ValueError("The %s parameter of %s needs to be set." %
                                 (error_attr, self))
            if not isinstance(self.namespace, uuid.UUID):
                raise ValueError("The name parameter of %s must be an "
                                 "UUID instance." % self)
            args = (self.namespace, self.name)
        else:
            args = ()
        return getattr(uuid, 'uuid%s' % self.version)(*args)

    def db_type(self, connection=None):
        """
        Return the special uuid data type on Postgres databases.
        """
        if connection and 'postgres' in connection.vendor:
            return 'uuid'
        return 'char(%s)' % self.max_length

    def pre_save(self, model_instance, add):
        """
        This is used to ensure that we auto-set values if required.
        See CharField.pre_save
        """
        value = getattr(model_instance, self.attname, None)
        if self.auto and add and not value:
            # Assign a new value for this attribute if required.
            uuid = self._create_uuid()
            setattr(model_instance, self.attname, uuid)
            value = uuid.hex
        return value

    def get_db_prep_value(self, value, connection, prepared=False):
        """
        Casts uuid.UUID values into the format expected by the back end
        """
        if isinstance(value, uuid.UUID):
            value = str(value)
        if isinstance(value, str):
            if '-' in value:
                return value.replace('-', '')
        return value

    def value_to_string(self, obj):
        val = self._get_val_from_obj(obj)
        if val is None:
            data = ''
        else:
            data = unicode(val)
        return data

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.CharField,
            'max_length': self.max_length,
            }
        defaults.update(kwargs)
        return super(UUIDField, self).formfield(**defaults)

try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^lutils\.db\.models\.fields\.JSONSortField"])
    add_introspection_rules([], ["^lutils\.db\.models\.fields\.JSONCharSortField"])
    add_introspection_rules([], ["^lutils\.db\.models\.fields\.UUIDField"])
except ImportError:
    pass