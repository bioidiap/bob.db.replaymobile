#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Sushil Bhattacharjee <sushil.bhattacharjee@idiap.ch>
# Tue 16 Aug 15:47:11 2016

"""Replay attack database implementation as antispoofing.utils.db.Database"""

from . import __doc__ as long_description
from . import Database as ReplayMobileDatabase
import antispoofing.utils
import os
import six

class File(antispoofing.utils.db.File):

  def __init__(self, f):
    """
    Initializes this File object with our own File equivalent
    """

    self.__f = f

  def videofile(self, directory=None):
    return self.__f.videofile(directory=directory)

  videofile.__doc__ = antispoofing.utils.db.File.videofile.__doc__

  def facefile(self, directory=None):
    return self.__f.facefile(directory=directory)
  facefile.__doc__ = antispoofing.utils.db.File.facefile.__doc__

  def bbx(self, directory=None):
    return self.__f.bbx(directory=directory)
  bbx.__doc__ = antispoofing.utils.db.File.bbx.__doc__


  def load(self, directory=None, extension='.hdf5'):
    return self.__f.load(directory=directory, extension=extension)
  load.__doc__ = antispoofing.utils.db.File.bbx.__doc__

  def save(self, data, directory=None, extension='.hdf5'):
    return self.__f.save(data, directory=directory, extension=extension)
  save.__doc__ = antispoofing.utils.db.File.save.__doc__

  def make_path(self, directory=None, extension=None):
    return self.__f.make_path(directory=directory, extension=extension)
  make_path.__doc__ = antispoofing.utils.db.File.make_path.__doc__

  def get_client_id(self):
    return self.__f.client_id
  get_client_id.__doc__ = antispoofing.utils.db.File.get_client_id.__doc__

  def is_real(self):
    return self.__f.is_real()
  is_real.__doc__ = antispoofing.utils.db.File.is_real.__doc__

  def is_mobile(self):
    return self.__f.is_mobile()
  #is_mobile.__doc__ = antispoofing.utils.db.File.is_mobile.__doc__

  def is_tablet(self):
    return self.__f.is_tablet()
  #is_tablet.__doc__ = antispoofing.utils.db.File.is_tablet.__doc__

class Database(antispoofing.utils.db.Database):
  __doc__ = long_description

  def __init__ (self, args=None):
    self.__db = ReplayMobileDatabase()

    self.__kwargs = {}

    if args is not None:

      self.__kwargs = {
        'protocol'   : args.replay_protocol,
        'support'    : args.replay_support,
        'sample_type': args.replay_sample_types,
        'light'      : args.replay_light,
        'clients'    : args.replay_client if args.replay_client else None,
	'device'     : args.replay_device,
       }
  __init__.__doc__ = antispoofing.utils.db.Database.__init__.__doc__

  def get_protocols(self):
    return [k.name for k in self.__db.protocols()]

  def get_attack_types(self):
    # In the case of this DB, this method does not precisely return the attack types
    return [k.name for k in self.__db.protocols()]

  def create_subparser(self, subparser, entry_point_name):
    from . import Attack as ReplayAttackModel, File as ReplayFileModel
    from argparse import RawDescriptionHelpFormatter

    ## remove '.. ' lines from rst
    desc = '\n'.join([k for k in self.long_description().split('\n') if k.strip().find('.. ') != 0])

    p = subparser.add_parser(entry_point_name,
        help=self.short_description(),
        description=desc,
        formatter_class=RawDescriptionHelpFormatter)

    protocols = [k.name for k in self.__db.protocols()]
    p.add_argument('--protocol', type=str, default='grandtest',
        choices=protocols, dest="replay_protocol", nargs='+',
      help='The protocol type may be specified instead of the the id switch to subselect a smaller number of files to operate on (defaults to "%(default)s")')

    supports = ReplayAttackModel.attack_support_choices
    p.add_argument('--support', type=str, dest='replay_support', choices=supports,
        help="If you would like to select a specific support to be used, use this option (if unset, the default, use all)")

    sample_type = ReplayAttackModel.sample_type_choices
    p.add_argument('--sample_types', type=str, dest='replay_sample_types', choices=sample_type,
        help="If you would like to select a specific media (photo or video) to be used, use this option (if unset, the default, use all)")

    lights = ReplayFileModel.light_choices
    p.add_argument('--light', type=str, choices=lights, dest='replay_light', help="Types of illumination conditions (if unset, the default, use all)")

    identities = [k.id for k in self.__db.clients()]
    p.add_argument('--client', type=int, action='append', choices=identities, dest='replay_client', help="Client identifier (if unset, the default, use all)")

    devices = ReplayFileModel.device_choices
    p.add_argument('--device', type=str, choices=devices, dest='replay_device', help="Types of captured device (if unset, the default, use all)")

    p.set_defaults(name=entry_point_name)
    p.set_defaults(cls=Database)
    #p.set_defaults(cls=ReplayMobileDatabase)

    return
  create_subparser.__doc__ = antispoofing.utils.db.Database.create_subparser.__doc__

  def name(self):
    from .driver import Interface
    i = Interface()
    return "Replay Mobile Database (%s)" % i.name()

  def short_name(self):
    from .driver import Interface
    i = Interface()
    return i.name()

  def version(self):
    from .driver import Interface
    i = Interface()
    return i.version()

  def short_description(self):
    return "Replay-Mobile anti-Spoofing database with 1200 videos produced at Idiap, Switzerland"
  short_description.__doc__ = antispoofing.utils.db.Database.short_description.__doc__

  def long_description(self):
    return Database.__doc__
  long_description.__doc__ = antispoofing.utils.db.Database.long_description.__doc__

  def implements_any_of(self, propname):
    if isinstance(propname, (tuple,list)):
      return 'video' in propname
    elif propname is None:
      return True
    elif isinstance(propname, six.string_types):
      return 'video' == propname

    # does not implement the given access protocol
    return False
 
  def get_clients(self, group=None):
    clients = self.__db.clients()
    if group == None:
      return [client.id for client in clients]
    else:
      return [client.id for client in clients if client.set == group]

  def get_data(self, group):
    """Returns either all objects or objects for a specific group"""
    real = dict(self.__kwargs)
    real.update({'groups': group, 'cls': 'real'})
    attack = dict(self.__kwargs)
    attack.update({'groups': group, 'cls': 'attack'})
    return [File(k) for k in self.__db.objects(**real)], \
        [File(k) for k in self.__db.objects(**attack)]

  def get_enroll_data(self, group=None):
    """Returns either all enrollment objects or enrollment objects for a specific group"""
    real = dict(self.__kwargs)
    real.update({'groups': group, 'cls': 'enroll'})
    return [File(k) for k in self.__db.objects(**real)]

  def get_train_data(self):
    return self.get_data('train')
  get_train_data.__doc__ = antispoofing.utils.db.Database.get_train_data.__doc__

  def get_devel_data(self):
    return self.get_data('devel')
  get_devel_data.__doc__ = antispoofing.utils.db.Database.get_devel_data.__doc__

  def get_test_data(self):
    return self.get_data('test')

  get_test_data.__doc__ = antispoofing.utils.db.Database.get_test_data.__doc__

  def get_test_filters(self):
    return ('device', 'support', 'light','protocol')

  def get_filtered_test_data(self, filter):
    
    def device_filter(obj, filter):
      return obj.make_path().find(filter) != -1
      #return obj.make_path().find('attack_' + filter) != -1

    def support_filter(obj, filter):
      return obj.make_path().find(filter) != -1

    def light_filter(obj, filter):
      return obj.make_path().find(filter) != -1

    def protocol_filter(obj, filter):
      return obj.make_path().find(filter) != -1

    real, attack = self.get_test_data()
    
    if filter == 'device':
      return {
          'tablet': ([k for k in real if device_filter(k, 'tablet')], [k for k in attack if device_filter(k, 'tablet')]),
          'mobile': ([k for k in real if device_filter(k, 'mobile')], [k for k in attack if device_filter(k, 'mobile')]),
          }
    elif filter == 'support':
      return {
          'hand': (real, [k for k in attack if support_filter(k, 'hand')]),
          'fixed': (real, [k for k in attack if support_filter(k, 'fixed')]),
          }
    elif filter == 'light':
      return {
 	  'lighton': ([k for k in real if light_filter(k, 'lighton')], [k for k in attack if light_filter(k, 'lighton')]),
	  'lightoff': ([k for k in real if light_filter(k, 'lightoff')], [k for k in attack if light_filter(k, 'lightoff')]),
          'controlled': ([k for k in real if light_filter(k, 'lightoff')], [k for k in attack if light_filter(k, 'lightoff')]),
          'adverse': ([k for k in real if light_filter(k, 'adverse')], [k for k in attack if light_filter(k, 'adverse')]),
	  'direct': ([k for k in real if light_filter(k, 'direct')], [k for k in attack if light_filter(k, 'direct')]),
          'lateral': ([k for k in real if light_filter(k, 'lateral')], [k for k in attack if light_filter(k, 'lateral')]),
          'diffuse': ([k for k in real if light_filter(k, 'diffuse')], [k for k in attack if light_filter(k, 'diffuse')]),
          }
    elif filter == 'protocol':
      return {
          'print': (real, [k for k in attack if protocol_filter(k, 'print')]),
          'mattescreen': (real, [k for k in attack if protocol_filter(k, 'mattescreen')]),
          }

  def get_filtered_devel_data(self, filter):

    def device_filter(obj, filter):
      return obj.make_path().find(filter) != -1
      #return obj.make_path().find('attack_' + filter) != -1

    def support_filter(obj, filter):
      return obj.make_path().find(filter) != -1

    def light_filter(obj, filter):
      return obj.make_path().find(filter) != -1

    def protocol_filter(obj, filter):
      return obj.make_path().find(filter) != -1

    real, attack = self.get_devel_data()

    if filter == 'device':
      return {
          'tablet': ([k for k in real if device_filter(k, 'tablet')], [k for k in attack if device_filter(k, 'tablet')]),
          'mobile': ([k for k in real if device_filter(k, 'mobile')], [k for k in attack if device_filter(k, 'mobile')]),
          }
    elif filter == 'support':
      return {
          'hand': (real, [k for k in attack if support_filter(k, 'hand')]),
          'fixed': (real, [k for k in attack if support_filter(k, 'fixed')]),
          }
    elif filter == 'light':
      return {
 	  'lighton': ([k for k in real if light_filter(k, 'lighton')], [k for k in attack if light_filter(k, 'lighton')]),
	  'lightoff': ([k for k in real if light_filter(k, 'lightoff')], [k for k in attack if light_filter(k, 'lightoff')]),
          'controlled': ([k for k in real if light_filter(k, 'lightoff')], [k for k in attack if light_filter(k, 'lightoff')]),
          'adverse': ([k for k in real if light_filter(k, 'adverse')], [k for k in attack if light_filter(k, 'adverse')]),
	  'direct': ([k for k in real if light_filter(k, 'direct')], [k for k in attack if light_filter(k, 'direct')]),
          'lateral': ([k for k in real if light_filter(k, 'lateral')], [k for k in attack if light_filter(k, 'lateral')]),
          'diffuse': ([k for k in real if light_filter(k, 'diffuse')], [k for k in attack if light_filter(k, 'diffuse')]),
          }
    elif filter == 'protocol':
      return {
          'print': (real, [k for k in attack if protocol_filter(k, 'print')]),
          'mattescreen': (real, [k for k in attack if protocol_filter(k, 'mattescreen')]),
          }

    raise RuntimeError("filter parameter should specify a valid filter among `%s'" % \
        self.get_test_filters())

  def get_all_data(self):
    return self.get_data(None)
  #get_all_data.__doc__ = DatabaseBase.get_all_data.__doc__
  get_all_data.__doc__ = antispoofing.utils.db.Database.get_all_data.__doc__


