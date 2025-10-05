# -*- coding: utf-8 -*-
from .fieldnamereplacer import FieldNameReplacer

def classFactory(iface):
    return FieldNameReplacer(iface)
