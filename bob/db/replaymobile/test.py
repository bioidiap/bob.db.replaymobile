#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Artur Costa Pazo <artur.costa-pazo@idiap.ch>
# Fri Nov 13 11:11:11 2015 +0200
#
# Copyright (C) 2015 Idiap Research Institute, Martigny, Switzerland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""A few checks at the replay mobile database.
"""

import os, sys
import unittest
from .query import Database
from .models import *

authenticate_str = 'authenticate'
if sys.version_info[0] < 3: authenticate_str = authenticate_str.encode('utf8')

enroll_str = 'enroll'
if sys.version_info[0] < 3: enroll_str = enroll_str.encode('utf8')

def db_available(test):
  """Decorator for detecting if OpenCV/Python bindings are available"""
  from bob.io.base.test_utils import datafile
  from nose.plugins.skip import SkipTest
  import functools

  @functools.wraps(test)
  def wrapper(*args, **kwargs):
    dbfile = datafile("db.sql3", __name__, None)
    if os.path.exists(dbfile):
      return test(*args, **kwargs)
    else:
      raise SkipTest("The database file '%s' is not available; did you forget to run 'bob_dbmanage.py %s create' ?" % (dbfile, 'replaymobile'))

  return wrapper


class ReplayMobileDatabaseTest(unittest.TestCase):
  """Performs various tests on the replay attack database."""

  @db_available
  def test01_queryRealAccesses(self):

    db = Database()
    f = db.objects(cls='real')
    #self.assertEqual(len(f), 400) # Still have to capture 1 users (client009)
    self.assertEqual(len(f), 390) 
    for v in f[:10]: #only the 10 first...
      self.assertTrue(isinstance(v.get_realaccess(), RealAccess))
      o = v.get_realaccess()
      self.assertEqual(o.purpose, authenticate_str)

    train = db.objects(cls='real', groups='train')
    self.assertEqual(len(train), 120)

    dev = db.objects(cls='real', groups='devel')
    #self.assertEqual(len(dev), 120) # Still have to capture 1 users (client009)
    self.assertEqual(len(dev), 160)

    test = db.objects(cls='real', groups='test')
    self.assertEqual(len(test), 110)

    #tests train, devel and test files are distinct
    s = set(train + dev + test)
    #self.assertEqual(len(s), 400) # Still have to capture 1 users (client009)
    self.assertEqual(len(s), 390)

  @db_available
  def queryAttackType(self, protocol, N):
    db = Database()
    f = db.objects(cls='attack', protocol=protocol)

    self.assertEqual(len(f), N)
    for k in f[:10]: #only the 10 first...
      k.get_attack()
      self.assertRaises(RuntimeError, k.get_realaccess)

    train = db.objects(cls='attack', groups='train', protocol=protocol)
    self.assertEqual(len(train), int(round(0.3*N)))

    dev = db.objects(cls='attack', groups='devel', protocol=protocol)
    self.assertEqual(len(dev), int(round(0.4*N)))

    test = db.objects(cls='attack', groups='test', protocol=protocol)
    self.assertEqual(len(test), int(round(0.3*N)))

    #tests train, devel and test files are distinct
    s = set(train + dev + test)
    self.assertEqual(len(s), N)

  @db_available
  def test02_queryAttacks(self):

    self.queryAttackType('grandtest', 640)

  @db_available
  def test03_queryPrintAttacks(self):

    self.queryAttackType('print', 320)

  @db_available
  def test04_queryMattescreenAttacks(self):

    self.queryAttackType('mattescreen', 320)
    
  @db_available  
  def test05_queryEnrollments(self):

    db = Database()
    f = db.objects(cls='enroll')
    self.assertEqual(len(f), 160) #40 clients, 2 conditions 2 devices
    for v in f:
      self.assertEqual(v.get_realaccess().purpose, enroll_str)

  @db_available
  def test06_queryClients(self):

    db = Database()
    f = db.clients()
    self.assertEqual(len(f), 40) #40 clients
    self.assertTrue(db.has_client_id(3))
    self.assertTrue(db.has_client_id(40))
    self.assertTrue(db.has_client_id(6))
    self.assertTrue(db.has_client_id(21))
    self.assertTrue(db.has_client_id(30))
    self.assertFalse(db.has_client_id(0))
    self.assertFalse(db.has_client_id(50))
    self.assertFalse(db.has_client_id(60))
    self.assertFalse(db.has_client_id(55))

  @db_available
  def test7_queryfacefile(self):

    db = Database()
    o = db.objects(clients=(1,))[0]
    o.facefile()

  @db_available
  def test8_manage_files(self):

    from bob.db.base.script.dbmanage import main

    self.assertEqual(main('replaymobile files'.split()), 0)

  @db_available
  def test9_manage_dumplist_1(self):

    from bob.db.base.script.dbmanage import main

    self.assertEqual(main('replaymobile dumplist --self-test'.split()), 0)

  @db_available
  def test10_manage_dumplist_2(self):

    from bob.db.base.script.dbmanage import main

    self.assertEqual(main('replaymobile dumplist --class=attack --group=devel --support=hand --protocol=print --self-test'.split()), 0)

  @db_available
  def test11_manage_dumplist_client(self):

    from bob.db.base.script.dbmanage import main

    self.assertEqual(main('replaymobile dumplist --client 1 --self-test'.split()), 0)

  @db_available
  def test12_manage_checkfiles(self):

    from bob.db.base.script.dbmanage import main

    self.assertEqual(main('replaymobile checkfiles --self-test'.split()), 0)
 
  @db_available
  def test13_queryRealAccesses(self):
      db = Database()
      trainClients=['001', '003', '008', '011', '012', '016', '018', '020', '026', '034', '037', '038']
      develClients=['005', '006', '013', '014', '015', '023', '024', '025', '028', '029', '031', '032', '035', '036', '039', '040']
      testClients =['002', '004', '007', '009', '010', '017', '019', '021', '022', '027', '030', '033']
      f = db.objects(cls='real')
      self.assertEqual(len(f), 390)

      train = db.objects(cls='real', groups='train')
      self.assertEqual(len(train), 120)
      for cl in train:
          clFilename = cl.videofile("")
          clientPos = clFilename.find('client')
          clientId = clFilename[clientPos+6:clientPos+9]
          self.assertTrue(clientId in trainClients)


      dev = db.objects(cls='real', groups='devel')
      self.assertEqual(len(dev), 160)
      for cl in dev:
          clFilename = cl.videofile("")
          clientPos = clFilename.find('client')
          clientId = clFilename[clientPos+6:clientPos+9]
          self.assertTrue(clientId in develClients)

      test = db.objects(cls='real', groups='test')
      self.assertEqual(len(test), 110)
      for cl in test:
          clFilename = cl.videofile("")
          clientPos = clFilename.find('client')
          clientId = clFilename[clientPos+6:clientPos+9]
          self.assertTrue(clientId in testClients)

