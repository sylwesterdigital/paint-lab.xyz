"""v0.1.37 regression: browser v4 -> Flask wire format -> SQLite, and PNG-only public links.

All tests run without Flask. Optional end-to-end Flask endpoints run in test_core.
"""
from __future__ import annotations

import base64,json,sqlite3,struct,tempfile,unittest,zlib
from pathlib import Path
from backend import db,project_format,public_image

APP=Path(__file__).resolve().parents[1]
FRONTEND=(APP/'frontend/index.html').read_text()
API=(APP/'backend/app.py').read_text()


def sample_doc(version=4):
    return {
        'format':'paint-lab-webgl','version':version,'title':'Ärtwork — 試',
        'baseW':640,'baseH':420,'head':3,'activeLayerId':'base-layer',
        'actions':[
            {'kind':'stroke','layerId':'base-layer','cfg':{'styleEngine':'existing-image-fx-v3',
             'strokeEffect':{'kind':'pixelate','cell':32,'amount':.8}},
             'seed':42,'points':[{'x':25,'y':54,'pressure':.7},{'x':120,'y':55,'pressure':1}]},
            {'kind':'layer-filter','layerId':'base-layer','filters':[{'kind':'halftone','cell':16,'amount':1}]},
            {'kind':'layer-filter','layerId':'base-layer','filters':[]}
        ]
    }


def make_png():
    def chunk(kind,payload):
        return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',zlib.crc32(kind+payload)&0xffffffff)
    pixel=bytes([23,155,220,255]);row=b'\0'+pixel*4
    raw=(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',4,4,8,6,0,0,0))+
         chunk(b'IDAT',zlib.compress(row*4))+chunk(b'IEND',b''))
    return 'data:image/png;base64,'+base64.b64encode(raw).decode(),raw

class CloudFormatV137(unittest.TestCase):
    def test_browser_server_format_agreement(self):
        self.assertIn("format:'paint-lab-webgl',version:4",FRONTEND)
        self.assertEqual(project_format.CURRENT_VERSION,4)
        self.assertEqual(project_format.READABLE_VERSIONS,{2,3,4})
        self.assertIn('return project_format.validate_document(obj)',API)
        self.assertIn('current_editable_format=project_format.CURRENT_VERSION',API)

    def test_browser_end_to_end_smoke_is_shipped(self):
        smoke=(APP/'tools/browser_cloud_share_v0137.py').read_text()
        self.assertIn('browser sends editable format v4',smoke)
        self.assertIn('await saveCloud(true)',smoke)
        self.assertIn('await publishArtwork()',smoke)

    def test_roundtrip_new_masked_strokes_and_filters_v4(self):
        doc=sample_doc()
        encoded=project_format.validate_document(doc)
        self.assertEqual(json.loads(encoded),doc)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.sqlite3';db.init(path)
            with db.connect(path) as conn:
                uid=conn.execute("INSERT INTO users(username,password_hash) VALUES('cloud_format_test','hash')").lastrowid
                conn.execute('INSERT INTO projects(id,owner_id,title,document) VALUES(?,?,?,?)',
                             ('project-v4',uid,doc['title'],encoded))
            with db.connect(path) as conn:
                result=json.loads(conn.execute('SELECT document FROM projects WHERE id=?',('project-v4',)).fetchone()[0])
            self.assertEqual(result,doc)
            self.assertEqual(result['actions'][0]['cfg']['styleEngine'],'existing-image-fx-v3')

    def test_legacy_project_versions_still_accepted(self):
        for version in (2,3,4):
            doc=sample_doc(version)
            self.assertEqual(json.loads(project_format.validate_document(doc)),doc)

    def test_reject_unknown_version_and_nonfinite_input(self):
        for value in (1,5,True,'4',None):
            doc=sample_doc();doc['version']=value
            with self.subTest(version=value),self.assertRaises(ValueError):
                project_format.validate_document(doc)
        doc=sample_doc();doc['actions'][0]['points'][0]['x']=float('nan')
        with self.assertRaises(ValueError):project_format.validate_document(doc)
        doc=sample_doc();doc['baseW']=8192;doc['baseH']=8192
        with self.assertRaises(ValueError):project_format.validate_document(doc)

    def test_public_share_accepts_real_png_not_project_json(self):
        payload,raw=make_png()
        self.assertEqual(public_image.check_public_png(payload),raw)
        with self.assertRaises(ValueError):public_image.check_public_png('data:application/json;base64,'+base64.b64encode(b'{}').decode())

    def test_public_share_rejects_broken_png_not_late_broken_link(self):
        payload,raw=make_png()
        damaged=bytearray(raw);damaged[-18]^=0xA8
        with self.assertRaises(ValueError):public_image.check_public_png('data:image/png;base64,'+base64.b64encode(damaged).decode())
        for truncated in (raw[:14],raw[:-12]):
            with self.assertRaises(ValueError):public_image.check_public_png('data:image/png;base64,'+base64.b64encode(truncated).decode())
        self.assertIn('function sharePNGBlob(resizeForCloud=false,includeBackground=',FRONTEND)
        self.assertIn('if(png.size<=limit)return png;',FRONTEND)

if __name__=='__main__':unittest.main()
