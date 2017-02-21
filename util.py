import re

def verifyFieldIsHash(data):
    return len(re.findall(r"([a-fA-F\d]{32})", data))==1
