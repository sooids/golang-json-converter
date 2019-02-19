#!/usr/bin/env python
# Python 3.7.4

# Python Version of JSON-to-Go by Matt Holt
# https://github.com/mholt/json-to-go
# A simple utility to translate JSON into a Go type definition.
# Ported by sooids
# https://github.com/sooids

import json
import re

Nums = {
    '0': "Zero_", '1': "One_", '2': "Two_", '3': "Three_",
	'4': "Four_", '5': "Five_", '6': "Six_", '7': "Seven_",
	'8': "Eight_", '9': "Nine_"
    }
        
CommonInitialisms = [
    "API", "ASCII", "CPU", "CSS", "DNS", "EOF", "GUID", "HTML", "HTTP", 
    "HTTPS", "ID", "IP", "JSON", "LHS", "QPS", "RAM", "RHS", "RPC", "SLA", 
    "SMTP", "SSH", "TCP", "TLS", "TTL", "UDP", "UI", "UID", "UUID", "URI", 
    "URL", "UTF8", "VM", "XML", "XSRF", "XSS"
    ]

class JsonToGo:
    def __init__(self):
        self._go = ""
        self._tabs = 0
    
    def indent(self, tabs):
        self._go += "\t" * tabs

    def append(self, data):
        self._go += data
    
    # Proper cases a string according to Go conventions
    def toProperCase(self, data):
        f = lambda frag: frag.group().upper().replace("_", "") if frag.group().upper() in CommonInitialisms else frag.group().title().replace("_", "")
        p = re.compile(r"(^|[^a-zA-Z])([a-z]+)")
        return p.sub(f, data)
    
    def parseScope(self, scope):
        if type(scope) == list:
            sliceType = None

            for obj in scope:
                thisType = self.goType(obj)
                if not sliceType:
                    sliceType = thisType
                elif sliceType != thisType:
                    sliceType = self.mostSpecificPossibleGoType(thisType, sliceType)
                    if sliceType == "interface{}":
                        break

            self.append("[]")
            if sliceType == "struct":
                allFields = dict()

                for i in range(len(scope)):
                    keys = scope[i].keys()
                    for obj in keys:
                        keyname = obj
                        if keyname not in allFields:
                            allFields[keyname] = {
                                "value": scope[i][keyname],
                                "count": 0
                            }
                        
                        allFields[keyname]["count"] += 1
                
                # create a common struct with all fields found in the current array
				# omitempty dict indicates if a field is optional
                keys = allFields.keys()
                struct = {}
                omitempty = {}

                for key in keys:
                    keyname = key
                    elem = allFields[keyname]
                    struct[keyname] = elem["value"]
                    omitempty[keyname] = elem["count"] != len(scope)
                self.parseStruct(struct, omitempty) # finally parse the struct !!
            elif sliceType == "slice":
                self.parseScope(scope[0])
            else:
                self.append(sliceType or "interface{}")
        elif type(scope) == dict:
            self.parseStruct(scope, None)
        else:
            self.append(self.goType(scope))
    
    def parseStruct(self, scope, omitempty):
        self.append("struct {\n")
        self._tabs +=1 

        for key in scope.keys():
            keyname = key
            self.indent(self._tabs)
            self.append(self.format(keyname)+" ")
            self.parseScope(scope[keyname])

            self.append(' `json:"' + keyname)
            if omitempty and omitempty[keyname] == True:
                self.append(',omitempty')
            self.append('"`\n')
        self._tabs -= 1
        self.indent(self._tabs)
        self.append("}")

    # Sanitizes and formats a string to make an appropriate identifier in Go
    def format(self, data):
        if not data:
            return ""
        elif re.compile(r"^\d+$").findall(data):
            data = "Num" + data
        elif re.compile(r"\d").findall(data[0]):
            data = Nums[data[0]] + data[1:]
        res = re.sub(r'[^a-z0-9]/ig', "", self.toProperCase(data))
        if not res:
            return "NAMING_FAILED"
        return res

    # Determines the most appropriate Go type
    def goType(self, val):
        if val == None:
            return "interface{}"
        if type(val) == str:
            if re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?(\+\d\d:\d\d|Z)").findall(val):
                return "time.Time"
            else:
                return "string"
        elif type(val) == int or type(val) == float:
            if val % 1 == 0:
                if val > -2147483648 and val < 2147483647:
                    return "int"
                else:
                    return "int64"
            else:
                return "float64"
        elif type(val) == bool:
            return "bool"
        elif type(val) == list:
            return "slice"
        elif type(val) == dict:
            return "struct"
        else:
            return "interface{}"

    # Given two types, returns the more specific of the two
    def mostSpecificPossibleGoType(self, typ1, typ2):
        if "float" in typ1 and "int" in typ2:
            return typ1
        elif "int" in typ1 and "float" in typ2:
            return typ2
        else:
            return "interface{}"

    def Convert(self, jsonString, typename="AutoGenerated"):
        try:
            data = json.loads(jsonString)
            scope = data
        except Exception as e:
            return dict(go="", error=e)
        
        typename = format(typename)
        self.append("type "+typename+" ")
        self.parseScope(scope)
        return self._go

if __name__ == "__main__":
    with open("/Users/soo/go/src/github.com/soo/golang-json-converter/example.json") as f:
        data = f.read()
        print(JsonToGo().Convert(data))