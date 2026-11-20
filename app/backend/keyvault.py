"""Encrypted user-specific provider keys. Keys never enter JSON reads or artwork."""
from __future__ import annotations
import os
from pathlib import Path
from cryptography.fernet import Fernet

PROVIDERS = {
 'openai':'OpenAI', 'anthropic':'Anthropic', 'google':'Google Gemini',
 'xai':'xAI', 'replicate':'Replicate', 'fal':'fal.ai'
}

def vault_path(data_dir:Path) -> Path:
    return Path(os.environ.get('PAINT_LAB_VAULT_KEY_FILE',str(data_dir/'vault.key')))

def cipher(data_dir:Path) -> Fernet:
    path=vault_path(data_dir)
    if not path.exists():
        path.parent.mkdir(parents=True,exist_ok=True)
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'wb') as out:out.write(Fernet.generate_key()+b'\n')
    return Fernet(path.read_bytes().strip())

def save(con,owner:int,provider:str,key:str,data_dir:Path):
    if provider not in PROVIDERS:raise ValueError('Unknown provider')
    if not 12<=len(key)<=4096 or any(c.isspace() or ord(c)<33 or ord(c)>126 for c in key):
        raise ValueError('Invalid API key format')
    encrypted=cipher(data_dir).encrypt(key.encode('ascii'))
    con.execute("INSERT INTO provider_keys(owner_id,provider,ciphertext,updated_at) VALUES(?,?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now')) ON CONFLICT(owner_id,provider) DO UPDATE SET ciphertext=excluded.ciphertext,updated_at=excluded.updated_at",(owner,provider,encrypted))

def get(con,owner:int,provider:str,data_dir:Path):
    row=con.execute('SELECT ciphertext FROM provider_keys WHERE owner_id=? AND provider=?',(owner,provider)).fetchone()
    return cipher(data_dir).decrypt(row['ciphertext']).decode('ascii') if row else None

def status(con,owner:int):
    rows={r['provider']:r['updated_at'] for r in con.execute('SELECT provider,updated_at FROM provider_keys WHERE owner_id=?',(owner,))}
    return [{'id':p,'name':name,'configured':p in rows,'updated_at':rows.get(p)} for p,name in PROVIDERS.items()]
