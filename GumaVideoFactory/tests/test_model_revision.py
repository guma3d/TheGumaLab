import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi import BackgroundTasks,HTTPException
from app import studio
from app.core import versions as store
from app.core.product_selection import selection_policy,choose_phone
from app.core.blender_runner import build


class ModelRevisionTests(unittest.TestCase):
    def test_dimension_selection_is_not_mesh_order(self):
        groups=[dict(group='max',mesh_count=94,size_m=[.0788,.16337,.01364]),dict(group='pro',mesh_count=94,size_m=[.07268,.14996,.01364])]
        self.assertEqual(choose_phone(groups,selection_policy('iPhone 18 Pro'))['group'],'pro')
        self.assertEqual(choose_phone(groups,selection_policy('iPhone 18 Pro Max'))['group'],'max')
        with self.assertRaises(ValueError):choose_phone(groups,None)
        with self.assertRaises(ValueError):choose_phone([groups[1],groups[1]],selection_policy('iPhone 18 Pro'))
        self.assertIsNone(selection_policy('iPhone 17 Pro'))

    def test_revision_reserves_new_folder_and_clears_approval(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(store,'ROOT',Path(temp)):
            idea=store.create(dict(category='tech',subject='iPhone 18 Pro'),'2026-10-02');iid=idea['id']
            store.reserve(iid,'3DModel')
            folder=store.version_dir(iid,'3DModel',1)
            (folder/'model.blend').write_bytes(b'old-approved-model');(folder/'downloaded.usdz').write_bytes(b'original-asset')
            store.update(iid,'3DModel',1,status='ready',kind='downloaded',approved_at='prior-approval')
            before=(folder/'version.json').read_bytes()
            tasks=BackgroundTasks()
            revision=asyncio.run(studio.revise_model(iid,1,studio.ModelRevision(operation="restore_materials"),tasks))
            self.assertEqual(revision['revision_operation'],'restore_materials');self.assertIn('UV',revision['revision_note'])
            self.assertEqual(revision['number'],2);self.assertEqual(revision['parent_model_version'],1)
            self.assertIsNone(revision['approved_at']);self.assertEqual(len(tasks.tasks),1)
            self.assertEqual((folder/'version.json').read_bytes(),before)
            self.assertEqual((folder/'model.blend').read_bytes(),b'old-approved-model')
            with self.assertRaises(HTTPException):asyncio.run(studio.revise_model(iid,1,studio.ModelRevision(),BackgroundTasks()))

    def test_renderer_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);(folder/'model.blend').write_bytes(b'keep')
            with self.assertRaises(ValueError):build(folder)
            self.assertEqual((folder/'model.blend').read_bytes(),b'keep')


if __name__=='__main__':unittest.main()
