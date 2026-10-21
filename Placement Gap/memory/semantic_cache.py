from __future__ import annotations
import hashlib, json, time
from pathlib import Path
class SemanticCache:
 def __init__(self,path:Path|None=None,ttl_days:int=14):self.path=path or Path('outputs/semantic-cache.json');self.ttl=ttl_days*86400
 def key(self,text:str)->str:return hashlib.sha256(text.encode()).hexdigest()
 def get(self,text:str):
  if not self.path.exists():return None
  entry=json.loads(self.path.read_text()).get(self.key(text));return entry['value'] if entry and entry['expires']>time.time() else None
 def put(self,text:str,value):
  self.path.parent.mkdir(parents=True,exist_ok=True);data=json.loads(self.path.read_text()) if self.path.exists() else {};data[self.key(text)]={'value':value,'expires':time.time()+self.ttl};self.path.write_text(json.dumps(data))
