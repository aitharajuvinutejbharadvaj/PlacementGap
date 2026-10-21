from __future__ import annotations
import json
from pathlib import Path
from typing import Any
class ProfileStore:
 def __init__(self,path:Path|None=None):self.path=path or Path('outputs/profiles.json')
 def get(self,student_id:str)->dict[str,Any]|None:
  if not self.path.exists():return None
  return json.loads(self.path.read_text()).get(student_id)
 def put(self,student_id:str,profile:dict[str,Any])->None:
  self.path.parent.mkdir(parents=True,exist_ok=True);data=json.loads(self.path.read_text()) if self.path.exists() else {};data[student_id]=profile;self.path.write_text(json.dumps(data,indent=2))
